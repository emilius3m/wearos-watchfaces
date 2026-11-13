"""Generate SOLARI: the Watch Face Format 2 XML and faithful previews from one scene."""
from pathlib import Path
import math
import sys
from xml.etree import ElementTree as ET
from PIL import Image, ImageDraw, ImageFont

from layout import (
    S, C, ARC_R, ARC_W, DOT_ORBIT, DATE_X, DATE_Y, DATE_W, DATE_H, DATE_R,
    FLIP_X, FLIP_W, FLIP_H, FLIP_R, HOUR_Y, MIN_Y, PIN, FLIP_FRAMES,
    TILE_X, TILE_W, TILE_H, TILE_R, HEART_Y, BATT_Y, STEPS_Y, BAR_X, BAR_W, BAR_H, ICON,
    BOT_Y, BOT_H, BOT_R, SLOT_X, SLOT_W, WX_X, WX_W, MIC_X, MIC_SIZE, MIC_ICON,
)

ROOT = Path(__file__).resolve().parents[1]
K = 3  # preview supersampling

# id, display name, crown_accent, minute_accent
THEMES = [
    ('ambra', 'Solari · Ambra', '#FFFFBE40', '#FFFF6068'),
    ('corallo', 'Corallo · Caldo', '#FFFF6068', '#FFFFBE40'),
    ('giada', 'Giada · Verde', '#FF4AD69E', '#FF4AD69E'),
    ('cobalto', 'Cobalto · Blu', '#FF68B0FF', '#FF68B0FF'),
    ('avorio', 'Avorio · Mono', '#FFF4EEE0', '#FFF4EEE0'),
]
TOKENS = {'CROWN': 0, 'MINUTE_COL': 1}

CREAM = '#FFF4EEE0'
WHITE = '#FFFFFFFF'
SLATE = '#FF161A23'
TILE_BG = '#FF181B23'
BORDER = '#FF3A4256'
TILE_EDGE = '#FF343A4A'
TRACK = '#FF2C3242'
CORAL = '#FFFF6068'
AMBER = '#FFFFC638'
SAGE = '#FF4AD69E'
SKY = '#FF76B2FF'
BLACK = '#FF000000'
AOD_EDGE = '#FF3C414E'

SAMPLE = dict(
    hour=9, minute=27, second=36,
    steps=6480, goal=10000, heart=72, battery=84,
    weekday='GIOVEDÌ', day=12, month='NOV',
    weather=dict(icon='partly', temperature=14),
)
FONTS = {'teko_semibold': 'SEMI_BOLD', 'teko_bold': 'BOLD'}
CAP_SHIFT = 0.0695
BASELINE = (0.958 - 0.475) / 2
HEALTH = 'com.samsung.android.wear.shealth/com.samsung.android.wear.shealth.app.home.HomeActivity'
RECORDER = 'com.samsung.android.wear.voicerecorder/com.samsung.android.wear.voicerecorder.view.MainActivity'
DARK_INK = '#FF12141A'


def fmt(v):
    if isinstance(v, float):
        return ('%.3f' % v).rstrip('0').rstrip('.')
    return str(v)


def el(parent, tag, **attrs):
    return ET.SubElement(parent, tag, {k: fmt(v) for k, v in attrs.items()})


def xml_color(c):
    return f'[CONFIGURATION.theme.{TOKENS[c]}]' if c in TOKENS else c


class Painter:
    """Pillow backend. Paints only what is visible in the requested mode."""

    def __init__(self, mode, theme):
        self.mode = mode
        self.theme = theme
        self.img = Image.new('RGBA', (S * K, S * K), (0, 0, 0, 255))
        self.fonts = {}

    def rgba(self, c, alpha=1.0):
        h = (self.theme[2 + TOKENS[c]] if c in TOKENS else c).lstrip('#')
        a = int(h[:2], 16) if len(h) == 8 else 255
        h = h[-6:]
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (round(a * alpha),)

    def shape(self, color, alpha, fn):
        col = self.rgba(color, alpha)
        if col[3] == 255:
            fn(ImageDraw.Draw(self.img), col)
        else:
            layer = Image.new('RGBA', self.img.size, (0, 0, 0, 0))
            fn(ImageDraw.Draw(layer), col)
            self.img.alpha_composite(layer)

    def font(self, family, size):
        key = (family, round(size * K, 2))
        if key not in self.fonts:
            self.fonts[key] = ImageFont.truetype(str(ROOT / f'res/font/{family}.ttf'), size * K)
        return self.fonts[key]

    def image(self, name, x, y, w, h, tint=None, angle=0):
        src = Image.open(ROOT / f'res/drawable/{name}.png').convert('RGBA')
        src = src.resize((round(w * K), round(h * K)), Image.BICUBIC)
        if tint:
            r, g, b, _ = self.rgba(tint)
            solid = Image.new('RGBA', src.size, (r, g, b, 255))
            solid.putalpha(src.getchannel('A'))
            src = solid
        layer = Image.new('RGBA', self.img.size, (0, 0, 0, 0))
        layer.paste(src, (round(x * K), round(y * K)))
        if angle:
            layer = layer.rotate(-angle, Image.BICUBIC, center=(C * K, C * K))
        self.img.alpha_composite(layer)


class Node:
    """WFF element + preview coordinates and mode visibility."""

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

    def group(self, name, x=0, y=0, w=S, h=S, vis='both', preview=True, launch=None, **attrs):
        if vis == 'ambient':
            attrs['alpha'] = 0
        g = el(self.node, 'Group', name=name, x=x, y=y, width=w, height=h, **attrs)
        if launch:
            el(g, 'Launch', target=launch)
        if vis == 'active':
            self.ambient(g, 0)
        elif vis == 'ambient':
            self.ambient(g, 255)
        shown = vis if self.vis == 'both' else self.vis
        return self.child(g, x, y, w, h, shown if preview else 'never')

    def part_draw(self):
        return self.child(el(self.node, 'PartDraw', x=0, y=0, width=self.w, height=self.h))

    def _box(self, x, y, w, h, grow=0.0):
        return [(self.ox + x - grow) * K, (self.oy + y - grow) * K,
                (self.ox + x + w + grow) * K - 1, (self.oy + y + h + grow) * K - 1]

    # ---- shapes -------------------------------------------------------------
    def rrect(self, x, y, w, h, r, fill=None, stroke=None, thickness=1.0):
        e = el(self.node, 'RoundRectangle', x=float(x), y=float(y), width=float(w), height=float(h),
               cornerRadiusX=float(r), cornerRadiusY=float(r))
        if fill:
            el(e, 'Fill', color=xml_color(fill))
        if stroke:
            el(e, 'Stroke', color=xml_color(stroke), thickness=float(thickness))
        if not self.shown:
            return
        if fill:
            self.p.shape(fill, self.alpha, lambda d, c: d.rounded_rectangle(self._box(x, y, w, h), radius=r * K, fill=c))
        if stroke:
            o = thickness / 2
            self.p.shape(stroke, self.alpha, lambda d, c: d.rounded_rectangle(
                self._box(x, y, w, h, o), radius=(r + o) * K, outline=c, width=max(1, round(thickness * K))))

    def rect_bar(self, x, y, w, h, r, fill, expr=None, sample=1.0):
        """Rounded bar whose width can be driven dynamically by `expr`."""
        e = el(self.node, 'RoundRectangle', x=float(x), y=float(y), width=float(w), height=float(h),
               cornerRadiusX=float(r), cornerRadiusY=float(r))
        if expr:
            el(e, 'Transform', target='width', value=expr)
        el(e, 'Fill', color=xml_color(fill))
        if self.shown and w * sample > 0:
            self.p.shape(fill, self.alpha,
                         lambda d, c: d.rounded_rectangle(self._box(x, y, w * sample, h), radius=r * K, fill=c))

    def hline(self, x, y, w, color, thickness=1.0):
        l = el(self.node, 'Line', startX=float(x), startY=float(y), endX=float(x + w), endY=float(y))
        el(l, 'Stroke', color=xml_color(color), thickness=float(thickness), cap='BUTT')
        if self.shown:
            self.p.shape(color, self.alpha,
                         lambda d, c: d.rectangle(self._box(x, y - thickness / 2, w, thickness), fill=c))

    def arc(self, cx, cy, r, start, end, color, thickness, expr=None):
        a = el(self.node, 'Arc', centerX=float(cx), centerY=float(cy), width=float(r * 2), height=float(r * 2),
               startAngle=float(start), endAngle=float(start if expr else end), direction='CLOCKWISE')
        if expr:
            el(a, 'Transform', target='endAngle', value=expr)
        el(a, 'Stroke', color=xml_color(color), thickness=float(thickness), cap='ROUND')
        if not self.shown or end <= start:
            return

        def draw(d, c):
            X, Y = (self.ox + cx) * K, (self.oy + cy) * K
            o = r + thickness / 2
            d.arc([X - o * K, Y - o * K, X + o * K, Y + o * K], start - 90, end - 90, fill=c,
                  width=max(1, round(thickness * K)))
            rr = thickness * K / 2
            for ang in (start, end):
                ex = X + r * K * math.sin(math.radians(ang))
                ey = Y - r * K * math.cos(math.radians(ang))
                d.ellipse([ex - rr, ey - rr, ex + rr, ey + rr], fill=c)

        self.p.shape(color, self.alpha, draw)

    def line(self, x1, y1, x2, y2, color, thickness=1.0):
        l = el(self.node, 'Line', startX=float(x1), startY=float(y1), endX=float(x2), endY=float(y2))
        el(l, 'Stroke', color=xml_color(color), thickness=float(thickness), cap='ROUND')
        if self.shown:
            self.p.shape(color, self.alpha, lambda d, c: d.line(
                [(self.ox + x1) * K, (self.oy + y1) * K, (self.ox + x2) * K, (self.oy + y2) * K],
                fill=c, width=max(1, round(thickness * K))))

    def ellipse(self, cx, cy, rx, ry=None, fill=None):
        ry = rx if ry is None else ry
        e = el(self.node, 'Ellipse', x=float(cx - rx), y=float(cy - ry), width=float(rx * 2), height=float(ry * 2))
        if fill:
            el(e, 'Fill', color=xml_color(fill))
        if self.shown and fill:
            self.p.shape(fill, self.alpha, lambda d, c: d.ellipse(self._box(cx - rx, cy - ry, 2 * rx, 2 * ry), fill=c))

    # ---- text ---------------------------------------------------------------
    def text(self, cx, cap_cy, width, size, color, sample, template='%s', params=(),
             family='teko_semibold', upper=False, ambient=None):
        height = math.ceil(size * 1.5)
        x = round(cx - width / 2)
        y = round(cap_cy + CAP_SHIFT * size - height / 2)
        cx = x + width / 2
        p = el(self.node, 'PartText', x=x, y=y, width=int(width), height=height)
        if ambient is not None:
            self.ambient(p, ambient)
        t = el(p, 'Text', align='CENTER', maxLines=1, ellipsis='TRUE')
        f = el(t, 'Font', family=family, size=float(size), weight=FONTS[family], color=xml_color(color))
        host = el(f, 'Upper') if upper else f
        if params:
            tpl = el(host, 'Template')
            tpl.text = template
            for expression in params:
                el(tpl, 'Parameter', expression=expression)
        else:
            host.text = template
        if not self.shown:
            return
        alpha = self.alpha * ((ambient / 255) if (ambient is not None and self.p.mode == 'ambient') else 1)
        self.p.shape(color, alpha, lambda d, c: d.text(
            ((self.ox + cx) * K, (self.oy + y + height / 2 + BASELINE * size) * K),
            sample, font=self.p.font(family, size), fill=c, anchor='ms'))

    # ---- bitmaps & animations -----------------------------------------------
    def image(self, name, x, y, w, h, tint=None):
        attrs = dict(x=x, y=y, width=w, height=h)
        if tint:
            attrs['tintColor'] = xml_color(tint)
        el(el(self.node, 'PartImage', **attrs), 'Image', resource=name)
        if self.shown:
            self.p.image(name, self.ox + x, self.oy + y, w, h, tint)

    def hand(self, kind, name, x, y, w, h, angle, tint):
        hnd = el(self.node, kind, resource=name, x=x, y=y, width=w, height=h,
                 pivotX=float((C - x) / w), pivotY=float((C - y) / h), tintColor=xml_color(tint))
        if self.shown:
            self.p.image(name, x, y, w, h, tint, angle)

    def flip(self, prefix, frames, x, y, w, h, trigger, fps):
        part = el(self.node, 'PartAnimatedImage', x=x, y=y, width=w, height=h)
        el(part, 'AnimationController', play=trigger, beforePlaying='HIDE', afterPlaying='HIDE')
        seq = el(part, 'SequenceImages', loopCount=1, frameRate=fps)
        for i in range(frames):
            el(seq, 'Image', resource=f'{prefix}_{i + 1}')

    def condition(self, expressions, branches, default=None, preview=None):
        """WFF Condition: the first Compare whose named expression is true is drawn, else Default."""
        c = el(self.node, 'Condition')
        ex = el(c, 'Expressions')
        for name, expr in expressions.items():
            el(ex, 'Expression', name=name).text = expr
        for name, fn in branches:
            fn(self.child(el(c, 'Compare', expression=name), vis=self.vis if name == preview else 'never'))
        if default:
            fn_vis = self.vis if preview not in [n for n, _ in branches] else 'never'
            default(self.child(el(c, 'Default'), vis=fn_vis))


# ---------------------------------------------------------------------------
def d_preview(c):
    return Node(ET.Element('Preview'), c.p, c.ox, c.oy, c.w, c.h, c.vis, c.alpha)


def icon_bell(d, cx, cy):
    d.arc(cx, cy - 1, 6.2, -90, 90, SKY, 2.4)
    d.line(cx - 6.2, cy - 1, cx - 6.2, cy + 4.0, SKY, 2.4)
    d.line(cx + 6.2, cy - 1, cx + 6.2, cy + 4.0, SKY, 2.4)
    d.line(cx - 8.8, cy + 5.2, cx + 8.8, cy + 5.2, SKY, 2.4)
    d.ellipse(cx, cy + 8.6, 1.8, fill=SKY)


def icon_sun(d, cx, cy):
    d.arc(cx, cy + 4, 5.4, -90, 90, AMBER, 2.4)
    d.line(cx - 9.5, cy + 5.8, cx + 9.5, cy + 5.8, AMBER, 2.2)
    for ang in (-55, 0, 55):
        sn, cs = math.sin(math.radians(ang)), -math.cos(math.radians(ang))
        d.line(cx + sn * 8.2, cy + 4 + cs * 8.2, cx + sn * 11.0, cy + 4 + cs * 11.0, AMBER, 2.0)


def _paint_tile_accent(parent, accent, icon, cy, bar_expr, bar_sample):
    d = parent.part_draw()
    d.rect_bar(7, 12, 5, TILE_H - 24, 2.5, accent)
    parent.image(icon, BAR_X, round(cy - ICON / 2), ICON, ICON, tint=accent)
    if bar_expr is not None:
        d = parent.part_draw()
        d.rect_bar(BAR_X, 53, BAR_W, BAR_H, 2.5, TRACK)
        d.rect_bar(BAR_X, 53, BAR_W, BAR_H, 2.5, accent, expr=bar_expr, sample=bar_sample)


def metric_tile(scene, name, y, launch, accent, icon, values, bar_expr=None, bar_sample=0.0,
                low_accent=None, low_cond=None):
    """Label-free dark metric tile: left accent bar + icon + numeric value (+ optional progress bar)."""
    g = scene.group(name, TILE_X, y, TILE_W, TILE_H, vis='active', launch=launch)
    g.part_draw().rrect(0, 0, TILE_W, TILE_H, TILE_R, fill=TILE_BG, stroke=TILE_EDGE, thickness=1.3)

    has_bar = bar_expr is not None
    cy = 27 if has_bar else TILE_H / 2

    if low_accent and low_cond:
        ok = g.group(f'{name}_ok', 0, 0, TILE_W, TILE_H, preview=True)
        el(ok.node, 'Transform', target='alpha', value=f'({low_cond}) ? 0 : 255')
        _paint_tile_accent(ok, accent, icon, cy, bar_expr, bar_sample)
        low = g.group(f'{name}_low', 0, 0, TILE_W, TILE_H, preview=False)
        el(low.node, 'Transform', target='alpha', value=f'({low_cond}) ? 255 : 0')
        _paint_tile_accent(low, low_accent, icon, cy, bar_expr, bar_sample)
    else:
        _paint_tile_accent(g, accent, icon, cy, bar_expr, bar_sample)

    for i, (size, sample, template, params, condition, preview) in enumerate(values):
        host = g
        if condition:
            host = g.group(f'{name}_s{i}', 0, 0, TILE_W, TILE_H, preview=preview)
            el(host.node, 'Transform', target='alpha', value=condition)
        host.text(104, cy, 102, size, CREAM, sample, template, params, family='teko_bold')


def complication_pill(scene, x, slot_id, name, provider, fallback_icon, sample_text, icon_tint):
    s = el(scene.node, 'ComplicationSlot', x=x, y=BOT_Y, width=SLOT_W, height=BOT_H,
           slotId=slot_id, displayName=name, isCustomizable='TRUE',
           supportedTypes='SHORT_TEXT RANGED_VALUE MONOCHROMATIC_IMAGE SMALL_IMAGE EMPTY')
    scene.ambient(s, 0)
    el(s, 'BoundingRoundBox', x=0, y=0, width=SLOT_W, height=BOT_H, cornerRadius=BOT_R)
    el(s, 'DefaultProviderPolicy', defaultSystemProvider=provider, defaultSystemProviderType='SHORT_TEXT')
    silent = Painter('none', scene.p.theme)
    for kind in ('SHORT_TEXT', 'RANGED_VALUE', 'MONOCHROMATIC_IMAGE', 'SMALL_IMAGE', 'EMPTY'):
        live = kind == 'SHORT_TEXT'
        c = Node(el(s, 'Complication', type=kind), scene.p if live else silent, x, BOT_Y, SLOT_W, BOT_H, 'active')
        c.part_draw().rrect(0, 0, SLOT_W, BOT_H, BOT_R, fill=SLATE, stroke=BORDER, thickness=1.4)
        if kind in ('SHORT_TEXT', 'RANGED_VALUE'):
            im = el(c.node, 'PartImage', x=15, y=round(BOT_H / 2 - 11), width=22, height=22, tintColor=icon_tint)
            el(im, 'Image', resource='[COMPLICATION.MONOCHROMATIC_IMAGE]')
            if live:
                fallback_icon(d_preview(c), 26, BOT_H / 2)
            c.text(62, BOT_H / 2, 42, 28, CREAM, sample_text, '%s', ['[COMPLICATION.TEXT]'])
        elif kind == 'MONOCHROMATIC_IMAGE':
            im = el(c.node, 'PartImage', x=round(SLOT_W / 2 - 14), y=round(BOT_H / 2 - 14),
                    width=28, height=28, tintColor=icon_tint)
            el(im, 'Image', resource='[COMPLICATION.MONOCHROMATIC_IMAGE]')
        elif kind == 'SMALL_IMAGE':
            im = el(c.node, 'PartImage', x=round(SLOT_W / 2 - 18), y=round(BOT_H / 2 - 18), width=36, height=36)
            el(im, 'Image', resource='[COMPLICATION.SMALL_IMAGE]')


def any_of(*codes):
    return ' || '.join(f'[WEATHER.CONDITION] == {c}' for c in codes)


WEATHER_ICONS = [
    ('sun', f'({any_of(1, 8)}) && [WEATHER.IS_DAY]', 'wx_sun'),
    ('moon', any_of(1, 8), 'wx_moon'),
    ('partly', any_of(14), 'wx_partly'),
    ('cloud', any_of(2), 'wx_cloud'),
    ('fog', any_of(3, 13), 'wx_fog'),
    ('rain', any_of(4, 6, 12), 'wx_rain'),
    ('snow', any_of(5, 7, 10, 11), 'wx_snow'),
    ('storm', any_of(9), 'wx_storm'),
    ('wind', any_of(15), 'wx_wind'),
]


def weather_pill(scene, sample):
    """Weather pill: native WFF condition glyph + temperature (or '--' when unavailable)."""
    g = scene.group('weather', WX_X, BOT_Y, WX_W, BOT_H, vis='active')
    g.part_draw().rrect(0, 0, WX_W, BOT_H, BOT_R, fill=SLATE, stroke=BORDER, thickness=1.4)

    def icon(name, tint=AMBER):
        return lambda n: n.image(name, 17, round(BOT_H / 2 - ICON / 2), ICON, ICON, tint=tint)

    def live(n):
        n.condition({name: expr for name, expr, _ in WEATHER_ICONS},
                    [(name, icon(res)) for name, _, res in WEATHER_ICONS],
                    default=icon('wx_cloud'), preview=sample['icon'])
        n.text(74, BOT_H / 2, 58, 30, CREAM, '%d°' % sample['temperature'], '%s°', ['[WEATHER.TEMPERATURE]'])

    def missing(n):
        icon('wx_cloud', tint=BORDER)(n)
        n.text(74, BOT_H / 2, 58, 30, BORDER, '--', '--')

    g.condition({'available': '[WEATHER.IS_AVAILABLE]'}, [('available', live)], default=missing, preview='available')


def recorder_button(scene):
    """Round accent button launching Samsung Voice Recorder."""
    r = MIC_SIZE / 2
    g = scene.group('recorder', MIC_X, BOT_Y, MIC_SIZE, MIC_SIZE, vis='active', launch=RECORDER)
    g.part_draw().ellipse(r, r, r, fill='CROWN')
    g.image('ic_mic', round(r - MIC_ICON / 2), round(r - MIC_ICON / 2), MIC_ICON, MIC_ICON, tint=DARK_INK)


def build(mode, theme):
    v = SAMPLE
    painter = Painter(mode, theme)
    wf = ET.Element('WatchFace', width=str(S), height=str(S), clipShape='CIRCLE')
    el(wf, 'Metadata', key='CLOCK_TYPE', value='DIGITAL')
    el(wf, 'Metadata', key='PREVIEW_TIME', value='%02d:%02d:%02d' % (v['hour'], v['minute'], v['second']))
    configs = el(wf, 'UserConfigurations')
    palette = el(configs, 'ColorConfiguration', id='theme', displayName='theme_color_name', defaultValue=THEMES[0][0])
    for key, _, crown_col, min_col in THEMES:
        el(palette, 'ColorOption', id=key, displayName='color_' + key, colors=f'{crown_col} {min_col}')

    scene = Node(el(wf, 'Scene', backgroundColor=BLACK), painter)

    # 1 · Outer seconds crown: 60 ticks + progress arc + orbiting seconds marker.
    crown = scene.group('crown', vis='active')
    crown.image('bezel_ticks', 0, 0, S, S)
    crown.part_draw().arc(C, C, ARC_R, 0, v['second'] * 6, 'CROWN', ARC_W, expr='6 * [SECOND]')
    analog = crown.child(el(crown.node, 'AnalogClock', x=0, y=0, width=S, height=S))
    analog.hand('SecondHand', 'sec_dot', C - 8, C - DOT_ORBIT - 8, 16, 16, v['second'] * 6, 'CROWN')

    # 2 · Date pill at top (clear of 12 o'clock system indicator).
    date_pill = scene.group('date_pill', DATE_X, DATE_Y, DATE_W, DATE_H, vis='active')
    date_pill.part_draw().rrect(0, 0, DATE_W, DATE_H, DATE_R, fill=SLATE, stroke=BORDER, thickness=1.4)
    date_sample = f"{v['weekday']} · {v['day']} {v['month']}"
    scene.text(C, DATE_Y + DATE_H / 2, DATE_W - 12, 24, CREAM, date_sample, '%s · %s %s',
               ['[DAY_OF_WEEK_F]', '[DAY]', '[MONTH_S]'], upper=True, ambient=165)

    # 3 · Flip bodies (hours stacked over minutes).
    flips = scene.group('flip_bodies', vis='active')
    flips.image('flap_body', FLIP_X, HOUR_Y, FLIP_W, FLIP_H)
    flips.image('flap_body', FLIP_X, MIN_Y, FLIP_W, FLIP_H)

    # 4 · Time digits (fixed two-digit columns; visible in both active and ambient).
    time_grp = scene.group('time_digits')
    hh, mm = '%02d' % v['hour'], '%02d' % v['minute']
    for y0, digits, source, col in ((HOUR_Y, hh, '[HOUR_0_23]', CREAM), (MIN_Y, mm, '[MINUTE]', 'MINUTE_COL')):
        cy = y0 + FLIP_H / 2
        for cx, sample, expr in ((FLIP_X + 49, digits[0], f'floor({source} / 10)'),
                                 (FLIP_X + 105, digits[1], f'{source} % 10')):
            time_grp.text(cx, cy, 58, 114, col, sample, '%s', [expr], family='teko_bold', ambient=175)

    # 5 · Flip hinges, cast shadow, and live falling-leaf animation on hour/minute change.
    front = scene.group('flip_front', vis='active')
    for y0, trigger in ((HOUR_Y, 'ON_NEXT_HOUR'), (MIN_Y, 'ON_NEXT_MINUTE')):
        front.image('flap_overlay', FLIP_X - PIN, y0, FLIP_W + 2 * PIN, FLIP_H)
        front.flip('flip_leaf', FLIP_FRAMES, FLIP_X, y0, FLIP_W, FLIP_H, trigger, 24)

    # 6 · Right column: three label-free metric tiles with tap targets.
    metric_tile(scene, 'heart', HEART_Y, 'HEALTH_HEART_RATE', CORAL, 'ic_heart',
                [(44, str(v['heart']), '%s', ["[HEART_RATE] > 0 ? [HEART_RATE] : '--'"], None, True)])
    metric_tile(scene, 'battery', BATT_Y, 'BATTERY_STATUS', AMBER, 'ic_battery',
                [(40, f"{v['battery']}%", '%s%%', ['[BATTERY_PERCENT]'], None, True)],
                bar_expr=f'{BAR_W} * clamp([BATTERY_PERCENT], 0, 100) / 100', bar_sample=v['battery'] / 100,
                low_accent=CORAL, low_cond='[BATTERY_PERCENT] <= 20')
    metric_tile(scene, 'steps', STEPS_Y, HEALTH, SAGE, 'ic_steps',
                [(39, str(v['steps']), '%s', ['[STEP_COUNT]'], '[STEP_COUNT] < 10000 ? 255 : 0', v['steps'] < 10000),
                 (32, str(v['steps']), '%s', ['[STEP_COUNT]'], '[STEP_COUNT] < 10000 ? 0 : 255', v['steps'] >= 10000)],
                bar_expr=f'{BAR_W} * clamp([STEP_COUNT] / clamp([STEP_GOAL], 1, 1000000), 0, 1)',
                bar_sample=v['steps'] / v['goal'])

    # 7 · Bottom row: notifications complication + native weather + voice recorder button.
    complication_pill(scene, SLOT_X, 0, 'slot_left_name', 'UNREAD_NOTIFICATION_COUNT', icon_bell, '0', SKY)
    weather_pill(scene, v['weather'])
    recorder_button(scene)

    # 8 · Always-on: dimmed card outlines + split groove + 4 subtle cardinal markers.
    aod = scene.group('aod_outline', vis='ambient').part_draw()
    for y0 in (HOUR_Y, MIN_Y):
        aod.rrect(FLIP_X, y0, FLIP_W, FLIP_H, FLIP_R, stroke=AOD_EDGE, thickness=1.5)
        aod.hline(FLIP_X, y0 + FLIP_H / 2, FLIP_W, BLACK, 3)
        aod.hline(FLIP_X, y0 + FLIP_H / 2 + 2, FLIP_W, AOD_EDGE, 1)
    for deg in (0, 90, 180, 270):
        rad = math.radians(deg)
        aod.line(C + 224 * math.sin(rad), C - 224 * math.cos(rad),
                 C + 234 * math.sin(rad), C - 234 * math.cos(rad), AOD_EDGE, thickness=1.6)

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
    for node in wf.iter():
        if node.tag in ('Font', 'Upper', 'Template') and len(node):
            if node.tag != 'Template':
                node.text = None
            for inner in node:
                inner.tail = None
    ET.ElementTree(wf).write(ROOT / 'res/raw/watchface.xml', encoding='utf-8', xml_declaration=True)
    print('Generated:', ROOT / 'res/raw/watchface.xml')
    round_mask(active).save(ROOT / 'res/drawable/preview.png', optimize=True)
    round_mask(active).save(ROOT / 'design/preview-ambra.png')
    round_mask(build('ambient', THEMES[0])[1]).save(ROOT / 'design/preview-ambient.png')
    if '--all' in sys.argv:
        cols = len(THEMES)
        sheet = Image.new('RGB', (S * cols, S), (0, 0, 0))
        for i, theme in enumerate(THEMES):
            img = round_mask(build('active', theme)[1])
            img.save(ROOT / f'design/preview-{theme[0]}.png')
            sheet.paste(img, (S * i, 0))
        sheet.save(ROOT / 'design/preview-themes.png')
    print('Preview: design/preview-ambra.png, design/preview-ambient.png')
