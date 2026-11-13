"""Generate ECLISSE: the Watch Face Format XML and a faithful preview, from one scene.

Every shape is declared once and sent to two backends: the WFF document installed
on the watch, and a Pillow painter that composes the same layers into a preview.
The preview is a simulation with sample values; the watch shows real data.
"""
from pathlib import Path
import math
import sys
from xml.etree import ElementTree as ET
from PIL import Image, ImageDraw, ImageFont

from layout import (S, C, R, ORBIT, RM, ICON, STAR_PAD, HANDS, polar, MOON_SLOT_LEFT,
                    MOON_SLOT_RIGHT, MOON_STEPS, MOON_HEART, MOON_BATTERY)

ROOT = Path(__file__).resolve().parents[1]
K = 3  # preview supersampling

# id, display name, accent, dim, hot
THEMES = [
    ('oro', 'Corona · Oro', '#FFFFC56E', '#FF8A6630', '#FFFFF4DE'),
    ('plasma', 'Plasma · Magenta', '#FFFF4F9E', '#FF8A2A55', '#FFFFE3EF'),
    ('aurora', 'Aurora · Verde', '#FF3DF5B0', '#FF1F7A58', '#FFE0FFF3'),
    ('zaffiro', 'Zaffiro · Blu', '#FF5B9DFF', '#FF2A4C8A', '#FFE2EDFF'),
    ('brace', 'Brace · Rosso', '#FFFF5B38', '#FF8A301D', '#FFFFE7DD'),
    ('luna', 'Luna · Argento', '#FFD5E0F2', '#FF5D6676', '#FFFFFFFF'),
]
TOKENS = {'ACCENT': 0, 'DIM': 1, 'HOT': 2}
INK = '#FFF6F4EF'
WHITE = '#FFFFFFFF'
SOFT = '#FFD2D5DD'
TRACK = '#FF343A48'     # empty part of a progress ring
BORDER = '#FF667086'    # outline that makes a moon read as a button
BLACK = '#FF000000'

SAMPLE = dict(hour=9, minute=27, second=6, steps=6480, goal=10000, heart=72, battery=84,
              weekday='GIOVEDÌ', date='12 NOV')
FONTS = {'teko_regular': 'NORMAL', 'teko_semibold': 'SEMI_BOLD'}
# Teko vertical metrics (hhea ascent 0.958, descent 0.475, cap height 0.622): the line box
# is centred in its part, so the capitals sit 0.0695 em above the centre of the box.
CAP_SHIFT = 0.0695
BASELINE = (0.958 - 0.475) / 2


def el(parent, tag, **attrs):
    return ET.SubElement(parent, tag, {k: fmt(v) for k, v in attrs.items()})


def fmt(v):
    if isinstance(v, float):
        return ('%.3f' % v).rstrip('0').rstrip('.')
    return str(v)


def xml_color(c):
    return f'[CONFIGURATION.corona.{TOKENS[c]}]' if c in TOKENS else c


class Painter:
    """Pillow backend. Paints only what is visible in the requested mode."""

    def __init__(self, mode, theme):
        self.mode = mode
        self.theme = theme
        self.img = Image.new('RGBA', (S * K, S * K), (0, 0, 0, 255))
        self.draw = ImageDraw.Draw(self.img)
        self.fonts = {}

    def rgb(self, c, alpha=1.0):
        h = self.theme[2 + TOKENS[c]] if c in TOKENS else c
        h = h.lstrip('#')[-6:]
        return tuple(round(int(h[i:i + 2], 16) * alpha) for i in (0, 2, 4)) + (255,)

    def font(self, family, size):
        key = (family, round(size * K, 2))
        if key not in self.fonts:
            self.fonts[key] = ImageFont.truetype(str(ROOT / f'res/font/{family}.ttf'), size * K)
        return self.fonts[key]

    def image(self, name, x, y, w, h, tint=None, angle=0):
        src = Image.open(ROOT / f'res/drawable/{name}.png').convert('RGBA')
        src = src.resize((round(w * K), round(h * K)), Image.BICUBIC)
        if tint:
            r, g, b, _ = self.rgb(tint)
            solid = Image.new('RGBA', src.size, (r, g, b, 255))
            solid.putalpha(src.getchannel('A'))
            src = solid
        layer = Image.new('RGBA', self.img.size, (0, 0, 0, 0))
        layer.paste(src, (round(x * K), round(y * K)))
        if angle:
            layer = layer.rotate(-angle, Image.BICUBIC, center=(C * K, C * K))
        self.img.alpha_composite(layer)
        self.draw = ImageDraw.Draw(self.img)


class Node:
    """A WFF element plus the absolute origin and visibility needed to preview it."""

    def __init__(self, node, painter, ox=0, oy=0, w=S, h=S, vis='both', alpha=1.0):
        self.node, self.p = node, painter
        self.ox, self.oy, self.w, self.h = ox, oy, w, h
        self.vis, self.alpha = vis, alpha

    @property
    def shown(self):
        return self.vis in ('both', self.p.mode)

    def child(self, node, x=0, y=0, w=None, h=None, vis=None, alpha=None):
        return Node(node, self.p, self.ox + x, self.oy + y, w or self.w, h or self.h,
                    vis or self.vis, self.alpha if alpha is None else alpha)

    def ambient(self, node, value):
        el(node, 'Variant', mode='AMBIENT', target='alpha', value=value)

    def group(self, name, x=0, y=0, w=S, h=S, vis='both', preview=True, **attrs):
        """vis: 'active' hides the group in ambient, 'ambient' shows it only there.
        preview=False keeps a conditional group out of the preview image."""
        if vis == 'ambient':
            attrs['alpha'] = 0
        g = el(self.node, 'Group', name=name, x=x, y=y, width=w, height=h, **attrs)
        if vis == 'active':
            self.ambient(g, 0)
        elif vis == 'ambient':
            self.ambient(g, 255)
        shown = vis if self.vis == 'both' else self.vis
        return self.child(g, x, y, w, h, shown if preview else 'never')

    def part_draw(self):
        return self.child(el(self.node, 'PartDraw', x=0, y=0, width=self.w, height=self.h))

    # ---- shapes -------------------------------------------------------------
    def _xy(self, x, y):
        return (self.ox + x) * K, (self.oy + y) * K

    def ellipse(self, cx, cy, rx, ry=None, fill=None, stroke=None, thickness=1.0):
        ry = rx if ry is None else ry
        e = el(self.node, 'Ellipse', x=float(cx - rx), y=float(cy - ry), width=float(rx * 2), height=float(ry * 2))
        if fill:
            el(e, 'Fill', color=xml_color(fill))
        if stroke:
            el(e, 'Stroke', color=xml_color(stroke), thickness=float(thickness))
        if not self.shown:
            return
        X, Y = self._xy(cx, cy)
        if fill:
            self.p.draw.ellipse([X - rx * K, Y - ry * K, X + rx * K, Y + ry * K], fill=self.p.rgb(fill, self.alpha))
        if stroke:
            o = thickness / 2
            self.p.draw.ellipse([X - (rx + o) * K, Y - (ry + o) * K, X + (rx + o) * K, Y + (ry + o) * K],
                                outline=self.p.rgb(stroke, self.alpha), width=max(1, round(thickness * K)))

    def line(self, x1, y1, x2, y2, color, thickness=1.0, cap='ROUND'):
        l = el(self.node, 'Line', startX=float(x1), startY=float(y1), endX=float(x2), endY=float(y2))
        el(l, 'Stroke', color=xml_color(color), thickness=float(thickness), cap=cap)
        if not self.shown:
            return
        a, b = self._xy(x1, y1), self._xy(x2, y2)
        c = self.p.rgb(color, self.alpha)
        self.p.draw.line([a, b], fill=c, width=max(1, round(thickness * K)))
        if cap == 'ROUND':
            r = thickness * K / 2
            for X, Y in (a, b):
                self.p.draw.ellipse([X - r, Y - r, X + r, Y + r], fill=c)

    def arc(self, cx, cy, r, start, end, color, thickness, expr=None):
        """`end` is the preview value; `expr` drives the live end angle on the watch."""
        a = el(self.node, 'Arc', centerX=float(cx), centerY=float(cy), width=float(r * 2), height=float(r * 2),
               startAngle=float(start), endAngle=float(start if expr else end), direction='CLOCKWISE')
        if expr:
            el(a, 'Transform', target='endAngle', value=expr)
        el(a, 'Stroke', color=xml_color(color), thickness=float(thickness), cap='ROUND')
        if not self.shown or end <= start:
            return
        X, Y = self._xy(cx, cy)
        c = self.p.rgb(color, self.alpha)
        o = r + thickness / 2
        self.p.draw.arc([X - o * K, Y - o * K, X + o * K, Y + o * K], start - 90, end - 90, fill=c,
                        width=max(1, round(thickness * K)))
        for ang in (start, end):
            ex = X + r * K * math.sin(math.radians(ang))
            ey = Y - r * K * math.cos(math.radians(ang))
            rr = thickness * K / 2
            self.p.draw.ellipse([ex - rr, ey - rr, ex + rr, ey + rr], fill=c)

    # ---- text ---------------------------------------------------------------
    def text(self, cx, cap_cy, width, size, color, sample, template=None, params=(), family='teko_semibold',
             spacing=None, upper=False, ambient=None):
        """Single centred line whose capitals are centred on `cap_cy`."""
        height = math.ceil(size * 1.5)
        x = round(cx - width / 2)          # part geometry is integer in WFF
        y = round(cap_cy + CAP_SHIFT * size - height / 2)
        cx = x + width / 2
        p = el(self.node, 'PartText', x=x, y=y, width=int(width), height=height)
        if ambient is not None:
            self.ambient(p, ambient)
        t = el(p, 'Text', align='CENTER', maxLines=1, ellipsis='TRUE')
        attrs = dict(family=family, size=float(size), weight=FONTS[family], color=xml_color(color))
        if spacing is not None:
            attrs['letterSpacing'] = float(spacing)
        f = el(t, 'Font', **attrs)
        host = el(f, 'Upper') if upper else f
        if params:
            tpl = el(host, 'Template')
            tpl.text = template or '%s'
            for expression in params:
                el(tpl, 'Parameter', expression=expression)
        else:
            host.text = sample
        if not self.shown:
            return
        alpha = self.alpha * ((ambient / 255) if (ambient is not None and self.p.mode == 'ambient') else 1)
        font = self.p.font(family, size)
        gap = (spacing or 0) * size * K
        widths = [font.getlength(ch) for ch in sample]
        total = sum(widths) + gap * len(sample)
        X = (self.ox + cx) * K - total / 2 + gap / 2
        Y = (self.oy + y + height / 2 + BASELINE * size) * K
        for ch, w in zip(sample, widths):
            self.p.draw.text((X, Y), ch, font=font, fill=self.p.rgb(color, alpha), anchor='ls')
            X += w + gap

    # ---- bitmaps ------------------------------------------------------------
    def image(self, name, x, y, w, h, tint=None, gyro=None):
        attrs = dict(x=x, y=y, width=w, height=h)
        if tint:
            attrs['tintColor'] = xml_color(tint)
        im = el(self.node, 'PartImage', **attrs)
        if gyro:
            el(im, 'Gyro', x=gyro.format(axis='X'), y=gyro.format(axis='Y'))
        el(im, 'Image', resource=name)
        if self.shown:
            self.p.image(name, self.ox + x, self.oy + y, w, h, tint)

    def hand(self, kind, name, angle, tint, sweep=False):
        x, y, w, h = HANDS[name]
        hnd = el(self.node, kind, resource=name, x=x, y=y, width=w, height=h,
                 pivotX=float((C - x) / w), pivotY=float((C - y) / h), tintColor=xml_color(tint))
        if sweep:
            el(hnd, 'Sweep', frequency='15')
        if self.shown:
            self.p.image(name, x, y, w, h, tint, angle)


# ---------------------------------------------------------------------------
def moon_body(d, progress=None, sample=0.0):
    """A dark satellite in front of the corona, with an optional progress ring."""
    d.ellipse(RM, RM, RM, fill=BLACK)
    if progress:
        d.ellipse(RM, RM, RM - 3.5, stroke=TRACK, thickness=5.0)
        d.arc(RM, RM, RM - 3.5, 0, 359.9 * sample, 'ACCENT', 5.0, expr=progress)
    else:
        d.ellipse(RM, RM, RM - 2, stroke=BORDER, thickness=2.0)


ICON_Y = RM - 33       # top of the 24 px icon inside a moon
VALUE_Y = RM + 10      # centre of the capitals of the value


def data_moon(parent, name, angle, launch, icon, progress, sample_progress, values):
    """values: (size, sample, template, params, alpha condition or None, shown in preview)."""
    mx, my = polar(angle, ORBIT)
    g = parent.group(name, round(mx - RM), round(my - RM), RM * 2, RM * 2)
    el(g.node, 'Launch', target=launch)
    moon_body(g.part_draw(), progress, sample_progress)
    g.image(icon, RM - ICON // 2, ICON_Y, ICON, ICON, tint='ACCENT')
    for i, (size, sample, template, params, condition, preview) in enumerate(values):
        host = g
        if condition:
            host = g.group(f'{name}_size{i}', 0, 0, RM * 2, RM * 2, preview=preview)
            el(host.node, 'Transform', target='alpha', value=condition)
        host.text(RM, VALUE_Y, RM * 2 - 8, size, WHITE, sample, template, params)


def complication_moon(scene, angle, slot_id, name, provider, sample_icon, sample_text):
    mx, my = polar(angle, ORBIT)
    x, y = round(mx - RM), round(my - RM)
    s = el(scene.node, 'ComplicationSlot', x=x, y=y, width=RM * 2, height=RM * 2, slotId=slot_id,
           displayName=name, isCustomizable='TRUE',
           supportedTypes='SHORT_TEXT RANGED_VALUE MONOCHROMATIC_IMAGE SMALL_IMAGE EMPTY')
    scene.ambient(s, 0)
    el(s, 'BoundingOval', x=0, y=0, width=RM * 2, height=RM * 2)
    el(s, 'DefaultProviderPolicy', defaultSystemProvider=provider, defaultSystemProviderType='SHORT_TEXT')
    silent = Painter('none', scene.p.theme)   # only the SHORT_TEXT layout is previewed
    for kind in ('SHORT_TEXT', 'RANGED_VALUE', 'MONOCHROMATIC_IMAGE', 'SMALL_IMAGE', 'EMPTY'):
        live = kind == 'SHORT_TEXT'
        c = Node(el(s, 'Complication', type=kind), scene.p if live else silent, x, y, RM * 2, RM * 2, 'active')
        d = c.part_draw()
        if kind == 'RANGED_VALUE':
            moon_body(d, '359.9 * clamp(([COMPLICATION.RANGED_VALUE_VALUE] - [COMPLICATION.RANGED_VALUE_MIN]) / '
                         'clamp([COMPLICATION.RANGED_VALUE_MAX] - [COMPLICATION.RANGED_VALUE_MIN], 1, 1000000000), 0, 1)')
        else:
            moon_body(d)
        if kind in ('SHORT_TEXT', 'RANGED_VALUE'):
            im = el(c.node, 'PartImage', x=RM - ICON // 2, y=ICON_Y, width=ICON, height=ICON,
                    tintColor=xml_color('ACCENT'))
            el(im, 'Image', resource='[COMPLICATION.MONOCHROMATIC_IMAGE]')
            if live:
                sample_icon(d_preview(c), RM, ICON_Y + ICON / 2)
            c.text(RM, VALUE_Y, RM * 2 - 12, 30, WHITE, sample_text, '%s', ['[COMPLICATION.TEXT]'])
        elif kind == 'MONOCHROMATIC_IMAGE':
            im = el(c.node, 'PartImage', x=RM - 21, y=RM - 21, width=42, height=42, tintColor=xml_color('ACCENT'))
            el(im, 'Image', resource='[COMPLICATION.MONOCHROMATIC_IMAGE]')
        elif kind == 'SMALL_IMAGE':
            im = el(c.node, 'PartImage', x=RM - 27, y=RM - 27, width=54, height=54)
            el(im, 'Image', resource='[COMPLICATION.SMALL_IMAGE]')


def d_preview(c):
    """Preview-only drawing surface: stands in for the icon a provider would send."""
    return Node(ET.Element('Preview'), c.p, c.ox, c.oy, c.w, c.h, c.vis)


def icon_bell(d, cx, cy):
    d.arc(cx, cy, 7.2, -90, 90, 'ACCENT', 2.8)
    d.line(cx - 7.2, cy, cx - 7.2, cy + 5.0, 'ACCENT', 2.8)
    d.line(cx + 7.2, cy, cx + 7.2, cy + 5.0, 'ACCENT', 2.8)
    d.line(cx - 10, cy + 6.5, cx + 10, cy + 6.5, 'ACCENT', 2.8)
    d.ellipse(cx, cy + 10.5, 2.0, fill='ACCENT')


def icon_sun(d, cx, cy):
    d.arc(cx, cy + 5, 6.2, -90, 90, 'ACCENT', 2.8)
    d.line(cx - 11, cy + 7, cx + 11, cy + 7, 'ACCENT', 2.6)
    for ang in (-60, 0, 60):
        s, c = math.sin(math.radians(ang)), -math.cos(math.radians(ang))
        d.line(cx + s * 9.6, cy + 5 + c * 9.6, cx + s * 12.6, cy + 5 + c * 12.6, 'ACCENT', 2.4)


def build(mode, theme):
    v = SAMPLE
    painter = Painter(mode, theme)
    wf = ET.Element('WatchFace', width=str(S), height=str(S), clipShape='CIRCLE')
    el(wf, 'Metadata', key='CLOCK_TYPE', value='DIGITAL')
    el(wf, 'Metadata', key='PREVIEW_TIME', value='%02d:%02d:%02d' % (v['hour'], v['minute'], v['second']))
    configs = el(wf, 'UserConfigurations')
    palette = el(configs, 'ColorConfiguration', id='corona', displayName='theme_color_name', defaultValue=THEMES[0][0])
    for key, _, accent, dim, hot in THEMES:
        el(palette, 'ColorOption', id=key, displayName='color_' + key, colors=f'{accent} {dim} {hot}')
    scene = Node(el(wf, 'Scene', backgroundColor=BLACK), painter)

    # 1 · Deep sky. Two star layers drift at different speeds as the wrist tilts.
    sky = scene.group('sky', vis='active')
    side = S + 2 * STAR_PAD
    sky.image('stars_far', -STAR_PAD, -STAR_PAD, side, side,
              gyro='clamp([ACCELEROMETER_ANGLE_{axis}], -40, 40) * 0.14')
    sky.image('stars_near', -STAR_PAD, -STAR_PAD, side, side,
              gyro='clamp([ACCELEROMETER_ANGLE_{axis}], -40, 40) * 0.34')

    # 2 · The corona. It leans the opposite way, like light behind an occluder.
    glow = scene.group('corona', vis='active')
    glow.image('corona', 0, 0, S, S, tint='ACCENT', gyro='clamp([ACCELEROMETER_ANGLE_{axis}], -40, 40) * -0.09')

    # 3 · Hours and minutes are two rays of the corona itself.
    rays = scene.group('rays', vis='active')
    clock = rays.child(el(rays.node, 'AnalogClock', x=0, y=0, width=S, height=S))
    clock.hand('HourHand', 'hand_hour', (v['hour'] % 12) * 30 + v['minute'] * 0.5, 'HOT')
    clock.hand('MinuteHand', 'hand_minute', v['minute'] * 6 + v['second'] * 0.1, 'HOT')
    rays.image('limb', 0, 0, S, S, tint='HOT')

    # 4 · The Moon: pure OLED black.
    scene.part_draw().ellipse(C, C, R, fill=BLACK)

    # 5 · Seconds: the diamond-ring bead sweeps the lunar edge at 15 fps.
    beads = scene.group('bead', vis='active')
    clock2 = beads.child(el(beads.node, 'AnalogClock', x=0, y=0, width=S, height=S))
    clock2.hand('SecondHand', 'hand_second', v['second'] * 6, 'HOT', sweep=True)

    # 6 · Time. Fixed columns keep the proportional digits from jumping.
    face = scene.group('time')
    hh, mm = '%02d' % v['hour'], '%02d' % v['minute']
    for cx, sample, expr in [(148, hh[0], 'floor([HOUR_0_23] / 10)'), (202, hh[1], '[HOUR_0_23] % 10'),
                             (278, mm[0], 'floor([MINUTE] / 10)'), (332, mm[1], '[MINUTE] % 10')]:
        face.text(cx, 242, 56, 134, INK, sample, '%s', [expr], family='teko_regular')
    dots = face.part_draw()
    for dy in (-17, 17):
        dots.ellipse(C, 242 + dy, 5.2, fill='ACCENT')
    # No letterSpacing here: on the Galaxy Watch it draws seams inside glyphs with overlapping contours (G, O).
    face.text(C, 163, 210, 33, 'ACCENT', v['weekday'], '%s', ['[DAY_OF_WEEK_F]'], upper=True, ambient=190)
    face.text(C, 321, 200, 33, SOFT, v['date'], '%s %s', ['[DAY]', '[MONTH_S]'], upper=True, ambient=190)

    # 7 · Three satellite moons with live data; each one is an 86 px button.
    moons = scene.group('moons', vis='active')
    data_moon(moons, 'steps', MOON_STEPS, 'com.samsung.android.wear.shealth/com.samsung.android.wear.shealth.app.home.HomeActivity',
              'ic_steps', '359.9 * clamp([STEP_COUNT] / clamp([STEP_GOAL], 1, 1000000), 0, 1)', v['steps'] / v['goal'],
              [(32, str(v['steps']), '%s', ['[STEP_COUNT]'], '[STEP_COUNT] < 10000 ? 255 : 0', v['steps'] < 10000),
               (26, str(v['steps']), '%s', ['[STEP_COUNT]'], '[STEP_COUNT] < 10000 ? 0 : 255', v['steps'] >= 10000)])
    data_moon(moons, 'heart', MOON_HEART, 'HEALTH_HEART_RATE', 'ic_heart', None, 0,
              [(38, str(v['heart']), '%s', ["[HEART_RATE] > 0 ? [HEART_RATE] : '--'"], None, True)])
    data_moon(moons, 'battery', MOON_BATTERY, 'BATTERY_STATUS', 'ic_battery',
              '3.599 * clamp([BATTERY_PERCENT], 0, 100)', v['battery'] / 100,
              [(32, '%d%%' % v['battery'], '%s%%', ['[BATTERY_PERCENT]'], None, True)])

    # 8 · Two more moons are free complication slots.
    complication_moon(scene, MOON_SLOT_LEFT, 0, 'slot_left_name', 'UNREAD_NOTIFICATION_COUNT', icon_bell, '3')
    complication_moon(scene, MOON_SLOT_RIGHT, 1, 'slot_right_name', 'SUNRISE_SUNSET', icon_sun, '07:12')

    # 9 · Always-on: only a hairline annulus stays lit around the time.
    aod = scene.group('annulus', vis='ambient').part_draw()
    aod.ellipse(C, C, R, stroke='DIM', thickness=1.5)

    return wf, painter.img.resize((S, S), Image.LANCZOS)


def round_mask(img):
    mask = Image.new('L', (S * K, S * K), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, S * K - 1, S * K - 1], fill=255)
    out = Image.new('RGBA', (S, S), (0, 0, 0, 255))
    out.paste(img, (0, 0), mask.resize((S, S), Image.LANCZOS))
    return out.convert('RGB')


if __name__ == '__main__':
    wf, active = build('active', THEMES[0])
    ET.indent(wf, space='    ')
    for node in wf.iter():      # text content is mixed XML: keep indentation out of the rendered strings
        if node.tag in ('Font', 'Upper', 'Template') and len(node):
            if node.tag != 'Template':
                node.text = None
            for inner in node:
                inner.tail = None
    ET.ElementTree(wf).write(ROOT / 'res/raw/watchface.xml', encoding='utf-8', xml_declaration=True)
    print('Generated:', ROOT / 'res/raw/watchface.xml')
    round_mask(active).save(ROOT / 'res/drawable/preview.png', optimize=True)
    round_mask(active).save(ROOT / 'design/preview-oro.png')
    round_mask(build('ambient', THEMES[0])[1]).save(ROOT / 'design/preview-ambient.png')
    if '--all' in sys.argv:
        sheet = Image.new('RGB', (S * 3, S * 2), (0, 0, 0))
        for i, theme in enumerate(THEMES):
            img = round_mask(build('active', theme)[1])
            img.save(ROOT / f'design/preview-{theme[0]}.png')
            sheet.paste(img, (S * (i % 3), S * (i // 3)))
        sheet.save(ROOT / 'design/preview-themes.png')
    print('Preview: design/preview-oro.png, design/preview-ambient.png')
