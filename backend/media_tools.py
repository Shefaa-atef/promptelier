"""Small process boundary between the web app and optional local model tools."""
import json
import os
import subprocess
import colorsys
import hashlib
import shutil
import time
from pathlib import Path

from PIL import Image, ImageDraw
from PIL import ImageColor

ROOT=Path(__file__).resolve().parents[1]
MEDIA_PYTHON=ROOT/'.venv-media/Scripts/python.exe'


def image_model_ready():
    return MEDIA_PYTHON.is_file() and (ROOT/'models/dreamshaper-8/download-manifest.json').is_file()


def run_model(job,folder,emit):
    if not image_model_ready():
        raise RuntimeError('Local image model is not installed. Run the media setup instructions.')
    folder.mkdir(parents=True,exist_ok=True)
    job_path=folder/'image-job.json'
    job_path.write_text(json.dumps(job,indent=2,ensure_ascii=False),encoding='utf8')
    emit('diffusion','Generating original artwork with local DreamShaper 8 on CUDA. This can take several minutes.')
    log_path=folder/'diffusion.log'
    environment={**os.environ,'PYTHONUTF8':'1','HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1'}
    start=time.monotonic()
    with log_path.open('w',encoding='utf8') as log:
        process=subprocess.Popen([str(MEDIA_PYTHON),'-m','backend.ai_media',str(job_path)],cwd=ROOT,
                                  stdout=log,stderr=subprocess.STDOUT,env=environment)
        try:
            code=process.wait(timeout=1800)
        except subprocess.TimeoutExpired:
            process.kill(); process.wait()
            raise RuntimeError('Local diffusion exceeded its 30-minute limit. See the saved diffusion log.')
    if code:
        tail=log_path.read_text(encoding='utf8',errors='replace')[-1800:]
        raise RuntimeError(f'Local diffusion failed: {tail}')
    output=Path(job['output'])
    with Image.open(output) as image:
        image.load()
        if image.size!=(job['width'],job['height']): raise ValueError('Wrong diffusion output dimensions')
    report=json.loads(output.with_suffix('.json').read_text(encoding='utf8'))
    report['worker_seconds']=round(time.monotonic()-start,2)
    emit('diffusion_inspection',f'Decoded generated artwork; {report["seconds"]}s; peak allocated VRAM {report["peak_vram_mib"]} MiB.')
    return report


def prepare_card_art(run,parent,folder,parent_folder,emit):
    mode=os.getenv('PROMPTELIER_CARD_ENGINE','auto')
    if mode not in ('auto','diffusion','procedural'): raise ValueError('Invalid card engine configuration')
    if mode=='procedural' or (mode=='auto' and not image_model_ready()):
        reason='Explicit procedural mode.' if mode=='procedural' else 'The optional local image model is not installed.'
        emit('procedural_fallback',reason)
        return None,{'engine':'procedural','reason':reason}
    folder.mkdir(parents=True,exist_ok=True)
    spec=run.design.specification
    original=parent_folder/'artwork.png' if parent_folder else None
    fields=run.design.applied_fields
    if run.route.intent=='revision' and parent and parent.status=='completed' and original and not original.is_file():
        previous_engine=(parent.generation or {}).get('engine','procedural')
        if previous_engine.startswith('diffusion'):
            raise ValueError('The parent AI artwork is missing; start a new complete card brief.')
        emit('revision_engine','Preserving the older procedural renderer and its geometry for this revision.')
        return None,{'engine':'procedural','reason':'Preserving the parent design method for a scoped revision.'}
    if (run.route.intent=='revision' and parent and original and original.is_file()
            and all(field.startswith('palette.') for field in fields)):
        target=folder/'artwork.png'
        if fields:
            checksum=recolor_artwork(original,target,parent.design.specification.palette,spec.palette)
            emit('palette_revision','Recolored saved AI pixels. Geometry and parent artwork are preserved.')
        else:
            shutil.copy2(original,target)
            checksum=hashlib.sha256(original.read_bytes()).hexdigest()
            emit('artwork_reuse','No recognized specification changes; saved artwork reused unchanged.')
        return target,{'engine':'diffusion_palette_revision' if fields else 'diffusion_reuse',
                       'model':'Lykon/dreamshaper-8','parent_artwork_sha256':checksum}
    prompt=run.prompt
    if run.route.intent=='revision' and parent:
        prompt=parent.prompt+'. Revision: '+prompt
    job=card_job(spec,prompt,folder)
    report=run_model(job,folder,emit)
    return folder/'artwork.png',report


def card_job(spec,prompt,folder):
    focal=spec.composition.focal_point.replace('_',' ')
    motifs=', '.join(spec.motifs).replace('_',' ')
    palette=spec.palette
    direction=f'central {focal}, {motifs}' if spec.theme!='ornamental' else 'distinct central emblem following the brief'
    brief=(f'{prompt[:220]}. Luxury playing card back surface artwork, '
           f'{direction}, intricate ornamental relief, embossed engraved metal, '
           'refined microdetail, symmetrical balanced layout, luminous enamel, '
           'rich jewel tones, straight-on flat full-bleed design, no typography')
    job={'prompt':brief,'negative_prompt':'photograph of cards, hand, table, perspective, tilted, mockup, letters, text, numbers, watermark, signature, blurry, low quality, clipart, basic shapes, human, person, face',
            'seed':spec.seed,'width':512,'height':704,'steps':28,'guidance':7.5,
            'output':str((folder/'artwork.png').resolve()),'palette':palette.model_dump()}
    if focal in ('crescent','crown'):
        if focal=='crown':
            job['negative_prompt']+=', writing, words, calligraphy, inscriptions, alphabet, typography, captions, logo'
        folder.mkdir(parents=True,exist_ok=True)
        condition=Image.new('RGB',(512,704),'#101D40');draw=ImageDraw.Draw(condition)
        draw.rounded_rectangle((20,20,492,684),radius=24,outline='white',width=3)
        if focal=='crescent':
            draw.ellipse((150,244,362,456),fill='white')
            draw.ellipse((197,216,385,410),fill='#101D40')
        else:
            draw.polygon([(168,365),(148,288),(205,326),(256,258),(307,326),(364,288),(344,365)],fill='white')
            draw.rounded_rectangle((169,377,343,393),5,fill='white')
            for x,y in [(148,288),(256,258),(364,288)]: draw.ellipse((x-7,y-7,x+7,y+7),fill='white')
        target=folder/'composition-guide.png'; condition.save(target)
        job['control_image']=str(target.resolve())
        job['control_strength']=.9
    return job


def recolor_artwork(source,destination,old_palette,new_palette):
    """Change palette without asking diffusion to redraw the parent's geometry."""
    def hsv(hex_color):
        return colorsys.rgb_to_hsv(*(v/255 for v in ImageColor.getrgb(hex_color)))
    old_bg,old_accent=hsv(old_palette.background),hsv(old_palette.ornament)
    new_bg,new_accent=hsv(new_palette.background),hsv(new_palette.ornament)
    def distance(a,b): return min(abs(a-b),1-abs(a-b))
    with Image.open(source) as image:
        image=image.convert('RGB')
        pixels=[]
        for r,g,b in image.getdata():
            h,s,v=colorsys.rgb_to_hsv(r/255,g/255,b/255)
            background=distance(h,old_bg[0])<distance(h,old_accent[0]) if s>.12 else v<.4
            previous,target=(old_bg,new_bg) if background else (old_accent,new_accent)
            hue=(h+target[0]-previous[0])%1
            saturation=min(1,s*target[1]/max(.1,previous[1]))
            if target[1]<.15: saturation=target[1]*.5
            pixels.append(tuple(round(c*255) for c in colorsys.hsv_to_rgb(hue,saturation,v)))
        image.putdata(pixels)
        image.save(destination)
    return hashlib.sha256(Path(source).read_bytes()).hexdigest()


def presenter_ready():
    return (MEDIA_PYTHON.is_file() and (ROOT/'models/sadtalker/MODEL_SOURCE.json').is_file()
            and (ROOT/'vendor/SadTalker-source/UPSTREAM_REVISION').is_file())


def choose_presenter_engine():
    mode=os.getenv('PROMPTELIER_PRESENTER_ENGINE','auto')
    if mode not in ('auto','sadtalker','voiceover','legacy'):
        raise ValueError('Invalid presenter engine configuration')
    if mode!='auto': return mode
    verified=(ROOT/'models/presenter/talking-verified.json').is_file()
    return 'sadtalker' if verified and presenter_ready() else 'voiceover'


def animation_cache_key(portrait,audio):
    key={'portrait':hashlib.sha256(Path(portrait).read_bytes()).hexdigest(),
         'audio':hashlib.sha256(Path(audio).read_bytes()).hexdigest(),
         'code':'cd4c0465ae0b54a6f85af57f5c65fec9fe23e7f8','size':512,'mode':'full-still'}
    return hashlib.sha256(json.dumps(key,sort_keys=True).encode()).hexdigest()


def animate_clip(portrait,audio,folder,emit):
    from backend.video import inspect_video
    if not presenter_ready(): raise RuntimeError('SadTalker is not installed')
    folder.mkdir(parents=True,exist_ok=True)
    cache=ROOT/'models/animation-cache'/animation_cache_key(portrait,audio)
    cached_clip=cache/'clip.mp4'; cache_record=cache/'record.json'
    if cached_clip.is_file() and cache_record.is_file():
        record=json.loads(cache_record.read_text(encoding='utf8'))
        if hashlib.sha256(cached_clip.read_bytes()).hexdigest()==record['sha256']:
            try:
                inspect_video(cached_clip,full=True)
            except (ValueError,OSError,subprocess.TimeoutExpired):
                emit('cache_rejected','Cached animation failed decoding; generate a replacement.')
            else:
                target=folder/'cached-talking.mp4';shutil.copy2(cached_clip,target)
                emit('presenter_cache','Reused a verified talking clip for the identical portrait and speech bytes.')
                return target
    log_path=folder/'animation.log'
    emit('talking_presenter','Animating the saved fictional portrait from the actual speech audio with SadTalker 512px.')
    with log_path.open('w',encoding='utf8') as log:
        process=subprocess.Popen([str(MEDIA_PYTHON),'-m','backend.animate_presenter',
            str(Path(portrait).resolve()),str(Path(audio).resolve()),str(folder.resolve())],
            cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,env={**os.environ,'PYTHONUTF8':'1'})
        try: code=process.wait(timeout=1800)
        except subprocess.TimeoutExpired:
            process.kill(); process.wait()
            raise RuntimeError('Talking presenter exceeded its 30-minute scene limit')
    if code:
        raise RuntimeError('SadTalker failed: '+log_path.read_text(encoding='utf8',errors='replace')[-1800:])
    clips=list(folder.glob('*.mp4'))
    if len(clips)!=1: raise RuntimeError(f'Expected one animated clip, found {len(clips)}')
    inspect_video(clips[0],full=True)
    cache.mkdir(parents=True,exist_ok=True);shutil.copy2(clips[0],cached_clip)
    cache_record.write_text(json.dumps({'sha256':hashlib.sha256(cached_clip.read_bytes()).hexdigest()}),encoding='utf8')
    return clips[0]
