"""Shared geometry of ECLISSE. One unit = one pixel of the 480 x 480 display."""
import math

S = 480            # canvas
C = 240            # centre
R = 132            # lunar disc radius
ORBIT = 190        # radius on which the five satellite moons sit
RM = 43            # satellite moon radius: an 86 px button
ICON = 24          # data icon size
STAR_PAD = 20      # star layers overflow the screen so parallax never shows an edge

# Bitmap hands: (x, y, width, height) of the cropped image; all pivot on the centre.
HANDS = {
    'hand_hour': (170, 40, 140, 200),
    'hand_minute': (190, 0, 100, 240),
    'hand_second': (130, 70, 220, 170),
}

# Satellite moons, as clock angles (0 = 12 o'clock, clockwise).
MOON_SLOT_LEFT, MOON_SLOT_RIGHT = 300, 60
MOON_STEPS, MOON_HEART, MOON_BATTERY = 228, 180, 132


def polar(angle, radius):
    a = math.radians(angle)
    return C + radius * math.sin(a), C - radius * math.cos(a)
