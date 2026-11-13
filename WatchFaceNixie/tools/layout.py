"""Shared geometry of NIXIE. One unit = one pixel of the 480 x 480 display."""

S = 480
C = 240

# Outer brushed bezel & recessed rehaut second track
BEZEL_IN = 212
REHAUT_IN = 203
REHAUT_MID = 207.5
SEC_BEAD_R = 7

# Top date caption (clear of top system status dot)
DATE_Y = 74

# Four IN-14/IN-18 cylindrical Nixie tubes (71 x 128 each)
TUBE_Y0, TUBE_Y1 = 108, 236
TUBE_W, TUBE_H = 71, 128
TUBE_XS = (74, 149, 260, 335)

# Nixie digit bitmap glyph box inside each tube (including plasma bleed padding)
GLYPH_W, GLYPH_H = 71, 108
GLYPH_Y = 112

# Central NE-2 glass colon bulbs
COLON_CY = 171
COLON_SPREAD = 15

# Ignition flicker frames on digit switch / screen wake
FLASH_FRAMES = 6

# Upper recessed brass instrument window (Heart, Steps, Battery + progress bar)
INST_X0, INST_Y0, INST_X1, INST_Y1 = 92, 252, 388, 312
INST_W, INST_H = INST_X1 - INST_X0, INST_Y1 - INST_Y0
INST_BAR_X, INST_BAR_Y, INST_BAR_W, INST_BAR_H = 26, 42, 244, 4.5
ICON_SM = 16

# Bottom row: Notifications + Weather + Voice Recorder button
BOT_Y0, BOT_Y1 = 324, 376
BOT_H = BOT_Y1 - BOT_Y0
SLOT_X, SLOT_W = 108, 86
WX_X, WX_W = 202, 100
MIC_X, MIC_W = 310, 62

# Plain seconds label at bottom
SEC_LABEL_Y = 404
