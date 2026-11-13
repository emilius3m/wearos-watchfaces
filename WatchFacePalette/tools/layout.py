"""Shared geometry of PALETTE. One unit = one pixel of the 480 x 480 display."""

S = 480
C = 240

# Big flaps: hours and minutes.
BIG_W, BIG_H, BIG_R = 150, 164, 16
BIG_Y = 104
HOUR_X, MINUTE_X = 48, 206
PIN = 5                       # the hinge pins overflow the flap by this much on each side

# Right column: recorder button above, seconds flap below.
SEC_X, SEC_Y, SEC_W, SEC_H = 364, 196, 72, 72
MIC_X, MIC_Y, MIC_R = 400, 146, 34

# Date flaps: weekday, day, month.
DATE_Y, DATE_H = 46, 42
DATE = [(140, 66), (212, 50), (268, 66)]          # (x, width)

# Data flaps: steps, heart rate, battery. The icon sits under each flap.
DATA_Y, DATA_W, DATA_H = 284, 112, 76
DATA_X = [64, 184, 304]
BAR_Y, BAR_W, BAR_H = 365, 88, 4
ICON = 24
ICON_Y = 374
DATA_TAP_H = 116                                   # tap area: flap + bar + icon

# Complication flaps.
SLOT_Y, SLOT_W, SLOT_H = 404, 96, 38
SLOT_X = [140, 244]

FLIP_BIG_FRAMES, FLIP_SMALL_FRAMES = 6, 4
