"""Four redesign studies for ECLISSE addressing the heavy side moons.

Design studies only: nothing here alters watchface.xml or ECLISSE.apk.
Every variant uses the actual ECLISSE bitmap assets and WFF-2-compatible primitives.
"""
from pathlib import Path
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from layout import S, C, HANDS, polar

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'design/mockups'
VAR = ROOT / 'design/teko_variable.ttf'

K = 2
N = S * K

ACCENT = (255, 197, 110)
DIM = (138, 102, 48)
HOT = (255, 244, 222)
INK = (246, 244, 239)
WHITE = (255, 255, 255)
SOFT = (210, 213, 221)
TRACK = (52, 58, 72)
BLACK = (0, 0, 0)

SAMPLE = dict(
    hour=9, minute=27, second=6,
    steps=6480, goal=10000, heart=72, battery=84,
    weekday='GIOVEDÌ', date='12 NOV', bell='3', sun='07:12',
)

_fonts = {}


def get_font(family, size):
    key = (family, round(size * K, 2))
    if key not in _fonts:
        _fonts[key] = ImageFont.truetype(str(ROOT / f'res/font/{family}.ttf'), size * K)
    return _fonts[key]


def paste_asset(img, name, x, y, w, h, tint=None, angle=0, scale_from_center=1.0):
    src = Image.open(ROOT / f'res/drawable/{name}.png').convert('RGBA')
    sw, sh = round(w * K * scale_from_center), round(h * K * scale_from_center)
    src = src.resize((sw, sh), Image.BICUBIC)
    if tint:
        solid = Image.new('RGBA', src.size, tint + (255,))
        solid.putalpha(src.getchannel('A'))
        src = solid
    layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
    if scale_from_center != 1.0:
        cx_off = round((C - (C - x) * scale_from_center) * K)
        cy_off = round((C - (C - y) * scale_from_center) * K)
        layer.paste(src, (cx_off, cy_off))
    else:
        layer.paste(src, (round(x * K), round(y * K)))
    if angle:
        layer = layer.rotate(-angle, Image.BICUBIC, center=(C * K, C * K))
    img.alpha_composite(layer)


def paint_sky_and_corona(img, disc_r=132):
    scale = disc_r / 132.0
    paste_asset(img, 'stars_far', -20, -20, 520, 520)
    paste_asset(img, 'stars_near', -20, -20, 520, 520)
    paste_asset(img, 'corona', 0, 0, S, S, tint=ACCENT, scale_from_center=scale)
    h_ang = (SAMPLE['hour'] % 12) * 30 + SAMPLE['minute'] * 0.5
    m_ang = SAMPLE['minute'] * 6 + SAMPLE['second'] * 0.1
    s_ang = SAMPLE['second'] * 6
    for name, ang in (('hand_hour', h_ang), ('hand_minute', m_ang)):
        x, y, w, h = HANDS[name]
        paste_asset(img, name, x, y, w, h, tint=HOT, angle=ang, scale_from_center=scale)
    paste_asset(img, 'limb', 0, 0, S, S, tint=HOT, scale_from_center=scale)
    d = ImageDraw.Draw(img)
    d.ellipse([(C - disc_r) * K, (C - disc_r) * K, (C + disc_r) * K, (C + disc_r) * K], fill=(0, 0, 0, 255))
    sx, sy, sw, sh = HANDS['hand_second']
    paste_asset(img, 'hand_second', sx, sy, sw, sh, tint=HOT, angle=s_ang, scale_from_center=scale)


def draw_text_centered(img, cx, cap_cy, size, color, text, family='teko_semibold'):
    d = ImageDraw.Draw(img)
    f = get_font(family, size)
    # Teko metrics match generate.py
    cap_shift = 0.0695
    baseline = (0.958 - 0.475) / 2
    height = math.ceil(size * 1.5)
    y = round(cap_cy + cap_shift * size - height / 2)
    w = f.getlength(text)
    X = cx * K - w / 2
    Y = (y + height / 2 + baseline * size) * K
    d.text((X, Y), text, font=f, fill=color + (255,), anchor='ls')


def paint_time(img, time_size=134, day_size=33, date_size=33, cy_time=242, cy_day=163, cy_date=321, col_step=54, gap_half=38):
    hh = '%02d' % SAMPLE['hour']
    mm = '%02d' % SAMPLE['minute']
    cols = [
        (C - gap_half - col_step, hh[0]),
        (C - gap_half, hh[1]),
        (C + gap_half, mm[0]),
        (C + gap_half + col_step, mm[1]),
    ]
    for cx, ch in cols:
        draw_text_centered(img, cx, cy_time, time_size, INK, ch, family='teko_regular')
    d = ImageDraw.Draw(img)
    dot_r = 5.2 * (time_size / 134.0) * K
    dot_dy = 17 * (time_size / 134.0)
    for dy in (-dot_dy, dot_dy):
        X, Y = C * K, (cy_time + dy) * K
        d.ellipse([X - dot_r, Y - dot_r, X + dot_r, Y + dot_r], fill=ACCENT + (255,))
    draw_text_centered(img, C, cy_day, day_size, ACCENT, SAMPLE['weekday'])
    draw_text_centered(img, C, cy_date, date_size, SOFT, SAMPLE['date'])


def draw_icon_bell(d, cx, cy, size, color):
    s = size / 24.0
    w = max(1, round(2.6 * s * K))
    d.arc([(cx - 7.2 * s) * K, (cy - 7.2 * s) * K, (cx + 7.2 * s) * K, (cy + 7.2 * s) * K],
          180, 0, fill=color + (255,), width=w)
    d.line([(cx - 7.2 * s) * K, cy * K, (cx - 7.2 * s) * K, (cy + 5.0 * s) * K], fill=color + (255,), width=w)
    d.line([(cx + 7.2 * s) * K, cy * K, (cx + 7.2 * s) * K, (cy + 5.0 * s) * K], fill=color + (255,), width=w)
    d.line([(cx - 10 * s) * K, (cy + 6.5 * s) * K, (cx + 10 * s) * K, (cy + 6.5 * s) * K], fill=color + (255,), width=w)
    r = 2.0 * s * K
    d.ellipse([cx * K - r, (cy + 10.5 * s) * K - r, cx * K + r, (cy + 10.5 * s) * K + r], fill=color + (255,))


def draw_icon_sun(d, cx, cy, size, color):
    s = size / 24.0
    w = max(1, round(2.6 * s * K))
    d.arc([(cx - 6.2 * s) * K, (cy - 1.2 * s) * K, (cx + 6.2 * s) * K, (cy + 11.2 * s) * K],
          180, 0, fill=color + (255,), width=w)
    d.line([(cx - 11 * s) * K, (cy + 7 * s) * K, (cx + 11 * s) * K, (cy + 7 * s) * K], fill=color + (255,), width=w)
    for ang in (-60, 0, 60):
        sn, cs = math.sin(math.radians(ang)), -math.cos(math.radians(ang))
        d.line([(cx + sn * 9.6 * s) * K, (cy + 5 * s + cs * 9.6 * s) * K,
                (cx + sn * 12.6 * s) * K, (cy + 5 * s + cs * 12.6 * s) * K],
               fill=color + (255,), width=max(1, round(2.2 * s * K)))


def draw_asset_icon(img, name, cx, cy, size, color):
    src = Image.open(ROOT / f'res/drawable/{name}.png').convert('RGBA')
    px = round(size * K)
    src = src.resize((px, px), Image.LANCZOS)
    solid = Image.new('RGBA', src.size, color + (255,))
    solid.putalpha(src.getchannel('A'))
    img.alpha_composite(solid, (round(cx * K - px / 2), round(cy * K - px / 2)))


def draw_arc(d, cx, cy, r, start_deg, end_deg, color, thickness):
    """Clock degrees: 0 = 12 o'clock, clockwise. Draws start_deg -> end_deg (or CCW if end < start)."""
    o = r + thickness / 2
    box = [(cx - o) * K, (cy - o) * K, (cx + o) * K, (cy + o) * K]
    a0, a1 = start_deg - 90, end_deg - 90
    if a1 < a0:
        a0, a1 = a1, a0
    d.arc(box, a0, a1, fill=color + (255,), width=max(1, round(thickness * K)))
    rr = thickness * K / 2
    for ang in (start_deg, end_deg):
        ex = (cx + r * math.sin(math.radians(ang))) * K
        ey = (cy - r * math.cos(math.radians(ang))) * K
        d.ellipse([ex - rr, ey - rr, ex + rr, ey + rr], fill=color + (255,))


def draw_inline_item(img, cx, cy, icon_fn_or_name, text, icon_size=18, text_size=26, icon_color=ACCENT, text_color=WHITE, gap=6):
    f = get_font('teko_semibold', text_size)
    tw = f.getlength(text) / K
    total = icon_size + gap + tw
    ix = cx - total / 2 + icon_size / 2
    tx = cx - total / 2 + icon_size + gap + tw / 2
    if callable(icon_fn_or_name):
        icon_fn_or_name(ImageDraw.Draw(img), ix, cy, icon_size, icon_color)
    else:
        draw_asset_icon(img, icon_fn_or_name, ix, cy, icon_size, icon_color)
    draw_text_centered(img, tx, cy, text_size, text_color, text)


def draw_stacked_item(img, cx, cy, icon_fn_or_name, text, icon_size=20, text_size=28, icon_color=ACCENT, text_color=WHITE, dy=13):
    if callable(icon_fn_or_name):
        icon_fn_or_name(ImageDraw.Draw(img), cx, cy - dy, icon_size, icon_color)
    else:
        draw_asset_icon(img, icon_fn_or_name, cx, cy - dy, icon_size, icon_color)
    draw_text_centered(img, cx, cy + dy + 1, text_size, text_color, text)


def finalize(img):
    mask = Image.new('L', (N, N), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, N - 1, N - 1], fill=255)
    out = Image.new('RGBA', (N, N), (0, 0, 0, 0))
    out.paste(img, (0, 0), mask)
    return out.resize((S, S), Image.LANCZOS)


# ---------------------------------------------------------------------------
def v1_fantasma():
    """Keep all 5 data points, remove the black circular moon containers completely."""
    img = Image.new('RGBA', (N, N), (0, 0, 0, 255))
    paint_sky_and_corona(img, 132)
    paint_time(img)
    # Floating micro-badges without black discs or borders, pushed slightly closer to the rim
    orbit = 196
    for ang, ic, val in [
        (302, draw_icon_bell, SAMPLE['bell']),
        (58, draw_icon_sun, SAMPLE['sun']),
        (228, 'ic_steps', str(SAMPLE['steps'])),
        (180, 'ic_heart', str(SAMPLE['heart'])),
        (132, 'ic_battery', f"{SAMPLE['battery']}%"),
    ]:
        mx, my = polar(ang, orbit)
        draw_stacked_item(img, mx, my, ic, val, icon_size=20, text_size=28, dy=13)
    # Subtle short progress underlines for steps and battery
    d = ImageDraw.Draw(img)
    for ang, frac in ((228, SAMPLE['steps'] / SAMPLE['goal']), (132, SAMPLE['battery'] / 100)):
        mx, my = polar(ang, orbit)
        y0 = (my + 29) * K
        w = 36 * K
        d.line([mx * K - w / 2, y0, mx * K + w / 2, y0], fill=TRACK + (255,), width=round(3 * K))
        d.line([mx * K - w / 2, y0, mx * K - w / 2 + w * frac, y0], fill=ACCENT + (255,), width=round(3 * K))
    return finalize(img)


def v2_arco_basso():
    """Leave upper sky and both sides 100% open; 3 core metrics sit quietly in the lower arc."""
    img = Image.new('RGBA', (N, N), (0, 0, 0, 255))
    paint_sky_and_corona(img, 132)
    paint_time(img)
    d = ImageDraw.Draw(img)
    # Outer edge progress gauges on the lower flanks (sides above 9/3 stay totally free)
    r_arc = 225
    # Left lower gauge: 258 -> 202 (56 deg span)
    draw_arc(d, C, C, r_arc, 202, 258, TRACK, 3.8)
    s_end = 258 - 56 * (SAMPLE['steps'] / SAMPLE['goal'])
    draw_arc(d, C, C, r_arc, s_end, 258, ACCENT, 3.8)
    # Right lower gauge: 102 -> 158 (56 deg span)
    draw_arc(d, C, C, r_arc, 102, 158, TRACK, 3.8)
    b_end = 102 + 56 * (SAMPLE['battery'] / 100)
    draw_arc(d, C, C, r_arc, 102, b_end, ACCENT, 3.8)

    # Three clean floating metrics clustered along the lower arc (r = 188)
    for ang, r_pos, ic, val in [
        (220, 188, 'ic_steps', str(SAMPLE['steps'])),
        (180, 190, 'ic_heart', str(SAMPLE['heart'])),
        (140, 188, 'ic_battery', f"{SAMPLE['battery']}%"),
    ]:
        mx, my = polar(ang, r_pos)
        draw_inline_item(img, mx, my, ic, val, icon_size=18, text_size=26, gap=5)
    return finalize(img)


def v3_nel_disco():
    """Pure eclipse outside: larger lunar disc (R=152) holds time + 3 core metrics inside."""
    img = Image.new('RGBA', (N, N), (0, 0, 0, 255))
    paint_sky_and_corona(img, 150)
    # Time + date slightly scaled to give room at bottom of disc for 3 compact stats
    paint_time(img, time_size=116, day_size=28, date_size=27, cy_time=222, cy_day=153, cy_date=292,
               col_step=47, gap_half=33)
    # Subtle divider line inside disc
    d = ImageDraw.Draw(img)
    d.line([(C - 72) * K, 314 * K, (C + 72) * K, 314 * K], fill=TRACK + (255,), width=max(1, round(1.2 * K)))
    # Three inline metrics tucked neatly inside the lower lunar disc
    draw_inline_item(img, C - 62, 338, 'ic_steps', str(SAMPLE['steps']), icon_size=15, text_size=23, gap=4)
    draw_inline_item(img, C, 344, 'ic_heart', str(SAMPLE['heart']), icon_size=15, text_size=23, gap=4)
    draw_inline_item(img, C + 62, 338, 'ic_battery', f"{SAMPLE['battery']}%", icon_size=15, text_size=23, gap=4)
    return finalize(img)


def v4_perimetro():
    """Keep all 5 data points, push them to the extreme rim with thin arcs and zero black moons."""
    img = Image.new('RGBA', (N, N), (0, 0, 0, 255))
    paint_sky_and_corona(img, 132)
    paint_time(img)
    d = ImageDraw.Draw(img)

    # Outer rim gauges for steps (bottom-left) and battery (bottom-right)
    r_arc = 226
    draw_arc(d, C, C, r_arc, 198, 246, TRACK, 3.5)
    draw_arc(d, C, C, r_arc, 246 - 48 * (SAMPLE['steps'] / SAMPLE['goal']), 246, ACCENT, 3.5)
    draw_arc(d, C, C, r_arc, 114, 162, TRACK, 3.5)
    draw_arc(d, C, C, r_arc, 114, 114 + 48 * (SAMPLE['battery'] / 100), ACCENT, 3.5)

    # Compact floating inline readouts near the rim (leaving 9 and 3 o'clock wide open!)
    for ang, rad, ic, val in [
        (312, 198, draw_icon_bell, SAMPLE['bell']),
        (48, 198, draw_icon_sun, SAMPLE['sun']),
        (222, 194, 'ic_steps', str(SAMPLE['steps'])),
        (180, 198, 'ic_heart', str(SAMPLE['heart'])),
        (138, 194, 'ic_battery', f"{SAMPLE['battery']}%"),
    ]:
        mx, my = polar(ang, rad)
        draw_inline_item(img, mx, my, ic, val, icon_size=17, text_size=25, gap=5)
    return finalize(img)


VARIANTS = [
    ('1', 'FANTASMA (5 dati)', 'Via i cerchi neri e i bordi: restano solo icone e cifre sul cielo', v1_fantasma),
    ('2', 'ARCO BASSO (3 dati)', 'Lati e corona 100% liberi; archi sottili in basso per passi e batteria', v2_arco_basso),
    ('3', 'TUTTO NEL DISCO', 'Esterno solo eclissi pura e stelle; 3 dati dentro il disco nero', v3_nel_disco),
    ('4', 'PERIMETRO (5 dati)', 'Ore 9 e 3 libere, tutti i 5 dati compatti verso il bordo', v4_perimetro),
]


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    pad, cap = 30, 86
    sheet = Image.new('RGB', (2 * S + 3 * pad, 2 * (S + cap) + 2 * pad), (24, 25, 29))
    title_f = ImageFont.truetype(str(VAR), 36)
    sub_f = ImageFont.truetype(str(VAR), 24)
    title_f.set_variation_by_axes([600])
    sub_f.set_variation_by_axes([400])

    for i, (num, name, line, fn) in enumerate(VARIANTS):
        img = fn()
        flat = Image.new('RGB', (S, S), (0, 0, 0))
        flat.paste(img, (0, 0), img)
        flat.save(OUT / f'eclisse-v{num}.png')

        x = pad + (i % 2) * (S + pad)
        y = pad + (i // 2) * (S + cap + pad // 2)
        sheet.paste(img, (x, y), img)
        d = ImageDraw.Draw(sheet)
        d.text((x + S / 2, y + S + 36), f'{num} · {name}', font=title_f, fill=(255, 255, 255), anchor='ms')
        d.text((x + S / 2, y + S + 68), line, font=sub_f, fill=(182, 186, 198), anchor='ms')

    out_path = OUT / 'confronto-eclisse.png'
    sheet.save(out_path)
    print('Saved:', out_path)
