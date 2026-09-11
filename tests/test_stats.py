"""Tests for simulation metrics collection and reporting."""

import os

import config as C
from core.density import DensityBoard
from stats import Stats


def test_stats_reports_density_clock_and_congestion(tmp_path):
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

    # Moderate and heavy congestion labels
    stats.congestion = 0.25
    assert stats.congestion_label()[0] == "MODERATE"
    stats.congestion = 0.50
    assert stats.congestion_label()[0] == "HEAVY"

    # Export report to temporary path
    report_path = str(tmp_path / "test_report.png")
    out = stats.export_report(report_path)
    assert out == report_path
    assert os.path.isfile(report_path)
    assert os.path.getsize(report_path) > 1000


def test_stats_series_capping():
    board = DensityBoard()
    stats = Stats(board)
    stats.series_t = list(range(700))
    stats.series["Signal_1"] = list(range(700))
    stats.series["Signal_2"] = list(range(700))
    stats.series["Signal_3"] = list(range(700))

    stats.second_sample()

    assert len(stats.series_t) == 600
    assert len(stats.series["Signal_1"]) == 600


def test_stats_empty_throughput():
    board = DensityBoard()
    stats = Stats(board)
    assert stats.throughput_per_min() == 0.0
