"""Tanks vs AI - map definitions (pure data + geometry, NO pygame).

A map is described by a MapSpec (a blueprint made of fractions of the arena
size, so it works for any arena width/height) and built into a GameMap that
the game queries for collisions:

    game_map.terrain_y(x)        -> screen y of the ground surface at column x
    game_map.obstacle_at(x, y)   -> True if the point is inside an obstacle

To add a map: append a MapSpec to DEFAULT_MAP_SPECS. Nothing else changes.
Coordinates are pygame style (y grows downward).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Tuple

Rect = Tuple[float, float, float, float]      # left, top, width, height
Color = Tuple[int, int, int]


@dataclass(frozen=True)
class ObstacleSpec:
    """kind='wall'    : pillar that rises from the terrain (height = its height)
       kind='platform': floating slab, `elevation` px above the base floor."""
    kind: str
    x: float              # centre, as a fraction of the arena width
    width: int
    height: int
    elevation: int = 0


@dataclass(frozen=True)
class MapSpec:
    name: str
    # control points (x fraction, terrain height in px above the arena bottom)
    terrain: Tuple[Tuple[float, int], ...]
    obstacles: Tuple[ObstacleSpec, ...] = ()
    sky_color: Color = (27, 40, 56)
    ground_color: Color = (80, 80, 80)
    obstacle_color: Color = (140, 120, 100)
    # x-range (fractions of the arena width) each tank may drive within
    player_zone: Tuple[float, float] = (0.04, 0.24)
    ai_zone: Tuple[float, float] = (0.76, 0.96)

    def build(self, width: int, height: int, min_height: int,
              spawn_margin: int = 100, pad_half_width: int = 30) -> "GameMap":
        # 1) smooth terrain from control points (cosine interpolation)
        ys: List[float] = []
        for xi in range(width + 1):
            xf = xi / width
            h = self._height_at(xf)
            ys.append(height - max(h, min_height))

        # 2) flat landing pads so the tanks sit level
        pz = (int(self.player_zone[0] * width), int(self.player_zone[1] * width))
        az = (int(self.ai_zone[0] * width), int(self.ai_zone[1] * width))
        player_x = min(max(spawn_margin, pz[0]), pz[1])
        ai_x = min(max(width - spawn_margin, az[0]), az[1])
        for sx in (player_x, ai_x):
            base = ys[sx]
            for i in range(max(0, sx - pad_half_width), min(width, sx + pad_half_width) + 1):
                ys[i] = base

        # 3) obstacles -> rectangles
        rects: List[Rect] = []
        for o in self.obstacles:
            left = int(o.x * width - o.width / 2)
            right = left + o.width
            if o.kind == "wall":
                top = min(ys[max(0, left):min(width, right) + 1]) - o.height
                rects.append((left, top, o.width, height - top))   # reaches the bottom
            else:  # platform
                top = height - min_height - o.elevation - o.height
                rects.append((left, top, o.width, o.height))

        return GameMap(self.name, width, height, ys, rects, player_x, ai_x,
                       self.sky_color, self.ground_color, self.obstacle_color,
                       pz, az)

    def _height_at(self, xf: float) -> float:
        pts = self.terrain
        if xf <= pts[0][0]:
            return pts[0][1]
        for (x0, h0), (x1, h1) in zip(pts, pts[1:]):
            if x0 <= xf <= x1:
                t = (xf - x0) / (x1 - x0) if x1 > x0 else 0.0
                s = (1 - math.cos(math.pi * t)) / 2
                return h0 + (h1 - h0) * s
        return pts[-1][1]


class GameMap:
    """A built map: terrain height per pixel column + obstacle rectangles."""

    def __init__(self, name, width, height, ys, obstacles, player_x, ai_x,
                 sky_color, ground_color, obstacle_color,
                 player_zone=(0, 0), ai_zone=(0, 0)):
        self.name = name
        self.width, self.height = width, height
        self._ys = ys
        self.obstacles: List[Rect] = obstacles
        self.player_x, self.ai_x = player_x, ai_x
        self.sky_color, self.ground_color = sky_color, ground_color
        self.obstacle_color = obstacle_color
        self.player_zone, self.ai_zone = player_zone, ai_zone   # px, tank centre

    def terrain_y(self, x: float) -> float:
        i = int(x)
        return self._ys[0 if i < 0 else self.width if i > self.width else i]

    def obstacle_at(self, x: float, y: float) -> bool:
        for left, top, w, h in self.obstacles:
            if left <= x <= left + w and top <= y <= top + h:
                return True
        return False

    def surface_points(self, step: int = 4) -> List[Tuple[float, float]]:
        """Polyline of the ground surface (for drawing)."""
        pts = [(x, self._ys[x]) for x in range(0, self.width + 1, step)]
        if pts[-1][0] != self.width:
            pts.append((self.width, self._ys[self.width]))
        return pts


# --------------------------------------------------------------------------- #
# The five built-in maps (1280x720 reference; everything scales with the arena)
# --------------------------------------------------------------------------- #
DEFAULT_MAP_SPECS: Tuple[MapSpec, ...] = (
    MapSpec(
        "Central Hill",
        terrain=((0, 60), (0.18, 60), (0.35, 130), (0.5, 380),
                 (0.65, 110), (0.82, 60), (1, 60)),
        obstacles=(ObstacleSpec("wall", 0.28, 32, 45),
                   ObstacleSpec("wall", 0.72, 32, 45)),
        sky_color=(27, 40, 56), ground_color=(84, 110, 70),
    ),
    MapSpec(
        "Twin Peaks",
        terrain=((0, 60), (0.15, 70), (0.3, 330), (0.42, 90), (0.5, 70),
                 (0.58, 90), (0.7, 330), (0.85, 70), (1, 60)),
        obstacles=(ObstacleSpec("wall", 0.5, 30, 80),),
        sky_color=(44, 36, 62), ground_color=(110, 90, 70),
        player_zone=(0.04, 0.20), ai_zone=(0.80, 0.96),
    ),
    MapSpec(
        "Sky Valley",
        terrain=((0, 200), (0.12, 200), (0.3, 70), (0.5, 50),
                 (0.7, 70), (0.88, 200), (1, 200)),
        obstacles=(ObstacleSpec("platform", 0.5, 180, 22, elevation=230),),
        sky_color=(30, 52, 70), ground_color=(96, 96, 108),
        obstacle_color=(170, 170, 190),
    ),
    MapSpec(
        "Fortress",
        terrain=((0, 50), (0.2, 50), (0.3, 120), (0.45, 120), (0.5, 50),
                 (0.55, 120), (0.7, 120), (0.8, 50), (1, 50)),
        obstacles=(ObstacleSpec("wall", 0.5, 36, 330),),
        sky_color=(52, 34, 34), ground_color=(120, 84, 70),
        obstacle_color=(150, 150, 150),
    ),
    MapSpec(
        "Broken Ridge",
        terrain=((0, 90), (0.1, 90), (0.2, 160), (0.3, 60), (0.4, 60),
                 (0.5, 280), (0.6, 60), (0.7, 60), (0.8, 160), (0.9, 90), (1, 90)),
        obstacles=(ObstacleSpec("platform", 0.35, 110, 20, elevation=250),
                   ObstacleSpec("platform", 0.65, 110, 20, elevation=250)),
        sky_color=(24, 48, 52), ground_color=(70, 100, 100),
        obstacle_color=(190, 170, 120),
    ),
)


def build_maps(width: int, height: int, min_height: int, spawn_margin: int = 100,
               specs: Tuple[MapSpec, ...] = DEFAULT_MAP_SPECS) -> List[GameMap]:
    return [s.build(width, height, min_height, spawn_margin) for s in specs]