"""
render/pedestrians.py — Ambient pedestrians at zebra crossings.

Each pedestrian is bound to one signalised approach. They wait on the kerb
while that approach's head is GREEN (vehicles flowing) and cross while it is
RED (vehicles held at the stop line) — the same state the vehicle logic
reads, so people and cars never fight over the zebra. Purely presentational:
no influence on the simulation core.
"""

import math
import random

import pygame as pg

import config as C
from config import RED
from core import network


class Pedestrian:
    __slots__ = ("key", "axis", "path_a", "path_b", "pos", "t", "speed",
                 "waiting", "tone", "shirt", "phase")

    def __init__(self, rng, key, info):
        self.key = key                      # (node, sig)
        orient, rid, road = info["axis"]
        stop = info["stop"]
        self.axis = orient
        off = rng.choice((-16, 16)) + (0 if stop == road.l_end else 0)
        if orient == "h":
            x = stop + (-16 if stop == road.l_end else 16)
            self.path_a = (x, road.w_start - 8)
            self.path_b = (x, road.w_end + 8)
        else:
            y = stop + (-16 if stop == road.l_end else 16)
            self.path_a = (road.w_start - 8, y)
            self.path_b = (road.w_end + 8, y)
        if rng.random() < 0.5:
            self.path_a, self.path_b = self.path_b, self.path_a
        self.t = 0.0
        self.speed = rng.uniform(0.10, 0.16)          # path fractions / s
        self.waiting = True
        self.tone = rng.choice(((236, 200, 172), (198, 150, 116),
                                (150, 108, 78), (110, 80, 58)))
        self.shirt = rng.choice(((214, 84, 70), (78, 128, 196), (240, 208, 90),
                                 (92, 176, 118), (200, 200, 208), (150, 96, 170)))
        self.phase = rng.uniform(0, math.tau)

    def pos_xy(self):
        ax, ay = self.path_a
        bx, by = self.path_b
        return (ax + (bx - ax) * self.t, ay + (by - ay) * self.t)


class PedestrianLayer:
    def __init__(self, env, signals):
        self.signals = signals
        self.rng = random.Random(C.RNG_SEED_DECOR + 3)
        self.approaches = {k: v for k, v in env.approaches.items()
                           if v["axis"] is not None}
        self.people = []
        keys = list(self.approaches.keys())
        for _ in range(C.PEDESTRIAN_MAX):
            k = self.rng.choice(keys)
            self.people.append(Pedestrian(self.rng, k, self.approaches[k]))

    def update(self, dt, sim_time):
        for p in self.people:
            n, s = p.key
            traffic_held = self.signals[n][s][1] == RED
            if p.waiting:
                if traffic_held and self.rng.random() < 0.9:
                    p.waiting = False
            else:
                p.t += p.speed * dt
                if p.t >= 1.0:                      # reached far kerb
                    p.t = 0.0
                    p.waiting = True
                    k = self.rng.choice(list(self.approaches.keys()))
                    p.__init__(self.rng, k, self.approaches[k])

    def draw(self, screen, sim_time):
        for p in self.people:
            x, y = p.pos_xy()
            walking = not p.waiting
            swing = math.sin(sim_time * 9 + p.phase) * (2.4 if walking else 0.4)
            # shadow
            pg.draw.ellipse(screen, (0, 0, 0, 60),
                            (x - 4, y + 2, 8, 4))
            # legs
            if p.axis == "h":
                pg.draw.line(screen, (40, 40, 48), (x - 1, y),
                             (x - 1, y + swing + 3), 2)
                pg.draw.line(screen, (40, 40, 48), (x + 1, y),
                             (x + 1, y - swing + 3), 2)
            else:
                pg.draw.line(screen, (40, 40, 48), (x, y - 1),
                             (x + swing + 3, y - 1), 2)
                pg.draw.line(screen, (40, 40, 48), (x, y + 1),
                             (x - swing + 3, y + 1), 2)
            pg.draw.circle(screen, p.shirt, (int(x), int(y)), 4)   # torso
            pg.draw.circle(screen, p.tone, (int(x), int(y) - 2), 2)  # head
