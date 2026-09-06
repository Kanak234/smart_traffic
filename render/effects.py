"""
render/effects.py — Dynamic lighting and weather.

* DayNight — a slow cycle (config.DAY_LENGTH_S) that darkens the scene with
  a cool blue multiply-style overlay and, at night, composites an additive
  light layer: street-lamp pools, lit building windows, vehicle headlight
  cones + tail/brake lights, signal-lamp bloom and emergency strobes.
* Rain — numpy particle streaks with a cold ambient tint.
* Fog — soft drifting alpha blobs.

Everything heavy (glow gradients, light pools, window layer) is pre-rendered
once; per-frame work is only blits.
"""

import math

import numpy as np
import pygame as pg

import config as C
from render import assets


class DayNight:
    def __init__(self, env):
        self.env = env
        self.t = 0.30                    # start mid-morning
        self.pool = assets.radial_glow(46, (255, 214, 150), peak=95)
        self.head_glow = assets.radial_glow(16, (255, 240, 190), peak=120)
        self.brake_glow = assets.radial_glow(10, (255, 70, 60), peak=130)
        self.strobe_r = assets.radial_glow(22, (255, 60, 60), peak=150)
        self.strobe_b = assets.radial_glow(22, (80, 120, 255), peak=150)
        self.window_layer = self._window_layer()
        self.dark = pg.Surface((C.SCREEN_W, C.SCREEN_H), pg.SRCALPHA)

    def _window_layer(self):
        layer = pg.Surface((C.SCREEN_W, C.SCREEN_H), pg.SRCALPHA)
        rng = np.random.default_rng(C.RNG_SEED_DECOR + 7)
        for (x, y, w, h) in self.env.window_lights:
            if rng.random() < 0.55:
                warm = (255, 214, 130, 150) if rng.random() < 0.8 \
                    else (190, 220, 255, 130)
                pg.draw.rect(layer, warm, (x, y, w, h))
        return layer

    def advance(self, dt):
        if C.FEATURES["day_night_cycle"] and not C.FEATURES["night"]:
            self.t = (self.t + dt / C.DAY_LENGTH_S) % 1.0

    def darkness(self):
        """0 (noon) → 1 (deep night)."""
        if C.FEATURES["night"]:
            return 1.0
        return self._smooth()

    def _smooth(self):
        # daylight peaks at t=0.5; night at t=0/1
        d = (math.cos(self.t * 2 * math.pi) + 1) / 2      # 1 at midnight
        return d ** 1.4

    def is_night(self):
        return self.darkness() > 0.45

    def apply(self, screen, vehicles, signal_lights, strobe_phase):
        d = self.darkness()
        if d < 0.03:
            return
        # ---- darkness overlay (cool blue) --------------------------------
        alpha = int(158 * d)
        self.dark.fill((10, 14, 38, alpha))
        # dawn/dusk warm rim
        if 0.25 < d < 0.75:
            warm = pg.Surface((C.SCREEN_W, C.SCREEN_H), pg.SRCALPHA)
            warm.fill((255, 120, 40, int(26 * (1 - abs(d - 0.5) * 2))))
            self.dark.blit(warm, (0, 0))
        screen.blit(self.dark, (0, 0))
        if d < 0.35:
            return
        # ---- additive light layer ----------------------------------------
        lum = min(1.0, (d - 0.35) / 0.5)
        flags = pg.BLEND_RGBA_ADD
        # street lamps
        for x, y in self.env.streetlights:
            screen.blit(self.pool, (x - 46, y - 46), special_flags=flags)
        # lit windows
        if lum > 0.4:
            screen.blit(self.window_layer, (0, 0), special_flags=flags)
        # vehicle lights
        for v, (rx, ry, rw, rh) in vehicles:
            cx, cy = rx + rw / 2, ry + rh / 2
            hx, hy = _head_anchor(v.direction, rx, ry, rw, rh)
            screen.blit(self.head_glow, (hx - 16, hy - 16), special_flags=flags)
            _draw_cone(screen, v.direction, hx, hy)
            tx, ty = _tail_anchor(v.direction, rx, ry, rw, rh)
            if v.brake:
                screen.blit(self.brake_glow, (tx - 10, ty - 10),
                            special_flags=flags)
            else:
                pg.draw.circle(screen, (200, 40, 40), (int(tx), int(ty)), 2)
            if v.vtype in ("police", "ambulance"):
                g = self.strobe_r if strobe_phase else self.strobe_b
                screen.blit(g, (cx - 22, cy - 22), special_flags=flags)
        # signal lamp bloom
        for (x, y, colour) in signal_lights:
            glow = assets.radial_glow(15, colour, peak=140)
            screen.blit(glow, (x - 15, y - 15), special_flags=flags)


_CONE = {}


def _cone_surface(direction):
    if direction in _CONE:
        return _CONE[direction]
    base = pg.Surface((46, 26), pg.SRCALPHA)      # east-facing cone
    pts = [(0, 9), (0, 17), (46, 26), (46, 0)]
    pg.draw.polygon(base, (255, 236, 170, 46), pts)
    pg.draw.polygon(base, (255, 236, 170, 26),
                    [(0, 11), (0, 15), (46, 22), (46, 4)])
    rot = {"East": 0, "North": 90, "West": 180, "South": 270}[direction]
    _CONE[direction] = pg.transform.rotate(base, rot)
    return _CONE[direction]


def _head_anchor(d, x, y, w, h):
    return {"East": (x + w, y + h / 2), "West": (x, y + h / 2),
            "North": (x + w / 2, y), "South": (x + w / 2, y + h)}[d]


def _tail_anchor(d, x, y, w, h):
    return {"West": (x + w, y + h / 2), "East": (x, y + h / 2),
            "South": (x + w / 2, y), "North": (x + w / 2, y + h)}[d]


def _draw_cone(screen, direction, hx, hy):
    cone = _cone_surface(direction)
    off = {"East": (0, -cone.get_height() / 2),
           "West": (-cone.get_width(), -cone.get_height() / 2),
           "North": (-cone.get_width() / 2, -cone.get_height()),
           "South": (-cone.get_width() / 2, 0)}[direction]
    screen.blit(cone, (hx + off[0], hy + off[1]),
                special_flags=pg.BLEND_RGBA_ADD)


class Rain:
    def __init__(self, n=230):
        rng = np.random.default_rng(11)
        self.x = rng.uniform(0, C.SCREEN_W, n).astype(np.float32)
        self.y = rng.uniform(0, C.SCREEN_H, n).astype(np.float32)
        self.spd = rng.uniform(420, 680, n).astype(np.float32)
        self.layer = pg.Surface((C.SCREEN_W, C.SCREEN_H), pg.SRCALPHA)
        self.tint = pg.Surface((C.SCREEN_W, C.SCREEN_H), pg.SRCALPHA)
        self.tint.fill((70, 82, 104, 46))

    def update_draw(self, screen, dt):
        self.y += self.spd * dt
        self.x -= self.spd * dt * 0.18
        wrap = self.y > C.SCREEN_H
        self.y[wrap] -= C.SCREEN_H + 8
        self.x[self.x < 0] += C.SCREEN_W
        self.layer.fill((0, 0, 0, 0))
        for x, y in zip(self.x.tolist(), self.y.tolist()):
            pg.draw.line(self.layer, (188, 206, 232, 130),
                         (x, y), (x + 2.4, y + 11), 1)
        screen.blit(self.tint, (0, 0))
        screen.blit(self.layer, (0, 0))


class Fog:
    def __init__(self):
        self.blobs = []
        rng = np.random.default_rng(23)
        for _ in range(7):
            r = int(rng.integers(120, 260))
            s = pg.Surface((r * 2, r * 2), pg.SRCALPHA)
            for i in range(8, 0, -1):
                a = int(30 * (1 - i / 9))
                pg.draw.circle(s, (222, 226, 232, a), (r, r), int(r * i / 8))
            self.blobs.append([float(rng.integers(0, C.SCREEN_W)),
                               float(rng.integers(0, C.SCREEN_H)),
                               float(rng.uniform(6, 18)), s])
        self.veil = pg.Surface((C.SCREEN_W, C.SCREEN_H), pg.SRCALPHA)
        self.veil.fill((214, 218, 226, 34))

    def update_draw(self, screen, dt):
        screen.blit(self.veil, (0, 0))
        for b in self.blobs:
            b[0] = (b[0] + b[2] * dt) % (C.SCREEN_W + 300) - 150
            screen.blit(b[3], (b[0] - b[3].get_width() / 2,
                               b[1] - b[3].get_height() / 2))
