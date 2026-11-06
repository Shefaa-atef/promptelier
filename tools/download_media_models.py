"""Download pinned public models locally. Never upload project/source assets."""
import hashlib
import json
import time
import urllib.request
import argparse
import concurrent.futures
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MODEL_ID='Lykon/dreamshaper-8'
MODEL_REVISION='a7e52b98680b1ba8ff7bce97c7f9f2e2e5337917'


def file_hash(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def download(url,path):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.is_file() and path.stat().st_size:
        print(f'Already downloaded: {path.name}',flush=True)
        return
    partial=path.with_suffix(path.suffix+'.part')
    for attempt in range(3):
        try:
            start=partial.stat().st_size if partial.exists() else 0
            request=urllib.request.Request(url,headers={'Range':f'bytes={start}-'} if start else {})
            with urllib.request.urlopen(request,timeout=120) as response:
                append=start>0 and response.status==206
                count=start if append else 0
                next_report=count+128*1024*1024
                with partial.open('ab' if append else 'wb') as out:
                    while block:=response.read(1024*1024):
                        out.write(block); count+=len(block)
                        if count>=next_report:
                            print(f'{path.name}: {count/1024**2:.0f} MiB',flush=True)
                            next_report=count+128*1024*1024
            partial.replace(path)
            print(f'Downloaded: {path.name} ({path.stat().st_size/1024**2:.1f} MiB)',flush=True)
            return
        except Exception as error:
            print(f'Download attempt {attempt+1}: {error}',flush=True)
            if attempt==2: raise
            time.sleep(2)


def download_images():
    metadata=json.load(urllib.request.urlopen(f'https://huggingface.co/api/models/{MODEL_ID}/revision/{MODEL_REVISION}'))
    folder=ROOT/'models/dreamshaper-8'
    for item in metadata['siblings']:
        name=item['rfilename']
        wanted=(name.endswith(('.json','.txt','.md')) or name.endswith('.fp16.safetensors'))
        if wanted:
            download(f'https://huggingface.co/{MODEL_ID}/resolve/{MODEL_REVISION}/{name}',folder/name)
    manifest={'model':MODEL_ID,'revision':MODEL_REVISION,'license':'creativeml-openrail-m',
              'files':{p.relative_to(folder).as_posix():file_hash(p)
                       for p in folder.rglob('*') if p.is_file() and p.name!='download-manifest.json'}}
    (folder/'download-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')


def download_voice():
    folder=ROOT/'models/piper'
    base='https://huggingface.co/rhasspy/piper-voices/resolve/e7229f7d33a10e145e109b886d661984201ac3c4/ar/ar_JO/kareem/medium/'
    for name in ['ar_JO-kareem-medium.onnx','ar_JO-kareem-medium.onnx.json','MODEL_CARD']:
        download(base+name,folder/name)


def download_controlnet():
    revision='115a470d547982438f70198e353a921996e2e819'
    folder=ROOT/'models/controlnet-canny'
    for name in ['config.json','diffusion_pytorch_model.fp16.safetensors','README.md']:
        download('https://huggingface.co/lllyasviel/control_v11p_sd15_canny/resolve/'+revision+'/'+name,folder/name)
    (folder/'download-manifest.json').write_text(json.dumps({'model':'lllyasviel/control_v11p_sd15_canny',
        'revision':revision,'license':'openrail','files':{p.name:file_hash(p) for p in folder.iterdir()
        if p.is_file() and p.name!='download-manifest.json'}},indent=2),encoding='utf8')


def download_presenter():
    revision='cd4c0465ae0b54a6f85af57f5c65fec9fe23e7f8'
    repository='https://api.github.com/repos/OpenTalker/SadTalker'
    tree=json.load(urllib.request.urlopen(repository+'/git/trees/'+revision+'?recursive=1'))
    source=ROOT/'vendor/SadTalker-source'
    files=[item['path'] for item in tree['tree'] if item['type']=='blob' and
           (item['path'].startswith('src/') or item['path'] in ['LICENSE','inference.py','README.md','requirements.txt'])]
    def fetch(name):
        download('https://raw.githubusercontent.com/OpenTalker/SadTalker/'+revision+'/'+name,source/name)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(fetch,files))
    (source/'UPSTREAM_REVISION').write_text(revision)
    model_revision='df6f230f2fbec618d69e47229ea32dd224fc9c5c'
    folder=ROOT/'models/sadtalker'
    urls=[('https://huggingface.co/vinthony/SadTalker-V002rc/resolve/'+model_revision+'/'+name,folder/name)
          for name in ['SadTalker_V0.0.2_512.safetensors','mapping_00109-model.pth.tar']]
    urls += [('https://github.com/xinntao/facexlib/releases/download/v0.1.0/'+name,source/'gfpgan/weights'/name)
             for name in ['alignment_WFLW_4HG.pth','detection_Resnet50_Final.pth']]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda item:download(*item),urls))
    (folder/'MODEL_SOURCE.json').write_text(json.dumps({'repository':'vinthony/SadTalker-V002rc',
        'revision':model_revision,'code_revision':revision},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--kind',choices=['images','controlnet','voice','presenter','all'],default='images')
    kind=parser.parse_args().kind
    for name,action in [('images',download_images),('controlnet',download_controlnet),('voice',download_voice),('presenter',download_presenter)]:
        if kind in (name,'all'): action()
