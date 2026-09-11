"""
core/signals.py — Signal phase timing.

`SignalController.second_tick()` is the original `signal_show()` countdown
(one call per simulated second) and `add_extra_time()` is copied verbatim —
these two functions plus the density managers ARE the synchronization
algorithm, so their arithmetic is untouched.

New, render-only additions:
  * per-signal amber bookkeeping (last N seconds of a counted-down green,
    or a short amber flash after the density manager force-switches a head)
  * emergency preemption (feature-gated, layered on top of the base logic)
"""

import config as C
from config import GREEN, RED, TIME_REM
from core import network


class SignalController:
    def __init__(self, signals):
        self.signals = signals                    # shared mutable structure
        self.sim_seconds = 0
        # (node, sig) → sim_second when the head last flipped, for amber FX
        self.forced_amber_until = {}
        self.last_state = {}
        self._snapshot_states()
        # emergency preemption
        self.preempted = {}                       # node → ticks remaining

    # -- original signal_show() -------------------------------------------
    def second_tick(self):
        """Advance every green head's countdown by one simulated second."""
        self.sim_seconds += 1
        signals = self.signals
        for node_id in range(C.TOT_NODES):
            ts = 4 if node_id == 0 else 3
            for sig_id in range(ts):
                if signals[node_id][sig_id][1] == GREEN:
                    if signals[node_id][sig_id][0]:
                        signals[node_id][sig_id][0] -= 1
                    else:
                        signals[node_id][sig_id][0] = TIME_REM
                        signals[node_id][sig_id][1] = RED
                        temp = sig_id + 1
                        if temp > (ts - 1):
                            temp = 0
                        signals[node_id][temp][1] = GREEN
        self._detect_forced_switches()

    # -- original add_extra_time() (verbatim arithmetic) --------------------
    def add_extra_time(self, time, node_id, sig_id):
        signals = self.signals
        if node_id == 0:
            ts = 3
            quo = time % 3
            rem = time // 3
        else:
            ts = 1
            quo = time % 2
            rem = time // 2
        temp = sig_id
        offset = 1
        for _ in range(ts):
            quo -= 1
            if quo < 0:
                offset = 0
            temp += 1
            if temp > ts:
                temp = 0
            signals[node_id][temp][0] += (rem + offset)

    # -- amber bookkeeping (render only) ------------------------------------
    def _snapshot_states(self):
        for n in range(C.TOT_NODES):
            for s in range(network.signals_per_node(n)):
                self.last_state[(n, s)] = self.signals[n][s][1]

    def _detect_forced_switches(self):
        """Any green→red flip earns a short amber flash for realism."""
        for n in range(C.TOT_NODES):
            for s in range(network.signals_per_node(n)):
                prev = self.last_state[(n, s)]
                cur = self.signals[n][s][1]
                if prev == GREEN and cur == RED:
                    self.forced_amber_until[(n, s)] = (
                        self.sim_seconds + C.AMBER_AFTER_FORCE)
                self.last_state[(n, s)] = cur

    def notice_manager_pass(self):
        """Called after density managers run (they flip heads directly)."""
        self._detect_forced_switches()

    def visual_state(self, node_id, sig_id):
        """RED / AMBER / GREEN for the renderer (AMBER == 2).

        Pure presentation: vehicles still read the raw RED/GREEN state, so
        behaviour matches the original exactly — amber is what a driver
        would *see* in the last moments of a phase.
        """
        head = self.signals[node_id][sig_id]
        if head[1] == GREEN:
            if head[0] <= C.AMBER_WINDOW - 1:      # last seconds of green
                return 2
            return GREEN
        if self.forced_amber_until.get((node_id, sig_id), -1) >= self.sim_seconds:
            return 2
        return RED

    # -- emergency preemption (additive feature) -----------------------------
    def preempt(self, node_id, sig_id):
        """Force one approach green for an emergency vehicle."""
        if not C.FEATURES["emergency"]:
            return
        ts = network.signals_per_node(node_id)
        for s in range(ts):
            self.signals[node_id][s][1] = RED
        self.signals[node_id][sig_id][1] = GREEN
        if self.signals[node_id][sig_id][0] < 3:
            self.signals[node_id][sig_id][0] = 3
        self.preempted[node_id] = C.EMERGENCY_HOLD_TICKS
        self._detect_forced_switches()

    def tick_preemption(self):
        for node in list(self.preempted):
            self.preempted[node] -= 1
            if self.preempted[node] <= 0:
                del self.preempted[node]

    def is_preempted(self, node_id):
        return node_id in self.preempted
