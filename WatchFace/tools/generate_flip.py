"""Native WFF flip clock with real three-day forecasts and static ambient mode.

Animation is reconstructed from local time, including previous-hour/day rollover.
Only changed digits enter the sub-second branch, for the first second of a change.
No animated GIF/WebP loops and no synthetic weather data are installed.
"""
from pathlib import Path
from xml.etree import ElementTree as ET
import math
from flip_assets import generate as generate_assets, W as CARD_W, H as CARD_H

ROOT=Path(__file__).resolve().parents[1]
INK='#FFF3ECDD'; SOFT='#FFB7B0A4'
ACCENT='[CONFIGURATION.verticalPalette.0]'
PAIR='[CONFIGURATION.verticalPalette.1]'
CARD_POS=[(78,81),(154,81),(78,164),(154,164)]
BUTTON_SIZE=100
BUTTON_CENTERS={'agenda':(117,344),'voice':(225,373),'alerts':(333,344)}
wf=ET.Element('WatchFace',width='450',height='450',clipShape='CIRCLE')
counter=0

def el(parent,tag,**attrs):
    return ET.SubElement(parent,tag,{k:str(int(v)) if isinstance(v,float) and v.is_integer() else str(v) for k,v in attrs.items()})
def mode(parent,value=0):
    el(parent,'Variant',mode='AMBIENT',target='alpha',value=value)
def group(parent,x=0,y=0,width=450,height=450,**attrs):
    global counter
    counter+=1
    return el(parent,'Group',name=f'flip_group_{counter}',x=x,y=y,width=width,height=height,**attrs)
def draw(parent,x=0,y=0,width=450,height=450):
    return el(parent,'PartDraw',x=x,y=y,width=width,height=height)
def line(parent,x1,y1,x2,y2,color=INK,width=2):
    p=el(parent,'Line',startX=x1,startY=y1,endX=x2,endY=y2)
    el(p,'Stroke',color=color,thickness=width,cap='ROUND')
def rect(parent,x,y,w,h,color,r=0):
    attrs=dict(x=x,y=y,width=w,height=h)
    if r: attrs.update(cornerRadiusX=r,cornerRadiusY=r)
    p=el(parent,'RoundRectangle' if r else 'Rectangle',**attrs); el(p,'Fill',color=color)
    return p
def ellipse(parent,cx,cy,rx,ry=None,fill=None,stroke=None,width=2):
    ry=rx if ry is None else ry
    p=el(parent,'Ellipse',x=cx-rx,y=cy-ry,width=rx*2,height=ry*2)
    if fill: el(p,'Fill',color=fill)
    if stroke: el(p,'Stroke',color=stroke,thickness=width)
    return p
def text(parent,x,y,w,h,size,value=None,expr=None,color=INK,weight='MEDIUM',family='SYNC_TO_DEVICE',parameters=None):
    p=el(parent,'PartText',x=x,y=y,width=w,height=h)
    t=el(p,'Text',align='CENTER',maxLines=1,ellipsis='TRUE')
    f=el(t,'Font',family=family,size=size,color=color,weight=weight)
    if expr or parameters:
        template=el(f,'Template'); template.text=value or '%s'
        for expression in (parameters or [expr]): el(template,'Parameter',expression=expression)
    else: f.text=value
    return p
def image(parent,x,y,w,h,resource,**attrs):
    p=el(parent,'PartImage',x=x,y=y,width=w,height=h,**attrs)
    el(p,'Image',resource=resource)
    return p
def condition(parent,expr,name='enabled'):
    c=el(parent,'Condition'); expressions=el(c,'Expressions')
    el(expressions,'Expression',name=name).text=expr
    return c,el(c,'Compare',expression=name)
def transform(parent,target,value):
    el(parent,'Transform',target=target,value=value)

def plate(parent,digit,color,half=None,**attrs):
    suffix=f'_{half}' if half else ''
    height=CARD_H/2 if half else CARD_H
    y=CARD_H/2 if half=='bottom' else 0
    g=group(parent,0,y,CARD_W,height,**attrs)
    image(g,0,0,CARD_W,height,f'flip_card{suffix}')
    image(g,0,0,CARD_W,height,f'flip{suffix}_{digit}',tintColor=color)
    return g


def flip_motion(parent,new,old,color):
    # Resting new card is already beneath these three half-plates.
    plate(parent,old,color,'bottom')
    top_scale='cos(rad(90 * clamp([MILLISECOND] / 260, 0, 1)))'
    bottom_scale='sin(rad(90 * clamp(([MILLISECOND] - 260) / 340, 0, 1)))'
    top=plate(parent,old,color,'top',pivotY=1)
    transform(top,'scaleY',top_scale)
    shadow=image(parent,0,0,CARD_W,CARD_H/2,'flip_card_top',pivotY=1,tintColor='#FF000000')
    transform(shadow,'scaleY',top_scale)
    transform(shadow,'alpha','100 * clamp([MILLISECOND] / 260, 0, 1)')
    bottom=plate(parent,new,color,'bottom',pivotY=0)
    transform(bottom,'scaleY',bottom_scale)
    shadow=image(parent,0,CARD_H/2,CARD_W,CARD_H/2,'flip_card_bottom',pivotY=0,tintColor='#FF000000')
    transform(shadow,'scaleY',bottom_scale)
    transform(shadow,'alpha','90 * (1 - clamp(([MILLISECOND] - 260) / 340, 0, 1))')

DIGITS=[
    ('floor([HOUR_0_23] / 10)', '[MINUTE] == 0 && ([HOUR_0_23] == 0 || [HOUR_0_23] == 10 || [HOUR_0_23] == 20)', range(3)),
    ('[HOUR_0_23] % 10', '[MINUTE] == 0', range(10)),
    ('[MINUTE_TENS_DIGIT]', '[MINUTE_UNITS_DIGIT] == 0', range(6)),
    ('[MINUTE_UNITS_DIGIT]', '1 == 1', range(10)),
]

def clock(parent,ambient=False):
    reader=el(parent,'ScreenReader',stringId='a11y_time')
    el(reader,'Parameter',expression='[HOUR_0_23_Z]')
    el(reader,'Parameter',expression='[MINUTE_Z]')
    for index,(source,changed,values) in enumerate(DIGITS):
        g=group(parent,*CARD_POS[index],CARD_W,CARD_H)
        color=PAIR if index<2 else ACCENT
        c=el(g,'Condition'); expressions=el(c,'Expressions')
        for value in values: el(expressions,'Expression',name=f'digit_{value}').text=f'{source} == {value}'
        for value in values:
            b=el(c,'Compare',expression=f'digit_{value}')
            content=group(b,0,0,CARD_W,CARD_H)
            if ambient:
                image(content,0,0,CARD_W,CARD_H,f'flip_ambient_{value}')
                continue
            plate(content,value,color)
            _,animation=condition(content,f'[SECOND] == 0 && ({changed})')
            motion=group(animation,0,0,CARD_W,CARD_H)
            if index==1 and value==0:
                cc,midnight=condition(motion,'[HOUR_0_23] == 0')
                midnight_group=group(midnight,0,0,CARD_W,CARD_H)
                flip_motion(midnight_group,0,3,color)
                other=el(cc,'Default'); other_group=group(other,0,0,CARD_W,CARD_H)
                flip_motion(other_group,0,9,color)
            else:
                old=(value-1)%({0:3,1:10,2:6,3:10}[index])
                flip_motion(motion,value,old,color)
        if not ambient:
            p=draw(g,0,0,CARD_W,CARD_H)
            for x in (1,CARD_W-4):
                rect(p,x,CARD_H/2-4,3,8,'#FF8A887D',1)
                line(p,x+.8,CARD_H/2-2,x+.8,CARD_H/2+2,'#FFC3BEAE',.6)


def seconds_grid(parent):
    bezel=group(parent)
    p=draw(bezel)
    for i in range(60):
        a=math.radians(i*6)
        major=i%5==0
        r=209 if major else 213
        line(p,round(225+math.sin(a)*r,3),round(225-math.cos(a)*r,3),
             round(225+math.sin(a)*219,3),round(225-math.cos(a)*219,3),
             '#FF63685E' if major else '#FF343A32',1.5 if major else 1)
    # One step per second; no millisecond dependency outside the brief flip.
    orbit=group(parent,pivotX=.5,pivotY=.5)
    transform(orbit,'angle','[SECOND] * 6')
    for age,alpha in [(4,35),(3,65),(2,110),(1,175),(0,255)]:
        g=group(orbit,alpha=alpha);p=draw(g)
        a=math.radians(-age*6);r=207 if age==0 else 213
        line(p,round(225+math.sin(a)*r,3),round(225-math.cos(a)*r,3),
             round(225+math.sin(a)*219,3),round(225-math.cos(a)*219,3),ACCENT,3 if age==0 else 2)

def weather_symbol(parent,code,x,y,size=36):
    g=group(parent,x,y,40,40,scaleX=size/40,scaleY=size/40,pivotX=0,pivotY=0)
    p=draw(g,0,0,40,40)
    def sun(cx=20,cy=19,r=7):
        ellipse(p,cx,cy,r,fill=ACCENT)
        for i in range(8):
            a=i*math.pi/4
            line(p,round(cx+math.cos(a)*(r+3),2),round(cy+math.sin(a)*(r+3),2),round(cx+math.cos(a)*(r+6),2),round(cy+math.sin(a)*(r+6),2),ACCENT,1.8)
    def cloud():
        ellipse(p,14,21,8,fill='#FFD6D9DA'); ellipse(p,22,17,9,fill='#FFD6D9DA')
        ellipse(p,30,23,7,fill='#FFD6D9DA'); rect(p,11,22,20,8,'#FFD6D9DA',3)
    if code in (1,8): sun()
    elif code==14: sun(12,12,5); cloud()
    elif code==2: cloud()
    elif code in (3,13):
        for yy,xx,ww in [(13,6,28),(20,3,33),(27,8,24)]: line(p,xx,yy,xx+ww,yy,SOFT,2.6)
    elif code==15:
        for yy,xx,ww in [(12,4,24),(20,0,34),(28,7,20)]: line(p,xx,yy,xx+ww,yy,SOFT,2.4)
    elif code in (4,6,12):
        cloud()
        for xx in ([12,21,30] if code==4 else [15,27]): line(p,xx,33,xx-2,38,'#FFA0CEE1',2)
    elif code in (5,7,11):
        cloud()
        for xx in (14,28):
            line(p,xx,32,xx,39,INK,1.5); line(p,xx-3,34,xx+3,37,INK,1.5); line(p,xx-3,37,xx+3,34,INK,1.5)
    elif code==9:
        cloud(); line(p,23,28,18,34,ACCENT,2.5); line(p,18,34,24,34,ACCENT,2.5); line(p,24,34,19,40,ACCENT,2.5)
    elif code==10:
        cloud(); line(p,13,33,11,38,'#FFA0CEE1',2); ellipse(p,28,36,2,fill=INK)
    else:
        g.remove(p)
        text(g,0,5,40,30,24,value='—',color=SOFT)

def weather_icon(parent,source,x,y,size=36):
    c=el(parent,'Condition'); expressions=el(c,'Expressions')
    for n in range(1,16): el(expressions,'Expression',name=f'weather_{n}').text=f'{source} == {n}'
    for n in range(1,16): weather_symbol(el(c,'Compare',expression=f'weather_{n}'),n,x,y,size)
    weather_symbol(el(c,'Default'),0,x,y,size)

def forecast(parent,day,cx):
    g=group(parent,cx-50,10,100,40)
    # Anchor tomorrow/day+N at noon: safe across a one-hour DST transition.
    stamp=f'[UTC_TIMESTAMP] - [SECONDS_IN_DAY] * 1000 - [MILLISECOND] + {day*86400000+43200000}'
    text(g,0,0,100,17,14,value='Domani' if day==1 else None,
         expr=None if day==1 else f'icuText("EEE d", {stamp})',color=SOFT)
    c,available=condition(g,f'[WEATHER.DAYS.{day}.IS_AVAILABLE]')
    data=group(available,0,0,100,40)
    weather_icon(data,f'[WEATHER.DAYS.{day}.CONDITION_DAY]',1,17,25)
    text(data,28,18,72,22,15,value='%s°/%s°',parameters=[f'[WEATHER.DAYS.{day}.TEMPERATURE_HIGH]',f'[WEATHER.DAYS.{day}.TEMPERATURE_LOW]'])
    missing=group(el(c,'Default'),0,0,100,40)
    weather_symbol(missing,0,1,17,25)
    text(missing,28,18,72,22,15,value='— / —',color=SOFT)

def shortcut(parent,center,slotid,provider,label,caption):
    cx,cy=center
    s=el(parent,'ComplicationSlot',x=cx-50,y=cy-50,width=BUTTON_SIZE,height=BUTTON_SIZE,slotId=slotid,displayName=label,isCustomizable='TRUE',supportedTypes='SHORT_TEXT RANGED_VALUE MONOCHROMATIC_IMAGE SMALL_IMAGE EMPTY')
    mode(s); el(s,'BoundingOval',x=0,y=0,width=BUTTON_SIZE,height=BUTTON_SIZE)
    el(s,'DefaultProviderPolicy',defaultSystemProvider=provider,defaultSystemProviderType='SHORT_TEXT')
    for kind in ('SHORT_TEXT','RANGED_VALUE'):
        c=el(s,'Complication',type=kind)
        image(c,0,0,100,100,'round_action_dark')
        image(c,33,19,34,34,'[COMPLICATION.MONOCHROMATIC_IMAGE]',tintColor=PAIR)
        text(c,8,60,84,25,20,value=caption,weight='BOLD')
    for kind in ('MONOCHROMATIC_IMAGE','SMALL_IMAGE'):
        c=el(s,'Complication',type=kind)
        image(c,0,0,100,100,'round_action_dark')
        image(c,33,19,34,34,f'[COMPLICATION.{kind}]',**({'tintColor':PAIR} if kind=='MONOCHROMATIC_IMAGE' else {}))
        text(c,8,60,84,25,20,value=caption,weight='BOLD')
    c=el(s,'Complication',type='EMPTY')
    image(c,0,0,100,100,'round_action_dark')
    text(c,8,38,84,25,20,value=caption,weight='BOLD',color=SOFT)

def weather_shortcut(parent,x,y,w,h,slotid,label,radius=12):
    s=el(parent,'ComplicationSlot',x=x,y=y,width=w,height=h,slotId=slotid,displayName=label,isCustomizable='TRUE',supportedTypes='MONOCHROMATIC_IMAGE SMALL_IMAGE SHORT_TEXT RANGED_VALUE EMPTY')
    mode(s); el(s,'BoundingRoundBox',x=0,y=0,width=w,height=h,cornerRadius=radius)
    el(s,'DefaultProviderPolicy',defaultSystemProvider='APP_SHORTCUT',defaultSystemProviderType='MONOCHROMATIC_IMAGE')
    for kind in ('MONOCHROMATIC_IMAGE','SMALL_IMAGE','SHORT_TEXT','RANGED_VALUE'):
        c=el(s,'Complication',type=kind)
        rect(draw(c,0,0,w,h),0,0,w,h,'#00000000')
    el(s,'Complication',type='EMPTY')

def health_column(parent):
    side=group(parent,265,0,108,240)
    text(side,18,80,72,43,52,expr='[SECOND_Z]',family='teko_semibold')
    text(side,18,120,72,14,10,value='SEC',color=SOFT)
    hr=group(side,0,138,108,40)
    el(hr,'Launch',target='HEALTH_HEART_RATE')
    p=draw(hr,0,11,27,25)
    for a,b,c,d in [(1,13,6,13),(6,13,10,4),(10,4,16,22),(16,22,20,10),(20,10,25,13)]:
        line(p,a,b,c,d,ACCENT,1.8)
    text(hr,30,0,76,27,34,expr="[HEART_RATE] > 0 ? [HEART_RATE] : '--'",family='teko_semibold')
    text(hr,30,26,76,13,9,value='BPM',color=SOFT)
    steps=group(side,0,180,108,37)
    el(steps,'Launch',target='com.samsung.android.wear.shealth/com.samsung.android.wear.shealth.app.home.HomeActivity')
    p=draw(steps,0,10,27,25)
    ellipse(p,9,9,3,6,fill=ACCENT);ellipse(p,19,16,3,6,fill=ACCENT)
    text(steps,28,0,80,25,30,expr='[STEP_COUNT]',family='teko_semibold')
    text(steps,28,24,80,13,9,value='PASSI',color=SOFT)
    battery=group(side,0,217,108,24)
    el(battery,'Launch',target='BATTERY_STATUS')
    p=draw(battery,0,5,27,18)
    b=el(p,'RoundRectangle',x=1,y=2,width=21,height=12,cornerRadiusX=2,cornerRadiusY=2)
    el(b,'Stroke',color=ACCENT,thickness=1.5)
    line(p,25,6,25,10,ACCENT,1.8)
    fill=rect(p,4,5,15,6,ACCENT,1)
    transform(fill,'width','15 * clamp([BATTERY_PERCENT], 0, 100) / 100')
    c,low=condition(battery,'[BATTERY_PERCENT] < 20')
    text(low,29,0,79,24,29,value='%s%%',expr='[BATTERY_PERCENT]',color='#FFFF7479',family='teko_semibold')
    text(el(c,'Default'),29,0,79,24,29,value='%s%%',expr='[BATTERY_PERCENT]',family='teko_semibold')


def build():
    generate_assets()
    configs=el(wf,'UserConfigurations')
    palette=el(configs,'ColorConfiguration',id='verticalPalette',displayName='theme_color_name',defaultValue='volt')
    for key,colors in [
        ('volt','#FFD5FF45 #FFF3ECDD'),
        ('warm','#FFFFBE78 #FF9CDCF0'),
        ('ice','#FF9CDCF0 #FFFFBE78'),
        ('ember','#FFFF9254 #FFF3ECDD'),
        ('red','#FFFF7479 #FFFFD670'),
        ('white','#FFE8E3D9 #FF6EE7B7'),
    ]:
        el(palette,'ColorOption',id=key,displayName='color_'+key,colors=colors)
    scene=el(wf,'Scene',backgroundColor='#FF000000')
    date=text(scene,90,53,270,26,18,expr='icuText("EEE d MMM")',color=INK)
    mode(date,140)
    active=group(scene); mode(active)
    seconds_grid(active)
    clock(active)
    aod=group(scene,alpha=0); mode(aod,255)
    clock(aod,True)
    health_column(active)
    weather=group(scene,60,241,330,52); mode(weather)
    # A configured complication can override this. On a fresh install the
    # empty app-shortcut slot still leaves a useful default weather action.
    el(weather,'Launch',target='com.samsung.android.watch.weather/com.samsung.android.watch.weather.ui.WeatherActivity')
    c,available=condition(weather,'[WEATHER.IS_AVAILABLE]')
    weather_data=group(available,0,0,330,52)
    for day,cx in [(1,57),(2,165),(3,273)]: forecast(weather_data,day,cx)
    # Preserve available-but-stale data and show its age rather than silently refreshing a date.
    _,stale_content=condition(weather_data,'[WEATHER.IS_ERROR]')
    text(stale_content,20,0,290,10,9,value='Da aggiornare · %s',expr='icuText("HH:mm", [WEATHER.LAST_UPDATED])',color=ACCENT)
    missing=group(el(c,'Default'),0,0,330,52)
    text(missing,20,0,290,12,9,value='METEO NON DISPONIBILE',color=SOFT)
    for day,cx in [(1,57),(2,165),(3,273)]:
        text(missing,cx-50,12,100,17,14,value=['Domani','Tra 2 giorni','Tra 3 giorni'][day-1],color=SOFT)
        weather_symbol(missing,0,cx-49,29,25)
        text(missing,cx-22,30,72,22,15,value='— / —',color=SOFT)
    p=draw(weather,0,0,330,52)
    for x in (111,219):line(p,x,14,x,46,'#FF242824',.7)
    shortcut(scene,BUTTON_CENTERS['agenda'],0,'NEXT_EVENT','slot_left_name','Agenda')
    shortcut(scene,BUTTON_CENTERS['alerts'],1,'UNREAD_NOTIFICATION_COUNT','slot_right_name','Avvisi')
    weather_shortcut(scene,60,241,330,52,3,'slot_weather_name',12)
    cx,cy=BUTTON_CENTERS['voice']
    # Give the voice key extra invisible padding. This runtime reports Group
    # accessibility dimensions in unscaled units, unlike ComplicationSlot.
    mic=group(active,cx-56,cy-56,112,112)
    mic.set('name','primary_voice')
    el(mic,'Launch',target='com.samsung.android.wear.voicerecorder/com.samsung.android.wear.voicerecorder.view.MainActivity')
    el(mic,'ScreenReader',stringId='a11y_voice')
    face=group(mic,6,6,100,100)
    p=draw(face,0,0,100,100); ellipse(p,50,50,49,fill=ACCENT)
    dark='#FF13190A'
    rect(p,44,18,12,27,dark,6)
    a=el(p,'Arc',centerX=50,centerY=39,width=30,height=30,startAngle=90,endAngle=270,direction='CLOCKWISE')
    el(a,'Stroke',color=dark,thickness=2.8,cap='ROUND')
    line(p,50,55,50,62,dark,2.8); line(p,41,62,59,62,dark,2.8)
    text(face,10,65,80,25,21,value='Voce',color=dark,weight='BOLD')
    ET.indent(wf,space='    ')
    ET.ElementTree(wf).write(ROOT/'res/raw/watchface.xml',encoding='utf-8',xml_declaration=True)
    print('Generated Palette Meteo 5: variant A, three 100-unit action keys, vertical flip clock, weather, AOD.')

if __name__=='__main__': build()
