"""Run the five-minute demo's briefs against the actual local HTTP application."""
import json
import sys
import time
import urllib.request
from pathlib import Path

BASE='http://127.0.0.1:5173'
if hasattr(sys.stdout,'reconfigure'):
    sys.stdout.reconfigure(encoding='utf8')


def submit(prompt,parent=None):
    request=urllib.request.Request(BASE+'/api/runs',data=json.dumps({'prompt':prompt,'parent_id':parent}).encode(),
                                   headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(request) as response: run=json.load(response)
    print('Submitted',run['id'],flush=True)
    deadline=time.monotonic()+3600
    last_stage=None
    while run['status']=='processing' and time.monotonic()<deadline:
        time.sleep(1.5)
        with urllib.request.urlopen(BASE+'/api/runs/'+run['id']) as response: run=json.load(response)
        stage=run['events'][-1]['stage']
        if stage!=last_stage:
            print(stage,run['events'][-1]['message'][:180],flush=True);last_stage=stage
    if run['status']!='completed': raise RuntimeError(run['message'])
    for name in run['outputs']:
        with urllib.request.urlopen(f"{BASE}/api/runs/{run['id']}/files/{name}") as response:
            assert response.status==200 and response.read()
    with urllib.request.urlopen(f"{BASE}/api/runs/{run['id']}/download") as response:
        Path('outputs',run['id'],'execution.json').write_bytes(response.read())
    print(run['id'],run['prompt'],flush=True)
    return run


if __name__=='__main__':
    ramadan=submit('A premium midnight blue Ramadan card with a large central golden crescent, tiny stars and intricate Islamic filigree.')
    botanical=submit('A premium emerald botanical playing card back, sculpted gold acanthus leaves and an ornate central crown, balanced filigree, pure decorative ornament without lettering.')
    colors=submit('Change only the colors to purple and silver',ramadan['id'])
    video=submit('Create a 20-second Arabic UGC video advertisement for VIP Baloot.')
    hook=submit('Change only the opening hook to "جاهز لتحدي بلوت جديد؟"',video['id'])
    examples=dict(zip(['ramadan','botanical','color_revision','arabic_video','hook_revision'],
                      [r['id'] for r in (ramadan,botanical,colors,video,hook)]))
    Path('outputs/examples.json').write_text(json.dumps(examples,indent=2),encoding='utf8')
    print(json.dumps(examples,indent=2))
