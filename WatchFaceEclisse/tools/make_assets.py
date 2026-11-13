"""Render the luminous bitmap layers of ECLISSE. Pure numpy, fully procedural.

Every glow is a white image whose alpha carries the light, so the watch can tint
it with the palette chosen by the user. Coordinates are device pixels (480 x 480).
"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

from layout import S, C, R, STAR_PAD, HANDS, ICON

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'res/drawable'
rng = np.random.default_rng(1364)  # 1364: Dondi completes the Astrarium in Padua


def grid(size=S, cx=C, cy=C):
    y, x = np.mgrid[0:size, 0:size].astype(np.float32)
    x = x + 0.5 - cx
    y = y + 0.5 - cy
    return x, y, np.hypot(x, y), np.arctan2(x, -y)  # theta: 0 = 12 o'clock, clockwise


def smoothstep(a, b, v):
    t = np.clip((v - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def angular_noise(theta, drift, harmonics, beta):
    """Periodic noise around the disc; `drift` bends the pattern with distance."""
    out = np.zeros_like(theta)
    power = 0.0
    for k in harmonics:
        amp = k ** -beta
        out += amp * np.cos(k * theta + rng.uniform(0, 2 * np.pi) + rng.normal() * drift)
        power += amp * amp / 2
    return out / np.sqrt(power)  # unit variance


def save_alpha(alpha, name, box=None):
    """White RGB + dithered alpha, cropped to `box` = (x, y, width, height)."""
    a = np.clip(alpha, 0, 1) * 255 + rng.uniform(-0.5, 0.5, alpha.shape)
    a = np.clip(np.rint(a), 0, 255).astype(np.uint8)
    rgba = np.dstack([np.full_like(a, 255)] * 3 + [a])
    if box:
        x, y, w, h = box
        rgba = rgba[y:y + h, x:x + w]
    Image.fromarray(rgba, 'RGBA').save(OUT / f'{name}.png', optimize=True)
    print(f'Asset: {name}.png {rgba.shape[1]}x{rgba.shape[0]}')


def corona():
    """Static outer corona: uneven streamers with fine radial striation."""
    x, y, r, th = grid()
    t = np.maximum(r / R, 1.0)
    lt = np.log(t)
    reach = angular_noise(th, lt * 0.3, range(1, 7), 0.45)
    reach = 1 / (1 + np.exp(-1.7 * reach))          # 0 = dark gap, 1 = long streamer
    # Short and calm on purpose: the light must never compete with the data moons.
    light = t ** -(8.6 - 4.6 * reach)
    fine = angular_noise(th, lt * 0.7, range(9, 110), 0.8)
    light *= np.clip(1 + 0.38 * fine * np.clip(lt * 6, 0, 1), 0.2, 2.0)
    light = light * 0.74 + 0.5 * np.exp(-(r - R) / 6.0)
    light = np.where(r < R, 1.0, light)
    alpha = np.clip(light, 0, 1) ** 0.9 * (1 - smoothstep(206, 239, r))
    save_alpha(alpha, 'corona')


def limb():
    """White-hot inner edge hugging the lunar disc."""
    x, y, r, th = grid()
    wobble = 1 + 0.18 * angular_noise(th, 0, range(3, 40), 0.7)
    alpha = np.where(r < R, 1.0, np.exp(-(r - R) / (2.6 * wobble)))
    save_alpha(alpha * 0.95, 'limb')


def ray(name, length, width, blade):
    """A coronal ray pointing at 12 o'clock: this is a clock hand made of light."""
    x, y, r, th = grid()
    s = np.clip((r - (R - 6)) / (length - (R - 6)), 0, 1)
    w = width * (1 - s) ** 1.35 + 1.1
    core = 0.8 * np.exp(-(x / w) ** 2) * (1 - s) ** 0.55
    veil = 0.3 * np.exp(-(x / (w * 2.0)) ** 2) * (1 - s) ** 1.2
    edge = np.exp(-(np.abs(x) / (blade * (1 - s) ** 0.5 + 0.7)) ** 2.4) * smoothstep(0, 0.1, 1 - s)  # crisp blade of light
    alpha = np.maximum(core + veil, edge) * (y < 0) * (r < length)
    save_alpha(alpha * 0.96, name, HANDS[name])


def bead():
    """Diamond-ring bead: the seconds hand. It rides the edge of the disc."""
    x, y, r, th = grid()
    by = -(R + 1.0)
    d = np.hypot(x, y - by)
    light = np.exp(-(d / 3.4) ** 2) + 0.55 * np.exp(-(d / 9.5) ** 2) + 0.2 * np.exp(-(d / 25) ** 2)
    dx, dy = np.abs(x), np.abs(y - by)
    light += 0.55 * np.exp(-(dy / 1.15) ** 2) * np.exp(-dx / 15)   # tangent flare
    light += 0.55 * np.exp(-(dx / 1.15) ** 2) * np.exp(-dy / 15)   # radial flare
    light += 0.8 * np.exp(-((r - (R + 1.4)) / 2.0) ** 2) * np.exp(-(th / 0.40) ** 2)  # bright crescent
    save_alpha(light, 'hand_second', HANDS['hand_second'])


def stars(name, count, sigma, brightness, flares=0):
    size = S + 2 * STAR_PAD
    rgb = np.zeros((size, size, 3), np.float32)
    alpha = np.zeros((size, size), np.float32)
    tints = np.array([[255, 255, 255], [205, 222, 255], [255, 236, 208], [186, 206, 255], [255, 214, 190]], np.float32)
    for i in range(count):
        cx, cy = rng.uniform(4, size - 4, 2)
        sg = rng.uniform(*sigma)
        peak = rng.uniform(*brightness)
        reach = int(np.ceil(sg * 4)) + (14 if i < flares else 0)
        x0, x1 = int(max(cx - reach, 0)), int(min(cx + reach + 1, size))
        y0, y1 = int(max(cy - reach, 0)), int(min(cy + reach + 1, size))
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        dx, dy = xx + 0.5 - cx, yy + 0.5 - cy
        a = peak * np.exp(-(dx * dx + dy * dy) / (2 * sg * sg))
        if i < flares:
            a = np.maximum(a, 0.55 * peak * np.exp(-(dy / 0.8) ** 2) * np.exp(-np.abs(dx) / 5.0))
            a = np.maximum(a, 0.55 * peak * np.exp(-(dx / 0.8) ** 2) * np.exp(-np.abs(dy) / 5.0))
        mask = a > alpha[y0:y1, x0:x1]
        alpha[y0:y1, x0:x1] = np.where(mask, a, alpha[y0:y1, x0:x1])
        rgb[y0:y1, x0:x1][mask] = tints[rng.integers(len(tints))]
    rgb[alpha <= 0] = 255
    rgba = np.dstack([rgb, np.clip(alpha, 0, 1) * 255]).round().astype(np.uint8)
    Image.fromarray(rgba, 'RGBA').save(OUT / f'{name}.png', optimize=True)
    print(f'Asset: {name}.png {size}x{size}')


def icon(name, paint):
    """Solid, tintable glyph drawn 8x oversampled so it stays crisp at 24 px."""
    k = 8
    im = Image.new('L', (ICON * k, ICON * k), 0)
    paint(ImageDraw.Draw(im), k)
    a = np.asarray(im.resize((ICON, ICON), Image.LANCZOS))
    Image.fromarray(np.dstack([np.full_like(a, 255)] * 3 + [a]), 'RGBA').save(OUT / f'{name}.png', optimize=True)
    print(f'Asset: {name}.png {ICON}x{ICON}')


def glyph_heart(d, k):
    pts = []
    for i in range(200):
        t = i / 200 * 2 * np.pi
        x = 16 * np.sin(t) ** 3
        y = -(13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t))
        pts.append(((12 + x * 0.66) * k, (11.2 + y * 0.66) * k))
    d.polygon(pts, fill=255)


def glyph_steps(d, k):
    for x, y in ((4.0, 7.6), (13.4, 1.2)):                      # left foot, right foot a stride ahead
        d.ellipse([x * k, y * k, (x + 6.6) * k, (y + 9.8) * k], fill=255)          # sole
        d.ellipse([(x + 0.8) * k, (y + 11.0) * k, (x + 5.8) * k, (y + 15.2) * k], fill=255)  # heel


def glyph_battery(d, k):
    d.rounded_rectangle([9.5 * k, 1.5 * k, 14.5 * k, 5 * k], radius=1 * k, fill=255)            # terminal
    d.rounded_rectangle([6 * k, 3.6 * k, 18 * k, 22.5 * k], radius=2.6 * k, outline=255, width=round(2.1 * k))
    d.rounded_rectangle([9.1 * k, 11 * k, 14.9 * k, 19.4 * k], radius=0.9 * k, fill=255)         # charge


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    corona()
    limb()
    icon('ic_heart', glyph_heart)
    icon('ic_steps', glyph_steps)
    icon('ic_battery', glyph_battery)
    ray('hand_minute', 238, 10.5, 1.9)
    ray('hand_hour', 198, 21.0, 3.6)
    bead()
    stars('stars_far', 230, (0.6, 0.95), (0.3, 0.8))
    stars('stars_near', 50, (0.9, 1.5), (0.7, 1.0), flares=8)
