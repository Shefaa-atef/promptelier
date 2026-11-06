"""Original parametric artwork and official-template composition, entirely local."""
import hashlib
import json
import math
import random
import zipfile
from pathlib import Path

from PIL import Image, ImageChops, ImageColor, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
MATERIAL = ROOT / 'task material'
DELIVERY = {'Source/b.png': (250, 346), 'cardPreview.png': (208, 261), 'Symbols/cardIcon.png': (46, 64)}


def asset(name):
    matches = list(MATERIAL.rglob(name))
    if len(matches) != 1:
        raise ValueError(f'Expected one supplied {name}, found {len(matches)}')
    return matches[0]


def artwork(spec, scale=4, simplified=False):
    w, h = 250*scale, 346*scale
    bg, secondary, gold, light = [ImageColor.getrgb(c) for c in
        (spec.palette.background, spec.palette.secondary, spec.palette.ornament, spec.palette.highlight)]
    rng = random.Random(spec.seed)
    im = Image.new('RGB', (w, h))
    pixels = im.load()
    for y in range(h):
        for x in range(w):
            radius = min(1, math.hypot((x/w-.49)*1.4, (y/h-.46)*1.6))
            blend = (1-radius)*.65 if spec.palette.gradient == 'radial' else (y/h*.6 if spec.palette.gradient == 'linear' else 0)
            grain = rng.randint(-2, 2) if spec.surface.texture == 'fine_grain' else (math.sin((x+y*.2)/scale)*1.5 if spec.surface.texture == 'silk' else 0)
            pixels[x,y] = tuple(max(0,min(255,round(a*(1-blend)+b*blend+grain))) for a,b in zip(bg,secondary))
    d = ImageDraw.Draw(im)
    def line(points, color=gold, width=.65):
        d.line([(round(x*scale),round(y*scale)) for x,y in points], fill=color, width=max(1,round(width*scale)), joint='curve')
    def ellipse(box, color=gold, width=.6, fill=None):
        d.ellipse(tuple(round(v*scale) for v in box), outline=color, width=max(1,round(width*scale)), fill=fill)
    def star(x,y,r,n=8):
        pts=[(x+math.cos(i*math.pi/n)*r*(1 if i%2==0 else .34), y+math.sin(i*math.pi/n)*r*(1 if i%2==0 else .34)) for i in range(n*2+1)]
        line(pts, width=.8)
    muted=tuple(round(a*.28+b*.72) for a,b in zip(gold,bg))
    dense={'sparse':0,'balanced':1,'dense':2}[spec.composition.density]
    # Ornament stays away from the focal silhouette so it remains readable at card size.
    if not simplified:
        step=36-dense*6
        for y in range(34,320,step):
            for x in range(28,230,step):
                if math.hypot((x-122)/.75,y-173)<85: continue
                if 'islamic_geometry' in spec.motifs: star(x,y,9+dense,8)
                elif spec.surface.style != 'minimal': ellipse((x-1,y-1,x+1,y+1),muted)
    for inset in range(15, 16+(1 if simplified else spec.surface.decorative_layers)*4, 4):
        line([(inset,39),(inset,307),(35,327),(210,327),(235-inset+15,307),(235-inset+15,39),(210,20),(35,20),(inset,39)],muted,.55)
    for cx,cy in [(38,46),(207,46),(38,300),(207,300)]:
        star(cx,cy,7,4)
    radius=spec.composition.focal_scale*108
    if spec.composition.layout == 'ornamental_panel':
        line([(122,92),(184,173),(122,254),(60,173),(122,92)],gold,1)
    else:
        for offset in (0,4): ellipse((122-radius-offset,173-radius-offset,122+radius+offset,173+radius+offset), gold if offset else muted)
    if 'vines' in spec.motifs or 'leaves' in spec.motifs:
        for side in (-1,1):
            points=[]
            for i in range(61):
                a=-1.15+i/60*2.3
                points.append((122+side*(43+math.cos(a)*35),173+math.sin(a)*102))
            line(points,gold,1.2)
            for i in range(9):
                a=-1+i*.25; x=122+side*(43+math.cos(a)*35); y=173+math.sin(a)*102
                # Two curved edges make a tapered leaf rather than a triangular symbol.
                pts=[]
                for j in range(41):
                    t=j/40; bend=math.sin(math.pi*t)*5
                    pts.append((x+side*(18*t+bend),y-18*t+bend))
                for j in range(40,-1,-1):
                    t=j/40; bend=math.sin(math.pi*t)*5
                    pts.append((x+side*(18*t-bend),y-18*t-bend))
                line(pts,gold,.8)
                line([(x,y),(x+side*18,y-18)],muted,.5)
    focal=spec.composition.focal_point
    if focal=='crescent':
        # Draw the crescent as one polygon; no flat patch over the gradient background.
        r=radius*.71; cx,cy=122,173
        pts=[]
        for i in range(101):
            a=math.radians(55+i*250/100); pts.append((cx+math.cos(a)*r,cy+math.sin(a)*r))
        for i in range(101):
            t=i/100; pts.append((cx+r*.574-r*.80*math.sin(math.pi*t),cy-r*.819+2*r*.819*t))
        d.polygon([(int(x*scale),int(y*scale)) for x,y in pts],fill=gold)
        star(138,164,8,5)
    elif focal=='crown':
        pts=[(93,186),(86,153),(107,166),(122,143),(137,166),(158,153),(151,186),(93,186)]
        line(pts,light,2); line([(96,192),(148,192)],gold,3)
        for x,y in [(86,151),(122,141),(158,151)]: ellipse((x-2,y-2,x+2,y+2),gold,fill=gold)
    elif focal=='leaves':
        for a in range(0,360,60):
            t=math.radians(a); x,y=122+math.cos(t)*30,173+math.sin(t)*30
            line([(122,173),(x-9,y-9),(x,y),(x+9,y+9),(122,173)],gold,1.4)
    else:
        star(122,173,radius*.8,12)
        star(122,173,radius*.48,8)
        ellipse((117,168,127,178),light,fill=gold)
    if 'stars' in spec.motifs:
        for x,y,r in [(122,82,5),(122,264,5),(72,113,3),(172,233,3)]: star(x,y,r,4)
    return im.convert('RGBA')


def frame_mask(frame):
    # Flood the transparent exterior; the enclosed transparent center is the artwork mask.
    alpha=frame.getchannel('A')
    blocked=alpha.point(lambda p: 255 if p>0 else 0)
    exterior=blocked.copy()
    ImageDraw.floodfill(exterior,(0,0),128)
    mask=exterior.point(lambda p: 0 if p==128 else 255)
    if mask.getpixel((122,173)) != 255 or mask.getpixel((0,0)) != 0:
        raise ValueError('Official frame does not enclose a safe artwork region')
    return mask


def validate_delivery(folder):
    actual={p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()}
    if actual != set(DELIVERY): raise ValueError(f'Unexpected delivery tree: {actual}')
    report={}
    for name,size in DELIVERY.items():
        p=folder/name
        with Image.open(p) as im:
            im.load()
            if im.format!='PNG' or im.size!=size or im.mode!='RGBA': raise ValueError(f'Invalid PNG: {name}')
            if im.getchannel('A').getextrema() != (0,255): raise ValueError(f'Missing transparency: {name}')
        report[name]={'size':list(size),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
    return report


def generate_card(spec, folder):
    folder.mkdir(parents=True,exist_ok=True)
    frame=Image.open(asset('Cardback-p2.png' if spec.tier=='premium' else 'Cardback-n1.png')).convert('RGBA')
    mask=frame_mask(frame)
    def compose(simple=False):
        art=artwork(spec,simplified=simple).resize((250,346),Image.Resampling.LANCZOS)
        art.putalpha(mask)
        return Image.alpha_composite(art,frame)
    card=compose()
    delivery=folder/'delivery'
    (delivery/'Source').mkdir(parents=True,exist_ok=True)
    (delivery/'Symbols').mkdir(exist_ok=True)
    card.save(delivery/'Source/b.png')
    # A measured, explicit two-card layout matching the supplied preview's bounds.
    preview=Image.new('RGBA',(208,261))
    face=Image.open(asset('kc.png')).convert('RGBA').resize((142,200),Image.Resampling.LANCZOS)
    preview.alpha_composite(face,(68,40))
    preview.alpha_composite(card.resize((136,187),Image.Resampling.LANCZOS),(0,25))
    preview.save(delivery/'cardPreview.png')
    compose(True).resize((46,64),Image.Resampling.LANCZOS).save(delivery/'Symbols/cardIcon.png')
    report=validate_delivery(delivery)
    # Opaque frame pixels must survive composition exactly.
    opaque=frame.getchannel('A').point(lambda a:255 if a==255 else 0)
    if ImageChops.multiply(ImageChops.difference(card,frame).convert('RGB').convert('L'),opaque).getbbox():
        raise ValueError('Official frame was altered')
    (folder/'specification.json').write_text(spec.model_dump_json(indent=2),encoding='utf8')
    (folder/'validation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    with zipfile.ZipFile(folder/'cards.zip','w',zipfile.ZIP_DEFLATED) as archive:
        for name in DELIVERY: archive.write(delivery/name,name)
    return [*DELIVERY,'cards.zip','validation.json']
