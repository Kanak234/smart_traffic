# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-09-12

### Added
- **PEP 621 Standard Packaging:** Complete `pyproject.toml` configuration with console entry point `smart-traffic`.
- **Headless Execution Support:** Integrated `--headless` driver switch setting `SDL_VIDEODRIVER=dummy`, `--autoquit SECONDS` timeout, and `--version` CLI flags.
- **Production CI Matrix:** GitHub Actions workflows executing across Python 3.10, 3.11, 3.12, and 3.13.
- **Security & Quality Tooling:** Integrated CodeQL SAST, Repository Guard, Ruff linting, Dependabot weekly dependency tracking, and `SECURITY.md` threat model.
- **Automated Release Workflow:** Release automation on tag push with wheel/sdist packaging and SHA256 checksum generation (`SHA256SUMS.txt`).
- **Deterministic Test Suite:** Expanded test suite (`test_core.py`, `test_vehicles.py`, `test_stats.py`, `test_simulator.py`) achieving 96%+ statement coverage with zero synthetic mocks.
- **Containerization:** Multi-stage unprivileged Dockerfile running under non-root `appuser` (UID 10001) with embedded healthcheck.
- **Context Documentation:** Source of truth specifications added in `docs/` (`PRD.md`, `TRD.md`, `SIMULATION_UX_BRIEF.md`, `IMPLEMENTATION_PLAN.md`, `OPEN_QUESTIONS.md`).

### Changed
- Refactored `main.py` entry point to accept `argv` parameter for testability and programmatic invocation.
- Cleaned unused imports, removed semicolons, and formatted code cleanly according to Ruff.
- Hardened font caching in `render/assets.py` to gracefully handle Pygame initialization/teardown cycles.
