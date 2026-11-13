"""Render the bitmap assets of SOLARI: split-flap body, hinges, falling leaf frames, bezel ticks, icons."""
from pathlib import Path
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from layout import (S, C, FLIP_W, FLIP_H, FLIP_R, PIN, FLIP_FRAMES,
                    TICK_R_OUT, TICK_R_MAJ, TICK_R_MIN, NUM_R, DOT_R, ICON, MIC_ICON)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'res/drawable'
Q = 4  # oversampling factor

FLAP_TOP = (52, 54, 62)
FLAP_MID_UP = (40, 41, 47)
FLAP_MID_DOWN = (33, 34, 40)
FLAP_BOTTOM = (26, 27, 32)
EDGE = (80, 84, 96)


def save(img, name):
    img.save(OUT / f'{name}.png', optimize=True)
    print(f'Asset: {name}.png {img.width}x{img.height}')


def rounded_mask(w, h, r, corners=(True, True, True, True)):
    m = Image.new('L', (w * Q, h * Q), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w * Q - 1, h * Q - 1], radius=r * Q, fill=255, corners=corners)
    return m


def vertical_gradient(w, h, stops):
    ys = (np.arange(h * Q) + 0.5) / Q
    cols = np.stack([np.interp(ys, [s[0] for s in stops], [s[1][i] for s in stops]) for i in range(3)], axis=1)
    return Image.fromarray(np.repeat(cols[:, None, :], w * Q, axis=1).astype(np.uint8), 'RGB')


def down(img, w, h):
    return img.resize((w, h), Image.LANCZOS)


def flap_body():
    mid = FLIP_H / 2
    body = vertical_gradient(FLIP_W, FLIP_H, [
        (0, FLAP_TOP), (mid, FLAP_MID_UP), (mid + 0.01, FLAP_MID_DOWN), (FLIP_H, FLAP_BOTTOM),
    ])
    d = ImageDraw.Draw(body)
    d.rounded_rectangle([0, 0, FLIP_W * Q - 1, FLIP_H * Q - 1], radius=FLIP_R * Q, outline=EDGE, width=round(1.4 * Q))
    # Subtle top-edge catchlight so the upper leaf reads as raised above the housing.
    d.line([FLIP_R * Q, round(1.5 * Q), (FLIP_W - FLIP_R) * Q, round(1.5 * Q)],
           fill=(110, 114, 130), width=max(1, round(1.0 * Q)))
    body.putalpha(rounded_mask(FLIP_W, FLIP_H, FLIP_R))
    save(down(body, FLIP_W, FLIP_H), 'flap_body')


def flap_overlay():
    """Split groove, cast shadow, lip highlight, and side hinge pins."""
    w, mid = FLIP_W + 2 * PIN, FLIP_H / 2
    ys = ((np.arange(FLIP_H * Q) + 0.5) / Q)[:, None]
    xs = ((np.arange(w * Q) + 0.5) / Q)[None, :]
    inside = (xs > PIN + 1) & (xs < PIN + FLIP_W - 1)
    a = np.where(ys > mid, 0.52 * np.exp(-(ys - mid) / 8.0), 0.16 * np.exp(-(mid - ys) / 3.5)) * inside
    shadow = np.zeros((FLIP_H * Q, w * Q, 4), np.uint8)
    shadow[..., 3] = np.clip(a * 255, 0, 255)
    img = Image.fromarray(shadow, 'RGBA')
    d = ImageDraw.Draw(img)
    d.rectangle([PIN * Q, (mid - 1.5) * Q, (PIN + FLIP_W) * Q, (mid + 1.5) * Q], fill=(6, 7, 10, 255))
    d.rectangle([(PIN + 2) * Q, (mid + 1.5) * Q, (PIN + FLIP_W - 2) * Q, (mid + 2.5) * Q], fill=(255, 255, 255, 52))
    for x in (1.5, FLIP_W + PIN - 3.5):
        d.rounded_rectangle([x * Q, (mid - 9) * Q, (x + 7) * Q, (mid + 9) * Q], radius=2.5 * Q,
                            fill=(18, 19, 23, 255), outline=EDGE + (255,), width=round(1.1 * Q))
    save(down(img, w, FLIP_H), 'flap_overlay')


def flip_frames():
    """Mechanical falling leaf animation played on every hour/minute change."""
    mid = FLIP_H / 2
    half = FLIP_FRAMES // 2
    card_mask = down(rounded_mask(FLIP_W, FLIP_H, FLIP_R), FLIP_W, FLIP_H)
    for i in range(FLIP_FRAMES):
        img = Image.new('RGBA', (FLIP_W * Q, FLIP_H * Q), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        if i < half:
            f = 1 - i / half * 0.86
            light = 0.60 + 0.40 * f
            top = mid - mid * f
            col = tuple(round(c * light) for c in FLAP_TOP)
            d.rounded_rectangle([0, top * Q, FLIP_W * Q - 1, mid * Q], radius=FLIP_R * Q * f,
                                fill=col + (255,), corners=(True, True, False, False))
            d.rectangle([Q, top * Q, FLIP_W * Q - 1 - Q, (top + 1.4) * Q], fill=(165, 168, 180, 255))
        else:
            f = (i - half + 1) / (FLIP_FRAMES - half)
            light = 0.68 + 0.32 * f
            bottom = mid + mid * f
            col = tuple(round(c * light) for c in FLAP_MID_DOWN)
            d.rectangle([0, bottom * Q, FLIP_W * Q - 1, min(FLIP_H, bottom + 7) * Q], fill=(0, 0, 0, 95))
            d.rounded_rectangle([0, mid * Q, FLIP_W * Q - 1, bottom * Q - 1], radius=FLIP_R * Q * f,
                                fill=col + (255,), corners=(False, False, True, True))
            d.rectangle([Q, (bottom - 1.4) * Q, FLIP_W * Q - 1 - Q, bottom * Q - 1], fill=(130, 134, 148, 255))
        d.rectangle([0, (mid - 1.2) * Q, FLIP_W * Q - 1, (mid + 1.2) * Q], fill=(6, 7, 10, 255))
        out = down(img, FLIP_W, FLIP_H)
        out.putalpha(Image.composite(out.getchannel('A'), Image.new('L', (FLIP_W, FLIP_H), 0), card_mask))
        save(out, f'flip_leaf_{i + 1}')


def bezel_ticks():
    """60 crisp perimeter chrono ticks + 12 o'clock anchor + 15/30/45 markers."""
    img = Image.new('RGBA', (S * Q, S * Q), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for i in range(60):
        a = math.radians(i * 6)
        major = (i % 5 == 0)
        r0 = (TICK_R_MAJ - 2 if i == 0 else TICK_R_MAJ) if major else TICK_R_MIN
        x0 = (C + r0 * math.sin(a)) * Q
        y0 = (C - r0 * math.cos(a)) * Q
        x1 = (C + TICK_R_OUT * math.sin(a)) * Q
        y1 = (C - TICK_R_OUT * math.cos(a)) * Q
        if i == 0:
            col = (224, 220, 210, 255)
            w = round(2.8 * Q)
        elif major:
            col = (114, 122, 144, 255)
            w = round(2.2 * Q)
        else:
            col = (60, 66, 82, 255)
            w = round(1.2 * Q)
        d.line([(x0, y0), (x1, y1)], fill=col, width=w)
    f = ImageFont.truetype(str(ROOT / 'res/font/teko_semibold.ttf'), 14 * Q)
    for deg, lbl in ((90, '15'), (180, '30'), (270, '45')):
        a = math.radians(deg)
        nx = (C + NUM_R * math.sin(a)) * Q
        ny = (C - NUM_R * math.cos(a)) * Q
        d.text((nx, ny + 0.311 * 14 * Q), lbl, font=f, fill=(144, 152, 174, 255), anchor='ms')
    save(down(img, S, S), 'bezel_ticks')


def sec_dot():
    """White tintable seconds bead with a crisp dark border."""
    size = 16
    img = Image.new('RGBA', (size * Q, size * Q), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = cy = size * Q / 2
    r_outer = (DOT_R + 1.4) * Q
    r_inner = DOT_R * Q
    d.ellipse([cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer], fill=(0, 0, 0, 230))
    d.ellipse([cx - r_inner, cy - r_inner, cx + r_inner, cy + r_inner], fill=(255, 255, 255, 255))
    save(down(img, size, size), 'sec_dot')


def icon(name, paint, size=ICON):
    k = max(1, round(size / 24 * 8))
    im = Image.new('L', (24 * k, 24 * k), 0)
    paint(ImageDraw.Draw(im), k)
    a = np.asarray(im.resize((size, size), Image.LANCZOS))
    save(Image.fromarray(np.dstack([np.full_like(a, 255)] * 3 + [a]), 'RGBA'), name)


def glyph_mic(d, k):
    d.rounded_rectangle([8.4 * k, 1.6 * k, 15.6 * k, 14.2 * k], radius=3.6 * k, fill=255)
    d.arc([4.6 * k, 3.2 * k, 19.4 * k, 18 * k], 0, 180, fill=255, width=round(2 * k))
    d.rectangle([11 * k, 17.6 * k, 13 * k, 21 * k], fill=255)
    d.rounded_rectangle([7.4 * k, 20.4 * k, 16.6 * k, 22.6 * k], radius=1.1 * k, fill=255)


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
    cloud(d, k, -2.6, 2.4, 1.0, fill=0)
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


WEATHER_GLYPHS = {
    'wx_sun': glyph_wx_sun, 'wx_moon': glyph_wx_moon, 'wx_partly': glyph_wx_partly,
    'wx_cloud': glyph_wx_cloud, 'wx_fog': glyph_wx_fog, 'wx_rain': glyph_wx_rain,
    'wx_snow': glyph_wx_snow, 'wx_storm': glyph_wx_storm, 'wx_wind': glyph_wx_wind,
}


def glyph_heart(d, k):
    pts = []
    for i in range(200):
        t = i / 200 * 2 * np.pi
        x = 16 * np.sin(t) ** 3
        y = -(13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t))
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


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    flap_body()
    flap_overlay()
    flip_frames()
    bezel_ticks()
    sec_dot()
    icon('ic_heart', glyph_heart)
    icon('ic_steps', glyph_steps)
    icon('ic_battery', glyph_battery)
    icon('ic_mic', glyph_mic, MIC_ICON)
    for name, paint in WEATHER_GLYPHS.items():
        icon(name, paint)
