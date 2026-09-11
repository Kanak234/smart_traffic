# Technical Requirements Document (TRD) — Smart Traffic

## 1. Technical Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             Execution Modes                                 │
│   Interactive Pygame GUI (60 FPS)   │   Headless Batch / CI Engine (dummy)  │
└──────────────────────┬───────────────────────────────┬──────────────────────┘
                       │                               │
                       ▼                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       Simulation Engine (main.py)                           │
│  - Fixed logic accumulator: dt = 0.1s (10 logic ticks = 1 simulated second) │
│  - Timestep interpolation (alpha blending for visual smoothness)            │
│  - Signal controller tick & Emergency preemption checks                     │
└──────────────┬───────────────────────────────┬──────────────────────────────┘
               │                               │
               ▼                               ▼
┌──────────────────────────────┐ ┌────────────────────────────────────────────┐
│      Signal Management       │ │              Vehicle Dynamics              │
│  - SignalController          │ │  - TrafficWorld: 170 active vehicles       │
│  - 9 Network nodes (3-phase) │ │  - Kinematic updates (velocity, headway)   │
│  - Extra-time distribution   │ │  - Intersection turning & respawn loops    │
└──────────────┬───────────────┘ └─────────────────────┬──────────────────────┘
               │                                       │
               └───────────────────────┬───────────────┘
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Density Board & Metrics (stats.py)                       │
│  - DensityBoard: Spatial vehicle-to-lane mapping                            │
│  - 28 DensityManagers: Threshold-driven green signal expansion              │
│  - Stats sampler: throughput, wait time, and congestion levels              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 2. Technology Stack & Runtime Dependencies
- **Python Version:** Python >= 3.10 (verified across 3.10, 3.11, 3.12, and 3.13).
- **Core Dependencies:**
  - `pygame>=2.5.0` (or `pygame-ce>=2.5.0`): Simulation graphics rendering and event handling.
  - `numpy>=1.24.0`: Array manipulations, coordinate transformations, and vector math.
  - `matplotlib>=3.7.0`: Plotting and density report generation (`density_report.png`).
- **Development & Verification Dependencies:**
  - `pytest>=7.0.0`: Test runner.
  - `pytest-cov>=4.0.0`: Statement and branch coverage measurement.
  - `ruff>=0.4.0`: Linter and code quality validator.
  - `build`: Distribution packaging tool.

## 3. Subsystem Specifications

### 3.1 Network Topology & Coordinate System (`core/network.py`)
- Screen canvas size: `1200 x 780` pixels (`SCREEN_W x SCREEN_H`).
- Grid of 19 roads (`ROADS[1]` to `ROADS[19]`), partitioned into lanes with coordinates:
  - `x1, y1, x2, y2` boundaries for roadway envelopes.
  - Directional headings: `HORR` (0 degrees, East/West) and `VERR` (90 degrees, North/South).
- 9 Intersection Nodes: Each node connects up to 3 signal heads with indexed phases (`RED=0, GREEN=1, YELLOW/AMBER=2`).

### 3.2 Signal Timing & Preemption Engine (`core/signals.py`)
- `SignalController`:
  - `second_tick()`: Decrements countdown timers on active green heads. When expired, triggers round-robin phase change (`add_extra_time`).
  - `preempt(node_idx, head_idx)`: Immediately forces selected signal head to GREEN, sets all competing heads at the node to RED, and holds for `EMERGENCY_HOLD_TICKS`.
  - `tick_preemption()`: Manages preemption countdown and restores standard cycling upon expiration.

### 3.3 Density Board & Adaptive Control (`core/density.py`)
- `DensityBoard`: Hash map tracking `(node, approach)` vehicle occupancy.
  - `append(vehicle_id, node, head)` / `remove(vehicle_id, node, head)`.
  - `count(node, head)`: Returns queue length.
- `DensityManager`: Monitors two coupled approaches. If difference exceeds `DENSITY_HIGH`, extends green phase of the congested approach.

### 3.4 Vehicle Simulation & Physics (`core/vehicles.py`)
- Headway calculation: Vehicles enforce minimum distance to the vehicle ahead or stop line.
- Turning logic: Probability-weighted left, right, and straight trajectory assignments at node boundaries.
- Collision avoidance: Bounded deceleration prevents vehicle overlapping.

### 3.5 Headless Execution & Telemetry
- In environments without an X11/Wayland display server (e.g. GitHub Actions or Docker containers), setting `SDL_VIDEODRIVER=dummy` allows the entire simulation and rendering pipeline to execute headlessly.
- Post-run analytics are generated via `stats.export_report(path)`.

## 4. Packaging, Containerization & CI/CD
- **Package Manifest:** `pyproject.toml` with PEP 621 metadata, console script `smart-traffic = "main:main"`, setuptools packaging of `core` and `render`.
- **Docker Image:** Multi-stage unprivileged build using `python:3.12-slim`, non-root user `appuser` (UID 10001), default headless mode with automated health check.
- **CI Matrix:** Python 3.10, 3.11, 3.12, 3.13 executing `compileall`, `ruff check .`, pytest coverage gate (`--cov=core --cov=stats --cov=config --cov-fail-under=80`), and package build checks.
