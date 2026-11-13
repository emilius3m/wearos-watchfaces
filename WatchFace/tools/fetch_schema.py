"""Fetch the official WFF 2 schema and its relative includes once."""
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import urljoin
from lxml import etree

ROOT = Path(__file__).resolve().parent / 'wff-schema-2'
BASE = 'https://raw.githubusercontent.com/google/watchface/main/third_party/wff/specification/documents/2/'
seen = set()

def fetch(relative='watchface.xsd'):
    target = (ROOT / relative).resolve()
    if target in seen:
        return
    seen.add(target)
    target.relative_to(ROOT.resolve())
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(urlopen(urljoin(BASE, target.relative_to(ROOT).as_posix()), timeout=30).read())
    tree = etree.parse(str(target))
    for node in tree.xpath('//*[@schemaLocation]'):
        child = (target.parent / node.get('schemaLocation')).resolve().relative_to(ROOT)
        fetch(str(child))

if __name__ == '__main__':
    fetch()
    print(f'Official WFF 2 schema: {len(seen)} files available.')
