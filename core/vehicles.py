"""
core/vehicles.py — Vehicle population and per-tick motion.

Spawn placement (choose_lane / generate_random_coordinates / check_overlap /
choose_position / initialise_vehicles), signal lookup (get_info_from_veh /
get_signal_info), turning (get_random_direction + the four direction blocks)
and the respawn tables are functionally identical to the original main.py —
including its quirks (e.g. negative-index density routing) so the emergent
traffic behaviour is the same.

New, additive layers that do not alter the base motion:
  * vehicle *type* (car/taxi/police/ambulance/bike/truck/bus) — purely a
    sprite choice keyed off the same random length the original generated;
  * previous-position bookkeeping so the renderer can interpolate between
    logic ticks (with a snap flag for turns/respawns);
  * wait-time / throughput statistics;
  * emergency preemption trigger (feature-gated).
"""

import random

import config as C
from config import RED, GREEN, HORR
from core import network
from core.network import ROADS, ROAD_LANES


CHOOSE_POSITION_FAILED = (-1, -1)

_COLOUR_NAMES = tuple(C.CAR_PAINTS.keys())


class Vehicle:
    __slots__ = ("idx", "position_x", "position_y", "length", "width",
                 "colour", "road_no", "lane_no", "direction", "vtype",
                 "prev_x", "prev_y", "snap", "wait_ticks", "total_wait",
                 "brake", "moved")

    def __init__(self, idx, length, colour, position_x, position_y,
                 road_no, lane_no, direction, vtype):
        self.idx = idx
        self.position_x = position_x
        self.position_y = position_y
        self.length = length
        self.width = 10
        self.colour = colour
        self.road_no = road_no
        self.lane_no = lane_no
        self.direction = direction
        self.vtype = vtype
        self.prev_x = position_x
        self.prev_y = position_y
        self.snap = True
        self.wait_ticks = 0        # current continuous wait at a red
        self.total_wait = 0.0      # lifetime seconds spent waiting
        self.brake = False         # brake lights this tick
        self.moved = False


def _assign_type(length, rng):
    """Visual class from the SAME random length the original rolled."""
    if length <= 17:
        return "bike"
    if length >= 27:
        return "bus"
    if length >= 24:
        return "truck"
    roll = rng.random()
    acc = 0.0
    for name, p in C.FLEET_SPECIAL.items():
        acc += p
        if roll < acc:
            return name
    return "car"


class TrafficWorld:
    """Owns vehicles + reproduces the original module-level motion logic."""

    def __init__(self, signals, controller, board, managers, stats, seed=None):
        self.signals = signals
        self.controller = controller
        self.board = board
        self.managers = managers
        self.stats = stats
        self.rng = random.Random(seed)
        self.vehicles = []
        self.vehicles_in_each_lane = [
            [[] for _ in range(1, len(ROAD_LANES[i]))]
            for i in range(len(ROAD_LANES))
        ]
        self._initialise_vehicles()

    # ------------------------------------------------------------------ spawn
    def _choose_lane(self, road_no):
        lane_no = self.rng.randint(1, len(ROAD_LANES[road_no]) - 1)
        return (lane_no, ROAD_LANES[road_no][lane_no], ROAD_LANES[road_no][0])

    def _generate_random_coordinates(self, symm, lane_dims, common_dims,
                                     length, width):
        if symm == HORR:
            x = self.rng.randint(common_dims[0], common_dims[1] - length)
            y = (lane_dims[0] + lane_dims[1] - width) // 2
        else:
            x = (lane_dims[0] + lane_dims[1] - width) // 2
            y = self.rng.randint(common_dims[0], common_dims[1] - length)
        return x, y

    @staticmethod
    def _check_overlap(symm, vx, vy, vlen, vwid, tx, ty, length, width):
        if symm == HORR:
            if (0 <= vx - tx <= length or 0 <= tx - vx <= vlen):
                return not (0 <= vy - ty <= width or 0 <= ty - vy <= vwid)
            return True
        if (0 <= vx - tx <= width or 0 <= tx - vx <= vwid):
            return not (0 <= vy - ty <= length or 0 <= ty - vy <= vlen)
        return True

    def _choose_position(self, road_no, lane_no, lane_dims, common_dims,
                         length, width):
        tx, ty = self._generate_random_coordinates(
            ROADS[road_no].symm, lane_dims, common_dims, length, width)
        i = 0
        change_count = 0
        while i < len(self.vehicles) and change_count <= 100:
            v = self.vehicles[i]
            if v.road_no == road_no and v.lane_no == lane_no:
                ok = self._check_overlap(ROADS[road_no].symm, v.position_x,
                                         v.position_y, v.length, v.width,
                                         tx, ty, length, width)
                if not ok:
                    tx, ty = self._generate_random_coordinates(
                        ROADS[road_no].symm, lane_dims, common_dims,
                        length, width)
                    change_count += 1
                    i = 0
                    continue
            i += 1
        if i >= len(self.vehicles):
            return tx, ty
        return CHOOSE_POSITION_FAILED

    def _initialise_vehicles(self):
        for i in range(C.NO_OF_VEH):
            attempt = 0
            length = self.rng.randint(15, 30)
            width = 10
            colour = self.rng.choice(_COLOUR_NAMES)
            pos = CHOOSE_POSITION_FAILED
            road_no = lane_no = -1
            lane_dims = common_dims = None
            while pos == CHOOSE_POSITION_FAILED and attempt < 100:
                road_no = self.rng.randint(0, 18)
                lane_no, lane_dims, common_dims = self._choose_lane(road_no)
                pos = self._choose_position(road_no, lane_no, lane_dims,
                                            common_dims, length, width)
                attempt += 1
            if pos == CHOOSE_POSITION_FAILED:
                print(f"Too many vehicles ({i + 1}) placed")
                return
            if ROADS[road_no].symm == HORR:
                direction = ("East" if lane_no <= (len(ROAD_LANES[road_no]) - 1) // 2
                             else "West")
            else:
                direction = ("North" if lane_no <= (len(ROAD_LANES[road_no]) - 1) // 2
                             else "South")
            vtype = _assign_type(length, self.rng)
            self.vehicles.append(Vehicle(i, length, colour, pos[0], pos[1],
                                         road_no, lane_no, direction, vtype))
            self.vehicles_in_each_lane[road_no][lane_no - 1].append(i)

    # -------------------------------------------------------- signal lookups
    def get_info_from_veh(self, pos_x, pos_y, veh_dir, root_no):
        node_lst = ROADS[root_no].next_nodes
        if len(node_lst) == 1:
            node_id = node_lst[0]
        else:
            node_id = node_lst[0] if veh_dir in ("West", "North") else node_lst[1]
        pos = network.node_pos(node_id)

        road = ROADS[root_no]
        if road.symm == HORR:
            if len(node_lst) == 1:
                if ((veh_dir == "East" and pos[0] - pos_x < 0)
                        or (veh_dir == "West" and pos[0] - pos_x > 0)):
                    return -1, -1, -1
            sig_pos = road.l_end if veh_dir == "East" else road.l_start
        else:
            if len(node_lst) == 1:
                if ((veh_dir == "South" and pos[1] - pos_y < 0)
                        or (veh_dir == "North" and pos[1] - pos_y > 0)):
                    return -1, -1, -1
            sig_pos = road.l_end if veh_dir == "South" else road.l_start
        sig_id = network.signal_id(node_id, sig_pos)
        return node_id, sig_id, sig_pos

    def get_signal_info(self, pos_x, pos_y, veh_dir, root_no):
        node_id, sig_id, sig_pos = self.get_info_from_veh(
            pos_x, pos_y, veh_dir, root_no)
        if node_id == -1:
            return 0, -1, -1
        sig_state = self.signals[node_id][sig_id][1]
        near = pos_x if veh_dir in ("East", "West") else pos_y
        if abs(sig_pos - near) < C.SIGNAL_RANGE_PX:
            return 1, sig_state, node_id
        return 0, sig_state, node_id

    def get_random_direction(self, direction, present_c):
        reverse = {"East": "West", "West": "East",
                   "North": "South", "South": "North"}[direction]
        table = {
            0: ["East", "West", "South", "North"],
            1: ["East", "West", "North"],
            2: ["East", "West", "South"],
            3: ["East", "West", "North"],
            4: ["East", "West", "South"],
            5: ["East", "West", "South"],
            6: ["East", "West", "North"],
            7: ["West", "South", "North"],
            8: ["East", "South", "North"],
        }
        arr = list(table[present_c])
        arr.remove(reverse)
        return arr[self.rng.randint(0, len(arr) - 1)]

    # --------------------------------------------------------------- per tick
    def motion_tick(self):
        """One logic tick — the original motion() body, order preserved."""
        signals = self.signals
        board = self.board
        for i in range(len(self.vehicles)):
            v = self.vehicles[i]
            v.prev_x, v.prev_y = v.position_x, v.position_y
            v.snap = False
            v.brake = False
            v.moved = False

            k, signal_status, node_id = self.get_signal_info(
                v.position_x, v.position_y, v.direction, v.road_no)

            # ---- density pre-condition (verbatim, incl. -1 index quirk)
            a, b, _sp = self.get_info_from_veh(
                v.position_x, v.position_y, v.direction, v.road_no)
            l1 = signals[a][b][2][0]
            l2 = signals[a][b][2][1]
            mod_x = abs(l1 - v.position_x)
            mod_y = abs(l2 - v.position_y)
            if (mod_x - C.DENSITY_REF < C.DENSITY_RADIUS
                    or mod_y - C.DENSITY_REF < C.DENSITY_RADIUS):
                board.append(i, a, b)

            # ---- emergency preemption (additive feature)
            if (C.FEATURES["emergency"] and v.vtype in ("ambulance", "police")
                    and a != -1 and signals[a][b][1] == RED):
                axis = v.position_x if v.direction in ("East", "West") else v.position_y
                if abs(_sp - axis) < C.EMERGENCY_RANGE_PX:
                    self.controller.preempt(a, b)
                    signal_status = signals[a][b][1] if k else signal_status

            # ---- out-of-bounds respawn (verbatim tables)
            ch_r = self.rng.randint(0, 9)
            if v.road_no in network.OUT_ROADS:
                change = 0
                if v.direction == "East" and v.position_x > 1370:
                    change = 1
                elif v.direction == "West" and v.position_x < 0:
                    change = 1
                elif v.direction == "South" and v.position_y > 770:
                    change = 1
                elif v.direction == "North" and v.position_y < 0:
                    change = 1
                if change:
                    v.position_x = network.RESPAWN_X[ch_r]
                    v.position_y = network.RESPAWN_Y[ch_r]
                    v.road_no = network.RESPAWN_ROAD[ch_r]
                    v.direction = network.RESPAWN_DIR[ch_r]
                    v.snap = True
                    self.stats.respawned += 1
                    continue

            # ---- free driving (not in signal range)
            if k == 0:
                if v.direction == "East":
                    v.position_x += C.VEH_STEP_PX
                elif v.direction == "West":
                    v.position_x -= C.VEH_STEP_PX
                elif v.direction == "North":
                    v.position_y -= C.VEH_STEP_PX
                elif v.direction == "South":
                    v.position_y += C.VEH_STEP_PX
                v.moved = True
                continue

            # ---- held at a red within range
            if signal_status == 0 and k != 0:
                v.brake = True
                v.wait_ticks += 1
                v.total_wait += C.LOGIC_TICK
                self.stats.wait_seconds += C.LOGIC_TICK
                continue

            # ---- green and in range: choose a turn and hop to next road
            if signal_status == 1 and k != 0:
                direction1 = self.get_random_direction(v.direction, node_id)
                board.remove(i, a, b)
                self.stats.passed += 1
                self.stats.node_pass[node_id] += 1
                v.wait_ticks = 0
            else:                       # unreachable, mirrors original flow
                continue

            lane_pick = 0
            rn = ROADS[v.road_no].r_next
            if v.direction == "North":
                if direction1 == "North":
                    v.road_no = rn[0][0]
                    v.position_y = ROADS[v.road_no].l_end + 15
                elif direction1 == "East":
                    v.road_no = rn[0][2]
                    if ROADS[v.road_no].lane == 4:
                        lane_pick = self.rng.randint(0, 1)
                    v.position_y = ROADS[v.road_no].w_start + 10 + 30 * lane_pick
                    v.position_x = ROADS[v.road_no].l_start + 15
                elif direction1 == "West":
                    v.road_no = rn[0][3]
                    if ROADS[v.road_no].lane == 4:
                        lane_pick = self.rng.randint(0, 1)
                    v.position_y = ROADS[v.road_no].w_end - 15 - 30 * lane_pick
                    v.position_x = ROADS[v.road_no].l_end - 15
            elif v.direction == "South":
                if direction1 == "South":
                    v.road_no = rn[1][1]
                    v.position_y = ROADS[v.road_no].l_start
                elif direction1 == "East":
                    v.road_no = rn[1][2]
                    if ROADS[v.road_no].lane == 4:
                        lane_pick = self.rng.randint(0, 1)
                    v.position_y = ROADS[v.road_no].w_start + 10 + 30 * lane_pick
                    v.position_x = ROADS[v.road_no].l_start
                elif direction1 == "West":
                    v.road_no = rn[1][3]
                    if ROADS[v.road_no].lane == 4:
                        lane_pick = self.rng.randint(0, 1)
                    v.position_y = ROADS[v.road_no].w_end - 15 - 30 * lane_pick
                    v.position_x = ROADS[v.road_no].l_end - 15
            elif v.direction == "East":
                if direction1 == "East":
                    v.road_no = rn[0][2]
                    v.position_x = ROADS[v.road_no].l_start
                elif direction1 == "North":
                    v.road_no = rn[0][0]
                    if ROADS[v.road_no].lane == 4:
                        lane_pick = self.rng.randint(0, 1)
                    v.position_x = ROADS[v.road_no].w_start + 15 + 30 * lane_pick
                    v.position_y = ROADS[v.road_no].l_end - 15
                elif direction1 == "South":
                    v.road_no = rn[0][1]
                    if ROADS[v.road_no].lane == 4:
                        lane_pick = self.rng.randint(0, 1)
                    v.position_x = ROADS[v.road_no].w_end - 15 - 30 * lane_pick
                    v.position_y = ROADS[v.road_no].l_start
            elif v.direction == "West":
                if direction1 == "West":
                    v.road_no = rn[1][3]
                    v.position_x = ROADS[v.road_no].l_end - 15
                elif direction1 == "South":
                    v.road_no = rn[1][1]
                    if ROADS[v.road_no].lane == 4:
                        lane_pick = self.rng.randint(0, 1)
                    v.position_x = ROADS[v.road_no].w_end - 15 - 30 * lane_pick
                    v.position_y = ROADS[v.road_no].l_start
                elif direction1 == "North":
                    v.road_no = rn[1][0]
                    if ROADS[v.road_no].lane == 4:
                        lane_pick = self.rng.randint(0, 1)
                    v.position_x = ROADS[v.road_no].w_start + 15 + 30 * lane_pick
                    v.position_y = ROADS[v.road_no].l_end - 15

            v.direction = direction1
            v.snap = True
            # original called manage_signal_system() after every turn:
            from core.density import manage_signal_system
            manage_signal_system(self.managers, self.signals,
                                 self.controller, board)
