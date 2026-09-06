"""
render/background.py — Pre-rendered static environment.

Built once at boot from the SAME geometry tables the simulation uses
(core.network), so lane markings, stop lines and zebra crossings line up
exactly with where the logic makes vehicles drive and halt:

  grass → sidewalks + kerbs → asphalt (+ per-pixel noise) → lane paint
  (dashed white separators, double-yellow centre for 4-lane arterials)
  → stop lines & zebra crossings at every signalised approach → medians
  → buildings, trees, street-light poles on the free blocks.

Decoration placement is deterministic (config.RNG_SEED_DECOR).
"""

import random

import numpy as np
import pygame as pg

import config as C
from config import HORR
from core import network
from core.network import ROADS, ROAD_LANES


class Environment:
    def __init__(self):
        self.rng = random.Random(C.RNG_SEED_DECOR)
        self.road_rects = [pg.Rect(network.road_rect(i))
                           for i in range(len(ROADS))]
        self.node_rects = [pg.Rect(r) for r in network.intersection_rects()]
        self.approaches = network.approach_geometry()
        self.streetlights = []     # (x, y) pole bases
        self.buildings = []        # (rect, body colour idx)
        self.trees = []            # (x, y, r)
        self.window_lights = []    # (x, y, w, h) lit at night
        self.zebras = []           # rects, exposed for pedestrians
        self.surface = self._build()

    # ---------------------------------------------------------------- build
    def _build(self):
        surf = pg.Surface((C.SCREEN_W, C.SCREEN_H))
        self._grass(surf)
        self._sidewalks(surf)
        self._asphalt(surf)
        self._lane_paint(surf)
        self._approach_paint(surf)
        self._decorate(surf)
        return surf

    def _grass(self, surf):
        surf.fill(C.COL_GRASS)
        rng = self.rng
        for _ in range(340):                       # mottled turf patches
            x, y = rng.randrange(C.SCREEN_W), rng.randrange(C.SCREEN_H)
            r = rng.randint(6, 26)
            pg.draw.circle(surf, C.COL_GRASS_DARK, (x, y), r)
        arr = pg.surfarray.pixels3d(surf)
        noise = (np.random.default_rng(C.RNG_SEED_DECOR)
                 .integers(-5, 6, arr.shape[:2]))[..., None]
        arr[...] = np.clip(arr.astype(np.int16) + noise, 0, 255)
        del arr

    def _sidewalks(self, surf):
        pads = [r.inflate(26, 26) for r in self.road_rects]
        pads += [r.inflate(26, 26) for r in self.node_rects]
        for p in pads:
            pg.draw.rect(surf, C.COL_SIDEWALK, p)
        for p in pads:                              # kerb edge highlight
            pg.draw.rect(surf, C.COL_SIDEWALK_EDGE, p, 2)
        # paving joints
        for r in self.road_rects:
            p = r.inflate(26, 26)
            if r.w >= r.h:
                for x in range(p.left, p.right, 26):
                    pg.draw.line(surf, C.COL_SIDEWALK_EDGE,
                                 (x, p.top), (x, p.top + 12))
                    pg.draw.line(surf, C.COL_SIDEWALK_EDGE,
                                 (x, p.bottom - 12), (x, p.bottom))
            else:
                for y in range(p.top, p.bottom, 26):
                    pg.draw.line(surf, C.COL_SIDEWALK_EDGE,
                                 (p.left, y), (p.left + 12, y))
                    pg.draw.line(surf, C.COL_SIDEWALK_EDGE,
                                 (p.right - 12, y), (p.right, y))

    def _asphalt(self, surf):
        tarmac = self.road_rects + self.node_rects
        for r in tarmac:
            pg.draw.rect(surf, C.COL_ASPHALT, r)
        # kerb line where asphalt meets sidewalk
        for r in self.road_rects:
            pg.draw.rect(surf, C.COL_KERB, r, 1)
        # subtle grain
        rng = np.random.default_rng(C.RNG_SEED_DECOR + 1)
        arr = pg.surfarray.pixels3d(surf)
        for r in tarmac:
            sub = arr[r.left:r.right, r.top:r.bottom]
            if sub.size == 0:
                continue
            noise = rng.integers(-C.COL_ASPHALT_VAR, C.COL_ASPHALT_VAR + 1,
                                 sub.shape[:2])[..., None]
            sub[...] = np.clip(sub.astype(np.int16) + noise, 0, 255)
        del arr

    # ------------------------------------------------------------ lane paint
    def _dash(self, surf, colour, a, b, along_x, dash=14, gap=12, width=2):
        if along_x:
            x = a[0]
            while x < b[0]:
                pg.draw.line(surf, colour, (x, a[1]),
                             (min(x + dash, b[0]), a[1]), width)
                x += dash + gap
        else:
            y = a[1]
            while y < b[1]:
                pg.draw.line(surf, colour, (a[0], y),
                             (a[0], min(y + dash, b[1])), width)
                y += dash + gap

    def _lane_paint(self, surf):
        for rid, road in enumerate(ROADS):
            lanes = ROAD_LANES[rid]
            l0, l1 = lanes[0]
            if road.symm == HORR:
                # edge lines
                pg.draw.line(surf, C.COL_LANE_WHITE,
                             (l0, road.w_start + 2), (l1, road.w_start + 2), 2)
                pg.draw.line(surf, C.COL_LANE_WHITE,
                             (l0, road.w_end - 3), (l1, road.w_end - 3), 2)
                if road.lane == 4:
                    # dashed separators inside each carriageway
                    y_a = lanes[1][1]
                    y_b = lanes[3][1]
                    self._dash(surf, C.COL_LANE_WHITE, (l0, y_a), (l1, y_a), True)
                    self._dash(surf, C.COL_LANE_WHITE, (l0, y_b), (l1, y_b), True)
                    # raised median band + double yellow centre
                    m = road.w_middle
                    pg.draw.line(surf, C.COL_MEDIAN, (l0, m), (l1, m), 4)
                    pg.draw.line(surf, C.COL_LANE_YELLOW, (l0, m - 3), (l1, m - 3), 2)
                    pg.draw.line(surf, C.COL_LANE_YELLOW, (l0, m + 3), (l1, m + 3), 2)
                else:
                    m = road.w_middle
                    pg.draw.line(surf, C.COL_LANE_YELLOW, (l0, m - 2), (l1, m - 2), 2)
                    pg.draw.line(surf, C.COL_LANE_YELLOW, (l0, m + 2), (l1, m + 2), 2)
            else:
                pg.draw.line(surf, C.COL_LANE_WHITE,
                             (road.w_start + 2, l0), (road.w_start + 2, l1), 2)
                pg.draw.line(surf, C.COL_LANE_WHITE,
                             (road.w_end - 3, l0), (road.w_end - 3, l1), 2)
                if road.lane == 4:
                    x_a = lanes[1][1]
                    x_b = lanes[3][1]
                    self._dash(surf, C.COL_LANE_WHITE, (x_a, l0), (x_a, l1), False)
                    self._dash(surf, C.COL_LANE_WHITE, (x_b, l0), (x_b, l1), False)
                    m = road.w_middle
                    pg.draw.line(surf, C.COL_MEDIAN, (m, l0), (m, l1), 4)
                    pg.draw.line(surf, C.COL_LANE_YELLOW, (m - 3, l0), (m - 3, l1), 2)
                    pg.draw.line(surf, C.COL_LANE_YELLOW, (m + 3, l0), (m + 3, l1), 2)
                else:
                    m = road.w_middle
                    pg.draw.line(surf, C.COL_LANE_YELLOW, (m - 2, l0), (m - 2, l1), 2)
                    pg.draw.line(surf, C.COL_LANE_YELLOW, (m + 2, l0), (m + 2, l1), 2)

    def _approach_paint(self, surf):
        """Stop line + zebra crossing at every signalised approach."""
        for (n, s), info in self.approaches.items():
            axis = info["axis"]
            if axis is None:
                continue
            orient, rid, road = axis
            stop = info["stop"]
            if orient == "h":
                y0, y1 = road.w_start + 4, road.w_end - 4
                inward = 1 if stop == road.l_end else -1
                zx0 = stop - 24 if inward == 1 else stop + 8
                zebra = pg.Rect(zx0, y0, 16, y1 - y0)
                for yy in range(y0, y1 - 4, 9):
                    pg.draw.rect(surf, C.COL_ZEBRA, (zx0, yy, 16, 5))
                sl_x = stop - 30 if inward == 1 else stop + 30
                pg.draw.line(surf, C.COL_LANE_WHITE,
                             (sl_x, y0 - 2), (sl_x, y1 + 2), 3)
            else:
                x0, x1 = road.w_start + 4, road.w_end - 4
                inward = 1 if stop == road.l_end else -1
                zy0 = stop - 24 if inward == 1 else stop + 8
                zebra = pg.Rect(x0, zy0, x1 - x0, 16)
                for xx in range(x0, x1 - 4, 9):
                    pg.draw.rect(surf, C.COL_ZEBRA, (xx, zy0, 5, 16))
                sl_y = stop - 30 if inward == 1 else stop + 30
                pg.draw.line(surf, C.COL_LANE_WHITE,
                             (x0 - 2, sl_y), (x1 + 2, sl_y), 3)
            self.zebras.append((zebra, orient))

    # ------------------------------------------------------------ decoration
    def _free(self, rect, margin=16):
        r = pg.Rect(rect).inflate(margin * 2, margin * 2)
        if r.left < 0 or r.top < 0 or r.right > C.SCREEN_W or r.bottom > C.SCREEN_H:
            return False
        blockers = self.road_rects + self.node_rects
        return not any(r.colliderect(b.inflate(26, 26)) for b in blockers)

    def _decorate(self, surf):
        rng = self.rng
        # -- buildings
        tries = 0
        while len(self.buildings) < 26 and tries < 3000:
            tries += 1
            w, h = rng.randint(58, 132), rng.randint(46, 104)
            x = rng.randrange(0, C.SCREEN_W - w)
            y = rng.randrange(0, C.SCREEN_H - h)
            rect = pg.Rect(x, y, w, h)
            if not self._free(rect, 10):
                continue
            if any(rect.colliderect(b[0].inflate(22, 22)) for b in self.buildings):
                continue
            idx = rng.randrange(len(C.COL_BUILDING_BODY))
            self.buildings.append((rect, idx))
        for rect, idx in self.buildings:
            body = C.COL_BUILDING_BODY[idx]
            roof = C.COL_BUILDING_ROOF[idx]
            pg.draw.rect(surf, (0, 0, 0, 0), rect)   # placeholder, drawn below
            shadow = rect.move(4, 4)
            sh = pg.Surface(shadow.size, pg.SRCALPHA)
            sh.fill((0, 0, 0, 46))
            surf.blit(sh, shadow.topleft)
            pg.draw.rect(surf, body, rect)
            pg.draw.rect(surf, tuple(max(0, c - 34) for c in body), rect, 2)
            roof_r = rect.inflate(-int(rect.w * 0.24), -int(rect.h * 0.24))
            pg.draw.rect(surf, roof, roof_r)
            pg.draw.rect(surf, tuple(max(0, c - 30) for c in roof), roof_r, 1)
            # roof units + window strip along edges facing streets
            for _ in range(rng.randint(1, 3)):
                ux = rng.randint(roof_r.left + 4, max(roof_r.left + 5, roof_r.right - 14))
                uy = rng.randint(roof_r.top + 4, max(roof_r.top + 5, roof_r.bottom - 12))
                pg.draw.rect(surf, tuple(min(255, c + 22) for c in roof),
                             (ux, uy, 10, 8))
            for wx in range(rect.left + 6, rect.right - 8, 14):
                self.window_lights.append((wx, rect.top + 3, 6, 4))
                self.window_lights.append((wx, rect.bottom - 7, 6, 4))
                pg.draw.rect(surf, (120, 140, 158), (wx, rect.top + 3, 6, 4))
                pg.draw.rect(surf, (120, 140, 158), (wx, rect.bottom - 7, 6, 4))
        # -- trees
        tries = 0
        while len(self.trees) < 70 and tries < 4000:
            tries += 1
            r = rng.randint(7, 13)
            x = rng.randrange(r + 2, C.SCREEN_W - r - 2)
            y = rng.randrange(r + 2, C.SCREEN_H - r - 2)
            rect = pg.Rect(x - r, y - r, r * 2, r * 2)
            if not self._free(rect, 4):
                continue
            if any(rect.colliderect(b[0].inflate(8, 8)) for b in self.buildings):
                continue
            if any((x - tx) ** 2 + (y - ty) ** 2 < (r + tr + 6) ** 2
                   for tx, ty, tr in self.trees):
                continue
            self.trees.append((x, y, r))
        for x, y, r in self.trees:
            pg.draw.circle(surf, (0, 0, 0, 0), (x, y), r)
            sh = pg.Surface((r * 2 + 6, r * 2 + 6), pg.SRCALPHA)
            pg.draw.circle(sh, (0, 0, 0, 44), (r + 5, r + 5), r)
            surf.blit(sh, (x - r - 1, y - r - 1))
            pg.draw.circle(surf, C.COL_TREE_TRUNK, (x, y), max(2, r // 3))
            fol = self.rng.choice(C.COL_TREE_FOLIAGE)
            pg.draw.circle(surf, fol, (x, y), r)
            pg.draw.circle(surf, tuple(min(255, c + 24) for c in fol),
                           (x - r // 3, y - r // 3), max(2, r // 2))
        # -- street-light poles along road edges
        for r in self.road_rects:
            if r.w >= r.h:                                   # horizontal road
                for x in range(r.left + 60, r.right - 20, 170):
                    self.streetlights.append((x, r.top - 8))
                    self.streetlights.append((x + 85, r.bottom + 8))
            else:
                for y in range(r.top + 60, r.bottom - 20, 170):
                    self.streetlights.append((r.left - 8, y))
                    self.streetlights.append((r.right + 8, y + 85))
        self.streetlights = [(x, y) for x, y in self.streetlights
                             if 0 <= x < C.SCREEN_W and 0 <= y < C.SCREEN_H]
        for x, y in self.streetlights:
            pg.draw.circle(surf, (70, 72, 76), (x, y), 3)
            pg.draw.circle(surf, (170, 172, 176), (x, y), 3, 1)
