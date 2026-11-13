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
    BOT_Y0, BOT_H, SLOT_X, SLOT_W, WX_X, WX_W, MIC_X, MIC_W, SEC_LABEL_Y,
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
    weather=dict(icon='partly', temperature=14),
)
FONTS = {'teko_semibold': 'SEMI_BOLD', 'teko_bold': 'BOLD'}
CAP_SHIFT = 0.0695
BASELINE = (0.958 - 0.475) / 2
HEALTH = 'com.samsung.android.wear.shealth/com.samsung.android.wear.shealth.app.home.HomeActivity'
RECORDER = 'com.samsung.android.wear.voicerecorder/com.samsung.android.wear.voicerecorder.view.MainActivity'


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


def build_notifications_slot(scene):
    s = el(scene.node, 'ComplicationSlot', x=SLOT_X, y=BOT_Y0, width=SLOT_W, height=BOT_H,
           slotId=0, displayName='slot_notif_name', isCustomizable='TRUE',
           supportedTypes='SHORT_TEXT RANGED_VALUE MONOCHROMATIC_IMAGE SMALL_IMAGE EMPTY')
    scene.ambient(s, 0)
    el(s, 'BoundingRoundBox', x=0, y=0, width=SLOT_W, height=BOT_H, cornerRadius=13)
    el(s, 'DefaultProviderPolicy', defaultSystemProvider='UNREAD_NOTIFICATION_COUNT', defaultSystemProviderType='SHORT_TEXT')
    silent = Painter('none', scene.p.theme, scene.p.case_finish)
    for kind in ('SHORT_TEXT', 'RANGED_VALUE', 'MONOCHROMATIC_IMAGE', 'SMALL_IMAGE', 'EMPTY'):
        live = kind == 'SHORT_TEXT'
        c = Node(el(s, 'Complication', type=kind), scene.p if live else silent, SLOT_X, BOT_Y0, SLOT_W, BOT_H, 'active')
        if kind in ('SHORT_TEXT', 'RANGED_VALUE'):
            im = el(c.node, 'PartImage', x=16, y=round(BOT_H / 2 - 9), width=18, height=18, tintColor=xml_color('ACCENT'))
            el(im, 'Image', resource='[COMPLICATION.MONOCHROMATIC_IMAGE]')
            if live:
                icon_bell(d_preview(c), 25, BOT_H / 2)
            c.text(56, BOT_H / 2 + 1, 38, 27, CREAM, '2', '%s', ['[COMPLICATION.TEXT]'])
        elif kind == 'MONOCHROMATIC_IMAGE':
            im = el(c.node, 'PartImage', x=round(SLOT_W / 2 - 12), y=round(BOT_H / 2 - 12),
                    width=24, height=24, tintColor=xml_color('ACCENT'))
            el(im, 'Image', resource='[COMPLICATION.MONOCHROMATIC_IMAGE]')
        elif kind == 'SMALL_IMAGE':
            im = el(c.node, 'PartImage', x=round(SLOT_W / 2 - 15), y=round(BOT_H / 2 - 15), width=30, height=30)
            el(im, 'Image', resource='[COMPLICATION.SMALL_IMAGE]')


def build_weather_slot(scene, sample):
    g = scene.group('weather', WX_X, BOT_Y0, WX_W, BOT_H, vis='active')

    def icon(name, tint='ACCENT'):
        return lambda n: n.image(name, 16, round(BOT_H / 2 - 11), 22, 22, tint=tint)

    def live(n):
        n.condition({name: expr for name, expr, _ in WEATHER_ICONS},
                    [(name, icon(res)) for name, _, res in WEATHER_ICONS],
                    default=icon('wx_cloud'), preview=sample['icon'])
        n.text(66, BOT_H / 2 + 1, 52, 27, CREAM, '%d°' % sample['temperature'], '%s°', ['[WEATHER.TEMPERATURE]'])

    def missing(n):
        icon('wx_cloud', tint=SLATE_AOD)(n)
        n.text(66, BOT_H / 2 + 1, 52, 27, SLATE_AOD, '--', '--')

    g.condition({'available': '[WEATHER.IS_AVAILABLE]'}, [('available', live)], default=missing, preview='available')


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

    # 2 · Orbiting neon seconds indicator bead along inner rehaut track (r = 207.5)
    sec_grp = scene.group('sec_crown', vis='active')
    analog = sec_grp.child(el(sec_grp.node, 'AnalogClock', x=0, y=0, width=S, height=S))
    analog.hand('SecondHand', 'sec_bead', C - 8, round(C - REHAUT_MID - 8), 16, 16, v['second'] * 6, 'ACCENT')

    # 3 · Top Italian date caption
    date_sample = f"{v['weekday']} · {v['day']} {v['month']}"
    scene.text(C, DATE_Y - 5, 220, 25, PARCHMENT, date_sample, '%s · %s %s',
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

    # 8 · Upper recessed instrument window (Heart Rate, Steps + bar, Battery + low-batt alert)
    inst = scene.group('instrument_plate', INST_X0, INST_Y0, INST_W, INST_H, vis='active')
    hr_g = inst.group('inst_heart', 12, 4, 84, 36, launch=HEALTH)
    hr_g.image('ic_heart', 14, 11, ICON_SM, ICON_SM, tint=CORAL)
    hr_g.text(50, 18, 44, 27, CORAL, str(v['heart']), '%s', ["[HEART_RATE] > 0 ? [HEART_RATE] : '--'"], family='teko_bold')

    st_g = inst.group('inst_steps', 98, 4, 102, 36, launch=HEALTH)
    st_g.image('ic_steps', 10, 11, ICON_SM, ICON_SM, tint=SAGE)
    for size, cond, prev in ((27, '[STEP_COUNT] < 10000 ? 255 : 0', True),
                             (22, '[STEP_COUNT] < 10000 ? 0 : 255', False)):
        sub = st_g.group(f'steps_sz_{size}', 28, 0, 74, 36, preview=prev)
        el(sub.node, 'Transform', target='alpha', value=cond)
        sub.text(30, 18, 60, size, CREAM, str(v['steps']), '%s', ['[STEP_COUNT]'], family='teko_bold')

    bt_g = inst.group('inst_batt', 202, 4, 84, 36, launch='BATTERY_STATUS')
    ok_b = bt_g.group('batt_ok', 0, 0, 84, 36, preview=True)
    el(ok_b.node, 'Transform', target='alpha', value='[BATTERY_PERCENT] <= 20 ? 0 : 255')
    ok_b.image('ic_battery', 8, 11, ICON_SM, ICON_SM, tint='ACCENT')
    ok_b.text(48, 18, 52, 27, 'ACCENT', f"{v['battery']}%", '%s%%', ['[BATTERY_PERCENT]'], family='teko_bold')
    low_b = bt_g.group('batt_low', 0, 0, 84, 36, preview=False)
    el(low_b.node, 'Transform', target='alpha', value='[BATTERY_PERCENT] <= 20 ? 255 : 0')
    low_b.image('ic_battery', 8, 11, ICON_SM, ICON_SM, tint=CORAL)
    low_b.text(48, 18, 52, 27, CORAL, f"{v['battery']}%", '%s%%', ['[BATTERY_PERCENT]'], family='teko_bold')

    # Thin luminous bargraph across lower rim of upper instrument window
    bar = inst.part_draw(INST_BAR_X, INST_BAR_Y, INST_BAR_W, INST_BAR_H)
    bar.rect_bar(0, 0, INST_BAR_W, INST_BAR_H, 2.2, TRACK_BG)
    bar.rect_bar(0, 0, INST_BAR_W, INST_BAR_H, 2.2, 'ACCENT',
                 expr=f'{INST_BAR_W} * clamp([STEP_COUNT] / clamp([STEP_GOAL], 1, 1000000), 0, 1)',
                 sample=v['steps'] / v['goal'])

    # 9 · Bottom physical modules: Notifications complication + Native Weather + Voice Recorder push-button
    build_notifications_slot(scene)
    build_weather_slot(scene, v['weather'])
    rec_g = scene.group('recorder_btn', MIC_X, BOT_Y0, MIC_W, BOT_H, vis='active', launch=RECORDER)
    rec_g.image('ic_mic', round(MIC_W / 2 - 11), round(BOT_H / 2 - 11), 22, 22, tint='ACCENT')

    # 10 · Plain seconds readout below (active mode only; hidden in AOD)
    scene.text(C, SEC_LABEL_Y - 3, 90, 20, 'ACCENT', f"{v['second']:02d} SEC", '%s%s SEC',
               ['floor([SECOND] / 10)', '[SECOND] % 10'], ambient=0)

    # 11 · Minimal Always-On Display glass silhouettes
    aod = scene.group('aod_silhouettes', vis='ambient').part_draw()
    for x0 in TUBE_XS:
        aod.rrect(x0, TUBE_Y0 + 6, TUBE_W, TUBE_H - 6, 17, stroke=SLATE_AOD, thickness=1.2)
    for deg in (0, 90, 180, 270):
        rad = math.radians(deg)
        x1 = C + 224 * math.sin(rad)
        y1 = C - 224 * math.cos(rad)
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
