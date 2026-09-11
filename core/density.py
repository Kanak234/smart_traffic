"""
core/density.py — Queue-density bookkeeping and the synchronization brain.

`DensityManager` is the original `signal_density_manager` with identical
thresholds and identical green/red forcing behaviour. The `den_sig`
structure, `append/remove`, the 28 manager configurations, and the fact
that only the first `ACTIVE_MANAGERS` run per pass are all preserved.

Index -1 quirk: in the original, vehicles with no upcoming signal produced
(node, sig) == (-1, -1), which Python's negative indexing silently routed
into den_sig[9][0] — the dummy bucket. We route them there explicitly so
the accounting is byte-for-byte the same, minus the accident.
"""

import config as C
from config import GREEN, RED


class DensityBoard:
    """den_sig — a set of vehicle ids queued near each signal head."""

    def __init__(self):
        self.den_sig = [[set() for _ in range(4)]]           # node 0
        for _ in range(1, C.TOT_NODES):
            self.den_sig.append([set() for _ in range(3)])   # nodes 1..8
        self.den_sig.append([set()])                          # dummy node 9

    def _route(self, a, b):
        if a == -1 or b == -1:            # original negative-index behaviour
            return C.DUMMY_NODE, 0
        return a, b

    def append(self, veh_id, a, b):
        a, b = self._route(a, b)
        self.den_sig[a][b].add(veh_id)

    def remove(self, veh_id, a, b):
        a, b = self._route(a, b)
        self.den_sig[a][b].discard(veh_id)

    def count(self, a, b):
        return len(self.den_sig[a][b])

    def real_total(self):
        """Vehicles queued at actual signals (dummy bucket excluded)."""
        return sum(len(s) for node in self.den_sig[:C.TOT_NODES] for s in node)


class DensityManager:
    """Original signal_density_manager — one per monitored approach.

    (s0, n0) is the approach this manager owns; (s1..s3, n1..n3) are the
    upstream approaches that receive extra green time when this approach
    saturates. node id 9 means "no such neighbour".
    """

    __slots__ = ("number", "s0", "n0", "s1", "n1", "s2", "n2", "s3", "n3",
                 "stat", "self_density", "acc_den1", "acc_den2", "acc_den3")

    def __init__(self, contact, s0, n0, s1, n1, s2, n2, s3, n3):
        self.number = contact
        self.s0, self.n0 = s0, n0
        self.s1, self.n1 = s1, n1
        self.s2, self.n2 = s2, n2
        self.s3, self.n3 = s3, n3
        self.stat = 0
        self.self_density = self.acc_den1 = self.acc_den2 = self.acc_den3 = 0

    def get_density(self, board):
        self.self_density = board.count(self.s0, self.n0)
        self.acc_den1 = board.count(self.s1, self.n1)
        self.acc_den2 = board.count(self.s2, self.n2)
        self.acc_den3 = board.count(self.s3, self.n3)

    def manage_density(self, signals, controller, board):
        if self.self_density >= C.DENSITY_HIGH or self.stat == 1:
            self.stat = 1
            count = 3
            if self.s1 != 9 and self.acc_den1 <= C.DENSITY_HIGH:
                controller.add_extra_time(1, self.s1, self.n1)
                count -= 1
            if self.s2 != 9 and self.acc_den2 <= C.DENSITY_HIGH:
                if count == 2:
                    controller.add_extra_time(1, self.s2, self.n2)
                    count -= 1
                else:
                    controller.add_extra_time(1, self.s2, self.n2)
            if self.s3 != 9 and self.acc_den3 <= C.DENSITY_HIGH:
                if count == 1:
                    controller.add_extra_time(1, self.s3, self.n3)
                else:
                    controller.add_extra_time(1, self.s3, self.n3)
            sig_arr = [0, 1, 2, 3]
            if self.s0 != 0:
                sig_arr.remove(3)
            for h in range(len(sig_arr)):
                signals[self.s0][sig_arr[h]][1] = RED
            signals[self.s0][self.n0][1] = GREEN

        if self.self_density <= C.DENSITY_LOW or self.stat == 0:
            self.stat = 0
            sig_arr = [0, 1, 2, 3]
            if self.s0 != 0:
                sig_arr.remove(3)
            for h in range(len(sig_arr)):
                signals[self.s0][sig_arr[h]][1] = RED
            signals[self.s0][self.n0][1] = RED
            sig_arr.remove(self.n0)
            if len(sig_arr) == 1:
                signals[self.s0][sig_arr[0]][1] = GREEN
            else:
                if (board.count(self.s0, sig_arr[0])
                        >= board.count(self.s0, sig_arr[1])):
                    signals[self.s0][sig_arr[0]][1] = GREEN
                else:
                    signals[self.s0][sig_arr[1]][1] = GREEN


# ---- the 28 manager configurations, verbatim ------------------------------
_MANAGER_ARGS = (
    (2, 0, 0, 4, 0, 4, 1, 9, 0),
    (0, 0, 1, 9, 0, 9, 0, 9, 0),
    (0, 0, 2, 9, 0, 9, 0, 9, 0),
    (2, 0, 3, 8, 0, 8, 1, 9, 0),
    (0, 1, 0, 9, 0, 9, 0, 9, 0),
    (2, 1, 1, 2, 0, 3, 0, 9, 0),
    (1, 1, 2, 2, 2, 9, 0, 9, 0),
    (1, 2, 0, 1, 1, 9, 0, 9, 0),
    (2, 2, 1, 3, 1, 3, 2, 9, 0),
    (2, 2, 2, 6, 0, 2, 2, 9, 0),
    (2, 3, 0, 2, 0, 2, 2, 9, 0),
    (0, 3, 1, 9, 0, 9, 0, 9, 0),
    (2, 3, 2, 4, 1, 4, 2, 9, 0),
    (2, 4, 0, 3, 1, 3, 0, 9, 0),
    (3, 4, 1, 0, 2, 0, 1, 0, 3),
    (2, 4, 2, 7, 0, 7, 2, 9, 0),
    (0, 5, 0, 9, 0, 9, 0, 9, 0),
    (2, 5, 1, 6, 1, 6, 2, 9, 0),
    (0, 5, 2, 9, 0, 9, 0, 9, 0),
    (2, 6, 0, 5, 0, 5, 1, 9, 0),
    (2, 6, 1, 6, 0, 2, 1, 9, 0),
    (2, 6, 2, 7, 1, 2, 1, 9, 0),
    (2, 7, 0, 6, 0, 6, 1, 9, 0),
    (2, 7, 1, 4, 1, 4, 0, 9, 0),
    (0, 7, 2, 9, 0, 9, 0, 9, 0),
    (3, 8, 0, 0, 0, 0, 1, 0, 2),
    (0, 8, 1, 9, 0, 9, 0, 9, 0),
    (0, 8, 2, 9, 0, 9, 0, 9, 0),
)


def build_managers():
    return [DensityManager(*args) for args in _MANAGER_ARGS]


def manage_signal_system(managers, signals, controller, board):
    """Original manage_signal_system(): only the first ACTIVE_MANAGERS run,
    exactly like the original `range(0, 20)` loop. Preemption-locked nodes
    are skipped so an ambulance's green is not immediately overridden."""
    for i in range(C.ACTIVE_MANAGERS):
        m = managers[i]
        if controller.is_preempted(m.s0):
            continue
        m.get_density(board)
        m.manage_density(signals, controller, board)
    controller.notice_manager_pass()
