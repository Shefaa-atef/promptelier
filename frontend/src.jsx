import React, {useEffect, useState} from 'react';
import {createRoot} from 'react-dom/client';
import './style.css';

const examples = ['Create a premium Ramadan card with gold decorations.', 'Create a 20-second Arabic UGC advertisement for VIP Baloot.'];
async function api(path, options) {
  const response = await fetch(path, options);
  if (!response.ok) { const body = await response.json().catch(()=>({})); throw new Error(typeof body.detail === 'string' ? body.detail : `Request failed (${response.status}).`); }
  return response.json();
}
function App(){
  const [runs,setRuns]=useState([]),[selected,setSelected]=useState(null),[prompt,setPrompt]=useState(''),[busy,setBusy]=useState(false),[error,setError]=useState(''),[online,setOnline]=useState(false),[context,setContext]=useState(null),[view,setView]=useState('studio');
  useEffect(()=>{Promise.all([api('/api/health'),api('/api/runs')]).then(([,history])=>{setOnline(true);setRuns(history);}).catch(()=>setError('Cannot reach the local backend. Start FastAPI, then reload.'));},[]);
  async function submit(e){
    e.preventDefault(); if(!prompt.trim()||busy)return;
    setBusy(true);setError('');
    try {const run=await api('/api/runs',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({prompt,parent_id:context?.id??null})});setRuns(r=>[run,...r]);setSelected(run);if(run.route.target)setContext(run);setPrompt('');setOnline(true);}
    catch(e){setError(e.message+' Check that the backend is running.');}finally{setBusy(false);}
  }
  function select(run){setSelected(run);setContext(run.route.target?run:null);setView('studio');}
  return <div className="app">
    <aside className="sidebar"><a className="brand" href="/" aria-label="Promptelier home"><span className="monogram">P<span>✧</span></span><span>promptelier<i>CREATIVE PRODUCTION STUDIO</i></span></a>
      <div className="workspace-label">YOUR WORKSPACE</div><nav><button className={view==='studio'?'active':''} onClick={()=>setView('studio')}><span>✧</span> Creative studio</button><button className={view==='history'?'active':''} onClick={()=>setView('history')}><span>◷</span> Run history <small>{runs.length}</small></button><button className={view==='assets'?'active':''} onClick={()=>setView('assets')}><span>▧</span> Asset library</button></nav>
      <div className="project"><span className="tiny">CURRENT PROJECT</span><strong>VIP Baloot</strong><p>Creative assessment</p><span className="tag">LOCAL WORKSPACE</span></div>
      <div className="sidebar-bottom"><span className="status-dot"/> Zero cloud API charges<p>Phase 1 · Foundation</p><div className="avatar">Y</div><span>Your local studio</span></div>
    </aside>
    <main><header><span>Workspace <b>/</b> {view==='studio'?'Creative studio':view==='history'?'Run history':'Asset library'}</span><span className="connection"><span className={'status-dot '+(!online?'offline':'')}/>{online?'Backend connected':'Backend offline'}</span></header>
      <div className="content"><div className="page-heading"><div><span className="eyebrow">FROM A THOUGHT TO A FINISHED ASSET</span><h1>Your next idea starts here<span>.</span></h1><p>One brief. A world of creative possibilities.</p></div><span className="phase">FOUNDATION <b>01</b></span></div>
      {error&&<div role="alert" className="error">{error}<button onClick={()=>setError('')} aria-label="Dismiss error">×</button></div>}
      {view==='studio'&&<><div className="studio-grid"><section className="brief panel"><div className="panel-title"><span>✧ &nbsp; Creative brief</span><span className="tiny">AUTO ROUTING</span></div><h2>What would you like to create?</h2><p>Describe your vision. We’ll find the right workflow.</p>
      <form onSubmit={submit}><label className="sr-only" htmlFor="prompt">Your creative prompt</label><textarea id="prompt" dir="auto" maxLength={4000} value={prompt} onChange={e=>setPrompt(e.target.value)} placeholder={'A premium Ramadan card with intricate gold decorations, a midnight blue palette, and a celestial feel…'} required/><div className="input-footer"><span>{prompt.length} / 4,000</span><span>English or Arabic</span></div>
      <div className="context">{context?<><span>↳ Revising: {context.prompt.slice(0,48)}</span><button type="button" onClick={()=>setContext(null)}>New brief ×</button></>:<span>↳ New brief · no previous context</span>}</div>
      <button className="submit" disabled={busy||!prompt.trim()}>{busy?'Routing your brief…':'Submit brief'} <span>↗</span></button></form>
      <div className="examples"><span className="tiny">A LITTLE INSPIRATION</span>{examples.map((x,i)=><button key={x} onClick={()=>{setPrompt(x);setContext(null)}}><span>{i===0?'♧':'▷'}</span>{i===0?'A premium Ramadan card':'An Arabic UGC advertisement'}<span>↗</span></button>)}</div>
      <div className="notice"><span>ⓘ</span><p><strong>Your studio is taking shape.</strong> Brief routing is ready. Card and video production arrive in the next phases.</p></div></section>
      <section className="preview panel"><div className="panel-title"><span>Preview stage</span><span className="tag">SUPPLIED REFERENCE</span></div><div className="art-stage"><span className="stage-corner tl"/><span className="stage-corner br"/><div className="orbit"/><img src="/api/references/premium" alt="Supplied VIP Baloot card reference: golden crescent on blue"/><div className="art-caption"><span>VIP BALOOT COLLECTION</span><h2>Crafted for the occasion.</h2><p>Original supplied artwork · not generated</p></div></div><div className="preview-footer"><span><span className="status-dot"/> Reference asset</span><span>250 × 346 · PNG</span></div></section></div>
      <section className="result panel" aria-live="polite"><div className="panel-title"><span>{busy?'Processing brief':selected?'Brief result':'Ready when you are'}</span><span className="tiny">{selected?selected.id.slice(0,8):'NO OUTPUT YET'}</span></div>{selected?<><div className="result-line"><span className="route-badge">{selected.route.intent}</span><strong>{selected.status==='needs_clarification'?'A little more direction needed':'Brief saved · production not implemented'}</strong><a href={`/api/runs/${selected.id}/download`} download>Download run log ↓</a></div><p>{selected.message}</p><blockquote dir="auto">{selected.prompt}</blockquote><details><summary>Execution log · {selected.events.length} events</summary>{selected.events.map((e,i)=><div className="event" key={i}><time>{new Date(e.time).toLocaleTimeString()}</time><b>{e.stage}</b><span>{e.message}</span></div>)}</details></>:<p>Submit a brief to inspect its route and execution log. Generated previews and asset downloads will appear here when production is available.</p>}</section></>}
      {view==='history'&&<section className="panel history"><div className="panel-title">Run history <span className="tiny">SAVED ON THIS COMPUTER</span></div>{runs.length?runs.map(r=><button className="history-row" key={r.id} onClick={()=>select(r)}><span className="route-badge">{r.route.intent}</span><span>{r.prompt}<small>{new Date(r.created_at).toLocaleString()} · {r.status.replaceAll('_',' ')}</small></span><span>↗</span></button>):<p>No runs yet. Submit your first creative brief in the studio.</p>}</section>}
      {view==='assets'&&<section className="panel assets"><div className="panel-title">Supplied references <span className="tag">PRIVATE · LOCAL ONLY</span></div><p>These original assets are visual references, not generated results.</p><div className="asset-grid"><figure><img src="/api/references/premium" alt="Supplied premium card back"/><figcaption>Card back · 250 × 346 PNG</figcaption></figure><figure><img src="/api/references/preview" alt="Supplied store preview with back and face"/><figcaption>Store preview · 208 × 261 PNG</figcaption></figure></div></section>}
      <footer><span>PROMPTELIER <b> / </b> A workspace for ideas worth making.</span><span>Local by design. Yours to create.</span></footer></div>
    </main></div>
}
createRoot(document.getElementById('root')).render(<App/>);
