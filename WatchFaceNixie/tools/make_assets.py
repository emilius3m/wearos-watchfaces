"""Render all photorealistic hardware & Nixie assets for NIXIE (Watch Face Format 2)."""
from pathlib import Path
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops

from layout import (
    S, C, OUTER_CASE_R, BEZEL_IN, REHAUT_IN, SCREW_R,
    TUBE_Y0, TUBE_Y1, TUBE_W, TUBE_H, TUBE_XS,
    GLYPH_W, GLYPH_H, GLYPH_Y, COLON_CY, COLON_SPREAD, FLASH_FRAMES,
    INST_X0, INST_Y0, INST_X1, INST_Y1, WX_X0, WX_Y0, WX_X1, WX_Y1,
    SLOT_L_X, SLOT_R_X, SLOT_W, BOT_Y0, BOT_H, BOT_CAP_R, MIC_X, MIC_Y, MIC_D,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'res/drawable'
Q = 3  # 3x supersampling for silky metal grains and curves


def save(img, name):
    img.save(OUT / f'{name}.png', optimize=True)


# ---------------------------------------------------------------------------
# Authentic bent thin-wire Nixie cathode shapes (0..9)
# ---------------------------------------------------------------------------
NIXIE_STROKES = {
    '0': [
        [(0.50, 0.06), (0.76, 0.10), (0.86, 0.28), (0.86, 0.72), (0.76, 0.90),
         (0.50, 0.94), (0.24, 0.90), (0.14, 0.72), (0.14, 0.28), (0.24, 0.10), (0.50, 0.06)]
    ],
    '1': [
        [(0.32, 0.22), (0.54, 0.07), (0.54, 0.93)],
        [(0.30, 0.93), (0.76, 0.93)]
    ],
    '2': [
        [(0.16, 0.25), (0.26, 0.10), (0.50, 0.06), (0.76, 0.11), (0.85, 0.27),
         (0.82, 0.44), (0.62, 0.60), (0.16, 0.93), (0.86, 0.93)]
    ],
    '3': [
        [(0.18, 0.08), (0.82, 0.08), (0.48, 0.42), (0.68, 0.44), (0.84, 0.56),
         (0.86, 0.74), (0.74, 0.90), (0.50, 0.94), (0.24, 0.90), (0.14, 0.78)]
    ],
    '4': [
        [(0.68, 0.93), (0.68, 0.07), (0.14, 0.66), (0.88, 0.66)]
    ],
    '5': [
        [(0.80, 0.08), (0.24, 0.08), (0.20, 0.44), (0.54, 0.40), (0.78, 0.48),
         (0.86, 0.66), (0.78, 0.86), (0.52, 0.94), (0.24, 0.90), (0.14, 0.78)]
    ],
    '6': [
        [(0.74, 0.11), (0.54, 0.06), (0.28, 0.14), (0.16, 0.38), (0.16, 0.74),
         (0.28, 0.90), (0.52, 0.94), (0.78, 0.88), (0.86, 0.70), (0.80, 0.50),
         (0.54, 0.43), (0.26, 0.48), (0.16, 0.62)]
    ],
    '7': [
        [(0.14, 0.08), (0.86, 0.08), (0.40, 0.93)]
    ],
    '8': [
        [(0.50, 0.47), (0.26, 0.41), (0.18, 0.25), (0.28, 0.10), (0.50, 0.06),
         (0.72, 0.10), (0.82, 0.25), (0.74, 0.41), (0.50, 0.47),
         (0.22, 0.55), (0.14, 0.73), (0.26, 0.90), (0.50, 0.94),
         (0.74, 0.90), (0.86, 0.73), (0.78, 0.55), (0.50, 0.47)]
    ],
    '9': [
        [(0.26, 0.89), (0.48, 0.94), (0.74, 0.86), (0.84, 0.62), (0.84, 0.26),
         (0.72, 0.10), (0.48, 0.06), (0.24, 0.12), (0.16, 0.29), (0.22, 0.48),
         (0.48, 0.54), (0.74, 0.48), (0.84, 0.34)]
    ],
}


def catmull_rom(pts, steps=6):
    if len(pts) < 3:
        return pts
    out = []
    ext = [pts[0]] + pts + [pts[-1]]
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        for s in range(steps):
            t = s / steps
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t +
                       (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 +
                       (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t +
                       (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 +
                       (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    out.append(pts[-1])
    return out


def draw_wire_digit(draw, ch, bx0, by0, bw, bh, width_px, fill):
    r = width_px / 2
    for path in NIXIE_STROKES[ch]:
        scaled = [(bx0 + px * bw, by0 + py * bh) for px, py in path]
        smooth = catmull_rom(scaled) if len(scaled) >= 3 else scaled
        draw.line(smooth, fill=fill, width=max(1, round(width_px)), joint='curve')
        for px, py in (smooth[0], smooth[-1]):
            draw.ellipse([px - r, py - r, px + r, py + r], fill=fill)


def draw_screw(d, cx, cy, r_px, metal, slot_deg=30):
    cxk, cyk, rk = cx * Q, cy * Q, r_px * Q
    d.ellipse([cxk - rk - Q, cyk - rk - Q, cxk + rk + Q, cyk + rk + Q], fill=(8, 7, 6, 235))
    d.ellipse([cxk - rk, cyk - rk, cxk + rk, cyk + rk],
              fill=(*metal, 255), outline=(44, 34, 24, 255), width=max(1, round(0.8 * Q)))
    a = math.radians(slot_deg)
    d.line([(cxk - math.cos(a) * rk * 0.72, cyk - math.sin(a) * rk * 0.72),
            (cxk + math.cos(a) * rk * 0.72, cyk + math.sin(a) * rk * 0.72)],
           fill=(20, 15, 12, 245), width=max(1, round(1.1 * Q)))


# ---------------------------------------------------------------------------
# 1. Brushed hardware dial plates (Titanium & Brass variants, 480x480)
# ---------------------------------------------------------------------------
CASE_STYLES = {
    'titanium': dict(
        case_base=np.array([58, 62, 68], dtype=np.float32),
        bezel_base=np.array([92, 97, 106], dtype=np.float32),
        rehaut_base=np.array([26, 29, 34], dtype=np.float32),
        dial_base=np.array([13, 15, 18], dtype=np.float32),
        accent_metal=(184, 122, 86),
    ),
    'brass': dict(
        case_base=np.array([46, 43, 41], dtype=np.float32),
        bezel_base=np.array([78, 66, 52], dtype=np.float32),
        rehaut_base=np.array([28, 25, 24], dtype=np.float32),
        dial_base=np.array([14, 12, 11], dtype=np.float32),
        accent_metal=(168, 128, 78),
    ),
}


def build_dial_hardware(style_key):
    N = S * Q
    st = CASE_STYLES[style_key]
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
    dx = (xx - N / 2) / Q
    dy = (yy - N / 2) / Q
    r = np.sqrt(dx * dx + dy * dy)
    ang = np.arctan2(dy, dx)

    rng = np.random.default_rng(42)
    plate_grain = rng.normal(0.0, 2.2, (N, N)).astype(np.float32)
    r_idx = np.clip((r * 2.2).astype(np.int32), 0, 900)
    concentric = rng.normal(0.0, 1.0, 902).astype(np.float32)[r_idx]

    aniso = np.cos(2.0 * (ang + math.pi * 0.25))
    top_light = -(dx + dy) / (240.0 * 1.414)

    img = np.zeros((N, N, 4), dtype=np.float32)
    img[..., 3] = 255.0

    # Matte dial base + warm subtle ambient pocket behind tube row
    dial_col = st['dial_base'][None, None, :] + plate_grain[..., None] * 1.4 + top_light[..., None] * 7.5
    tube_mid_dy = (TUBE_Y0 + TUBE_Y1) / 2.0 - C
    tube_field = np.exp(-((dx / 152.0) ** 2 + ((dy - tube_mid_dy) / 68.0) ** 2))
    dial_col += tube_field[..., None] * np.array([18.0, 8.0, 3.0], dtype=np.float32)
    img[..., :3] = dial_col

    # Recessed rehaut wall (REHAUT_IN..BEZEL_IN)
    lip_mask = (r >= REHAUT_IN) & (r < BEZEL_IN)
    lip_shade = 0.55 + 0.45 * np.sin(ang + math.pi * 0.75)
    img[..., :3] = np.where(lip_mask[..., None],
                            st['rehaut_base'][None, None, :] * lip_shade[..., None] + concentric[..., None] * 2.5,
                            img[..., :3])

    # Slim brushed bezel chamfer (BEZEL_IN..OUTER_CASE_R)
    bezel_mask = (r >= BEZEL_IN) & (r < OUTER_CASE_R)
    bevel = np.sin((r - BEZEL_IN) / (OUTER_CASE_R - BEZEL_IN) * math.pi)
    bezel_col = st['bezel_base'][None, None, :] * (
        0.72 + 0.38 * aniso[..., None] + 0.25 * top_light[..., None] + 0.22 * bevel[..., None]
    ) + concentric[..., None] * 4.5
    img[..., :3] = np.where(bezel_mask[..., None], bezel_col, img[..., :3])

    # Outer case edge bevel (>= OUTER_CASE_R)
    case_mask = r >= OUTER_CASE_R
    case_col = st['case_base'][None, None, :] * (
        0.75 + 0.35 * aniso[..., None] + 0.30 * top_light[..., None]
    ) + concentric[..., None] * 3.0
    img[..., :3] = np.where(case_mask[..., None], case_col, img[..., :3])

    pil = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), 'RGBA')
    d = ImageDraw.Draw(pil)
    metal = st['accent_metal']

    # 60 machined rehaut ticks + 4 diagonal bezel screws
    for m in range(60):
        a = math.radians(m * 6)
        r0, r1 = (REHAUT_IN + 1.0, BEZEL_IN - 0.8) if m % 5 == 0 else (REHAUT_IN + 2.5, BEZEL_IN - 1.2)
        col = (*metal, 185) if m % 5 == 0 else (112, 104, 96, 110)
        d.line([((C + r0 * math.sin(a)) * Q, (C - r0 * math.cos(a)) * Q),
                ((C + r1 * math.sin(a)) * Q, (C - r1 * math.cos(a)) * Q)],
               fill=col, width=max(1, round((1.4 if m % 5 == 0 else 0.9) * Q)))

    for sa in (45, 135, 225, 315):
        draw_screw(d, C + SCREW_R * math.sin(math.radians(sa)), C - SCREW_R * math.cos(math.radians(sa)),
                   3.0, metal=(146, 122, 92) if style_key == 'brass' else (152, 158, 168), slot_deg=sa + 22)

    # 4 recessed Nixie bulb cavities, sockets, porcelain pins & stacked unlit cathodes
    for x0 in TUBE_XS:
        x1 = x0 + TUBE_W
        cx = (x0 + x1) / 2
        # Soft cast shadow behind tube onto matte plate
        d.rounded_rectangle([(x0 + 3) * Q, (TUBE_Y0 + 10) * Q, (x1 + 5) * Q, (TUBE_Y1 + 12) * Q],
                            radius=19 * Q, fill=(4, 3, 3, 185))
        # Top blown-glass exhaust nipple
        d.polygon([((cx - 5.0) * Q, (TUBE_Y0 + 8) * Q), (cx * Q, (TUBE_Y0 - 3) * Q), ((cx + 5.0) * Q, (TUBE_Y0 + 8) * Q)],
                  fill=(34, 28, 24, 240), outline=(118, 104, 92, 220))
        d.line([((cx - 3.0) * Q, (TUBE_Y0 + 7) * Q), (cx * Q, (TUBE_Y0 - 2) * Q)], fill=(210, 198, 184, 160), width=Q)

        # Dark bulb interior
        d.rounded_rectangle([x0 * Q, (TUBE_Y0 + 6) * Q, x1 * Q, TUBE_Y1 * Q], radius=17 * Q,
                            fill=(11, 8, 7, 255), outline=(66, 54, 45, 255), width=max(1, round(1.3 * Q)))

        # Machined base collar + porcelain insulator + 4 copper pins
        d.rounded_rectangle([(x0 + 2) * Q, (TUBE_Y1 - 20) * Q, (x1 - 2) * Q, (TUBE_Y1 + 7) * Q], radius=6 * Q,
                            fill=(22, 18, 15, 255), outline=(*metal, 215), width=max(1, round(1.5 * Q)))
        d.rounded_rectangle([(x0 + 8) * Q, (TUBE_Y1 - 15) * Q, (x1 - 8) * Q, (TUBE_Y1 - 3) * Q], radius=3 * Q,
                            fill=(38, 30, 26, 255), outline=(88, 70, 52, 190), width=Q)
        for px in np.linspace(x0 + 15, x1 - 15, 4):
            d.rectangle([(px - 1.2) * Q, (TUBE_Y1 - 19) * Q, (px + 1.2) * Q, (TUBE_Y1 - 6) * Q],
                        fill=(176, 132, 76, 215))

        # Stacked unlit dark wire cathodes inside bulb (aligned cleanly above base collar)
        dx0, dy0, dw, dh = (x0 + 14) * Q, (TUBE_Y0 + 20) * Q, (TUBE_W - 28) * Q, 86 * Q
        for idx, gch in enumerate(('8', '3', '5')):
            ox, oy = (idx - 1) * 1.3 * Q, (idx - 1) * 1.1 * Q
            draw_wire_digit(d, gch, dx0 + ox, dy0 + oy, dw, dh, 1.9 * Q, (42, 30, 24, 110))

    # Central NE-2 glass colon bulb grommets
    for dy_c in (-COLON_SPREAD, COLON_SPREAD):
        cy_c = COLON_CY + dy_c
        d.ellipse([(C - 8) * Q, (cy_c - 8) * Q, (C + 8) * Q, (cy_c + 8) * Q],
                  fill=(18, 14, 12, 255), outline=(*metal, 215), width=max(1, round(1.3 * Q)))
        d.line([((C - 2.2) * Q, (cy_c - 3.2) * Q), ((C - 2.2) * Q, (cy_c + 3.2) * Q)], fill=(116, 86, 58, 200), width=Q)
        d.line([((C + 2.2) * Q, (cy_c - 3.2) * Q), ((C + 2.2) * Q, (cy_c + 3.2) * Q)], fill=(116, 86, 58, 200), width=Q)

    def draw_riveted_window(x0, y0, x1, y1, screw_r=2.8):
        d.rounded_rectangle([x0 * Q, y0 * Q, x1 * Q, y1 * Q], radius=13 * Q,
                            fill=(26, 21, 18, 255), outline=(*metal, 235), width=max(1, round(1.8 * Q)))
        d.rounded_rectangle([(x0 + 5) * Q, (y0 + 5) * Q, (x1 - 5) * Q, (y1 - 5) * Q], radius=9 * Q,
                            fill=(11, 9, 8, 255), outline=(58, 46, 36, 220), width=Q)
        draw_screw(d, x0 + 11, (y0 + y1) / 2, screw_r, metal=metal, slot_deg=25)
        draw_screw(d, x1 - 11, (y0 + y1) / 2, screw_r, metal=metal, slot_deg=-40)

    # Tier 1: Wide upper riveted telemetry aperture (Heart, Steps, Battery + bar)
    draw_riveted_window(INST_X0, INST_Y0, INST_X1, INST_Y1, screw_r=2.9)

    # Tier 2: Full-width riveted weather & forecast console aperture
    draw_riveted_window(WX_X0, WX_Y0, WX_X1, WX_Y1, screw_r=2.7)

    # Tier 3: Curved bottom hardware capsules (Left Complication, Right Complication) + Center Round Push-Button
    for bx0 in (SLOT_L_X, SLOT_R_X):
        bx1, by1 = bx0 + SLOT_W, BOT_Y0 + BOT_H
        d.rounded_rectangle([bx0 * Q, BOT_Y0 * Q, bx1 * Q, by1 * Q], radius=BOT_CAP_R * Q,
                            fill=(24, 20, 17, 255), outline=(*metal, 235), width=max(1, round(1.7 * Q)))
        d.rounded_rectangle([(bx0 + 4) * Q, (BOT_Y0 + 4) * Q, (bx1 - 4) * Q, (by1 - 4) * Q],
                            radius=(BOT_CAP_R - 4) * Q, fill=(11, 9, 8, 255), outline=(54, 44, 36, 200), width=Q)

    # Center recessed round push-button collar + sunken concave cap
    d.ellipse([MIC_X * Q, MIC_Y * Q, (MIC_X + MIC_D) * Q, (MIC_Y + MIC_D) * Q],
              fill=(38, 31, 26, 255), outline=(*metal, 240), width=max(1, round(1.8 * Q)))
    d.ellipse([(MIC_X + 5) * Q, (MIC_Y + 5) * Q, (MIC_X + MIC_D - 5) * Q, (MIC_Y + MIC_D - 5) * Q],
              fill=(18, 15, 13, 255), outline=(88, 70, 52, 200), width=Q)

    save(pil.resize((S, S), Image.LANCZOS), f'dial_{style_key}')


# ---------------------------------------------------------------------------
# 2. Transparent Front Glass + Honeycomb Anode Mesh Overlay (480x480)
# ---------------------------------------------------------------------------
def build_glass_overlay():
    N = S * Q
    canvas = Image.new('RGBA', (N, N), (0, 0, 0, 0))
    w, h = TUBE_W * Q, TUBE_H * Q
    mask = Image.new('L', (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, round(6 * Q), w - 1, h - 1], radius=17 * Q, fill=255)

    u = np.linspace(-1.0, 1.0, w, dtype=np.float32)[None, :]
    v = np.linspace(0.0, 1.0, h, dtype=np.float32)[:, None]

    glass = np.zeros((h, w, 4), dtype=np.float32)
    spec_l = np.exp(-((u + 0.58) / 0.14) ** 2) * (1.0 - 0.35 * np.abs(v - 0.45))
    spec_edge_l = np.exp(-((u + 0.85) / 0.045) ** 2)
    spec_edge_r = np.exp(-((u - 0.84) / 0.06) ** 2)
    edge_dark = np.clip((np.abs(u) - 0.70) / 0.30, 0.0, 1.0) ** 1.7

    glass[..., :3] = 8.0
    glass[..., 3] = edge_dark * 145.0
    white_a = np.clip(spec_l * 60.0 + spec_edge_l * 102.0 + spec_edge_r * 42.0, 0.0, 220.0)
    tot_a = np.clip(glass[..., 3] + white_a, 0, 255)
    blend_r = np.where(tot_a > 0, (white_a * 255.0) / tot_a, 0.0)
    glass[..., 0] = np.clip(blend_r, 0, 255)
    glass[..., 1] = np.clip(blend_r * 0.96, 0, 255)
    glass[..., 2] = np.clip(blend_r * 0.90, 0, 255)
    glass[..., 3] = tot_a

    dome = np.exp(-((v - 0.10) / 0.045) ** 2) * (1.0 - u * u * 0.8)
    glass[..., :3] = np.clip(glass[..., :3] + dome[..., None] * 60.0, 0, 255)
    glass[..., 3] = np.clip(glass[..., 3] + dome * 48.0, 0, 255)

    tube_gl = Image.fromarray(glass.astype(np.uint8), 'RGBA')
    tube_gl.putalpha(ImageChops.multiply(tube_gl.split()[3], mask))

    mesh = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    md = ImageDraw.Draw(mesh)
    hex_r = 4.0 * Q
    dx_h, dy_h = hex_r * 1.732, hex_r * 1.5
    row, y_cur = 0, 10 * Q
    while y_cur < h - 8 * Q:
        x_cur = 4 * Q + (dx_h / 2 if row % 2 else 0)
        while x_cur < w - 4 * Q:
            pts = [(x_cur + hex_r * math.sin(math.radians(a)), y_cur + hex_r * math.cos(math.radians(a)))
                   for a in range(0, 360, 60)]
            md.polygon(pts, outline=(72, 46, 30, 88))
            x_cur += dx_h
        y_cur += dy_h
        row += 1
    mesh.putalpha(ImageChops.multiply(mesh.split()[3], mask))
    tube_gl.alpha_composite(mesh)

    for x0 in TUBE_XS:
        canvas.alpha_composite(tube_gl, (round(x0 * Q), round(TUBE_Y0 * Q)))

    # Subtle diagonal sapphire sheen over telemetry & weather windows
    sheen = Image.new('RGBA', (N, N), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sheen)
    for x0, y0, y1 in ((INST_X0, INST_Y0, INST_Y1), (WX_X0, WX_Y0, WX_Y1)):
        sd.polygon(
            [((x0 + 6) * Q, (y0 + 4) * Q), ((x0 + 104) * Q, (y0 + 4) * Q),
             ((x0 + 52) * Q, (y1 - 4) * Q), ((x0 + 6) * Q, (y1 - 4) * Q)],
            fill=(255, 244, 228, 14)
        )
    canvas.alpha_composite(sheen)
    save(canvas.resize((S, S), Image.LANCZOS), 'tube_glass_array')


# ---------------------------------------------------------------------------
# 3. Theme-tintable Nixie BitmapFont glyphs (nixie_glow_0..9 & nixie_core_0..9)
# ---------------------------------------------------------------------------
def build_nixie_bitmap_fonts():
    # Box is GLYPH_W (73) x GLYPH_H (114). Inside tube, cathode sits at dx=14, dy=16, dw=45, dh=86
    w, h = GLYPH_W * Q, GLYPH_H * Q
    dx0, dy0, dw, dh = 14 * Q, 16 * Q, (GLYPH_W - 28) * Q, 86 * Q
    for digit in '0123456789':
        # Glow sprite (wide cloud + tight sheath, pure white alpha so WFF tints it by PLASMA_COL)
        wide = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        draw_wire_digit(ImageDraw.Draw(wide), digit, dx0, dy0, dw, dh, 8.2 * Q, (255, 255, 255, 165))
        wide = wide.filter(ImageFilter.GaussianBlur(8.5 * Q))

        tight = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        draw_wire_digit(ImageDraw.Draw(tight), digit, dx0, dy0, dw, dh, 4.8 * Q, (255, 255, 255, 230))
        tight = tight.filter(ImageFilter.GaussianBlur(2.6 * Q))
        wide.alpha_composite(tight)
        save(wide.resize((GLYPH_W, GLYPH_H), Image.LANCZOS), f'nixie_glow_{digit}')

        # Hot filament core sprite (tinted cleanly by CORE_COL)
        core = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        cd = ImageDraw.Draw(core)
        draw_wire_digit(cd, digit, dx0, dy0, dw, dh, 3.0 * Q, (255, 255, 255, 225))
        draw_wire_digit(cd, digit, dx0, dy0, dw, dh, 1.5 * Q, (255, 255, 255, 255))
        save(core.resize((GLYPH_W, GLYPH_H), Image.LANCZOS), f'nixie_core_{digit}')


# ---------------------------------------------------------------------------
# 4. Dynamic Colon, Seconds Bead & Ignition Strike Frames
# ---------------------------------------------------------------------------
def build_colon_and_bead():
    # Colon: 24 x 52 centered at (C, COLON_CY)
    cw, ch = 24, 52
    for kind, r_pt, blur_r in (('colon_glow', 5.0, 4.0), ('colon_core', 2.4, 0.4)):
        im = Image.new('RGBA', (cw * Q, ch * Q), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        for dy_c in (-COLON_SPREAD, COLON_SPREAD):
            cy_c = ch / 2 + dy_c
            d.ellipse([(cw / 2 - r_pt) * Q, (cy_c - r_pt) * Q, (cw / 2 + r_pt) * Q, (cy_c + r_pt) * Q],
                      fill=(255, 255, 255, 245))
        if blur_r > 0:
            im = im.filter(ImageFilter.GaussianBlur(blur_r * Q))
        save(im.resize((cw, ch), Image.LANCZOS), kind)

    # Active seconds glowing bead (16x16 white-alpha so it tints per theme)
    bw = 16 * Q
    bead = Image.new('RGBA', (bw, bw), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bead)
    bd.ellipse([3 * Q, 3 * Q, 13 * Q, 13 * Q], fill=(255, 255, 255, 190))
    bead = bead.filter(ImageFilter.GaussianBlur(1.8 * Q))
    bd2 = Image.new('RGBA', (bw, bw), (0, 0, 0, 0))
    ImageDraw.Draw(bd2).ellipse([5 * Q, 5 * Q, 11 * Q, 11 * Q], fill=(255, 255, 255, 255))
    bead.alpha_composite(bd2)
    save(bead.resize((16, 16), Image.LANCZOS), 'sec_bead')


def build_ignition_frames():
    """6-frame gas-discharge ignition strike played inside tubes on wake / minute change."""
    intensities = (0.85, 0.30, 0.95, 0.55, 0.25, 0.08)
    w, h = TUBE_W * Q, TUBE_H * Q
    mask = Image.new('L', (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([2 * Q, 8 * Q, (TUBE_W - 2) * Q, (TUBE_H - 12) * Q],
                                           radius=15 * Q, fill=255)
    for idx, amp in enumerate(intensities, 1):
        im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        cx, cy = w / 2, h * 0.46
        rx, ry = w * (0.28 + 0.12 * amp), h * (0.28 + 0.14 * amp)
        d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=(255, 255, 255, round(155 * amp)))
        im = im.filter(ImageFilter.GaussianBlur(10 * Q))
        im.putalpha(ImageChops.multiply(im.split()[3], mask))
        save(im.resize((TUBE_W, TUBE_H), Image.LANCZOS), f'nixie_flash_{idx}')


# ---------------------------------------------------------------------------
# 5. Weather & Instrument Icons
# ---------------------------------------------------------------------------
def icon_png(name, draw_fn, size=24):
    k = 6
    im = Image.new('L', (24 * k, 24 * k), 0)
    draw_fn(ImageDraw.Draw(im), k)
    im = im.resize((size, size), Image.LANCZOS)
    rgba = Image.new('RGBA', (size, size), (255, 255, 255, 255))
    rgba.putalpha(im)
    save(rgba, name)


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


def glyph_mic(d, k):
    d.rounded_rectangle([8.4 * k, 2.4 * k, 15.6 * k, 13.4 * k], radius=3.6 * k, fill=255)
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
    d.polygon([(13.6 * k, 13.2 * k), (8.4 * k, 19.2 * k), (11.6 * k, 19.2 * k), (10 * k, 23.6 * k),
               (16 * k, 17 * k), (12.6 * k, 17 * k)], fill=255)
    d.line([(13.6 * k, 13.2 * k), (8.4 * k, 19.2 * k)], fill=0, width=1)


def glyph_wx_wind(d, k):
    w = round(2.2 * k)
    d.line([(2.5 * k, 8.6 * k), (14.5 * k, 8.6 * k)], fill=255, width=w)
    d.arc([11.6 * k, 2.6 * k, 17.6 * k, 8.6 * k + w / 2], 160, 90, fill=255, width=w)
    d.line([(2.5 * k, 13.4 * k), (18.6 * k, 13.4 * k)], fill=255, width=w)
    d.arc([15.4 * k, 13.4 * k - w / 2, 21.8 * k, 19.8 * k], 270, 200, fill=255, width=w)
    d.line([(2.5 * k, 18.2 * k), (10.5 * k, 18.2 * k)], fill=255, width=w)


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    for sk in CASE_STYLES:
        build_dial_hardware(sk)
    build_glass_overlay()
    build_nixie_bitmap_fonts()
    build_colon_and_bead()
    build_ignition_frames()
    for name, fn, sz in (
        ('ic_heart', glyph_heart, 16),
        ('ic_steps', glyph_steps, 16),
        ('ic_battery', glyph_battery, 16),
        ('ic_mic', glyph_mic, 26),
        ('wx_sun', glyph_wx_sun, 22),
        ('wx_moon', glyph_wx_moon, 22),
        ('wx_partly', glyph_wx_partly, 22),
        ('wx_cloud', glyph_wx_cloud, 22),
        ('wx_fog', glyph_wx_fog, 22),
        ('wx_rain', glyph_wx_rain, 22),
        ('wx_snow', glyph_wx_snow, 22),
        ('wx_storm', glyph_wx_storm, 22),
        ('wx_wind', glyph_wx_wind, 22),
    ):
        icon_png(name, fn, sz)
    print('All NIXIE assets generated in', OUT)
