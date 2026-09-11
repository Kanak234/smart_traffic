"""Regression tests for the simulator's deterministic, non-GUI core."""

import pytest

import config as C
from core.density import DensityBoard, DensityManager, build_managers, manage_signal_system
from core.network import (
    approach_geometry,
    build_signals,
    intersection_rects,
    node_pos,
    road_rect,
    signal_id,
    signals_per_node,
)
from core.signals import SignalController


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


def test_preemption_disabled_feature_gate():
    signals = build_signals()
    controller = SignalController(signals)
    orig = C.FEATURES["emergency"]
    try:
        C.FEATURES["emergency"] = False
        controller.preempt(1, 2)
        assert not controller.is_preempted(1)
    finally:
        C.FEATURES["emergency"] = orig


def test_signal_controller_add_extra_time_and_visual_states():
    signals = build_signals()
    controller = SignalController(signals)

    # Node 0 distribution (ts = 3)
    controller.add_extra_time(5, 0, 0)
    # Node 1 distribution (ts = 1)
    controller.add_extra_time(4, 1, 0)

    # Visual states: Green head countdown
    signals[0][0][1] = C.GREEN
    signals[0][0][0] = 5
    assert controller.visual_state(0, 0) == C.GREEN

    # Amber window check
    signals[0][0][0] = C.AMBER_WINDOW - 1
    assert controller.visual_state(0, 0) == 2  # Amber

    # Forced amber check
    signals[0][0][1] = C.RED
    controller.notice_manager_pass()
    assert controller.visual_state(0, 0) == 2  # Forced amber active

    controller.sim_seconds += C.AMBER_AFTER_FORCE + 2
    assert controller.visual_state(0, 0) == C.RED


def test_signal_preemption_time_floor():
    signals = build_signals()
    controller = SignalController(signals)
    signals[2][1][0] = 1  # less than 3
    controller.preempt(2, 1)
    assert signals[2][1][0] >= 3


def test_network_geometry_and_lookups():
    assert node_pos(0) == [1042, 260]
    assert signals_per_node(0) == 4
    assert signals_per_node(1) == 3

    assert signal_id(0, 980) == 0
    with pytest.raises(AssertionError, match="not on node"):
        signal_id(0, 99999)

    r_horr = road_rect(0)
    assert len(r_horr) == 4
    assert r_horr[2] > 0 and r_horr[3] > 0

    r_vert = road_rect(1)
    assert len(r_vert) == 4
    assert r_vert[2] > 0 and r_vert[3] > 0

    rects = intersection_rects()
    assert len(rects) == C.TOT_NODES

    approaches = approach_geometry()
    assert (0, 0) in approaches
    assert "stop" in approaches[(0, 0)]
    assert "lamp" in approaches[(0, 0)]
    assert "axis" in approaches[(0, 0)]


def test_density_manager_multi_neighbour_and_system_sweep():
    signals = build_signals()
    controller = SignalController(signals)
    board = DensityBoard()

    managers = build_managers()
    assert len(managers) == 28

    # Multi-neighbour manager (manager 14: (3, 4, 1, 0, 2, 0, 1, 0, 3))
    m14 = managers[14]
    for v in range(C.DENSITY_HIGH + 2):
        board.append(v, m14.s0, m14.n0)
    m14.get_density(board)
    m14.manage_density(signals, controller, board)
    assert m14.stat == 1

    # Node 0 density manager (4 heads)
    m0 = managers[0]
    board.append(999, m0.s0, m0.n0)
    m0.get_density(board)
    m0.manage_density(signals, controller, board)

    # manage_signal_system execution and preemption skipping
    controller.preempt(managers[0].s0, 0)
    manage_signal_system(managers, signals, controller, board)
