"""Four physical / horological watch face mockups:
M1 · Skeleton Mechanical, M2 · Classic Diver Chrono, M3 · Nixie Tubes, M4 · Retro LCD.

Design studies only: rendered at 2x supersampling into 480x480 previews + comparison sheet.
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from mockups import Canvas, mix, polar, V, S, C, K, N, WHITE, BLACK, OUT, VAR, seven_text

HOUR_ANG = (9 + 27 / 60) * 30
MIN_ANG = (27 + V['sec'] / 60) * 6
SEC_ANG = V['sec'] * 6


def draw_gear(d, cx, cy, r_out, r_in, teeth, col, hole_r=0, spoke_n=5, rot=0):
    pts = []
    step = 360 / teeth
    for i in range(teeth):
        a0 = math.radians(rot + i * step)
        a1 = math.radians(rot + (i + 0.35) * step)
        a2 = math.radians(rot + (i + 0.55) * step)
        a3 = math.radians(rot + (i + 0.90) * step)
        pts.extend([
            (cx + r_in * math.sin(a0), cy - r_in * math.cos(a0)),
            (cx + r_out * math.sin(a1), cy - r_out * math.cos(a1)),
            (cx + r_out * math.sin(a2), cy - r_out * math.cos(a2)),
            (cx + r_in * math.sin(a3), cy - r_in * math.cos(a3)),
        ])
    d.poly(pts, fill=col)
    if hole_r > 0:
        d.circle(cx, cy, hole_r, fill=(10, 12, 16))
        d.circle(cx, cy, r_in * 0.82, outline=col, width=max(1.5, r_out * 0.12))
        for s in range(spoke_n):
            sa = math.radians(rot + s * 360 / spoke_n)
            d.line([(cx, cy), (cx + r_in * 0.8 * math.sin(sa), cy - r_in * 0.8 * math.cos(sa))],
                   fill=col, width=max(2.0, r_out * 0.09), cap=False)


def draw_bevel_hand(c, angle, length, tail, w_base, w_tip, fill_l, fill_r, lume_col=None):
    """Realistic 2-facet metallic watch hand with drop shadow."""
    a = math.radians(angle)
    dx, dy = math.sin(a), -math.cos(a)
    px, py = math.cos(a), math.sin(a)

    p_tip = (C + dx * length, C + dy * length)
    p_tail = (C - dx * tail, C - dy * tail)
    p_l = (C - px * w_base, C - py * w_base)
    p_r = (C + px * w_base, C + py * w_base)
    p_tl = (C + dx * (length * 0.78) - px * w_tip, C + dy * (length * 0.78) - py * w_tip)
    p_tr = (C + dx * (length * 0.78) + px * w_tip, C + dy * (length * 0.78) + py * w_tip)

    def shadow(d):
        sh = (4, 5)
        d.poly([(x + sh[0], y + sh[1]) for x, y in (p_tail, p_l, p_tl, p_tip, p_tr, p_r)], fill=(0, 0, 0, 165))

    def body(d):
        d.poly([p_tail, p_l, p_tl, p_tip], fill=fill_l)
        d.poly([p_tail, p_tip, p_tr, p_r], fill=fill_r)
        if lume_col:
            l0 = (C + dx * (length * 0.28), C + dy * (length * 0.28))
            l1 = (C + dx * (length * 0.76), C + dy * (length * 0.76))
            d.line([l0, l1], fill=lume_col, width=w_base * 0.75, cap=True)

    c.paint(shadow, blur=3.2)
    c.paint(body)


# ---------------------------------------------------------------------------
# M1 · MECCANICO SCHELETRATO
# ---------------------------------------------------------------------------
def m1_meccanico():
    c = Canvas(Image.new('RGBA', (N, N), (10, 11, 15, 255)))
    brass = (214, 170, 94)
    brass_dim = (146, 112, 58)
    steel = (176, 184, 198)
    steel_dk = (92, 98, 112)
    ruby = (218, 38, 72)

    # Exposed gears behind bridges
    def gears(d):
        draw_gear(d, 178, 170, 62, 53, 24, (78, 82, 94), hole_r=36, spoke_n=5, rot=12)
        draw_gear(d, 294, 192, 50, 42, 20, brass_dim, hole_r=28, spoke_n=5, rot=28)
        draw_gear(d, 240, 240, 44, 37, 18, (112, 118, 134), hole_r=22, spoke_n=6, rot=5)
        draw_gear(d, 162, 294, 46, 39, 20, (68, 72, 84), hole_r=26, spoke_n=4, rot=18)

    c.paint(gears)

    # Balance wheel at 6 o'clock
    def balance(d):
        bx, by = C, 336
        d.circle(bx, by, 54, fill=(8, 9, 12), outline=(48, 52, 62), width=2)
        draw_gear(d, bx, by, 44, 39, 28, brass, hole_r=32, spoke_n=3, rot=22)
        # Hair-spring spiral
        pts = []
        for k in range(80):
            t = k / 79
            a = t * 5.2 * math.pi
            rr = 4 + t * 18
            pts.append((bx + rr * math.sin(a), by - rr * math.cos(a)))
        d.line(pts, fill=(130, 165, 210), width=1.1, cap=False)
        d.circle(bx, by, 5.5, fill=ruby, outline=steel, width=1.2)

    c.paint(balance)

    # Skeleton bridges in dark brushed titanium with beveled edges + ruby jewels
    def bridges(d):
        # Upper Y-bridge & chapter ring
        d.circle(C, C, 224, outline=(36, 40, 48), width=28)
        d.circle(C, C, 209, outline=(96, 102, 118), width=1.5)
        y_pts = [(96, 150), (195, 195), (285, 195), (384, 150), (376, 128), (284, 174), (196, 174), (104, 128)]
        d.poly(y_pts, fill=(26, 29, 36))
        d.line(y_pts + [y_pts[0]], fill=(88, 94, 110), width=1.4, cap=True)
        # Balance bridge bar across 6 o'clock
        d.rect(178, 376, 302, 394, 9, fill=(32, 35, 44), outline=(96, 102, 118), width=1.3)
        # Jewel bearings & blued screws
        for jx, jy in ((178, 170), (294, 192), (240, 385)):
            d.circle(jx, jy, 5.2, fill=ruby, outline=brass, width=1.4)
        for sx, sy in ((118, 146), (362, 146), (190, 385), (290, 385)):
            d.circle(sx, sy, 4.0, fill=(64, 118, 210), outline=(140, 175, 230), width=0.9)

        # Hour indices on chapter ring
        for i in range(60):
            a = i * 6
            maj = (i % 5 == 0)
            x0, y0 = polar(a, 212 if maj else 218)
            x1, y1 = polar(a, 228)
            d.line([(x0, y0), (x1, y1)], fill=(235, 240, 226) if maj else (110, 116, 130),
                   width=3.2 if maj else 1.2, cap=False)

        # Date window at 3 o'clock + compact steps/batt arc readouts at 9 & 3
        d.rect(342, 224, 386, 256, 5, fill=(242, 238, 226), outline=brass, width=1.6)
        d.text(364, 240, '12', 24, 700, (16, 18, 22))
        d.text(132, 240, f"{V['batt']}%", 20, 600, brass)

    c.paint(bridges)
    draw_bevel_hand(c, HOUR_ANG, 128, 24, 9.5, 4.5, (236, 240, 248), (132, 140, 156), (222, 240, 196))
    draw_bevel_hand(c, MIN_ANG, 192, 28, 7.5, 3.0, (242, 246, 252), (144, 152, 168), (222, 240, 196))

    # Sweeping seconds hand
    def sec_hand(d):
        x1, y1 = polar(SEC_ANG, 206)
        x0, y0 = polar(SEC_ANG + 180, 44)
        d.line([(x0, y0), (x1, y1)], fill=(226, 62, 68), width=2.2)
        d.circle(C, C, 7.5, fill=steel, outline=brass, width=1.8)
        d.circle(C, C, 2.8, fill=(226, 62, 68))

    c.paint(sec_hand)
    return c.finish()


# ---------------------------------------------------------------------------
# M2 · DIVER / CRONOGRAFO CLASSICO
# ---------------------------------------------------------------------------
def m2_diver():
    # Deep matte navy-charcoal dial with ceramic bezel
    c = Canvas(Image.new('RGBA', (N, N), (8, 12, 18, 255)))
    lume = (238, 234, 212)
    steel = (218, 224, 234)
    steel_dk = (116, 124, 138)
    coral = (234, 82, 66)

    def dial(d):
        # Ceramic diver bezel ring (outer)
        d.circle(C, C, 238, fill=(18, 22, 30))
        d.circle(C, C, 196, fill=(10, 15, 24), outline=(56, 66, 84), width=1.6)
        # Bezel triangle at 12 + 10..50 numerals + minute ticks
        d.poly([(C - 8, 10), (C + 8, 10), (C, 28)], fill=lume)
        d.circle(C, 16, 2.8, fill=(255, 255, 255))
        for m in range(60):
            if m == 0:
                continue
            x0, y0 = polar(m * 6, 216 if m % 5 == 0 else 224)
            x1, y1 = polar(m * 6, 232)
            if m % 10 == 0:
                nx, ny = polar(m * 6, 217)
                d.text(nx, ny, str(m), 22, 600, (218, 224, 236))
            else:
                d.line([(x0, y0), (x1, y1)], fill=(154, 164, 182) if m % 5 == 0 else (72, 80, 96),
                       width=2.0 if m % 5 == 0 else 1.2, cap=False)

        # Applied hour indices inside dial
        for h in range(12):
            a = h * 30
            if h == 0:
                p0 = polar(0, 174)
                x1, y1 = polar(352, 188)
                x2, y2 = polar(8, 188)
                t_pts = [p0, (x1, y1), (x2, y2)]
                d.poly(t_pts, fill=lume)
                d.line(t_pts + [t_pts[0]], fill=steel_dk, width=1.2, cap=True)
            elif h in (3, 6, 9):
                x0, y0 = polar(a, 166)
                x1, y1 = polar(a, 188)
                d.line([(x0, y0), (x1, y1)], fill=lume, width=7.0, cap=False)
            else:
                cx, cy = polar(a, 176)
                d.circle(cx, cy, 6.2, fill=lume, outline=steel_dk, width=1.4)

        # Two recessed chronograph subdials (9 o'clock: Steps, 3 o'clock: Battery)
        for sx, val, frac, col in ((152, V['steps'], V['sp'], (84, 206, 154)),
                                   (328, f"{V['batt']}%", V['bp'], (244, 190, 68))):
            d.circle(sx, C, 44, fill=(7, 10, 16), outline=(58, 68, 86), width=1.5)
            d.arc(sx, C, 38, 0, 359.9, (28, 34, 46), 3.5, cap=False)
            d.arc(sx, C, 38, 0, 360 * frac, col, 3.5)
            d.text(sx, C + 2, val, 24, 600, WHITE)

        # Clean date window at 6 o'clock
        d.rect(200, 320, 280, 350, 5, fill=(238, 234, 220), outline=steel_dk, width=1.4)
        d.text(C, 335, f"{V['dow']} 12", 21, 700, (16, 18, 22))
        d.text(C, 146, 'AUTOMATICO', 16, 600, (134, 148, 172), spacing=0.18)

    c.paint(dial)
    draw_bevel_hand(c, HOUR_ANG, 118, 22, 10.5, 5.0, steel, steel_dk, lume)
    draw_bevel_hand(c, MIN_ANG, 168, 26, 8.0, 3.5, steel, steel_dk, lume)

    def sec_hand(d):
        x1, y1 = polar(SEC_ANG, 184)
        x0, y0 = polar(SEC_ANG + 180, 42)
        d.line([(x0, y0), (x1, y1)], fill=coral, width=2.2)
        lx, ly = polar(SEC_ANG, 134)
        d.circle(lx, ly, 5.5, fill=lume, outline=coral, width=1.8)
        d.circle(C, C, 7.2, fill=steel, outline=steel_dk, width=1.5)
        d.circle(C, C, 2.8, fill=coral)

    c.paint(sec_hand)
    return c.finish()


# ---------------------------------------------------------------------------
# M3 · TUBI NIXIE (valvole calde anni '60)
# ---------------------------------------------------------------------------
def m3_nixie():
    c = Canvas(Image.new('RGBA', (N, N), (14, 11, 10, 255)))
    neon = (255, 116, 28)
    core = (255, 228, 168)
    ghost = (48, 30, 22)

    tubes = [
        (58, 132, 144, 262, V['hh'][0]),
        (146, 132, 232, 262, V['hh'][1]),
        (248, 132, 334, 262, V['mm'][0]),
        (336, 132, 422, 262, V['mm'][1]),
    ]

    # Glass tube bodies + hexagonal mesh grid inside each tube
    def tube_backs(d):
        d.circle(C, C, 232, outline=(52, 42, 34), width=4)
        d.text(C, 88, f"{V['dowf']} · {V['date']}", 26, 600, (218, 174, 126), spacing=0.06)
        for x0, y0, x1, y1, _ in tubes:
            d.rect(x0, y0, x1, y1, 24, fill=(18, 13, 11), outline=(74, 62, 54), width=1.6)
            # Anode wire mesh grid inside tube
            for gy in range(y0 + 18, y1 - 12, 14):
                d.line([(x0 + 8, gy), (x1 - 8, gy)], fill=(38, 28, 24), width=0.9, cap=False)
            for gx in range(x0 + 14, x1 - 8, 14):
                d.line([(gx, y0 + 14), (gx, y1 - 14)], fill=(34, 25, 21), width=0.9, cap=False)
            # Ghost unlit digits stacked behind
            d.text((x0 + x1) / 2, (y0 + y1) / 2, '8', 110, 500, ghost)
            # Ceramic socket base
            d.rect(x0 + 6, y1 - 14, x1 - 6, y1 + 4, 5, fill=(44, 34, 28), outline=(92, 72, 56), width=1.1)

        # Warm glowing colon bulbs
        for dy in (-18, 18):
            d.circle(C, 197 + dy, 4.5, fill=neon)

    c.paint(tube_backs)

    # Neon filament gas glow + bright hot core
    def filament(d, col):
        for x0, y0, x1, y1, ch in tubes:
            d.text((x0 + x1) / 2, (y0 + y1) / 2, ch, 110, 500, col)
        for dy in (-18, 18):
            d.circle(C, 197 + dy, 4.0, fill=col)

    c.paint(lambda d: filament(d, neon), blur=8, repeat=2)
    c.paint(lambda d: filament(d, core))

    # Specular glass sheen + lower brushed dark brass plaque for metrics
    def glass_and_plaque(d):
        for x0, y0, x1, y1, _ in tubes:
            d.line([(x0 + 11, y0 + 18), (x0 + 11, y1 - 24)], fill=(255, 242, 224, 55), width=2.4)
        # Brass-trimmed plaque
        d.rect(96, 290, 384, 380, 18, fill=(22, 18, 16), outline=(124, 94, 58), width=1.5)
        d.text(162, 322, V['hr'], 32, 600, core)
        d.text(246, 322, V['steps'], 32, 600, core)
        d.text(336, 322, f"{V['batt']}%", 32, 600, neon)
        d.rect(122, 356, 358, 362, 3, fill=(44, 32, 26))
        d.rect(122, 356, 122 + 236 * (V['sec'] / 60), 362, 3, fill=neon)
        d.text(C, 404, f"{V['sec']:02d} SEC", 22, 600, (198, 152, 108), spacing=0.08)

    c.paint(glass_and_plaque)
    c.icon('heart', 128, 322, 18, (255, 96, 86))
    c.icon('steps', 204, 322, 18, (124, 214, 150))
    c.icon('battery', 300, 322, 18, neon)
    return c.finish()


# ---------------------------------------------------------------------------
# M4 · CASIO / BRAUN LCD RETRO (display riflettente a cristalli liquidi)
# ---------------------------------------------------------------------------
def m4_lcd():
    c = Canvas(Image.new('RGBA', (N, N), (20, 22, 26, 255)))
    lcd_bg = (148, 164, 132)
    lcd_dark = (22, 28, 22)
    lcd_ghost = (132, 148, 118)
    lcd_shadow = (104, 118, 92)
    amber_tag = (232, 154, 48)

    def bezel_and_lcd(d):
        # Matte dark resin/steel octagonal-round case
        d.circle(C, C, 234, fill=(24, 27, 32), outline=(68, 74, 86), width=2)
        d.circle(C, C, 214, fill=(14, 16, 20), outline=(48, 54, 66), width=1.4)
        d.text(C, 54, 'QUARTZ CHRONO', 18, 600, amber_tag, spacing=0.14)
        # Recessed olive-grey LCD panel
        d.rect(58, 86, 422, 386, 24, fill=lcd_bg, outline=(18, 22, 20), width=3.5)
        # Inner glass depth shadow along top/left of LCD recess
        d.rect(61, 89, 419, 383, 22, outline=(96, 110, 86), width=2.0)

        # Top LCD info strip: weekday, date, seconds
        d.line([(76, 134), (404, 134)], fill=lcd_shadow, width=1.6, cap=False)
        d.text(92, 112, f"{V['dow']} {V['date']}", 25, 700, lcd_dark, 'l')
        d.text(392, 112, f"{V['sec']:02d}", 28, 700, lcd_dark, 'r')

        # Ghost 88:88 segments behind
        seven_text(d, 146, 152, '88', 48, 102, 10, 12, lcd_ghost, lit=False)
        seven_text(d, 304, 152, '88', 48, 102, 10, 12, lcd_ghost, lit=False)

        # Cast LCD segment drop shadow (+2.5, +2.5) onto reflective backing
        seven_text(d, 148.5, 154.5, V['hh'], 48, 102, 10, 12, lcd_shadow, lit=True)
        seven_text(d, 306.5, 154.5, V['mm'], 48, 102, 10, 12, lcd_shadow, lit=True)

        # Crisp dark LCD segments
        seven_text(d, 146, 152, V['hh'], 48, 102, 10, 12, lcd_dark, lit=True)
        seven_text(d, 304, 152, V['mm'], 48, 102, 10, 12, lcd_dark, lit=True)
        for dy in (-18, 18):
            d.rect(220, 203 + dy - 5, 230, 203 + dy + 5, 1, fill=lcd_dark)

        # Bottom LCD divider & 3 crisp sub-blocks
        d.line([(76, 278), (404, 278)], fill=lcd_shadow, width=1.6, cap=False)
        for bx, val in ((128, V['steps']), (240, V['hr']), (352, f"{V['batt']}%")):
            d.rect(bx - 48, 294, bx + 48, 362, 8, outline=lcd_shadow, width=1.4)
            d.text(bx, 340, val, 32, 700, lcd_dark)

        # Bottom bezel legend
        d.text(C, 412, '100M WATER RESIST', 16, 600, (124, 134, 150), spacing=0.14)

    c.paint(bezel_and_lcd)
    c.icon('steps', 128, 309, 17, lcd_dark)
    c.icon('heart', 240, 309, 17, lcd_dark)
    c.icon('battery', 352, 309, 17, lcd_dark)

    # Diagonal glass reflection over LCD panel
    def sheen(d):
        d.poly([(64, 88), (220, 88), (112, 382), (64, 382)], fill=(255, 255, 255, 22))

    c.paint(sheen)
    return c.finish()


VARIANTS = [
    ('M1', 'MECCANICO SCHELETRATO', 'Ingranaggi, bilanciere oscillante a ore 6 e lancette metalliche con ombra', m1_meccanico),
    ('M2', 'DIVER / CRONOGRAFO', 'Ghiera subacquea, indici lume, due contatori e lancette sfaccettate', m2_diver),
    ('M3', 'TUBI NIXIE ANNI 60', 'Valvole in vetro scuro con griglia, filamenti caldi e riflessi speculari', m3_nixie),
    ('M4', 'CASIO / BRAUN LCD', 'Display a cristalli liquidi con ombra reale dei segmenti e vetro inclinato', m4_lcd),
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
        flat.save(OUT / f'{code}-{name.lower().replace(" / ", "-").replace(" ", "-")}.png')

        x = pad + (i % 2) * (S + pad)
        y = pad + (i // 2) * (S + cap + pad // 2)
        sheet.paste(img, (x, y), img)
        d = ImageDraw.Draw(sheet)
        d.text((x + S / 2, y + S + 36), f'{code} · {name}', font=title_f, fill=(255, 255, 255), anchor='ms')
        d.text((x + S / 2, y + S + 68), line, font=sub_f, fill=(182, 186, 198), anchor='ms')

    out_path = OUT / 'confronto-fisici.png'
    sheet.save(out_path)
    print('Saved:', out_path)
