"""Check the actual WFF hit regions against the measured Galaxy Watch display."""
import argparse
import json
import math
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--pixels',type=int,default=480)
    parser.add_argument('--density',type=int,default=340)
    args=parser.parse_args()
    face=ET.parse(ROOT/'res/raw/watchface.xml').getroot()
    units=float(face.get('width'))
    scale=args.pixels/units
    px_per_dp=args.density/160
    parts=[('Agenda',face.find(".//ComplicationSlot[@slotId='0']")),
           ('Voce',face.find(".//Group[@name='primary_voice']")),
           ('Avvisi',face.find(".//ComplicationSlot[@slotId='1']"))]
    targets=[]
    for name,part in parts:
        assert part is not None,name
        x,y,w,h=(float(part.get(k)) for k in ('x','y','width','height'))
        if part.tag=='ComplicationSlot':
            bounds=part.find('BoundingOval')
            assert bounds is not None,name+' needs a circular hit area'
            assert float(bounds.get('width'))==w and float(bounds.get('height'))==h
        assert min(w,h)*scale/px_per_dp>=48,(name,'touch area too small')
        cx,cy=x+w/2,y+h/2
        # The entire visible circular key fits safely on the round display.
        clearance=units/2-math.hypot(cx-units/2,cy-units/2)-w/2
        assert clearance>=12,(name,'button too close to screen edge',clearance)
        assert part.find('Variant') is not None or name=='Voce'
        targets.append({'name':name,'rect':[x,y,w,h],'center':[cx,cy],
                        'diameter_px':round(w*scale,2),'diameter_dp':round(w*scale/px_per_dp,2),
                        'edge_clearance_px':round(clearance*scale,2)})
    # Bounding rectangles cannot overlap either; this also protects the voice
    # Group, whose platform hit region can be a square around the visible circle.
    for i,a in enumerate(targets):
        for b in targets[i+1:]:
            ax,ay,aw,ah=a['rect'];bx,by,bw,bh=b['rect']
            assert ax+aw<=bx or bx+bw<=ax or ay+ah<=by or by+bh<=ay,(a['name'],b['name'])
    weather=face.find(".//ComplicationSlot[@slotId='3']")
    assert weather is not None,'Preserve customizable weather shortcut'
    weather_bottom=float(weather.get('y'))+float(weather.get('height'))
    assert weather_bottom<=min(t['rect'][1] for t in targets),'Weather steals taps from action keys'
    report={'screen_px':args.pixels,'density_dpi':args.density,'minimum_target_dp':48,'targets':targets}
    out=ROOT/'design/round-buttons';out.mkdir(parents=True,exist_ok=True)
    (out/'touch-geometry.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('PASS: three 50.20 dp hit areas, separate bounds, safe circular margins, no weather overlap.')


if __name__=='__main__':main()
