"""Local animated-presenter production with an inspect/choose/repair agent.

This is a symbolic, goal-directed agent, not an LLM. Tools change inspected state;
the policy selects missing work, reuse, or bounded repair from that state.
"""
import hashlib
import json
import re
import shutil
import subprocess
import sys
import wave
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont
from backend.cards.render import ROOT, asset


def ffmpeg(args, timeout=180):
    result = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-hide_banner', '-y', *map(str,args)],
                            capture_output=True, timeout=timeout)
    if result.returncode:
        raise ValueError(result.stderr.decode('utf8',errors='replace')[-2500:])
    return result


def inspect_video(path, full=False):
    result = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-hide_banner','-i',str(path)],capture_output=True)
    info=result.stderr.decode('utf8',errors='replace')
    duration=re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)',info)
    dimensions=re.search(r'Video:.*? (\d{2,5})x(\d{2,5})',info)
    if not duration or not dimensions: raise ValueError('Media has no readable video stream')
    h,m,s=map(float,duration.groups())
    report={'duration':h*3600+m*60+s,'width':int(dimensions[1]),'height':int(dimensions[2]),
            'audio':'Audio:' in info,'h264':'Video: h264' in info,'bytes':path.stat().st_size,
            'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    if full:
        ffmpeg(['-v','error','-xerror','-i',path,'-f','null','-'])
    return report


def plan_video(prompt, parent=None):
    if parent:
        if not re.search(r'hook|opening|افتتاح',prompt,re.I):
            raise ValueError('Video revisions currently support the opening hook only. Request a hook revision or start a new video.')
        plan=json.loads(json.dumps(parent))
        quoted=re.search(r'["“](.+?)["”]',prompt)
        hook=quoted[1] if quoted else ('Ready for your next Baloot challenge?' if plan['language']=='en' else 'جاهز لتحدي بلوت جديد؟')
        if len(hook)>100: raise ValueError('Keep the opening hook under 100 characters so it fits its scene.')
        plan['scenes'][0]['text']=hook
        return plan
    arabic=bool(re.search(r'arabic|عربي|عربية',prompt,re.I))
    match=re.search(r'\b(\d{2})[ -]*(?:second|sec|s\b)',prompt,re.I)
    duration=int(match[1]) if match else 20
    if not 15<=duration<=30: raise ValueError('Choose a duration from 15 to 30 seconds.')
    texts=(['جاهز لجولة بلوت؟','شاهد اللعب وخطط لحركتك القادمة.','كل جولة فرصة لتحدي جديد.','جرب في آي بي بلوت الآن.'] if arabic else
           ['Your next Baloot challenge starts here.','Watch the table. Plan your next move.','Every round brings a fresh challenge.','Try VIP Baloot. Join the table today.'])
    quoted=re.search(r'(?:hook|opening)\s*[:=]?\s*["“](.+?)["”]',prompt,re.I)
    if quoted: texts[0]=quoted[1][:100]
    return {'language':'ar' if arabic else 'en','duration':duration,'presenter':'Nour · fictional illustrated host',
            'scenes':[{'name':name,'text':text,'seconds':duration*fraction,'offset':[118,124,215,222][i]}
                      for i,(name,text,fraction) in enumerate(zip(['hook','gameplay','challenge','cta'],texts,[.2,.3,.3,.2]))]}


def voice_worker(text,path,language,rate):
    if language=='ar' or sys.platform!='win32':
        return espeak_voice(text,path,language,rate)
    try:
        import pyttsx3
    except ImportError:
        return espeak_voice(text,path,language,rate)
    engine=pyttsx3.init()
    voices=engine.getProperty('voices')
    candidates=[v for v in voices if any(language in str(l).lower() for l in v.languages)]
    if not candidates: return espeak_voice(text,path,language,rate)
    engine.setProperty('voice',candidates[0].id)
    engine.setProperty('rate',rate)
    engine.save_to_file(text,str(path))
    engine.runAndWait()


def espeak_voice(text,path,language,rate):
    """Portable offline formant speech; Arabic works without installing a system voice."""
    import ctypes as c
    import espeakng_loader
    lib=espeakng_loader.load_library()
    if lib is None: raise ValueError('Portable eSpeak library could not load')
    lib.espeak_Initialize.argtypes=[c.c_int,c.c_int,c.c_char_p,c.c_int]
    sample_rate=lib.espeak_Initialize(2,0,str(Path(espeakng_loader.get_data_path()).parent).encode(),0)
    if sample_rate<=0: raise ValueError('eSpeak initialization failed')
    lib.espeak_SetVoiceByName.argtypes=[c.c_char_p]
    if lib.espeak_SetVoiceByName(language.encode()) != 0: raise ValueError(f'Voice unavailable: {language}')
    lib.espeak_SetParameter(1,rate,0)
    chunks=[]
    callback_type=c.CFUNCTYPE(c.c_int,c.POINTER(c.c_short),c.c_int,c.c_void_p)
    @callback_type
    def callback(samples,count,events):
        if samples and count: chunks.append(c.string_at(samples,count*2))
        return 0
    lib.espeak_SetSynthCallback.argtypes=[callback_type]
    lib.espeak_SetSynthCallback(callback)
    lib.espeak_Synth.argtypes=[c.c_void_p,c.c_size_t,c.c_uint,c.c_int,c.c_uint,c.c_uint,c.c_void_p,c.c_void_p]
    encoded=text.encode('utf8')+b'\0'
    if lib.espeak_Synth(encoded,len(encoded),0,1,0,1,None,None)!=0: raise ValueError('eSpeak synthesis failed')
    lib.espeak_Synchronize()
    with wave.open(str(path),'wb') as wav:
        wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(sample_rate); wav.writeframes(b''.join(chunks))
    lib.espeak_Terminate()


def synthesize(text,path,language,seconds,attempt):
    # SAPI runs in its own process so a stalled voice cannot block the server forever.
    args=[sys.executable,'-m','backend.video','voice',text,str(path),language,str(175+attempt*25)]
    result=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=40)
    if result.returncode: raise ValueError(result.stderr.decode('utf8',errors='replace')[-700:])
    with wave.open(str(path)) as wav:
        duration=wav.getnframes()/wav.getframerate()
    if duration<.2 or duration>seconds-.1:
        raise ValueError(f'Voice duration {duration:.2f}s does not fit {seconds:.2f}s; retry at a faster rate')
    return duration


def scene_graphics(scene,folder,language):
    font_path=asset('Alexandria-Medium.ttf')
    title=ImageFont.truetype(str(font_path),26)
    small=ImageFont.truetype(str(font_path),16)
    caption_font=ImageFont.truetype(str(font_path),29)
    text=scene['text']
    if language=='ar':
        import arabic_reshaper
        from bidi.algorithm import get_display
        def display(s): return get_display(arabic_reshaper.reshape(s))
    else:
        def display(s): return s
    # Fixed character identity is shared across every scene and revision.
    for mouth in (0,1):
        im=Image.new('RGBA',(540,960),'#101D35'); d=ImageDraw.Draw(im)
        d.rounded_rectangle((18,18,522,352),24,fill='#20334C')
        d.ellipse((128,27,412,311),fill='#294861')
        d.rounded_rectangle((158,206,382,360),60,fill='#D6AC62')
        d.rounded_rectangle((238,188,302,240),20,fill='#BC7F60')
        d.ellipse((193,59,347,228),fill='#D39B77')
        d.pieslice((186,45,352,170),180,355,fill='#222536')
        d.ellipse((218,135,230,147),fill='#18233A'); d.ellipse((308,135,320,147),fill='#18233A')
        d.arc((243,145,285,174),0,80,fill='#985E4B',width=3)
        if mouth: d.ellipse((251,179,287,198),fill='#633D38'); d.rectangle((256,180,282,185),fill='#FFF1DD')
        else: d.arc((247,168,291,192),0,180,fill='#633D38',width=4)
        logo=Image.open(asset('Logo.png')).convert('RGBA'); logo.thumbnail((94,94))
        im.alpha_composite(logo,(25,35))
        d.text((270,308),'NOUR  /  FICTIONAL HOST',font=small,fill='white',anchor='mm')
        # Gameplay is placed by FFmpeg into this separate panel.
        d.rectangle((0,370,540,800),fill='#071525')
        d.text((270,830),'VIP BALOOT',font=title,fill='#E7BD75',anchor='mm')
        words=text.split(); lines=[]; current=''
        for word in words:
            candidate=(current+' '+word).strip()
            if d.textlength(display(candidate),font=caption_font)>490 and current:
                lines.append(current); current=word
            else: current=candidate
        lines.append(current)
        if len(lines)>3: raise ValueError('Caption does not fit the safe area')
        for i,line in enumerate(lines): d.text((270,866+i*34),display(line),font=caption_font,fill='white',anchor='mm')
        im.save(folder/f'{scene["name"]}-{mouth}.png')


def render_scene(scene,folder,attempt):
    name=scene['name']; duration=scene['seconds']
    # Fit the complete vertical gameplay screen rather than cropping away its controls.
    graph=(f'[0:v]scale=540:960,setsar=1[base];'
           f'[1:v]scale=540:960,setsar=1[open];'
           f"[base][open]overlay=enable='lt(mod(t,0.32),0.16)'[host];"
           '[2:v]scale=540:430:force_original_aspect_ratio=decrease,pad=540:430:(ow-iw)/2:(oh-ih)/2:color=0x071525[game];'
           '[host][game]overlay=0:370,format=yuv420p[v];'
           f'[3:a]apad,atrim=duration={duration},afade=t=out:st={duration-.15}:d=0.15[a]')
    ffmpeg(['-loop','1','-framerate','24','-i',folder/f'{name}-0.png',
            '-loop','1','-framerate','24','-i',folder/f'{name}-1.png',
            '-ss',scene['offset'],'-stream_loop','-1','-i',asset('Gameplay.mp4'),
            '-i',folder/f'{name}.wav','-filter_complex',graph,'-map','[v]','-map','[a]',
            '-t',duration,'-r','24','-c:v','libx264','-preset','ultrafast' if attempt else 'veryfast',
            '-crf','24','-c:a','aac','-ar','44100','-ac','2','-movflags','+faststart',folder/f'{name}.mp4'])


def run_agent(plan,folder,emit,parent_folder=None,parent_plan=None):
    folder.mkdir(parents=True,exist_ok=True)
    attempts={}; reused=[]; completed=set(); voice_ready=set(); decisions=[]; rejected_reuse=set()
    def record(tool,reason):
        decisions.append({'tool':tool,'reason':reason})
        emit('agent_decision',f'{tool}: {reason}')
        (folder/'decisions.json').write_text(json.dumps(decisions,indent=2,ensure_ascii=False),encoding='utf8')
    record('inspect_source','Inspect actual supplied gameplay before selecting production tools.')
    source=inspect_video(asset('Gameplay.mp4'))
    if source['duration']<max(s['offset']+s['seconds'] for s in plan['scenes']):
        raise ValueError('Supplied gameplay is shorter than the selected scenes')
    emit('source_inspection',f'Gameplay: {source["width"]}×{source["height"]}, {source["duration"]:.2f}s. Using inspected table-play intervals.')
    for step in range(36):
        missing=[s for s in plan['scenes'] if s['name'] not in completed]
        if not missing:
            record('assemble_and_validate','All inspected scene goals are satisfied; assemble the delivery MP4.')
            concat=folder/'concat.txt'
            concat.write_text(''.join(f"file '{s['name']}.mp4'\n" for s in plan['scenes']),encoding='utf8')
            ffmpeg(['-f','concat','-safe','0','-i',concat,'-c','copy','-movflags','+faststart',folder/'video.mp4'])
            report=inspect_video(folder/'video.mp4',full=True)
            if not (15<=report['duration']<=30.2 and report['width']==540 and report['height']==960 and report['audio'] and report['h264']):
                raise ValueError(f'Final video validation failed: {report}')
            report['reused_scenes']=reused
            report['presenter']='Illustrated fictional host with simple mouth animation; no photorealism or phoneme lip sync.'
            (folder/'validation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
            (folder/'plan.json').write_text(json.dumps(plan,indent=2,ensure_ascii=False),encoding='utf8')
            ffmpeg(['-ss','1','-i',folder/'video.mp4','-frames:v','1',folder/'poster.png'])
            return ['video.mp4','poster.png','validation.json','plan.json','decisions.json']
        scene=missing[0]; name=scene['name']
        old=next((s for s in (parent_plan or {}).get('scenes',[]) if s['name']==name),None)
        reusable=parent_folder and old==scene and name not in rejected_reuse and (parent_folder/f'{name}.mp4').is_file()
        key=f'{name}:reuse' if reusable else f'{name}:voice' if name not in voice_ready else f'{name}:render'
        attempt=attempts.get(key,0)
        if attempt>=3: raise ValueError(f'Agent exhausted three attempts for {key}; inspect execution log.')
        attempts[key]=attempt+1
        try:
            if reusable:
                record('reuse_scene',f'{name}: request and inspected parent scene match; preserve bytes and presenter.')
                inspect_video(parent_folder/f'{name}.mp4',full=True)
                shutil.copy2(parent_folder/f'{name}.mp4',folder/f'{name}.mp4')
                if hashlib.sha256((parent_folder/f'{name}.mp4').read_bytes()).digest()!=hashlib.sha256((folder/f'{name}.mp4').read_bytes()).digest():
                    raise ValueError('Reuse hash mismatch')
                reused.append(name); completed.add(name)
            elif name not in voice_ready:
                record('synthesize_voice',f'{name}: missing verified voice; attempt {attempt+1}, adapt speech rate to fit scene.')
                duration=synthesize(scene['text'],folder/f'{name}.wav',plan['language'],scene['seconds'],attempt)
                emit('voice_inspection',f'{name}: decoded WAV, {duration:.2f}s, within scene budget.')
                voice_ready.add(name)
            else:
                record('render_scene',f'{name}: voice is verified; render animated presenter, gameplay and matching captions; attempt {attempt+1}.')
                scene_graphics(scene,folder,plan['language'])
                render_scene(scene,folder,attempt)
                report=inspect_video(folder/f'{name}.mp4',full=True)
                if not report['audio'] or abs(report['duration']-scene['seconds'])>.15: raise ValueError('Scene duration/audio check failed')
                emit('scene_inspection',f'{name}: full decode passed; {report["duration"]:.2f}s, H.264 and audio present.')
                completed.add(name)
        except (ValueError,subprocess.TimeoutExpired,OSError) as error:
            if reusable:
                rejected_reuse.add(name)
            record('repair',f'{key} failed inspection: {error}. Retry {attempt+1}/3 with adjusted voice rate or faster encoder.')
    raise ValueError('Agent step budget exhausted')


if __name__=='__main__':
    if sys.argv[1]=='voice': voice_worker(sys.argv[2],Path(sys.argv[3]),sys.argv[4],int(sys.argv[5]))
