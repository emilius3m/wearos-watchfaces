"""Four alternative watch face concepts, rendered as mockups to choose from.

These are design studies only: nothing here is installed on the watch. Every concept
shows the same sample values so they can be compared fairly, and uses only effects
that Watch Face Format 2 can reproduce (vector shapes, tinted bitmaps, rotations).
"""
from pathlib import Path
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

import make_assets as MA

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'design/mockups'
VAR = ROOT / 'design/teko_variable.ttf'
K = 2
S = 480
N = S * K
C = 240
V = dict(hh='09', mm='27', sec=36, steps='6480', sp=0.648, hr='72', batt='84', bp=0.84,
         dow='GIO', dowf='GIOVEDÌ', date='12 NOV', bell='0', sun='16:44')
HOUR = 9 + 27 / 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)


def mix(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


_fonts = {}


def font(size, weight):
    key = (round(size * K), weight)
    if key not in _fonts:
        f = ImageFont.truetype(str(VAR), key[0])
        f.set_variation_by_axes([weight])
        _fonts[key] = f
    return _fonts[key]


def polar(angle, radius, cx=C, cy=C):
    a = math.radians(angle)
    return cx + radius * math.sin(a), cy - radius * math.cos(a)


class Canvas:
    def __init__(self, img=None):
        self.img = img or Image.new('RGBA', (N, N), BLACK + (255,))

    def paint(self, fn, blur=0, repeat=1):
        """Draw on a transparent layer, optionally blurred (for glows), then composite."""
        layer = Image.new('RGBA', (N, N), (0, 0, 0, 0))
        fn(Draw(ImageDraw.Draw(layer)))
        if blur:
            layer = layer.filter(ImageFilter.GaussianBlur(blur * K))
        for _ in range(repeat):
            self.img.alpha_composite(layer)

    def glow(self, fn, blur=8, repeat=1):
        self.paint(fn, blur, repeat)
        self.paint(fn)

    def icon(self, name, cx, cy, size, color):
        k = max(1, round(size * K / 24 * 4))
        im = Image.new('L', (24 * k, 24 * k), 0)
        GLYPHS[name](ImageDraw.Draw(im), k)
        im = im.resize((round(size * K), round(size * K)), Image.LANCZOS)
        out = Image.new('RGBA', im.size, tuple(color[:3]) + (255,))
        out.putalpha(im)
        self.img.alpha_composite(out, (round(cx * K - out.width / 2), round(cy * K - out.height / 2)))

    def finish(self):
        mask = Image.new('L', (N, N), 0)
        ImageDraw.Draw(mask).ellipse([0, 0, N - 1, N - 1], fill=255)
        out = Image.new('RGBA', (N, N), (0, 0, 0, 0))
        out.paste(self.img, (0, 0), mask)
        return out.resize((S, S), Image.LANCZOS)


class Draw:
    """Thin wrapper in logical pixels (480 x 480)."""

    def __init__(self, d):
        self.d = d

    def rect(self, x0, y0, x1, y1, r=0, fill=None, outline=None, width=1.0, corners=None):
        self.d.rounded_rectangle([x0 * K, y0 * K, x1 * K, y1 * K], radius=r * K, fill=fill, outline=outline,
                                 width=max(1, round(width * K)), corners=corners)

    def circle(self, cx, cy, r, fill=None, outline=None, width=1.0):
        self.d.ellipse([(cx - r) * K, (cy - r) * K, (cx + r) * K, (cy + r) * K], fill=fill, outline=outline,
                       width=max(1, round(width * K)))

    def line(self, pts, fill, width=1.0, cap=True):
        pts = [(x * K, y * K) for x, y in pts]
        self.d.line(pts, fill=fill, width=max(1, round(width * K)), joint='curve')
        if cap:
            r = width * K / 2
            for x, y in (pts[0], pts[-1]):
                self.d.ellipse([x - r, y - r, x + r, y + r], fill=fill)

    def poly(self, pts, fill=None, outline=None):
        self.d.polygon([(x * K, y * K) for x, y in pts], fill=fill, outline=outline)

    def arc(self, cx, cy, r, start, end, fill, width, cap=True):
        """Clock angles: 0 = 12 o'clock, clockwise."""
        if end <= start:
            return
        o = r + width / 2
        self.d.arc([(cx - o) * K, (cy - o) * K, (cx + o) * K, (cy + o) * K], start - 90, end - 90, fill=fill,
                   width=max(1, round(width * K)))
        if cap:
            for a in (start, end):
                x, y = polar(a, r, cx, cy)
                self.circle(x, y, width / 2, fill=fill)

    def text(self, x, y, s, size, weight=600, fill=WHITE, anchor='m', spacing=0.0):
        """y is the centre of the capitals. Returns the text width."""
        f = font(size, weight)
        base = (y + 0.311 * size) * K
        gap = spacing * size * K
        total = f.getlength(s) + gap * (len(s) - 1)
        X = x * K - (total / 2 if anchor == 'm' else total if anchor == 'r' else 0)
        if not gap:
            self.d.text((X, base), s, font=f, fill=fill, anchor='ls')
        else:
            for ch in s:
                self.d.text((X, base), ch, font=f, fill=fill, anchor='ls')
                X += f.getlength(ch) + gap
        return total / K


def glyph_bell(d, k):
    d.pieslice([5 * k, 3.4 * k, 19 * k, 17.4 * k], 180, 360, fill=255)
    d.rectangle([5 * k, 10.4 * k, 19 * k, 17 * k], fill=255)
    d.rounded_rectangle([2.6 * k, 16.4 * k, 21.4 * k, 19.4 * k], radius=1.5 * k, fill=255)
    d.ellipse([9.8 * k, 20.2 * k, 14.2 * k, 23.6 * k], fill=255)
    d.ellipse([10.5 * k, 1.0 * k, 13.5 * k, 4.0 * k], fill=255)


def glyph_sun(d, k):
    d.pieslice([6 * k, 9 * k, 18 * k, 21 * k], 180, 360, fill=255)
    d.rounded_rectangle([1.5 * k, 17 * k, 22.5 * k, 19.6 * k], radius=1.3 * k, fill=255)
    for a in (-66, -33, 0, 33, 66):
        s, c = math.sin(math.radians(a)), -math.cos(math.radians(a))
        d.line([((12 + s * 8.6) * k, (15 + c * 8.6) * k), ((12 + s * 12) * k, (15 + c * 12) * k)], fill=255,
               width=round(2 * k))


GLYPHS = {'heart': MA.glyph_heart, 'steps': MA.glyph_steps, 'battery': MA.glyph_battery,
          'bell': glyph_bell, 'sun': glyph_sun}


# ---------------------------------------------------------------------------
# A · ORIZZONTE: a sky that follows the day, a dashboard under the horizon.
# ---------------------------------------------------------------------------
def orizzonte():
    HZ = 290
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32) / K
    stops = [(0, (2, 4, 14)), (140, (7, 18, 50)), (HZ - 50, (20, 42, 92)), (HZ, (78, 78, 120))]
    arr = np.dstack([np.interp(yy, [s[0] for s in stops], [s[1][i] for s in stops]) for i in range(3)])
    sx, sy = polar((HOUR - 12) / 24 * 360, 214)            # the Sun is a 24-hour hand: noon at the top
    arr += np.array([255, 160, 70]) * (0.75 * np.exp(-((xx - sx) ** 2 + (yy - sy) ** 2) / (2 * 60 ** 2)))[..., None]
    arr += np.array([255, 176, 110]) * (0.5 * np.exp(-((yy - HZ) / 16) ** 2) * np.exp(-((xx - C) / 190) ** 2))[..., None]
    arr[yy > HZ] *= 0.0
    c = Canvas(Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), 'RGB').convert('RGBA'))
    rng = np.random.default_rng(7)

    def stars(d):
        for _ in range(70):
            x, y = rng.uniform(20, 460), rng.uniform(10, 200)
            d.circle(x, y, rng.uniform(0.5, 1.1), fill=WHITE + (int(rng.uniform(50, 150)),))
        for h in range(24):                                  # hour marks of the solar orbit
            x, y = polar(h * 15, 214)
            if y < HZ - 6:
                d.circle(x, y, 1.6 if h % 6 else 2.6, fill=WHITE + (90 if h % 6 else 170,))
    c.paint(stars)
    c.glow(lambda d: d.circle(sx, sy, 12, fill=(255, 214, 140)), blur=12, repeat=2)
    c.paint(lambda d: d.circle(sx, sy, 7, fill=(255, 248, 228)))
    c.glow(lambda d: d.line([(22, HZ), (458, HZ)], (255, 214, 160), 1.8), blur=5)

    def face(d):
        d.text(C, 112, f"{V['dow']} {V['date']}", 32, 600, (255, 208, 146), spacing=0.05)
        d.text(C - 15, 204, V['hh'], 156, 500, WHITE, 'r')
        d.text(C + 15, 204, V['mm'], 156, 500, WHITE, 'l')
        for dy in (-19, 19):
            d.circle(C, 204 + dy, 5.6, fill=(255, 208, 146))
        for i, (ic, val, lab, prog) in enumerate([('steps', V['steps'], None, V['sp']), ('heart', V['hr'], 'BPM', None),
                                                  ('battery', V['batt'] + '%', None, V['bp'])]):
            x0 = 72 + i * 114
            d.rect(x0, 306, x0 + 108, 400, 18, fill=(13, 17, 26), outline=(74, 86, 110), width=1.5)
            d.text(x0 + 54, 352, val, 42, 600, WHITE)
            if prog is not None:
                d.rect(x0 + 18, 381, x0 + 90, 387, 3, fill=(46, 54, 72))
                d.rect(x0 + 18, 381, x0 + 18 + 72 * prog, 387, 3, fill=(255, 196, 120))
            else:
                d.text(x0 + 54, 384, lab, 17, 600, (150, 160, 182), spacing=0.12)
        d.rect(170, 410, 310, 448, 19, fill=(13, 17, 26), outline=(74, 86, 110), width=1.5)
        d.text(254, 429, V['sun'], 28, 600, WHITE)
    c.paint(face)
    for i, ic in enumerate(('steps', 'heart', 'battery')):
        c.icon(ic, 72 + i * 114 + 54, 324, 24, (255, 196, 120))
    c.icon('sun', 200, 428, 24, (255, 196, 120))
    return c.finish()


# ---------------------------------------------------------------------------
# B · MOSAICO: colour blocks. Every piece of data is a big coloured key.
# ---------------------------------------------------------------------------
def mosaico():
    c = Canvas()
    cream, ink = (244, 238, 224), (14, 15, 18)
    tiles = [('steps', V['steps'], 'PASSI', (46, 222, 158), V['sp']), ('heart', V['hr'], 'BPM', (255, 96, 104), None),
             ('battery', V['batt'] + '%', 'BATT', (255, 198, 54), V['bp'])]

    def face(d):
        d.arc(C, C, 233, 0, 359.9, (38, 42, 52), 5, cap=False)
        d.arc(C, C, 233, 0, V['sec'] * 6, cream, 5)
        d.text(C, 80, f"{V['dowf']} {V['date']}", 30, 600, cream, spacing=0.04)
        d.rect(52, 104, 428, 238, 30, fill=cream)
        d.text(C - 16, 171, V['hh'], 148, 700, ink, 'r')
        d.text(C + 16, 171, V['mm'], 148, 700, ink, 'l')
        for dy in (-19, 19):
            d.rect(C - 6, 171 + dy - 6, C + 6, 171 + dy + 6, 3, fill=(255, 96, 104))
        for i, (ic, val, lab, col, prog) in enumerate(tiles):
            x0 = 52 + i * 128
            d.rect(x0, 246, x0 + 120, 354, 24, fill=col)
            d.text(x0 + 106, 266, lab, 18, 700, mix(col, ink, 0.72), 'r', spacing=0.08)
            d.text(x0 + 60, 310, val, 50, 700, ink)
            if prog is not None:
                d.rect(x0 + 16, 337, x0 + 104, 343, 3, fill=mix(col, ink, 0.28))
                d.rect(x0 + 16, 337, x0 + 16 + 88 * prog, 343, 3, fill=ink)
        for x0, val in ((132, V['bell']), (244, V['sun'])):
            d.rect(x0, 362, x0 + 104, 420, 22, fill=(30, 34, 44), outline=(78, 86, 104), width=1.5)
            d.text(x0 + 64, 391, val, 30, 600, WHITE)
    c.paint(face)
    for i, (ic, _, _, col, _) in enumerate(tiles):
        c.icon(ic, 52 + i * 128 + 26, 267, 24, ink)
    c.icon('bell', 132 + 26, 391, 22, (120, 178, 255))
    c.icon('sun', 244 + 22, 390, 22, (255, 198, 54))
    return c.finish()


# ---------------------------------------------------------------------------
# C · CRISTALLO: a luminous segment display with labelled modules.
# ---------------------------------------------------------------------------
SEGMENTS = {'0': 'abcdef', '1': 'bc', '2': 'abged', '3': 'abgcd', '4': 'fgbc', '5': 'afgcd', '6': 'afgedc',
            '7': 'abc', '8': 'abcdefg', '9': 'abcdfg', ' ': ''}


def seven(d, x, y, w, h, t, ch, color, lit=True):
    """One slanted seven-segment digit in the box (x, y, w, h); t = stroke."""
    g = t * 0.16
    ym = y + h / 2

    def shear(pts):
        return [(px + (y + h - py) * 0.085, py) for px, py in pts]

    def horiz(yc):
        x1, x2 = x + t / 2 + g, x + w - t / 2 - g
        return shear([(x1, yc), (x1 + t / 2, yc - t / 2), (x2 - t / 2, yc - t / 2), (x2, yc), (x2 - t / 2, yc + t / 2),
                      (x1 + t / 2, yc + t / 2)])

    def vert(xc, y1, y2):
        y1, y2 = y1 + g, y2 - g
        return shear([(xc, y1), (xc + t / 2, y1 + t / 2), (xc + t / 2, y2 - t / 2), (xc, y2), (xc - t / 2, y2 - t / 2),
                      (xc - t / 2, y1 + t / 2)])
    shapes = {'a': horiz(y + t / 2), 'g': horiz(ym), 'd': horiz(y + h - t / 2),
              'f': vert(x + t / 2, y + t / 2, ym), 'b': vert(x + w - t / 2, y + t / 2, ym),
              'e': vert(x + t / 2, ym, y + h - t / 2), 'c': vert(x + w - t / 2, ym, y + h - t / 2)}
    for name in ('abcdefg' if not lit else SEGMENTS[ch]):
        d.poly(shapes[name], fill=color)


def seven_text(d, cx, y, s, w, h, t, gap, color, lit=True):
    total = len(s) * w + (len(s) - 1) * gap
    x = cx - total / 2 - h * 0.0425
    for ch in s:
        seven(d, x, y, w, h, t, ch, color, lit)
        x += w + gap


def cristallo():
    c = Canvas(Image.new('RGBA', (N, N), (3, 9, 9, 255)))
    ph, ghost, dim, track = (120, 255, 214), (9, 24, 22), (84, 170, 150), (22, 54, 49)

    def time_segments(d, color, lit):
        seven_text(d, C - 88, 124, V['hh'], 66, 120, 13, 14, color, lit)
        seven_text(d, C + 88, 124, V['mm'], 66, 120, 13, 14, color, lit)

    def colon(d):
        for dy in (-22, 22):
            d.rect(C - 6 - (dy * 0.085), 184 + dy - 6, C + 6 - (dy * 0.085), 184 + dy + 6, 3, fill=ph)

    def values(d, color, lit):
        for cx, s in ((118, V['steps']), (240, V['hr']), (362, V['batt'])):
            seven_text(d, cx, 334, s if lit else '8' * len(s), 21, 42, 5.5, 5, color, lit)

    c.paint(lambda d: [d.rect(60 + i * 122, 292, 176 + i * 122, 390, 14, fill=(4, 13, 12), outline=dim, width=1.6)
                       for i in range(3)])
    c.paint(lambda d: (time_segments(d, ghost, False), values(d, ghost, False)))
    c.glow(lambda d: (time_segments(d, ph, True), colon(d)), blur=7)
    c.glow(lambda d: values(d, ph, True), blur=4)

    def chrome(d):
        d.text(C, 88, f"{V['dowf']}  {V['date']}", 28, 600, ph, spacing=0.14)
        for i in range(60):                                   # seconds as a segmented bar
            x = 78 + i * 5.4
            d.rect(x, 264, x + 3.4, 275 if i % 5 else 279, 1, fill=ph if i < V['sec'] else track)
        for i, lab in enumerate(('PASSI', 'BPM', 'BATT %')):
            d.text(60 + i * 122 + 68, 312, lab, 19, 600, dim, spacing=0.12)
        for x0, prog in ((72, V['sp']), (316, V['bp'])):
            d.rect(x0, 381, x0 + 92, 384, 1, fill=track)
            d.rect(x0, 381, x0 + 92 * prog, 384, 1, fill=ph)
        d.text(204, 420, V['bell'], 28, 600, ph, 'l')
        d.text(266, 420, V['sun'], 28, 600, ph, 'l')
    c.paint(chrome)
    for i, ic in enumerate(('steps', 'heart', 'battery')):
        c.icon(ic, 60 + i * 122 + 22, 311, 20, ph)
    c.icon('bell', 186, 420, 22, dim)
    c.icon('sun', 248, 419, 22, dim)
    return c.finish()


# ---------------------------------------------------------------------------
# D · CRONO: an analogue instrument. Three sub-dials carry the numbers.
# ---------------------------------------------------------------------------
def crono():
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32) / K
    r = np.hypot(xx - C, yy - C)
    shade = np.clip(20 - r / 16, 4, 20)
    c = Canvas(Image.fromarray(np.dstack([shade, shade * 1.06, shade * 1.2]).astype(np.uint8), 'RGB').convert('RGBA'))
    acc, lume, steel = (255, 122, 36), (238, 244, 236), (108, 116, 132)
    subs = [(132, 240, 'steps', V['steps'], V['sp'], 34), (348, 240, 'battery', V['batt'] + '%', V['bp'], 34),
            (240, 348, 'heart', V['hr'], None, 40)]

    def dial(d):
        for i in range(60):
            a = i * 6
            if i % 5:
                d.line([polar(a, 226), polar(a, 234)], steel, 1.6, cap=False)
            elif i == 0:
                for off in (-7, 7):
                    p1, p2 = polar(a, 200), polar(a, 234)
                    d.line([(p1[0] + off, p1[1]), (p2[0] + off, p2[1])], lume, 8, cap=False)
            else:
                d.line([polar(a, 206 if i % 15 else 198), polar(a, 234)], lume, 8 if i % 15 == 0 else 6, cap=False)
        d.rect(180, 106, 300, 150, 10, fill=(6, 7, 10), outline=steel, width=1.6)
        d.text(C, 128, f"{V['dow']} {V['date'][:2]}", 32, 600, WHITE, spacing=0.06)
        for cx, cy, ic, val, prog, size in subs:
            d.circle(cx, cy, 58, fill=(5, 6, 9), outline=steel, width=1.6)
            if prog is not None:
                d.arc(cx, cy, 50, 0, 359.9, (44, 50, 64), 5, cap=False)
                d.arc(cx, cy, 50, 0, 359.9 * prog, acc, 5)
            d.text(cx, cy + 12, val, size, 600, WHITE)
    c.paint(dial)
    for cx, cy, ic, *_ in subs:
        c.icon(ic, cx, cy - 22, 22, acc)

    def hand(d, angle, length, width, tail=22):
        """Skeleton hand: an open frame, so the numbers underneath stay readable."""
        a = math.radians(angle)
        ux, uy = math.sin(a), -math.cos(a)
        px, py = -uy, ux
        w = width / 2

        def pt(along, across):
            return C + ux * along + px * across, C + uy * along + py * across
        frame = [pt(-tail, -w * 0.6), pt(length * 0.72, -w), pt(length, 0), pt(length * 0.72, w), pt(-tail, w * 0.6)]
        d.line(frame + [frame[0]], lume, 3.2)
        d.poly([pt(length * 0.72, -w), pt(length, 0), pt(length * 0.72, w), pt(length * 0.5, w * 0.92),
                pt(length * 0.5, -w * 0.92)], fill=lume)

    def hands(d):
        hand(d, (9 % 12) * 30 + 27 * 0.5, 132, 22)
        hand(d, 27 * 6 + V['sec'] * 0.1, 204, 16)
    c.paint(lambda d: hands(Shadow(d)), blur=5)
    c.paint(hands)

    def second(d):
        a = V['sec'] * 6
        d.line([polar(a + 180, 46), polar(a, 222)], acc, 2.6)
        d.circle(*polar(a + 180, 34), 6.5, fill=acc)
        d.circle(C, C, 9, fill=acc)
        d.circle(C, C, 3.4, fill=(10, 10, 12))
    c.paint(second)
    return c.finish()


class Shadow:
    """Proxy that paints everything in translucent black, for a soft drop shadow."""

    def __init__(self, d):
        self._d = d

    def line(self, pts, fill, width=1.0, cap=True):
        self._d.line([(x + 3, y + 4) for x, y in pts], (0, 0, 0, 170), width, cap)

    def poly(self, pts, fill=None, outline=None):
        self._d.poly([(x + 3, y + 4) for x, y in pts], fill=(0, 0, 0, 170))


# ---------------------------------------------------------------------------
# E · PALETTE: a vintage split-flap clock. Every value sits on its own flap.
# ---------------------------------------------------------------------------
FLIP_THEMES = {
    'notte': dict(flap=(40, 41, 46), edge=(74, 76, 84), ink=(242, 232, 210), accent=(244, 112, 36),
                  label=(168, 160, 146), wood=None),
    'teak': dict(flap=(24, 23, 24), edge=(92, 72, 48), ink=(244, 234, 212), accent=(232, 178, 84),
                 label=(226, 204, 170), wood=(70, 42, 22)),
}


def palette(theme):
    t = FLIP_THEMES[theme]
    if t['wood']:
        rng = np.random.default_rng(3)
        yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
        rows = np.convolve(rng.normal(size=N * 2), np.ones(9) / 9, mode='same')
        fine = np.convolve(rng.normal(size=N * 2), np.ones(3) / 3, mode='same')
        idx = np.clip(yy + 14 * np.sin(xx / 150 + 1.3) + 5 * np.sin(xx / 47), 0, N * 2 - 1).astype(int)
        grain = 1 + 0.5 * rows[idx] + 0.16 * fine[idx]
        shade = 1.05 - 0.5 * (np.hypot(xx - N / 2, yy - N / 2) / (N / 2)) ** 2
        arr = np.array(t['wood'], np.float32) * (grain * shade)[..., None]
        c = Canvas(Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), 'RGB').convert('RGBA'))
    else:
        c = Canvas(Image.new('RGBA', (N, N), (9, 9, 10, 255)))
    flaps = []      # (x0, y0, x1, y1, radius)

    def fit(s, width, size, weight):
        while font(size, weight).getlength(s) / K > width:
            size -= 2
        return size

    def flap(d, x0, y0, x1, y1, r, s=None, size=0, weight=600, dy=0.0):
        flaps.append((x0, y0, x1, y1, r))
        d.rect(x0, y0, x1, y1, r, fill=t['flap'], outline=t['edge'], width=1.2)
        if s:
            d.text((x0 + x1) / 2, (y0 + y1) / 2 + dy, s, fit(s, x1 - x0 - 12, size, weight), weight, t['ink'])

    def shadows(d):
        d.rect(52, 96, 428, 276, 20, fill=(0, 0, 0, 120))            # recess behind the big flaps

    def body(d):
        for i in range(60):
            d.line([polar(i * 6, 229 if i % 5 else 225), polar(i * 6, 235)], t['label'] if i % 5 == 0 else t['edge'],
                   2 if i % 5 == 0 else 1.2, cap=False)
        for x0, x1, s in ((146, 210, V['dow']), (216, 264, V['date'][:2]), (270, 334, V['date'][3:])):
            flap(d, x0, 48, x1, 88, 7, s, 30)
        flap(d, 60, 104, 232, 268, 16, V['hh'], 190, 600)
        flap(d, 248, 104, 420, 268, 16, V['mm'], 190, 600)
        for i, s in enumerate((V['steps'], V['hr'], V['batt'] + '%')):
            flap(d, 70 + i * 116, 284, 178 + i * 116, 356, 11, s, 46)
        for x0, s in ((140, V['bell']), (244, V['sun'])):
            flap(d, x0, 396, x0 + 96, 436, 8)
            d.text(x0 + 60, 416, s, 27, 600, t['ink'])
        for i, lab in enumerate(('PASSI', 'BPM', 'BATT')):
            d.text(70 + i * 116 + 64, 376, lab, 18, 600, t['label'], spacing=0.12)

    def hinges(d):
        for x0, y0, x1, y1, r in flaps:
            ym, big = (y0 + y1) / 2, (y1 - y0) > 100
            if not big:      # small flaps carry data: only a hairline, so the numbers stay whole and bright
                d.rect(x0 + 1, ym - 0.5, x1 - 1, ym + 0.5, 0, fill=(4, 4, 5, 215))
                continue
            d.rect(x0 + 1, ym, x1 - 1, y1 - 1, r, fill=(0, 0, 0, 44), corners=(False, False, True, True))  # lower leaf in shade
            d.rect(x0, ym - 1.6, x1, ym + 1.6, 0, fill=(4, 4, 5, 255))
            d.rect(x0 + 2, ym + 1.6, x1 - 2, ym + 2.6, 0, fill=(255, 255, 255, 30))
            if big:
                for hx in (x0 - 3, x1 - 5):
                    d.rect(hx, ym - 11, hx + 8, ym + 11, 3, fill=(14, 14, 15, 255), outline=t['edge'] + (255,), width=1)

    def marks(d):
        for dy in (-22, 22):
            d.circle(C, 186 + dy, 4.6, fill=t['accent'])
        x, y = polar(V['sec'] * 6, 230)
        d.circle(x, y, 6.5, fill=t['accent'])
        d.rect(82, 361, 82 + 84, 365, 2, fill=(0, 0, 0, 150))
        d.rect(82, 361, 82 + 84 * V['sp'], 365, 2, fill=t['accent'])
        d.rect(314, 361, 314 + 84, 365, 2, fill=(0, 0, 0, 150))
        d.rect(314, 361, 314 + 84 * V['bp'], 365, 2, fill=t['accent'])

    c.paint(shadows, blur=6)
    c.paint(body)
    c.paint(hinges)
    c.paint(marks)
    for i, ic in enumerate(('steps', 'heart', 'battery')):
        c.icon(ic, 70 + i * 116 + 20, 376, 18, t['accent'])
    c.icon('bell', 140 + 24, 416, 20, t['accent'])
    c.icon('sun', 244 + 20, 415, 20, t['accent'])
    return c.finish()


CONCEPTS = [
    ('A', 'ORIZZONTE', 'Il cielo segue la giornata: il Sole è una lancetta delle 24 ore', orizzonte),
    ('B', 'MOSAICO', 'Blocchi di colore: ogni dato è un tasto grande e colorato', mosaico),
    ('C', 'CRISTALLO', 'Display a segmenti luminosi, moduli con etichetta', cristallo),
    ('D', 'CRONO', 'Analogico da strumento: i numeri stanno nei tre contatori', crono),
]


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    pad, cap = 30, 86
    sheet = Image.new('RGB', (2 * S + 3 * pad, 2 * (S + cap) + 2 * pad), (24, 25, 29))
    for i, (letter, name, line, fn) in enumerate(CONCEPTS):
        img = fn()
        flat = Image.new('RGB', (S, S), (0, 0, 0))
        flat.paste(img, (0, 0), img)
        flat.save(OUT / f'{letter}-{name.lower()}.png')
        x, y = pad + (i % 2) * (S + pad), pad + (i // 2) * (S + cap + pad // 2)
        sheet.paste(img, (x, y), img)
        d = ImageDraw.Draw(sheet)
        title, sub = ImageFont.truetype(str(VAR), 40), ImageFont.truetype(str(VAR), 26)
        title.set_variation_by_axes([600])
        sub.set_variation_by_axes([400])
        d.text((x + S / 2, y + S + 36), f'{letter} · {name}', font=title, fill=(255, 255, 255), anchor='ms')
        d.text((x + S / 2, y + S + 68), line, font=sub, fill=(182, 186, 198), anchor='ms')
        print('Mockup:', f'{letter}-{name.lower()}.png')
    sheet.save(OUT / 'confronto.png')
    print('Sheet:', OUT / 'confronto.png')

    flip = Image.new('RGB', (2 * S + 3 * pad, S + cap + pad), (24, 25, 29))
    for i, (theme, line) in enumerate((('notte', 'Notte: palette antracite, cifre avorio, accenti arancio'),
                                       ('teak', 'Teak: cassa in legno, accenti ottone'))):
        img = palette(theme)
        flat = Image.new('RGB', (S, S), (0, 0, 0))
        flat.paste(img, (0, 0), img)
        flat.save(OUT / f'E-palette-{theme}.png')
        x = pad + i * (S + pad)
        flip.paste(img, (x, pad), img)
        d = ImageDraw.Draw(flip)
        title, sub = ImageFont.truetype(str(VAR), 40), ImageFont.truetype(str(VAR), 26)
        title.set_variation_by_axes([600])
        sub.set_variation_by_axes([400])
        d.text((x + S / 2, pad + S + 36), f'E{i + 1} · PALETTE', font=title, fill=(255, 255, 255), anchor='ms')
        d.text((x + S / 2, pad + S + 68), line, font=sub, fill=(182, 186, 198), anchor='ms')
    flip.save(OUT / 'E-palette.png')
    print('Sheet:', OUT / 'E-palette.png')
