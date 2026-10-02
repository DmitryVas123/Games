from __future__ import annotations

import math
import random
from enum import Enum, auto

import pygame

try:                                   # project layout: Games/games/tanks.py
    from GUI.games.tanks import TanksGame, GameConfig
except ImportError:                    # fallback when run next to tanks.py
    from .tanks import TanksGame, GameConfig

# ------------------------------------------------------------------ palette --
WHITE = (255, 255, 255)
TEXT_DIM = (170, 178, 192)
BLUE = (88, 160, 255)
RED = (255, 98, 98)
GREEN = (84, 214, 120)
AMBER = (255, 205, 90)


def shade(color, f):
    return tuple(max(0, min(255, int(c * f))) for c in color[:3])


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


class GameState(Enum):
    PLAYER_AIMING = auto()
    AI_THINKING = auto()
    AI_MOVING = auto()
    PROJECTILE_FLYING = auto()
    IMPACT_PAUSE = auto()
    ROUND_SUMMARY = auto()
    MATCH_OVER = auto()


class TanksWindow:
    FPS = 60
    AI_THINK_FRAMES = 50
    IMPACT_PAUSE_FRAMES = 55
    SUMMARY_FRAMES = 130

    def __init__(self, on_match_finished=None, username: str = "Player1",
                 arena_width: int = 1280, arena_height: int = 720,
                 config: GameConfig | None = None):
        pygame.init()
        self.username = username
        self.on_match_finished = on_match_finished
        self.width, self.height = arena_width, arena_height

        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Tanks vs AI")
        self.clock = pygame.time.Clock()
        self.world = pygame.Surface((self.width, self.height))   # shaken layer
        self.f_s = pygame.font.SysFont("Arial", 15)
        self.f_m = pygame.font.SysFont("Arial", 21, bold=True)
        self.f_l = pygame.font.SysFont("Arial", 34, bold=True)
        self.f_xl = pygame.font.SysFont("Arial", 58, bold=True)
        pygame.key.set_repeat(250, 35)

        self.game = TanksGame(self.width, self.height, config)
        self.fx_rng = random.Random()
        self._map_cache: dict = {}
        self._sprite_cache: dict = {}
        self.particles: list = []
        self.floaters: list = []
        self.trail: list = []
        self.shake = 0
        self.frame = 0
        self._prev_x = {"player": self.game.player_tank.x, "ai": self.game.ai_tank.x}

        self.angle = 45
        self.power = 100
        self.timer = 0
        self.message = ""
        self.summary_text = ""
        self.state = GameState.PLAYER_AIMING
        self._begin_turn()

    # ------------------------------------------------------------------ loop
    def run(self):
        """Blocks until the window is closed. Returns the result dict if the
        match was finished (and calls on_match_finished with it)."""
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    if self.on_match_finished:
                        self.on_match_finished(None)
                    return None
                elif self.state == GameState.MATCH_OVER:
                    if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                        running = False
                else:
                    self.handle_input(event)
            self.update()
            self.draw()
            self.clock.tick(self.FPS)

        result = self.game.get_match_result() if self.state == GameState.MATCH_OVER else None
        pygame.quit()
        if result and self.on_match_finished:
            self.on_match_finished(result)
        return result

    # ----------------------------------------------------------------- input
    def handle_input(self, event):
        if self.state != GameState.PLAYER_AIMING or event.type != pygame.KEYDOWN:
            return
        step = 5 if event.mod & pygame.KMOD_SHIFT else 1
        max_power = self.game.config.max_power
        if event.key == pygame.K_LEFT:
            self.angle = min(180, self.angle + step)
        elif event.key == pygame.K_RIGHT:
            self.angle = max(0, self.angle - step)
        elif event.key == pygame.K_UP:
            self.power = min(max_power, self.power + step)
        elif event.key == pygame.K_DOWN:
            self.power = max(0, self.power - step)
        elif event.key == pygame.K_SPACE:
            if self.game.fire_player(self.angle, self.power):
                self.message = ""
                self.trail.clear()
                self.state = GameState.PROJECTILE_FLYING

    # ---------------------------------------------------------------- update
    def _begin_turn(self):
        if self.game.turn == "player":
            self.state = GameState.PLAYER_AIMING
        else:
            self.state = GameState.AI_THINKING
            self.timer = self.AI_THINK_FRAMES

    def update(self):
        g = self.game
        self.frame += 1
        g.update_explosions()
        g.update_motion()
        self._update_fx()

        if self.state == GameState.PLAYER_AIMING:
            g.player_tank.barrel_angle = self.angle
            keys = pygame.key.get_pressed()
            if keys[pygame.K_a]:
                g.move_player(-1)
            elif keys[pygame.K_d]:
                g.move_player(+1)

        elif self.state == GameState.AI_THINKING:
            self.timer -= 1
            if self.timer <= 0:
                if g.plan_ai_move():
                    self.state = GameState.AI_MOVING
                elif g.fire_ai():
                    self.trail.clear()
                    self.state = GameState.PROJECTILE_FLYING

        elif self.state == GameState.AI_MOVING:
            if not g.advance_ai_move() and g.ai_tank.slide_target is None:
                if g.fire_ai():
                    self.trail.clear()
                    self.state = GameState.PROJECTILE_FLYING

        elif self.state == GameState.PROJECTILE_FLYING:
            p = g.active_projectile
            if p:
                self.trail.append((p.x, p.y))
                del self.trail[:-18]
            impact = g.update_projectile()
            if impact:
                self._on_impact(impact)
                self.state = GameState.IMPACT_PAUSE
                self.timer = self.IMPACT_PAUSE_FRAMES

        elif self.state == GameState.IMPACT_PAUSE:
            self.timer -= 1
            if self.timer <= 0 and g.player_tank.slide_target is None \
                    and g.ai_tank.slide_target is None:
                round_result = g.finish_turn()
                if round_result:
                    self.summary_text = round_result
                    self.state = GameState.ROUND_SUMMARY
                    self.timer = self.SUMMARY_FRAMES
                else:
                    self._begin_turn()

        elif self.state == GameState.ROUND_SUMMARY:
            self.timer -= 1
            if self.timer <= 0:
                if g.is_match_finished():
                    self.state = GameState.MATCH_OVER
                else:
                    g.start_next_round()
                    self.message = ""
                    self.particles.clear()
                    self.trail.clear()
                    self._prev_x = {"player": g.player_tank.x, "ai": g.ai_tank.x}
                    self._begin_turn()

    def _on_impact(self, impact):
        g = self.game
        if impact.kind == "out":
            self.message = "Shot flew out of the arena"
            return
        parts = []
        if impact.damage.get("ai"):
            parts.append(f"Bot  -{impact.damage['ai']} HP")
        if impact.damage.get("player"):
            parts.append(f"You  -{impact.damage['player']} HP")
        self.message = "     ".join(parts) if parts else "Miss"
        for side, dmg in impact.damage.items():
            tank = g.player_tank if side == "player" else g.ai_tank
            self.floaters.append({"text": f"-{dmg}", "x": tank.x, "y": tank.y - 112,
                                  "life": 70, "color": RED if side == "player" else AMBER})
        self.shake = 14 if impact.damage else 6
        self._spawn_impact_fx(impact)

    # ------------------------------------------------------------- particles
    def _spawn(self, x, y, vx, vy, life, color, size, gravity=0.0, grow=0.0, kind="solid"):
        self.particles.append({"x": x, "y": y, "vx": vx, "vy": vy, "life": life,
                               "max": life, "color": color, "size": size,
                               "gravity": gravity, "grow": grow, "kind": kind})

    def _spawn_impact_fx(self, impact):
        m = self.game.current_map
        base = m.obstacle_color if impact.kind == "obstacle" else m.ground_color
        r = self.fx_rng
        for _ in range(28):
            a = r.uniform(math.pi * 0.08, math.pi * 0.92)
            sp = r.uniform(2.0, 7.5)
            self._spawn(impact.x, impact.y, math.cos(a) * sp, -math.sin(a) * sp,
                        r.randint(35, 70), shade(base, r.uniform(0.7, 1.3)),
                        r.uniform(2, 4.5), gravity=0.28)
        for _ in range(16):
            a = r.uniform(0, math.tau)
            sp = r.uniform(1.5, 6)
            self._spawn(impact.x, impact.y, math.cos(a) * sp, math.sin(a) * sp - 1,
                        r.randint(15, 32), r.choice(((255, 220, 110), (255, 160, 60))),
                        r.uniform(1.5, 3), gravity=0.12)
        for _ in range(9):
            self._spawn(impact.x + r.uniform(-14, 14), impact.y + r.uniform(-8, 8),
                        r.uniform(-0.6, 0.6), r.uniform(-1.3, -0.4),
                        r.randint(45, 80), (70, 70, 76), r.uniform(7, 12),
                        grow=0.35, kind="smoke")

    def _update_fx(self):
        g, r = self.game, self.fx_rng
        # dust behind driving / sliding tanks, smoke from wrecks
        for side, tank in (("player", g.player_tank), ("ai", g.ai_tank)):
            if abs(tank.x - self._prev_x[side]) > 0.2 and self.frame % 3 == 0:
                self._spawn(tank.x - (tank.x - self._prev_x[side]) * 6, tank.y - 2,
                            r.uniform(-0.3, 0.3), r.uniform(-0.6, -0.2), 28,
                            shade(g.current_map.ground_color, 1.3), 3.5, grow=0.12, kind="smoke")
            self._prev_x[side] = tank.x
            if not tank.is_alive() and r.random() < 0.12:
                self._spawn(tank.x + r.uniform(-8, 8), tank.y - 18, r.uniform(-0.2, 0.2),
                            r.uniform(-1.0, -0.5), 55, (60, 60, 64), 6, grow=0.3, kind="smoke")
        for p in self.particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vy"] += p["gravity"]
            p["size"] += p["grow"]
            p["life"] -= 1
        self.particles = [p for p in self.particles if p["life"] > 0]
        for f in self.floaters:
            f["y"] -= 0.9
            f["life"] -= 1
        self.floaters = [f for f in self.floaters if f["life"] > 0]
        if self.state != GameState.PROJECTILE_FLYING and self.trail:
            self.trail.pop(0)
        self.shake = max(0, self.shake - 1)

    # ------------------------------------------------------------------ draw
    def draw(self):
        g = self.game
        w = self.world
        w.blit(self._map_surface(g.current_map), (0, 0))

        if self.state == GameState.PLAYER_AIMING:
            self._draw_zone(w, g.player_tank)
        for tank in (g.ai_tank, g.player_tank):
            self._draw_tank(w, tank)
        self._draw_particles(w)
        self._draw_projectile(w)
        self._draw_explosions(w)
        if self.state == GameState.PLAYER_AIMING:
            self._draw_aim_assist(w)
        for tank, label, col in ((g.player_tank, "YOU", BLUE), (g.ai_tank, "BOT", RED)):
            self._draw_health(w, tank, label, col)

        off = (0, 0)
        if self.shake:
            s = self.shake / 2
            off = (self.fx_rng.uniform(-s, s), self.fx_rng.uniform(-s, s))
        self.screen.fill((0, 0, 0))
        self.screen.blit(w, off)

        self._draw_floaters()
        self._draw_hud()
        pygame.display.flip()

    # ---- map ---------------------------------------------------------------
    def _map_surface(self, m) -> pygame.Surface:
        """Sky, mountains, terrain and obstacles are static: draw once per map."""
        cached = self._map_cache.get(m.name)
        if cached is not None:
            return cached
        W, H = self.width, self.height
        rng = random.Random(m.name)
        surf = pygame.Surface((W, H))

        top, bot = shade(m.sky_color, 0.75), shade(m.sky_color, 1.7)
        for y in range(H):
            pygame.draw.line(surf, mix(top, bot, y / H), (0, y), (W, y))

        glow = pygame.Surface((W, H), pygame.SRCALPHA)
        for _ in range(55):                                   # stars
            pygame.draw.circle(glow, (255, 255, 255, rng.randint(70, 200)),
                               (rng.randint(0, W), rng.randint(0, int(H * 0.45))), rng.choice((1, 1, 2)))
        sx, sy, sr = rng.randint(int(W * .2), int(W * .8)), rng.randint(70, 140), rng.randint(28, 42)
        for k in range(5, 0, -1):                             # sun / moon with halo
            pygame.draw.circle(glow, (255, 240, 200, 16 * (6 - k)), (sx, sy), sr + k * 9)
        pygame.draw.circle(glow, (255, 244, 214, 255), (sx, sy), sr)
        for _ in range(5):                                    # clouds
            cx, cy = rng.randint(0, W), rng.randint(60, 220)
            for _ in range(5):
                pygame.draw.ellipse(glow, (255, 255, 255, 28),
                                    (cx + rng.randint(-60, 60), cy + rng.randint(-10, 10),
                                     rng.randint(90, 170), rng.randint(24, 40)))
        surf.blit(glow, (0, 0))

        for layer in range(2):                                # distant mountains
            ph1, ph2 = rng.uniform(0, 6), rng.uniform(0, 6)
            base = H * (0.60 + 0.07 * layer)
            pts = [(0, H)] + [(x, base - 60 - 55 * math.sin(x * 0.0042 + ph1)
                               - 28 * math.sin(x * 0.012 + ph2)) for x in range(0, W + 30, 30)] + [(W, H)]
            pygame.draw.polygon(surf, mix(bot, m.ground_color, 0.18 + 0.22 * layer), pts)

        # terrain: gradient clipped to the ground polygon
        pts = m.surface_points(2)
        poly = pts + [(W, H), (0, H)]
        grad = pygame.Surface((W, H), pygame.SRCALPHA)
        y0 = int(min(y for _, y in pts))
        light, dark = shade(m.ground_color, 1.25), shade(m.ground_color, 0.5)
        for y in range(y0, H):
            pygame.draw.line(grad, mix(light, dark, (y - y0) / max(1, H - y0)), (0, y), (W, y))
        mask = pygame.Surface((W, H), pygame.SRCALPHA)
        pygame.draw.polygon(mask, (255, 255, 255, 255), poly)
        grad.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        for _ in range(260):                                  # speckles
            x = rng.randint(0, W - 1)
            y = rng.randint(int(m.terrain_y(x)) + 12, H)
            pygame.draw.circle(grad, shade(m.ground_color, rng.uniform(0.45, 0.8)) + (255,),
                               (x, y), rng.choice((1, 2, 3)))
        grad.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        surf.blit(grad, (0, 0))
        pygame.draw.lines(surf, shade(m.ground_color, 0.4), False, [(x, y + 3) for x, y in pts], 10)
        pygame.draw.lines(surf, shade(m.ground_color, 1.55), False, pts, 6)

        for left, top_, ow, oh in m.obstacles:                # obstacles
            rect = pygame.Rect(left, top_, ow, oh)
            pygame.draw.rect(surf, m.obstacle_color, rect)
            line = shade(m.obstacle_color, 0.7)
            for row, y in enumerate(range(rect.top + 14, rect.bottom, 14)):
                pygame.draw.line(surf, line, (rect.left, y), (rect.right, y), 1)
                for x in range(rect.left + (10 if row % 2 else 24), rect.right, 28):
                    pygame.draw.line(surf, line, (x, y - 14), (x, y), 1)
            pygame.draw.rect(surf, shade(m.obstacle_color, 1.4), (rect.left, rect.top, ow, 4))
            pygame.draw.rect(surf, (25, 25, 30), rect, 2)

        self._map_cache[m.name] = surf
        return surf

    # ---- tanks -------------------------------------------------------------
    def _base_sprite(self, side, alive) -> pygame.Surface:
        color = {"player": (74, 140, 240), "ai": (232, 76, 76)}[side] if alive else (92, 92, 96)
        light, dark = shade(color, 1.3), shade(color, 0.6)
        s = pygame.Surface((44, 22), pygame.SRCALPHA)
        pygame.draw.rect(s, (36, 36, 42), (0, 13, 44, 9), border_radius=4)       # tracks
        for cx in (6, 15, 22, 29, 38):
            pygame.draw.circle(s, (86, 88, 98), (cx, 17), 3)
            pygame.draw.circle(s, (44, 44, 52), (cx, 17), 1)
        pygame.draw.rect(s, color, (4, 6, 36, 9), border_radius=3)               # hull
        pygame.draw.rect(s, light, (5, 6, 34, 3), border_radius=2)
        pygame.draw.rect(s, dark, (4, 13, 36, 2))
        pygame.draw.ellipse(s, color, (12, 0, 20, 12))                           # turret
        pygame.draw.arc(s, light, (13, 1, 18, 10), 0.5, 2.6, 2)
        pygame.draw.circle(s, dark, (22, 5), 3)
        return s

    def _tank_sprite(self, tank) -> pygame.Surface:
        key = (tank.side, tank.is_alive(), int(round(tank.tilt)))
        sprite = self._sprite_cache.get(key)
        if sprite is None:
            S = 40
            canvas = pygame.Surface((2 * S, 2 * S), pygame.SRCALPHA)
            canvas.blit(self._base_sprite(tank.side, tank.is_alive()), (S - 22, S - 22))
            sprite = pygame.transform.rotate(canvas, tank.tilt)   # pivot = bottom centre
            self._sprite_cache[key] = sprite
        return sprite

    def _draw_tank(self, surf, tank):
        # barrel first (turret overlaps its base)
        ox, oy = tank.barrel_origin
        ex, ey = tank.get_barrel_end()
        pygame.draw.line(surf, (24, 24, 30), (ox, oy + 2), (ex, ey + 2), 8)
        pygame.draw.line(surf, (176, 180, 190), (ox, oy + 2), (ex, ey + 2), 5)
        pygame.draw.circle(surf, (60, 62, 70), (int(ex), int(ey + 2)), 4)
        sprite = self._tank_sprite(tank)
        surf.blit(sprite, sprite.get_rect(center=(tank.x, tank.y)))

    def _draw_health(self, surf, tank, label, color):
        bar_w, bar_h = 70, 10
        x, y = int(tank.x - bar_w / 2), int(tank.y - 70)
        pct = tank.hp / tank.max_hp
        pygame.draw.rect(surf, (14, 16, 22), (x - 2, y - 2, bar_w + 4, bar_h + 4), border_radius=6)
        if pct > 0:
            col = GREEN if pct > 0.5 else AMBER if pct > 0.25 else RED
            pygame.draw.rect(surf, col, (x, y, max(4, int(bar_w * pct)), bar_h), border_radius=5)
        name = self.f_s.render(f"{label}  {tank.hp}", True, color)
        surf.blit(name, name.get_rect(midbottom=(tank.x, y - 4)))

    def _draw_zone(self, surf, tank):
        """Show the range the player may drive in."""
        m = self.game.current_map
        lo, hi = self.game.zone_for(tank)
        for x in range(int(lo), int(hi), 10):
            y = m.terrain_y(x)
            pygame.draw.line(surf, AMBER, (x, y - 3), (min(hi, x + 5), m.terrain_y(x + 5) - 3), 3)
        for x in (lo, hi):
            y = m.terrain_y(x)
            pygame.draw.line(surf, AMBER, (x, y), (x, y - 34), 3)
            pygame.draw.polygon(surf, AMBER, [(x, y - 34), (x + (14 if x == lo else -14), y - 28),
                                              (x, y - 22)])

    def _draw_aim_assist(self, surf):
        """Dots along the first third of the predicted flight path."""
        pts = self.game.preview_trajectory(self.angle, self.power)
        n = len(pts)
        for i, (x, y) in enumerate(pts):
            t = i / max(1, n - 1)
            r = 5 - int(2.5 * t)
            dot = pygame.Surface((r * 2 + 6, r * 2 + 6), pygame.SRCALPHA)
            c = r + 3
            pygame.draw.circle(dot, (255, 255, 255, int(70 * (1 - t))), (c, c), r + 3)
            pygame.draw.circle(dot, (255, 255, 255, int(235 - 130 * t)), (c, c), r)
            surf.blit(dot, (x - c, y - c))

    # ---- projectile / effects ----------------------------------------------
    def _draw_projectile(self, surf):
        for i, (x, y) in enumerate(self.trail):
            t = (i + 1) / max(1, len(self.trail))
            pygame.draw.circle(surf, mix((60, 60, 70), (255, 190, 90), t), (int(x), int(y)), max(1, int(4 * t)))
        p = self.game.active_projectile
        if p:
            pygame.draw.circle(surf, (255, 150, 60), (int(p.x), int(p.y)), 8, 2)
            pygame.draw.circle(surf, WHITE, (int(p.x), int(p.y)), 5)

    def _draw_explosions(self, surf):
        for e in self.game.explosions:
            prog = 1 - e.timer / e.duration
            r = max(2, int(e.max_radius * (1 - (1 - prog) ** 2)))
            alpha = int(255 * (1 - prog) ** 1.3)
            size = int(e.max_radius * 2 + 6)
            c = size // 2
            layer = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(layer, (255, 70, 30, alpha // 2), (c, c), r)
            pygame.draw.circle(layer, (255, 150, 40, alpha), (c, c), max(1, int(r * 0.72)))
            pygame.draw.circle(layer, (255, 240, 170, alpha), (c, c), max(1, int(r * 0.42)))
            surf.blit(layer, (e.x - c, e.y - c))

    def _draw_particles(self, surf):
        for p in self.particles:
            life = p["life"] / p["max"]
            if p["kind"] == "smoke":
                r = max(1, int(p["size"]))
                layer = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(layer, p["color"] + (int(120 * life),), (r, r), r)
                surf.blit(layer, (p["x"] - r, p["y"] - r))
            else:
                pygame.draw.circle(surf, p["color"], (int(p["x"]), int(p["y"])),
                                   max(1, int(p["size"] * (0.4 + 0.6 * life))))

    def _draw_floaters(self):
        for f in self.floaters:
            alpha = min(255, int(255 * f["life"] / 30))
            for color, dx in (((0, 0, 0), 2), (f["color"], 0)):
                t = self.f_l.render(f["text"], True, color)
                t.set_alpha(alpha)
                self.screen.blit(t, t.get_rect(center=(f["x"] + dx, f["y"] + dx)))

    # ---- HUD ---------------------------------------------------------------
    def _panel(self, rect, alpha=170, radius=14):
        rect = pygame.Rect(rect)
        s = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(s, (10, 14, 24, alpha), s.get_rect(), border_radius=radius)
        pygame.draw.rect(s, (255, 255, 255, 38), s.get_rect(), 1, border_radius=radius)
        self.screen.blit(s, rect.topleft)
        return rect

    def _text(self, text, font, color, pos, anchor="topleft"):
        surf = font.render(text, True, color)
        self.screen.blit(surf, surf.get_rect(**{anchor: pos}))

    def _bar(self, x, y, w, frac, color, h=12):
        pygame.draw.rect(self.screen, (30, 34, 46), (x, y, w, h), border_radius=6)
        if frac > 0:
            pygame.draw.rect(self.screen, color, (x, y, max(5, int(w * frac)), h), border_radius=6)

    def _draw_hud(self):
        g, cx = self.game, self.width // 2
        # --- top bar
        bar = pygame.Surface((self.width, 66), pygame.SRCALPHA)
        for y in range(66):
            pygame.draw.line(bar, (8, 10, 18, int(200 * (1 - y / 90))), (0, y), (self.width, y))
        self.screen.blit(bar, (0, 0))
        self._text("YOU", self.f_m, BLUE, (24, 8))
        self._text(f"{g.wins} won", self.f_s, TEXT_DIM, (24, 34))
        self._text("BOT", self.f_m, RED, (self.width - 24, 8), "topright")
        self._text(f"{g.loses} won", self.f_s, TEXT_DIM, (self.width - 24, 34), "topright")
        self._text(f"ROUND {g.round_number} / {g.config.max_rounds}", self.f_m, WHITE, (cx, 6), "midtop")
        for i in range(g.config.max_rounds):
            px, py = cx + (i - (g.config.max_rounds - 1) / 2) * 30, 46
            if i < len(g.round_results):
                col = {"W": GREEN, "L": RED, "D": AMBER}[g.round_results[i]]
                pygame.draw.circle(self.screen, col, (px, py), 8)
            else:
                active = i == len(g.round_results) and self.state != GameState.MATCH_OVER
                pygame.draw.circle(self.screen, WHITE if active else (80, 88, 104), (px, py), 8, 2)

        # --- info pill + turn banner
        info = f"{g.current_map.name}   ·   Score {g.score}"
        w = self.f_s.size(info)[0] + 32
        self._panel((cx - w // 2, 72, w, 26), 150, 13)
        self._text(info, self.f_s, TEXT_DIM, (cx, 85), "center")
        banner = {GameState.PLAYER_AIMING: ("YOUR TURN", BLUE),
                  GameState.AI_THINKING: ("BOT IS AIMING...", RED),
                  GameState.AI_MOVING: ("BOT IS MOVING...", RED)}.get(self.state)
        if banner:
            self._text(banner[0], self.f_m, banner[1], (cx, 106), "midtop")
        if self.message:
            self._text(self.message, self.f_l, (0, 0, 0), (cx + 2, 134 + 2), "midtop")
            self._text(self.message, self.f_l, AMBER, (cx, 134), "midtop")

        # --- control panel
        if self.state == GameState.PLAYER_AIMING:
            r = self._panel((self.width // 2 - 186, self.height - 150, 372, 138))
            rows = (("ANGLE", f"{self.angle}°", self.angle / 180, BLUE),
                    ("POWER", f"{self.power}", self.power / g.config.max_power, AMBER),
                    ("FUEL", f"{int(g.move_left)}", g.move_left / g.config.move_budget, GREEN))
            for i, (name, val, frac, col) in enumerate(rows):
                y = r.y + 14 + i * 29
                self._text(name, self.f_s, TEXT_DIM, (r.x + 18, y))
                self._bar(r.x + 92, y + 2, 190, frac, col)
                self._text(val, self.f_m, WHITE, (r.right - 18, y - 3), "topright")
            self._text("←/→ angle   ↑/↓ power   A/D drive   SPACE fire", self.f_s, TEXT_DIM,
                       (r.x + 18, r.bottom - 36))
            self._text("Hold Shift for steps of 5", self.f_s, (120, 128, 144), (r.x + 18, r.bottom - 20))

        # --- overlays
        if self.state == GameState.ROUND_SUMMARY:
            col = {"YOU WIN": GREEN, "BOT WINS": RED}.get(self.summary_text, AMBER)
            self._overlay(self.summary_text, col,
                          f"Round {g.rounds_played} of {g.config.max_rounds}   ·   Score {g.score}")
        elif self.state == GameState.MATCH_OVER:
            data = g.get_match_result()
            title, col = {"win": ("YOU WON THE MATCH!", GREEN),
                          "lose": ("YOU LOST THE MATCH", RED)}.get(data["result"], ("MATCH DRAWN", AMBER))
            d = data["details"]
            self._overlay(title, col, f"Wins {d['wins']}   Draws {d['draws']}   Losses {d['loses']}"
                                      f"   ·   Final score {data['score']}",
                          "Press any key to continue")

    def _overlay(self, title, color, sub, hint=None):
        dim = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 120))
        self.screen.blit(dim, (0, 0))
        r = self._panel((self.width // 2 - 290, self.height // 2 - 100, 580, 200 if hint else 170), 215, 20)
        pygame.draw.rect(self.screen, color, (r.x + 24, r.y, r.width - 48, 5), border_radius=3)
        self._text(title, self.f_xl, color, (r.centerx, r.y + 24), "midtop")
        self._text(sub, self.f_m, WHITE, (r.centerx, r.y + 106), "midtop")
        if hint:
            self._text(hint, self.f_s, TEXT_DIM, (r.centerx, r.y + 150), "midtop")


if __name__ == "__main__":
    def _print_result(data):
        print("--- MATCH FINISHED ---")
        print(data)

    TanksWindow(on_match_finished=_print_result).run()