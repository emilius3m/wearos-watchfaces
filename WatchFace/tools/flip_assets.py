"""Draw clock components from the bundled font; no photographic assets required."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'res/drawable-nodpi'
W, H, SCALE = 80, 102, 2

def digit_image(digit, ambient=False):
    w,h = W*SCALE,H*SCALE
    font = ImageFont.truetype(str(ROOT/'res/font/teko_semibold.ttf'), 136*SCALE)
    glyph = Image.new('L',(w,h))
    d = ImageDraw.Draw(glyph)
    box = d.textbbox((0,0),str(digit),font=font)
    d.text(((w-(box[2]-box[0]))/2-box[0],(h-(box[3]-box[1]))/2-box[1]-SCALE),str(digit),font=font,fill=255)
    if ambient:
        edge = ImageChops.subtract(glyph.filter(ImageFilter.MaxFilter(5)),glyph)
        image = Image.new('RGBA',(w,h),(157,150,135,0))
        image.putalpha(edge)
        return image
    # Separate pigment from the plate so the minute digits follow the accent.
    image = Image.new('RGBA',(w,h),'white')
    ImageDraw.Draw(glyph).rectangle((0,h//2-SCALE,w,h//2+SCALE),fill=0)
    image.putalpha(glyph)
    return image


def card_image():
    w,h = W*SCALE,H*SCALE
    shape = Image.new('L',(w,h)); sd=ImageDraw.Draw(shape)
    sd.rounded_rectangle((1,1,w-2,h-2),radius=7*SCALE,fill=255)
    plate = Image.new('RGBA',(w,h))
    pd=ImageDraw.Draw(plate)
    for y in range(h):
        level=round(46-12*y/(h/2)) if y<h/2 else round(32+4*(y-h/2)/(h/2))
        pd.line((0,y,w,y),fill=(level,level+1,level+2,255))
    plate.putalpha(shape)
    image=plate
    d=ImageDraw.Draw(image)
    d.rounded_rectangle((1,1,w-2,h-2),radius=7*SCALE,outline='#373A3B',width=1)
    d.line((8*SCALE,2*SCALE,(W-8)*SCALE,2*SCALE),fill='#42413D',width=1)
    d.rectangle((0,h//2-SCALE,w,h//2+SCALE),fill='#080909')
    d.line((3*SCALE,h//2+2*SCALE,(W-3)*SCALE,h//2+2*SCALE),fill='#3B3A35',width=1)
    return image

def generate():
    OUT.mkdir(parents=True,exist_ok=True)
    card=card_image()
    card.save(OUT/'flip_card.png',optimize=True)
    card.crop((0,0,W*SCALE,H*SCALE//2)).save(OUT/'flip_card_top.png',optimize=True)
    card.crop((0,H*SCALE//2,W*SCALE,H*SCALE)).save(OUT/'flip_card_bottom.png',optimize=True)
    for digit in range(10):
        image=digit_image(digit)
        image.save(OUT/f'flip_{digit}.png',optimize=True)
        image.crop((0,0,W*SCALE,H*SCALE//2)).save(OUT/f'flip_top_{digit}.png',optimize=True)
        image.crop((0,H*SCALE//2,W*SCALE,H*SCALE)).save(OUT/f'flip_bottom_{digit}.png',optimize=True)
        digit_image(digit,True).save(OUT/f'flip_ambient_{digit}.png',optimize=True)
    print('Generated 43 compact flip-clock components: plates, tintable digits, AOD.')

if __name__ == '__main__': generate()
