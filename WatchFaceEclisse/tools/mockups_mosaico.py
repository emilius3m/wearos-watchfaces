"""Four design variations based on B · MOSAICO.

Design studies only: nothing here alters watchface.xml or ECLISSE.apk.
"""
from PIL import Image, ImageDraw, ImageFont

from mockups import Canvas, GLYPHS, mix, polar, V, S, C, WHITE, BLACK, OUT, VAR

INK = (15, 17, 22)
CREAM = (244, 238, 224)
SLATE = (22, 26, 35)
SLATE_HI = (31, 36, 48)
BORDER = (56, 64, 84)


def b1_bento_scuro():
    """Dark-first bento: charcoal time card + refined matte tiles + clean outer ticks."""
    c = Canvas()
    mint = (46, 212, 152)
    coral = (248, 92, 98)
    amber = (246, 188, 52)
    sky = (112, 172, 255)
    tiles = [
        ('steps', V['steps'], 'PASSI', mint, V['sp']),
        ('heart', V['hr'], 'BPM', coral, None),
        ('battery', V['batt'] + '%', 'BATT', amber, V['bp']),
    ]

    def face(d):
        # Segmented 60-second bezel ticks + thin progress arc
        for i in range(60):
            a = i * 6
            r1 = 235
            r0 = 228 if i % 5 == 0 else 231
            x0, y0 = polar(a, r0)
            x1, y1 = polar(a, r1)
            lit = a <= V['sec'] * 6
            col = CREAM if lit else (52, 58, 72)
            d.line([(x0, y0), (x1, y1)], fill=col, width=2.2 if i % 5 == 0 else 1.3, cap=False)

        # Top date pill (leaves room at 12 o'clock for system indicator)
        d.text(C, 76, f"{V['dowf']} · {V['date']}", 28, 600, (198, 204, 218), spacing=0.05)

        # Charcoal time block with crisp hairline border
        d.rect(58, 102, 422, 234, 28, fill=SLATE, outline=BORDER, width=1.6)
        d.text(C - 16, 168, V['hh'], 144, 700, CREAM, 'r')
        d.text(C + 16, 168, V['mm'], 144, 700, CREAM, 'l')
        for dy in (-19, 19):
            d.rect(C - 5.5, 168 + dy - 5.5, C + 5.5, 168 + dy + 5.5, 3, fill=coral)

        # Middle row: 3 solid color tiles with tight 8px grid gap
        for i, (_, val, lab, col, prog) in enumerate(tiles):
            x0 = 58 + i * 124
            d.rect(x0, 242, x0 + 116, 348, 22, fill=col)
            d.text(x0 + 102, 261, lab, 17, 700, mix(col, INK, 0.78), 'r', spacing=0.08)
            d.text(x0 + 58, 301, val, 45, 700, INK)
            if prog is not None:
                d.rect(x0 + 16, 331, x0 + 100, 337, 3, fill=mix(col, INK, 0.25))
                d.rect(x0 + 16, 331, x0 + 16 + 84 * prog, 337, 3, fill=INK)

        # Bottom row: matching bento complication cards
        for x0, val, tag in ((120, V['bell'], 'NOTIF'), (244, V['sun'], 'TRAM')):
            d.rect(x0, 356, x0 + 116, 412, 20, fill=SLATE, outline=BORDER, width=1.6)
            d.text(x0 + 74, 384, val, 30, 600, CREAM)

    c.paint(face)
    for i, (ic, _, _, _, _) in enumerate(tiles):
        c.icon(ic, 58 + i * 124 + 25, 263, 22, INK)
    c.icon('bell', 120 + 27, 384, 21, sky)
    c.icon('sun', 244 + 25, 383, 21, amber)
    return c.finish()


def b2_asymmetric():
    """Asymmetric bento: stacked cream hour-minute hero on left, live metric tiles on right."""
    c = Canvas()
    sage = (74, 214, 158)
    coral = (255, 96, 104)
    amber = (255, 198, 56)
    sky = (118, 178, 255)

    def face(d):
        d.arc(C, C, 233, 0, 359.9, (34, 39, 50), 4.5, cap=False)
        d.arc(C, C, 233, 0, V['sec'] * 6, CREAM, 4.5)

        # Top date bar (well inside circle at y=74)
        d.rect(128, 52, 352, 86, 14, fill=SLATE, outline=BORDER, width=1.4)
        d.text(C, 69, f"{V['dowf']} {V['date']}", 24, 600, CREAM, spacing=0.06)

        # Left Hero Block: stacked 09 / 27 on cream (clean margin from outer ring)
        d.rect(70, 96, 228, 326, 28, fill=CREAM)
        d.text(149, 155, V['hh'], 128, 700, INK)
        d.line([(92, 211), (206, 211)], fill=mix(CREAM, INK, 0.16), width=2.0)
        d.text(149, 267, V['mm'], 128, 700, coral)

        # Right Column: 3 aligned stacked metric tiles (x = 236..406)
        # Top-right: Heart (coral)
        d.rect(236, 96, 406, 168, 22, fill=coral)
        d.text(392, 114, 'BPM', 16, 700, mix(coral, INK, 0.78), 'r', spacing=0.08)
        d.text(321, 140, V['hr'], 42, 700, INK)

        # Mid-right: Battery (amber)
        d.rect(236, 176, 406, 248, 22, fill=amber)
        d.text(392, 194, 'BATT', 16, 700, mix(amber, INK, 0.78), 'r', spacing=0.08)
        d.text(321, 215, f"{V['batt']}%", 38, 700, INK)
        d.rect(254, 236, 388, 241, 2.5, fill=mix(amber, INK, 0.28))
        d.rect(254, 236, 254 + 134 * V['bp'], 241, 2.5, fill=INK)

        # Lower-right: Steps (sage)
        d.rect(236, 256, 406, 326, 22, fill=sage)
        d.text(392, 273, 'PASSI', 16, 700, mix(sage, INK, 0.78), 'r', spacing=0.08)
        d.text(321, 294, V['steps'], 37, 700, INK)
        d.rect(254, 314, 388, 319, 2.5, fill=mix(sage, INK, 0.28))
        d.rect(254, 314, 254 + 134 * V['sp'], 319, 2.5, fill=INK)

        # Bottom row: 2 wide complication pills
        for x0, val in ((124, V['bell']), (244, V['sun'])):
            d.rect(x0, 336, x0 + 112, 392, 20, fill=SLATE, outline=BORDER, width=1.4)
            d.text(x0 + 72, 364, val, 28, 600, WHITE)

    c.paint(face)
    c.icon('heart', 260, 115, 20, INK)
    c.icon('battery', 260, 195, 20, INK)
    c.icon('steps', 260, 274, 20, INK)
    c.icon('bell', 150, 364, 20, sky)
    c.icon('sun', 268, 363, 20, amber)
    return c.finish()


def b3_swiss():
    """Refined Swiss/Braun evolution of B: better bezel margins, calmer palette, unified tiles."""
    c = Canvas()
    paper = (242, 236, 222)
    terra = (238, 108, 77)
    jade = (82, 196, 152)
    ochre = (238, 184, 68)
    slate_card = (32, 37, 48)
    tiles = [
        ('steps', V['steps'], 'PASSI', jade, V['sp']),
        ('heart', V['hr'], 'BPM', terra, None),
        ('battery', V['batt'] + '%', 'BATT', ochre, V['bp']),
    ]

    def face(d):
        # Clean thin double-track seconds ring
        d.arc(C, C, 232, 0, 359.9, (34, 39, 49), 4, cap=False)
        d.arc(C, C, 232, 0, V['sec'] * 6, paper, 4)

        d.text(C, 76, f"{V['dowf']} · {V['date']}", 28, 600, (216, 212, 202), spacing=0.05)

        # Better proportioned time block (stays well clear of the round bezel)
        d.rect(62, 100, 418, 226, 26, fill=paper)
        d.text(C - 15, 163, V['hh'], 138, 700, INK, 'r')
        d.text(C + 15, 163, V['mm'], 138, 700, INK, 'l')
        for dy in (-18, 18):
            d.rect(C - 5.5, 163 + dy - 5.5, C + 5.5, 163 + dy + 5.5, 3, fill=terra)

        # 3 calm editorial color tiles
        for i, (_, val, lab, col, prog) in enumerate(tiles):
            x0 = 62 + i * 121
            d.rect(x0, 234, x0 + 114, 340, 22, fill=col)
            d.text(x0 + 100, 252, lab, 17, 700, mix(col, INK, 0.78), 'r', spacing=0.08)
            d.text(x0 + 57, 293, val, 44, 700, INK)
            if prog is not None:
                d.rect(x0 + 16, 323, x0 + 98, 329, 3, fill=mix(col, INK, 0.25))
                d.rect(x0 + 16, 323, x0 + 16 + 82 * prog, 329, 3, fill=INK)

        # Unified bottom tiles (same corner family, cleaner silhouette)
        for x0, val in ((124, V['bell']), (244, V['sun'])):
            d.rect(x0, 348, x0 + 112, 404, 20, fill=slate_card)
            d.text(x0 + 71, 376, val, 29, 600, paper)

    c.paint(face)
    for i, (ic, _, _, _, _) in enumerate(tiles):
        c.icon(ic, 62 + i * 121 + 25, 254, 22, INK)
    c.icon('bell', 150, 376, 21, (130, 182, 248))
    c.icon('sun', 268, 375, 21, ochre)
    return c.finish()


def b4_tastiera_oled():
    """Pure OLED black top for giant crisp time, vibrant modular 3+2 color keyboard below."""
    c = Canvas()
    mint = (46, 222, 158)
    coral = (255, 96, 104)
    amber = (255, 198, 54)
    cyan = (98, 182, 255)
    tiles = [
        ('steps', V['steps'], 'PASSI', mint, V['sp']),
        ('heart', V['hr'], 'BPM', coral, None),
        ('battery', V['batt'] + '%', 'BATT', amber, V['bp']),
    ]

    def face(d):
        d.arc(C, C, 232, 0, 359.9, (34, 38, 48), 4.5, cap=False)
        d.arc(C, C, 232, 0, V['sec'] * 6, amber, 4.5)

        # Date + Giant crisp digits directly on pure OLED black
        d.text(C, 70, f"{V['dowf']} · {V['date']}", 28, 600, amber, spacing=0.06)
        d.text(C - 16, 156, V['hh'], 152, 700, WHITE, 'r')
        d.text(C + 16, 156, V['mm'], 152, 700, WHITE, 'l')
        for dy in (-20, 20):
            d.rect(C - 5.5, 156 + dy - 5.5, C + 5.5, 156 + dy + 5.5, 3, fill=coral)

        # 3 solid color keys below
        for i, (_, val, lab, col, prog) in enumerate(tiles):
            x0 = 56 + i * 125
            d.rect(x0, 234, x0 + 118, 340, 22, fill=col)
            d.text(x0 + 104, 253, lab, 17, 700, mix(col, INK, 0.78), 'r', spacing=0.08)
            d.text(x0 + 59, 293, val, 44, 700, INK)
            if prog is not None:
                d.rect(x0 + 16, 323, x0 + 102, 329, 3, fill=mix(col, INK, 0.25))
                d.rect(x0 + 16, 323, x0 + 16 + 86 * prog, 329, 3, fill=INK)

        # Two tinted complication keys below (subtle dark-tinted fill matching the key grid)
        for x0, val, bg in ((118, V['bell'], (28, 42, 62)), (244, V['sun'], (54, 44, 24))):
            d.rect(x0, 348, x0 + 118, 404, 20, fill=bg)
            d.text(x0 + 75, 376, val, 30, 600, WHITE)

    c.paint(face)
    for i, (ic, _, _, _, _) in enumerate(tiles):
        c.icon(ic, 56 + i * 125 + 25, 255, 22, INK)
    c.icon('bell', 146, 376, 21, cyan)
    c.icon('sun', 270, 375, 21, amber)
    return c.finish()


VARIANTS = [
    ('B1', 'BENTO SCURO', 'Blocco ora antracite e tacche secondi: meno luce, più contrasto OLED', b1_bento_scuro),
    ('B2', 'ASIMMETRICO', 'Ora verticale a sinistra + colonna tessere a destra: griglia bento vera', b2_asymmetric),
    ('B3', 'SWISS / BRAUN', 'Evoluzione pulita di B: margini corretti e palette editoriale calma', b3_swiss),
    ('B4', 'TASTIERA OLED', 'Ora gigante su nero puro + tastiera modulare colorata sotto', b4_tastiera_oled),
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

    out_path = OUT / 'confronto-mosaico.png'
    sheet.save(out_path)
    print('Saved:', out_path)
