"""Four design studies: B2 Asymmetric Bento + Vintage Flip-Clock digits + Seconds Crown.

Design studies only: nothing here alters watchface.xml or ECLISSE.apk.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from mockups import Canvas, mix, polar, V, S, C, K, WHITE, BLACK, OUT, VAR

INK = (15, 17, 22)
CREAM = (244, 238, 224)
SLATE = (22, 26, 35)
BORDER = (58, 66, 86)


def draw_flip_card(canvas, x0, y0, x1, y1, r, text, text_size, text_col,
                   top_col, mid_up, mid_down, bot_col, edge_col, split_col=(8, 9, 12),
                   pin_col=(18, 19, 23), pin_edge=(76, 80, 92), text_dx=0):
    """Draw a realistic vintage split-flap card in logical coordinates (480 x 480)."""
    w = round(x1 - x0)
    h = round(y1 - y0)
    mid = h / 2.0

    # Vertical gradient body at Kx oversampling
    W, H = w * K, h * K
    ys = (np.arange(H) + 0.5) / K
    stops = [(0, top_col), (mid, mid_up), (mid + 0.01, mid_down), (h, bot_col)]
    cols = np.stack([np.interp(ys, [s[0] for s in stops], [s[1][i] for s in stops]) for i in range(3)], axis=1)
    body = Image.fromarray(np.repeat(cols[:, None, :], W, axis=1).astype(np.uint8), 'RGB').convert('RGBA')

    mask = Image.new('L', (W, H), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, W - 1, H - 1], radius=r * K, fill=255)
    body.putalpha(mask)

    bd = ImageDraw.Draw(body)
    bd.rounded_rectangle([0, 0, W - 1, H - 1], radius=r * K, outline=edge_col + (255,), width=max(1, round(1.4 * K)))
    canvas.img.alpha_composite(body, (round(x0 * K), round(y0 * K)))

    # Digit across the flap
    canvas.paint(lambda d: d.text(x0 + w / 2 + text_dx, y0 + h / 2, text, text_size, 700, text_col))

    # Cast shadow + split groove + lip highlight + side hinge pins
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    yy = ((np.arange(H) + 0.5) / K)[:, None]
    alpha = np.where(yy > mid, 0.34 * np.exp(-(yy - mid) / 7.5), 0.12 * np.exp(-(mid - yy) / 3.5))
    arr = np.zeros((H, W, 4), np.uint8)
    arr[..., 3] = np.clip(alpha * 255, 0, 255)
    ov = Image.fromarray(arr, 'RGBA')
    ov.putalpha(Image.composite(ov.getchannel('A'), Image.new('L', (W, H), 0), mask))
    od = ImageDraw.Draw(ov)
    od.rectangle([0, (mid - 1.5) * K, W, (mid + 1.5) * K], fill=split_col + (255,))
    od.rectangle([2 * K, (mid + 1.5) * K, W - 2 * K, (mid + 2.4) * K], fill=(255, 255, 255, 36))
    canvas.img.alpha_composite(ov, (round(x0 * K), round(y0 * K)))

    # Side hinge pins slightly proud of card edge
    def pins(d):
        ym = y0 + mid
        for px in (x0 - 2.5, x1 - 4.5):
            d.rect(px, ym - 9, px + 7, ym + 9, 2.5, fill=pin_col, outline=pin_edge, width=1.1)

    canvas.paint(pins)


def draw_seconds_crown_ticks(d, sec, lit_col, dim_col, pointer_col=None, numbers=False):
    """60-tick perimeter seconds crown."""
    for i in range(60):
        a = i * 6
        major = (i % 5 == 0)
        r1 = 235
        r0 = 225 if major else 230
        x0, y0 = polar(a, r0)
        x1, y1 = polar(a, r1)
        lit = a <= sec * 6
        col = lit_col if lit else dim_col
        d.line([(x0, y0), (x1, y1)], fill=col, width=2.4 if major else 1.3, cap=False)
    if numbers:
        for a, lbl in ((90, '15'), (180, '30'), (270, '45')):
            nx, ny = polar(a, 218)
            d.text(nx, ny, lbl, 14, 600, (142, 150, 170))
    if pointer_col:
        px, py = polar(sec * 6, 231)
        d.circle(px, py, 4.8, fill=pointer_col, outline=BLACK, width=1.2)


def draw_seconds_crown_rail(d, sec, lit_col, dim_col, dot_col):
    """Railway minute-track + sweeping glowing progress arc + seconds bead."""
    d.arc(C, C, 233, 0, 359.9, dim_col, 3.2, cap=False)
    d.arc(C, C, 233, 0, sec * 6, lit_col, 3.2)
    for i in range(60):
        a = i * 6
        major = (i % 5 == 0)
        x0, y0 = polar(a, 223 if major else 227)
        x1, y1 = polar(a, 230)
        col = lit_col if a <= sec * 6 else dim_col
        d.line([(x0, y0), (x1, y1)], fill=col, width=2.0 if major else 1.1, cap=False)
    px, py = polar(sec * 6, 233)
    d.circle(px, py, 5.2, fill=dot_col, outline=BLACK, width=1.2)


def draw_right_tiles(c, dark_mode=False):
    sage = (74, 214, 158)
    coral = (255, 96, 104)
    amber = (255, 198, 56)
    sky = (118, 178, 255)

    def paint_tiles(d):
        # Top date bar
        d.rect(128, 52, 352, 86, 14, fill=SLATE, outline=BORDER, width=1.4)
        d.text(C, 69, f"{V['dowf']} · {V['date']}", 24, 600, CREAM, spacing=0.05)

        if not dark_mode:
            # Solid color tiles (Mosaico pop)
            d.rect(236, 98, 404, 168, 20, fill=coral)
            d.text(390, 115, 'BPM', 16, 700, mix(coral, INK, 0.78), 'r', spacing=0.08)
            d.text(320, 141, V['hr'], 42, 700, INK)

            d.rect(236, 176, 404, 246, 20, fill=amber)
            d.text(390, 193, 'BATT', 16, 700, mix(amber, INK, 0.78), 'r', spacing=0.08)
            d.text(320, 214, f"{V['batt']}%", 38, 700, INK)
            d.rect(254, 234, 386, 239, 2.5, fill=mix(amber, INK, 0.28))
            d.rect(254, 234, 254 + 132 * V['bp'], 239, 2.5, fill=INK)

            d.rect(236, 254, 404, 324, 20, fill=sage)
            d.text(390, 271, 'PASSI', 16, 700, mix(sage, INK, 0.78), 'r', spacing=0.08)
            d.text(320, 292, V['steps'], 37, 700, INK)
            d.rect(254, 312, 386, 317, 2.5, fill=mix(sage, INK, 0.28))
            d.rect(254, 312, 254 + 132 * V['sp'], 317, 2.5, fill=INK)
        else:
            # Dark architectural tiles with bold colored left accent bars
            for y0, y1, lab, val, col, prog in [
                (98, 168, 'BPM', V['hr'], coral, None),
                (176, 246, 'BATT', f"{V['batt']}%", amber, V['bp']),
                (254, 324, 'PASSI', V['steps'], sage, V['sp']),
            ]:
                d.rect(236, y0, 404, y1, 20, fill=(24, 27, 35), outline=(52, 58, 74), width=1.3)
                d.rect(243, y0 + 12, 248, y1 - 12, 2.5, fill=col)
                d.text(390, y0 + 17, lab, 16, 700, (162, 170, 190), 'r', spacing=0.08)
                d.text(323, y0 + (43 if prog is None else 38), val, 40 if prog is None else 37, 700, CREAM)
                if prog is not None:
                    d.rect(258, y1 - 12, 386, y1 - 7, 2.5, fill=(44, 50, 66))
                    d.rect(258, y1 - 12, 258 + 128 * prog, y1 - 7, 2.5, fill=col)

        # Bottom complication pills
        for x0, val in ((124, V['bell']), (244, V['sun'])):
            d.rect(x0, 334, x0 + 112, 388, 19, fill=SLATE, outline=BORDER, width=1.4)
            d.text(x0 + 72, 361, val, 28, 600, CREAM)

    c.paint(paint_tiles)
    if not dark_mode:
        c.icon('heart', 259, 116, 19, INK)
        c.icon('battery', 259, 194, 19, INK)
        c.icon('steps', 259, 272, 19, INK)
    else:
        c.icon('heart', 268, 116, 19, coral)
        c.icon('battery', 268, 194, 19, amber)
        c.icon('steps', 268, 272, 19, sage)
    c.icon('bell', 150, 361, 20, sky)
    c.icon('sun', 268, 360, 20, amber)


# ---------------------------------------------------------------------------
def f1_flip_scuro_pop():
    """Dark vintage Solari flip-cards on left + solid pop tiles on right + 60-tick crown."""
    c = Canvas()
    c.paint(lambda d: draw_seconds_crown_ticks(d, V['sec'], CREAM, (50, 56, 70), pointer_col=(255, 96, 104)))
    draw_right_tiles(c, dark_mode=False)
    # Two stacked dark graphite split-flap cards on left (72..226)
    top, mu, md, bot, edge = (54, 56, 64), (42, 43, 49), (35, 36, 42), (27, 28, 33), (82, 86, 98)
    draw_flip_card(c, 72, 98, 226, 207, 18, V['hh'], 116, CREAM, top, mu, md, bot, edge)
    draw_flip_card(c, 72, 215, 226, 324, 18, V['mm'], 116, (255, 198, 56), top, mu, md, bot, edge)
    return c.finish()


def f2_flip_crema_rail():
    """Warm cream vintage flip-cards on left + solid pop tiles on right + railway seconds crown."""
    c = Canvas()
    c.paint(lambda d: draw_seconds_crown_rail(d, V['sec'], CREAM, (48, 54, 68), dot_col=(255, 96, 104)))
    draw_right_tiles(c, dark_mode=False)
    top, mu, md, bot, edge = (250, 245, 232), (236, 229, 214), (224, 216, 200), (206, 198, 182), (176, 168, 152)
    draw_flip_card(c, 72, 98, 226, 207, 18, V['hh'], 116, INK, top, mu, md, bot, edge,
                   split_col=(44, 42, 38), pin_col=(46, 48, 54), pin_edge=(130, 126, 118))
    draw_flip_card(c, 72, 215, 226, 324, 18, V['mm'], 116, (212, 54, 64), top, mu, md, bot, edge,
                   split_col=(44, 42, 38), pin_col=(46, 48, 54), pin_edge=(130, 126, 118))
    return c.finish()


def f3_solari_strumento():
    """Industrial 70s instrument: dark flip-cards + dark accented tiles + chrono ticks (15/30/45)."""
    c = Canvas()
    amber = (255, 190, 64)
    c.paint(lambda d: draw_seconds_crown_ticks(d, V['sec'], amber, (48, 52, 64), pointer_col=amber, numbers=True))
    draw_right_tiles(c, dark_mode=True)
    top, mu, md, bot, edge = (52, 54, 62), (40, 41, 47), (33, 34, 40), (26, 27, 32), (80, 84, 96)
    draw_flip_card(c, 72, 98, 226, 207, 18, V['hh'], 116, CREAM, top, mu, md, bot, edge)
    draw_flip_card(c, 72, 215, 226, 324, 18, V['mm'], 116, (255, 96, 104), top, mu, md, bot, edge)
    return c.finish()


def f4_cassa_flip_2x2():
    """Twin flip-cards inside a brushed bezel housing + clean 60-tick emerald/cream seconds crown."""
    c = Canvas()
    mint = (74, 214, 158)
    c.paint(lambda d: draw_seconds_crown_ticks(d, V['sec'], mint, (46, 52, 64), pointer_col=CREAM))
    draw_right_tiles(c, dark_mode=False)
    # Outer metallic flip-housing frame wrapping both cards
    c.paint(lambda d: d.rect(65, 91, 233, 331, 24, fill=(10, 11, 15), outline=(88, 94, 110), width=1.6))
    top, mu, md, bot, edge = (48, 50, 58), (37, 38, 44), (31, 32, 37), (24, 25, 29), (74, 78, 90)
    draw_flip_card(c, 73, 99, 225, 207, 16, V['hh'], 114, CREAM, top, mu, md, bot, edge)
    draw_flip_card(c, 73, 215, 225, 323, 16, V['mm'], 114, CREAM, top, mu, md, bot, edge)
    return c.finish()


VARIANTS = [
    ('F1', 'FLIP SCURO + POP', 'Palette flip grafite a sinistra, tessere piene a destra, corona a 60 tacche', f1_flip_scuro_pop),
    ('F2', 'FLIP CREMA + RAIL', 'Palette avorio vintage con cerniere scure + corona ferroviaria', f2_flip_crema_rail),
    ('F3', 'SOLARI STRUMENTO', 'Look anni 70 scuro con barre colore e corona crono (15·30·45)', f3_solari_strumento),
    ('F4', 'CASSA FLIP + POP', 'Doppio flip incassato in cornice metallica + corona a tacche verdi', f4_cassa_flip_2x2),
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
        flat.save(OUT / f'{code}-{name.lower().replace(" + ", "-").replace(" ", "-")}.png')

        x = pad + (i % 2) * (S + pad)
        y = pad + (i // 2) * (S + cap + pad // 2)
        sheet.paste(img, (x, y), img)
        d = ImageDraw.Draw(sheet)
        d.text((x + S / 2, y + S + 36), f'{code} · {name}', font=title_f, fill=(255, 255, 255), anchor='ms')
        d.text((x + S / 2, y + S + 68), line, font=sub_f, fill=(182, 186, 198), anchor='ms')

    out_path = OUT / 'confronto-b2-flip.png'
    sheet.save(out_path)
    print('Saved:', out_path)
