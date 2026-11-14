"""Shared geometry of NIXIE. One unit = one pixel of the 480 x 480 display."""

S = 480
C = 240

# Slimmed brushed bezel (14 px) & recessed rehaut second track (7 px) -> 438 px usable dial
OUTER_CASE_R = 238.0
BEZEL_IN = 226.0
REHAUT_IN = 219.0
REHAUT_MID = 222.5
SCREW_R = 232.0
SEC_BEAD_R = 6.5

# Top date caption (clear of top system status dot & slimmed rehaut)
DATE_Y = 58

# Four taller IN-14/IN-18 cylindrical Nixie tubes (73 x 136 each)
TUBE_Y0, TUBE_Y1 = 88, 224
TUBE_W, TUBE_H = 73, 136
TUBE_XS = (74, 150, 257, 333)

# Nixie digit bitmap glyph box inside each tube (including plasma bleed padding)
GLYPH_W, GLYPH_H = 73, 114
GLYPH_Y = 92

# Central NE-2 glass colon bulbs
COLON_CY = 152
COLON_SPREAD = 15

# Ignition flicker frames on digit switch / screen wake
FLASH_FRAMES = 6

# Tier 1: Wide upper riveted instrument window (Heart, Steps, Battery + progress bar)
INST_X0, INST_Y0, INST_X1, INST_Y1 = 62, 232, 418, 288
INST_W, INST_H = INST_X1 - INST_X0, INST_Y1 - INST_Y0
INST_BAR_X, INST_BAR_Y, INST_BAR_W, INST_BAR_H = 24, 42, 308, 4.5
ICON_SM = 16

# Tier 2: Full-width recessed Weather & 2-Day Forecast console
WX_X0, WX_Y0, WX_X1, WX_Y1 = 68, 294, 412, 348
WX_W, WX_H = WX_X1 - WX_X0, WX_Y1 - WX_Y0

# Tier 3: Curved bottom tactile hardware row (Left Complication + Center Round Push-Button + Right Complication)
BOT_Y0, BOT_H = 356, 60
BOT_CAP_R = 29
SLOT_L_X, SLOT_W = 99, 94
SLOT_R_X = 287
MIC_D = 80
MIC_X, MIC_Y = C - MIC_D // 2, 356

