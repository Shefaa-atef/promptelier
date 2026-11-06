import json, urllib.request, hashlib
from pathlib import Path
base='http://127.0.0.1:5173'
for endpoint in ['/', '/api/health','/api/references/premium','/api/references/preview']:
 with urllib.request.urlopen(base+endpoint) as r: print(endpoint,r.status,r.headers.get('Content-Type'),len(r.read()))
req=urllib.request.Request(base+'/api/runs',data=json.dumps({'prompt':'Create a premium Ramadan card with gold decorations.'}).encode(),headers={'Content-Type':'application/json'})
with urllib.request.urlopen(req) as r:
 run=json.load(r); print('live submit',r.status,run['route']['intent'],run['status']); assert run['status'] in ('processing','completed')
req=urllib.request.Request(base+'/api/runs',data=json.dumps({'prompt':'Make the previous card blue instead of green.','parent_id':run['id']}).encode(),headers={'Content-Type':'application/json'})
with urllib.request.urlopen(req) as r:
 revision=json.load(r); assert revision['route']['intent']=='revision'; print('live revision',r.status,revision['parent_id'])
rows=json.loads(Path('asset_inventory.json').read_text(encoding='utf8'))
assert all(hashlib.sha256(Path(x['path']).read_bytes()).hexdigest()==x['sha256'] for x in rows)
print('Original hashes unchanged:',len(rows),'files; PNGs:',sum(x['path'].endswith('.png') for x in rows))
