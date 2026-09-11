# Product Requirements Document (PRD) — Smart Traffic

## 1. Product Overview
Smart Traffic is an enterprise-hardened, synchronized multi-intersection traffic signal network simulation engine. It models a complex urban road grid comprising 19 interconnected roads, 9 traffic nodes, 170 active vehicles across 7 distinct classes, and 28 density-based signal managers. It preserves the classic density-sensitive signal timing algorithm verbatim while delivering high-performance headless execution, fixed-timestep physics, and real-time operational telemetry.

## 2. Problem Statement
Urban traffic gridlock causes excessive vehicular wait times, increased fuel consumption, elevated emissions, and delayed emergency response vehicles. Traditional fixed-timer signals cannot adapt to dynamic congestion spikes or emergency dispatch routes.

Smart Traffic provides an adaptable, deterministic simulation platform that:
1. Dynamically balances green signal durations based on real-time lane queue density.
2. Distributes extra green time to downstream congested corridors.
3. Provides emergency vehicle preemption (forcing green corridors for ambulances and police vehicles).
4. Tracks system-wide throughput, average wait times, and congestion metrics, exporting analytical reports upon simulation termination.

## 3. Goals and Non-Goals

### Goals
- **Algorithm Parity:** Preserve the core density-based signal scheduling and phase rotation logic with 100% deterministic accuracy.
- **Deterministic Headless Operation:** Support headless execution via `SDL_VIDEODRIVER=dummy` and command-line flags (`--autoquit`, `--demo-shots`, `--seed`) for automated testing, CI pipelines, and batch benchmarking.
- **Production Hardening (C1–C9):**
  - Standard PEP 621 packaging with console script entry point `smart-traffic = "main:main"`.
  - Comprehensive unit and integration test suite achieving >=80% statement coverage with zero synthetic mocks.
  - Multi-stage unprivileged Docker containerization running as `appuser` (UID 10001).
  - Clean Ruff linting, compileall syntax validation, and CodeQL security analysis.
  - Release automation with SHA256 checksums and Keep a Changelog documentation.

### Non-Goals
- **Physical Roadside Controller Interfacing:** Smart Traffic is a simulation and analysis engine; it does not directly transmit wire signals to physical NEMA TS2 controllers.
- **Geographic Information Systems (GIS) Ingestion:** The network topology is modeled on a canonical 19-road, 9-node urban grid rather than live OpenStreetMap data.

## 4. Target Users
- **Traffic Engineers & Urban Planners:** Evaluating adaptive signal timing strategies and emergency preemption behavior.
- **Researchers & Educators:** Studying queueing theory, vehicle routing, and decentralized congestion management.
- **Autonomous Systems Developers:** Testing simulated sensor feeds and vehicle density heuristics in a deterministic sandbox.

## 5. Functional Requirements

### FR-1: Network & Topology Model (`core/network.py`)
- Define 19 road segments with defined lane geometry (`ROAD_LANES`), orientations (Horizontal/Vertical), and spatial boundaries.
- Define 9 intersection nodes with signal configurations, coordinates, and turning permissions.

### FR-2: Signal Controller & Preemption (`core/signals.py`)
- Support countdown timers, round-robin phase rotation, and extra-time distribution across signal heads.
- Emergency preemption: Detect emergency vehicles within distance threshold (`C.EMERGENCY_HOLD_TICKS`) and force green approach, locking out competing phases.

### FR-3: Density Management Engine (`core/density.py`)
- Track vehicle count per node and approach lane via `DensityBoard`.
- Evaluate 28 density managers (`ACTIVE_MANAGERS` configurable) comparing queue thresholds (`DENSITY_HIGH`, `DENSITY_LOW`) and overriding signal durations.

### FR-4: Vehicle Dynamics & Lifecycle (`core/vehicles.py`)
- Manage 170 vehicles across 7 classes (car, taxi, police, ambulance, bike, truck, bus).
- Handle forward motion, safe following distance, signal compliance, intersection turning, and respawn loops.

### FR-5: Telemetry & Analytics (`stats.py`)
- Sample queue depths, passed vehicle count, cumulative delay, and throughput per minute.
- Generate post-simulation density reports (`density_report.png` or tabular metrics).

### FR-6: CLI & Headless Execution (`main.py`)
- Headless execution flags: `--demo-shots <dir>`, `--ticks <n>`, `--autoquit <sec>`, `--seed <int>`, `--version`, `--headless`.
- Exit with code 0 on successful completion.

## 6. Acceptance Criteria
1. Clean PEP 621 `pyproject.toml` with console script `smart-traffic = "main:main"`.
2. Multi-stage unprivileged `Dockerfile` (UID 10001) with headless execution support.
3. Test suite achieving >=80% statement coverage across core modules with zero synthetic mocks.
4. Clean Ruff static analysis (`ruff check .`) and bytecode compilation (`python -m compileall -q .`).
5. GitHub Actions CI matrix across Python 3.10–3.13, CodeQL static analysis, Repository Guard, and Dependabot.
6. Comprehensive `SECURITY.md`, `CHANGELOG.md`, and updated `README.md`.
