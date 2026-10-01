"""Tanks vs AI - pure game logic (NO pygame imports in this file).

The window (GUI/games/tanks_window.py) only draws what is stored here and
forwards player input. Everything that decides the outcome of a match lives
in this module, so it can be unit-tested, reused by another GUI, or driven
over a network later.

Coordinate system: pygame style - x grows to the right, y grows DOWNWARD.
Angles: 0 deg = right, 90 = straight up, 180 = left.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

try:                                   # project layout: Games/games/tank_maps.py
    from GUI.games.tank_maps import GameMap, build_maps
except ImportError:                    # fallback when run next to the files
    from tank_maps import GameMap, build_maps

Point = Tuple[float, float]


# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
@dataclass
class GameConfig:
    """Every tunable number in one place (future maps / difficulties)."""
    ground_height: int = 50         # minimum terrain height (the base floor)
    spawn_margin: int = 100         # tank distance from the arena edges
    map_mode: str = "shuffle"       # "shuffle": every map once per cycle | "random"
    # physics (same feel as the prototype: 0.1 time units per frame)
    gravity: float = 9.8
    time_step: float = 0.1          # simulated time per rendered frame
    physics_substeps: int = 4       # collision checks per frame (no tunnelling)
    max_power: int = 200
    # tanks
    tank_hp: int = 100
    move_budget: int = 300          # px a tank may drive per turn
    move_speed: float = 2.0         # px per step while driving
    max_climb: float = 3.0          # max terrain height change per step (steepness limit)
    knockback_per_damage: float = 1.2   # px a tank is pushed per HP lost
    knockback_max: float = 60.0
    knockback_speed: float = 3.0    # px per frame of the knockback slide
    # explosion
    explosion_radius: float = 60
    explosion_max_damage: int = 50
    explosion_duration: int = 30    # frames the animation lasts
    # match rules
    rounds_to_win: int = 3
    max_rounds: int = 5             # Best of 5
    max_turns_per_tank: int = 5     # after that the round is a draw
    points_win: int = 10
    points_draw: int = 5
    points_lose: int = 0
    max_score: int = 50
    tie_result: str = "draw"        # "result" value if 5 rounds end level
    # AI
    ai_difficulty: str = "normal"   # "easy" | "normal" | "hard"
    # aim assistant
    preview_fraction: float = 1 / 3  # share of the flight that is shown
    preview_dot_spacing: int = 10    # one dot every N physics sub-steps


# --------------------------------------------------------------------------- #
# Small data holders
# --------------------------------------------------------------------------- #
@dataclass
class ImpactEvent:
    """What happened when a projectile stopped flying."""
    x: float
    y: float
    kind: str                         # "tank" | "ground" | "out"
    owner: str = ""                   # side that fired: "player" | "ai"
    hit_side: Optional[str] = None    # side of the tank that was hit directly
    damage: Dict[str, int] = field(default_factory=dict)  # side -> HP lost


class Projectile:
    """A shell. Pure physics, knows nothing about the arena."""

    def __init__(self, x: float, y: float, angle: float, power: float,
                 owner: str = "player", gravity: float = 9.8):
        self.x, self.y = x, y
        rad = math.radians(angle)
        self.vx = power * math.cos(rad)
        self.vy = -power * math.sin(rad)      # screen y is inverted
        self.gravity = gravity
        self.owner = owner
        self.armed = False   # becomes True once it has left its own tank

    def step(self, dt: float) -> None:
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += self.gravity * dt

    @property
    def position(self) -> Point:
        return (self.x, self.y)


class Explosion:
    """Damage area + animation timer. Damage falls off linearly with distance."""

    def __init__(self, x: float, y: float, max_radius: float = 60,
                 max_damage: int = 60, duration: int = 30):
        self.x, self.y = x, y
        self.max_radius, self.max_damage = max_radius, max_damage
        self.duration = duration
        self.timer = duration

    def calculate_damage(self, tank_pos: Point) -> int:
        dist = math.hypot(self.x - tank_pos[0], self.y - tank_pos[1])
        if dist > self.max_radius:
            return 0
        return int(self.max_damage * (1 - dist / self.max_radius))

    def update(self) -> None:
        self.timer -= 1

    @property
    def finished(self) -> bool:
        return self.timer <= 0


# --------------------------------------------------------------------------- #
# Tanks
# --------------------------------------------------------------------------- #
class Tank:
    """Base tank. (x, y) is the bottom-centre of the hull (touches the ground)."""
    side = "tank"
    color = (200, 200, 200)

    def __init__(self, x: float, y: float, width: int = 40, height: int = 20,
                 max_hp: int = 100, barrel_length: int = 30):
        self.x, self.y = x, y
        self.width, self.height = width, height
        self.max_hp = self.hp = max_hp
        self.barrel_length = barrel_length
        self.barrel_angle = 45.0
        self.tilt = 0.0                          # hull tilt on slopes (degrees, for drawing)
        self.slide_target: Optional[float] = None  # knockback destination (x)

    # geometry ---------------------------------------------------------------
    @property
    def center(self) -> Point:
        return (self.x, self.y - self.height / 2)

    @property
    def rect(self) -> Tuple[float, float, float, float]:
        """(left, top, width, height) - handy for drawing."""
        return (self.x - self.width / 2, self.y - self.height, self.width, self.height)

    def contains(self, px: float, py: float) -> bool:
        return (self.x - self.width / 2 <= px <= self.x + self.width / 2
                and self.y - self.height <= py <= self.y)

    @property
    def barrel_origin(self) -> Point:
        return (self.x, self.y - self.height)

    def get_barrel_end(self, angle: Optional[float] = None,
                       length: Optional[float] = None) -> Point:
        angle = self.barrel_angle if angle is None else angle
        length = self.barrel_length if length is None else length
        rad = math.radians(angle)
        ox, oy = self.barrel_origin
        return (ox + length * math.cos(rad), oy - length * math.sin(rad))

    # state ------------------------------------------------------------------
    def take_damage(self, damage: int) -> None:
        self.hp = max(0, self.hp - damage)

    def is_alive(self) -> bool:
        return self.hp > 0

    # shooting ---------------------------------------------------------------
    def make_projectile(self, angle: float, power: float,
                        gravity: float = 9.8) -> Projectile:
        """Create a shell WITHOUT changing the tank (used by previews / AI)."""
        x, y = self.get_barrel_end(angle)
        return Projectile(x, y, angle, power, owner=self.side, gravity=gravity)

    def fire(self, angle: float, power: float, gravity: float = 9.8) -> Projectile:
        self.barrel_angle = angle
        return self.make_projectile(angle, power, gravity)


class PlayerTank(Tank):
    side = "player"
    color = (66, 135, 245)


class AITank(Tank):
    """Computer opponent.

    Strategy: pick a few random firing angles, solve the power for each with a
    binary search on the REAL physics simulation, keep the most accurate one,
    then add an aiming error that depends on the difficulty and shrinks with
    every shot in the round (the bot 'adjusts' after missing).
    """
    side = "ai"
    color = (245, 66, 66)

    DIFFICULTY = {              # max error (uniform +-), degrees / power units
        "easy":   {"angle_error": 10.0, "power_error": 12.0},
        "normal": {"angle_error": 4.5, "power_error": 5.0},
        "hard":   {"angle_error": 2.0, "power_error": 2.5},
    }

    def __init__(self, x, y, difficulty: str = "normal", **kwargs):
        super().__init__(x, y, **kwargs)
        self.difficulty = difficulty if difficulty in self.DIFFICULTY else "normal"
        self.barrel_angle = 135.0
        self.shots_fired = 0

    def choose_move(self, last_impact: Optional[ImpactEvent],
                    zone: Tuple[float, float], budget: float,
                    rng: random.Random) -> Optional[float]:
        """Return an x to drive to, or None to stay. The bot dodges when the
        last enemy shell landed close, and sometimes repositions at random."""
        in_danger = (last_impact is not None and last_impact.owner == "player"
                     and abs(last_impact.x - self.x) < 160)
        if not in_danger and rng.random() > 0.35:
            return None
        distance = rng.uniform(40, budget)
        direction = rng.choice((-1, 1))
        lo, hi = zone
        new_x = min(max(self.x + direction * distance, lo), hi)
        if abs(new_x - self.x) < 20:                      # blocked by the zone edge
            new_x = min(max(self.x - direction * distance, lo), hi)
        return None if abs(new_x - self.x) < 20 else new_x

    def choose_shot(self, target: Tank,
                    simulate: Callable[..., ImpactEvent],
                    max_power: float, rng: random.Random) -> Tuple[int, int]:
        """Search the shot space on the real physics (terrain and obstacles
        included): coarse scan over a few random angles and all powers, then a
        fine refinement around the best candidate."""
        shoots_left = target.x < self.x
        tx, ty = target.center

        def miss(angle, power, fast):
            ev = simulate(angle, power, fast)
            return math.hypot(ev.x - tx, ev.y - ty)

        best_d, best_angle, best_power = float("inf"), 90.0, max_power / 2
        for elevation in rng.sample(range(20, 85, 4), 7):
            angle = 180 - elevation if shoots_left else elevation
            for power in range(30, int(max_power) + 1, 5):
                d = miss(angle, power, True)
                if d < best_d:
                    best_d, best_angle, best_power = d, angle, power
            if best_d < 12:
                break

        # refine with the exact (fine-step) simulation
        refined = best_power
        best_d = miss(best_angle, best_power, False)
        for k in range(-10, 11):
            p = best_power + k * 0.5
            if 5 <= p <= max_power:
                d = miss(best_angle, p, False)
                if d < best_d:
                    best_d, refined = d, p

        cfg = self.DIFFICULTY[self.difficulty]
        shrink = 0.8 ** self.shots_fired      # the bot corrects itself over time
        angle = best_angle + rng.uniform(-1, 1) * cfg["angle_error"] * shrink
        power = refined + rng.uniform(-1, 1) * cfg["power_error"] * shrink
        self.shots_fired += 1
        return (int(round(max(0, min(180, angle)))),
                int(round(max(5, min(max_power, power)))))


# --------------------------------------------------------------------------- #
# Game
# --------------------------------------------------------------------------- #
class TanksGame:
    """Owns the whole match: tanks, projectile, turns, rounds, score.

    Typical frame flow used by the window:
        fire_player()/fire_ai()  -> update_projectile() each frame until it
        returns an ImpactEvent  -> finish_turn() -> (round result | None)
        -> start_next_round()   -> ... -> is_match_finished() -> get_match_result()
    """

    def __init__(self, arena_width: int = 1280, arena_height: int = 720,
                 config: Optional[GameConfig] = None, seed: Optional[int] = None):
        self.arena_width = arena_width
        self.arena_height = arena_height
        self.config = config or GameConfig()
        self.rng = random.Random(seed)
        self.maps: List[GameMap] = build_maps(
            arena_width, arena_height, self.config.ground_height,
            self.config.spawn_margin)
        self.current_map: GameMap = self.maps[0]
        self._map_deck: List[GameMap] = []

        self.wins = self.loses = self.draws = 0
        self.score = 0
        self.rounds_played = 0
        self.round_results: List[str] = []      # "W" / "D" / "L" per finished round
        self.explosions: List[Explosion] = []
        self.last_ai_shot: Optional[Tuple[int, int]] = None
        self.last_impact: Optional[ImpactEvent] = None
        self.reset_round()

    # ---- round setup -------------------------------------------------------
    def _pick_map(self) -> GameMap:
        """'shuffle': a random order where no map repeats until all were used
        (a Best-of-5 therefore plays all 5 maps). 'random': plain random."""
        if self.config.map_mode == "random" or len(self.maps) == 1:
            return self.rng.choice(self.maps)
        if not self._map_deck:
            self._map_deck = self.maps[:]
            self.rng.shuffle(self._map_deck)
            if self._map_deck[-1] is self.current_map:      # no back-to-back repeat
                self._map_deck[0], self._map_deck[-1] = self._map_deck[-1], self._map_deck[0]
        return self._map_deck.pop()

    def reset_round(self) -> None:
        cfg = self.config
        self.current_map = self._pick_map()
        m = self.current_map
        self.player_tank = PlayerTank(m.player_x, m.terrain_y(m.player_x),
                                      max_hp=cfg.tank_hp)
        self.ai_tank = AITank(m.ai_x, m.terrain_y(m.ai_x),
                              difficulty=cfg.ai_difficulty, max_hp=cfg.tank_hp)
        self.active_projectile: Optional[Projectile] = None
        self.turns_taken = 0
        self.move_left = float(cfg.move_budget)
        self.ai_move_target: Optional[float] = None
        self.last_impact = None
        self._place_tank(self.player_tank, m.player_x)
        self._place_tank(self.ai_tank, m.ai_x)
        # the shooter alternates every round: player, bot, player, ...
        self.turn = "player" if self.rounds_played % 2 == 0 else "ai"

    def start_next_round(self) -> None:
        if not self.is_match_finished():
            self.reset_round()

    @property
    def round_number(self) -> int:
        return min(self.rounds_played + 1, self.config.max_rounds)

    # ---- movement ----------------------------------------------------------
    def zone_for(self, tank: Tank) -> Tuple[float, float]:
        m = self.current_map
        return m.player_zone if tank.side == "player" else m.ai_zone

    def _place_tank(self, tank: Tank, x: float) -> None:
        """Put the tank at column x, resting on the terrain (and tilt it)."""
        m = self.current_map
        tank.x = x
        tank.y = m.terrain_y(x)
        half = tank.width / 2
        tank.tilt = math.degrees(math.atan2(m.terrain_y(x - half) - m.terrain_y(x + half),
                                            tank.width))

    def _try_step(self, tank: Tank, direction: int) -> float:
        """Drive one step. Returns the distance moved (0 if blocked)."""
        lo, hi = self.zone_for(tank)
        new_x = min(max(tank.x + direction * self.config.move_speed, lo), hi)
        if new_x == tank.x:
            return 0.0                                   # edge of the allowed range
        m = self.current_map
        if abs(m.terrain_y(new_x) - m.terrain_y(tank.x)) > self.config.max_climb:
            return 0.0                                   # too steep
        moved = abs(new_x - tank.x)
        self._place_tank(tank, new_x)
        return moved

    def move_player(self, direction: int) -> bool:
        """Drive the player's tank one step (-1 = left, +1 = right)."""
        if (self.turn != "player" or self.active_projectile or self.move_left <= 0
                or not self.player_tank.is_alive() or self.player_tank.slide_target is not None):
            return False
        moved = self._try_step(self.player_tank, direction)
        self.move_left -= moved
        return moved > 0

    def plan_ai_move(self) -> bool:
        """Let the bot decide whether to reposition before shooting."""
        target = self.ai_tank.choose_move(self.last_impact, self.ai_tank_zone(),
                                          self.config.move_budget, self.rng)
        self.ai_move_target = target
        return target is not None

    def ai_tank_zone(self) -> Tuple[float, float]:
        return self.zone_for(self.ai_tank)

    def advance_ai_move(self) -> bool:
        """One driving step towards the planned x. True while still moving."""
        if self.ai_move_target is None:
            return False
        tank = self.ai_tank
        direction = 1 if self.ai_move_target > tank.x else -1
        if abs(self.ai_move_target - tank.x) < self.config.move_speed \
                or self._try_step(tank, direction) == 0:
            self.ai_move_target = None
            return False
        return True

    def _knockback(self, tank: Tank, explosion: Explosion, damage: int) -> None:
        """A damaged tank is shoved away from the blast, so the opponent's
        next shot needs a different angle / power."""
        cfg = self.config
        away = 1 if tank.x > explosion.x else -1 if tank.x < explosion.x \
            else (-1 if tank.side == "player" else 1)
        push = min(cfg.knockback_max, damage * cfg.knockback_per_damage)
        lo, hi = self.zone_for(tank)
        tank.slide_target = min(max(tank.x + away * push, lo), hi)

    def update_motion(self) -> None:
        """Advance knockback slides (call once per frame)."""
        for tank in (self.player_tank, self.ai_tank):
            if tank.slide_target is None:
                continue
            dx = tank.slide_target - tank.x
            step = min(abs(dx), self.config.knockback_speed)
            self._place_tank(tank, tank.x + (step if dx > 0 else -step))
            if abs(tank.slide_target - tank.x) < 0.01:
                tank.slide_target = None

    # ---- shooting ----------------------------------------------------------
    def fire_player(self, angle: float, power: float) -> bool:
        if self.turn != "player" or self.active_projectile \
                or not self.player_tank.is_alive():
            return False
        angle = max(0, min(180, angle))
        power = max(0, min(self.config.max_power, power))
        self.active_projectile = self.player_tank.fire(angle, power, self.config.gravity)
        return True

    def fire_ai(self) -> bool:
        if self.turn != "ai" or self.active_projectile or not self.ai_tank.is_alive():
            return False
        angle, power = self.ai_tank.choose_shot(
            self.player_tank,
            lambda a, p, fast=False: self.simulate_shot(self.ai_tank, a, p, fast),
            self.config.max_power, self.rng)
        self.last_ai_shot = (angle, power)
        self.active_projectile = self.ai_tank.fire(angle, power, self.config.gravity)
        return True

    # ---- physics / collisions ---------------------------------------------
    def _advance(self, p: Projectile, dt: Optional[float] = None) -> Optional[ImpactEvent]:
        """One physics sub-step. Returns an ImpactEvent when the shell stops."""
        cfg = self.config
        p.step(dt or cfg.time_step / cfg.physics_substeps)

        for tank in (self.player_tank, self.ai_tank):
            inside = tank.contains(p.x, p.y)
            if tank.side == p.owner and not p.armed:
                if not inside:          # shell has cleared its own tank
                    p.armed = True
                continue
            if inside:
                return ImpactEvent(p.x, p.y, "tank", p.owner, tank.side)

        if p.x <= 0 or p.x >= self.arena_width:
            x = 0 if p.x <= 0 else self.arena_width
            return ImpactEvent(x, p.y, "out", p.owner)
        m = self.current_map
        if m.obstacle_at(p.x, p.y):
            return ImpactEvent(p.x, p.y, "obstacle", p.owner)
        ground = m.terrain_y(p.x)
        if p.y >= ground:
            return ImpactEvent(p.x, ground, "ground", p.owner)
        return None

    def simulate_shot(self, shooter: Tank, angle: float, power: float,
                      fast: bool = False) -> ImpactEvent:
        """Dry run of a shot (no state is changed). `fast` uses a 4x coarser
        time step - good enough for the AI's search, not for the real shot."""
        p = shooter.make_projectile(angle, power, self.config.gravity)
        dt = self.config.time_step if fast else None
        for _ in range(100_000):
            event = self._advance(p, dt)
            if event:
                return event
        return ImpactEvent(p.x, p.y, "out", shooter.side)

    def preview_trajectory(self, angle: float, power: float,
                           shooter: Optional[Tank] = None) -> List[Point]:
        """Aim assistant: dots along the first third of the flight path."""
        cfg = self.config
        shooter = shooter or self.player_tank
        p = shooter.make_projectile(angle, power, cfg.gravity)
        points: List[Point] = [p.position]
        for _ in range(100_000):
            event = self._advance(p)
            points.append(p.position)
            if event:
                break
        visible = points[: max(1, int(len(points) * cfg.preview_fraction))]
        return visible[:: max(1, cfg.preview_dot_spacing)]

    def update_projectile(self) -> Optional[ImpactEvent]:
        """Advance the active shell one frame. Returns the ImpactEvent on landing."""
        p = self.active_projectile
        if p is None:
            return None
        for _ in range(self.config.physics_substeps):
            event = self._advance(p)
            if event:
                return self._resolve_impact(event)
        return None

    def _resolve_impact(self, event: ImpactEvent) -> ImpactEvent:
        cfg = self.config
        if event.kind != "out":
            explosion = Explosion(event.x, event.y, cfg.explosion_radius,
                                  cfg.explosion_max_damage, cfg.explosion_duration)
            self.explosions.append(explosion)
            for tank in (self.player_tank, self.ai_tank):   # friendly fire counts
                dmg = explosion.calculate_damage(tank.center)
                if dmg:
                    tank.take_damage(dmg)
                    event.damage[tank.side] = dmg
                    if tank.is_alive():
                        self._knockback(tank, explosion, dmg)
        self.active_projectile = None
        self.last_impact = event
        return event

    def update_explosions(self) -> None:
        for e in self.explosions:
            e.update()
        self.explosions = [e for e in self.explosions if not e.finished]

    # ---- turns & rounds ----------------------------------------------------
    def finish_turn(self) -> Optional[str]:
        """Call after an impact. Returns the round result text if the round is
        over (and scores it), otherwise hands the turn to the other tank."""
        self.turns_taken += 1
        both_alive = self.player_tank.is_alive() and self.ai_tank.is_alive()
        turn_limit = self.turns_taken >= 2 * self.config.max_turns_per_tank
        if not both_alive or turn_limit:
            return self.evaluate_round()
        self.turn = "ai" if self.turn == "player" else "player"
        self.move_left = float(self.config.move_budget)
        return None

    def evaluate_round(self) -> str:
        cfg = self.config
        player_alive = self.player_tank.is_alive()
        ai_alive = self.ai_tank.is_alive()

        if player_alive and not ai_alive:
            self.wins += 1
            self.score += cfg.points_win
            text = "YOU WIN"
            self.round_results.append("W")
        elif ai_alive and not player_alive:
            self.loses += 1
            self.score += cfg.points_lose
            text = "BOT WINS"
            self.round_results.append("L")
        else:                                  # both dead, or turn limit reached
            self.draws += 1
            self.score += cfg.points_draw
            text = "DRAW"
            self.round_results.append("D")
        self.rounds_played += 1
        return text

    # ---- match -------------------------------------------------------------
    def is_match_finished(self) -> bool:
        cfg = self.config
        return (self.wins >= cfg.rounds_to_win or self.loses >= cfg.rounds_to_win
                or self.rounds_played >= cfg.max_rounds)

    def get_match_result(self) -> dict:
        """Exactly the format the launcher / DatabaseManager expect."""
        if self.wins > self.loses:
            result = "win"
        elif self.loses > self.wins:
            result = "lose"
        else:
            result = self.config.tie_result
        return {
            "result": result,
            "score": min(self.score, self.config.max_score),
            "details": {"wins": self.wins, "draws": self.draws, "loses": self.loses},
        }