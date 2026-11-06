"""Compatibility launcher for pinned SadTalker, isolated from the web service."""
import argparse
import os
import runpy
import shutil
import sys
import types
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'vendor/SadTalker-source'


def animate(portrait,audio,output):
    import numpy as np
    from PIL import Image
    import torch
    import imageio_ffmpeg
    torch.set_num_threads(4)

    if not torch.cuda.is_available(): raise RuntimeError('SadTalker requires the verified CUDA environment')
    if not (SOURCE/'UPSTREAM_REVISION').is_file(): raise RuntimeError('Pinned SadTalker source is not installed')
    # Upstream predates NumPy 2 and Pillow 10. Keep the changes in this small
    # launcher rather than rewriting third-party model code or downgrading the app.
    for name,value in [('float',float),('int',int),('complex',complex)]:
        if name not in np.__dict__: setattr(np,name,value)
    if not hasattr(np,'VisibleDeprecationWarning'):
        np.VisibleDeprecationWarning=np.exceptions.VisibleDeprecationWarning
    if not hasattr(Image,'ANTIALIAS'): Image.ANTIALIAS=Image.Resampling.LANCZOS

    # Restoration is optional and is not used. Avoid its unrelated legacy
    # BasicSR/GFPGAN import; native SadTalker still performs the actual animation.
    enhancer=types.ModuleType('src.utils.face_enhancer')
    def unavailable(*args,**kwargs): raise RuntimeError('Optional GFPGAN enhancement is not installed')
    enhancer.enhancer_generator_with_len=unavailable
    enhancer.enhancer_list=unavailable
    sys.modules['src.utils.face_enhancer']=enhancer
    binary_dir=ROOT/'models/bin'; binary_dir.mkdir(parents=True,exist_ok=True)
    ffmpeg=binary_dir/'ffmpeg.exe'
    if not ffmpeg.exists(): shutil.copy2(imageio_ffmpeg.get_ffmpeg_exe(),ffmpeg)
    os.environ['PATH']=str(binary_dir)+os.pathsep+os.environ.get('PATH','')
    os.environ['IMAGEIO_FFMPEG_EXE']=str(ffmpeg)
    os.chdir(SOURCE)
    sys.path.insert(0,str(SOURCE))
    from src.face3d.util import preprocess as face_preprocess
    original_pos=face_preprocess.POS
    def scalar_translation(*args,**kwargs):
        translation,scale=original_pos(*args,**kwargs)
        # NumPy 2 rejects the upstream mix of scalar values and (1,) arrays.
        return translation.reshape(-1),scale
    face_preprocess.POS=scalar_translation
    output=Path(output).resolve(); output.mkdir(parents=True,exist_ok=True)
    sys.argv=[str(SOURCE/'inference.py'),'--source_image',str(Path(portrait).resolve()),
              '--driven_audio',str(Path(audio).resolve()),'--result_dir',str(output),
              '--checkpoint_dir',str(ROOT/'models/sadtalker'),'--size','512','--batch_size','1',
              '--still','--preprocess','full']
    runpy.run_path(str(SOURCE/'inference.py'),run_name='__main__')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('portrait',type=Path)
    parser.add_argument('audio',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    # Resolve paths before the upstream tool changes working directory.
    animate(args.portrait.resolve(),args.audio.resolve(),args.output.resolve())
