from pathlib import Path
from PIL import Image, ImageOps, ImageDraw
from pypdf import PdfReader
import json, hashlib
root=Path('task material'); rows=[]; thumbs=[]
for p in sorted(root.rglob('*')):
 if not p.is_file(): continue
 r={'path':p.as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
 if p.suffix.lower()=='.png':
  with Image.open(p) as im:
   im.load(); a=im.convert('RGBA').getchannel('A'); r.update(format=im.format,width=im.width,height=im.height,mode=im.mode,alpha_extrema=a.getextrema(),transparent_pixels=sum(v for k,v in enumerate(a.histogram()) if k<255))
   if '/source/' not in p.as_posix() or p.name in ['as.png','b.png']:
    t=Image.new('RGB',(170,210),'#303746'); v=im.convert('RGBA'); v.thumbnail((145,170)); t.paste(v,((170-v.width)//2,5),v); ImageDraw.Draw(t).text((5,180),p.name,fill='white'); thumbs.append(t)
 elif p.suffix=='.ai':
  r['header']=p.read_bytes()[:24].decode('latin1')
  try:
   pdf=PdfReader(p); r['pdf_pages']=len(pdf.pages); r['page_boxes']=[list(map(float,x.mediabox)) for x in pdf.pages]; r['metadata']=str(pdf.metadata)
  except Exception as e:r['inspection_error']=str(e)
 rows.append(r)
Path('asset_inventory.json').write_text(json.dumps(rows,indent=2),encoding='utf8')
canvas=Image.new('RGB',(170*7,210*((len(thumbs)+6)//7)),'#303746')
for i,t in enumerate(thumbs):canvas.paste(t,((i%7)*170,(i//7)*210))
canvas.save('asset_contact_sheet.png')
print(json.dumps(rows,indent=2))
