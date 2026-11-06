"""FFmpeg inspection, captions, and scene composition."""
import hashlib
import re
import subprocess
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


def scene_graphics(scene,folder,language):
    font_path=asset('Alexandria-Medium.ttf')
    title=ImageFont.truetype(str(font_path),26)
    small=ImageFont.truetype(str(font_path),16)
    caption_font=ImageFont.truetype(str(font_path),29)
    text=scene['text']
    if language=='ar':
        import arabic_reshaper
        from bidi.algorithm import get_display
        reshaper=arabic_reshaper.ArabicReshaper(configuration={'use_unshaped_instead_of_isolated':True})
        def display(s): return get_display(reshaper.reshape(s))
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


def render_realistic_scene(scene,folder,language,presenter_clip=None,attempt=0):
    """Compose a real animated portrait, or an explicitly labelled voiceover fallback."""
    name=scene['name']; duration=scene['seconds']
    font=ImageFont.truetype(str(asset('Alexandria-Medium.ttf')),29)
    small=ImageFont.truetype(str(asset('Alexandria-Medium.ttf')),14)
    if language=='ar':
        import arabic_reshaper
        from bidi.algorithm import get_display
        # Alexandria lacks some isolated presentation forms; base Arabic glyphs work.
        reshaper=arabic_reshaper.ArabicReshaper(configuration={'use_unshaped_instead_of_isolated':True})
        def display(text): return get_display(reshaper.reshape(text))
    else:
        def display(text): return text
    overlay=Image.new('RGBA',(540,960)); draw=ImageDraw.Draw(overlay)
    hero=presenter_clip is not None and name in ('hook','cta')
    top=700 if hero else 795
    draw.rounded_rectangle((18,top,522,top+130),18,fill=(10,20,37,235),outline=(211,176,106,180),width=1)
    lines=[]; current=''
    for word in scene['text'].split():
        candidate=(current+' '+word).strip()
        if draw.textlength(display(candidate),font=font)>458 and current:
            lines.append(current); current=word
        else: current=candidate
    lines.append(current)
    if len(lines)>3: raise ValueError('Caption exceeds three lines')
    for index,line in enumerate(lines):
        y=top+65+(index-(len(lines)-1)/2)*36
        draw.text((270,y),display(line),font=font,fill='white',anchor='mm')
    logo=Image.open(asset('Logo.png')).convert('RGBA');logo.thumbnail((80,80))
    overlay.alpha_composite(logo,(20,18))
    if presenter_clip:
        draw.text((520,28),display('مقدم افتراضي' if language=='ar' else 'Fictional presenter'),
                  font=small,fill='white',anchor='ra')
    overlay_path=folder/f'{name}-overlay.png';overlay.save(overlay_path)
    args=['-ss',scene['offset'],'-stream_loop','-1','-i',asset('Gameplay.mp4')]
    # Fill the side bars with blurred footage while retaining the complete game screen.
    graph=('[0:v]split[back][front];[back]scale=540:960:force_original_aspect_ratio=increase,crop=540:960,gblur=sigma=18,eq=brightness=-0.25[bg];'
           '[front]scale=540:960:force_original_aspect_ratio=decrease[game];'
           '[bg][game]overlay=(W-w)/2:(H-h)/2[table];')
    if presenter_clip:
        args += ['-i',presenter_clip]
        if hero:
            graph += f'[table]gblur=sigma=18,eq=brightness=-0.2[soft];[1:v]scale=540:540,tpad=stop_mode=clone:stop_duration={duration}[host];[soft][host]overlay=0:100[scene];'
        else:
            graph += f'[1:v]scale=170:170,tpad=stop_mode=clone:stop_duration={duration},drawbox=x=0:y=0:w=iw:h=ih:color=0xD3B06A:t=2[host];[table][host]overlay=350:110[scene];'
        overlay_index,audio_index=2,3
    else:
        graph += '[table]null[scene];'
        overlay_index,audio_index=1,2
    args += ['-loop','1','-framerate','24','-i',overlay_path,'-i',folder/f'{name}.wav']
    graph += (f'[scene][{overlay_index}:v]overlay=0:0,format=yuv420p[v];'
              f'[{audio_index}:a]apad,atrim=duration={duration},afade=t=out:st={duration-.15}:d=0.15[a]')
    ffmpeg([*args,'-filter_complex',graph,'-map','[v]','-map','[a]','-t',duration,'-r','24',
            '-c:v','libx264','-preset','ultrafast' if attempt else 'veryfast','-crf','21',
            '-c:a','aac','-ar','44100','-ac','2','-movflags','+faststart',folder/f'{name}.mp4'])
