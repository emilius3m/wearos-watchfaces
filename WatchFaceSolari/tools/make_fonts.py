"""Instantiate SemiBold (600) and Bold (700) Teko fonts from the variable font."""
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parents[1]
VAR = ROOT / 'design/teko_variable.ttf'
OUT = ROOT / 'res/font'

if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    for name, weight in (('teko_semibold', 600), ('teko_bold', 700)):
        f = instantiateVariableFont(TTFont(VAR), {'wght': weight})
        f['OS/2'].usWeightClass = weight
        target = OUT / f'{name}.ttf'
        f.save(target)
        print('Font:', target.name, target.stat().st_size, 'bytes')
