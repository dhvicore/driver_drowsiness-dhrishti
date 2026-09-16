# ============================================================
# DRIVER MONITORING CONFIGURATION
# ============================================================

# ---------------- EYES ----------------

EYE_CLOSE_THRESHOLD = 0.20
EYE_OPEN_THRESHOLD = 0.24

EYE_CONFIRM_FRAMES = 4
EAR_SMOOTHING_FRAMES = 7

# Eye closed durations
DROWSY_EYE_SECONDS = 1.5
CRITICAL_EYE_SECONDS = 3.0


# ---------------- YAWN ----------------

MAR_YAWN_START = 0.38
MAR_YAWN_STOP = 0.20

MAR_SMOOTHING_FRAMES = 7

YAWN_CONFIRM_SECONDS = 0.7
YAWN_STOP_SECONDS = 0.4


# ---------------- PERCLOS ----------------

# rolling ~30-second window
PERCLOS_WINDOW_SECONDS = 30

# fraction of time eyes closed
PERCLOS_WARNING = 0.30
PERCLOS_DROWSY = 0.45


# ---------------- HEAD / DISTRACTION ----------------

# Head direction must persist before distraction
DISTRACTION_CONFIRM_SECONDS = 1.5

# Approximate pose thresholds.
# We can calibrate these after testing.
YAW_THRESHOLD = 22
PITCH_DOWN_THRESHOLD = 18
PITCH_UP_THRESHOLD = -18


# ---------------- PHONE ----------------

PHONE_CONFIDENCE = 0.35
PHONE_CONFIRM_SECONDS = 1.0


# ---------------- FINAL ENGINE ----------------

FATIGUED_SCORE = 25
DROWSY_SCORE = 50
CRITICAL_SCORE = 75