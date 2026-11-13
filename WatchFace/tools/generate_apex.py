"""Generate the native, vector-only APEX watch face. Coordinates: 450 x 450.

The installed face uses real WFF data. No demo data is packaged in the face.
"""
from pathlib import Path
import math
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ACCENT = '[CONFIGURATION.apexPalette.0]'
DIM = '[CONFIGURATION.apexPalette.1]'
INK = '#FFF0F4ED'
MUTED = '#FF929D91'
TRACK = '#FF20271F'

def el(parent, tag, **attrs):
    return ET.SubElement(parent, tag, {k: str(v) for k, v in attrs.items()})

def ambient(parent, value=0):
    el(parent, 'Variant', mode='AMBIENT', target='alpha', value=value)

def group(parent, x=0, y=0, width=450, height=450, hide=True, **attrs):
    attrs.setdefault('name', f'apex_{len(list(wf.iter("Group")))}')
    g = el(parent, 'Group', x=x, y=y, width=width, height=height, **attrs)
    if hide: ambient(g)
    return g

def draw(parent, x=0, y=0, width=450, height=450):
    return el(parent, 'PartDraw', x=x, y=y, width=width, height=height)

def line(parent, x1, y1, x2, y2, color, thickness=1, cap='ROUND'):
    l = el(parent, 'Line', startX=round(x1, 3), startY=round(y1, 3), endX=round(x2, 3), endY=round(y2, 3))
    el(l, 'Stroke', color=color, thickness=thickness, cap=cap)
    return l

def circle(parent, cx, cy, r, fill=None, stroke=None, thickness=1):
    p = el(parent, 'Ellipse', x=cx-r, y=cy-r, width=r*2, height=r*2)
    if fill: el(p, 'Fill', color=fill)
    if stroke: el(p, 'Stroke', color=stroke, thickness=thickness)
    return p

def arc(parent, cx, cy, r, start, end, color, thickness, transform=None, direction='CLOCKWISE', cap='ROUND'):
    p = el(parent, 'Arc', centerX=cx, centerY=cy, width=r*2, height=r*2, startAngle=start, endAngle=end, direction=direction)
    if transform: el(p, 'Transform', target='endAngle', value=transform)
    el(p, 'Stroke', color=color, thickness=thickness, cap=cap)
    return p

def text(parent, x, y, width, height, size, color, value=None, expression=None, family='SYNC_TO_DEVICE', weight='MEDIUM', outline=False, spacing=None):
    p = el(parent, 'PartText', x=x, y=y, width=width, height=height)
    t = el(p, 'Text', align='CENTER', maxLines=1, ellipsis='TRUE')
    attrs = dict(family=family, size=size, weight=weight, color=color)
    if spacing is not None: attrs['letterSpacing'] = spacing
    f = el(t, 'Font', **attrs)
    if outline: f = el(f, 'Outline', color='#FF8C9989', width=1)
    if expression:
        template = el(f, 'Template')
        template.text = value or '%s'
        el(template, 'Parameter', expression=expression)
    else:
        f.text = value
    return p

def mic(parent):
    p = draw(parent, 0, 0, 64, 64)
    circle(p, 32, 32, 30, fill=ACCENT)
    r = el(p, 'RoundRectangle', x=27, y=15, width=10, height=21, cornerRadiusX=5, cornerRadiusY=5)
    el(r, 'Fill', color='#FF10150A')
    arc(p, 32, 29, 10, 90, 270, '#FF10150A', 2.5)
    line(p, 32, 40, 32, 47, '#FF10150A', 2.5)
    line(p, 25, 47, 39, 47, '#FF10150A', 2.5)

def slot(parent, x, slot_id, name, provider):
    s = el(parent, 'ComplicationSlot', x=x, y=347, width=76, height=66, slotId=slot_id, displayName=name, isCustomizable='TRUE', supportedTypes='SHORT_TEXT RANGED_VALUE MONOCHROMATIC_IMAGE SMALL_IMAGE EMPTY')
    ambient(s)
    el(s, 'BoundingOval', x=0, y=0, width=76, height=66)
    el(s, 'DefaultProviderPolicy', defaultSystemProvider=provider, defaultSystemProviderType='SHORT_TEXT')
    for kind in ('SHORT_TEXT', 'RANGED_VALUE'):
        c = el(s, 'Complication', type=kind)
        if kind == 'RANGED_VALUE':
            p = draw(c, 0, 0, 76, 66)
            arc(p, 38, 29, 24, 215, 505, TRACK, 2)
            arc(p, 38, 29, 24, 215, 215, ACCENT, 2,
                '215 + clamp(([COMPLICATION.RANGED_VALUE_VALUE] - [COMPLICATION.RANGED_VALUE_MIN]) / clamp([COMPLICATION.RANGED_VALUE_MAX] - [COMPLICATION.RANGED_VALUE_MIN], 1, 1000000000), 0, 1) * 290')
        im = el(c, 'PartImage', x=27, y=6, width=22, height=22, tintColor=ACCENT)
        el(im, 'Image', resource='[COMPLICATION.MONOCHROMATIC_IMAGE]')
        text(c, 0, 35, 76, 22, 14, INK, expression='[COMPLICATION.TEXT]')
    for kind, key in [('MONOCHROMATIC_IMAGE', 'MONOCHROMATIC_IMAGE'), ('SMALL_IMAGE', 'SMALL_IMAGE')]:
        c = el(s, 'Complication', type=kind)
        attrs = dict(x=21, y=14, width=34, height=34)
        if kind == 'MONOCHROMATIC_IMAGE': attrs['tintColor'] = ACCENT
        im = el(c, 'PartImage', **attrs)
        el(im, 'Image', resource=f'[COMPLICATION.{key}]')
    el(s, 'Complication', type='EMPTY')
    return s

wf = ET.Element('WatchFace', width='450', height='450', clipShape='CIRCLE')
configs = el(wf, 'UserConfigurations')
palette = el(configs, 'ColorConfiguration', id='apexPalette', displayName='theme_color_name', defaultValue='volt')
for key, colors in [
    ('volt', '#FFD5FF45 #FF556322'),
    ('ice', '#FF8DE5FF #FF284F60'),
    ('ember', '#FFFF9450 #FF643C25'),
    ('white', '#FFE8EDE5 #FF4A5147'),
    ('red', '#FFFF5964 #FF64262D'),
]:
    el(palette, 'ColorOption', id=key, displayName='color_'+key, colors=colors)
scene = el(wf, 'Scene', backgroundColor='#FF000000')

# Fixed precision index. No fake sensor graphs or simulated measurements.
bezel = group(scene)
p = draw(bezel)
circle(p, 225, 225, 201, stroke='#FF161D16', thickness=1)
for i in range(60):
    a = math.radians(i * 6)
    r1 = 204 if i % 5 == 0 else 212
    c = '#FF798374' if i % 5 == 0 else '#FF35402F'
    line(p, 225 + math.sin(a)*r1, 225-math.cos(a)*r1,
         225+math.sin(a)*219, 225-math.cos(a)*219, c, 2 if i % 5 == 0 else 1.5, 'BUTT')

# The outer left arc measures the daily step goal; the right arc measures charge.
for start, end, expr in [
    (216, 326, '216 + clamp([STEP_COUNT] / clamp([STEP_GOAL], 1, 1000000), 0, 1) * 110'),
    (34, 144, '34 + clamp([BATTERY_PERCENT], 0, 100) * 1.1')
]:
    arc(p, 225, 225, 191, start, end, TRACK, 7)
    arc(p, 225, 225, 191, start, start, ACCENT, 7, expr)
    for j in range(1, 20):
        a = math.radians(start + j * (end-start)/20)
        line(p, 225+math.sin(a)*186, 225-math.cos(a)*186,
             225+math.sin(a)*196, 225-math.cos(a)*196, '#FF000000', 1.6, 'BUTT')

# A small orbiting seconds marker with a short, three-stage trail.
orbit = group(scene, pivotX=0.5, pivotY=0.5)
el(orbit, 'Transform', target='angle', value='[SECOND] * 6')
p = draw(orbit)
for a, c, t in [(-12, '#FF263217', 2), (-8, DIM, 2.5), (-4, ACCENT, 3)]:
    arc(p, 225, 225, 224, a, a+3, c, t)
line(p, 225, 3, 225, 21, ACCENT, 4, 'BUTT')

# Reserved top area leaves the operating system's charging/notification icons clear.
date = text(scene, 110, 54, 230, 27, 18, INK, value='%s  %s  %s')
font = date.find('./Text/Font')
font.text = None
tpl = el(font, 'Template'); tpl.text = '%s  %s  %s'
for v in ('DAY_OF_WEEK_S', 'DAY', 'MONTH_S'):
    el(tpl, 'Parameter', expression=f'[{v}]')
ambient(date, 130)

# Separate digit columns prevent proportional-font jitter at minute changes.
def time_digits(parent, outlined=False):
    for y, expression, color in [(88, '[HOUR_0_23]', INK), (213, '[MINUTE]', ACCENT)]:
        for x, expr in [(72, f'floor({expression} / 10)'), (162, f'{expression} % 10')]:
            text(parent, x, y, 95, 140, 184, '#FF000000' if outlined else color,
                 expression=expr, family='teko_semibold', weight='SEMI_BOLD', outline=outlined)

active = group(scene)
time_digits(active)
aod = group(scene, hide=False, alpha=0)
ambient(aod, 255)
time_digits(aod, True)

side = group(scene, 273, 88, 102, 249)
p = draw(side, 0, 25, 102, 80)
arc(p, 51, 40, 36, 0, 360, TRACK, 2)
arc(p, 51, 40, 36, 0, 0, ACCENT, 2.5, '[SECOND] * 6')
text(side, 12, 32, 78, 50, 44, INK, expression='[SECOND_Z]', family='teko_semibold')
text(side, 7, 77, 88, 17, 11, MUTED, value='SEC')

hr = group(side, 0, 111, 102, 43, hide=False)
el(hr, 'Launch', target='HEALTH_HEART_RATE')
p = draw(hr, 3, 12, 24, 24)
for a,b,c,d in [(0,12,5,12),(5,12,9,4),(9,4,14,20),(14,20,18,9),(18,9,22,12)]:
    line(p, a,b,c,d, ACCENT, 1.8)
text(hr, 27, -5, 74, 44, 36, INK, expression="[HEART_RATE] > 0 ? [HEART_RATE] : '--'", family='teko_semibold')
text(hr, 27, 30, 74, 17, 10, MUTED, value='BPM')

steps = group(side, 0, 164, 102, 43, hide=False)
el(steps, 'Launch', target='com.samsung.android.wear.shealth/com.samsung.android.wear.shealth.app.home.HomeActivity')
p = draw(steps, 4, 12, 24, 24)
for x,y in [(3,2),(12,8)]:
    r=el(p, 'Ellipse', x=x, y=y, width=6, height=11); el(r,'Fill',color=ACCENT)
text(steps, 23, -5, 80, 44, 32, INK, expression='[STEP_COUNT]', family='teko_semibold')
text(steps, 25, 30, 78, 17, 10, MUTED, value='PASSI')

battery = group(side, 0, 217, 102, 40, hide=False)
el(battery, 'Launch', target='BATTERY_STATUS')
p = draw(battery, 2, 12, 25, 20)
r = el(p, 'RoundRectangle', x=0, y=2, width=18, height=10, cornerRadiusX=2, cornerRadiusY=2)
el(r, 'Stroke', color=ACCENT, thickness=1.8)
line(p, 21, 5, 21, 9, ACCENT, 2)
r = el(p, 'Rectangle', x=3, y=5, width=12, height=4)
el(r, 'Transform', target='width', value='12 * clamp([BATTERY_PERCENT], 0, 100) / 100')
el(r, 'Fill', color=ACCENT)
text(battery, 25, -7, 78, 44, 30, INK, value='%s%%', expression='[BATTERY_PERCENT]', family='teko_semibold')

# Low charge has a concrete meaning: only the battery readout turns red below 20%.
low = group(scene, 273, 305, 102, 40)
el(low, 'Transform', target='alpha', value='[BATTERY_PERCENT] < 20 ? 255 : 0')
text(low, 25, -7, 78, 44, 30, '#FFFF5964', value='%s%%', expression='[BATTERY_PERCENT]', family='teko_semibold')

slot(scene, 104, 0, 'slot_left_name', 'UNREAD_NOTIFICATION_COUNT')
slot(scene, 270, 1, 'slot_right_name', 'NEXT_EVENT')
button = group(scene, 193, 348, 64, 64)
el(button, 'Launch', target='com.samsung.android.wear.voicerecorder/com.samsung.android.wear.voicerecorder.view.MainActivity')
mic(button)

ET.indent(wf, space='    ')
ET.ElementTree(wf).write(ROOT/'res/raw/watchface.xml', encoding='utf-8', xml_declaration=True)
print('Generated native APEX face:', ROOT/'res/raw/watchface.xml')
