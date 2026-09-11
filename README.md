# Smart Traffic Control — Synchronized Signal Network Simulator

[![CI](https://github.com/Kanak234/smart_traffic/actions/workflows/ci.yml/badge.svg)](https://github.com/Kanak234/smart_traffic/actions/workflows/ci.yml)
[![CodeQL Analysis](https://github.com/Kanak234/smart_traffic/actions/workflows/codeql.yml/badge.svg)](https://github.com/Kanak234/smart_traffic/actions/workflows/codeql.yml)
[![Python Versions](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue)](https://www.python.org/)
[![Coverage](https://img.shields.io/badge/coverage-96%25-brightgreen)](https://github.com/Kanak234/smart_traffic)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](Dockerfile)

Modern, realistic rewrite of the classic "Smart Street Light" traffic signal
synchronization project. **The original traffic algorithm is preserved
verbatim** — density-based signal management, extra-time distribution,
round-robin phase rotation, vehicle turning logic, respawn tables — with a
hardened fixed-timestep simulation core, comprehensive test coverage, and
reproducible packaging.

![day](docs/shot_day.png)

## Installation & Quick Start

### Standard Installation (PEP 621)

```bash
# Clone the repository
git clone https://github.com/Kanak234/smart_traffic.git
cd smart_traffic

# Set up virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install the package and dependencies
pip install --upgrade pip
pip install -e .
```

### Running the Simulator

Launch the interactive simulation GUI:
```bash
smart-traffic
# or alternatively:
python3 main.py
```

### Headless & Automated Execution

Run headlessly inside CI or containers without an X11 display:
```bash
# Run headlessly and exit after 10 simulated seconds, exporting density_report.png
smart-traffic --headless --autoquit 10.0 --seed 42

# Capture demo snapshot frames and analytics report headlessly
smart-traffic --demo-shots out/ --ticks 420
```

### Docker Container

```bash
# Build unprivileged container image
docker build -t smart-traffic .

# Run headless simulation inside container
docker run --rm -v $(pwd)/output:/app/output smart-traffic --headless --autoquit 15.0 --seed 42
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

## Testing & Verification

Run the test suite with coverage enforcement:
```bash
# Run pytest with 80%+ statement coverage gate
pytest

# Check code quality and style with Ruff
ruff check .

# Verify strict bytecode syntax compilation
python3 -m compileall -q .
```

## Documentation

Full context specifications and architecture documents:
- [Product Requirements Document (PRD)](docs/PRD.md)
- [Technical Requirements Document (TRD)](docs/TRD.md)
- [Simulation UX Brief](docs/SIMULATION_UX_BRIEF.md)
- [Implementation Plan](docs/IMPLEMENTATION_PLAN.md)
- [Open Questions & Decisions](docs/OPEN_QUESTIONS.md)
- [Security Policy](SECURITY.md)
- [Changelog](CHANGELOG.md)

## License

MIT licensed, same as the original project.
