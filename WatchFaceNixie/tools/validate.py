"""Validate NIXIE against the official WFF 2 schema and check all packaged assets."""
from pathlib import Path
import re
from lxml import etree
import xmlschema

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
print(f'PASS: official WFF 2 XSD, {len(face.xpath("//*"))} elements, strings, fonts, drawables, palettes.')
