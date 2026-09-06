"""
stats.py — Live simulation metrics + end-of-run analytics export.

The original project popped a blocking matplotlib bar chart every 20 frames,
which throttled the render loop badly. Here the same three densities
(den_sig[4][0], den_sig[3][1], den_sig[3][0] — exactly the signals the
original charted) are sampled every simulated second into a time series,
drawn live on the in-game dashboard, and written out as a proper
matplotlib report (`density_report.png`) when the simulation exits.
"""

import time
from collections import deque

import config as C


class Stats:
    def __init__(self, board):
        self.board = board
        self.t0 = time.time()
        self.sim_seconds = 0
        self.passed = 0                 # vehicles cleared through a green
        self.respawned = 0
        self.wait_seconds = 0.0         # cumulative vehicle-seconds waited
        self.node_pass = [0] * C.TOT_NODES
        self.fps = 0.0
        # rolling series for the dashboard sparkline + final report
        self.series_t = []
        self.series = {"Signal_1": [], "Signal_2": [], "Signal_3": []}
        self.throughput_window = deque(maxlen=60)   # per-second pass counts
        self._passed_last_second = 0
        self.congestion = 0.0

    # sampled once per simulated second ------------------------------------
    def second_sample(self):
        self.sim_seconds += 1
        b = self.board
        self.series_t.append(self.sim_seconds)
        self.series["Signal_1"].append(b.count(4, 0))
        self.series["Signal_2"].append(b.count(3, 1))
        self.series["Signal_3"].append(b.count(3, 0))
        for k in self.series:
            if len(self.series[k]) > 600:
                self.series[k] = self.series[k][-600:]
        if len(self.series_t) > 600:
            self.series_t = self.series_t[-600:]
        self.throughput_window.append(self.passed - self._passed_last_second)
        self._passed_last_second = self.passed
        self.congestion = min(1.0, b.real_total() / max(1, C.NO_OF_VEH))

    # dashboard-facing numbers ----------------------------------------------
    def avg_wait(self):
        return self.wait_seconds / max(1, C.NO_OF_VEH)

    def throughput_per_min(self):
        if not self.throughput_window:
            return 0.0
        return sum(self.throughput_window) / len(self.throughput_window) * 60.0

    def congestion_label(self):
        c = self.congestion
        if c < 0.18:
            return "LOW", C.HUD_GOOD
        if c < 0.38:
            return "MODERATE", C.HUD_WARN
        return "HEAVY", C.HUD_BAD

    def sim_clock(self):
        m, s = divmod(self.sim_seconds, 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    # end-of-run report ------------------------------------------------------
    def export_report(self, path="density_report.png"):
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
        except Exception as exc:                      # matplotlib optional
            print(f"[stats] matplotlib unavailable, skipping report: {exc}")
            return None
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))
        fig.suptitle("Smart Traffic — Signal Density Report", fontsize=13)
        for name, ys in self.series.items():
            ax1.plot(self.series_t[-len(ys):], ys, label=name, linewidth=1.6)
        ax1.set_xlabel("Simulated seconds")
        ax1.set_ylabel("Queued vehicles")
        ax1.set_title("Density over time")
        ax1.legend()
        ax1.grid(alpha=0.3)
        finals = {k: (v[-1] if v else 0) for k, v in self.series.items()}
        ax2.bar(list(finals.keys()), list(finals.values()),
                color="#4c8ed9", width=0.45)
        ax2.set_title("Final snapshot (original bar chart)")
        ax2.set_ylabel("Density in number")
        ax2.grid(axis="y", alpha=0.3)
        fig.tight_layout()
        fig.savefig(path, dpi=130)
        plt.close(fig)
        print(f"[stats] report written → {path}")
        return path
