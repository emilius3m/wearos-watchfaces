"""Offline rendering of the generated XML subset for visual QA, not a device emulator.

Forecast fixture values are illustrative and are never packaged into the APK.
"""
from pathlib import Path
from xml.etree import ElementTree as ET
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from PIL import Image,ImageDraw,ImageFont,ImageChops
import math,re

ROOT=Path(__file__).resolve().parents[1]
TREE=ET.parse(ROOT/'res/raw/watchface.xml')
S=2
DEMO={'WEATHER.IS_AVAILABLE':True,'WEATHER.IS_ERROR':False,'WEATHER.TEMPERATURE':16,'WEATHER.CONDITION':14,'WEATHER.CONDITION_NAME':'Poco nuvoloso',
      'STEP_COUNT':510,'HEART_RATE':77,'BATTERY_PERCENT':81,
      'CONFIGURATION.verticalPalette.0':'#FFD5FF45','CONFIGURATION.verticalPalette.1':'#FFF3ECDD',
      'COMPLICATION.TEXT':'Nessuno','COMPLICATION.MONOCHROMATIC_IMAGE':'demo_calendar'}
for i,(condition,low,high) in enumerate([(2,6,10),(6,9,14),(14,8,15)],1):
    DEMO.update({f'WEATHER.DAYS.{i}.IS_AVAILABLE':True,f'WEATHER.DAYS.{i}.CONDITION_DAY':condition,
                 f'WEATHER.DAYS.{i}.TEMPERATURE_LOW':low,f'WEATHER.DAYS.{i}.TEMPERATURE_HIGH':high})

class Renderer:
    def __init__(self,date,ambient=False,weather=True):
        self.date=date; self.ambient=ambient; self.data=dict(DEMO)
        self.data.update({'HOUR_0_23':date.hour,'MINUTE':date.minute,'MINUTE_UNITS_DIGIT':date.minute%10,
                          'MINUTE_TENS_DIGIT':date.minute//10,'SECOND':date.second,'SECOND_Z':f'{date.second:02}',
                          'HOUR_0_23_Z':f'{date.hour:02}','MINUTE_Z':f'{date.minute:02}',
                          'MILLISECOND':date.microsecond//1000,'SECONDS_IN_DAY':date.hour*3600+date.minute*60+date.second,
                          'UTC_TIMESTAMP':int(date.timestamp()*1000),'WEATHER.LAST_UPDATED':int(date.timestamp()*1000)-300000})
        self.data['WEATHER.IS_AVAILABLE']=weather
    def icu(self,pattern,timestamp=None):
        d=self.date if timestamp is None else datetime.fromtimestamp(float(timestamp)/1000,self.date.tzinfo)
        days=['Lun','Mar','Mer','Gio','Ven','Sab','Dom']; months=['Gen','Feb','Mar','Apr','Mag','Giu','Lug','Ago','Set','Ott','Nov','Dic']
        return {'EEE d MMM':f'{days[d.weekday()]} {d.day} {months[d.month-1]}','EEE d':f'{days[d.weekday()]} {d.day}',
                'HH:mm':f'{d.hour:02}:{d.minute:02}'}[pattern]
    def expr(self,expr):
        expr=re.sub(r'\[([^]]+)\]',lambda m:repr(self.data[m[1]]),expr)
        if '?' in expr:
            test,rest=expr.split('?',1); yes,no=rest.split(':',1)
            expr=f'({yes} if {test} else {no})'
        expr=expr.replace('&&',' and ').replace('||',' or ')
        return eval(expr,{'__builtins__':{}},{'floor':math.floor,'sin':math.sin,'cos':math.cos,'rad':math.radians,
                    'clamp':lambda x,a,b:min(max(x,a),b),'icuText':self.icu})
    def attrs(self,node):
        a=dict(node.attrib)
        for t in node.findall('Transform'): a[t.get('target')]=self.expr(t.get('value'))
        if self.ambient:
            for v in node.findall('Variant'):
                if v.get('mode')=='AMBIENT': a[v.get('target')]=v.get('value')
        return a
    def color(self,value):
        if value.startswith('['): value=self.expr(value)
        h=value.lstrip('#')
        if len(h)==8: return tuple(int(h[i:i+2],16) for i in (2,4,6,0))
        return tuple(int(h[i:i+2],16) for i in (0,2,4))+(255,)
    def shape(self,node,canvas):
        a=self.attrs(node); d=ImageDraw.Draw(canvas)
        n=lambda k,default=0:float(a.get(k,default))*S
        fill=node.find('Fill'); stroke=node.find('Stroke')
        fc=self.color(fill.get('color')) if fill is not None else None
        sc=self.color(stroke.get('color')) if stroke is not None else None
        sw=max(1,round(float(stroke.get('thickness','1'))*S)) if stroke is not None else 1
        if node.tag=='Line':
            pts=(n('startX'),n('startY'),n('endX'),n('endY')); d.line(pts,fill=sc,width=sw)
            if stroke.get('cap','ROUND')=='ROUND':
                for x,y in [pts[:2],pts[2:]]:d.ellipse((x-sw/2,y-sw/2,x+sw/2,y+sw/2),fill=sc)
        elif node.tag=='Arc':
            cx,cy,w,h=n('centerX'),n('centerY'),n('width'),n('height')
            start,end=float(a['startAngle'])-90,float(a['endAngle'])-90
            if abs(end-start)<.001:return
            d.arc((cx-w/2,cy-h/2,cx+w/2,cy+h/2),start,end,fill=sc,width=sw)
        else:
            x,y,w,h=n('x'),n('y'),n('width'),n('height');box=(x,y,x+w,y+h)
            if node.tag=='Ellipse':d.ellipse(box,fill=fc,outline=sc,width=sw)
            elif node.tag=='RoundRectangle':d.rounded_rectangle(box,radius=n('cornerRadiusX'),fill=fc,outline=sc,width=sw)
            elif node.tag=='Rectangle':d.rectangle(box,fill=fc,outline=sc,width=sw)
    def node(self,node,canvas):
        tag=node.tag
        if tag=='Condition':
            expressions={e.get('name'):e.text for e in node.find('Expressions')}
            chosen=node.find('Default')
            for b in node.findall('Compare'):
                if self.expr(expressions[b.get('expression')]): chosen=b;break
            if chosen is not None:
                for child in chosen:self.node(child,canvas)
            return
        if tag in ('Line','Arc','Rectangle','RoundRectangle','Ellipse'):
            self.shape(node,canvas);return
        if tag not in ('Group','PartDraw','PartImage','PartText','ComplicationSlot'): return
        a=self.attrs(node); alpha=int(float(a.get('alpha',255)))
        if alpha<=0:return
        w,h=int(float(a.get('width',450))),int(float(a.get('height',450)))
        sx,sy=float(a.get('scaleX',1)),float(a.get('scaleY',1))
        if sx<.00001 or sy<.00001:return
        layer=Image.new('RGBA',(w*S,h*S))
        if tag=='PartImage':
            resource=node.find('Image').get('resource')
            if resource.startswith('[COMPLICATION.'):
                icon=Image.new('RGBA',(40,40));d=ImageDraw.Draw(icon);color=self.color(self.data['CONFIGURATION.verticalPalette.1'])
                if self.data['COMPLICATION.MONOCHROMATIC_IMAGE']=='demo_calendar':
                    d.rounded_rectangle((5,6,35,36),radius=3,outline=color,width=3)
                    d.line((5,14,35,14),fill=color,width=2)
                    for x in (12,28):d.line((x,2,x,10),fill=color,width=3)
                else:
                    d.ellipse((11,4,29,28),fill=color)
                    d.rectangle((11,15,29,29),fill=color)
                    d.rounded_rectangle((6,26,34,31),radius=2,fill=color)
                    d.ellipse((17,32,23,38),fill=color)
                layer=icon.resize((w*S,h*S),Image.Resampling.LANCZOS)
            else: layer=asset(resource).resize((w*S,h*S),Image.Resampling.LANCZOS)
        elif tag=='PartText':
            font_node=node.find('./Text/Font'); template=font_node.find('Template')
            if template is not None:
                args=[self.expr(p.get('expression')) for p in template]
                args=[int(v) if isinstance(v,float) and v.is_integer() else v for v in args]
                string=(template.text or '')%tuple(args)
            else:string=(font_node.text or '').strip()
            path=ROOT/'res/font/teko_semibold.ttf' if font_node.get('family')=='teko_semibold' else Path('C:/Windows/Fonts/arial.ttf')
            font=ImageFont.truetype(str(path),round(float(font_node.get('size'))*S))
            d=ImageDraw.Draw(layer); box=d.textbbox((0,0),string,font=font)
            # Approximation of native text alignment; image-based digits are exact assets.
            x=(w*S-box[2]+box[0])/2-box[0];y=(h*S-box[3]+box[1])/2-box[1]
            d.text((x,y),string,font=font,fill=self.color(font_node.get('color',INK)))
        elif tag=='ComplicationSlot':
            original_text=self.data['COMPLICATION.TEXT'];original_icon=self.data['COMPLICATION.MONOCHROMATIC_IMAGE']
            notification=node.get('slotId')=='1'
            self.data['COMPLICATION.TEXT']='1' if notification else 'Nessuno'
            self.data['COMPLICATION.MONOCHROMATIC_IMAGE']='demo_bell' if notification else 'demo_calendar'
            child=node.find("Complication[@type='SHORT_TEXT']")
            if child is not None:
                for item in child:self.node(item,layer)
            self.data['COMPLICATION.TEXT']=original_text;self.data['COMPLICATION.MONOCHROMATIC_IMAGE']=original_icon
        else:
            for child in node:self.node(child,layer)
        if 'tintColor' in a:
            tint=Image.new('RGBA',layer.size,self.color(a['tintColor']));tint.putalpha(layer.getchannel('A'));layer=tint
        if alpha<255:layer.putalpha(layer.getchannel('A').point(lambda p:round(p*alpha/255)))
        if sx!=1 or sy!=1:layer=layer.resize((max(1,round(w*S*sx)),max(1,round(h*S*sy))),Image.Resampling.LANCZOS)
        if float(a.get('angle',0)):
            layer=layer.rotate(-float(a['angle']),resample=Image.Resampling.BICUBIC,
                               center=(float(a.get('pivotX',.5))*layer.width,float(a.get('pivotY',.5))*layer.height))
        x=float(a.get('x',0))+float(a.get('pivotX',.5))*w*(1-sx)
        y=float(a.get('y',0))+float(a.get('pivotY',.5))*h*(1-sy)
        canvas.alpha_composite(layer,(round(x*S),round(y*S)))
    def render(self):
        canvas=Image.new('RGBA',(450*S,450*S),'black')
        for node in TREE.find('Scene'):self.node(node,canvas)
        mask=Image.new('L',canvas.size);ImageDraw.Draw(mask).ellipse((0,0,450*S,450*S),fill=255)
        return Image.composite(canvas,Image.new('RGBA',canvas.size,'black'),mask).convert('RGB')

INK='#FFF3ECDD'
@lru_cache(maxsize=50)
def asset(resource):
    return Image.open(ROOT/f'res/drawable-nodpi/{resource}.png').convert('RGBA')

def main():
    out=ROOT/'design/round-buttons';out.mkdir(parents=True,exist_ok=True)
    still=datetime(2026,11,14,13,43,16,tzinfo=timezone(timedelta(hours=1)))
    base=still.replace(minute=59,second=59)
    Renderer(still).render().save(out/'preview-illustrative-weather.png')
    Renderer(still,weather=False).render().save(out/'preview-weather-unavailable.png')
    Renderer(still,weather=False).render().resize((450,450),Image.Resampling.LANCZOS).save(ROOT/'res/drawable/preview.png')
    Renderer(still,ambient=True).render().save(out/'preview-always-on.png')
    frames=[];durations=[];snapshots=[]
    frames.append(Renderer(base).render().resize((450,450),Image.Resampling.LANCZOS));durations.append(1400)
    for ms in range(0,641,40):
        pic=Renderer(base+timedelta(seconds=1,milliseconds=ms)).render()
        frames.append(pic.resize((450,450),Image.Resampling.LANCZOS));durations.append(40)
        if ms in (0,120,240,320,440,600):snapshots.append((ms,pic))
    frames.append(Renderer(base+timedelta(seconds=2)).render().resize((450,450),Image.Resampling.LANCZOS));durations.append(1600)
    frames[0].save(out/'flip-preview.gif',save_all=True,append_images=frames[1:],duration=durations,loop=0,optimize=False)
    sheet=Image.new('RGB',(1350,970),'#161616');d=ImageDraw.Draw(sheet)
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20)
    for i,(ms,pic) in enumerate(snapshots):
        x=(i%3)*450;y=(i//3)*485
        sheet.paste(pic.resize((450,450),Image.Resampling.LANCZOS),(x,y))
        d.text((x+180,y+455),f'{ms} ms',font=font,fill='white')
    sheet.save(out/'flip-contact-sheet.jpg',quality=94)
    # Test the rendered clock against the previous/current time at boundaries.
    for hour,minute in [(0,0),(10,0),(20,0),(14,0),(9,10),(23,59)]:
        now=base.replace(hour=hour,minute=minute,second=0,microsecond=0)
        clockbox=(76*S,79*S,226*S,241*S)
        prior=Renderer(now-timedelta(seconds=1)).render().crop(clockbox)
        start=Renderer(now).render().crop(clockbox)
        current=Renderer(now+timedelta(seconds=1)).render().crop(clockbox)
        finish=Renderer(now+timedelta(milliseconds=600)).render().crop(clockbox)
        assert not ImageChops.difference(prior,start).getbbox(),f'Wrong previous digit at {hour:02}:{minute:02}'
        assert not ImageChops.difference(current,finish).getbbox(),f'Wrong final digit at {hour:02}:{minute:02}'
    for code in range(16):
        r=Renderer(base);r.data['WEATHER.DAYS.1.CONDITION_DAY']=code;r.render()
    r=Renderer(base);r.data['WEATHER.DAYS.2.IS_AVAILABLE']=False;r.render().save(out/'preview-one-day-unavailable.png')
    r=Renderer(base);r.data['WEATHER.IS_ERROR']=True;r.render().save(out/'preview-stale-weather.png')
    # The perimeter hand must point to the corresponding index, including wrap.
    for second in (0,15,16,30,45,59):
        pic=Renderer(still.replace(second=second)).render()
        a=math.radians(second*6)
        point=(round((225+math.sin(a)*216)*S),round((225-math.cos(a)*216)*S))
        r,g,b=pic.getpixel(point)
        assert g>190 and r>140 and b<130,(second,point,(r,g,b))
    aod=Renderer(still,ambient=True).render()
    later=Renderer(still.replace(second=59),ambient=True).render()
    assert not ImageChops.difference(aod,later).getbbox(),'AOD changed with seconds'
    print('PASS: six flip rollovers, perimeter seconds/wrap, static AOD, 16 weather conditions, missing/stale data.')

if __name__=='__main__':main()
