"""Render the font and the bitmap parts of PALETTE: flap bodies, hinges, flip frames, icons.

Teko is licensed under the SIL Open Font License 1.1 (see licenses/Teko-OFL.txt).
"""
from pathlib import Path
import math
import numpy as np
from PIL import Image, ImageDraw
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

from layout import BIG_W, BIG_H, BIG_R, PIN, SEC_W, SEC_H, ICON, FLIP_BIG_FRAMES, FLIP_SMALL_FRAMES

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'res/drawable'
Q = 4   # oversampling

FLAP_TOP, FLAP_MID_UP, FLAP_MID_DOWN, FLAP_BOTTOM = (52, 53, 60), (41, 42, 47), (36, 37, 42), (29, 30, 34)
EDGE = (74, 76, 84)


def font():
    f = instantiateVariableFont(TTFont(ROOT / 'design/teko_variable.ttf'), {'wght': 600})
    f['OS/2'].usWeightClass = 600
    target = ROOT / 'res/font/teko_semibold.ttf'
    f.save(target)
    print('Font:', target.name, target.stat().st_size, 'bytes')


def save(img, name, folder=OUT):
    img.save(folder / f'{name}.png', optimize=True)
    print(f'Asset: {name}.png {img.width}x{img.height}')


def rounded_mask(w, h, r, corners=(True, True, True, True)):
    m = Image.new('L', (w * Q, h * Q), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w * Q - 1, h * Q - 1], radius=r * Q, fill=255, corners=corners)
    return m


def vertical_gradient(w, h, stops):
    """stops: [(y, (r, g, b))] in logical pixels -> RGB image at Q x."""
    ys = (np.arange(h * Q) + 0.5) / Q
    cols = np.stack([np.interp(ys, [s[0] for s in stops], [s[1][i] for s in stops]) for i in range(3)], axis=1)
    return Image.fromarray(np.repeat(cols[:, None, :], w * Q, axis=1).astype(np.uint8), 'RGB')


def down(img, w, h):
    return img.resize((w, h), Image.LANCZOS)


def flap_big():
    """Flap body with a soft gradient: lit from above, lower leaf slightly in shade."""
    mid = BIG_H / 2
    body = vertical_gradient(BIG_W, BIG_H, [(0, FLAP_TOP), (mid, FLAP_MID_UP), (mid + 0.01, FLAP_MID_DOWN), (BIG_H, FLAP_BOTTOM)])
    d = ImageDraw.Draw(body)
    d.rounded_rectangle([0, 0, BIG_W * Q - 1, BIG_H * Q - 1], radius=BIG_R * Q, outline=EDGE, width=round(1.3 * Q))
    body.putalpha(rounded_mask(BIG_W, BIG_H, BIG_R))
    save(down(body, BIG_W, BIG_H), 'flap_big')


def flap_big_overlay():
    """Everything that sits in front of the digits: hinge, its cast shadow, the two pins."""
    w, mid = BIG_W + 2 * PIN, BIG_H / 2
    img = Image.new('RGBA', (w * Q, BIG_H * Q), (0, 0, 0, 0))
    a = np.zeros((BIG_H * Q, w * Q), np.float32)
    ys = ((np.arange(BIG_H * Q) + 0.5) / Q)[:, None]
    xs = ((np.arange(w * Q) + 0.5) / Q)[None, :]
    inside = (xs > PIN + 1) & (xs < PIN + BIG_W - 1)
    a += np.where(ys > mid, 0.42 * np.exp(-(ys - mid) / 9.0), 0.16 * np.exp(-(mid - ys) / 4.0)) * inside   # cast shadow
    shadow = np.zeros((BIG_H * Q, w * Q, 4), np.uint8)
    shadow[..., 3] = np.clip(a * 255, 0, 255)
    img = Image.fromarray(shadow, 'RGBA')
    d = ImageDraw.Draw(img)
    d.rectangle([PIN * Q, (mid - 1.6) * Q, (PIN + BIG_W) * Q, (mid + 1.6) * Q], fill=(4, 4, 5, 255))        # the split
    d.rectangle([(PIN + 2) * Q, (mid + 1.6) * Q, (PIN + BIG_W - 2) * Q, (mid + 2.5) * Q], fill=(255, 255, 255, 34))
    for x in (1, BIG_W + PIN - 4):                                                                    # hinge pins
        d.rounded_rectangle([x * Q, (mid - 12) * Q, (x + 8) * Q, (mid + 12) * Q], radius=3 * Q, fill=(15, 15, 17, 255),
                            outline=EDGE + (255,), width=Q)
    save(down(img, w, BIG_H), 'flap_big_overlay')


def flip_frames(prefix, w, h, r, count):
    """A blank leaf falling across the flap: first over the upper half, then onto the lower half."""
    mid = h / 2
    half = count // 2
    for i in range(count):
        img = Image.new('RGBA', (w * Q, h * Q), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        if i < half:                       # upper phase: leaf shrinks towards the hinge and darkens edge-on
            f = 1 - i / half * 0.85
            light = 0.62 + 0.38 * f
            top = mid - mid * f
            col = tuple(round(c * light) for c in FLAP_TOP)
            d.rounded_rectangle([0, top * Q, w * Q - 1, mid * Q], radius=r * Q * f, fill=col + (255,),
                                corners=(True, True, False, False))
            d.rectangle([Q, top * Q, w * Q - 1 - Q, (top + 1.4) * Q], fill=(150, 152, 162, 255))      # catching the light
        else:                              # lower phase: leaf swings down and lands
            f = (i - half + 1) / (count - half)
            light = 0.7 + 0.3 * f
            bottom = mid + mid * f
            col = tuple(round(c * light) for c in FLAP_MID_DOWN)
            d.rectangle([0, bottom * Q, w * Q - 1, min(h, bottom + 7) * Q], fill=(0, 0, 0, 90))        # shadow ahead of the leaf
            d.rounded_rectangle([0, mid * Q, w * Q - 1, bottom * Q - 1], radius=r * Q * f, fill=col + (255,),
                                corners=(False, False, True, True))
            d.rectangle([Q, (bottom - 1.4) * Q, w * Q - 1 - Q, bottom * Q - 1], fill=(120, 122, 132, 255))
        d.rectangle([0, (mid - 1.2) * Q, w * Q - 1, (mid + 1.2) * Q], fill=(4, 4, 5, 255))
        out = down(img, w, h)
        out.putalpha(Image.composite(out.getchannel('A'), Image.new('L', (w, h), 0), down(rounded_mask(w, h, r), w, h)))
        save(out, f'{prefix}_{i + 1}')


def icon(name, paint, size=ICON, folder=OUT):
    k = max(1, round(size / 24 * 8))
    im = Image.new('L', (24 * k, 24 * k), 0)
    paint(ImageDraw.Draw(im), k)
    a = np.asarray(im.resize((size, size), Image.LANCZOS))
    save(Image.fromarray(np.dstack([np.full_like(a, 255)] * 3 + [a]), 'RGBA'), name, folder)


def glyph_heart(d, k):
    pts = []
    for i in range(200):
        t = i / 200 * 2 * math.pi
        x = 16 * math.sin(t) ** 3
        y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
        pts.append(((12 + x * 0.66) * k, (11.2 + y * 0.66) * k))
    d.polygon(pts, fill=255)


def glyph_steps(d, k):
    for x, y in ((4.0, 7.6), (13.4, 1.2)):
        d.ellipse([x * k, y * k, (x + 6.6) * k, (y + 9.8) * k], fill=255)
        d.ellipse([(x + 0.8) * k, (y + 11.0) * k, (x + 5.8) * k, (y + 15.2) * k], fill=255)


def glyph_battery(d, k):
    d.rounded_rectangle([9.5 * k, 1.5 * k, 14.5 * k, 5 * k], radius=1 * k, fill=255)
    d.rounded_rectangle([6 * k, 3.6 * k, 18 * k, 22.5 * k], radius=2.6 * k, outline=255, width=round(2.1 * k))
    d.rounded_rectangle([9.1 * k, 11 * k, 14.9 * k, 19.4 * k], radius=0.9 * k, fill=255)


def glyph_mic(d, k):
    d.rounded_rectangle([8.4 * k, 1.6 * k, 15.6 * k, 14.2 * k], radius=3.6 * k, fill=255)             # capsule
    d.arc([4.6 * k, 3.2 * k, 19.4 * k, 18 * k], 0, 180, fill=255, width=round(2 * k))                 # cradle
    d.rectangle([11 * k, 17.6 * k, 13 * k, 21 * k], fill=255)                                         # stem
    d.rounded_rectangle([7.4 * k, 20.4 * k, 16.6 * k, 22.6 * k], radius=1.1 * k, fill=255)             # foot


# ---- weather glyphs (24-unit grid) -------------------------------------------
def cloud(d, k, dx=0.0, dy=0.0, s=1.0, fill=255):
    def box(x0, y0, x1, y1):
        return [(dx + x0 * s) * k, (dy + y0 * s) * k, (dx + x1 * s) * k, (dy + y1 * s) * k]
    d.ellipse(box(3, 10, 12, 19), fill=fill)
    d.ellipse(box(7.5, 5, 18.5, 16), fill=fill)
    d.ellipse(box(14, 10.5, 22, 18.5), fill=fill)
    d.rounded_rectangle(box(6, 13, 19, 19), radius=2.5 * s * k, fill=fill)


def rays(d, k, cx, cy, r0, r1, n=8, width=2.0):
    for i in range(n):
        a = math.radians(i * 360 / n)
        d.line([((cx + math.sin(a) * r0) * k, (cy - math.cos(a) * r0) * k),
                ((cx + math.sin(a) * r1) * k, (cy - math.cos(a) * r1) * k)], fill=255, width=round(width * k))


def glyph_wx_sun(d, k):
    d.ellipse([6.6 * k, 6.6 * k, 17.4 * k, 17.4 * k], fill=255)
    rays(d, k, 12, 12, 7.8, 11)


def glyph_wx_moon(d, k):
    d.ellipse([3.5 * k, 3.5 * k, 20.5 * k, 20.5 * k], fill=255)
    d.ellipse([9 * k, 1 * k, 24 * k, 16 * k], fill=0)


def glyph_wx_partly(d, k):
    d.ellipse([12.2 * k, 3.2 * k, 20.2 * k, 11.2 * k], fill=255)
    rays(d, k, 16.2, 7.2, 5.4, 7.4, width=1.7)
    cloud(d, k, -2.6, 2.4, 1.0, fill=0)          # dark gap between sun and cloud
    cloud(d, k, -1.2, 4.2, 0.88)


def glyph_wx_cloud(d, k):
    cloud(d, k, -0.5, 0.5)


def glyph_wx_fog(d, k):
    cloud(d, k, 1.2, -2.6, 0.86)
    for y, x0, x1 in ((16.6, 3, 21), (20.6, 6, 18)):
        d.rounded_rectangle([x0 * k, y * k, x1 * k, (y + 2.2) * k], radius=1.1 * k, fill=255)


def glyph_wx_rain(d, k):
    cloud(d, k, 1.2, -3.4, 0.86)
    for x in (7, 12, 17):
        d.line([((x + 0.9) * k, 16.4 * k), ((x - 1.1) * k, 22 * k)], fill=255, width=round(2.2 * k))


def glyph_wx_snow(d, k):
    cloud(d, k, 1.2, -3.4, 0.86)
    for x, y in ((7, 17.6), (12, 20.2), (17, 17.6), (7.4, 22.2), (16.6, 22.2)):
        d.ellipse([(x - 1.4) * k, (y - 1.4) * k, (x + 1.4) * k, (y + 1.4) * k], fill=255)


def glyph_wx_storm(d, k):
    cloud(d, k, 1.2, -3.6, 0.86)
    d.polygon([(13.6 * k, 13.2 * k), (8.4 * k, 19.2 * k), (11.6 * k, 19.2 * k), (10 * k, 23.6 * k), (16 * k, 17 * k),
               (12.6 * k, 17 * k)], fill=255)
    d.line([(13.6 * k, 13.2 * k), (8.4 * k, 19.2 * k)], fill=0, width=1)


def glyph_wx_wind(d, k):
    w = round(2.2 * k)
    d.line([(2.5 * k, 8.6 * k), (14.5 * k, 8.6 * k)], fill=255, width=w)
    d.arc([11.6 * k, 2.6 * k, 17.6 * k, 8.6 * k + w / 2], 160, 90, fill=255, width=w)
    d.line([(2.5 * k, 13.4 * k), (18.6 * k, 13.4 * k)], fill=255, width=w)
    d.arc([15.4 * k, 13.4 * k - w / 2, 21.8 * k, 19.8 * k], 270, 200, fill=255, width=w)
    d.line([(2.5 * k, 18.2 * k), (10.5 * k, 18.2 * k)], fill=255, width=w)


def glyph_umbrella(d, k):
    d.pieslice([2.5 * k, 2.6 * k, 21.5 * k, 21.6 * k], 180, 360, fill=255)
    d.rectangle([11 * k, 11 * k, 13 * k, 19.4 * k], fill=255)
    d.arc([7.4 * k, 16 * k, 13 * k, 21.8 * k], 0, 180, fill=255, width=round(2 * k))


WEATHER_GLYPHS = {'wx_sun': glyph_wx_sun, 'wx_moon': glyph_wx_moon, 'wx_partly': glyph_wx_partly,
                  'wx_cloud': glyph_wx_cloud, 'wx_fog': glyph_wx_fog, 'wx_rain': glyph_wx_rain,
                  'wx_snow': glyph_wx_snow, 'wx_storm': glyph_wx_storm, 'wx_wind': glyph_wx_wind,
                  'ic_umbrella': glyph_umbrella}


if __name__ == '__main__':
    for stale in list(OUT.glob('*.png')) + list((ROOT / 'res/font').glob('*.ttf')):
        stale.unlink()
    font()
    flap_big()
    flap_big_overlay()
    flip_frames('flip_big', BIG_W, BIG_H, BIG_R, FLIP_BIG_FRAMES)
    flip_frames('flip_small', SEC_W, SEC_H, 10, FLIP_SMALL_FRAMES)
    icon('ic_steps', glyph_steps)
    icon('ic_heart', glyph_heart)
    icon('ic_battery', glyph_battery)
    icon('ic_mic', glyph_mic, 38)
    for name, paint in WEATHER_GLYPHS.items():
        icon(name, paint)
    sheet = Image.new('RGB', (len(WEATHER_GLYPHS) * 56 + 8, 64), (20, 20, 22))    # contact sheet to proof the glyphs
    for i, name in enumerate(WEATHER_GLYPHS):
        g = Image.open(OUT / f'{name}.png').resize((48, 48), Image.LANCZOS)
        sheet.paste(Image.new('RGB', g.size, (244, 112, 36)), (8 + i * 56, 8), g.getchannel('A'))
    sheet.save(ROOT / 'design/weather-glyphs.png')
