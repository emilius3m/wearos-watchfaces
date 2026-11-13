"""Four 3D Tunnel watch face concepts (WFF-2 reproducible with layered <Gyro> depth).

Design studies only: rendered at 2x supersampling into 480x480 previews + comparison sheet.
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from mockups import Canvas, mix, polar, V, S, C, K, N, WHITE, BLACK, OUT, VAR

INK = (244, 238, 224)


def draw_oct_ring(d, cx, cy, r, rot_deg, outline, width, fill=None):
    pts = []
    for i in range(8):
        a = math.radians(rot_deg + i * 45)
        pts.append((cx + r * math.sin(a), cy - r * math.cos(a)))
    if fill:
        d.poly(pts, fill=fill)
    d.line(pts + [pts[0]], fill=outline, width=width, cap=True)
    return pts


def draw_hud_bottom(c, accent, sec_col):
    """Minimal floating HUD along bottom outer rim: heart, steps, battery, weather."""
    def paint(d):
        # Compact bottom arc bar
        d.rect(128, 376, 352, 412, 16, fill=(10, 12, 18, 215), outline=(54, 64, 84, 220), width=1.2)
        d.text(172, 394, V['hr'], 22, 600, WHITE)
        d.text(242, 394, V['steps'], 22, 600, WHITE)
        d.text(314, 394, f"{V['batt']}%", 22, 600, accent)

    c.paint(paint)
    c.icon('heart', 148, 394, 15, (255, 92, 108))
    c.icon('steps', 208, 394, 15, (74, 214, 158))
    c.icon('battery', 284, 394, 15, accent)


# ---------------------------------------------------------------------------
# T1 · TUNNEL WARP: nested chamfered portals receding with parallax ribs
# ---------------------------------------------------------------------------
def t1_warp():
    c = Canvas()
    cyan = (88, 224, 255)
    deep = (12, 36, 62)

    # 8 receding octagonal portals; deeper ones shift slightly (+14, -10) to show live 3D gyro parallax
    radii = [232, 198, 168, 141, 118, 97, 79, 63]
    shifts = [(i / 7) ** 1.25 for i in range(len(radii))]
    dx_max, dy_max = 16, -11

    def tunnel_glow(d):
        prev_pts = None
        for idx, (r, s) in enumerate(zip(radii, shifts)):
            t = 1 - idx / (len(radii) - 1)
            cx, cy = C + dx_max * s, C + dy_max * s
            col = mix(deep, cyan, 0.20 + 0.80 * (t ** 1.4))
            pts = draw_oct_ring(d, cx, cy, r, 22.5, col, 1.3 + 1.4 * t)
            if prev_pts is not None:
                for p0, p1 in zip(prev_pts, pts):
                    d.line([p0, p1], fill=mix(deep, cyan, 0.14 + 0.55 * (t ** 1.5)), width=1.1, cap=False)
            prev_pts = pts

    c.glow(tunnel_glow, blur=4.5)

    def fg(d):
        # Dark readable aperture behind time
        d.circle(C, C - 6, 86, fill=(4, 6, 12, 215))
        # Seconds sweep on outer ring
        d.arc(C, C, 234, 0, V['sec'] * 6, cyan, 3.2)
        px, py = polar(V['sec'] * 6, 234)
        d.circle(px, py, 5.0, fill=WHITE, outline=cyan, width=1.5)
        # Time & Date
        d.text(C, 162, f"{V['dow']} · {V['date']}", 22, 600, cyan, spacing=0.06)
        d.text(C - 10, 224, V['hh'], 114, 700, WHITE, 'r')
        d.text(C + 10, 224, V['mm'], 114, 700, cyan, 'l')
        for dy in (-14, 14):
            d.circle(C, 224 + dy, 4.2, fill=WHITE)
        # Subtle top weather pill
        d.rect(198, 46, 282, 76, 14, fill=(10, 14, 22, 215), outline=(64, 96, 124, 210), width=1.1)
        d.text(252, 61, '14°', 22, 600, WHITE)

    c.paint(fg)
    c.icon('sun', 220, 61, 16, (255, 200, 72))
    draw_hud_bottom(c, cyan, cyan)
    return c.finish()


# ---------------------------------------------------------------------------
# T2 · TRON / WIREFRAME: crisp laser corridor with perspective grid
# ---------------------------------------------------------------------------
def t2_tron():
    c = Canvas()
    laser = (0, 240, 255)
    magenta = (255, 76, 138)

    # Perspective ring radii: dense near center, wide at edges (1 / z)
    zs = np.linspace(1.0, 4.6, 10)
    radii = [234 / z for z in zs]
    vanish_x, vanish_y = C - 18, C - 14

    def grid(d):
        # 16 perspective radial rays from outer bezel into the vanishing pit
        for i in range(16):
            a = math.radians(i * 22.5 + 11.25)
            x1, y1 = C + 236 * math.sin(a), C - 236 * math.cos(a)
            x0 = vanish_x + 36 * math.sin(a)
            y0 = vanish_y - 36 * math.cos(a)
            col = mix((16, 48, 66), laser, 0.72) if i % 2 == 0 else mix((14, 34, 52), laser, 0.40)
            d.line([(x0, y0), (x1, y1)], fill=col, width=1.2, cap=False)

        # Receding depth circles with gyro parallax shift
        for idx, (z, r) in enumerate(zip(zs, radii)):
            t = 1 - idx / (len(zs) - 1)
            f = (z - 1.0) / (4.6 - 1.0)
            cx = C + (vanish_x - C) * f
            cy = C + (vanish_y - C) * f
            col = mix((14, 46, 70), laser, 0.22 + 0.78 * (t ** 1.3))
            d.circle(cx, cy, r, outline=col, width=1.1 + 1.4 * t)

    c.glow(grid, blur=3.5)

    def fg(d):
        # Crisp dark HUD backdrop for time
        d.rect(92, 162, 388, 294, 24, fill=(4, 8, 14, 215), outline=laser + (180,), width=1.3)
        d.text(C, 184, f"{V['dowf']} · {V['date']}", 22, 600, magenta, spacing=0.07)
        d.text(C - 12, 242, V['hh'], 116, 700, WHITE, 'r')
        d.text(C + 12, 242, V['mm'], 116, 700, laser, 'l')
        for dy in (-14, 14):
            d.rect(C - 4, 242 + dy - 4, C + 4, 242 + dy + 4, 2, fill=magenta)
        # Outer seconds rail
        d.arc(C, C, 234, 0, V['sec'] * 6, magenta, 3.4)
        px, py = polar(V['sec'] * 6, 234)
        d.circle(px, py, 5.2, fill=WHITE, outline=magenta, width=1.5)

    c.paint(fg)
    draw_hud_bottom(c, laser, magenta)
    return c.finish()


# ---------------------------------------------------------------------------
# T3 · DIAFRAMMA 3D: stepped mechanical camera iris blades forming a deep lens well
# ---------------------------------------------------------------------------
def t3_diaframma():
    c = Canvas()
    amber = (255, 194, 72)

    # 3 stepped iris tiers (outer -> mid -> inner), each with 10 overlapping metallic blades
    tiers = [
        (238, 174, 0, (44, 48, 58), (88, 94, 112), (0, 0)),
        (182, 134, 18, (30, 33, 41), (70, 76, 92), (5, -4)),
        (140, 104, 36, (18, 20, 26), (54, 59, 72), (10, -7)),
    ]

    for r_out, r_in, rot_off, body_col, edge_col, (ox, oy) in tiers:
        # Soft drop shadow under each iris tier onto the deeper tier
        def tier_shadow(d, r_in=r_in, ox=ox, oy=oy):
            draw_oct_ring(d, C + ox, C + oy, r_in + 10, rot_off, (0, 0, 0, 200), 14)

        c.paint(tier_shadow, blur=6)

        def paint_tier(d, r_out=r_out, r_in=r_in, rot_off=rot_off, body_col=body_col, edge_col=edge_col, ox=ox, oy=oy):
            n_blades = 10
            for i in range(n_blades):
                a0 = math.radians(rot_off + i * 360 / n_blades)
                a1 = math.radians(rot_off + (i + 1) * 360 / n_blades)
                a2 = math.radians(rot_off + (i + 1.55) * 360 / n_blades)
                p_in0 = (C + ox + r_in * math.sin(a0), C + oy - r_in * math.cos(a0))
                p_in1 = (C + ox + r_in * math.sin(a1), C + oy - r_in * math.cos(a1))
                p_out1 = (C + ox + r_out * math.sin(a2), C + oy - r_out * math.cos(a2))
                p_out0 = (C + ox + r_out * math.sin(a0 - 0.15), C + oy - r_out * math.cos(a0 - 0.15))
                shade = mix(body_col, (14, 16, 20), (i % 2) * 0.25)
                d.poly([p_in0, p_in1, p_out1, p_out0], fill=shade)
                # Catchlight edge along each overlapping blade lip
                d.line([p_in0, p_in1, p_out1], fill=edge_col, width=1.4, cap=True)

        c.paint(paint_tier)

    def center_well(d):
        # Deep black center lens pit
        d.circle(C + 10, C - 7, 102, fill=BLACK, outline=(62, 68, 84), width=1.4)
        # Bezel seconds ticks + marker
        for i in range(60):
            a = i * 6
            x0, y0 = polar(a, 226 if i % 5 == 0 else 230)
            x1, y1 = polar(a, 235)
            d.line([(x0, y0), (x1, y1)], fill=amber if a <= V['sec'] * 6 else (68, 74, 90),
                   width=2.2 if i % 5 == 0 else 1.2, cap=False)
        px, py = polar(V['sec'] * 6, 232)
        d.circle(px, py, 4.8, fill=amber, outline=BLACK, width=1.2)

        # Time & date crisp inside the central aperture
        d.text(C + 6, 174, f"{V['dow']} {V['date']}", 22, 600, amber, spacing=0.05)
        d.text(C + 6 - 9, 230, V['hh'], 102, 700, INK, 'r')
        d.text(C + 6 + 9, 230, V['mm'], 102, 700, amber, 'l')
        for dy in (-13, 13):
            d.circle(C + 6, 230 + dy, 3.8, fill=INK)

    c.paint(center_well)
    draw_hud_bottom(c, amber, amber)
    return c.finish()


# ---------------------------------------------------------------------------
# T4 · SPIRALE ABISSO: twisted segmented 3D vortex blades + seconds wave
# ---------------------------------------------------------------------------
def t4_spirale():
    c = Canvas()
    gold = (255, 194, 96)
    coral = (255, 98, 86)

    # 9 receding segmented rings, each twisted +15 deg and shifted for 3D depth
    radii = [232, 204, 178, 155, 134, 115, 98, 82, 68]

    def vortex(d):
        for idx, r in enumerate(radii):
            t = 1 - idx / (len(radii) - 1)
            s = (idx / (len(radii) - 1)) ** 1.2
            cx, cy = C + 14 * s, C - 10 * s
            base_col = mix((28, 14, 12), mix(coral, gold, t), 0.16 + 0.84 * (t ** 1.35))
            twist = idx * 14
            w = 3.6 * (0.45 + 0.55 * t)
            for k in range(6):
                a0 = twist + k * 60
                d.arc(cx, cy, r, a0, a0 + 36, base_col, w, cap=True)

    c.glow(vortex, blur=3.2)

    def fg(d):
        d.circle(C, C - 4, 88, fill=(4, 4, 6, 225), outline=(92, 62, 42, 160), width=1.1)
        d.arc(C, C, 235, 0, V['sec'] * 6, gold, 3.0)
        px, py = polar(V['sec'] * 6, 235)
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
    ('T1', 'TUNNEL WARP', '8 portali prospettici + costole a fuga, parallasse 3D con il polso', t1_warp),
    ('T2', 'TRON WIREFRAME', 'Corridoio laser anni 80 su nero OLED, punto di fuga reattivo', t2_tron),
    ('T3', 'DIAFRAMMA 3D', '3 livelli di lame meccaniche con ombre reali fino al pozzo centrale', t3_diaframma),
    ('T4', 'SPIRALE ABISSO', '9 anelli a elica sfasati in profondità, vortice caldo con secondi', t4_spirale),
]


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    pad, cap = 30, 86
    sheet = Image.new('RGB', (2 * S + 3 * pad, 2 * (S + cap) + 2 * pad), (24, 25, 29))
    title_f = ImageFont.truetype(str(VAR), 36)
    sub_f = ImageFont.truetype(str(VAR), 24)
    title_f.set_variation_by_axes([600])
    sub_f.set_variation_by_axes([400])

    for i, (code, name, line, fn) in enumerate(VARIANTS):
        img = fn()
        flat = Image.new('RGB', (S, S), (0, 0, 0))
        flat.paste(img, (0, 0), img)
        flat.save(OUT / f'{code}-{name.lower().replace(" ", "-")}.png')

        x = pad + (i % 2) * (S + pad)
        y = pad + (i // 2) * (S + cap + pad // 2)
        sheet.paste(img, (x, y), img)
        d = ImageDraw.Draw(sheet)
        d.text((x + S / 2, y + S + 36), f'{code} · {name}', font=title_f, fill=(255, 255, 255), anchor='ms')
        d.text((x + S / 2, y + S + 68), line, font=sub_f, fill=(182, 186, 198), anchor='ms')

    out_path = OUT / 'confronto-tunnel.png'
    sheet.save(out_path)
    print('Saved:', out_path)
