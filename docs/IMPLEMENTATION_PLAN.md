# Implementation Plan — Smart Traffic Production Hardening (C1–C9)

## 1. Scope & Objective
Bring `Kanak234/smart_traffic` to complete enterprise production readiness fulfilling all 9 criteria (C1–C9):
- Standard PEP 621 packaging with console script `smart-traffic = "main:main"`.
- Multi-stage unprivileged Docker containerization (`appuser` UID 10001, SDL dummy driver).
- Comprehensive test coverage (>80% target, enforced barrier, zero synthetic mocks).
- Full CI/CD matrix across Python 3.10–3.13, CodeQL security scanning, Repository Guard, Dependabot.
- Robust headless execution, threat modeling, input validation, and release automation.

---

## 2. Work Breakdown Structure

### Phase 1: Context & Specifications [COMPLETE]
- [x] Establish PRD (`docs/PRD.md`)
- [x] Establish TRD (`docs/TRD.md`)
- [x] Establish Simulation UX Brief (`docs/SIMULATION_UX_BRIEF.md`)
- [x] Track Open Questions (`docs/OPEN_QUESTIONS.md`)
- [x] Establish Implementation Plan (`docs/IMPLEMENTATION_PLAN.md`)

### Phase 2: Packaging, CLI & Docker (C1, C6, C7)
- [ ] Implement `pyproject.toml` with PEP 621 metadata, `smart-traffic = "main:main"` console script, module discovery for `core` and `render`, and tool configs (`pytest`, `ruff`).
- [ ] Fix `main.py` CLI:
  - Wire up `autoquit` argument properly in `Simulator`.
  - Add `--headless` flag (setting `SDL_VIDEODRIVER=dummy` automatically).
  - Add `--version` argument (`smart-traffic 1.0.0`).
- [ ] Create multi-stage unprivileged `Dockerfile` (`appuser` UID 10001, headless dummy video driver support, container healthcheck) and `.dockerignore`.
- [ ] Clean up `.gitignore` for Python, Pygame, pytest, and build artifacts.

### Phase 3: Code Quality, Linting & Bug Fixes (C3, C6)
- [ ] Fix Ruff errors in `core/network.py` (remove semicolons, format signal coordinates).
- [ ] Fix unused imports in `core/vehicles.py` (`GREEN`) and `render/pedestrians.py` (`core.network`, unused `off`).
- [ ] Validate bytecode compilation with `python -m compileall -q .`.
- [ ] Ensure `ruff check .` passes with zero errors.

### Phase 4: Test Expansion & Verification (C2, C6)
- [ ] Expand test suite in `tests/test_core.py` or new test modules:
  - Test `core/vehicles.py`: `TrafficWorld` initialization, `motion_tick`, vehicle spawning, turning logic, collision avoidance, and state updates.
  - Test `core/signals.py`: `add_extra_time`, emergency preemption hold and countdown expiration, invalid node preemption safety.
  - Test `core/density.py`: All 28 manager evaluations, density board capacity, clear operations, and dummy node edge cases.
  - Test `stats.py`: Metrics calculations, sampling, throughput, congestion labels, and `export_report()` generation.
  - Test `main.py`: Headless CLI simulation runs (`--autoquit`, `--demo-shots`, `--seed`, `--help`, `--version`).
- [ ] Achieve >=80% statement coverage (target >=85%) with zero synthetic mocks.

### Phase 5: CI/CD & Security Workflows (C4, C5, C8)
- [ ] Create `SECURITY.md` covering threat model, headless sandboxing, and non-root execution.
- [ ] Update `.github/workflows/ci.yml` (matrix Python 3.10–3.13, compileall, ruff lint, pytest coverage gate, CLI test, package build).
- [ ] Add `.github/workflows/codeql.yml` for static security analysis.
- [ ] Add `.github/workflows/repository-guard.yml`.
- [ ] Add `.github/dependabot.yml`.
- [ ] Add `.github/workflows/release.yml` with SHA256 checksum generation.
- [ ] Create `CHANGELOG.md` for v1.0.0.
- [ ] Update `README.md` with status badges, CLI instructions, and architecture diagrams.

### Phase 6: Release, PR & Portfolio Reporting (C9)
- [ ] Verify `git diff --check` and clean working tree.
- [ ] Commit all hardening changes to `prod-hardening`.
- [ ] Push to `origin/prod-hardening`.
- [ ] Create GitHub Pull Request against `master`.
- [ ] Verify GitHub Actions CI runs pass.
- [ ] Create portfolio report `SMART_TRAFFIC_REPORT.md` in `/home/kanak/prod-hardening/`.
- [ ] Update portfolio tracking docs (`STATUS.md`, `PROGRESS.md`, `PORTFOLIO_HARDENING_MATRIX.md`, `PRODUCTION_READINESS_REPORT.md`, `TIER2_CANDIDATES.md`).
