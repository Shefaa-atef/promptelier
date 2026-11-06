"""Bounded symbolic video agent: inspect state, select tools, verify, reuse, repair.

This is a small goal-directed policy, not an LLM or a general planning system.
"""
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from backend.cards.render import ROOT, asset
from backend.media_tools import choose_presenter_engine, animate_clip
from backend.video_audio import voice_engine, voice_worker, synthesize, voice_cache_path
from backend.video_render import ffmpeg, inspect_video, scene_graphics, render_scene, render_realistic_scene


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
    texts=(['جاهز لجولة بلوت فيها تحدي؟','تابع اللعب، ركز على الورق، وخطط لحركتك القادمة.','كل جولة لها حسابها. العب بذكاء وكن قد التحدي.','جرب في آي بي بلوت الآن.'] if arabic else
           ['Your next Baloot challenge starts here.','Watch the table. Plan your next move.','Every round brings a fresh challenge.','Try VIP Baloot. Join the table today.'])
    quoted=re.search(r'(?:hook|opening)\s*[:=]?\s*["“](.+?)["”]',prompt,re.I)
    if quoted: texts[0]=quoted[1][:100]
    engine=choose_presenter_engine()
    return {'language':'ar' if arabic else 'en','duration':duration,'presenter':'Nour · fictional host',
            'presenter_engine':engine,
            'scenes':[{'name':name,'text':text,'seconds':duration*fraction,'offset':[118,124,130,136][i]}
                      for i,(name,text,fraction) in enumerate(zip(['hook','gameplay','challenge','cta'],texts,[.2,.3,.3,.2]))]}


def run_agent(plan,folder,emit,parent_folder=None,parent_plan=None):
    folder.mkdir(parents=True,exist_ok=True)
    attempts={}; reused=[]; completed=set(); voice_ready=set(); decisions=[]; rejected_reuse=set(); animated={}
    presenter_engine=plan.get('presenter_engine','legacy')
    portrait=None
    if presenter_engine=='sadtalker':
        source_portrait=parent_folder/'presenter.png' if parent_folder and (parent_folder/'presenter.png').is_file() else ROOT/'models/presenter/nour.png'
        if not source_portrait.is_file(): raise ValueError('The fictional presenter portrait is missing')
        portrait=folder/'presenter.png';shutil.copy2(source_portrait,portrait)
        checksum=hashlib.sha256(portrait.read_bytes()).hexdigest()
        if plan.get('presenter_sha256') and checksum!=plan['presenter_sha256']:
            raise ValueError('Presenter identity changed; refusing an inconsistent revision')
        plan['presenter_sha256']=checksum
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
            report['scene_sha256']={s['name']:hashlib.sha256((folder/f"{s['name']}.mp4").read_bytes()).hexdigest() for s in plan['scenes']}
            if parent_folder:
                report['parent_scene_sha256']={name:hashlib.sha256((parent_folder/f'{name}.mp4').read_bytes()).hexdigest() for name in reused}
            descriptions={
                'legacy':'Legacy illustrated host with simple mouth animation.',
                'sadtalker':'AI-generated fictional human, animated from the actual speech with SadTalker 512px.',
                'voiceover':'Gameplay with voiceover. No talking presenter is included.'}
            report['presenter']=descriptions[presenter_engine]
            report['voice_engine']=voice_engine(plan['language'])
            if portrait: report['presenter_sha256']=plan['presenter_sha256']
            (folder/'validation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
            (folder/'plan.json').write_text(json.dumps(plan,indent=2,ensure_ascii=False),encoding='utf8')
            generation={'engine':'video-'+presenter_engine,'description':report['presenter'],
                        'voice_engine':report['voice_engine'],'presenter_sha256':report.get('presenter_sha256')}
            (folder/'generation.json').write_text(json.dumps(generation,indent=2),encoding='utf8')
            ffmpeg(['-ss','1','-i',folder/'video.mp4','-frames:v','1',folder/'poster.png'])
            return ['video.mp4','poster.png','validation.json','plan.json','decisions.json','generation.json']+(['presenter.png'] if portrait else [])
        scene=missing[0]; name=scene['name']
        old=next((s for s in (parent_plan or {}).get('scenes',[]) if s['name']==name),None)
        reusable=parent_folder and old==scene and name not in rejected_reuse and (parent_folder/f'{name}.mp4').is_file()
        key=(f'{name}:reuse' if reusable else f'{name}:voice' if name not in voice_ready else
             f'{name}:animate' if presenter_engine=='sadtalker' and name not in animated else f'{name}:render')
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
                emit('reuse_inspection',f'{name}: unchanged SHA-256 {hashlib.sha256((folder/f"{name}.mp4").read_bytes()).hexdigest()}.')
                reused.append(name); completed.add(name)
            elif name not in voice_ready:
                record('synthesize_voice',f'{name}: missing verified voice; engine {voice_engine(plan["language"])}; attempt {attempt+1}, adapt speech rate to fit scene.')
                duration=synthesize(scene['text'],folder/f'{name}.wav',plan['language'],scene['seconds'],attempt)
                emit('voice_inspection',f'{name}: decoded WAV, {duration:.2f}s, within scene budget.')
                voice_ready.add(name)
            elif presenter_engine=='sadtalker' and name not in animated:
                record('animate_presenter',f'{name}: verified speech needs a real talking clip; use the saved presenter identity.')
                clip=animate_clip(portrait,folder/f'{name}.wav',folder/f'{name}-talking'/f'attempt-{attempt+1}',emit)
                inspection=inspect_video(clip,full=True)
                if inspection['duration']<.5: raise ValueError('Talking clip is too short')
                animated[name]=clip
                emit('talking_inspection',f'{name}: animated MP4 decoded; {inspection["duration"]:.2f}s, {inspection["width"]}×{inspection["height"]}.')
            else:
                record('render_scene',f'{name}: voice is verified; render animated presenter, gameplay and matching captions; attempt {attempt+1}.')
                if presenter_engine=='legacy':
                    scene_graphics(scene,folder,plan['language'])
                    render_scene(scene,folder,attempt)
                else:
                    render_realistic_scene(scene,folder,plan['language'],animated.get(name),attempt)
                report=inspect_video(folder/f'{name}.mp4',full=True)
                if not report['audio'] or abs(report['duration']-scene['seconds'])>.15: raise ValueError('Scene duration/audio check failed')
                emit('scene_inspection',f'{name}: full decode passed; {report["duration"]:.2f}s, H.264 and audio present.')
                completed.add(name)
        except (ValueError,RuntimeError,subprocess.TimeoutExpired,OSError) as error:
            if reusable:
                rejected_reuse.add(name)
            record('repair',f'{key} failed inspection: {error}. Retry {attempt+1}/3 with adjusted voice rate or faster encoder.')
    raise ValueError('Agent step budget exhausted')


if __name__=='__main__':
    if sys.argv[1]=='voice': voice_worker(sys.argv[2],Path(sys.argv[3]),sys.argv[4],int(sys.argv[5]))
