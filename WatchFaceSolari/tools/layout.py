"""Shared geometry of SOLARI. One unit = one pixel of the 480 x 480 display."""

S = 480
C = 240

# Outer seconds crown: 60 bezel ticks inside the progress arc + synced cursor dot.
TICK_R_OUT = 229
TICK_R_MAJ = 220
TICK_R_MIN = 225
NUM_R = 211
ARC_R = 235
ARC_W = 2.4
DOT_R = 4.4
DOT_ORBIT = 235

# Top date pill (uniform 8 px grid gap to flip stack; 0..56 clear for system indicator).
DATE_X, DATE_Y, DATE_W, DATE_H, DATE_R = 128, 56, 224, 34, 14

# Left column: two stacked vintage split-flap cards (74..228).
FLIP_X, FLIP_W, FLIP_H, FLIP_R = 74, 154, 109, 18
HOUR_Y, MIN_Y = 98, 215
PIN = 4                 # hinge pins protrude this much on each side of the card
FLIP_FRAMES = 8         # mechanical falling leaf animation frames

# Right column: three label-free metric tiles (236..406), total span 74..406 centred on 240.
TILE_X, TILE_W, TILE_H, TILE_R = 236, 170, 70, 20
HEART_Y, BATT_Y, STEPS_Y = 98, 176, 254
BAR_X, BAR_W, BAR_H = 24, 130, 5
ICON = 24

# Bottom row (104..376, centred on 240): notifications pill + weather pill + recorder button.
BOT_Y, BOT_H, BOT_R = 332, 54, 19
SLOT_X, SLOT_W = 104, 90
WX_X, WX_W = 202, 112
MIC_X, MIC_SIZE, MIC_ICON = 322, 54, 28
