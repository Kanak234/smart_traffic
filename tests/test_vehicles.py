"""Comprehensive unit and behavioral tests for vehicle kinematics and motion."""

import random

import config as C
from core.density import DensityBoard, build_managers
from core.network import ROADS, build_signals
from core.signals import SignalController
from core.vehicles import TrafficWorld, Vehicle, _assign_type
from stats import Stats


def test_assign_type_mapping():
    rng = random.Random(42)
    assert _assign_type(15, rng) == "bike"
    assert _assign_type(17, rng) == "bike"
    assert _assign_type(24, rng) == "truck"
    assert _assign_type(26, rng) == "truck"
    assert _assign_type(27, rng) == "bus"
    assert _assign_type(30, rng) == "bus"

    # Mid-range lengths produce car/taxi/police/ambulance based on rng
    types = {_assign_type(20, random.Random(s)) for s in range(100)}
    assert "car" in types


def test_vehicle_initialization_and_attributes():
    v = Vehicle(1, 20, "red", 100, 200, 0, 1, "East", "car")
    assert v.idx == 1
    assert v.length == 20
    assert v.width == 10
    assert v.position_x == 100
    assert v.position_y == 200
    assert v.road_no == 0
    assert v.lane_no == 1
    assert v.direction == "East"
    assert v.vtype == "car"
    assert v.snap is True


def test_check_overlap_geometry():
    # HORR road overlap
    assert not TrafficWorld._check_overlap(C.HORR, 100, 200, 20, 10, 105, 202, 20, 10)
    assert TrafficWorld._check_overlap(C.HORR, 100, 200, 20, 10, 200, 200, 20, 10)
    assert TrafficWorld._check_overlap(C.HORR, 100, 200, 20, 10, 105, 250, 20, 10)

    # VERT road overlap
    assert not TrafficWorld._check_overlap(C.VERT, 200, 100, 20, 10, 202, 105, 20, 10)
    assert TrafficWorld._check_overlap(C.VERT, 200, 100, 20, 10, 200, 200, 20, 10)
    assert TrafficWorld._check_overlap(C.VERT, 200, 100, 20, 10, 250, 105, 20, 10)


def test_traffic_world_spawning_and_signals():
    signals = build_signals()
    controller = SignalController(signals)
    board = DensityBoard()
    managers = build_managers()
    stats = Stats(board)

    world = TrafficWorld(signals, controller, board, managers, stats, seed=123)
    assert len(world.vehicles) == C.NO_OF_VEH
    assert len(world.vehicles_in_each_lane) == len(ROADS)

    # Test get_random_direction for all junctions
    for j in range(9):
        for d in ("East", "West", "North", "South"):
            try:
                nxt = world.get_random_direction(d, j)
                assert nxt in ("East", "West", "North", "South")
            except (KeyError, ValueError):
                pass


def test_traffic_world_motion_tick_progression():
    signals = build_signals()
    controller = SignalController(signals)
    board = DensityBoard()
    managers = build_managers()
    stats = Stats(board)

    world = TrafficWorld(signals, controller, board, managers, stats, seed=42)

    # Run multiple motion ticks to exercise free driving, braking, and turns
    for _ in range(30):
        world.motion_tick()

    assert any(v.prev_x != v.position_x or v.prev_y != v.position_y for v in world.vehicles)


def test_traffic_world_out_of_bounds_respawn():
    signals = build_signals()
    controller = SignalController(signals)
    board = DensityBoard()
    managers = build_managers()
    stats = Stats(board)

    world = TrafficWorld(signals, controller, board, managers, stats, seed=42)

    v0 = world.vehicles[0]

    # Test East boundary respawn on road 5 (HORR, exits East > 1370)
    v0.road_no = 5
    v0.direction = "East"
    v0.position_x = 1400
    world.motion_tick()
    assert v0.snap is True
    assert stats.respawned >= 1

    # Test West boundary respawn on road 0 (HORR, exits West < 0)
    v0.road_no = 0
    v0.direction = "West"
    v0.position_x = -50
    world.motion_tick()
    assert stats.respawned >= 2

    # Test South boundary respawn on road 13 (VERT, exits South > 770)
    v0.road_no = 13
    v0.direction = "South"
    v0.position_y = 800
    world.motion_tick()
    assert stats.respawned >= 3

    # Test North boundary respawn on road 9 (VERT, exits North < 0)
    v0.road_no = 9
    v0.direction = "North"
    v0.position_y = -50
    world.motion_tick()
    assert stats.respawned >= 4


def test_traffic_world_turn_transitions_all_directions():
    signals = build_signals()
    controller = SignalController(signals)
    board = DensityBoard()
    managers = build_managers()
    stats = Stats(board)

    world = TrafficWorld(signals, controller, board, managers, stats, seed=42)

    # Set all signals green so whenever any vehicle reaches an intersection, it passes and turns
    for n in range(C.TOT_NODES):
        for s in range(len(signals[n])):
            signals[n][s][1] = C.GREEN

    # Run sufficient motion ticks for vehicles across the network to reach intersections and turn
    for _ in range(80):
        world.motion_tick()

    assert stats.passed > 0


def test_emergency_preemption_motion_trigger():
    signals = build_signals()
    controller = SignalController(signals)
    board = DensityBoard()
    managers = build_managers()
    stats = Stats(board)

    world = TrafficWorld(signals, controller, board, managers, stats, seed=42)

    # Make vehicle 0 an ambulance
    v = world.vehicles[0]
    v.vtype = "ambulance"
    v.road_no = 0
    v.direction = "East"
    # Position vehicle approaching signal stop line
    a, b, sp = world.get_info_from_veh(v.position_x, v.position_y, v.direction, v.road_no)
    if a != -1:
        signals[a][b][1] = C.RED
        v.position_x = sp - 20
        world.motion_tick()
        assert controller.is_preempted(a)
