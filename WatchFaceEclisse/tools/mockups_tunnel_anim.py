"""Animated 3D Tunnel mockup previews (18 frames @ 15 fps, seamless loop).

Produces individual GIFs (T1..T4) and a 2x2 animated comparison sheet (confronto-tunnel.gif).
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from mockups import Canvas, mix, polar, V, S, C, K, WHITE, BLACK, OUT, VAR
from mockups_tunnel import draw_oct_ring, draw_hud_bottom, INK

N_FRAMES = 18
DURATION_MS = 67  # ~15 fps


def anim_t1_warp(p, sec):
    c = Canvas()
    cyan = (88, 224, 255)
    deep = (10, 30, 54)
    # Subtle gyro figure-8 sway in preview to showcase 3D parallax
    ang = p * 2 * math.pi
    dx_max, dy_max = 12 * math.sin(ang), 9 * math.cos(ang)

    def tunnel_glow(d):
        prev_pts = None
        for i in range(9):
            z = i - p  # shrinks from 8 -> -1; at p=1 ring i == ring i-1 at p=0
            if z < -0.15:
                continue
            r = 236 * (0.85 ** z)
            t = max(0.0, min(1.0, 1.0 - z / 8.0))
            s = max(0.0, z / 8.0) ** 1.25
            cx, cy = C + dx_max * s, C + dy_max * s
            col = mix(deep, cyan, 0.16 + 0.84 * (t ** 1.45))
            pts = draw_oct_ring(d, cx, cy, r, 22.5, col, 1.2 + 1.5 * t)
            if prev_pts is not None:
                for p0, p1 in zip(prev_pts, pts):
                    d.line([p0, p1], fill=mix(deep, cyan, 0.12 + 0.55 * (t ** 1.5)), width=1.1, cap=False)
            prev_pts = pts

    c.glow(tunnel_glow, blur=4.0)

    def fg(d):
        d.circle(C, C - 6, 84, fill=(4, 6, 12, 220))
        d.arc(C, C, 234, 0, sec * 6, cyan, 3.2)
        px, py = polar(sec * 6, 234)
        d.circle(px, py, 5.0, fill=WHITE, outline=cyan, width=1.5)
        d.text(C, 162, f"{V['dow']} · {V['date']}", 22, 600, cyan, spacing=0.06)
        d.text(C - 10, 224, V['hh'], 114, 700, WHITE, 'r')
        d.text(C + 10, 224, V['mm'], 114, 700, cyan, 'l')
        for dy in (-14, 14):
            d.circle(C, 224 + dy, 4.2, fill=WHITE)
        d.rect(198, 46, 282, 76, 14, fill=(10, 14, 22, 215), outline=(64, 96, 124, 210), width=1.1)
        d.text(252, 61, '14°', 22, 600, WHITE)

    c.paint(fg)
    c.icon('sun', 220, 61, 16, (255, 200, 72))
    draw_hud_bottom(c, cyan, cyan)
    return c.finish()


def anim_t2_tron(p, sec):
    c = Canvas()
    laser = (0, 240, 255)
    magenta = (255, 76, 138)
    ang = p * 2 * math.pi
    vanish_x, vanish_y = C + 14 * math.sin(ang), C - 10 * math.cos(ang)

    def grid(d):
        for i in range(16):
            a = math.radians(i * 22.5 + 11.25)
            x1, y1 = C + 236 * math.sin(a), C - 236 * math.cos(a)
            x0, y0 = vanish_x + 34 * math.sin(a), vanish_y - 34 * math.cos(a)
            col = mix((16, 48, 66), laser, 0.72) if i % 2 == 0 else mix((14, 34, 52), laser, 0.40)
            d.line([(x0, y0), (x1, y1)], fill=col, width=1.2, cap=False)

        for i in range(11):
            z = 1.0 + (i - p) * 0.42
            if z < 0.88:
                continue
            r = 234 / z
            t = max(0.0, min(1.0, 1.0 - (z - 1.0) / 4.2))
            f = max(0.0, (z - 1.0) / 4.2)
            cx = C + (vanish_x - C) * f
            cy = C + (vanish_y - C) * f
            col = mix((12, 40, 62), laser, 0.18 + 0.82 * (t ** 1.35))
            d.circle(cx, cy, r, outline=col, width=1.0 + 1.5 * t)

    c.glow(grid, blur=3.2)

    def fg(d):
        d.rect(92, 162, 388, 294, 24, fill=(4, 8, 14, 215), outline=laser + (180,), width=1.3)
        d.text(C, 184, f"{V['dowf']} · {V['date']}", 22, 600, magenta, spacing=0.07)
        d.text(C - 12, 242, V['hh'], 116, 700, WHITE, 'r')
        d.text(C + 12, 242, V['mm'], 116, 700, laser, 'l')
        for dy in (-14, 14):
            d.rect(C - 4, 242 + dy - 4, C + 4, 242 + dy + 4, 2, fill=magenta)
        d.arc(C, C, 234, 0, sec * 6, magenta, 3.4)
        px, py = polar(sec * 6, 234)
        d.circle(px, py, 5.2, fill=WHITE, outline=magenta, width=1.5)

    c.paint(fg)
    draw_hud_bottom(c, laser, magenta)
    return c.finish()


def anim_t3_diaframma(p, sec):
    c = Canvas()
    amber = (255, 194, 72)
    ang = p * 2 * math.pi
    # Seamless 36-deg blade rotation + breathing aperture
    breath = 6 * math.sin(ang)
    sway_x, sway_y = 6 * math.sin(ang), -5 * math.cos(ang)

    tiers = [
        (228, 170 + breath * 0.4, p * 36.0, (44, 48, 58), (90, 96, 114), (0, 0)),
        (178, 130 + breath * 0.7, 18 - p * 36.0, (30, 33, 41), (72, 78, 94), (sway_x * 0.5, sway_y * 0.5)),
        (136, 98 + breath, 36 + p * 36.0, (18, 20, 26), (56, 62, 76), (sway_x, sway_y)),
    ]

    for r_out, r_in, rot_off, body_col, edge_col, (ox, oy) in tiers:
        def paint_tier(d, r_out=r_out, r_in=r_in, rot_off=rot_off, body_col=body_col, edge_col=edge_col, ox=ox, oy=oy):
            n_blades = 10
            for i in range(n_blades):
                a0 = math.radians(rot_off + i * 360 / n_blades)
                a1 = math.radians(rot_off + (i + 1) * 360 / n_blades)
                a2 = math.radians(rot_off + (i + 1.45) * 360 / n_blades)
                p_in0 = (C + ox + r_in * math.sin(a0), C + oy - r_in * math.cos(a0))
                p_in1 = (C + ox + r_in * math.sin(a1), C + oy - r_in * math.cos(a1))
                p_out1 = (C + ox + r_out * math.sin(a2), C + oy - r_out * math.cos(a2))
                p_out0 = (C + ox + r_out * math.sin(a0 - 0.12), C + oy - r_out * math.cos(a0 - 0.12))
                shade = mix(body_col, (14, 16, 20), (i % 2) * 0.25)
                d.poly([p_in0, p_in1, p_out1, p_out0], fill=shade)
                d.line([p_in0, p_in1, p_out1], fill=edge_col, width=1.4, cap=True)

        c.paint(paint_tier)

    def center_well(d):
        # Clean circular outer barrel frame clipping the blades neatly
        d.circle(C, C, 232, outline=(52, 58, 72), width=14)
        d.circle(C + sway_x, C + sway_y, 96 + breath, fill=BLACK, outline=(66, 72, 90), width=1.4)
        for i in range(60):
            a = i * 6
            x0, y0 = polar(a, 226 if i % 5 == 0 else 230)
            x1, y1 = polar(a, 235)
            d.line([(x0, y0), (x1, y1)], fill=amber if a <= sec * 6 else (68, 74, 90),
                   width=2.2 if i % 5 == 0 else 1.2, cap=False)
        px, py = polar(sec * 6, 232)
        d.circle(px, py, 4.8, fill=amber, outline=BLACK, width=1.2)
        d.text(C, 174, f"{V['dow']} {V['date']}", 22, 600, amber, spacing=0.05)
        d.text(C - 9, 230, V['hh'], 102, 700, INK, 'r')
        d.text(C + 9, 230, V['mm'], 102, 700, amber, 'l')
        for dy in (-13, 13):
            d.circle(C, 230 + dy, 3.8, fill=INK)

    c.paint(center_well)
    draw_hud_bottom(c, amber, amber)
    return c.finish()


def anim_t4_spirale(p, sec):
    c = Canvas()
    gold = (255, 194, 96)
    coral = (255, 98, 86)
    ang = p * 2 * math.pi
    dx_max, dy_max = 10 * math.sin(ang), -8 * math.cos(ang)

    def vortex(d):
        for i in range(10):
            z = i - p
            if z < -0.2:
                continue
            r = 232 * (0.865 ** z)
            t = max(0.0, min(1.0, 1.0 - z / 9.0))
            s = max(0.0, z / 9.0) ** 1.2
            cx, cy = C + dx_max * s, C + dy_max * s
            base_col = mix((28, 14, 12), mix(coral, gold, t), 0.14 + 0.86 * (t ** 1.35))
            twist = z * 14
            w = 3.6 * (0.45 + 0.55 * t)
            for k in range(6):
                a0 = twist + k * 60
                d.arc(cx, cy, r, a0, a0 + 36, base_col, w, cap=True)

    c.glow(vortex, blur=3.0)

    def fg(d):
        d.circle(C, C - 4, 86, fill=(4, 4, 6, 225), outline=(92, 62, 42, 160), width=1.1)
        d.arc(C, C, 235, 0, sec * 6, gold, 3.0)
        px, py = polar(sec * 6, 235)
        d.circle(px, py, 4.8, fill=WHITE, outline=gold, width=1.4)
        d.text(C, 166, f"{V['dow']} · {V['date']}", 22, 600, gold, spacing=0.06)
        d.text(C - 10, 226, V['hh'], 112, 700, INK, 'r')
        d.text(C + 10, 226, V['mm'], 112, 700, coral, 'l')
        for dy in (-14, 14):
            d.circle(C, 226 + dy, 4.0, fill=gold)

    c.paint(fg)
    draw_hud_bottom(c, gold, gold)
    return c.finish()


VARIANTS = [
    ('T1', 'TUNNEL WARP', anim_t1_warp),
    ('T2', 'TRON WIREFRAME', anim_t2_tron),
    ('T3', 'DIAFRAMMA 3D', anim_t3_diaframma),
    ('T4', 'SPIRALE ABISSO', anim_t4_spirale),
]


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    pad, cap = 24, 64
    W_SHEET = 2 * S + 3 * pad
    H_SHEET = 2 * (S + cap) + 2 * pad
    title_f = ImageFont.truetype(str(VAR), 34)
    title_f.set_variation_by_axes([600])

    # Pre-build static sheet background + labels
    base_sheet = Image.new('RGB', (W_SHEET, H_SHEET), (24, 25, 29))
    bd = ImageDraw.Draw(base_sheet)
    for i, (code, name, _) in enumerate(VARIANTS):
        x = pad + (i % 2) * (S + pad)
        y = pad + (i // 2) * (S + cap + pad // 2)
        bd.text((x + S / 2, y + S + 38), f'{code} · {name}', font=title_f, fill=(255, 255, 255), anchor='ms')

    per_variant_frames = {code: [] for code, _, _ in VARIANTS}
    sheet_frames = []

    for fi in range(N_FRAMES):
        p = fi / N_FRAMES
        sec = V['sec'] + p
        frame_sheet = base_sheet.copy()
        for i, (code, _, fn) in enumerate(VARIANTS):
            im = fn(p, sec)
            flat = Image.new('RGB', (S, S), (0, 0, 0))
            flat.paste(im, (0, 0), im)
            per_variant_frames[code].append(flat.convert('P', palette=Image.ADAPTIVE, colors=128))
            x = pad + (i % 2) * (S + pad)
            y = pad + (i // 2) * (S + cap + pad // 2)
            frame_sheet.paste(im, (x, y), im)
        sheet_frames.append(frame_sheet.convert('P', palette=Image.ADAPTIVE, colors=160))

    for code, name, _ in VARIANTS:
        gif_path = OUT / f'{code}-{name.lower().replace(" ", "-")}.gif'
        frames = per_variant_frames[code]
        frames[0].save(gif_path, save_all=True, append_images=frames[1:], duration=DURATION_MS, loop=0, optimize=True)
        print('Saved:', gif_path)

    sheet_gif = OUT / 'confronto-tunnel.gif'
    sheet_frames[0].save(sheet_gif, save_all=True, append_images=sheet_frames[1:], duration=DURATION_MS, loop=0, optimize=True)
    print('Saved:', sheet_gif)
