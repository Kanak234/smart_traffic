"""
core/network.py — Road-network geometry and signal placement.

Every table in this file (signal coordinates, `sig_pos`, node positions,
`roots`, `road_lanes_dimensions`) is copied **verbatim** from the original
main.py. The rendering layer derives prettier geometry (kerbs, zebra
crossings, medians) from these numbers, but the numbers themselves are the
single source of truth for the simulation and must stay untouched.
"""

from config import (TOT_NODES, TIME_REM, RED, GREEN, HORR, VERT)


class Road:
    """One directed-pair road segment (original class `root`).

    symm      : HORR (east-west) or VERT (north-south)
    w_*       : cross-axis coordinates (start / centre / end)
    l_*       : along-axis start / end coordinates
    r_next    : ((N,S,E,W) next-road ids for fwd dir, same for reverse)
    next_nodes: node ids this road feeds into
    lane      : 2 or 4 physical lanes
    """

    __slots__ = ("symm", "w_start", "w_middle", "w_end",
                 "l_start", "l_end", "r_next", "next_nodes", "lane")

    def __init__(self, symm, w_start, w_middle, w_end,
                 l_start, l_end, r_next, node_list, lane=2):
        self.symm = symm
        self.w_start = w_start
        self.w_middle = w_middle
        self.w_end = w_end
        self.l_start = l_start
        self.l_end = l_end
        self.r_next = r_next
        self.next_nodes = node_list
        self.lane = lane


# --------------------------------------------------------------------------
# Signals ————  signals[node_id][sig_id] == [time_remaining, state, (x, y)]
# --------------------------------------------------------------------------
def build_signals():
    """Recreate the original `signals` structure with initial states."""
    signals = [[[5, GREEN, (940, 165)],
                [2, RED, (1100, 165)],
                [3, RED, (1100, 315)],
                [7, RED, (940, 315)]]]
    for _ in range(TOT_NODES - 1):
        signals.append([[6, RED, (0, 0)], [4, GREEN, (0, 0)], [1, GREEN, (0, 0)]])

    signals[1][0][2] = (10, 165);   signals[1][1][2] = (115, 165);  signals[1][2][2] = (115, 315)
    signals[2][0][2] = (222, 165);  signals[2][1][2] = (335, 315);  signals[2][2][2] = (222, 315)
    signals[3][0][2] = (418, 165);  signals[3][1][2] = (528, 165);  signals[3][2][2] = (528, 315)
    signals[4][0][2] = (650, 165);  signals[4][1][2] = (765, 315);  signals[4][2][2] = (650, 315)
    signals[5][0][2] = (70, 455);   signals[5][1][2] = (175, 565);  signals[5][2][2] = (70, 565)
    signals[6][0][2] = (222, 455);  signals[6][1][2] = (335, 455);  signals[6][2][2] = (335, 565)
    signals[7][0][2] = (650, 455);  signals[7][1][2] = (765, 455);  signals[7][2][2] = (650, 565)
    signals[8][0][2] = (1100, 583); signals[8][1][2] = (1100, 695); signals[8][2][2] = (940, 695)
    return signals


# stop-line coordinate of every signal of every node (original `sig_pos`)
SIG_POS = ((980, 205, 1100, 315), (50, 205, 115), (262, 315, 335),
           (458, 205, 528), (690, 765, 315), (110, 175, 565),
           (262, 335, 495), (690, 565, 495), (1100, 623, 695))

# intersection centre points (original node.pos table)
NODE_POS = [[1042, 260], [82, 260], [300, 260], [495, 260],
            [730, 260], [143, 528], [300, 528], [730, 528], [1042, 660]]


def node_pos(node_id):
    return NODE_POS[node_id]


def signal_id(node_id, signal_pos):
    """Original node.signal_id — map a stop-line coordinate to a sig index."""
    for sig_id in range(len(SIG_POS[node_id])):
        if SIG_POS[node_id][sig_id] == signal_pos:
            return sig_id
    raise AssertionError(f"signal position {signal_pos} not on node {node_id}")


def signals_per_node(node_id):
    return 4 if node_id == 0 else 3


# --------------------------------------------------------------------------
# Roads — verbatim `roots` tuple
# --------------------------------------------------------------------------
ROADS = (
    Road(HORR, 205, 260, 315, 0, 50,     ((9, -1, 1, -1), (-1, -1, -1, -1)), [1], 4),
    Road(HORR, 205, 260, 315, 115, 262,  ((-1, 11, 2, -1), (9, -1, -1, 0)), (1, 2), 4),
    Road(HORR, 205, 260, 315, 335, 458,  ((10, -1, 3, -1), (-1, 11, -1, 1)), (2, 3), 4),
    Road(HORR, 205, 260, 315, 528, 690,  ((-1, 12, 4, -1), (10, -1, -1, 2)), (3, 4), 4),
    Road(HORR, 205, 260, 315, 765, 980,  ((6, 7, 5, -1), (-1, 12, -1, 3)), (4, 0), 4),
    Road(HORR, 205, 260, 315, 1100, 1370, ((-1, -1, -1, -1), (6, 7, -1, 4)), [0], 4),
    Road(VERT, 980, 1042, 1100, 0, 205,  ((-1, -1, -1, -1), (-1, 7, 5, 4)), [0], 4),
    Road(VERT, 980, 1042, 1100, 315, 623, ((6, -1, 5, 4), (-1, 8, 18, -1)), (0, 8), 4),
    Road(VERT, 980, 1042, 1100, 695, 770, ((7, -1, 18, -1), (-1, -1, -1, -1)), [8], 4),
    Road(VERT, 50, 82, 115, 0, 205,      ((-1, -1, -1, -1), (-1, -1, 1, 0)), [1]),
    Road(VERT, 458, 495, 528, 0, 205,    ((-1, -1, -1, -1), (-1, -1, 3, 2)), [3]),
    Road(VERT, 262, 300, 335, 315, 495,  ((-1, -1, 2, 1), (-1, -1, 16, 15)), (2, 6)),
    Road(VERT, 690, 730, 765, 315, 495,  ((-1, -1, 4, 3), (-1, 13, -1, 16)), (4, 7)),
    Road(VERT, 690, 730, 765, 565, 770,  ((12, -1, -1, 16), (-1, -1, -1, -1)), [7]),
    Road(HORR, 495, 528, 565, 0, 110,    ((-1, 17, 15, -1), (-1, -1, -1, -1)), [5]),
    Road(HORR, 495, 528, 565, 175, 262,  ((11, -1, 16, -1), (-1, 17, -1, 14)), (5, 6)),
    Road(HORR, 495, 528, 565, 335, 690,  ((12, 13, -1, -1), (11, -1, -1, 15)), (6, 7)),
    Road(VERT, 110, 143, 175, 565, 770,  ((-1, -1, 15, 14), (-1, -1, -1, -1)), [5]),
    Road(HORR, 623, 660, 695, 1100, 1370, ((-1, -1, -1, -1), (7, 8, -1, -1)), [8]),
)

# --------------------------------------------------------------------------
# Lane geometry — verbatim `road_lanes_dimensions`
# --------------------------------------------------------------------------
ROAD_LANES = (
    ((0, 50),     (205, 233), (233, 260), (260, 285), (285, 315)),
    ((115, 262),  (205, 233), (233, 260), (260, 285), (285, 315)),
    ((335, 458),  (205, 233), (233, 260), (260, 285), (285, 315)),
    ((528, 690),  (205, 233), (233, 260), (260, 285), (285, 315)),
    ((765, 980),  (205, 233), (233, 260), (260, 285), (285, 315)),
    ((1100, 1370), (205, 233), (233, 260), (260, 285), (285, 315)),
    ((0, 205),    (980, 1012), (1012, 1042), (1042, 1072), (1072, 1100)),
    ((315, 623),  (980, 1012), (1012, 1042), (1042, 1072), (1072, 1100)),
    ((695, 770),  (980, 1012), (1012, 1042), (1042, 1072), (1072, 1100)),
    ((0, 205),    (50, 82),   (82, 115)),
    ((0, 205),    (458, 495), (495, 528)),
    ((315, 495),  (262, 300), (300, 335)),
    ((315, 495),  (690, 730), (730, 765)),
    ((565, 770),  (690, 730), (730, 765)),
    ((0, 110),    (495, 528), (528, 565)),
    ((175, 262),  (495, 528), (528, 565)),
    ((335, 690),  (495, 528), (528, 565)),
    ((565, 770),  (110, 143), (143, 175)),
    ((1100, 1370), (623, 660), (660, 695)),
)

# --------------------------------------------------------------------------
# Respawn tables + open-ended roads (verbatim from motion())
# --------------------------------------------------------------------------
RESPAWN_X = [125, 705, 995, 1370, 1370, 0, 0, 100, 513, 1085]
RESPAWN_Y = [770, 770, 770, 300, 680, 220, 510, 0, 0, 0]
RESPAWN_ROAD = [17, 13, 8, 5, 18, 0, 14, 9, 10, 6]
RESPAWN_DIR = ["North", "North", "North", "West", "West",
               "East", "East", "South", "South", "South"]
OUT_ROADS = (0, 9, 14, 17, 13, 8, 18, 5, 6, 10)

# --------------------------------------------------------------------------
# Derived render geometry (presentation only — safe to change)
# --------------------------------------------------------------------------
def road_rect(road_id):
    """Axis-aligned bounding rect (x, y, w, h) of a road's tarmac."""
    r = ROADS[road_id]
    if r.symm == HORR:
        return (r.l_start, r.w_start, r.l_end - r.l_start, r.w_end - r.w_start)
    return (r.w_start, r.l_start, r.w_end - r.w_start, r.l_end - r.l_start)


def intersection_rects():
    """Tarmac rect for every intersection node, derived from adjoining roads."""
    rects = []
    for n in range(TOT_NODES):
        cx, cy = NODE_POS[n]
        # find widest horizontal + vertical road meeting this node
        half_h = half_v = 0
        for rid, road in enumerate(ROADS):
            if n not in road.next_nodes:
                continue
            if road.symm == HORR:
                half_h = max(half_h, (road.w_end - road.w_start) // 2)
            else:
                half_v = max(half_v, (road.w_end - road.w_start) // 2)
        if half_h == 0:
            half_h = 55
        if half_v == 0:
            half_v = 32
        rects.append((cx - half_v, cy - half_h, half_v * 2, half_h * 2))
    return rects


def approach_geometry():
    """For every (node, sig) return dict with stop-line + zebra placement.

    A signal at coordinate `stop` guards traffic arriving along one axis;
    the zebra crossing is painted across the approach road just before the
    intersection box, and the light head is planted on the near-side kerb.
    """
    out = {}
    for n in range(TOT_NODES):
        cx, cy = NODE_POS[n]
        for s in range(signals_per_node(n)):
            stop = SIG_POS[n][s]
            lx, ly = build_signals()[n][s][2]  # lamp anchor (original blit pos)
            # find the road this stop-line lives on
            axis = None
            for rid, road in enumerate(ROADS):
                if n not in road.next_nodes:
                    continue
                if road.symm == HORR and stop in (road.l_start, road.l_end):
                    axis = ("h", rid, road)
                    break
                if road.symm == VERT and stop in (road.l_start, road.l_end):
                    axis = ("v", rid, road)
                    break
            out[(n, s)] = {"stop": stop, "lamp": (lx, ly), "axis": axis,
                           "node_xy": (cx, cy)}
    return out
