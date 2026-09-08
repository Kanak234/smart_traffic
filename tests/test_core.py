"""Regression tests for the simulator's deterministic, non-GUI core."""

import config as C
from core.density import DensityBoard, DensityManager
from core.network import build_signals
from core.signals import SignalController
from stats import Stats


def test_density_board_routes_missing_signal_to_the_dummy_bucket():
    board = DensityBoard()

    board.append("vehicle-1", -1, -1)

    assert board.count(C.DUMMY_NODE, 0) == 1
    assert board.real_total() == 0

    board.remove("vehicle-1", -1, -1)

    assert board.count(C.DUMMY_NODE, 0) == 0


def test_signal_countdown_rotates_to_the_next_head():
    signals = build_signals()
    controller = SignalController(signals)

    for _ in range(6):
        controller.second_tick()

    assert signals[0][0][0] == C.TIME_REM
    assert signals[0][0][1] == C.RED
    assert signals[0][1][1] == C.GREEN


def test_density_manager_forces_green_then_releases_on_low_density():
    signals = build_signals()
    controller = SignalController(signals)
    board = DensityBoard()
    manager = DensityManager(0, 1, 0, 9, 0, 9, 0, 9, 0)

    for vehicle_id in range(C.DENSITY_HIGH):
        board.append(vehicle_id, 1, 0)
    manager.get_density(board)
    manager.manage_density(signals, controller, board)

    assert manager.stat == 1
    assert [head[1] for head in signals[1]] == [C.GREEN, C.RED, C.RED]

    for vehicle_id in range(C.DENSITY_HIGH):
        board.remove(vehicle_id, 1, 0)
    manager.get_density(board)
    manager.manage_density(signals, controller, board)

    assert manager.stat == 0
    assert [head[1] for head in signals[1]] == [C.RED, C.GREEN, C.RED]


def test_preemption_holds_an_emergency_approach_then_expires():
    signals = build_signals()
    controller = SignalController(signals)

    controller.preempt(1, 2)

    assert [head[1] for head in signals[1]] == [C.RED, C.RED, C.GREEN]
    assert controller.is_preempted(1)

    for _ in range(C.EMERGENCY_HOLD_TICKS):
        controller.tick_preemption()

    assert not controller.is_preempted(1)


def test_stats_reports_density_clock_and_congestion():
    board = DensityBoard()
    board.append("a", 4, 0)
    board.append("b", 3, 1)
    board.append("c", 3, 0)
    board.append("d", -1, -1)
    stats = Stats(board)
    stats.passed = 5
    stats.wait_seconds = 17.0

    stats.second_sample()

    assert stats.series_t == [1]
    assert stats.series == {"Signal_1": [1], "Signal_2": [1], "Signal_3": [1]}
    assert stats.sim_clock() == "00:00:01"
    assert stats.avg_wait() == 17.0 / C.NO_OF_VEH
    assert stats.throughput_per_min() == 300.0
    assert stats.congestion_label()[0] == "LOW"
