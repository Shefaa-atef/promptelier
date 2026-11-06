import json
import os
import sqlite3
import threading
import logging
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from typing import Literal
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from backend.router import Route, route_prompt
from backend.cards.specification import Interpretation, RuleSpecificationProvider
from backend.cards.render import generate_card, DELIVERY
from backend.video import plan_video, run_agent
from backend.media_tools import prepare_card_art, choose_presenter_engine, image_model_ready

ROOT = Path(__file__).resolve().parents[1]


class RunRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=4000)
    parent_id: str | None = None


class Event(BaseModel):
    time: str
    stage: str
    message: str


class Run(BaseModel):
    id: str
    prompt: str
    parent_id: str | None
    created_at: str
    route: Route
    status: Literal['not_implemented', 'needs_clarification', 'specification_ready', 'processing', 'completed', 'failed']
    message: str
    outputs: list[str] = Field(default_factory=list)
    events: list[Event]
    design: Interpretation | None = None
    video_plan: dict | None = None
    generation: dict | None = None


def create_app(db_path: str | Path | None = None, output_root: str | Path | None = None) -> FastAPI:
    app = FastAPI(title='Promptelier', version='0.4.0')
    database = Path(db_path or os.getenv('PROMPTELIER_DB', str(ROOT / 'data/promptelier.sqlite3')))
    database.parent.mkdir(parents=True, exist_ok=True)
    outputs = Path(output_root or os.getenv('PROMPTELIER_OUTPUTS',str(ROOT/'outputs')))
    outputs.mkdir(parents=True,exist_ok=True)
    # One production worker keeps local CPU, SAPI and memory use predictable.
    worker_lock = threading.Lock()
    @contextmanager
    def connect():
        db = sqlite3.connect(database, timeout=30)
        try:
            db.execute('CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, body TEXT NOT NULL)')
            with db:
                yield db
        finally:
            db.close()
    with connect():
        pass

    def save_run(run):
        with connect() as db:
            db.execute('INSERT INTO runs VALUES (?,?) ON CONFLICT(id) DO UPDATE SET body=excluded.body',
                       (run.id,run.model_dump_json()))

    with connect() as db:
        for row in db.execute('SELECT body FROM runs').fetchall():
            interrupted=Run.model_validate_json(row[0])
            if interrupted.status=='processing':
                interrupted.status='failed'
                interrupted.message='Production was interrupted by a backend restart. Submit again to retry.'
                db.execute('UPDATE runs SET body=? WHERE id=?',(interrupted.model_dump_json(),interrupted.id))

    def get_run(run_id: str) -> Run:
        with connect() as db:
            row = db.execute('SELECT body FROM runs WHERE id=?', (run_id,)).fetchone()
        if not row:
            raise HTTPException(404, 'Run not found')
        return Run.model_validate_json(row[0])

    @app.get('/api/health')
    def health():
        return {'status': 'ok', 'phase': 4, 'milestone': 'local-production', 'router': 'rules', 'generation_available': True, 'card_specification_available': True,
                'agent':'symbolic inspect/choose/repair policy', 'video_presenter':choose_presenter_engine(),
                'card_ai_ready':image_model_ready()}

    def produce(run,parent):
        with worker_lock:
            def emit(stage,message):
                run.events.append(Event(time=datetime.now(timezone.utc).isoformat(),stage=stage,message=message))
                save_run(run)
            try:
                emit('production','Local worker started.')
                if run.design:
                    folder=outputs/run.id
                    artwork,run.generation=prepare_card_art(run,parent,folder,outputs/parent.id if parent else None,emit)
                    if artwork:
                        run.outputs=generate_card(run.design.specification,folder,artwork)
                        run.generation['description']='Local AI artwork: DreamShaper 8, with the official supplied card frame.'
                        run.outputs.append('artwork.png')
                    else:
                        run.outputs=generate_card(run.design.specification,folder)
                        run.generation['description']='Procedural fallback. '+run.generation['reason']
                    (folder/'generation.json').write_text(json.dumps(run.generation,indent=2,ensure_ascii=False),encoding='utf8')
                    run.outputs.append('generation.json')
                    emit('validation','Three PNGs decoded; exact names, dimensions, transparency and opaque frame preservation verified.')
                else:
                    previous=parent if run.route.intent=='revision' else None
                    run.outputs=run_agent(run.video_plan,outputs/run.id,emit,
                        outputs/previous.id if previous else None,previous.video_plan if previous else None)
                    run.generation=json.loads((outputs/run.id/'generation.json').read_text(encoding='utf8'))
                run.status='completed'
                run.message='Production complete. Actual files passed validation; previews and downloads are available.'
                emit('completed',run.message)
            except Exception as error:
                logging.exception('Production failed for %s',run.id)
                run.status='failed'; run.outputs=[]
                run.message=f'Production failed: {error}'
                emit('failed',run.message)
            save_run(run)

    @app.get('/api/runs', response_model=list[Run])
    def history():
        with connect() as db:
            return [Run.model_validate_json(r[0]) for r in db.execute('SELECT body FROM runs ORDER BY rowid DESC')]

    @app.get('/api/runs/{run_id}', response_model=Run)
    def detail(run_id: str):
        return get_run(run_id)

    @app.post('/api/runs', response_model=Run, status_code=201)
    def submit(request: RunRequest):
        prompt = request.prompt.strip()
        if not prompt:
            raise HTTPException(422, 'Prompt must contain text')
        parent = get_run(request.parent_id) if request.parent_id else None
        route = route_prompt(prompt, parent.route.target if parent else None)
        now = datetime.now(timezone.utc).isoformat()
        status = 'needs_clarification' if route.intent == 'clarification' else 'processing'
        message = route.reason if status == 'needs_clarification' else 'Local production queued.'
        design = None
        if route.target == 'card':
            if route.intent == 'revision' and (not parent or not parent.design):
                status = 'needs_clarification'
                message = 'This older brief has no design specification. Submit a new complete card brief first, then revise its saved specification.'
            else:
                previous = parent.design.specification if route.intent == 'revision' and parent and parent.design else None
                design = RuleSpecificationProvider().interpret(prompt, previous)
                status = 'processing'
                message = 'Specification saved. Local artwork generation and validation queued.'
        run = Run(id=str(uuid4()), prompt=prompt, parent_id=parent.id if parent else None,
                  created_at=now, route=route, status=status, message=message, design=design,
                  events=[Event(time=now, stage='received', message='Prompt accepted.'),
                          Event(time=now, stage='context', message=f'Parent: {parent.id}' if parent else 'New independent brief.'),
                          Event(time=now, stage='routing', message=route.reason),
                          Event(time=now, stage=status, message=message)])
        if design:
            run.events.insert(-1, Event(time=now, stage='specification', message=f'{design.provider}; changed fields: {", ".join(design.applied_fields) or "none"}.'))
            for warning in design.warnings:
                run.events.insert(-1, Event(time=now, stage='interpretation_warning', message=warning))
        if route.target=='video' and route.intent!='clarification':
            try:
                if route.intent=='revision' and (not parent or not parent.video_plan or parent.status!='completed'):
                    raise ValueError('Select a completed video before requesting a hook revision.')
                run.video_plan=plan_video(prompt,parent.video_plan if route.intent=='revision' else None)
                run.status='processing'; run.message='Local video agent queued. Inspect execution log for tool decisions.'
            except ValueError as error:
                run.status='needs_clarification'; run.message=str(error)
        save_run(run)
        if run.status=='processing':
            threading.Thread(target=produce,args=(run.model_copy(deep=True),parent),daemon=True).start()
        return run

    @app.get('/api/runs/{run_id}/files/{name:path}')
    def output_file(run_id: str,name: str):
        run=get_run(run_id)
        if run.status!='completed' or name not in run.outputs:
            raise HTTPException(404,'Validated output not found')
        relative=Path('delivery')/name if name in DELIVERY else Path(name)
        path=(outputs/run.id/relative).resolve()
        if not path.is_relative_to((outputs/run.id).resolve()) or not path.is_file():
            raise HTTPException(404,'Output not found')
        if name.endswith('.zip'):
            return FileResponse(path,filename=path.name,media_type='application/zip',content_disposition_type='attachment',headers={'Cache-Control':'no-store'})
        return FileResponse(path,filename=path.name,content_disposition_type='inline')

    # Deliberate allowlist: never expose the complete proprietary asset directory.
    references = {
        'premium': ROOT / 'task material/Cards Design-20261106T115436Z-1-001/Cards Design/b.png',
        'preview': ROOT / 'task material/cardPreview.png',
    }

    @app.get('/api/references/{name}')
    def reference(name: str):
        path = references.get(name)
        if path is None or not path.is_file():
            raise HTTPException(404, 'Reference not found')
        return FileResponse(path, media_type='image/png')

    @app.get('/api/runs/{run_id}/download')
    def download(run_id: str):
        run = get_run(run_id)
        # Download a truthful run record, never masquerade it as a production asset.
        from fastapi.responses import Response
        return Response(json.dumps(run.model_dump(), indent=2), media_type='application/json',
                        headers={'Content-Disposition': f'attachment; filename="run-{run.id}.json"'})
    return app


app = create_app()
