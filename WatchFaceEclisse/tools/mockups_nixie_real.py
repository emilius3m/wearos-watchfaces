"""Photorealistic physical Nixie wristwatch study (WFF 2 compatible layered rendering).

Focuses on true hardware materiality:
- Anisotropic brushed metal bezel & concentric lathe dial plate with screws
- Recessed brass tube collars with ambient occlusion & ceramic pin insulators
- 3D cylindrical glass bulbs with vacuum exhaust tip & curved Fresnel reflections
- Fine hexagonal honeycomb anode mesh overlaid in front of the plasma glow
- Custom thin-wire Nixie cathode numerals (0-9) + stacked unlit cathode wires
- Physical NE-2 glass neon colon bulb & recessed riveted brass data aperture
"""
from pathlib import Path
import math
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_assets as MA

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'design/mockups'
VAR = ROOT / 'design/teko_variable.ttf'

S = 480
K = 2
N = S * K
C = S / 2


# ---------------------------------------------------------------------------
# Authentic thin-wire Nixie cathode shapes (normalized in 0..1 x 0..1 box)
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


def catmull_rom_chain(pts, steps=8):
    """Smooth polyline through points using Catmull-Rom spline for bent-wire feel."""
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
    """Draw bent cathode wire numeral with rounded joints and ends."""
    r = width_px / 2
    for path in NIXIE_STROKES[ch]:
        scaled = [(bx0 + px * bw, by0 + py * bh) for px, py in path]
        smooth = catmull_rom_chain(scaled, steps=6) if len(scaled) >= 3 else scaled
        draw.line(smooth, fill=fill, width=max(1, round(width_px)), joint='curve')
        for px, py in (smooth[0], smooth[-1]):
            draw.ellipse([px - r, py - r, px + r, py + r], fill=fill)


# ---------------------------------------------------------------------------
# Procedural Metal / Bezel / Dial Background Synthesis (numpy)
# ---------------------------------------------------------------------------
def build_hardware_dial(style='brass_gunmetal', sec=36):
    """Synthesize brushed metallic bezel, stepped rehaut, matte plate, and brass hardware."""
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
    dx = (xx - N / 2) / K
    dy = (yy - N / 2) / K
    r = np.sqrt(dx * dx + dy * dy)
    ang = np.arctan2(dy, dx)

    rng = np.random.default_rng(42)
    radial_noise = rng.normal(0.0, 1.0, (N, N)).astype(np.float32)
    # Concentric brushed lathe grain (function of radius + faint angular streak)
    r_idx = np.clip((r * 2.2).astype(np.int32), 0, 700)
    concentric = rng.normal(0.0, 1.0, 702).astype(np.float32)[r_idx]
    plate_grain = radial_noise * 2.2

    # Directional studio lighting from top-left (-135 deg -> vector (-0.707, -0.707))
    aniso = np.cos(2.0 * (ang + math.pi * 0.25))  # metallic anisotropic highlight
    top_light = -(dx + dy) / (240.0 * 1.414)

    img = np.zeros((N, N, 4), dtype=np.float32)
    img[..., 3] = 255.0

    if style == 'brass_gunmetal':
        case_base = np.array([46, 43, 41], dtype=np.float32)
        bezel_base = np.array([78, 66, 52], dtype=np.float32)   # aged dark bronze/brass
        rehaut_base = np.array([28, 25, 24], dtype=np.float32)
        dial_base = np.array([15, 13, 12], dtype=np.float32)
        accent_metal = (166, 128, 78)
    else:  # titanium_copper
        case_base = np.array([58, 62, 68], dtype=np.float32)
        bezel_base = np.array([92, 97, 106], dtype=np.float32)  # brushed titanium
        rehaut_base = np.array([26, 29, 34], dtype=np.float32)
        dial_base = np.array([14, 16, 19], dtype=np.float32)
        accent_metal = (184, 122, 86)

    # 1. Matte dark textured watch dial plate (r <= 212)
    dial_col = dial_base[None, None, :] + plate_grain[..., None] * 1.4 + top_light[..., None] * 8.0
    # Subtle warm ambient glow centered behind the 4 tubes
    tube_glow_field = np.exp(-(((dx) / 145.0) ** 2 + ((dy + 34.0) / 72.0) ** 2))
    dial_col += tube_glow_field[..., None] * np.array([28.0, 11.0, 3.0], dtype=np.float32)
    img[..., :3] = dial_col

    # 2. Inner recessed shadow lip at r = 204..212
    lip_mask = (r >= 203.0) & (r < 212.0)
    lip_shade = 0.55 + 0.45 * np.sin(ang + math.pi * 0.75)  # brighter bottom-right wall, shadow top-left
    lip_col = rehaut_base[None, None, :] * lip_shade[..., None] + concentric[..., None] * 2.5
    img[..., :3] = np.where(lip_mask[..., None], lip_col, img[..., :3])

    # 3. Machined brushed bezel chamfer (r = 212..234)
    bezel_mask = (r >= 212.0) & (r < 234.0)
    bevel_profile = np.sin((r - 212.0) / 22.0 * math.pi)
    bezel_col = (
        bezel_base[None, None, :]
        * (0.72 + 0.38 * aniso[..., None] + 0.25 * top_light[..., None] + 0.22 * bevel_profile[..., None])
        + concentric[..., None] * 4.5
    )
    img[..., :3] = np.where(bezel_mask[..., None], bezel_col, img[..., :3])

    # 4. Outer dark stainless case rim (r >= 234)
    case_mask = r >= 234.0
    case_col = case_base[None, None, :] * (0.75 + 0.35 * aniso[..., None] + 0.3 * top_light[..., None]) + concentric[..., None] * 3.0
    img[..., :3] = np.where(case_mask[..., None], case_col, img[..., :3])

    pil = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), 'RGBA')
    d = ImageDraw.Draw(pil)

    # Machined rehaut ticks + active amber LED bead for seconds
    for m in range(60):
        a = math.radians(m * 6)
        r0, r1 = (204.5, 211.0) if m % 5 == 0 else (206.5, 210.5)
        x0 = (C + r0 * math.sin(a)) * K
        y0 = (C - r0 * math.cos(a)) * K
        x1 = (C + r1 * math.sin(a)) * K
        y1 = (C - r1 * math.cos(a)) * K
        if m == sec:
            d.line([(x0, y0), (x1, y1)], fill=(255, 198, 92, 255), width=round(2.4 * K))
        else:
            col = (*accent_metal, 180) if m % 5 == 0 else (110, 102, 94, 105)
            d.line([(x0, y0), (x1, y1)], fill=col, width=round((1.4 if m % 5 == 0 else 0.9) * K))

    # Micro slotted brass bezel/plate screws at cardinal outer points
    for sa in (45, 135, 225, 315):
        sr = 223.0
        sx = (C + sr * math.sin(math.radians(sa))) * K
        sy = (C - sr * math.cos(math.radians(sa))) * K
        rr = 4.2 * K
        d.ellipse([sx - rr - 1, sy - rr - 1, sx + rr + 1, sy + rr + 1], fill=(12, 10, 9, 220))
        d.ellipse([sx - rr, sy - rr, sx + rr, sy + rr], fill=(142, 118, 86, 255), outline=(56, 44, 32, 255), width=K)
        slot_a = math.radians(sa + 22)
        dx_s, dy_s = math.cos(slot_a) * rr * 0.72, math.sin(slot_a) * rr * 0.72
        d.line([(sx - dx_s, sy - dy_s), (sx + dx_s, sy + dy_s)], fill=(26, 20, 16, 240), width=round(1.3 * K))

    return pil, accent_metal


def draw_screw(d, cx, cy, r_px, metal=(156, 122, 76), slot_deg=35):
    cxk, cyk, rk = cx * K, cy * K, r_px * K
    d.ellipse([cxk - rk - K, cyk - rk - K, cxk + rk + K, cyk + rk + K], fill=(8, 7, 6, 230))
    d.ellipse([cxk - rk, cyk - rk, cxk + rk, cyk + rk], fill=(*metal, 255), outline=(48, 38, 28, 255), width=max(1, K // 2))
    a = math.radians(slot_deg)
    d.line([(cxk - math.cos(a) * rk * 0.72, cyk - math.sin(a) * rk * 0.72),
            (cxk + math.cos(a) * rk * 0.72, cyk + math.sin(a) * rk * 0.72)], fill=(22, 17, 13, 245), width=max(1, round(1.1 * K)))


# ---------------------------------------------------------------------------
# 3D Cylindrical Nixie Tube Layering (Socket + Cathodes + Plasma + Mesh + Glass)
# ---------------------------------------------------------------------------
def build_glass_overlay(x0, y0, x1, y1):
    """Create cylindrical glass envelope sheen, Fresnel edge bounce, and exhaust tip."""
    w = round((x1 - x0) * K)
    h = round((y1 - y0) * K)
    r_px = round(18 * K)

    # Mask for domed glass envelope
    mask = Image.new('L', (w, h), 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle([0, round(6 * K), w - 1, h - 1], radius=r_px, fill=255)

    # Compute analytical cylindrical reflection across X in [0..1]
    u = np.linspace(-1.0, 1.0, w, dtype=np.float32)[None, :]
    v = np.linspace(0.0, 1.0, h, dtype=np.float32)[:, None]

    glass = np.zeros((h, w, 4), dtype=np.float32)
    # 1) Soft curved studio window specular on left-center (u ~ -0.58)
    spec_l = np.exp(-((u + 0.58) / 0.14) ** 2) * (1.0 - 0.35 * np.abs(v - 0.45))
    # 2) Sharp thin bright glass edge highlight on far left (u ~ -0.84)
    spec_edge_l = np.exp(-((u + 0.85) / 0.045) ** 2)
    # 3) Subtle cool-amber rim reflection on right wall (u ~ +0.84)
    spec_edge_r = np.exp(-((u - 0.84) / 0.06) ** 2)
    # 4) Cylindrical edge darkening (glass thickness)
    edge_dark = np.clip((np.abs(u) - 0.70) / 0.30, 0.0, 1.0) ** 1.7

    # Dark concave border tint
    glass[..., :3] = 8.0
    glass[..., 3] = edge_dark * 145.0

    # Add white-warm glass specular bands
    white_a = np.clip(spec_l * 62.0 + spec_edge_l * 105.0 + spec_edge_r * 45.0, 0.0, 220.0)
    # Blend specular over glass dark edge
    tot_a = np.clip(glass[..., 3] + white_a, 0, 255)
    blend_r = np.where(tot_a > 0, (white_a * 255.0) / tot_a, 0.0)
    glass[..., 0] = np.clip(blend_r, 0, 255)
    glass[..., 1] = np.clip(blend_r * 0.96, 0, 255)
    glass[..., 2] = np.clip(blend_r * 0.90, 0, 255)
    glass[..., 3] = tot_a

    # Subtle dome top crescent reflection
    dome_band = np.exp(-((v - 0.10) / 0.045) ** 2) * (1.0 - u * u * 0.8)
    glass[..., :3] = np.clip(glass[..., :3] + dome_band[..., None] * 60.0, 0, 255)
    glass[..., 3] = np.clip(glass[..., 3] + dome_band * 50.0, 0, 255)

    out = Image.fromarray(glass.astype(np.uint8), 'RGBA')
    out.putalpha(ImageChops.multiply(out.split()[3], mask))

    # Add subtle hexagonal honeycomb anode wire mesh inside glass
    mesh = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    mdraw = ImageDraw.Draw(mesh)
    hex_r = 4.1 * K
    dx_h = hex_r * 1.732
    dy_h = hex_r * 1.5
    row = 0
    y_cur = 10 * K
    while y_cur < h - 8 * K:
        x_off = (dx_h / 2) if (row % 2) else 0
        x_cur = 4 * K + x_off
        while x_cur < w - 4 * K:
            pts = [(x_cur + hex_r * math.sin(math.radians(a)), y_cur + hex_r * math.cos(math.radians(a)))
                   for a in range(0, 360, 60)]
            mdraw.polygon(pts, outline=(72, 46, 30, 88))
            x_cur += dx_h
        y_cur += dy_h
        row += 1
    mesh.putalpha(ImageChops.multiply(mesh.split()[3], mask))
    out.alpha_composite(mesh)
    return out


def stamp_glyph(canvas, draw_fn, cx, cy, size, color):
    k = max(2, round(size * K / 24 * 4))
    im = Image.new('L', (24 * k, 24 * k), 0)
    draw_fn(ImageDraw.Draw(im), k)
    im = im.resize((round(size * K), round(size * K)), Image.LANCZOS)
    out = Image.new('RGBA', im.size, tuple(color[:3]) + (255,))
    out.putalpha(im)
    canvas.alpha_composite(out, (round(cx * K - out.width / 2), round(cy * K - out.height / 2)))


def glyph_bell(d, k):
    d.pieslice([5 * k, 3.4 * k, 19 * k, 17.4 * k], 180, 360, fill=255)
    d.rectangle([5 * k, 10.4 * k, 19 * k, 17 * k], fill=255)
    d.rounded_rectangle([2.6 * k, 16.4 * k, 21.4 * k, 19.4 * k], radius=1.5 * k, fill=255)
    d.ellipse([9.8 * k, 20.2 * k, 14.2 * k, 23.6 * k], fill=255)
    d.ellipse([10.5 * k, 1.0 * k, 13.5 * k, 4.0 * k], fill=255)


def glyph_mic(d, k):
    d.rounded_rectangle([8.4 * k, 2.4 * k, 15.6 * k, 13.4 * k], radius=3.6 * k, fill=255)
    d.arc([5.2 * k, 6.0 * k, 18.8 * k, 17.6 * k], 0, 180, fill=255, width=max(1, round(1.8 * k)))
    d.line([(12 * k, 17.6 * k), (12 * k, 21.6 * k)], fill=255, width=max(1, round(1.8 * k)))
    d.line([(7.8 * k, 21.6 * k), (16.2 * k, 21.6 * k)], fill=255, width=max(1, round(1.8 * k)))


def stamp_partly_cloudy(canvas, cx, cy, size):
    """Two-tone sun + cream cloud glyph matching WatchFaceSolari clarity."""
    k = max(2, round(size * K / 24 * 4))
    im = Image.new('RGBA', (24 * k, 24 * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # Amber sun
    d.ellipse([9.5 * k, 3.0 * k, 19.5 * k, 13.0 * k], fill=(255, 190, 68, 255))
    # Cream cloud in front
    d.ellipse([3.2 * k, 10.6 * k, 11.4 * k, 18.8 * k], fill=(242, 234, 218, 255))
    d.ellipse([7.6 * k, 7.6 * k, 17.2 * k, 17.2 * k], fill=(242, 234, 218, 255))
    d.ellipse([13.2 * k, 11.2 * k, 20.8 * k, 18.8 * k], fill=(242, 234, 218, 255))
    d.rectangle([7.2 * k, 13.0 * k, 17.2 * k, 18.8 * k], fill=(242, 234, 218, 255))
    im = im.resize((round(size * K), round(size * K)), Image.LANCZOS)
    canvas.alpha_composite(im, (round(cx * K - im.width / 2), round(cy * K - im.height / 2)))


def render_real_nixie(style='brass_gunmetal', hh='09', mm='27', sec=36,
                      shimmer=1.0, colon_pulse=1.0, ignition=None):
    """Render photorealistic Nixie dial; optional shimmer/pulse/ignition for animation frames."""
    dial_pil, accent_metal = build_hardware_dial(style=style, sec=sec)
    canvas = dial_pil

    # 4 tall cylindrical Nixie tubes positioned cleanly inside inner bezel ring
    tubes = [
        (74, 108, 145, 236, hh[0]),
        (149, 108, 220, 236, hh[1]),
        (260, 108, 331, 236, mm[0]),
        (335, 108, 406, 236, mm[1]),
    ]

    # LAYER 1: Brass sockets, top vacuum tips, internal dark plate, unlit cathode stack
    back_layer = Image.new('RGBA', (N, N), (0, 0, 0, 0))
    bd = ImageDraw.Draw(back_layer)

    # Clear date only at top (no obscure jargon)
    font_sm = ImageFont.truetype(str(VAR), round(25 * K))
    font_sm.set_variation_by_axes([600])
    bd.text((C * K, 74 * K), "GIOVEDÌ · 12 NOV", font=font_sm, fill=(214, 180, 138, 235), anchor='ms')

    for x0, y0, x1, y1, ch in tubes:
        cx = (x0 + x1) / 2
        bd.rounded_rectangle([(x0 + 3) * K, (y0 + 10) * K, (x1 + 5) * K, (y1 + 12) * K], radius=19 * K,
                             fill=(4, 3, 3, 185))
        bd.polygon([((cx - 5.0) * K, (y0 + 8) * K), (cx * K, (y0 - 3) * K), ((cx + 5.0) * K, (y0 + 8) * K)],
                   fill=(34, 28, 24, 240), outline=(118, 104, 92, 220))
        bd.line([((cx - 3.0) * K, (y0 + 7) * K), (cx * K, (y0 - 2) * K)], fill=(210, 198, 184, 160), width=K)

        bd.rounded_rectangle([x0 * K, (y0 + 6) * K, x1 * K, y1 * K], radius=17 * K,
                             fill=(11, 8, 7, 255), outline=(66, 54, 45, 255), width=max(1, round(1.3 * K)))

        bd.rounded_rectangle([(x0 + 2) * K, (y1 - 20) * K, (x1 - 2) * K, (y1 + 7) * K], radius=6 * K,
                             fill=(22, 18, 15, 255), outline=(*accent_metal, 210), width=max(1, round(1.5 * K)))
        bd.rounded_rectangle([(x0 + 8) * K, (y1 - 15) * K, (x1 - 8) * K, (y1 - 3) * K], radius=3 * K,
                             fill=(38, 30, 26, 255), outline=(88, 70, 52, 190), width=K)
        for px in np.linspace(x0 + 15, x1 - 15, 4):
            bd.rectangle([(px - 1.2) * K, (y1 - 19) * K, (px + 1.2) * K, (y1 - 6) * K], fill=(176, 132, 76, 215))

        dx0, dy0, dw, dh = (x0 + 14) * K, (y0 + 22) * K, (x1 - x0 - 28) * K, (y1 - y0 - 48) * K
        for idx, gch in enumerate(('8', '3', '5')):
            if gch != ch:
                ox = (idx - 1) * 1.3 * K
                oy = (idx - 1) * 1.1 * K
                draw_wire_digit(bd, gch, dx0 + ox, dy0 + oy, dw, dh, 2.0 * K, (44, 31, 24, 120))

    # Physical NE-2 neon colon bulbs
    for dy_c in (-15, 15):
        cy_c = 171 + dy_c
        bd.ellipse([(C - 8) * K, (cy_c - 8) * K, (C + 8) * K, (cy_c + 8) * K],
                   fill=(18, 14, 12, 255), outline=(*accent_metal, 210), width=round(1.3 * K))
        bd.line([((C - 2.2) * K, (cy_c - 3.2) * K), ((C - 2.2) * K, (cy_c + 3.2) * K)], fill=(120, 88, 60, 210), width=K)
        bd.line([((C + 2.2) * K, (cy_c - 3.2) * K), ((C + 2.2) * K, (cy_c + 3.2) * K)], fill=(120, 88, 60, 210), width=K)

    canvas.alpha_composite(back_layer)

    # LAYER 2: Multi-stage incandescent neon plasma bloom + hot thin-wire core
    def paint_filaments(col, stroke_w, is_colon=True, alpha_scale=1.0):
        layer = Image.new('RGBA', (N, N), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        base_a = round(col[3] * alpha_scale)
        for idx, (x0, y0, x1, y1, ch) in enumerate(tubes):
            dx0, dy0, dw, dh = (x0 + 14) * K, (y0 + 22) * K, (x1 - x0 - 28) * K, (y1 - y0 - 48) * K
            if ignition and ignition[0] == idx:
                _, old_ch, old_a, new_a = ignition
                if old_a > 0.02:
                    draw_wire_digit(ld, old_ch, dx0, dy0, dw, dh, stroke_w * K, (*col[:3], round(base_a * old_a)))
                if new_a > 0.02:
                    draw_wire_digit(ld, ch, dx0, dy0, dw, dh, stroke_w * K, (*col[:3], round(base_a * new_a)))
            else:
                # Subtle organic per-tube phase variation for living gas-discharge buzz
                t_scale = min(1.0, max(0.65, alpha_scale * (1.0 + (idx - 1.5) * 0.03 * (shimmer - 1.0))))
                draw_wire_digit(ld, ch, dx0, dy0, dw, dh, stroke_w * K, (*col[:3], round(col[3] * t_scale)))
        if is_colon:
            c_col = (*col[:3], round(col[3] * colon_pulse))
            for dy_c in (-15, 15):
                cy_c = 171 + dy_c
                r_c = stroke_w * 1.05 * K
                ld.ellipse([C * K - r_c, cy_c * K - r_c, C * K + r_c, cy_c * K + r_c], fill=c_col)
        return layer

    canvas.alpha_composite(paint_filaments((255, 62, 6, 150), 8.2 * (0.94 + 0.08 * shimmer), alpha_scale=0.82 + 0.22 * shimmer).filter(ImageFilter.GaussianBlur(12 * K)))
    canvas.alpha_composite(paint_filaments((255, 126, 22, 225), 5.0 * (0.96 + 0.05 * shimmer), alpha_scale=0.88 + 0.14 * shimmer).filter(ImageFilter.GaussianBlur(3.4 * K)))
    canvas.alpha_composite(paint_filaments((255, 198, 92, 255), 3.1, alpha_scale=0.93 + 0.07 * shimmer))
    canvas.alpha_composite(paint_filaments((255, 245, 214, 255), 1.6))

    # LAYER 3: Hexagonal anode mesh & cylindrical glass reflections IN FRONT of glow
    for x0, y0, x1, y1, _ in tubes:
        glass_ov = build_glass_overlay(x0, y0, x1, y1)
        canvas.alpha_composite(glass_ov, (round(x0 * K), round(y0 * K)))

    # LAYER 4: Upper recessed instrument aperture (Heart, Steps, Battery - icons + clear values only)
    plate = Image.new('RGBA', (N, N), (0, 0, 0, 0))
    pd = ImageDraw.Draw(plate)
    px0, py0, px1, py1 = 92, 252, 388, 312
    pd.rounded_rectangle([px0 * K, py0 * K, px1 * K, py1 * K], radius=13 * K,
                         fill=(26, 21, 18, 255), outline=(*accent_metal, 235), width=round(1.8 * K))
    pd.rounded_rectangle([(px0 + 5) * K, (py0 + 5) * K, (px1 - 5) * K, (py1 - 5) * K], radius=9 * K,
                         fill=(11, 9, 8, 255), outline=(58, 46, 36, 220), width=K)
    draw_screw(pd, px0 + 12, (py0 + py1) / 2, 3.2, metal=accent_metal, slot_deg=25)
    draw_screw(pd, px1 - 12, (py0 + py1) / 2, 3.2, metal=accent_metal, slot_deg=-40)

    f_val = ImageFont.truetype(str(VAR), round(27 * K))
    f_val.set_variation_by_axes([600])
    pd.text((152 * K, 278 * K), "72", font=f_val, fill=(255, 118, 88, 255), anchor='ms')
    pd.text((246 * K, 278 * K), "6480", font=f_val, fill=(255, 224, 158, 255), anchor='ms')
    pd.text((342 * K, 278 * K), "84%", font=f_val, fill=(255, 148, 44, 255), anchor='ms')

    # Thin steps/seconds progress bar inside instrument plate
    bx0, bx1, by = 118, 362, 294
    pd.rounded_rectangle([bx0 * K, by * K, bx1 * K, (by + 4.5) * K], radius=2.2 * K, fill=(32, 24, 18, 255))
    fill_w = (bx1 - bx0) * (sec / 60.0)
    pd.rounded_rectangle([bx0 * K, by * K, (bx0 + fill_w) * K, (by + 4.5) * K], radius=2.2 * K, fill=(255, 134, 34, 245))

    # LAYER 5: Bottom interactive row: Notifications + Weather + Voice Recorder physical button
    y_b0, y_b1 = 324, 376
    y_bm = (y_b0 + y_b1) / 2
    # 1) Notifications recessed brass slot (108..194)
    pd.rounded_rectangle([108 * K, y_b0 * K, 194 * K, y_b1 * K], radius=13 * K,
                         fill=(24, 20, 17, 255), outline=(*accent_metal, 230), width=round(1.6 * K))
    pd.rounded_rectangle([112 * K, (y_b0 + 4) * K, 190 * K, (y_b1 - 4) * K], radius=9 * K,
                         fill=(11, 9, 8, 255), outline=(54, 44, 36, 200), width=K)
    pd.text((166 * K, (y_bm + 2) * K), "2", font=f_val, fill=(255, 214, 142, 255), anchor='ms')

    # 2) Weather recessed brass slot (202..302)
    pd.rounded_rectangle([202 * K, y_b0 * K, 302 * K, y_b1 * K], radius=13 * K,
                         fill=(24, 20, 17, 255), outline=(*accent_metal, 230), width=round(1.6 * K))
    pd.rounded_rectangle([206 * K, (y_b0 + 4) * K, 298 * K, (y_b1 - 4) * K], radius=9 * K,
                         fill=(11, 9, 8, 255), outline=(54, 44, 36, 200), width=K)
    pd.text((268 * K, (y_bm + 2) * K), "14°", font=f_val, fill=(255, 224, 162, 255), anchor='ms')

    # 3) Voice Recorder tactile machined metal push-button (310..372)
    pd.rounded_rectangle([310 * K, y_b0 * K, 372 * K, y_b1 * K], radius=15 * K,
                         fill=(42, 34, 28, 255), outline=(*accent_metal, 240), width=round(1.8 * K))
    pd.rounded_rectangle([315 * K, (y_b0 + 5) * K, 367 * K, (y_b1 - 5) * K], radius=11 * K,
                         fill=(22, 18, 15, 255), outline=(92, 72, 54, 190), width=K)

    # Diagonal sapphire crystal sheen over the top instrument window
    sheen = Image.new('RGBA', (N, N), (0, 0, 0, 0))
    ImageDraw.Draw(sheen).polygon(
        [(98 * K, 256 * K), (190 * K, 256 * K), (138 * K, 308 * K), (98 * K, 308 * K)],
        fill=(255, 244, 228, 16)
    )
    plate.alpha_composite(sheen)

    # Bottom plain seconds numeral (clear, zero jargon)
    f_bot = ImageFont.truetype(str(VAR), round(20 * K))
    f_bot.set_variation_by_axes([600])
    pd.text((C * K, 404 * K), f"{sec:02d} SEC", font=f_bot, fill=(*accent_metal, 220), anchor='ms')

    canvas.alpha_composite(plate)

    # Stamp clean hardware icons into the apertures
    stamp_glyph(canvas, MA.glyph_heart, 128, 274, 15, (255, 96, 86))
    stamp_glyph(canvas, MA.glyph_steps, 208, 274, 15, (124, 214, 150))
    stamp_glyph(canvas, MA.glyph_battery, 310, 274, 15, (255, 148, 44))
    stamp_glyph(canvas, glyph_bell, 136, y_bm, 18, (255, 174, 68))
    stamp_partly_cloudy(canvas, 228, y_bm, 24)
    stamp_glyph(canvas, glyph_mic, 341, y_bm, 20, (255, 148, 44))

    mask = Image.new('L', (N, N), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, N - 1, N - 1], fill=255)
    out = Image.new('RGBA', (N, N), (0, 0, 0, 0))
    out.paste(canvas, (0, 0), mask)
    return out.resize((S, S), Image.LANCZOS)


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    items = [
        ('R1', 'OTTONE & GUNMETAL', 'Cassa ottone, valvole 3D, meteo + notifiche + registratore, nessuna sigla',
         render_real_nixie('brass_gunmetal')),
        ('R2', 'TITANIO & RAME', 'Lunetta in titanio spazzolato, rame, meteo + notifiche + registratore',
         render_real_nixie('titanium_copper')),
    ]

    pad, cap = 34, 86
    sheet = Image.new('RGB', (2 * S + 3 * pad, S + cap + 2 * pad), (20, 21, 24))
    tfont = ImageFont.truetype(str(VAR), 38)
    sfont = ImageFont.truetype(str(VAR), 23)
    tfont.set_variation_by_axes([600])
    sfont.set_variation_by_axes([400])

    for i, (code, title, desc, img) in enumerate(items):
        flat = Image.new('RGB', (S, S), (0, 0, 0))
        flat.paste(img, (0, 0), img)
        flat.save(OUT / f"{code}-{title.lower().replace(' ', '-').replace('&', 'e')}.png")
        x = pad + i * (S + pad)
        sheet.paste(img, (x, pad), img)
        sd = ImageDraw.Draw(sheet)
        sd.text((x + S / 2, pad + S + 36), f"{code} · {title}", font=tfont, fill=(255, 255, 255), anchor='ms')
        sd.text((x + S / 2, pad + S + 68), desc, font=sfont, fill=(182, 186, 198), anchor='ms')

    out_sheet = OUT / 'confronto-nixie-reale.png'
    sheet.save(out_sheet)
    print('Saved:', out_sheet)

    # Animated GIF demonstrating subtle high-voltage plasma shimmer + minute switch strike
    fps = 14
    frames = []
    # 3 seconds: 09:27:58 -> 09:27:59 -> 09:28:00 (digit switch flicker)
    for fi in range(3 * fps):
        sec_idx = fi // fps
        frac = (fi % fps) / fps
        if sec_idx == 0:
            hh, mm, sec, ign = '09', '27', 58, None
        elif sec_idx == 1:
            hh, mm, sec, ign = '09', '27', 59, None
        else:
            hh, mm, sec = '09', '28', 0
            if frac < 0.45:
                t = frac / 0.45
                flick = 0.45 if 0.16 < frac < 0.25 else (1.15 if 0.25 <= frac < 0.34 else 1.0)
                ign = (3, '7', max(0.0, 1.0 - t * 2.2), min(1.0, t * 1.4) * flick)
            else:
                ign = None

        # High-frequency plasma discharge micro-shimmer (~6Hz electric hum) + 1Hz NE-2 pulse
        shimmer = 0.72 + 0.56 * (0.5 + 0.5 * math.sin(2 * math.pi * 6.0 * (fi / fps)))
        colon_p = 0.42 + 0.58 * (0.5 + 0.5 * math.cos(2 * math.pi * frac))
        im = render_real_nixie('titanium_copper', hh=hh, mm=mm, sec=sec,
                               shimmer=shimmer, colon_pulse=colon_p, ignition=ign)
        flat = Image.new('RGB', (S, S), (12, 12, 14))
        flat.paste(im, (0, 0), im)
        frames.append(flat.quantize(colors=160, method=Image.Quantize.FASTOCTREE))

    gif_path = OUT / 'R2-nixie-vibrazione.gif'
    frames[0].save(gif_path, save_all=True, append_images=frames[1:],
                   duration=round(1000 / fps), loop=0, optimize=True)
    print('Saved:', gif_path)
