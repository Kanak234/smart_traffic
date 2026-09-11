"""Tests for headless Simulator execution, lifecycle, events, and CLI."""

import os

import pygame as pg
import pytest

from main import Simulator, main


@pytest.fixture(autouse=True)
def dummy_video_driver():
    os.environ["SDL_VIDEODRIVER"] = "dummy"


def test_simulator_init_and_logic_ticks():
    sim = Simulator(seed=42, autoquit=0.5)
    assert sim.screen is not None
    assert len(sim.world.vehicles) > 0

    # Advance 15 logic ticks to cross a second mark
    for _ in range(15):
        sim.logic_tick()

    assert sim.tick_count == 15
    assert sim.stats.sim_seconds >= 1
    sim.shutdown()


def test_simulator_vehicle_rect_interpolation():
    sim = Simulator(seed=42)
    v = sim.world.vehicles[0]

    # Snap mode
    v.snap = True
    v.position_x, v.position_y = 100, 200
    v.direction = "East"
    rx, ry, rw, rh = sim._vehicle_rect(v, 0.5)
    assert rx == 100 and ry == 200

    # Interpolated mode
    v.snap = False
    v.prev_x, v.prev_y = 80, 200
    v.position_x, v.position_y = 100, 200
    rx, ry, rw, rh = sim._vehicle_rect(v, 0.5)
    assert rx == 90.0

    # Vertical vehicle
    v.direction = "North"
    rx, ry, rw, rh = sim._vehicle_rect(v, 0.5)
    assert rw == v.width and rh == v.length
    sim.shutdown()


def test_simulator_render_and_save_shot(tmp_path):
    sim = Simulator(seed=42)
    sim.logic_tick()
    sim.render(1.0, "RAIN")
    shot_path = sim.save_shot(str(tmp_path))
    assert os.path.isfile(shot_path)
    assert os.path.getsize(shot_path) > 1000
    sim.shutdown()


def test_simulator_event_handling():
    sim = Simulator(seed=42)

    # Space key toggles paused
    pg.event.post(pg.event.Event(pg.KEYDOWN, key=pg.K_SPACE))
    sim.handle_events()
    assert sim.paused is True

    pg.event.post(pg.event.Event(pg.KEYDOWN, key=pg.K_SPACE))
    sim.handle_events()
    assert sim.paused is False

    # Speed controls
    pg.event.post(pg.event.Event(pg.KEYDOWN, key=pg.K_PLUS))
    sim.handle_events()
    assert sim.time_scale == 2.0

    pg.event.post(pg.event.Event(pg.KEYDOWN, key=pg.K_MINUS))
    sim.handle_events()
    assert sim.time_scale == 1.0

    # Feature toggles
    for key in (pg.K_TAB, pg.K_t, pg.K_n, pg.K_c, pg.K_r, pg.K_f, pg.K_p, pg.K_e, pg.K_h):
        pg.event.post(pg.event.Event(pg.KEYDOWN, key=key))
        sim.handle_events()

    # Quit event
    pg.event.post(pg.event.Event(pg.QUIT))
    sim.handle_events()
    assert sim.running is False
    sim.shutdown()


def test_simulator_run_loop_autoquit():
    sim = Simulator(seed=42, autoquit=0.05)
    sim.run()
    assert not sim.running


def test_simulator_demo_shots(tmp_path):
    demo_dir = str(tmp_path / "demo_output")
    sim = Simulator(seed=42)
    sim.run_demo_shots(demo_dir, ticks=10)
    assert os.path.isfile(os.path.join(demo_dir, "shot_day.png"))
    assert os.path.isfile(os.path.join(demo_dir, "shot_night_rain.png"))
    assert os.path.isfile(os.path.join(demo_dir, "density_report.png"))


def test_cli_version(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])
    assert exc_info.value.code == 0


def test_cli_headless_autoquit():
    ret = main(["--headless", "--autoquit", "0.05", "--seed", "42"])
    assert ret == 0


def test_cli_demo_shots(tmp_path):
    out_dir = str(tmp_path / "cli_demo")
    ret = main(["--demo-shots", out_dir, "--ticks", "5", "--seed", "42"])
    assert ret == 0
    assert os.path.isfile(os.path.join(out_dir, "shot_day.png"))
