"""
render/dashboard.py — Glassmorphism HUD.

Top status bar (title · sim clock · phase icon · FPS), a right-hand stats
panel (vehicle counts, average wait, throughput, congestion meter, live
density sparklines for the same three signals the original project charted)
and per-signal timer/density pills. All panels are translucent rounded
"glass" cards with hairline borders; drawing is cheap blits + text.
"""

import math

import pygame as pg

import config as C
from core import network
from render import assets


def _glass(size, alpha=None, radius=12):
    s = pg.Surface(size, pg.SRCALPHA)
    col = C.HUD_GLASS if alpha is None else (*C.HUD_GLASS[:3], alpha)
    pg.draw.rect(s, col, s.get_rect(), border_radius=radius)
    pg.draw.rect(s, C.HUD_BORDER, s.get_rect(), 1, border_radius=radius)
    hl = pg.Rect(1, 1, size[0] - 2, max(2, size[1] // 5))
    pg.draw.rect(s, (255, 255, 255, 14), hl,
                 border_top_left_radius=radius, border_top_right_radius=radius)
    return s


class Dashboard:
    def __init__(self, controller, board, stats):
        self.controller = controller
        self.board = board
        self.stats = stats
        self.f_small = assets.font(12)
        self.f_body = assets.font(14)
        self.f_bold = assets.font(15, bold=True)
        self.f_big = assets.font(19, bold=True)
        self.topbar = _glass((C.SCREEN_W - 16, 34), alpha=150, radius=10)
        self.panel_bg = _glass((C.PANEL_W, 356))
        self.help_bg = _glass((420, 262), alpha=210, radius=14)
        self.pill_cache = {}

    # ------------------------------------------------------------- top bar
    def draw_topbar(self, screen, daynight, weather_txt):
        screen.blit(self.topbar, (8, 6))
        screen.blit(self.f_big.render("SMART TRAFFIC CONTROL",
                                      True, C.HUD_TEXT), (22, 13))
        screen.blit(self.f_small.render(
            "density-synchronized signal network", True, C.HUD_SUBTEXT),
            (232, 17))
        clock = self.stats.sim_clock()
        d = daynight.darkness()
        phase = "NIGHT" if d > 0.55 else ("DUSK" if d > 0.30 else "DAY")
        mid = (f"SIM {clock}   ·   {phase}"
               + (f"   ·   {weather_txt}" if weather_txt else ""))
        t = self.f_bold.render(mid, True, C.HUD_ACCENT)
        screen.blit(t, (C.SCREEN_W // 2 - t.get_width() // 2, 15))
        # sun/moon pictogram
        cx = C.SCREEN_W - 168
        if phase == "NIGHT":
            pg.draw.circle(screen, (210, 218, 240), (cx, 23), 8)
            pg.draw.circle(screen, (20, 24, 44), (cx + 4, 20), 7)
        else:
            pg.draw.circle(screen, (250, 208, 84), (cx, 23), 7)
            for k in range(8):
                a = k * math.pi / 4
                pg.draw.line(screen, (250, 208, 84),
                             (cx + math.cos(a) * 9, 23 + math.sin(a) * 9),
                             (cx + math.cos(a) * 12, 23 + math.sin(a) * 12), 2)
        fps = self.f_bold.render(f"{self.stats.fps:4.0f} FPS", True,
                                 C.HUD_GOOD if self.stats.fps > 45 else C.HUD_WARN)
        screen.blit(fps, (C.SCREEN_W - 128, 15))

    # -------------------------------------------------------------- panel
    def draw_panel(self, screen):
        x0 = C.SCREEN_W - C.PANEL_W - 10
        y0 = 48
        screen.blit(self.panel_bg, (x0, y0))
        pad = 14
        y = y0 + 10
        screen.blit(self.f_bold.render("LIVE METRICS", True, C.HUD_ACCENT),
                    (x0 + pad, y))
        y += 24
        st = self.stats
        active_greens = sum(
            1 for n in range(C.TOT_NODES)
            for s in range(network.signals_per_node(n))
            if self.controller.signals[n][s][1] == 1)
        rows = [
            ("Total vehicles", f"{C.NO_OF_VEH}", C.HUD_TEXT),
            ("Queued at signals", f"{self.board.real_total()}", C.HUD_TEXT),
            ("Avg waiting time", f"{st.avg_wait():5.1f} s", C.HUD_TEXT),
            ("Throughput", f"{st.throughput_per_min():5.0f} veh/min", C.HUD_TEXT),
            ("Vehicles cleared", f"{st.passed}", C.HUD_TEXT),
            ("Active greens", f"{active_greens}", C.HUD_GOOD),
        ]
        for label, value, col in rows:
            screen.blit(self.f_body.render(label, True, C.HUD_SUBTEXT),
                        (x0 + pad, y))
            v = self.f_bold.render(value, True, col)
            screen.blit(v, (x0 + C.PANEL_W - pad - v.get_width(), y))
            y += 21
        # congestion meter
        label, col = st.congestion_label()
        screen.blit(self.f_body.render("Congestion", True, C.HUD_SUBTEXT),
                    (x0 + pad, y))
        v = self.f_bold.render(label, True, col)
        screen.blit(v, (x0 + C.PANEL_W - pad - v.get_width(), y))
        y += 20
        bar = pg.Rect(x0 + pad, y, C.PANEL_W - 2 * pad, 8)
        pg.draw.rect(screen, (255, 255, 255, 26), bar, border_radius=4)
        fill = bar.copy()
        fill.w = max(4, int(bar.w * st.congestion))
        pg.draw.rect(screen, col, fill, border_radius=4)
        y += 18
        # sparkline chart of the three legacy-tracked signals
        screen.blit(self.f_bold.render("SIGNAL DENSITY (LIVE)", True,
                                       C.HUD_ACCENT), (x0 + pad, y))
        y += 20
        chart = pg.Rect(x0 + pad, y, C.PANEL_W - 2 * pad, 66)
        pg.draw.rect(screen, (255, 255, 255, 16), chart, border_radius=6)
        colors = {"Signal_1": C.HUD_ACCENT, "Signal_2": C.HUD_GOOD,
                  "Signal_3": C.HUD_WARN}
        peak = max(6, max((max(v) if v else 0)
                          for v in st.series.values()))
        for name, ys in st.series.items():
            pts = ys[-64:]
            if len(pts) < 2:
                continue
            step = chart.w / max(1, len(pts) - 1)
            poly = [(chart.left + i * step,
                     chart.bottom - 3 - (p / peak) * (chart.h - 8))
                    for i, p in enumerate(pts)]
            pg.draw.lines(screen, colors[name], False, poly, 2)
        y += 72
        lx = x0 + pad
        for name in ("Signal_1", "Signal_2", "Signal_3"):
            pg.draw.rect(screen, colors[name], (lx, y + 3, 10, 4))
            t = self.f_small.render(name, True, C.HUD_SUBTEXT)
            screen.blit(t, (lx + 14, y - 2))
            lx += 14 + t.get_width() + 10
        y += 18
        screen.blit(self.f_small.render(
            "H help · Tab panel · N night · R rain", True, C.HUD_SUBTEXT),
            (x0 + pad, y))

    # ------------------------------------------------- per-signal pills
    def draw_signal_labels(self, screen):
        for n in range(C.TOT_NODES):
            for s in range(network.signals_per_node(n)):
                head = self.controller.signals[n][s]
                vs = self.controller.visual_state(n, s)
                dens = self.board.count(n, s)
                col = (C.LAMP_GREEN if vs == 1
                       else C.LAMP_AMBER if vs == 2 else C.LAMP_RED)
                txt = f"{head[0]:>2}s · {dens}"
                key = (txt, col)
                if key not in self.pill_cache:
                    t = self.f_small.render(txt, True, C.HUD_TEXT)
                    pill = pg.Surface((t.get_width() + 14, 16), pg.SRCALPHA)
                    pg.draw.rect(pill, (*C.HUD_GLASS[:3], 190),
                                 pill.get_rect(), border_radius=8)
                    pg.draw.circle(pill, col, (8, 8), 3)
                    pill.blit(t, (13, 1))
                    if len(self.pill_cache) > 400:
                        self.pill_cache.clear()
                    self.pill_cache[key] = pill
                pill = self.pill_cache[key]
                x, y = head[2]
                screen.blit(pill, (x + 8 - pill.get_width() // 2, y - 14))

    def draw_preemption_badges(self, screen):
        for node in self.controller.preempted:
            cx, cy = network.node_pos(node)
            t = self.f_bold.render("EMS PRIORITY", True, (255, 255, 255))
            w = t.get_width() + 16
            badge = pg.Surface((w, 18), pg.SRCALPHA)
            pg.draw.rect(badge, (200, 40, 40, 220), badge.get_rect(),
                         border_radius=9)
            badge.blit(t, (8, 1))
            screen.blit(badge, (cx - w // 2, cy - 40))

    # ---------------------------------------------------------- help card
    def draw_help(self, screen):
        x = C.SCREEN_W // 2 - 210
        y = C.SCREEN_H // 2 - 131
        screen.blit(self.help_bg, (x, y))
        lines = [
            ("SPACE", "pause / resume"),
            ("+ / -", "simulation speed"),
            ("Tab", "metrics panel"),
            ("T", "signal timer & density labels"),
            ("N / C", "force night / auto day-night cycle"),
            ("R / F", "rain / fog"),
            ("P / E", "pedestrians / emergency priority"),
            ("S", "save screenshot"),
            ("H", "close help"),
            ("Q / Esc", "quit (writes density_report.png)"),
        ]
        screen.blit(self.f_big.render("CONTROLS", True, C.HUD_ACCENT),
                    (x + 20, y + 14))
        yy = y + 46
        for k, desc in lines:
            screen.blit(self.f_bold.render(k, True, C.HUD_TEXT), (x + 24, yy))
            screen.blit(self.f_body.render(desc, True, C.HUD_SUBTEXT),
                        (x + 110, yy))
            yy += 21
