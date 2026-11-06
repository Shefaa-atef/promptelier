import hashlib
import json
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageChops

from backend.cards.render import DELIVERY, generate_card, validate_delivery
from backend.cards.specification import RuleSpecificationProvider
from backend.main import create_app
from tests.test_app import wait_run
from backend.video import plan_video, run_agent


def test_card_outputs_determinism_and_geometry(tmp_path):
    provider=RuleSpecificationProvider()
    original=provider.interpret('premium Ramadan card midnight blue gold crescent stars').specification
    revised=provider.interpret('Change only the colors to emerald and silver',original).specification
    for name,spec in [('a',original),('copy',original),('revision',revised)]:
        generate_card(spec,tmp_path/name)
    a=tmp_path/'a/delivery'
    assert (a/'Source/b.png').read_bytes()==(tmp_path/'copy/delivery/Source/b.png').read_bytes()
    assert (a/'Source/b.png').read_bytes()!=(tmp_path/'revision/delivery/Source/b.png').read_bytes()
    with Image.open(a/'Source/b.png') as first, Image.open(tmp_path/'revision/delivery/Source/b.png') as second:
        assert not ImageChops.difference(first.getchannel('A'),second.getchannel('A')).getbbox()
    with zipfile.ZipFile(tmp_path/'a/cards.zip') as z:
        assert set(z.namelist())==set(DELIVERY)
        for name in DELIVERY: assert z.read(name)==(a/name).read_bytes()
    (a/'extra.txt').write_text('wrong')
    with pytest.raises(ValueError): validate_delivery(a)


def test_api_downloads_failure_and_restart(tmp_path,monkeypatch):
    import backend.main as main
    app=create_app(tmp_path/'runs.db',tmp_path/'outputs')
    with TestClient(app) as client:
        first=wait_run(client,client.post('/api/runs',json={'prompt':'A premium gold card'}).json())
        assert first['status']=='completed',first['message']
        for name in first['outputs']:
            response=client.get(f"/api/runs/{first['id']}/files/{name}")
            assert response.status_code==200
        assert client.get(f"/api/runs/{first['id']}/files/specification.json").status_code==404
        assert client.get(f"/api/runs/{first['id']}/files/../../.env").status_code==404
        def fail(*args): raise ValueError('Injected renderer fault')
        monkeypatch.setattr(main,'generate_card',fail)
        failed=wait_run(client,client.post('/api/runs',json={'prompt':'A blue card'}).json())
        assert failed['status']=='failed' and failed['outputs']==[]
        assert 'Injected renderer fault' in failed['message']
        assert client.get(f"/api/runs/{failed['id']}/files/cards.zip").status_code==404


def test_video_agent_repairs_and_reuses_real_scenes(tmp_path,monkeypatch):
    import backend.video as video
    plan=plan_video('Create a 15-second Arabic UGC video')
    events=[]; original_render=video.render_scene; injected=set()
    def fail_once(scene,folder,attempt):
        if scene['name']=='hook' and not injected:
            injected.add('failure'); raise ValueError('Injected encoder failure')
        return original_render(scene,folder,attempt)
    monkeypatch.setattr(video,'render_scene',fail_once)
    run_agent(plan,tmp_path/'parent',lambda a,b:events.append((a,b)))
    assert any('repair:' in message for stage,message in events)
    before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (tmp_path/'parent').glob('*.mp4')}
    revision=plan_video('Change only the opening hook to "جاهز للتحدي؟"',plan)
    run_agent(revision,tmp_path/'revision',lambda *args:None,tmp_path/'parent',plan)
    report=json.loads((tmp_path/'revision/validation.json').read_text())
    assert report['reused_scenes']==['gameplay','challenge','cta']
    for name in ('gameplay','challenge','cta'):
        assert hashlib.sha256((tmp_path/f'revision/{name}.mp4').read_bytes()).hexdigest()==before[name+'.mp4']
    assert hashlib.sha256((tmp_path/'revision/hook.mp4').read_bytes()).hexdigest()!=before['hook.mp4']
    for name,checksum in before.items():
        assert hashlib.sha256((tmp_path/'parent'/name).read_bytes()).hexdigest()==checksum


def test_video_policy_budget_and_prompt_bounds(tmp_path,monkeypatch):
    import backend.video as video
    with pytest.raises(ValueError): plan_video('Create a 60-second video')
    with pytest.raises(ValueError): plan_video('Change all music',plan_video('A video'))
    calls=[]
    def unavailable(*args): calls.append(1); raise ValueError('Voice unavailable')
    monkeypatch.setattr(video,'synthesize',unavailable)
    with pytest.raises(ValueError,match='exhausted three attempts'):
        run_agent(plan_video('Create a video'),tmp_path,lambda *args:None)
    assert len(calls)==3
