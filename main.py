"""
Smart City Traffic Signal Synchronization — entry point.

Architecture
------------
Fixed-timestep core, interpolated presentation:

  * the ORIGINAL algorithm ran one motion pass per `time.sleep(0.1)` frame
    and one signal countdown per wall-clock second. Here the identical
    logic runs on a fixed 0.1 s accumulator (10 ticks == 1 simulated
    second → `SignalController.second_tick`), so behaviour is preserved
    tick-for-tick while the renderer draws at 60 FPS, interpolating each
    vehicle between its previous and current logic position.

Run:            python main.py
Demo capture:   python main.py --demo-shots out_dir   (headless-friendly)
Keys:           H in-app for the full list.
"""

import argparse
import math
import os
import sys
import time

import pygame as pg

__version__ = "1.0.0"

import config as C
from core import density, network
from core.signals import SignalController
from core.vehicles import TrafficWorld
from render import assets
from render.background import Environment
from render.dashboard import Dashboard
from render.effects import DayNight, Fog, Rain
from render.pedestrians import PedestrianLayer
from stats import Stats


class Simulator:
    def __init__(self, seed=None, autoquit=None):
        self.autoquit = autoquit
        self.wall_time = 0.0
        pg.init()
        pg.display.set_caption(C.WINDOW_TITLE)
        self.screen = pg.display.set_mode((C.SCREEN_W, C.SCREEN_H))
        self.clock = pg.time.Clock()

        # ---- core (original algorithm state) -----------------------------
        self.signals = network.build_signals()
        self.controller = SignalController(self.signals)
        self.board = density.DensityBoard()
        self.managers = density.build_managers()
        self.stats = Stats(self.board)
        self.world = TrafficWorld(self.signals, self.controller, self.board,
                                  self.managers, self.stats, seed=seed)
        self.controller.add_extra_time(5, 0, 0)   # original boot call

        # ---- presentation -------------------------------------------------
        self.env = Environment()
        self.daynight = DayNight(self.env)
        self.rain = Rain()
        self.fog = Fog()
        self.peds = PedestrianLayer(self.env, self.signals)
        self.hud = Dashboard(self.controller, self.board, self.stats)

        self.running = True
        self.paused = False
        self.show_help = False
        self.time_scale = 1.0
        self.acc = 0.0
        self.tick_count = 0
        self.sim_time = 0.0
        self.shot_index = 0

    # ------------------------------------------------------------------ core
    def logic_tick(self):
        self.tick_count += 1
        self.sim_time = self.tick_count * C.LOGIC_TICK
        if self.tick_count % 10 == 0:             # one simulated second
            self.controller.second_tick()
            self.stats.second_sample()
        self.controller.tick_preemption()
        self.world.motion_tick()

    # ------------------------------------------------------------- rendering
    def _vehicle_rect(self, v, alpha):
        if v.snap:
            x, y = v.position_x, v.position_y
        else:
            x = v.prev_x + (v.position_x - v.prev_x) * alpha
            y = v.prev_y + (v.position_y - v.prev_y) * alpha
        if v.direction in ("East", "West"):
            return x, y, v.length, v.width
        return x, y, v.width, v.length

    def render(self, alpha, weather_txt):
        screen = self.screen
        screen.blit(self.env.surface, (0, 0))

        # vehicles (+shadows) ------------------------------------------------
        placed = []
        for v in self.world.vehicles:
            x, y, w, h = self._vehicle_rect(v, alpha)
            placed.append((v, (x, y, w, h)))
        if C.FEATURES["shadows"]:
            for v, (x, y, w, h) in placed:
                screen.blit(assets.vehicle_shadow(v.length, v.direction),
                            (x + 2, y + 3))
        if C.FEATURES["pedestrians"]:
            self.peds.draw(screen, self.sim_time)
        for v, (x, y, w, h) in placed:
            screen.blit(assets.vehicle_sprite(v.vtype, v.colour, v.length,
                                              v.direction), (x, y))

        # signal heads -------------------------------------------------------
        strobe = int(time.time() * 6) % 2 == 0
        lit = []
        pole = assets.signal_pole()
        for n in range(C.TOT_NODES):
            for s in range(network.signals_per_node(n)):
                x, y = self.signals[n][s][2]
                vs = self.controller.visual_state(n, s)
                screen.blit(pole, (x + 17, y + 34))
                head = assets.signal_head(vs)
                hx, hy = x + 12, y
                # soft drop shadow
                pg.draw.ellipse(screen, (0, 0, 0, 60),
                                (hx - 1, hy + 38, 18, 6))
                screen.blit(head, (hx, hy))
                ox, oy = assets.LAMP_OFFSET[vs]
                colour = assets.LAMP_COLOURS[vs]
                lit.append((hx + ox, hy + oy, colour))
                if C.FEATURES["glow"]:
                    pulse = 12 + int(3 * math.sin(self.sim_time * 4 + n + s))
                    glow = assets.radial_glow(pulse, colour, peak=90)
                    screen.blit(glow, (hx + ox - pulse, hy + oy - pulse),
                                special_flags=pg.BLEND_RGBA_ADD)

        # lighting + weather ---------------------------------------------------
        self.daynight.apply(screen, placed, lit, strobe)
        if C.FEATURES["rain"]:
            self.rain.update_draw(screen, 1 / max(30, self.stats.fps or 60))
        if C.FEATURES["fog"]:
            self.fog.update_draw(screen, 1 / max(30, self.stats.fps or 60))

        # HUD ------------------------------------------------------------------
        if C.FEATURES["labels"]:
            self.hud.draw_signal_labels(screen)
        self.hud.draw_preemption_badges(screen)
        self.hud.draw_topbar(screen, self.daynight, weather_txt)
        if C.FEATURES["dashboard"]:
            self.hud.draw_panel(screen)
        if self.show_help:
            self.hud.draw_help(screen)
        if self.paused:
            t = assets.font(30, bold=True).render("PAUSED", True,
                                                  (255, 255, 255))
            screen.blit(t, (C.SCREEN_W // 2 - t.get_width() // 2, 60))

    # --------------------------------------------------------------- events
    def handle_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
            elif event.type == pg.KEYDOWN:
                k = event.key
                if k in (pg.K_q, pg.K_ESCAPE):
                    self.running = False
                elif k == pg.K_SPACE:
                    self.paused = not self.paused
                elif k in (pg.K_PLUS, pg.K_EQUALS, pg.K_KP_PLUS):
                    self.time_scale = min(8.0, self.time_scale * 2)
                elif k in (pg.K_MINUS, pg.K_KP_MINUS):
                    self.time_scale = max(0.25, self.time_scale / 2)
                elif k == pg.K_TAB:
                    C.FEATURES["dashboard"] = not C.FEATURES["dashboard"]
                elif k == pg.K_t:
                    C.FEATURES["labels"] = not C.FEATURES["labels"]
                elif k == pg.K_n:
                    C.FEATURES["night"] = not C.FEATURES["night"]
                elif k == pg.K_c:
                    C.FEATURES["day_night_cycle"] = \
                        not C.FEATURES["day_night_cycle"]
                elif k == pg.K_r:
                    C.FEATURES["rain"] = not C.FEATURES["rain"]
                elif k == pg.K_f:
                    C.FEATURES["fog"] = not C.FEATURES["fog"]
                elif k == pg.K_p:
                    C.FEATURES["pedestrians"] = not C.FEATURES["pedestrians"]
                elif k == pg.K_e:
                    C.FEATURES["emergency"] = not C.FEATURES["emergency"]
                elif k == pg.K_h:
                    self.show_help = not self.show_help
                elif k == pg.K_s:
                    self.save_shot(".")

    def save_shot(self, folder):
        self.shot_index += 1
        path = os.path.join(folder, f"screenshot_{self.shot_index:02d}.png")
        pg.image.save(self.screen, path)
        print(f"[shot] saved {path}")
        return path

    # ------------------------------------------------------------------ loop
    def run(self):
        while self.running:
            frame_dt = self.clock.tick(C.TARGET_FPS) / 1000.0
            self.wall_time += frame_dt
            if self.autoquit is not None and self.wall_time >= self.autoquit:
                self.running = False
                break
            self.stats.fps = self.clock.get_fps()
            self.handle_events()
            if not self.paused:
                sim_dt = min(frame_dt, 0.25) * self.time_scale
                self.daynight.advance(sim_dt)
                if C.FEATURES["pedestrians"]:
                    self.peds.update(sim_dt, self.sim_time)
                self.acc += sim_dt
                guard = 0
                while self.acc >= C.LOGIC_TICK and guard < 40:
                    self.logic_tick()
                    self.acc -= C.LOGIC_TICK
                    guard += 1
            alpha = 0.0 if self.paused else min(1.0, self.acc / C.LOGIC_TICK)
            weather = " + ".join(w for w, on in (("RAIN", C.FEATURES["rain"]),
                                                 ("FOG", C.FEATURES["fog"]))
                                 if on)
            self.render(alpha if C.FEATURES["vsync_interp"] else 1.0, weather)
            pg.display.flip()
        self.shutdown()

    def run_demo_shots(self, out_dir, ticks=420):
        """Headless capture: warm the sim, save a day and a night+rain frame."""
        os.makedirs(out_dir, exist_ok=True)
        for i in range(ticks):
            self.logic_tick()
            self.peds.update(C.LOGIC_TICK, self.sim_time)
        self.stats.fps = 60.0
        self.render(1.0, "")
        pg.image.save(self.screen, os.path.join(out_dir, "shot_day.png"))
        C.FEATURES["night"] = True
        C.FEATURES["rain"] = True
        for i in range(60):
            self.logic_tick()
            self.peds.update(C.LOGIC_TICK, self.sim_time)
        self.render(1.0, "RAIN")
        pg.image.save(self.screen, os.path.join(out_dir, "shot_night_rain.png"))
        self.stats.export_report(os.path.join(out_dir, "density_report.png"))
        print(f"[demo] frames written to {out_dir}; "
              f"ticks={self.tick_count}, passed={self.stats.passed}, "
              f"queued={self.board.real_total()}")
        pg.quit()

    def shutdown(self):
        self.stats.export_report("density_report.png")
        pg.quit()


def main(argv=None):
    ap = argparse.ArgumentParser(prog="smart-traffic", description=C.WINDOW_TITLE)
    ap.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")
    ap.add_argument("--seed", type=int, default=None,
                    help="RNG seed for reproducible runs")
    ap.add_argument("--headless", action="store_true",
                    help="run headlessly without an active display")
    ap.add_argument("--demo-shots", metavar="DIR",
                    help="headless: simulate, save demo frames to DIR, exit")
    ap.add_argument("--ticks", type=int, default=420,
                    help="warm-up ticks for --demo-shots")
    ap.add_argument("--autoquit", type=float, default=None,
                    help="quit automatically after N seconds (testing/CI)")
    args = ap.parse_args(argv)

    if args.headless or args.demo_shots or args.autoquit is not None:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    sim = Simulator(seed=args.seed, autoquit=args.autoquit)
    if args.demo_shots:
        sim.run_demo_shots(args.demo_shots, args.ticks)
    else:
        sim.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
