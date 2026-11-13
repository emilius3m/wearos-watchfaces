from pathlib import Path
from lxml import etree
import xmlschema

ROOT = Path(__file__).resolve().parents[1]
schema_path = ROOT / 'tools/wff-schema-2/watchface.xsd'
if not schema_path.exists():
    raise SystemExit('Run python tools/fetch_schema.py first.')
schema = xmlschema.XMLSchema11(str(schema_path))
face = etree.parse(str(ROOT/'res/raw/watchface.xml'))
errors = list(schema.iter_errors(str(ROOT/'res/raw/watchface.xml')))
if errors:
    for error in errors[:12]:
        print(error.path, error.reason)
    print(f'{len(errors)} schema errors.')
    raise SystemExit(1)
# All custom fonts and string references must be packaged.
strings = {e.get('name') for e in etree.parse(str(ROOT/'res/values/strings.xml')).getroot()}
for node in face.xpath('//*[@displayName]'):
    assert node.get('displayName') in strings, node.get('displayName')
for node in face.xpath('//ScreenReader'):
    assert node.get('stringId') in strings, node.get('stringId')
for node in face.xpath('//Font'):
    family = node.get('family')
    if family != 'SYNC_TO_DEVICE':
        assert (ROOT / f'res/font/{family}.ttf').exists(), family
for config in face.xpath('//ColorConfiguration'):
    assert config.get('defaultValue') in {e.get('id') for e in config}
resources = {p.stem for folder in ROOT.glob('res/drawable*') for p in folder.iterdir() if p.is_file()}
for node in face.xpath('//Image'):
    resource=node.get('resource')
    if not resource.startswith('[COMPLICATION.'):
        assert resource in resources, f'Missing image: {resource}'
print('PASS: official WFF 2 XSD, resource references, palette defaults.')
