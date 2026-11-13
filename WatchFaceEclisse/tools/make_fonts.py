"""Instance the two static Teko weights used by ECLISSE from the variable font.

Teko is licensed under the SIL Open Font License 1.1 (see licenses/Teko-OFL.txt).
"""
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'design/teko_variable.ttf'

for stale in (ROOT / 'res/font').glob('*.ttf'):
    stale.unlink()
for name, weight in [('teko_regular', 400), ('teko_semibold', 600)]:
    font = instantiateVariableFont(TTFont(SOURCE), {'wght': weight})
    font['OS/2'].usWeightClass = weight
    target = ROOT / 'res/font' / f'{name}.ttf'
    font.save(target)
    print('Font:', target.name, target.stat().st_size, 'bytes')
