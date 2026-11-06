import time
import pytest
from fastapi.testclient import TestClient
from backend.main import create_app
from backend.router import route_prompt


@pytest.mark.parametrize('prompt,context,intent,target', [
    ('Create a premium Ramadan card with gold decorations.',None,'card','card'),
    ('Create a 20-second Arabic UGC advertisement for VIP Baloot.',None,'video','video'),
    ('Make the previous card blue instead of green.','card','revision','card'),
    ('Change only the opening hook of my previous video.','video','revision','video'),
    ('Make it blue',None,'clarification',None),
    ('Make it blue','card','revision','card'),
    ('Create a card and a video',None,'clarification',None),
    ('Help me',None,'clarification',None),
    ('Create a postcardigan',None,'clarification',None),
    ('Change my previous video','card','clarification',None),
    ('صمم بطاقة رمضانية',None,'card','card'),
    ('أنشئ فيديو إعلاني',None,'video','video'),
])
def test_router(prompt, context, intent, target):
    result = route_prompt(prompt, context)
    assert (result.intent, result.target) == (intent,target)


def wait_run(client, run, timeout=90):
    deadline=time.monotonic()+timeout
    while run['status']=='processing' and time.monotonic()<deadline:
        time.sleep(.1)
        run=client.get(f"/api/runs/{run['id']}").json()
    assert run['status']!='processing', 'Production timed out'
    return run


def test_api_and_persistence(tmp_path):
    path = tmp_path / 'runs.db'
    with TestClient(create_app(path,tmp_path/'outputs')) as client:
        assert client.get('/api/health').json()['generation_available'] is True
        first = client.post('/api/runs', json={'prompt':'Create a gold card'}).json()
        first=wait_run(client,first)
        assert first['status'] == 'completed' and 'cards.zip' in first['outputs']
        revision = client.post('/api/runs',json={'prompt':'Make it blue','parent_id':first['id']}).json()
        revision=wait_run(client,revision)
        assert revision['route']['intent'] == 'revision'
        assert revision['parent_id'] == first['id']
        assert any(e['stage'] == 'specification' for e in revision['events'])
        assert revision['design']['specification']['palette']['background'] != first['design']['specification']['palette']['background']
        assert client.post('/api/runs',json={'prompt':'   '}).status_code == 422
        assert client.post('/api/runs',json={'prompt':'x'*4001}).status_code == 422
        assert client.post('/api/runs',json={'prompt':'a card','parent_id':'missing'}).status_code == 404
        assert client.get('/api/references/secret').status_code == 404
        assert client.get('/api/runs/missing/download').status_code == 404
        assert client.get(f"/api/runs/{first['id']}/download").json()['id'] == first['id']
    with TestClient(create_app(path,tmp_path/'outputs')) as restarted:
        assert len(restarted.get('/api/runs').json()) == 2
        assert restarted.get(f"/api/runs/{first['id']}").json() == first
