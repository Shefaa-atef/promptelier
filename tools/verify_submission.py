"""Verify saved assessment examples, downloads, reuse, and original asset integrity."""
import hashlib
import json
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.cards.render import DELIVERY, validate_delivery
from backend.video import inspect_video


def checksum(path):
    with path.open('rb') as file:
        return hashlib.file_digest(file, 'sha256').hexdigest()


def verify(base='http://127.0.0.1:5173'):
    examples = json.loads((ROOT/'outputs/examples.json').read_text())
    report = {'examples': examples, 'cards': {}, 'videos': {}, 'reuse': {}}
    for label, run_id in examples.items():
        folder = ROOT/'outputs'/run_id
        with urllib.request.urlopen(f'{base}/api/runs/{run_id}') as response:
            run = json.load(response)
        assert run['status'] == 'completed', run['message']
        for name in run['outputs']:
            local = folder/('delivery/'+name if name in DELIVERY else name)
            with urllib.request.urlopen(f'{base}/api/runs/{run_id}/files/{name}') as response:
                assert hashlib.sha256(response.read()).hexdigest() == checksum(local), name
        with urllib.request.urlopen(f'{base}/api/runs/{run_id}/download') as response:
            (folder/'execution.json').write_bytes(response.read())
        if run['route']['target'] == 'card':
            report['cards'][label] = validate_delivery(folder/'delivery')
            with zipfile.ZipFile(folder/'cards.zip') as archive:
                assert set(archive.namelist()) == set(DELIVERY)
                for name in DELIVERY:
                    assert archive.read(name) == (folder/'delivery'/name).read_bytes()
        else:
            result = inspect_video(folder/'video.mp4', full=True)
            assert result['width'] == 540 and result['height'] == 960
            assert 15 <= result['duration'] <= 30.2 and result['audio'] and result['h264']
            report['videos'][label] = result
    parent = ROOT/'outputs'/examples['arabic_video']
    revised = ROOT/'outputs'/examples['hook_revision']
    parent_report = json.loads((parent/'validation.json').read_text())
    assert checksum(parent/'video.mp4') == parent_report['sha256']
    assert checksum(parent/'presenter.png') == checksum(revised/'presenter.png')
    for scene in ('hook', 'gameplay', 'challenge', 'cta'):
        before, after = checksum(parent/f'{scene}.mp4'), checksum(revised/f'{scene}.mp4')
        assert before == parent_report['scene_sha256'][scene], 'Parent scene changed after completion'
        assert (before == after) == (scene != 'hook'), scene
        report['reuse'][scene] = {'original_sha256': before, 'revision_sha256': after, 'identical': before == after}
    decisions = json.loads((revised/'decisions.json').read_text(encoding='utf8'))
    assert sum(item['tool'] == 'reuse_scene' for item in decisions) == 3
    originals = json.loads((ROOT/'asset_inventory.json').read_text())
    for item in originals:
        assert checksum(ROOT/item['path']) == item['sha256'], item['path']
    report['original_assets_unchanged'] = len(originals)
    (ROOT/'outputs/submission-verification.json').write_text(json.dumps(report, indent=2), encoding='utf8')
    package(examples)
    print(json.dumps(report, indent=2))


def package(examples):
    """Copy only verified delivery files and evidence into a private handoff bundle."""
    bundle=ROOT/'outputs/submission'
    for label,run_id in examples.items():
        source=ROOT/'outputs'/run_id
        if label in ('ramadan','botanical'):
            for name in DELIVERY:
                target=bundle/'cards'/label/name
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(source/'delivery'/name,target)
            shutil.copy2(source/'cards.zip',bundle/'cards'/label/'cards.zip')
        elif label in ('arabic_video','hook_revision'):
            target=bundle/'videos'/('original.mp4' if label=='arabic_video' else 'revised-hook.mp4')
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(source/'video.mp4',target)
        evidence=bundle/'logs'/label
        evidence.mkdir(parents=True,exist_ok=True)
        for name in ('execution.json','generation.json','validation.json','plan.json','decisions.json','specification.json'):
            if (source/name).is_file(): shutil.copy2(source/name,evidence/name)
    shutil.copy2(ROOT/'outputs/submission-verification.json',bundle/'verification.json')
    for name in ('README.md','PROJECT_PLAN.md','.env.example','docs/DEMO.md','docs/IMPLEMENTATION_NOTES.md'):
        target=bundle/name;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(ROOT/name,target)
    (bundle/'SUBMISSION.txt').write_text(
        'PRIVATE TAMATEM ASSESSMENT OUTPUTS\n'
        'cards/ contains both exact three-PNG deliveries and individual ZIPs.\n'
        'videos/ contains the original and hook-revised 20-second advertisements.\n'
        'logs/ and verification.json contain execution, validation and SHA-256 reuse evidence.\n'
        'Source and environment setup: https://github.com/Shefaa-atef/promptelier (private).\n'
        'Run README commands from the source checkout, not this output-only bundle.\n'
        'See docs/IMPLEMENTATION_NOTES.md for models, costs, manual work and limitations.\n'
        'Arabic listening review and creative approval remain human review tasks.\n'
        'Do not publish this bundle; it contains derived proprietary assets.\n',encoding='utf8')
    hashes={p.relative_to(bundle).as_posix():checksum(p) for p in bundle.rglob('*') if p.is_file() and p.name!='manifest.json'}
    (bundle/'manifest.json').write_text(json.dumps(hashes,indent=2),encoding='utf8')
    with zipfile.ZipFile(ROOT/'outputs/Promptelier-assessment.zip','w',zipfile.ZIP_DEFLATED) as archive:
        for path in bundle.rglob('*'):
            if path.is_file(): archive.write(path,path.relative_to(bundle).as_posix())


if __name__ == '__main__':
    verify(sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:5173')
