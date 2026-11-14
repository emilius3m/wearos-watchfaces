"""Generate NIXIE: the Watch Face Format 2 XML and faithful Pillow previews from one scene."""
from pathlib import Path
import math
import sys
from xml.etree import ElementTree as ET
from PIL import Image, ImageChops, ImageDraw, ImageFont

from layout import (
    S, C, REHAUT_MID, DATE_Y, TUBE_Y0, TUBE_W, TUBE_H, TUBE_XS,
    GLYPH_W, GLYPH_H, GLYPH_Y, COLON_CY, FLASH_FRAMES,
    INST_X0, INST_Y0, INST_W, INST_H, INST_BAR_X, INST_BAR_Y, INST_BAR_W, INST_BAR_H, ICON_SM,
    WX_X0, WX_Y0, WX_W, WX_H,
    BOT_Y0, BOT_H, BOT_CAP_R, SLOT_L_X, SLOT_R_X, SLOT_W, MIC_X, MIC_Y, MIC_D,
)

ROOT = Path(__file__).resolve().parents[1]
K = 3  # preview supersampling factor

# id, display_name, plasma_col, wire_core_col, ui_accent_col
THEMES = [
    ('ambra', 'Ambra Neon', '#FFFF6A14', '#FFFFECBA', '#FFFF942C'),
    ('vfd', 'VFD Verde Fosforo', '#FF1CE6B0', '#FFD6FFF2', '#FF3EE8BA'),
    ('cobalto', 'Cobalto Ionico', '#FF3A9BFF', '#FFE0F2FF', '#FF68B6FF'),
    ('rubino', 'Rubino Caldo', '#FFFF3646', '#FFFFD8DC', '#FFFF6470'),
]
TOKENS = {'PLASMA': 0, 'CORE': 1, 'ACCENT': 2}

CASE_FINISHES = ('titanium', 'brass')

CREAM = '#FFFFE0A2'
PARCHMENT = '#FFD6B48A'
CORAL = '#FFFF6056'
SAGE = '#FF7CD696'
BLACK = '#FF000000'
SLATE_AOD = '#FF38322C'
TRACK_BG = '#FF201812'
ICON_SZ = 15

SAMPLE = dict(
    hour=9, minute=27, second=36,
    steps=6480, goal=10000, heart=72, battery=84,
    weekday='GIOVEDÌ', day=12, month='NOV',
    weather=dict(
        icon='partly', temperature=14, precip=20,
        days=[
            dict(day=1, label='DOMANI', icon='cloud', high=10, low=6),
            dict(day=2, label='SAB 14', icon='partly', high=15, low=8),
        ],
    ),
)
FONTS = {'teko_semibold': 'SEMI_BOLD', 'teko_bold': 'BOLD'}
CAP_SHIFT = 0.0695
BASELINE = (0.958 - 0.475) / 2
HEALTH = 'com.samsung.android.wear.shealth/com.samsung.android.wear.shealth.app.home.HomeActivity'
RECORDER = 'com.samsung.android.wear.voicerecorder/com.samsung.android.wear.voicerecorder.view.MainActivity'
WEATHER = 'com.samsung.android.watch.weather/com.samsung.android.watch.weather.ui.WeatherActivity'
DIVIDER = '#FF382C22'


def fmt(v):
    if isinstance(v, float):
        return ('%.3f' % v).rstrip('0').rstrip('.')
    return str(v)


def el(parent, tag, **attrs):
    return ET.SubElement(parent, tag, {k: fmt(v) for k, v in attrs.items()})


def xml_color(c):
    return f'[CONFIGURATION.theme.{TOKENS[c]}]' if c in TOKENS else c


class Painter:
    """Pillow preview renderer sharing coordinates with the XML emitter."""

    def __init__(self, mode, theme, case_finish='titanium'):
        self.mode = mode
        self.theme = theme
        self.case_finish = case_finish
        self.img = Image.new('RGBA', (S * K, S * K), (0, 0, 0, 255))
        self.fonts = {}
        self.drawables = {}

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

    def drawable(self, name):
        if name not in self.drawables:
            self.drawables[name] = Image.open(ROOT / f'res/drawable/{name}.png').convert('RGBA')
        return self.drawables[name]

    def image(self, name, x, y, w, h, tint=None, angle=0, alpha=1.0):
        im = self.drawable(name)
        if tint:
            tr, tg, tb, ta = self.rgba(tint, alpha)
            tint_layer = Image.new('RGBA', im.size, (tr, tg, tb, 255))
            tint_layer.putalpha(im.split()[3])
            im = tint_layer
            if ta < 255:
                a_ch = im.split()[3].point(lambda p: round(p * ta / 255))
                im.putalpha(a_ch)
        elif alpha < 1.0:
            im = im.copy()
            a_ch = im.split()[3].point(lambda p: round(p * alpha))
            im.putalpha(a_ch)
        im = im.resize((round(w * K), round(h * K)), Image.LANCZOS)
        if angle:
            pad = round(max(im.size) * 1.5)
            frame = Image.new('RGBA', (pad, pad), (0, 0, 0, 0))
            frame.paste(im, ((pad - im.width) // 2, (pad - im.height) // 2))
            frame = frame.rotate(-angle, Image.BICUBIC)
            cx = (x + w / 2 - C) * K
            cy = (y + h / 2 - C) * K
            rad = math.radians(angle)
            rx = cx * math.cos(rad) - cy * math.sin(rad) + C * K
            ry = cx * math.sin(rad) + cy * math.cos(rad) + C * K
            self.img.alpha_composite(frame, (round(rx - pad / 2), round(ry - pad / 2)))
        else:
            self.img.alpha_composite(im, (round(x * K), round(y * K)))


class Node:
    """Simultaneously writes WFF XML nodes and executes preview draws."""

    def __init__(self, xml_node, painter, ox=0, oy=0, w=S, h=S, vis='both', alpha=1.0):
        self.node = xml_node
        self.p = painter
        self.ox, self.oy, self.w, self.h = ox, oy, w, h
        self.vis = vis
        self.alpha = alpha
        self.shown = vis in ('both', painter.mode) and alpha > 0

    def child(self, xml_node, ox=0, oy=0, w=None, h=None, vis=None, preview=True):
        return Node(xml_node, self.p, self.ox + ox, self.oy + oy,
                    self.w if w is None else w, self.h if h is None else h,
                    vis or self.vis, self.alpha if preview else 0.0)

    def group(self, name, x=0, y=0, w=None, h=None, vis=None, launch=None, preview=True, ambient_alpha=None):
        w = self.w - x if w is None else w
        h = self.h - y if h is None else h
        attrs = dict(name=name, x=int(x), y=int(y), width=int(w), height=int(h))
        g = el(self.node, 'Group', **attrs)
        if vis in ('active', 'ambient'):
            self.ambient(g, 255 if vis == 'ambient' else 0)
        elif ambient_alpha is not None:
            self.ambient(g, ambient_alpha)
        if launch:
            el(g, 'Launch', target=launch)
        eff_alpha = self.alpha * ((ambient_alpha / 255) if (ambient_alpha is not None and self.p.mode == 'ambient') else 1.0)
        n = Node(g, self.p, self.ox + x, self.oy + y, w, h, vis or self.vis, eff_alpha if preview else 0.0)
        return n

    def ambient(self, target, value):
        el(target, 'Variant', mode='AMBIENT', target='alpha', value=int(value))

    def part_draw(self, x=0, y=0, w=None, h=None):
        w = self.w if w is None else w
        h = self.h if h is None else h
        return DrawProxy(el(self.node, 'PartDraw', x=int(x), y=int(y), width=int(w), height=int(h)), self, x, y)

    def _box(self, x, y, w, h):
        return [(self.ox + x) * K, (self.oy + y) * K, (self.ox + x + w) * K, (self.oy + y + h) * K]

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
            for expr in params:
                el(tpl, 'Parameter', expression=expr)
        else:
            host.text = template
        if not self.shown:
            return
        alpha = self.alpha * ((ambient / 255) if (ambient is not None and self.p.mode == 'ambient') else 1.0)
        self.p.shape(color, alpha, lambda d, c: d.text(
            ((self.ox + cx) * K, (self.oy + y + height / 2 + BASELINE * size) * K),
            sample, font=self.p.font(family, size), fill=c, anchor='ms'))

    def bitmap_digit(self, x, y, w, h, bm_family, color, sample_ch, expr, ambient=None):
        p = el(self.node, 'PartText', x=x, y=y, width=w, height=h)
        if ambient is not None:
            self.ambient(p, ambient)
        t = el(p, 'Text', align='CENTER', maxLines=1, ellipsis='FALSE')
        bf = el(t, 'BitmapFont', family=bm_family, size=float(h), color=xml_color(color))
        tpl = el(bf, 'Template')
        tpl.text = '%s'
        el(tpl, 'Parameter', expression=expr)
        if not self.shown:
            return
        alpha = self.alpha * ((ambient / 255) if (ambient is not None and self.p.mode == 'ambient') else 1.0)
        self.p.image(f'{bm_family}_{sample_ch}', self.ox + x, self.oy + y, w, h, tint=color, alpha=alpha)

    def image(self, name, x, y, w, h, tint=None):
        attrs = dict(x=x, y=y, width=w, height=h)
        if tint:
            attrs['tintColor'] = xml_color(tint)
        el(el(self.node, 'PartImage', **attrs), 'Image', resource=name)
        if self.shown:
            self.p.image(name, self.ox + x, self.oy + y, w, h, tint, alpha=self.alpha)

    def hand(self, kind, name, x, y, w, h, angle, tint):
        el(self.node, kind, resource=name, x=x, y=y, width=w, height=h,
           pivotX=float((C - x) / w), pivotY=float((C - y) / h), tintColor=xml_color(tint))
        if self.shown:
            self.p.image(name, x, y, w, h, tint, angle=angle, alpha=self.alpha)

    def animated_strike(self, prefix, frames, x, y, w, h, trigger, fps, tint):
        part = el(self.node, 'PartAnimatedImage', x=x, y=y, width=w, height=h, tintColor=xml_color(tint))
        el(part, 'AnimationController', play=trigger, beforePlaying='HIDE', afterPlaying='HIDE')
        seq = el(part, 'SequenceImages', loopCount=1, frameRate=fps)
        for i in range(frames):
            el(seq, 'Image', resource=f'{prefix}_{i + 1}')

    def condition(self, expressions, branches, default=None, preview=None):
        c = el(self.node, 'Condition')
        ex = el(c, 'Expressions')
        for name, expr in expressions.items():
            el(ex, 'Expression', name=name).text = expr
        for name, fn in branches:
            fn(self.child(el(c, 'Compare', expression=name), vis=self.vis if name == preview else 'never'))
        if default:
            fn_vis = self.vis if preview not in [n for n, _ in branches] else 'never'
            default(self.child(el(c, 'Default'), vis=fn_vis))


class DrawProxy:
    def __init__(self, part, node, ox, oy):
        self.part, self.n, self.ox, self.oy = part, node, ox, oy

    def _box(self, x, y, w, h):
        return self.n._box(self.ox + x, self.oy + y, w, h)

    def rrect(self, x, y, w, h, r, fill=None, stroke=None, thickness=1.0):
        e = el(self.part, 'RoundRectangle', x=float(x), y=float(y), width=float(w), height=float(h),
               cornerRadiusX=float(r), cornerRadiusY=float(r))
        if fill:
            el(e, 'Fill', color=xml_color(fill))
        if stroke:
            el(e, 'Stroke', color=xml_color(stroke), thickness=float(thickness))
        if not self.n.shown:
            return
        if fill:
            self.n.p.shape(fill, self.n.alpha, lambda d, c: d.rounded_rectangle(self._box(x, y, w, h), radius=r * K, fill=c))
        if stroke:
            self.n.p.shape(stroke, self.n.alpha, lambda d, c: d.rounded_rectangle(
                self._box(x, y, w, h), radius=r * K, outline=c, width=max(1, round(thickness * K))))

    def rect_bar(self, x, y, w, h, r, fill, expr=None, sample=1.0):
        e = el(self.part, 'RoundRectangle', x=float(x), y=float(y), width=float(w), height=float(h),
               cornerRadiusX=float(r), cornerRadiusY=float(r))
        if expr:
            el(e, 'Transform', target='width', value=expr)
        el(e, 'Fill', color=xml_color(fill))
        if self.n.shown and w * sample > 0:
            self.n.p.shape(fill, self.n.alpha,
                           lambda d, c: d.rounded_rectangle(self._box(x, y, w * sample, h), radius=r * K, fill=c))

    def line(self, x1, y1, x2, y2, stroke, thickness=1.0):
        ln = el(self.part, 'Line', startX=float(x1), startY=float(y1), endX=float(x2), endY=float(y2))
        el(ln, 'Stroke', color=xml_color(stroke), thickness=float(thickness))
        if self.n.shown:
            self.n.p.shape(stroke, self.n.alpha, lambda d, c: d.line(
                [(self.n.ox + self.ox + x1) * K, (self.n.oy + self.oy + y1) * K,
                 (self.n.ox + self.ox + x2) * K, (self.n.oy + self.oy + y2) * K],
                fill=c, width=max(1, round(thickness * K))))

    def ellipse(self, x, y, w, h, fill=None, stroke=None, thickness=1.0):
        e = el(self.part, 'Ellipse', x=float(x), y=float(y), width=float(w), height=float(h))
        if fill:
            el(e, 'Fill', color=xml_color(fill))
        if stroke:
            el(e, 'Stroke', color=xml_color(stroke), thickness=float(thickness))
        if not self.n.shown:
            return
        if fill:
            self.n.p.shape(fill, self.n.alpha, lambda d, c: d.ellipse(self._box(x, y, w, h), fill=c))
        if stroke:
            self.n.p.shape(stroke, self.n.alpha, lambda d, c: d.ellipse(
                self._box(x, y, w, h), outline=c, width=max(1, round(thickness * K))))


def d_preview(c):
    return Node(ET.Element('Preview'), c.p, c.ox, c.oy, c.w, c.h, c.vis, c.alpha)


def icon_bell_preview(d, cx, cy):
    d.arc(cx, cy - 1, 6.2, -90, 90, 'ACCENT', 2.4)
    d.line(cx - 6.2, cy - 1, cx - 6.2, cy + 4.0, 'ACCENT', 2.4)
    d.line(cx + 6.2, cy - 1, cx + 6.2, cy + 4.0, 'ACCENT', 2.4)
    d.line(cx - 8.8, cy + 5.2, cx + 8.8, cy + 5.2, 'ACCENT', 2.4)
    d.ellipse(cx, cy + 8.6, 1.8, fill='ACCENT')


# Tiny helper to render bell fallback icon cleanly in preview only
class _ShapeDrawHelper:
    def __init__(self, n):
        self.n = n

    def arc(self, cx, cy, r, s, e, col, th):
        if self.n.shown:
            self.n.p.shape(col, self.n.alpha, lambda d, c: d.arc(
                self.n._box(cx - r, cy - r, r * 2, r * 2), s - 90, e - 90, fill=c, width=max(1, round(th * K))))

    def line(self, x1, y1, x2, y2, col, th):
        if self.n.shown:
            self.n.p.shape(col, self.n.alpha, lambda d, c: d.line(
                [(self.n.ox + x1) * K, (self.n.oy + y1) * K, (self.n.ox + x2) * K, (self.n.oy + y2) * K],
                fill=c, width=max(1, round(th * K))))

    def ellipse(self, cx, cy, r, fill):
        if self.n.shown:
            self.n.p.shape(fill, self.n.alpha, lambda d, c: d.ellipse(
                self.n._box(cx - r, cy - r, r * 2, r * 2), fill=c))


def icon_bell(d, cx, cy):
    h = _ShapeDrawHelper(d)
    h.arc(cx, cy - 1, 5.4, -90, 90, 'ACCENT', 2.1)
    h.line(cx - 5.4, cy - 1, cx - 5.4, cy + 3.4, 'ACCENT', 2.1)
    h.line(cx + 5.4, cy - 1, cx + 5.4, cy + 3.4, 'ACCENT', 2.1)
    h.line(cx - 7.6, cy + 4.4, cx + 7.6, cy + 4.4, 'ACCENT', 2.1)
    h.ellipse(cx, cy + 7.4, 1.6, fill='ACCENT')


def icon_calendar(d, cx, cy):
    """Tiny calendar glyph for previewing the right customizable NEXT_EVENT capsule."""
    h = _ShapeDrawHelper(d)
    # Outer frame lines + header bar
    h.line(cx - 7.0, cy - 5.5, cx + 7.0, cy - 5.5, 'ACCENT', 1.8)
    h.line(cx - 7.0, cy - 1.5, cx + 7.0, cy - 1.5, 'ACCENT', 1.5)
    h.line(cx - 7.0, cy + 7.0, cx + 7.0, cy + 7.0, 'ACCENT', 1.8)
    h.line(cx - 7.0, cy - 5.5, cx - 7.0, cy + 7.0, 'ACCENT', 1.8)
    h.line(cx + 7.0, cy - 5.5, cx + 7.0, cy + 7.0, 'ACCENT', 1.8)
    h.line(cx - 3.6, cy - 8.0, cx - 3.6, cy - 4.2, 'ACCENT', 1.8)
    h.line(cx + 3.6, cy - 8.0, cx + 3.6, cy - 4.2, 'ACCENT', 1.8)
    h.ellipse(cx, cy + 3.0, 1.6, fill='ACCENT')


def any_of(var, *codes):
    return ' || '.join(f'{var} == {c}' for c in codes)


def weather_icon_cond(node, cond_expr, x, y, size, sample_key, tint='ACCENT', check_is_day=False):
    icons = [
        ('sun', f'({any_of(cond_expr, 1, 8)}) && [WEATHER.IS_DAY]' if check_is_day else any_of(cond_expr, 1, 8), 'wx_sun'),
    ]
    if check_is_day:
        icons.append(('moon', any_of(cond_expr, 1, 8), 'wx_moon'))
    icons += [
        ('partly', any_of(cond_expr, 14), 'wx_partly'),
        ('cloud', any_of(cond_expr, 2), 'wx_cloud'),
        ('fog', any_of(cond_expr, 3, 13), 'wx_fog'),
        ('rain', any_of(cond_expr, 4, 6, 12), 'wx_rain'),
        ('snow', any_of(cond_expr, 5, 7, 10, 11), 'wx_snow'),
        ('storm', any_of(cond_expr, 9), 'wx_storm'),
        ('wind', any_of(cond_expr, 15), 'wx_wind'),
    ]
    icon = lambda res: (lambda n: n.image(res, x, y, size, size, tint=tint))
    node.condition(
        {name: expr for name, expr, _ in icons},
        [(name, icon(res)) for name, _, res in icons],
        default=icon('wx_cloud'),
        preview=sample_key,
    )


def build_capsule_slot(scene, slot_id, x0, display_name, provider, sample_text, text_size, preview_icon_fn):
    s = el(scene.node, 'ComplicationSlot', x=x0, y=BOT_Y0, width=SLOT_W, height=BOT_H,
           slotId=slot_id, displayName=display_name, isCustomizable='TRUE',
           supportedTypes='SHORT_TEXT RANGED_VALUE MONOCHROMATIC_IMAGE SMALL_IMAGE EMPTY')
    scene.ambient(s, 0)
    el(s, 'BoundingRoundBox', x=0, y=0, width=SLOT_W, height=BOT_H, cornerRadius=BOT_CAP_R)
    el(s, 'DefaultProviderPolicy', defaultSystemProvider=provider, defaultSystemProviderType='SHORT_TEXT')
    silent = Painter('none', scene.p.theme, scene.p.case_finish)
    for kind in ('SHORT_TEXT', 'RANGED_VALUE', 'MONOCHROMATIC_IMAGE', 'SMALL_IMAGE', 'EMPTY'):
        live = kind == 'SHORT_TEXT'
        c = Node(el(s, 'Complication', type=kind), scene.p if live else silent, x0, BOT_Y0, SLOT_W, BOT_H, 'active')
        if kind in ('SHORT_TEXT', 'RANGED_VALUE'):
            im = el(c.node, 'PartImage', x=16, y=round(BOT_H / 2 - 9), width=18, height=18, tintColor=xml_color('ACCENT'))
            el(im, 'Image', resource='[COMPLICATION.MONOCHROMATIC_IMAGE]')
            if live:
                preview_icon_fn(d_preview(c), 25, BOT_H / 2)
            c.text(59, BOT_H / 2 + 1, 48, text_size, CREAM, sample_text, '%s', ['[COMPLICATION.TEXT]'])
        elif kind == 'MONOCHROMATIC_IMAGE':
            im = el(c.node, 'PartImage', x=round(SLOT_W / 2 - 12), y=round(BOT_H / 2 - 12),
                    width=24, height=24, tintColor=xml_color('ACCENT'))
            el(im, 'Image', resource='[COMPLICATION.MONOCHROMATIC_IMAGE]')
        elif kind == 'SMALL_IMAGE':
            im = el(c.node, 'PartImage', x=round(SLOT_W / 2 - 15), y=round(BOT_H / 2 - 15), width=30, height=30)
            el(im, 'Image', resource='[COMPLICATION.SMALL_IMAGE]')
        elif kind == 'EMPTY':
            c.text(round(SLOT_W / 2), BOT_H / 2 + 1, SLOT_W - 24, 20, SLATE_AOD, '—', '—')


def build_weather_console(scene, sample):
    g = scene.group('weather', WX_X0, WX_Y0, WX_W, WX_H, vis='active', launch=WEATHER)

    def live(n):
        # Engraved vertical column dividers between Today | Tomorrow | Day+2
        # Usable content inner span inside left/right screws (x=18..326 -> 3 cols of 102px)
        div = n.part_draw(0, 0, WX_W, WX_H)
        for dx in (121, 225):
            div.line(dx, 10, dx, WX_H - 10, DIVIDER, 1.0)

        # Col 1: Current conditions + chance of precipitation + live temperature (x=18..120)
        c1 = n.group('wx_today', 18, 0, 102, WX_H)
        c1.text(51, 14, 96, 15, PARCHMENT, f"OGGI · {sample['precip']}%",
                'OGGI · %s%%', ['[WEATHER.CHANCE_OF_PRECIPITATION]'], family='teko_semibold')
        weather_icon_cond(c1, '[WEATHER.CONDITION]', 18, 25, 22, sample['icon'], tint='ACCENT', check_is_day=True)
        c1.text(67, 36, 52, 25, CREAM, f"{sample['temperature']}°", '%s°',
                ['[WEATHER.TEMPERATURE]'], family='teko_bold')

        # Subtle dot indicator in top-left corner only when cached weather needs refresh
        c1.condition({'stale': '[WEATHER.IS_ERROR]'},
                     [('stale', lambda sn: sn.part_draw(0, 0, 12, 14).ellipse(3, 5, 5, 5, fill='ACCENT'))])

        # Cols 2 & 3: Tomorrow (x=122..224) + Day+2 (x=226..328) forecasts with high/low temps
        for d_info in sample['days']:
            d = d_info['day']
            fx0 = 122 if d == 1 else 226
            col = n.group(f'wx_day_{d}', fx0, 0, 102, WX_H)
            if d == 1:
                col.text(51, 14, 94, 15, PARCHMENT, d_info['label'], 'DOMANI', family='teko_semibold')
            else:
                stamp = f'[UTC_TIMESTAMP] - [SECONDS_IN_DAY] * 1000 - [MILLISECOND] + {d * 86400000 + 43200000}'
                col.text(51, 14, 94, 15, PARCHMENT, d_info['label'], '%s',
                         [f'icuText("EEE d", {stamp})'], family='teko_semibold', upper=True)

            def day_ok(dn, di=d_info, day_num=d):
                weather_icon_cond(dn, f'[WEATHER.DAYS.{day_num}.CONDITION_DAY]', 10, 26, 20, di['icon'], tint='ACCENT')
                dn.text(63, 36, 62, 21, CREAM, f"{di['high']}°/{di['low']}°", '%s°/%s°',
                        [f'[WEATHER.DAYS.{day_num}.TEMPERATURE_HIGH]',
                         f'[WEATHER.DAYS.{day_num}.TEMPERATURE_LOW]'],
                        family='teko_semibold')

            def day_na(dn):
                dn.image('wx_cloud', 10, 26, 20, 20, tint=SLATE_AOD)
                dn.text(63, 36, 62, 21, SLATE_AOD, '--°/--°', '--°/--°', family='teko_semibold')

            col.condition({f'd{d}_avail': f'[WEATHER.DAYS.{d}.IS_AVAILABLE]'},
                          [(f'd{d}_avail', day_ok)], default=day_na, preview=f'd{d}_avail')

    def missing(n):
        n.image('wx_cloud', 74, round(WX_H / 2 - 11), 22, 22, tint=SLATE_AOD)
        n.text(192, WX_H / 2 + 1, 210, 20, SLATE_AOD, 'METEO NON DISPONIBILE', 'METEO NON DISPONIBILE')

    g.condition({'available': '[WEATHER.IS_AVAILABLE]'}, [('available', live)], default=missing, preview='available')

    # Transparent customizable APP_SHORTCUT slot: local taps fall through EMPTY to Samsung Weather;
    # configured shortcuts override it seamlessly on Play Store watches.
    ws = el(scene.node, 'ComplicationSlot', x=WX_X0, y=WX_Y0, width=WX_W, height=WX_H,
            slotId=3, displayName='slot_weather_name', isCustomizable='TRUE',
            supportedTypes='MONOCHROMATIC_IMAGE SMALL_IMAGE SHORT_TEXT RANGED_VALUE EMPTY')
    scene.ambient(ws, 0)
    el(ws, 'BoundingRoundBox', x=0, y=0, width=WX_W, height=WX_H, cornerRadius=13)
    el(ws, 'DefaultProviderPolicy', defaultSystemProvider='APP_SHORTCUT', defaultSystemProviderType='MONOCHROMATIC_IMAGE')
    for kind in ('MONOCHROMATIC_IMAGE', 'SMALL_IMAGE', 'SHORT_TEXT', 'RANGED_VALUE'):
        c = el(ws, 'Complication', type=kind)
        sh = el(el(c, 'PartDraw', x=0, y=0, width=WX_W, height=WX_H), 'Rectangle', x=0, y=0, width=WX_W, height=WX_H)
        el(sh, 'Fill', color='#00000000')
    el(ws, 'Complication', type='EMPTY')


def build(mode, theme, case_finish='titanium'):
    v = SAMPLE
    painter = Painter(mode, theme, case_finish=case_finish)
    wf = ET.Element('WatchFace', width=str(S), height=str(S), clipShape='CIRCLE')
    el(wf, 'Metadata', key='CLOCK_TYPE', value='DIGITAL')
    el(wf, 'Metadata', key='PREVIEW_TIME', value='%02d:%02d:%02d' % (v['hour'], v['minute'], v['second']))

    configs = el(wf, 'UserConfigurations')
    case_cfg = el(configs, 'ListConfiguration', id='case_finish', displayName='case_finish_name', defaultValue='titanium')
    for cf in CASE_FINISHES:
        el(case_cfg, 'ListOption', id=cf, displayName=f'case_{cf}')

    palette = el(configs, 'ColorConfiguration', id='theme', displayName='tube_color_name', defaultValue=THEMES[0][0])
    for key, _, plasma_col, core_col, acc_col in THEMES:
        el(palette, 'ColorOption', id=key, displayName='color_' + key, colors=f'{plasma_col} {core_col} {acc_col}')

    bm_fonts = el(wf, 'BitmapFonts')
    for fam in ('nixie_glow', 'nixie_core'):
        bf = el(bm_fonts, 'BitmapFont', name=fam)
        for d_ch in '0123456789':
            el(bf, 'Character', name=d_ch, resource=f'{fam}_{d_ch}', width=GLYPH_W, height=GLYPH_H)

    scene = Node(el(wf, 'Scene', backgroundColor=BLACK), painter)

    # 1 · Machined hardware dial plate & brushed metal bezel (switchable Titanium / Brass)
    dial_grp = scene.group('dial_hardware', vis='active')
    lc = el(dial_grp.node, 'ListConfiguration', id='case_finish')
    for cf in CASE_FINISHES:
        opt = dial_grp.child(el(lc, 'ListOption', id=cf), vis='active' if cf == case_finish else 'never')
        opt.image(f'dial_{cf}', 0, 0, S, S)

    # 2 · Orbiting neon seconds indicator bead along inner rehaut track (REHAUT_MID)
    sec_grp = scene.group('sec_crown', vis='active')
    analog = sec_grp.child(el(sec_grp.node, 'AnalogClock', x=0, y=0, width=S, height=S))
    analog.hand('SecondHand', 'sec_bead', C - 8, round(C - REHAUT_MID - 8), 16, 16, v['second'] * 6, 'ACCENT')

    # 3 · Top Italian date caption
    date_sample = f"{v['weekday']} · {v['day']} {v['month']}"
    scene.text(C, DATE_Y - 2, 200, 24, PARCHMENT, date_sample, '%s · %s %s',
               ['[DAY_OF_WEEK_F]', '[DAY]', '[MONTH_S]'], upper=True, ambient=155)

    # 4 · Vibrating Nixie filament plasma layer (integer-cycle harmonics in 1000ms for smooth hum)
    hh, mm = '%02d' % v['hour'], '%02d' % v['minute']
    digits_spec = (
        (TUBE_XS[0], hh[0], 'floor([HOUR_0_23] / 10)', '208 + 47 * sin(0.037699 * [MILLISECOND])', 'ON_VISIBLE ON_NEXT_HOUR'),
        (TUBE_XS[1], hh[1], '[HOUR_0_23] % 10', '208 + 47 * sin(0.037699 * [MILLISECOND] + 1.57)', 'ON_VISIBLE ON_NEXT_HOUR'),
        (TUBE_XS[2], mm[0], 'floor([MINUTE] / 10)', '206 + 49 * cos(0.031416 * [MILLISECOND])', 'ON_VISIBLE ON_NEXT_MINUTE'),
        (TUBE_XS[3], mm[1], '[MINUTE] % 10', '206 + 49 * sin(0.043982 * [MILLISECOND] + 2.4)', 'ON_VISIBLE ON_NEXT_MINUTE'),
    )
    glow_root = scene.group('nixie_glow_layer', vis='active')
    for idx, (x0, d_ch, expr, vib_expr, _) in enumerate(digits_spec):
        tg = glow_root.group(f'tube_glow_{idx}', x0, GLYPH_Y, GLYPH_W, GLYPH_H)
        el(tg.node, 'Transform', target='alpha', value=vib_expr)
        tg.bitmap_digit(0, 0, GLYPH_W, GLYPH_H, 'nixie_glow', 'PLASMA', d_ch, expr)

    colon_glow_grp = glow_root.group('colon_glow_grp', C - 12, COLON_CY - 26, 24, 52)
    el(colon_glow_grp.node, 'Transform', target='alpha', value='110 + 145 * (0.5 + 0.5 * cos(0.006283 * [MILLISECOND]))')
    colon_glow_grp.image('colon_glow', 0, 0, 24, 52, tint='PLASMA')

    # 5 · Incandescent thin-wire core layer (crisp & visible in both Active and dimmed AOD)
    core_root = scene.group('nixie_core_layer', ambient_alpha=165)
    for x0, d_ch, expr, _, _ in digits_spec:
        core_root.bitmap_digit(x0, GLYPH_Y, GLYPH_W, GLYPH_H, 'nixie_core', 'CORE', d_ch, expr)

    colon_core_grp = core_root.group('colon_core_grp', C - 12, COLON_CY - 26, 24, 52)
    el(colon_core_grp.node, 'Transform', target='alpha', value='155 + 100 * (0.5 + 0.5 * cos(0.006283 * [MILLISECOND]))')
    colon_core_grp.image('colon_core', 0, 0, 24, 52, tint='CORE')

    # 6 · Gas-discharge ignition strike flash inside tubes on wake & digit change
    flash_grp = scene.group('nixie_ignition', vis='active')
    for idx, (x0, _, _, _, trig) in enumerate(digits_spec):
        flash_grp.animated_strike('nixie_flash', FLASH_FRAMES, x0, TUBE_Y0, TUBE_W, TUBE_H, trig, 24, 'CORE')

    # 7 · Front cylindrical 3D glass envelopes + hexagonal honeycomb mesh (sits OVER glowing digits!)
    glass_grp = scene.group('tube_glass_front', vis='active')
    glass_grp.image('tube_glass_array', 0, 0, S, S)

    # 8 · Tier 1: Wide upper riveted instrument window (Heart Rate, Steps + bar, Battery + low-batt alert)
    inst = scene.group('instrument_plate', INST_X0, INST_Y0, INST_W, INST_H, vis='active')
    hr_g = inst.group('inst_heart', 18, 4, 100, 36, launch=HEALTH)
    hr_g.image('ic_heart', 12, 10, ICON_SM, ICON_SM, tint=CORAL)
    hr_g.text(56, 18, 54, 27, CORAL, str(v['heart']), '%s', ["[HEART_RATE] > 0 ? [HEART_RATE] : '--'"], family='teko_bold')

    st_g = inst.group('inst_steps', 118, 4, 120, 36, launch=HEALTH)
    st_g.image('ic_steps', 14, 10, ICON_SM, ICON_SM, tint=SAGE)
    for size, cond, prev in ((27, '[STEP_COUNT] < 10000 ? 255 : 0', True),
                             (22, '[STEP_COUNT] < 10000 ? 0 : 255', False)):
        sub = st_g.group(f'steps_sz_{size}', 34, 0, 82, 36, preview=prev)
        el(sub.node, 'Transform', target='alpha', value=cond)
        sub.text(36, 18, 72, size, CREAM, str(v['steps']), '%s', ['[STEP_COUNT]'], family='teko_bold')

    bt_g = inst.group('inst_batt', 238, 4, 100, 36, launch='BATTERY_STATUS')
    ok_b = bt_g.group('batt_ok', 0, 0, 100, 36, preview=True)
    el(ok_b.node, 'Transform', target='alpha', value='[BATTERY_PERCENT] <= 20 ? 0 : 255')
    ok_b.image('ic_battery', 12, 10, ICON_SM, ICON_SM, tint='ACCENT')
    ok_b.text(56, 18, 56, 27, 'ACCENT', f"{v['battery']}%", '%s%%', ['[BATTERY_PERCENT]'], family='teko_bold')
    low_b = bt_g.group('batt_low', 0, 0, 100, 36, preview=False)
    el(low_b.node, 'Transform', target='alpha', value='[BATTERY_PERCENT] <= 20 ? 255 : 0')
    low_b.image('ic_battery', 12, 10, ICON_SM, ICON_SM, tint=CORAL)
    low_b.text(56, 18, 56, 27, CORAL, f"{v['battery']}%", '%s%%', ['[BATTERY_PERCENT]'], family='teko_bold')

    # Full-width luminous bargraph across lower rim of Tier 1
    bar = inst.part_draw(INST_BAR_X, INST_BAR_Y, INST_BAR_W, INST_BAR_H)
    bar.rect_bar(0, 0, INST_BAR_W, INST_BAR_H, 2.2, TRACK_BG)
    bar.rect_bar(0, 0, INST_BAR_W, INST_BAR_H, 2.2, 'ACCENT',
                 expr=f'{INST_BAR_W} * clamp([STEP_COUNT] / clamp([STEP_GOAL], 1, 1000000), 0, 1)',
                 sample=v['steps'] / v['goal'])

    # 9 · Tier 2: Full-width recessed Weather & 2-Day Forecast Console + customizable shortcut
    build_weather_console(scene, v['weather'])

    # 10 · Tier 3: Curved bottom hardware row (Notifications + Big Round Voice Push-Button + Agenda/Complication)
    build_capsule_slot(scene, 0, SLOT_L_X, 'slot_notif_name', 'UNREAD_NOTIFICATION_COUNT', '2', 27, icon_bell)
    build_capsule_slot(scene, 1, SLOT_R_X, 'slot_right_name', 'NEXT_EVENT', '10:30', 21, icon_calendar)
    rec_g = scene.group('recorder_btn', MIC_X, MIC_Y, MIC_D, MIC_D, vis='active', launch=RECORDER)
    rec_ring = rec_g.part_draw(0, 0, MIC_D, MIC_D)
    rec_ring.ellipse(9, 9, MIC_D - 18, MIC_D - 18, stroke='ACCENT', thickness=1.5)
    rec_g.image('ic_mic', round((MIC_D - 26) / 2), round((MIC_D - 26) / 2), 26, 26, tint='ACCENT')

    # 11 · Minimal Always-On Display glass silhouettes
    aod = scene.group('aod_silhouettes', vis='ambient').part_draw()
    for x0 in TUBE_XS:
        aod.rrect(x0, TUBE_Y0 + 6, TUBE_W, TUBE_H - 6, 17, stroke=SLATE_AOD, thickness=1.2)
    for deg in (0, 90, 180, 270):
        rad = math.radians(deg)
        x1 = C + REHAUT_MID * math.sin(rad)
        y1 = C - REHAUT_MID * math.cos(rad)
        aod.rrect(x1 - 1.5, y1 - 1.5, 3, 3, 1.5, fill=SLATE_AOD)

    return wf, painter.img.resize((S, S), Image.LANCZOS)


def round_mask(img):
    mask = Image.new('L', (S * K, S * K), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, S * K - 1, S * K - 1], fill=255)
    out = Image.new('RGBA', (S, S), (0, 0, 0, 255))
    out.paste(img, (0, 0), mask.resize((S, S), Image.LANCZOS))
    return out.convert('RGB')


if __name__ == '__main__':
    wf, active = build('active', THEMES[0], 'titanium')
    ET.indent(wf, space='    ')
    for node in wf.iter():
        if node.tag in ('Font', 'BitmapFont', 'Upper', 'Template') and len(node):
            if node.tag != 'Template':
                node.text = None
            for inner in node:
                inner.tail = None
    ET.ElementTree(wf).write(ROOT / 'res/raw/watchface.xml', encoding='utf-8', xml_declaration=True)
    print('Generated:', ROOT / 'res/raw/watchface.xml')
    round_mask(active).save(ROOT / 'res/drawable/preview.png', optimize=True)
    round_mask(active).save(ROOT / 'design/preview-titanium-ambra.png')
    round_mask(build('ambient', THEMES[0], 'titanium')[1]).save(ROOT / 'design/preview-ambient.png')
    if '--all' in sys.argv:
        # Render showcase sheet: Titanium Ambra, Brass Ambra, Titanium VFD, Titanium Cobalto, Brass Rubino
        combos = [
            ('titanium', THEMES[0]),
            ('brass', THEMES[0]),
            ('titanium', THEMES[1]),
            ('titanium', THEMES[2]),
            ('brass', THEMES[3]),
        ]
        sheet = Image.new('RGB', (S * len(combos), S), (0, 0, 0))
        for i, (cf, th) in enumerate(combos):
            im = round_mask(build('active', th, cf)[1])
            im.save(ROOT / f'design/preview-{cf}-{th[0]}.png')
            sheet.paste(im, (S * i, 0))
        sheet.save(ROOT / 'design/preview-themes.png')
    print('Previews ready in design/')
