"""
render/assets.py — Procedural sprite factory.

No external art files are needed: every sprite (vehicles of seven classes,
LED signal heads, radial glows, shadows) is drawn once at boot on a 4×
super-sampled canvas and smooth-scaled down, which gives clean anti-aliased
edges at the tiny sizes the network geometry dictates (vehicles are only
15–30 px long, exactly the logical rects the original used).

All sprites are authored facing EAST and rotated for the other headings, so
orientation is always correct.
"""

import pygame as pg

import config as C

SS = 4  # super-sampling factor

_cache = {}
_fonts = {}


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def font(size, bold=False):
    if not pg.font.get_init():
        pg.font.init()
        _fonts.clear()
    key = (size, bold)
    if key in _fonts:
        try:
            _fonts[key].render("", True, (0, 0, 0))
        except Exception:
            _fonts.pop(key, None)
    if key not in _fonts:
        try:
            _fonts[key] = pg.font.SysFont("dejavusans,freesans,arial",
                                          size, bold=bold)
        except Exception:
            _fonts[key] = pg.font.Font(None, size + 2)
    return _fonts[key]


def _shade(col, f):
    return (max(0, min(255, int(col[0] * f))),
            max(0, min(255, int(col[1] * f))),
            max(0, min(255, int(col[2] * f))))


def _rr(surface, color, rect, radius):
    pg.draw.rect(surface, color, rect, border_radius=radius)


def radial_glow(radius, color, peak=110, steps=10):
    """Soft additive radial gradient used for lamps / headlights / strobes."""
    key = ("glow", radius, color, peak)
    if key in _cache:
        return _cache[key]
    surf = pg.Surface((radius * 2, radius * 2), pg.SRCALPHA)
    for i in range(steps, 0, -1):
        r = int(radius * i / steps)
        a = int(peak * (1 - i / (steps + 1)) ** 2)
        pg.draw.circle(surf, (*color, a), (radius, radius), r)
    _cache[key] = surf
    return surf


# --------------------------------------------------------------------------
# vehicle sprites
# --------------------------------------------------------------------------
def _paint_wheels(s, L, W, positions):
    for fx in positions:
        x = int(L * fx)
        pg.draw.rect(s, (20, 20, 22), (x, 0, int(L * 0.10), int(W * 0.16)))
        pg.draw.rect(s, (20, 20, 22),
                     (x, W - int(W * 0.16), int(L * 0.10), int(W * 0.16)))


def _paint_lights(s, L, W):
    ly1, ly2 = int(W * 0.22), int(W * 0.78)
    pg.draw.circle(s, (255, 244, 190), (L - int(L * 0.04), ly1), int(W * 0.09))
    pg.draw.circle(s, (255, 244, 190), (L - int(L * 0.04), ly2), int(W * 0.09))
    pg.draw.rect(s, (214, 40, 36), (0, ly1 - int(W * 0.07),
                                    int(L * 0.05), int(W * 0.14)))
    pg.draw.rect(s, (214, 40, 36), (0, ly2 - int(W * 0.07),
                                    int(L * 0.05), int(W * 0.14)))


def _body(s, L, W, colour, nose=0.24):
    r = int(W * nose)
    _rr(s, _shade(colour, 0.72), (0, 0, L, W), r)                 # dark base
    _rr(s, colour, (0, int(W * 0.05), L, int(W * 0.90)), r)       # body
    _rr(s, _shade(colour, 1.22),                                  # roof light
        (int(L * 0.08), int(W * 0.16), int(L * 0.84), int(W * 0.28)), r)


def _glass(s, L, W, front_f, back_f, w_f=0.16):
    glass = (150, 190, 214)
    pg.draw.rect(s, glass, (int(L * front_f), int(W * 0.12),
                            int(L * w_f), int(W * 0.76)),
                 border_radius=int(W * 0.10))
    if back_f is not None:
        pg.draw.rect(s, _shade(glass, 0.85),
                     (int(L * back_f), int(W * 0.14),
                      int(L * (w_f - 0.03)), int(W * 0.72)),
                     border_radius=int(W * 0.10))


def _sprite_car(L, W, colour):
    s = pg.Surface((L, W), pg.SRCALPHA)
    _body(s, L, W, colour)
    _paint_wheels(s, L, W, (0.14, 0.66))
    _glass(s, L, W, 0.60, 0.24)
    _paint_lights(s, L, W)
    return s


def _sprite_taxi(L, W, _colour):
    yellow = (240, 190, 40)
    s = _sprite_car(L, W, yellow)
    for i, x in enumerate(range(int(L * 0.10), int(L * 0.90), int(W * 0.30))):
        col = (20, 20, 20) if i % 2 == 0 else (245, 245, 245)
        pg.draw.rect(s, col, (x, int(W * 0.44), int(W * 0.24), int(W * 0.14)))
    pg.draw.rect(s, (24, 24, 24), (int(L * 0.42), int(W * 0.30),
                                   int(L * 0.16), int(W * 0.40)),
                 border_radius=2)
    return s


def _lightbar(s, L, W, x_f=0.42, w_f=0.18):
    x, w = int(L * x_f), int(L * w_f)
    pg.draw.rect(s, (200, 40, 40), (x, int(W * 0.26), w // 2, int(W * 0.48)))
    pg.draw.rect(s, (50, 80, 220), (x + w // 2, int(W * 0.26),
                                    w - w // 2, int(W * 0.48)))
    pg.draw.rect(s, (20, 20, 24), (x, int(W * 0.26), w, int(W * 0.48)), 1)


def _sprite_police(L, W, _colour):
    s = pg.Surface((L, W), pg.SRCALPHA)
    _body(s, L, W, (236, 238, 242))
    pg.draw.rect(s, (28, 40, 96), (0, int(W * 0.40), L, int(W * 0.22)))
    _paint_wheels(s, L, W, (0.14, 0.66))
    _glass(s, L, W, 0.60, 0.24)
    _paint_lights(s, L, W)
    _lightbar(s, L, W)
    return s


def _sprite_ambulance(L, W, _colour):
    s = pg.Surface((L, W), pg.SRCALPHA)
    _body(s, L, W, (240, 242, 246), nose=0.18)
    pg.draw.rect(s, (208, 44, 44), (0, int(W * 0.42), L, int(W * 0.18)))
    cx, cy, a = int(L * 0.28), int(W * 0.50), max(2, int(W * 0.30))
    pg.draw.rect(s, (208, 44, 44), (cx - a // 6, cy - a // 2, a // 3, a))
    pg.draw.rect(s, (208, 44, 44), (cx - a // 2, cy - a // 6, a, a // 3))
    _paint_wheels(s, L, W, (0.12, 0.70))
    _glass(s, L, W, 0.66, None, 0.14)
    _paint_lights(s, L, W)
    _lightbar(s, L, W, 0.50, 0.16)
    return s


def _sprite_bike(L, W, colour):
    s = pg.Surface((L, W), pg.SRCALPHA)
    cy = W // 2
    pg.draw.line(s, (30, 30, 34), (int(L * 0.10), cy), (int(L * 0.90), cy),
                 max(2, W // 4))
    for fx in (0.16, 0.84):
        pg.draw.circle(s, (18, 18, 20), (int(L * fx), cy), int(W * 0.30))
    pg.draw.circle(s, _shade(colour, 1.05), (int(L * 0.46), cy),
                   int(W * 0.34))                                   # rider
    pg.draw.circle(s, (240, 220, 190), (int(L * 0.60), cy), int(W * 0.20))
    pg.draw.circle(s, (255, 244, 190), (int(L * 0.94), cy), int(W * 0.12))
    return s


def _sprite_truck(L, W, colour):
    s = pg.Surface((L, W), pg.SRCALPHA)
    cab = int(L * 0.30)
    _rr(s, (188, 190, 196), (0, int(W * 0.04), L - cab - int(L * 0.03),
                             int(W * 0.92)), int(W * 0.12))          # cargo
    pg.draw.rect(s, (150, 152, 158), (0, int(W * 0.04),
                                      L - cab - int(L * 0.03), int(W * 0.92)), 1)
    _rr(s, _shade(colour, 0.9), (L - cab, int(W * 0.06), cab,
                                 int(W * 0.88)), int(W * 0.22))      # cab
    _glass(s, L, W, 0.80, None, 0.10)
    _paint_wheels(s, L, W, (0.10, 0.36, 0.74))
    _paint_lights(s, L, W)
    return s


def _sprite_bus(L, W, colour):
    s = pg.Surface((L, W), pg.SRCALPHA)
    base = colour if sum(colour) > 180 else (226, 150, 40)
    _body(s, L, W, base, nose=0.16)
    for x in range(int(L * 0.14), int(L * 0.86), int(W * 0.34)):
        pg.draw.rect(s, (150, 190, 214), (x, int(W * 0.20),
                                          int(W * 0.22), int(W * 0.26)))
        pg.draw.rect(s, (150, 190, 214), (x, int(W * 0.56),
                                          int(W * 0.22), int(W * 0.26)))
    _paint_wheels(s, L, W, (0.10, 0.74))
    _paint_lights(s, L, W)
    return s


_BUILDERS = {"car": _sprite_car, "taxi": _sprite_taxi,
             "police": _sprite_police, "ambulance": _sprite_ambulance,
             "bike": _sprite_bike, "truck": _sprite_truck,
             "bus": _sprite_bus}

_ROT = {"East": 0, "North": 90, "West": 180, "South": 270}


def vehicle_sprite(vtype, colour_name, length, direction):
    """AA sprite sized to the vehicle's logical rect, correctly oriented."""
    key = (vtype, colour_name, length, direction)
    if key in _cache:
        return _cache[key]
    base_key = (vtype, colour_name, length, "East")
    if base_key not in _cache:
        colour = C.CAR_PAINTS.get(colour_name, (120, 120, 128))
        big = _BUILDERS[vtype](length * SS, 10 * SS, colour)
        _cache[base_key] = pg.transform.smoothscale(big, (length, 10))
    sprite = pg.transform.rotate(_cache[base_key], _ROT[direction])
    _cache[key] = sprite
    return sprite


def vehicle_shadow(length, direction):
    key = ("shadow", length, direction)
    if key in _cache:
        return _cache[key]
    big = pg.Surface((length * SS, 10 * SS), pg.SRCALPHA)
    _rr(big, (0, 0, 0, 70), big.get_rect(), 10)
    small = pg.transform.smoothscale(big, (length, 10))
    _cache[key] = pg.transform.rotate(small, _ROT[direction])
    return _cache[key]


# --------------------------------------------------------------------------
# LED traffic-light head
# --------------------------------------------------------------------------
HEAD_W, HEAD_H = 16, 40


def signal_head(state):
    """state: 0 red, 1 green, 2 amber → rendered LED head surface."""
    key = ("head", state)
    if key in _cache:
        return _cache[key]
    W, H = HEAD_W * SS, HEAD_H * SS
    s = pg.Surface((W, H), pg.SRCALPHA)
    _rr(s, (26, 28, 32), (0, 0, W, H), W // 4)
    _rr(s, (48, 52, 58), (int(W * 0.08), int(H * 0.03),
                          int(W * 0.84), int(H * 0.94)), W // 5)
    lamps = [(C.LAMP_RED, 0), (C.LAMP_AMBER, 2), (C.LAMP_GREEN, 1)]
    for row, (col, on_state) in enumerate(lamps):
        cy = int(H * (0.20 + 0.30 * row))
        on = (state == on_state)
        colour = col if on else _shade(col, 0.22)
        pg.draw.circle(s, (18, 18, 20), (W // 2, cy), int(W * 0.34))
        pg.draw.circle(s, colour, (W // 2, cy), int(W * 0.28))
        if on:
            pg.draw.circle(s, _shade(col, 1.5),
                           (W // 2 - int(W * 0.08), cy - int(W * 0.08)),
                           int(W * 0.10))
    small = pg.transform.smoothscale(s, (HEAD_W, HEAD_H))
    _cache[key] = small
    return small


def signal_pole():
    key = "pole"
    if key in _cache:
        return _cache[key]
    s = pg.Surface((6, 18), pg.SRCALPHA)
    pg.draw.rect(s, (60, 62, 66), (2, 0, 2, 18))
    pg.draw.ellipse(s, (40, 42, 46), (0, 14, 6, 4))
    _cache[key] = s
    return s


LAMP_COLOURS = {0: C.LAMP_RED, 1: C.LAMP_GREEN, 2: C.LAMP_AMBER}
# lamp-centre offsets inside the head surface for the glow anchor
LAMP_OFFSET = {0: (HEAD_W // 2, int(HEAD_H * 0.20)),
               2: (HEAD_W // 2, int(HEAD_H * 0.50)),
               1: (HEAD_W // 2, int(HEAD_H * 0.80))}
