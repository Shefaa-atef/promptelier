from pathlib import Path
import json

from PIL import Image
import pytest

from backend.cards.render import generate_card, validate_delivery
from backend.cards.specification import RuleSpecificationProvider
from backend.media_tools import card_job, recolor_artwork


def test_external_artwork_preserves_delivery_contract(tmp_path):
    spec=RuleSpecificationProvider().interpret('A premium Ramadan gold card').specification
    source=tmp_path/'original.png'
    Image.new('RGB',(512,704),'#214685').save(source)
    outputs=generate_card(spec,tmp_path/'run',source)
    report=validate_delivery(tmp_path/'run/delivery')
    assert len(report)==3 and 'cards.zip' in outputs
    with Image.open(tmp_path/'run/delivery/Source/b.png') as back:
        assert back.getpixel((122,173))[:3]==(33,70,133)


def test_palette_revision_keeps_pixels_and_parent(tmp_path):
    provider=RuleSpecificationProvider()
    parent=provider.interpret('A premium blue gold Ramadan card').specification
    revision=provider.interpret('Change only the colors to green and silver',parent).specification
    source=tmp_path/'parent.png'
    image=Image.new('RGB',(4,4),'#142F65');image.putpixel((1,1),(216,175,88));image.save(source)
    before=source.read_bytes()
    recolor_artwork(source,tmp_path/'revision.png',parent.palette,revision.palette)
    assert source.read_bytes()==before
    with Image.open(tmp_path/'revision.png') as result:
        assert result.size==(4,4)
        assert result.getpixel((0,0))!=image.getpixel((0,0))
        assert result.getpixel((1,1))!=result.getpixel((0,0))


def test_custom_theme_is_kept_in_diffusion_job(tmp_path):
    provider=RuleSpecificationProvider()
    spec=provider.interpret('A winter dragon card with icy silver scales').specification
    job=card_job(spec,'A winter dragon card with icy silver scales',tmp_path)
    assert 'winter dragon' in job['prompt']
    assert 'rosette' not in job['prompt']
    assert job['width']==512 and job['height']==704


def test_realistic_compositor_has_vertical_video_audio_and_captions(tmp_path):
    import wave
    from backend.video import ffmpeg, inspect_video, render_realistic_scene
    portrait_clip=tmp_path/'talking.mp4'
    ffmpeg(['-f','lavfi','-i','color=c=teal:s=512x512:r=24:d=1',
            '-c:v','libx264','-pix_fmt','yuv420p',portrait_clip])
    with wave.open(str(tmp_path/'hook.wav'),'wb') as wav:
        wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(22050)
        wav.writeframes(b'\0\0'*22050)
    scene={'name':'hook','text':'جاهز للتحدي؟','seconds':1,'offset':118}
    render_realistic_scene(scene,tmp_path,'ar',portrait_clip)
    report=inspect_video(tmp_path/'hook.mp4',full=True)
    assert (report['width'],report['height'])==(540,960)
    assert report['h264'] and report['audio'] and report['duration']==1
    with Image.open(tmp_path/'hook-overlay.png') as overlay:
        assert overlay.getchannel('A').getbbox() and overlay.size==(540,960)
