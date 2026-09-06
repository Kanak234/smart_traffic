"""
config.py — Central configuration for the Smart Traffic Simulator.

Every tunable constant of the simulation lives here. The values in the
"LEGACY CORE" section are copied verbatim from the original main.py and
MUST NOT be changed if you want behaviour identical to the original
academic project. Everything else is presentation / feature layer.
"""

# --------------------------------------------------------------------------
# LEGACY CORE — original algorithm constants (do not touch for parity)
# --------------------------------------------------------------------------
TOT_NODES = 9            # number of intersections
NODE_SIGNALS = 3         # signals per ordinary node (node 0 has 4)
TIME_REM = 5             # seconds a green phase lasts by default
RED, GREEN = 0, 1        # signal states (AMBER is a render-only overlay)
NO_OF_VEH = 170          # number of vehicles in the closed system
SIGNAL_RANGE_PX = 30     # distance at which a vehicle "sees" its signal
DENSITY_REF = 10         # 'ref' in the original density pre-condition
DENSITY_RADIUS = 50      # mod - ref < 50  →  within 60 px counts as queued
DENSITY_HIGH = 10        # manager trips to congested at >= this
DENSITY_LOW = 8          # manager relaxes at <= this
VEH_STEP_PX = 5          # pixels a vehicle advances per logic tick
LOGIC_TICK = 0.1         # seconds per logic tick (original time.sleep(0.1))
ACTIVE_MANAGERS = 20     # original loop ran managers [0, 20) of the 28
                         # defined. Set to 28 to enable every manager.
DUMMY_NODE = 9           # den_sig bucket used when a vehicle has no signal

HORR, VERT = 10, 20      # road orientation flags (original horr/vert)

# --------------------------------------------------------------------------
# Window / timing
# --------------------------------------------------------------------------
SCREEN_W, SCREEN_H = 1366, 768   # geometry tables are locked to this size
TARGET_FPS = 60
WINDOW_TITLE = "Smart City Traffic Signal Synchronization"

# --------------------------------------------------------------------------
# Feature toggles (runtime-switchable, these are the boot defaults)
# --------------------------------------------------------------------------
FEATURES = {
    "dashboard":        True,    # Tab
    "labels":           True,    # T  — timers + density text at signals
    "day_night_cycle":  True,    # C  — automatic day/night cycle
    "night":            False,   # N  — force night instantly
    "rain":             False,   # R
    "fog":              False,   # F
    "pedestrians":      True,    # P
    "emergency":        True,    # E  — emergency vehicle signal preemption
    "shadows":          True,
    "glow":             True,
    "vsync_interp":     True,    # smooth interpolation between logic ticks
}

DAY_LENGTH_S = 150.0             # one full day/night cycle in sim seconds
EMERGENCY_RANGE_PX = 120         # preemption trigger distance
EMERGENCY_HOLD_TICKS = 30        # ticks a preempted node stays locked
PEDESTRIAN_MAX = 26

# --------------------------------------------------------------------------
# Vehicle fleet composition (visual layer only — core motion identical)
# --------------------------------------------------------------------------
FLEET_SPECIAL = {                # probability a car-sized vehicle becomes:
    "taxi": 0.08,
    "police": 0.03,
    "ambulance": 0.03,
}

# body paint palette (name → RGB) used for ordinary cars
CAR_PAINTS = {
    "forestgreen": (34, 139, 34),
    "blue":        (36, 84, 196),
    "red":         (196, 40, 40),
    "black":       (28, 30, 34),
    "brown":       (118, 78, 46),
    "purple":      (108, 60, 160),
    "navyblue":    (24, 34, 96),
    "magenta":     (178, 48, 130),
    "darkgreen":   (18, 88, 44),
    "tomato2":     (222, 92, 62),
    "silver":      (176, 180, 188),
    "white":       (232, 234, 238),
}

# --------------------------------------------------------------------------
# Palette — environment
# --------------------------------------------------------------------------
COL_ASPHALT      = (52, 54, 58)
COL_ASPHALT_VAR  = 6                  # per-pixel noise amplitude
COL_LANE_WHITE   = (222, 224, 226)
COL_LANE_YELLOW  = (238, 186, 44)
COL_SIDEWALK     = (148, 148, 146)
COL_SIDEWALK_EDGE= (120, 120, 118)
COL_KERB         = (172, 172, 170)
COL_GRASS        = (150, 176, 106)
COL_GRASS_DARK   = (128, 156, 88)
COL_ZEBRA        = (226, 228, 230)
COL_MEDIAN       = (94, 96, 100)
COL_BUILDING_BODY= [(196, 178, 160), (176, 168, 188), (160, 176, 168),
                    (188, 160, 150), (168, 170, 176), (198, 188, 168)]
COL_BUILDING_ROOF= [(120, 104, 96), (104, 100, 116), (96, 108, 100),
                    (114, 96, 90), (100, 102, 108), (122, 114, 100)]
COL_TREE_FOLIAGE = [(66, 120, 58), (58, 108, 52), (78, 132, 64)]
COL_TREE_TRUNK   = (94, 68, 46)

# --------------------------------------------------------------------------
# Dashboard / HUD
# --------------------------------------------------------------------------
HUD_GLASS       = (16, 20, 30, 168)     # RGBA glass panels
HUD_GLASS_SOFT  = (16, 20, 30, 120)
HUD_BORDER      = (255, 255, 255, 34)
HUD_TEXT        = (232, 238, 246)
HUD_SUBTEXT     = (150, 160, 176)
HUD_ACCENT      = (94, 200, 255)
HUD_GOOD        = (86, 214, 130)
HUD_WARN        = (250, 200, 80)
HUD_BAD         = (244, 96, 96)
PANEL_W         = 252

# signal lamp colours
LAMP_RED    = (236, 58, 48)
LAMP_AMBER  = (250, 176, 32)
LAMP_GREEN  = (52, 214, 96)
LAMP_OFF    = (52, 46, 44)
AMBER_WINDOW = 2          # render amber during the last N seconds of green
AMBER_AFTER_FORCE = 1.0   # seconds of amber shown after a forced switch

RNG_SEED_DECOR = 20260702  # deterministic environment decoration
