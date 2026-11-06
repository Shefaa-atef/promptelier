"""Offline speech and content-addressed speech reuse."""
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import wave
from pathlib import Path
from backend.cards.render import ROOT


def voice_engine(language):
    choice=os.getenv('PROMPTELIER_VOICE_ENGINE','auto')
    ready=(ROOT/'models/piper/ar_JO-kareem-medium.onnx').is_file() and importlib.util.find_spec('piper') is not None
    if language=='ar' and choice!='legacy' and ready: return 'piper-ar_JO-kareem-medium'
    if choice=='piper' and language=='ar': raise ValueError('Piper Arabic voice is not installed')
    return 'espeak' if language=='ar' or sys.platform!='win32' else 'windows-sapi'


def voice_worker(text,path,language,rate):
    if voice_engine(language).startswith('piper'):
        from piper import PiperVoice, SynthesisConfig
        voice=PiperVoice.load(str(ROOT/'models/piper/ar_JO-kareem-medium.onnx'))
        config=SynthesisConfig(length_scale=175/rate,noise_scale=.4,noise_w_scale=.6,volume=.85)
        with wave.open(str(path),'wb') as wav:
            voice.synthesize_wav(text,wav,syn_config=config)
        return
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
    rate=175+attempt*25
    cached=voice_cache_path(text,language,rate)
    if cached.is_file():
        shutil.copy2(cached,path)
    else:
        args=[sys.executable,'-m','backend.video','voice',text,str(path),language,str(rate)]
        result=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=180)
        if result.returncode: raise ValueError(result.stderr.decode('utf8',errors='replace')[-700:])
    with wave.open(str(path)) as wav:
        duration=wav.getnframes()/wav.getframerate()
    if duration<.2 or duration>seconds-.1:
        raise ValueError(f'Voice duration {duration:.2f}s does not fit {seconds:.2f}s; retry at a faster rate')
    cached.parent.mkdir(parents=True,exist_ok=True)
    if not cached.exists(): shutil.copy2(path,cached)
    return duration


def voice_cache_path(text,language,rate):
    key=json.dumps({'text':text,'language':language,'rate':rate,'engine':voice_engine(language),
                    'config':'length-rate-v1-noise0.4-noisew0.6-volume0.85'},sort_keys=True)
    return ROOT/'models/voice-cache'/(hashlib.sha256(key.encode()).hexdigest()+'.wav')
