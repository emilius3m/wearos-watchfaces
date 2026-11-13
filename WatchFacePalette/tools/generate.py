"""Generate PALETTE, a vintage split-flap watch face: the WFF XML and a faithful preview.

Every element is declared once and sent to two backends: the Watch Face Format
document installed on the watch, and a Pillow painter that composes the same
layers into a preview with sample values. The watch shows real data.
"""
from pathlib import Path
import math
from xml.etree import ElementTree as ET
from PIL import Image, ImageDraw, ImageFont

from layout import *  # noqa: F401,F403 (geometry constants)

ROOT = Path(__file__).resolve().parents[1]
K = 3  # preview supersampling

# id, display name, accent
THEMES = [
    ('arancio', 'Arancio', '#FFF47024'),
    ('ottone', 'Ottone', '#FFE8B254'),
    ('rosso', 'Rosso', '#FFFF4D4D'),
    ('verde', 'Verde', '#FF5FE08A'),
    ('azzurro', 'Azzurro', '#FF5CB8FF'),
]
INK = '#FFF2E8D2'        # ivory digits
FLAP = '#FF28292E'
EDGE = '#FF4A4C54'
SPLIT = '#D7040405'      # hairline across the small flaps: thin, so the numbers stay whole
TRACK = '#FF2A2B30'
DARK = '#FF14100C'
BLACK = '#FF000000'
AOD_EDGE = '#FF3A3B41'

SAMPLE = dict(hour=9, minute=27, second=36, steps=6480, goal=10000, heart=72, battery=84,
              weekday='GIO', day='12', month='NOV', weather=dict(icon='partly', temperature=12, rain=30))
FAMILY, WEIGHT = 'teko_semibold', 'SEMI_BOLD'
# Teko vertical metrics (hhea ascent 0.958, descent 0.475, cap height 0.622): the line box is
# centred in its part, so the capitals sit 0.0695 em above the centre. Verified on the watch.
CAP_SHIFT = 0.0695
BASELINE = (0.958 - 0.475) / 2
# REC (C:\WatchProjects\WatchRec) starts recording as soon as it opens. The Samsung recorder, which
# only opens, was: com.samsung.android.wear.voicerecorder/com.samsung.android.wear.voicerecorder.view.MainActivity
RECORDER = 'com.local.rec/com.local.rec.RecordActivity'
HEALTH = 'com.samsung.android.wear.shealth/com.samsung.android.wear.shealth.app.home.HomeActivity'


def fmt(v):
    if isinstance(v, float):
        return ('%.3f' % v).rstrip('0').rstrip('.')
    return str(v)


def el(parent, tag, **attrs):
    return ET.SubElement(parent, tag, {k: fmt(v) for k, v in attrs.items()})


def xml_color(c):
    return '[CONFIGURATION.accent.0]' if c == 'ACCENT' else c


class Painter:
    """Pillow backend. Paints only what is visible in the requested mode."""

    def __init__(self, mode, theme):
        self.mode, self.theme = mode, theme
        self.img = Image.new('RGBA', (S * K, S * K), (0, 0, 0, 255))
        self.fonts = {}

    def rgba(self, c, dim=1.0):
        h = (self.theme[2] if c == 'ACCENT' else c).lstrip('#')
        a = int(h[:2], 16) if len(h) == 8 else 255
        h = h[-6:]
        return tuple(round(int(h[i:i + 2], 16) * dim) for i in (0, 2, 4)) + (a,)

    def shape(self, color, dim, fn):
        """Opaque colours draw straight on the image; translucent ones are composited."""
        rgba = self.rgba(color, dim)
        if rgba[3] == 255:
            fn(ImageDraw.Draw(self.img), rgba)
        else:
            layer = Image.new('RGBA', self.img.size, (0, 0, 0, 0))
            fn(ImageDraw.Draw(layer), rgba)
            self.img.alpha_composite(layer)

    def font(self, size):
        key = round(size * K, 2)
        if key not in self.fonts:
            self.fonts[key] = ImageFont.truetype(str(ROOT / f'res/font/{FAMILY}.ttf'), size * K)
        return self.fonts[key]

    def image(self, name, x, y, w, h, tint=None):
        src = Image.open(ROOT / f'res/drawable/{name}.png').convert('RGBA').resize((round(w * K), round(h * K)), Image.BICUBIC)
        if tint:
            solid = Image.new('RGBA', src.size, self.rgba(tint)[:3] + (255,))
            solid.putalpha(src.getchannel('A'))
            src = solid
        self.img.alpha_composite(src, (round(x * K), round(y * K)))


class Node:
    """A WFF element plus the absolute origin and visibility needed to preview it."""

    def __init__(self, node, painter, ox=0, oy=0, w=S, h=S, vis='both'):
        self.node, self.p = node, painter
        self.ox, self.oy, self.w, self.h, self.vis = ox, oy, w, h, vis

    @property
    def shown(self):
        return self.vis in ('both', self.p.mode)

    def ambient(self, node, value):
        el(node, 'Variant', mode='AMBIENT', target='alpha', value=value)

    def group(self, name, x=0, y=0, w=S, h=S, vis='both', preview=True, launch=None, **attrs):
        """vis: 'active' hides the group in ambient, 'ambient' shows it only there."""
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
        return Node(g, self.p, self.ox + x, self.oy + y, w, h, shown if preview else 'never')

    def part_draw(self):
        return Node(el(self.node, 'PartDraw', x=0, y=0, width=self.w, height=self.h), self.p, self.ox, self.oy,
                    self.w, self.h, self.vis)

    def _box(self, x, y, w, h, grow=0.0):
        return [(self.ox + x - grow) * K, (self.oy + y - grow) * K, (self.ox + x + w + grow) * K - 1,
                (self.oy + y + h + grow) * K - 1]

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
            self.p.shape(fill, 1, lambda d, c: d.rounded_rectangle(self._box(x, y, w, h), radius=r * K, fill=c))
        if stroke:
            o = thickness / 2
            self.p.shape(stroke, 1, lambda d, c: d.rounded_rectangle(self._box(x, y, w, h, o), radius=(r + o) * K,
                                                                    outline=c, width=max(1, round(thickness * K))))

    def rect(self, x, y, w, h, fill, expr=None, sample=1.0):
        """`expr` drives the live width on the watch; `sample` is the previewed fraction."""
        e = el(self.node, 'Rectangle', x=float(x), y=float(y), width=float(w), height=float(h))
        if expr:
            el(e, 'Transform', target='width', value=expr)
        el(e, 'Fill', color=xml_color(fill))
        if self.shown and w * sample > 0:
            self.p.shape(fill, 1, lambda d, c: d.rectangle(self._box(x, y, w * sample, h), fill=c))

    def circle(self, cx, cy, r, fill):
        e = el(self.node, 'Ellipse', x=float(cx - r), y=float(cy - r), width=float(r * 2), height=float(r * 2))
        el(e, 'Fill', color=xml_color(fill))
        if self.shown:
            self.p.shape(fill, 1, lambda d, c: d.ellipse(self._box(cx - r, cy - r, 2 * r, 2 * r), fill=c))

    def hline(self, x, y, w, color, thickness=1.0):
        l = el(self.node, 'Line', startX=float(x), startY=float(y), endX=float(x + w), endY=float(y))
        el(l, 'Stroke', color=xml_color(color), thickness=float(thickness), cap='BUTT')
        if self.shown:
            self.p.shape(color, 1, lambda d, c: d.rectangle(self._box(x, y - thickness / 2, w, thickness), fill=c))

    # ---- text ---------------------------------------------------------------
    def text(self, cx, cap_cy, width, size, color, sample, template='%s', params=(), upper=False, ambient=None):
        """Single centred line whose capitals are centred on `cap_cy`."""
        height = math.ceil(size * 1.5)
        x = round(cx - width / 2)          # part geometry is integer in WFF
        y = round(cap_cy + CAP_SHIFT * size - height / 2)
        cx = x + width / 2
        p = el(self.node, 'PartText', x=x, y=y, width=int(width), height=height)
        if ambient is not None:
            self.ambient(p, ambient)
        t = el(p, 'Text', align='CENTER', maxLines=1, ellipsis='TRUE')
        f = el(t, 'Font', family=FAMILY, size=float(size), weight=WEIGHT, color=xml_color(color))
        host = el(f, 'Upper') if upper else f
        if params:
            tpl = el(host, 'Template')
            tpl.text = template
            for expression in params:
                el(tpl, 'Parameter', expression=expression)
        else:
            host.text = template           # fixed text
        if not self.shown:
            return
        dim = (ambient / 255) if (ambient is not None and self.p.mode == 'ambient') else 1
        self.p.shape(color, dim, lambda d, c: d.text(((self.ox + cx) * K, (self.oy + y + height / 2 + BASELINE * size) * K),
                                                     sample, font=self.p.font(size), fill=c, anchor='ms'))

    # ---- bitmaps ------------------------------------------------------------
    def image(self, name, x, y, w, h, tint=None):
        attrs = dict(x=x, y=y, width=w, height=h)
        if tint:
            attrs['tintColor'] = xml_color(tint)
        el(el(self.node, 'PartImage', **attrs), 'Image', resource=name)
        if self.shown:
            self.p.image(name, self.ox + x, self.oy + y, w, h, tint)

    def condition(self, expressions, branches, default=None, preview=None):
        """WFF Condition: the first Compare whose named expression is true is drawn, else Default.
        Only the branch named `preview` is painted in the preview."""
        c = el(self.node, 'Condition')
        ex = el(c, 'Expressions')
        for name, expr in expressions.items():
            el(ex, 'Expression', name=name).text = expr
        for name, fn in branches:
            fn(Node(el(c, 'Compare', expression=name), self.p, self.ox, self.oy, self.w, self.h,
                    self.vis if name == preview else 'never'))
        if default:
            fn_vis = self.vis if preview not in [n for n, _ in branches] else 'never'
            default(Node(el(c, 'Default'), self.p, self.ox, self.oy, self.w, self.h, fn_vis))

    def flip(self, prefix, frames, x, y, w, h, trigger, fps):
        """The falling leaf: plays by itself on every new second, minute or hour."""
        part = el(self.node, 'PartAnimatedImage', x=x, y=y, width=w, height=h)
        el(part, 'AnimationController', play=trigger, beforePlaying='HIDE', afterPlaying='HIDE')
        seq = el(part, 'SequenceImages', loopCount=1, frameRate=fps)
        for i in range(frames):
            el(seq, 'Image', resource=f'{prefix}_{i + 1}')


# ---------------------------------------------------------------------------
def small_flap(d, x, y, w, h, r=8):
    d.rrect(x, y, w, h, r, fill=FLAP, stroke=EDGE, thickness=1.2)


def data_flap(scene, name, x, launch, icon, values, bar=None, bar_sample=0.0):
    """values: (size, sample, template, params, alpha condition or None, shown in preview)."""
    g = scene.group(name, x, DATA_Y, DATA_W, DATA_TAP_H, vis='active', launch=launch)
    small_flap(g.part_draw(), 0, 0, DATA_W, DATA_H, 11)
    for i, (size, sample, template, params, condition, preview) in enumerate(values):
        host = g
        if condition:
            host = g.group(f'{name}_size{i}', 0, 0, DATA_W, DATA_H, preview=preview)
            el(host.node, 'Transform', target='alpha', value=condition)
        host.text(DATA_W / 2, DATA_H / 2, DATA_W - 8, size, INK, sample, template, params)
    d = g.part_draw()
    d.hline(1, DATA_H / 2, DATA_W - 2, SPLIT)
    if bar:
        bx = (DATA_W - BAR_W) / 2
        d.rect(bx, BAR_Y - DATA_Y, BAR_W, BAR_H, TRACK)
        d.rect(bx, BAR_Y - DATA_Y, BAR_W, BAR_H, 'ACCENT', expr=bar, sample=bar_sample)
    g.image(icon, (DATA_W - ICON) // 2, ICON_Y - DATA_Y, ICON, ICON, tint='ACCENT')


# Watch Face Format weather conditions (WEATHER.CONDITION): 0 unknown, 1 clear, 2 cloudy, 3 fog,
# 4 heavy rain, 5 heavy snow, 6 rain, 7 snow, 8 sunny, 9 thunderstorm, 10 sleet, 11 light snow,
# 12 light rain, 13 mist, 14 partly cloudy, 15 windy. The first matching Compare wins.
def any_of(*codes):
    return ' || '.join(f'[WEATHER.CONDITION] == {c}' for c in codes)


WEATHER_ICONS = [
    ('sun', f'({any_of(1, 8)}) && [WEATHER.IS_DAY]', 'wx_sun'),
    ('moon', any_of(1, 8), 'wx_moon'),                 # clear, and the day test above failed
    ('partly', any_of(14), 'wx_partly'),
    ('cloud', any_of(2), 'wx_cloud'),
    ('fog', any_of(3, 13), 'wx_fog'),
    ('rain', any_of(4, 6, 12), 'wx_rain'),
    ('snow', any_of(5, 7, 10, 11), 'wx_snow'),
    ('storm', any_of(9), 'wx_storm'),
    ('wind', any_of(15), 'wx_wind'),
]
AVAILABLE = {'available': '[WEATHER.IS_AVAILABLE]'}


def weather_flaps(scene, sample):
    """Two flaps: current condition and temperature, then the chance of rain."""
    g = scene.group('weather', SLOT_X[0], SLOT_Y, SLOT_X[1] + SLOT_W - SLOT_X[0], SLOT_H, vis='active')
    right = SLOT_X[1] - SLOT_X[0]
    d = g.part_draw()
    small_flap(d, 0, 0, SLOT_W, SLOT_H)
    small_flap(d, right, 0, SLOT_W, SLOT_H)

    def icon(name):
        return lambda n: n.image(name, 8, 7, ICON, ICON, tint='ACCENT')

    def live(n):
        n.condition({name: expr for name, expr, _ in WEATHER_ICONS}, [(name, icon(res)) for name, _, res in WEATHER_ICONS],
                    default=icon('wx_cloud'), preview=sample['icon'])
        n.text(64, SLOT_H / 2, 56, 28, INK, '%d°' % sample['temperature'], '%s°', ['[WEATHER.TEMPERATURE]'])
        n.image('ic_umbrella', right + 8, 7, ICON, ICON, tint='ACCENT')
        n.text(right + 64, SLOT_H / 2, 56, 26, INK, '%d%%' % sample['rain'], '%s%%', ['[WEATHER.CHANCE_OF_PRECIPITATION]'])

    def missing(n):                     # no forecast yet (no phone, no location): say so plainly
        n.image('wx_cloud', 8, 7, ICON, ICON, tint=EDGE)
        n.text(64, SLOT_H / 2, 56, 28, INK, '--', '--')
        n.image('ic_umbrella', right + 8, 7, ICON, ICON, tint=EDGE)
        n.text(right + 64, SLOT_H / 2, 56, 26, INK, '--', '--')

    g.condition(AVAILABLE, [('available', live)], default=missing, preview='available')
    d = g.part_draw()
    d.hline(1, SLOT_H / 2, SLOT_W - 2, SPLIT)
    d.hline(right + 1, SLOT_H / 2, SLOT_W - 2, SPLIT)


def build(mode, theme):
    v = SAMPLE
    painter = Painter(mode, theme)
    wf = ET.Element('WatchFace', width=str(S), height=str(S), clipShape='CIRCLE')
    el(wf, 'Metadata', key='CLOCK_TYPE', value='DIGITAL')
    el(wf, 'Metadata', key='PREVIEW_TIME', value='%02d:%02d:%02d' % (v['hour'], v['minute'], v['second']))
    configs = el(wf, 'UserConfigurations')
    accent = el(configs, 'ColorConfiguration', id='accent', displayName='accent_name', defaultValue=THEMES[0][0])
    for key, _, color in THEMES:
        el(accent, 'ColorOption', id=key, displayName='color_' + key, colors=color)
    scene = Node(el(wf, 'Scene', backgroundColor=BLACK), painter)
    mid = BIG_Y + BIG_H / 2

    # 1 · Bodies of the two big flaps and of the three date flaps.
    bodies = scene.group('bodies', vis='active')
    for x in (HOUR_X, MINUTE_X):
        bodies.image('flap_big', x, BIG_Y, BIG_W, BIG_H)
    d = bodies.part_draw()
    for x, w in DATE:
        small_flap(d, x, DATE_Y, w, DATE_H, 7)

    # 2 · Hours and minutes. One fixed column per digit, so nothing shifts when a digit changes.
    time = scene.group('time')
    hh, mm = '%02d' % v['hour'], '%02d' % v['minute']
    for x0, digits, source in ((HOUR_X, hh, '[HOUR_0_23]'), (MINUTE_X, mm, '[MINUTE]')):
        for cx, sample, expr in ((x0 + 41, digits[0], f'floor({source} / 10)'), (x0 + 109, digits[1], f'{source} % 10')):
            time.text(cx, mid, 70, 142, INK, sample, '%s', [expr], ambient=175)
    for (x, w), sample, expr in zip(DATE, (v['weekday'], v['day'], v['month']), ('[DAY_OF_WEEK_S]', '[DAY]', '[MONTH_S]')):
        time.text(x + w / 2, DATE_Y + DATE_H / 2, w - 4, 30, INK, sample, '%s', [expr], upper=True, ambient=175)

    # 3 · In front of the digits: hinges, their shadow, and the falling leaf on each change.
    front = scene.group('hinges', vis='active')
    for x, trigger in ((HOUR_X, 'ON_NEXT_HOUR'), (MINUTE_X, 'ON_NEXT_MINUTE')):
        front.image('flap_big_overlay', x - PIN, BIG_Y, BIG_W + 2 * PIN, BIG_H)
        front.flip('flip_big', FLIP_BIG_FRAMES, x, BIG_Y, BIG_W, BIG_H, trigger, 20)
    d = front.part_draw()
    for x, w in DATE:
        d.hline(x + 1, DATE_Y + DATE_H / 2, w - 2, SPLIT)

    # 4 · Seconds: their own flap, flicking every second.
    sec = scene.group('seconds', SEC_X, SEC_Y, SEC_W, SEC_H, vis='active')
    small_flap(sec.part_draw(), 0, 0, SEC_W, SEC_H, 10)
    sec.text(SEC_W / 2, SEC_H / 2, SEC_W - 4, 58, 'ACCENT', '%02d' % v['second'], '%s', ['[SECOND_Z]'])
    sec.part_draw().hline(1, SEC_H / 2, SEC_W - 2, '#FF040405', 1.6)
    sec.flip('flip_small', FLIP_SMALL_FRAMES, 0, 0, SEC_W, SEC_H, 'ON_NEXT_SECOND', 30)

    # 5 · Recorder button: one tap opens REC, which is already recording.
    mic = scene.group('recorder', MIC_X - MIC_R, MIC_Y - MIC_R, MIC_R * 2, MIC_R * 2, vis='active', launch=RECORDER)
    mic.part_draw().circle(MIC_R, MIC_R, MIC_R, 'ACCENT')
    mic.image('ic_mic', MIC_R - 19, MIC_R - 19, 38, 38, tint=DARK)

    # 6 · Data flaps. No labels: the icon under each flap says what it is. Each one opens its app.
    data_flap(scene, 'steps', DATA_X[0], HEALTH, 'ic_steps',
              [(46, str(v['steps']), '%s', ['[STEP_COUNT]'], '[STEP_COUNT] < 10000 ? 255 : 0', v['steps'] < 10000),
               (38, str(v['steps']), '%s', ['[STEP_COUNT]'], '[STEP_COUNT] < 10000 ? 0 : 255', v['steps'] >= 10000)],
              f'{BAR_W} * clamp([STEP_COUNT] / clamp([STEP_GOAL], 1, 1000000), 0, 1)', v['steps'] / v['goal'])
    data_flap(scene, 'heart', DATA_X[1], 'HEALTH_HEART_RATE', 'ic_heart',
              [(46, str(v['heart']), '%s', ["[HEART_RATE] > 0 ? [HEART_RATE] : '--'"], None, True)])
    data_flap(scene, 'battery', DATA_X[2], 'BATTERY_STATUS', 'ic_battery',
              [(46, '%d%%' % v['battery'], '%s%%', ['[BATTERY_PERCENT]'], None, True)],
              f'{BAR_W} * clamp([BATTERY_PERCENT], 0, 100) / 100', v['battery'] / 100)

    # 7 · Weather: condition and temperature, chance of rain.
    weather_flaps(scene, v['weather'])

    # 8 · Always-on: only the outline of the two big flaps, with dimmed digits and date.
    aod = scene.group('outline', vis='ambient').part_draw()
    for x in (HOUR_X, MINUTE_X):
        aod.rrect(x, BIG_Y, BIG_W, BIG_H, BIG_R, stroke=AOD_EDGE, thickness=1.5)
        aod.hline(x, mid, BIG_W, BLACK, 3)
        aod.hline(x, mid + 2, BIG_W, AOD_EDGE, 1)
    return wf, painter.img


def round_image(img):
    mask = Image.new('L', (S * K, S * K), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, S * K - 1, S * K - 1], fill=255)
    out = Image.new('RGBA', (S * K, S * K), (0, 0, 0, 255))
    out.paste(img, (0, 0), mask)
    return out.resize((S, S), Image.LANCZOS).convert('RGB')


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
    round_image(active).save(ROOT / 'res/drawable/preview.png', optimize=True)
    round_image(active).save(ROOT / 'design/preview-arancio.png')
    round_image(build('ambient', THEMES[0])[1]).save(ROOT / 'design/preview-ambient.png')
    sheet = Image.new('RGB', (S * len(THEMES), S), (0, 0, 0))
    for i, theme in enumerate(THEMES):
        sheet.paste(round_image(build('active', theme)[1]), (S * i, 0))
    sheet.save(ROOT / 'design/preview-themes.png')
    print('Preview: design/preview-arancio.png, preview-ambient.png, preview-themes.png')
