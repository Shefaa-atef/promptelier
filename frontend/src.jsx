import React, {useEffect, useRef, useState} from 'react';
import {createRoot} from 'react-dom/client';
import './style.css';

const fileUrl = (run, name) => `/api/runs/${run.id}/files/${name}`;
const examples = [
  ['Ramadan card', 'Create a premium midnight blue Ramadan card with gold crescent, stars and Islamic geometry.'],
  ['UGC video', 'Create a 20-second Arabic UGC advertisement for VIP Baloot.'],
];
async function api(path, options) {
  const response = await fetch(path, options);
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(typeof body.detail === 'string' ? body.detail : `Request failed (${response.status}).`);
  }
  return response.json();
}
function App() {
  const [runs, setRuns] = useState([]);
  const [selected, setSelected] = useState(null);
  const [prompt, setPrompt] = useState('');
  const [context, setContext] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [preview, setPreview] = useState('Source/b.png');
  const historyDialog = useRef(null);
  const promptInput = useRef(null);
  const processing = runs.some(run => run.status === 'processing');

  useEffect(() => {
    api('/api/runs').then(setRuns).catch(() => setError('The studio is offline. Start the local server and reload.'));
  }, []);
  useEffect(() => {
    if (!processing) return;
    let active = true;
    const timer = setInterval(() => api('/api/runs').then(history => {
      if (!active) return;
      setRuns(history);
      setSelected(current => current ? history.find(run => run.id === current.id) ?? current : null);
      setContext(current => current ? history.find(run => run.id === current.id) ?? current : null);
    }).catch(() => {
      if (active) setError('Connection lost. Your work is saved; reload when the server is available.');
    }), 1500);
    return () => { active = false; clearInterval(timer); };
  }, [processing]);

  function startNew() {
    setContext(null); setSelected(null); setPrompt(''); setError('');
    setPreview('Source/b.png'); promptInput.current?.focus();
  }
  async function submit(event) {
    event.preventDefault();
    if (!prompt.trim() || submitting || selected?.status === 'processing') return;
    setSubmitting(true); setError('');
    try {
      const run = await api('/api/runs', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({prompt, parent_id: context?.id ?? null}),
      });
      setRuns(previous => [run, ...previous]); setSelected(run); setPreview('Source/b.png');
      if (run.route.target && run.status !== 'needs_clarification') setContext(run);
      setPrompt('');
    } catch (problem) { setError(problem.message); }
    finally { setSubmitting(false); }
  }
  function select(run) {
    setSelected(run); setContext(run.route.target ? run : null); setPreview('Source/b.png');
    historyDialog.current.close();
  }
  async function showHistory() {
    historyDialog.current.showModal();
    try { setRuns(await api('/api/runs')); } catch (problem) { setError(problem.message); }
  }
  const completed = selected?.status === 'completed';
  const working = submitting || selected?.status === 'processing';
  const isVideo = selected?.route.target === 'video';
  const previewChoices = [['Source/b.png', 'Card', '250 × 346'], ['cardPreview.png', 'Store preview', '208 × 261'], ['Symbols/cardIcon.png', 'Icon', '46 × 64']];

  return <div className="studio">
    <header className="topbar">
      <a href="/" className="wordmark" aria-label="Promptelier home">promptelier<span>.</span></a>
      <button className="quiet-button" onClick={showHistory}>Recent work <span aria-hidden="true">↗</span></button>
    </header>
    <main className={selected ? 'workspace has-result' : 'workspace'}>
      <section className="composer" aria-labelledby="brief-heading">
        <div className="intro"><h1 id="brief-heading">{context ? 'Refine your work.' : 'What would you like to make?'}</h1>
          <p>{context ? `Describe a change to this ${context.route.target}.` : 'Describe a card design or a video.'}</p>
        </div>
        <form onSubmit={submit}>
          <label className="sr-only" htmlFor="prompt">Creative brief</label>
          <div className="prompt-box"><textarea ref={promptInput} id="prompt" dir="auto" maxLength={4000} value={prompt}
            onChange={event => setPrompt(event.target.value)} placeholder={context ? (isVideo ? 'Change only the opening hook to “…”' : 'Make the background deep emerald green…') : 'A midnight-blue Ramadan card with intricate gold ornament…'} required/>
            <div className="prompt-actions"><span className="input-hint">{context ? `Editing ${context.route.target}` : 'English or Arabic'}</span>
              <button className="create-button" disabled={working || !prompt.trim()}>{working ? 'Creating…' : context ? 'Apply change' : 'Create'} <span aria-hidden="true">↑</span></button>
            </div>
          </div>
        </form>
        <div className="below-prompt">{context ? <button className="text-button" onClick={startNew}>Start something new</button> :
          <div className="examples"><span>Try</span>{examples.map(([label, value]) => <button key={label} onClick={() => {setPrompt(value); promptInput.current.focus();}}>{label}</button>)}</div>}
        </div>
        {error && <div className="error" role="alert"><span>{error}</span><button aria-label="Dismiss error" onClick={() => setError('')}>×</button></div>}
      </section>
      {selected && <section className="result" aria-label="Your result" aria-live="polite">
        {completed ? <>
          <div className="result-toolbar"><span className="result-label">{isVideo ? 'Your video' : 'Your card'}</span>
            <a className="download-button" href={fileUrl(selected, isVideo ? 'video.mp4' : 'cards.zip')} download>Download {isVideo ? 'video' : 'ZIP'} <span aria-hidden="true">↓</span></a>
          </div>
          {!isVideo && <div className="preview-tabs" role="tablist" aria-label="Preview format">{previewChoices.map(([name, label]) =>
            <button key={name} role="tab" aria-selected={preview === name} onClick={() => setPreview(name)}>{label}</button>)}</div>}
          <div className={'media-stage ' + (isVideo ? 'video-stage' : '')}>
            {isVideo ? <video aria-label="Generated video" key={selected.id} controls preload="metadata" poster={fileUrl(selected, 'poster.png')} src={fileUrl(selected, 'video.mp4')}/> :
              <img key={preview} className={preview === 'Symbols/cardIcon.png' ? 'icon-preview' : ''} src={fileUrl(selected, preview)} alt={previewChoices.find(choice => choice[0] === preview)[1]}/>}
          </div>
          <div className="media-caption"><span>{isVideo ? '540 × 960 · MP4' : `${previewChoices.find(choice => choice[0] === preview)[2]} · PNG`}</span>
            {!isVideo && <a href={fileUrl(selected, preview)} download>Download PNG ↓</a>}
          </div>
        </> : <div className="status-message" role="status">
          {selected.status === 'processing' ? <><span className="spinner"/><h2>Creating your {isVideo ? 'video' : 'card'}…</h2><p>You can leave this open while it finishes.</p></> :
            <><h2>{selected.status === 'failed' ? 'This attempt failed.' : selected.status === 'needs_clarification' ? 'A little more detail.' : 'Saved brief'}</h2><p>{selected.message}</p></>}
        </div>}
        <details className="work-details"><summary>Work details</summary>
          <p className="saved-prompt" dir="auto">{selected.prompt}</p>
          <p className="method-note">{isVideo ? 'Current video method: illustrated host and offline synthetic voice. Arabic speech is robotic.' : 'Current card method: procedural illustration using the supplied frames.'}</p>
          <div className="detail-links"><a href={`/api/runs/${selected.id}/download`} download>Download execution log</a>
            {completed && selected.outputs.filter(name => name.endsWith('.json')).map(name => <a href={fileUrl(selected, name)} key={name} download>{name}</a>)}
          </div>
          {selected.design && <details><summary>Design specification</summary><pre>{JSON.stringify(selected.design, null, 2)}</pre></details>}
          <details><summary>Execution log · {selected.events.length} events</summary><ol className="events">{selected.events.map((event, index) => <li key={index}><span>{event.stage.replaceAll('_', ' ')}</span><p>{event.message}</p></li>)}</ol></details>
        </details>
      </section>}
    </main>
    <footer className="footer">Private workspace · VIP Baloot</footer>
    <dialog ref={historyDialog} className="history-dialog">
      <div className="dialog-heading"><h2>Recent work</h2><button className="quiet-button" onClick={() => historyDialog.current.close()} aria-label="Close recent work">×</button></div>
      {runs.length ? <div className="history-list">{runs.map(run => <button key={run.id} className="history-item" onClick={() => select(run)}>
        <span className="history-type">{run.route.target ?? 'Brief'}</span><span className="history-copy"><span dir="auto">{run.prompt}</span><small>{new Date(run.created_at).toLocaleDateString()} · {run.status.replaceAll('_', ' ')}</small></span><span aria-hidden="true">↗</span>
      </button>)}</div> : <p className="empty-history">Your saved creations will appear here.</p>}
    </dialog>
  </div>;
}
createRoot(document.getElementById('root')).render(<App/>);
