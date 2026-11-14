"""Validate NIXIE against the official WFF 2 schema, packaged assets, and circular geometry."""
import math
from pathlib import Path
import re
from lxml import etree
import xmlschema

from layout import (
    C, REHAUT_IN, TUBE_XS, TUBE_Y0, TUBE_W, TUBE_H,
    INST_X0, INST_Y0, INST_W, INST_H, WX_X0, WX_Y0, WX_W, WX_H,
    SLOT_L_X, SLOT_R_X, SLOT_W, BOT_Y0, BOT_H, BOT_CAP_R, MIC_X, MIC_Y, MIC_D,
)

ROOT = Path(__file__).resolve().parents[1]
FACE = ROOT / 'res/raw/watchface.xml'
schema = xmlschema.XMLSchema11(str(ROOT / 'tools/wff-schema-2/watchface.xsd'))
errors = list(schema.iter_errors(str(FACE)))
for error in errors:
    print('SCHEMA:', error.path, error.reason)
if errors:
    raise SystemExit(1)

face = etree.parse(str(FACE))
strings = {e.get('name') for e in etree.parse(str(ROOT / 'res/values/strings.xml')).getroot()}
for node in face.xpath('//*[@displayName]'):
    assert node.get('displayName') in strings, f"missing string {node.get('displayName')}"
for node in face.xpath('//Font'):
    assert (ROOT / f"res/font/{node.get('family')}.ttf").exists(), f"missing font {node.get('family')}"
bm_families = {b.get('name') for b in face.xpath('//BitmapFonts/BitmapFont')}
for node in face.xpath('//BitmapFont'):
    if node.get('family'):
        assert node.get('family') in bm_families, f"missing bitmap font {node.get('family')}"
for node in face.xpath('//*[@resource]'):
    name = node.get('resource')
    if not name.startswith('['):
        assert (ROOT / f'res/drawable/{name}.png').exists(), f'missing drawable {name}'
xml_text = etree.tostring(face).decode()
for config in face.xpath('//ColorConfiguration'):
    options = {e.get('id'): e.get('colors').split() for e in config}
    assert config.get('defaultValue') in options
    assert len({len(c) for c in options.values()}) == 1, 'palettes must have the same number of colours'
    used = {int(i) for i in re.findall(r'\[CONFIGURATION\.%s\.(\d)\]' % config.get('id'), xml_text)}
    assert not used or max(used) < len(next(iter(options.values()))), 'palette index out of range'
groups = [g.get('name') for g in face.xpath('//Group')]
assert len(groups) == len(set(groups)), 'duplicate group names'

# Circular dial clearances and non-overlapping interactive targets
def max_r_rounded(x, y, w, h, cr):
    return max(math.hypot(px - C, py - C) + cr
               for px in (x + cr, x + w - cr) for py in (y + cr, y + h - cr))

for idx, x0 in enumerate(TUBE_XS):
    mr = max_r_rounded(x0, TUBE_Y0 + 6, TUBE_W, TUBE_H - 6, 17)
    assert mr < REHAUT_IN - 2.0, f'tube {idx} too close to rehaut: {mr:.2f} >= {REHAUT_IN}'

for label, rect, cr in (
    ('inst', (INST_X0, INST_Y0, INST_W, INST_H), 13),
    ('weather', (WX_X0, WX_Y0, WX_W, WX_H), 13),
    ('slot_left', (SLOT_L_X, BOT_Y0, SLOT_W, BOT_H), BOT_CAP_R),
    ('slot_right', (SLOT_R_X, BOT_Y0, SLOT_W, BOT_H), BOT_CAP_R),
    ('mic_center', (MIC_X, MIC_Y, MIC_D, MIC_D), MIC_D / 2),
):
    mr = max_r_rounded(*rect, cr)
    assert mr < REHAUT_IN - 2.0, f'{label} clips rehaut: {mr:.2f} >= {REHAUT_IN}'

bottom_boxes = [
    ('left', (SLOT_L_X, BOT_Y0, SLOT_W, BOT_H)),
    ('center', (MIC_X, MIC_Y, MIC_D, MIC_D)),
    ('right', (SLOT_R_X, BOT_Y0, SLOT_W, BOT_H)),
]
for i, (na, ra) in enumerate(bottom_boxes):
    assert WX_Y0 + WX_H < ra[1], f'weather overlaps {na}'
    for nb, rb in bottom_boxes[i + 1:]:
        assert ra[0] + ra[2] < rb[0] or rb[0] + rb[2] < ra[0], f'{na} overlaps {nb}'

print(f'PASS: official WFF 2 XSD, {len(face.xpath("//*"))} elements, strings, fonts, drawables, palettes, clearances.')
