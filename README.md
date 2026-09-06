# Smart Traffic Control — Synchronized Signal Network Simulator

Modern, realistic rewrite of the classic "Smart Street Light" traffic signal
synchronization project. **The original traffic algorithm is preserved
verbatim** — density-based signal management, extra-time distribution,
round-robin phase rotation, vehicle turning logic, respawn tables — only the
presentation layer is new.

![day](docs/shot_day.png)

## Run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Python 3.10+ (tested on 3.12). On **Python 3.14**, agar `pygame` ka wheel na
mile to `pip install pygame-ce` use karo (drop-in replacement, same
`import pygame`).

Headless demo frames (CI/testing):

```bash
python main.py --demo-shots out/          # saves day + night+rain PNGs
python main.py --autoquit 10 --seed 42    # 10 s run, then exits + report
```

## Keys

| Key | Action | Key | Action |
|-----|--------|-----|--------|
| SPACE | pause / resume | N | night on/off |
| + / − | sim speed 0.25×–8× | C | day-night cycle |
| Tab | metrics panel | R / F | rain / fog |
| T | signal labels | P | pedestrians |
| E | emergency priority | S | screenshot |
| H | help overlay | Q / Esc | quit (+ density report) |

## What you get

- Textured roads: lane paint, dashed separators, double-yellow medians,
  zebra crossings, stop lines, kerbed sidewalks, grass with noise.
- Procedural city: 26 buildings (windows light up at night), ~70 trees,
  streetlights along every road.
- 7 vehicle types (car, taxi, police, ambulance, bike, truck, bus) —
  procedurally drawn, supersampled 4×, rotated per direction, soft shadows.
- LED signal heads with red/amber/green, glow bloom, per-signal
  timer + live density pills.
- Day/night cycle: headlight cones, brake lights, tail lights,
  emergency strobes, streetlight pools, lit windows. Rain + fog layers.
- Pedestrians who cross on red at zebra crossings.
- Glassmorphism dashboard: total vehicles, queued, avg wait, throughput
  (veh/min), cleared, active greens, congestion meter, live density
  sparklines, sim clock, FPS.
- Emergency preemption (feature-gated, default on): ambulance/police within
  120 px of a red gets the approach forced green; density managers skip
  preempted nodes; "EMS PRIORITY" badge shows at the node.
- On exit: `density_report.png` — same three signals the original plotted.

## Architecture

```
config.py            all constants + FEATURES toggles
core/network.py      19 roads, 9 nodes, signal positions   (original data, verbatim)
core/signals.py      countdown, phase rotation, add_extra_time (original logic)
core/density.py      density board + 28 manager configs    (original algorithm)
core/vehicles.py     170 vehicles, movement, turns, respawn (original logic)
stats.py             live metrics + exit report
render/…             sprites, environment, lighting, weather, pedestrians, HUD
main.py              fixed-timestep engine (0.1 s logic tick) + 60 FPS
                     interpolated renderer
```

Parity notes:
- Logic runs on a fixed 0.1 s accumulator — identical cadence to the
  original `time.sleep(0.1)` loop; 10 ticks = 1 signal-countdown second.
- Amber is **render-only** (last 2 s of green); the algorithm still sees
  only RED/GREEN, exactly like the original.
- `ACTIVE_MANAGERS = 20` in `config.py` mirrors the original loop
  (`range(0, 20)` over 28 configured managers). Set 28 to enable all.
- Vehicle types are cosmetic, keyed off the same random length — speeds
  and geometry unchanged.

MIT licensed, same as the original project.
