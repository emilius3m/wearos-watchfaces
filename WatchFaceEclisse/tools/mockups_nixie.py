"""M3 Nixie Tube deep-dive: 4 variations + animated GIF preview.

Design studies only — generated under WatchFaceEclisse/design/mockups/.
"""
from pathlib import Path
import math
import sys
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mockups import Canvas, Draw, GLYPHS, mix, polar, S, N, C, V, WHITE, BLACK, OUT, VAR


PALETTES = {
    'amber': dict(
        bg=(13, 10, 9),
        glass=(18, 13, 11),
        rim=(74, 62, 54),
        mesh_h=(38, 28, 24),
        mesh_v=(34, 25, 21),
        ghost=(46, 29, 21),
        neon=(255, 114, 26),
        core=(255, 228, 168),
        label=(218, 174, 126),
        brass=(134, 100, 62),
        plaque=(22, 18, 15),
        socket=(46, 35, 29),
    ),
    'vfd': dict(
        bg=(8, 13, 14),
        glass=(11, 18, 19),
        rim=(46, 74, 72),
        mesh_h=(22, 38, 36),
        mesh_v=(20, 34, 32),
        ghost=(24, 46, 44),
        neon=(38, 232, 184),
        core=(204, 255, 238),
        label=(154, 218, 202),
        brass=(64, 106, 98),
        plaque=(13, 21, 22),
        socket=(26, 40, 42),
    ),
}


def draw_nixie_tube(d, x0, y0, x1, y1, ch, pal, font_size, radius=22,
                    ghost_chars=('3', '8'), show_socket=True):
    """Draw tube enclosure, anode mesh, stacked ghost cathodes, and socket."""
    d.rect(x0, y0, x1, y1, radius, fill=pal['glass'], outline=pal['rim'], width=1.6)
    step = max(10, round((y1 - y0) / 9))
    for gy in range(round(y0 + step), round(y1 - 10), step):
        d.line([(x0 + 8, gy), (x1 - 8, gy)], fill=pal['mesh_h'], width=0.85, cap=False)
    for gx in range(round(x0 + 13), round(x1 - 8), 13):
        d.line([(gx, y0 + 12), (gx, y1 - 12)], fill=pal['mesh_v'], width=0.85, cap=False)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    for i, gch in enumerate(ghost_chars):
        if gch != ch:
            ox = (-1.5 if i == 0 else 1.5)
            d.text(cx + ox, cy, gch, font_size, 500, pal['ghost'])
    if show_socket:
        d.rect(x0 + 6, y1 - 13, x1 - 6, y1 + 4, 5, fill=pal['socket'], outline=pal['brass'], width=1.1)
        # Brass mounting pins on ceramic base
        for px in (x0 + 16, cx, x1 - 16):
            d.circle(px, y1 - 4, 2.0, fill=pal['brass'])


def draw_tube_sheen(d, x0, y0, x1, y1):
    """Specular highlight strip on left inner wall of glass envelope."""
    d.line([(x0 + 10, y0 + 16), (x0 + 10, y1 - 22)], fill=(255, 244, 228, 52), width=2.2)
    d.line([(x1 - 9, y0 + 22), (x1 - 9, y1 - 26)], fill=(255, 244, 228, 22), width=1.2)


def draw_colon(d, cx, cy, col, r=4.2, spread=17):
    for dy in (-spread, spread):
        d.circle(cx, cy + dy, r, fill=col)


def draw_brass_plaque(c, pal, x0, y0, x1, y1, sec_ratio=None, show_bar=True):
    """Draw dark brushed brass metrics plaque with heart, steps, battery."""
    def base(d):
        d.rect(x0, y0, x1, y1, 16, fill=pal['plaque'], outline=pal['brass'], width=1.5)
        y_mid = y0 + (30 if show_bar else (y1 - y0) / 2)
        d.text(x0 + 66, y_mid, V['hr'], 30, 600, pal['core'])
        d.text(x0 + 152, y_mid, V['steps'], 30, 600, pal['core'])
        d.text(x0 + 240, y_mid, f"{V['batt']}%", 30, 600, pal['neon'])
        if show_bar and sec_ratio is not None:
            bx0, bx1, by = x0 + 24, x1 - 24, y1 - 22
            d.rect(bx0, by, bx1, by + 6, 3, fill=pal['socket'])
            d.rect(bx0, by, bx0 + (bx1 - bx0) * max(0.02, sec_ratio), by + 6, 3, fill=pal['neon'])

    c.paint(base)
    y_ic = y0 + (30 if show_bar else (y1 - y0) / 2)
    c.icon('heart', x0 + 32, y_ic, 17, (255, 96, 86))
    c.icon('steps', x0 + 110, y_ic, 17, (124, 214, 150))
    c.icon('battery', x0 + 204, y_ic, 17, pal['neon'])


def draw_mic_glyph(d, cx, cy, size, col):
    """Draw clean microphone capsule icon without external font dependency."""
    s = size / 24.0
    d.rect(cx - 3.6 * s, cy - 9 * s, cx + 3.6 * s, cy + 1.5 * s, 3.6 * s, fill=col)
    d.arc(cx, cy - 2 * s, 6.8 * s, 95, 265, fill=col, width=1.8 * s)
    d.line([(cx, cy + 4.8 * s), (cx, cy + 9.2 * s)], fill=col, width=1.8 * s)
    d.line([(cx - 4.2 * s, cy + 9.2 * s), (cx + 4.2 * s, cy + 9.2 * s)], fill=col, width=1.8 * s)


def render_nixie_classic():
    """N1: Classic IN-18 Nixie watch face with stacked cathodes & brass plaque."""
    pal = PALETTES['amber']
    c = Canvas(Image.new('RGBA', (N, N), pal['bg'] + (255,)))
    tubes = [
        (56, 130, 142, 262, V['hh'][0]),
        (146, 130, 232, 262, V['hh'][1]),
        (248, 130, 334, 262, V['mm'][0]),
        (338, 130, 424, 262, V['mm'][1]),
    ]

    def backs(d):
        d.circle(C, C, 232, outline=(56, 44, 34), width=3.5)
        d.circle(C, C, 224, outline=(36, 28, 22), width=1.0)
        d.text(C, 86, f"{V['dowf']} · {V['date']}", 26, 600, pal['label'], spacing=0.06)
        for x0, y0, x1, y1, ch in tubes:
            draw_nixie_tube(d, x0, y0, x1, y1, ch, pal, 110)

    c.paint(backs)

    def glow_layer(d, col):
        for x0, y0, x1, y1, ch in tubes:
            d.text((x0 + x1) / 2, (y0 + y1) / 2, ch, 110, 500, col)
        draw_colon(d, C, 196, col, r=4.2)

    c.paint(lambda d: glow_layer(d, pal['neon']), blur=8, repeat=2)
    c.paint(lambda d: glow_layer(d, pal['core']))

    c.paint(lambda d: [draw_tube_sheen(d, x0, y0, x1, y1) for x0, y0, x1, y1, _ in tubes])
    draw_brass_plaque(c, pal, 96, 290, 384, 378, sec_ratio=V['sec'] / 60, show_bar=True)
    c.paint(lambda d: d.text(C, 405, f"{V['sec']:02d} SEC", 22, 600, pal['label'], spacing=0.08))
    return c.finish()


def render_nixie_crown(pal_key='amber', hh='09', mm='27', sec=36,
                       fade_digit=None, colon_dim=1.0):
    """N2/N4: Round 60-pip neon crown + top weather/date + bottom notifications/REC.

    Supports animated frame generation via (hh, mm, sec, fade_digit, colon_dim).
    fade_digit: optional tuple (tube_index, old_char, old_alpha, new_alpha)
    """
    pal = PALETTES[pal_key]
    c = Canvas(Image.new('RGBA', (N, N), pal['bg'] + (255,)))
    tubes = [
        (60, 126, 144, 254, hh[0]),
        (146, 126, 230, 254, hh[1]),
        (250, 126, 334, 254, mm[0]),
        (336, 126, 420, 254, mm[1]),
    ]

    def crown_and_backs(d):
        # Outer dial bezel + 60 tiny neon indicator pips
        d.circle(C, C, 224, outline=pal['rim'], width=1.2)
        for m in range(60):
            ang = m * 6
            r = 231
            px, py = polar(ang, r)
            diff = (sec - m) % 60
            is_maj = (m % 5 == 0)
            if diff == 0:
                d.circle(px, py, 4.4, fill=pal['core'])
            elif diff <= 3:
                fade = 1.0 - diff * 0.25
                d.circle(px, py, 2.8, fill=mix(pal['glass'], pal['neon'], fade))
            elif m <= sec:
                d.circle(px, py, 2.2 if is_maj else 1.5, fill=mix(pal['glass'], pal['neon'], 0.34 if is_maj else 0.18))
            else:
                d.circle(px, py, 2.0 if is_maj else 1.3, fill=pal['rim'] if is_maj else pal['mesh_h'])

        # Top header: date + weather temperature chip
        d.text(196, 86, f"{V['dow']} {V['date']}", 25, 600, pal['label'], 'm', spacing=0.05)
        d.rect(282, 70, 354, 102, 16, fill=pal['plaque'], outline=pal['brass'], width=1.2)
        d.text(328, 86, "14°", 24, 600, pal['core'], 'm')

        for x0, y0, x1, y1, ch in tubes:
            draw_nixie_tube(d, x0, y0, x1, y1, ch, pal, 106)

    c.paint(crown_and_backs)
    c.icon('sun', 300, 86, 16, pal['neon'])

    # Glow around active second pip
    def sec_pip_glow(d):
        px, py = polar(sec * 6, 231)
        d.circle(px, py, 5.2, fill=pal['neon'])

    c.paint(sec_pip_glow, blur=5, repeat=1)

    # Tube filaments (with optional smooth digit transition for animation frames)
    def paint_digits(d, base_col, is_core=False):
        for idx, (x0, y0, x1, y1, ch) in enumerate(tubes):
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            if fade_digit and fade_digit[0] == idx:
                _, old_ch, old_a, new_a = fade_digit
                if old_a > 0.02:
                    c_old = (*base_col[:3], round(255 * old_a))
                    d.text(cx, cy, old_ch, 106, 500, c_old)
                if new_a > 0.02:
                    c_new = (*base_col[:3], round(255 * new_a))
                    d.text(cx, cy, ch, 106, 500, c_new)
            else:
                d.text(cx, cy, ch, 106, 500, base_col)
        colon_col = mix(pal['glass'], base_col, colon_dim)
        draw_colon(d, C, 190, colon_col, r=3.8 if is_core else 4.2)

    c.paint(lambda d: paint_digits(d, pal['neon'], False), blur=7.5, repeat=2)
    c.paint(lambda d: paint_digits(d, pal['core'], True))

    c.paint(lambda d: [draw_tube_sheen(d, x0, y0, x1, y1) for x0, y0, x1, y1, _ in tubes])

    # Brass metrics plaque (middle-lower) + bottom interactive row (Notifications + REC)
    draw_brass_plaque(c, pal, 96, 280, 384, 344, sec_ratio=sec / 60, show_bar=False)

    def bottom_row(d):
        # Notifications complication slot (left pill)
        d.rect(128, 360, 266, 404, 18, fill=pal['plaque'], outline=pal['brass'], width=1.4)
        d.text(210, 382, "2 NOTIFICHE", 22, 600, pal['label'])
        # Quick Voice Recorder button (right pill)
        d.rect(282, 360, 352, 404, 18, fill=pal['plaque'], outline=pal['brass'], width=1.4)
        draw_mic_glyph(d, 317, 382, 20, pal['neon'])

    c.paint(bottom_row)
    c.icon('bell', 150, 382, 16, pal['neon'])
    return c.finish()


def render_nixie_six_tubes():
    """N3: 6-Tube bench deck (HH:MM big + SS Nixie tubes on lower chassis)."""
    pal = PALETTES['amber']
    c = Canvas(Image.new('RGBA', (N, N), pal['bg'] + (255,)))
    big_tubes = [
        (60, 118, 144, 240, V['hh'][0]),
        (146, 118, 230, 240, V['hh'][1]),
        (250, 118, 334, 240, V['mm'][0]),
        (336, 118, 420, 240, V['mm'][1]),
    ]
    sec_str = f"{V['sec']:02d}"
    sec_tubes = [
        (288, 272, 346, 364, sec_str[0]),
        (350, 272, 408, 364, sec_str[1]),
    ]

    def backs(d):
        d.circle(C, C, 232, outline=pal['rim'], width=3.0)
        d.text(C, 78, f"{V['dowf']} · {V['date']}", 25, 600, pal['label'], spacing=0.06)
        for x0, y0, x1, y1, ch in big_tubes:
            draw_nixie_tube(d, x0, y0, x1, y1, ch, pal, 102)
        # Compact left brass plaque beside the 2 small seconds Nixie tubes
        d.rect(72, 272, 270, 364, 16, fill=pal['plaque'], outline=pal['brass'], width=1.4)
        d.text(140, 300, V['hr'], 28, 600, pal['core'])
        d.text(224, 300, f"{V['batt']}%", 28, 600, pal['neon'])
        d.text(172, 340, f"{V['steps']} PASSI", 24, 600, pal['label'])
        for x0, y0, x1, y1, ch in sec_tubes:
            draw_nixie_tube(d, x0, y0, x1, y1, ch, pal, 72, radius=16)

    c.paint(backs)

    def glow_digits(d, col):
        for x0, y0, x1, y1, ch in big_tubes:
            d.text((x0 + x1) / 2, (y0 + y1) / 2, ch, 102, 500, col)
        for x0, y0, x1, y1, ch in sec_tubes:
            d.text((x0 + x1) / 2, (y0 + y1) / 2, ch, 72, 500, col)
        draw_colon(d, C, 179, col, r=3.8, spread=15)

    c.paint(lambda d: glow_digits(d, pal['neon']), blur=7.5, repeat=2)
    c.paint(lambda d: glow_digits(d, pal['core']))
    c.paint(lambda d: [draw_tube_sheen(d, x0, y0, x1, y1) for x0, y0, x1, y1, _ in big_tubes + sec_tubes])
    c.icon('heart', 102, 300, 16, (255, 96, 86))
    c.icon('battery', 184, 300, 16, pal['neon'])
    c.icon('steps', 104, 340, 16, (124, 214, 150))
    c.paint(lambda d: d.text(C, 405, "IN-18 LAB · CHRONO", 18, 600, pal['brass'], spacing=0.14))
    return c.finish()


def build_animated_gif(out_path):
    """Build smooth 15fps animated GIF of N2: ticks 58 -> 59 -> 00 -> 01 with digit fade & ignition flicker."""
    frames = []
    # Timeline: 4 seconds at 15 fps = 60 frames
    # Beat 0: 09:27:58, Beat 1: 09:27:59, Beat 2: 09:28:00 (digit switch!), Beat 3: 09:28:01
    fps = 12
    total_frames = 4 * fps
    for fi in range(total_frames):
        sec_idx = fi // fps
        frac = (fi % fps) / fps
        if sec_idx == 0:
            hh, mm, sec = '09', '27', 58
            fade = None
        elif sec_idx == 1:
            hh, mm, sec = '09', '27', 59
            fade = None
        elif sec_idx == 2:
            hh, mm, sec = '09', '28', 0
            # Crossfade + slight warm gas ignition flicker during first 0.5s
            if frac < 0.55:
                t = frac / 0.55
                flicker = 0.82 if 0.18 < frac < 0.28 else 1.0
                fade = (3, '7', max(0.0, 1.0 - t * 1.4), min(1.0, t * 1.15) * flicker)
            else:
                fade = None
        else:
            hh, mm, sec = '09', '28', 1
            fade = None

        # 1Hz gentle neon colon pulse
        colon_dim = 0.48 + 0.52 * (0.5 + 0.5 * math.cos(2 * math.pi * frac))
        im = render_nixie_crown('amber', hh=hh, mm=mm, sec=sec,
                                fade_digit=fade, colon_dim=colon_dim)
        flat = Image.new('RGB', (S, S), (12, 10, 9))
        flat.paste(im, (0, 0), im)
        frames.append(flat.quantize(colors=128, method=Image.Quantize.FASTOCTREE))

    frames[0].save(
        out_path,
        save_all=True,
        append_images=frames[1:],
        duration=round(1000 / fps),
        loop=0,
        optimize=True,
    )


VARIANTS = [
    ('N1', 'CLASSICO IN-18', '4 valvole calde con catodi sovrapposti, base ceramica e placca', render_nixie_classic),
    ('N2', 'COMPLETO + CORONA', 'Corona 60 tacche neon, meteo in alto, notifiche + tasto REC', lambda: render_nixie_crown('amber')),
    ('N3', '6 TUBI HH:MM:SS', '4 tubi grandi + 2 tubi Nixie dedicati ai secondi su chassis', render_nixie_six_tubes),
    ('N4', 'VFD VERDE FOSFORO', 'Tema alternativo VFD anni 70 con corona neon e slot completi', lambda: render_nixie_crown('vfd')),
]


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    pad, cap = 30, 86
    sheet = Image.new('RGB', (2 * S + 3 * pad, 2 * (S + cap) + 2 * pad), (24, 25, 29))
    title = ImageFont.truetype(str(VAR), 40)
    sub = ImageFont.truetype(str(VAR), 24)
    title.set_variation_by_axes([600])
    sub.set_variation_by_axes([400])

    for i, (code, name, line, fn) in enumerate(VARIANTS):
        img = fn()
        flat = Image.new('RGB', (S, S), (0, 0, 0))
        flat.paste(img, (0, 0), img)
        fname = f"{code}-{name.lower().replace(' ', '-').replace('+', '').replace(':', '')}.png"
        flat.save(OUT / fname)
        x, y = pad + (i % 2) * (S + pad), pad + (i // 2) * (S + cap + pad // 2)
        sheet.paste(img, (x, y), img)
        d = ImageDraw.Draw(sheet)
        d.text((x + S / 2, y + S + 36), f'{code} · {name}', font=title, fill=(255, 255, 255), anchor='ms')
        d.text((x + S / 2, y + S + 68), line, font=sub, fill=(182, 186, 198), anchor='ms')

    sheet_path = OUT / 'confronto-nixie.png'
    sheet.save(sheet_path)
    gif_path = OUT / 'M3-nixie-anim.gif'
    build_animated_gif(gif_path)
    print('Saved:', sheet_path)
    print('Saved:', gif_path)
