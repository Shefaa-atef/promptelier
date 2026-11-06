import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from typing import Literal
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from backend.router import Route, route_prompt

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
    status: Literal['not_implemented', 'needs_clarification']
    message: str
    outputs: list[str] = Field(default_factory=list)
    events: list[Event]


def create_app(db_path: str | Path | None = None) -> FastAPI:
    app = FastAPI(title='Promptelier', version='0.1.0')
    database = Path(db_path or os.getenv('PROMPTELIER_DB', str(ROOT / 'data/promptelier.sqlite3')))
    database.parent.mkdir(parents=True, exist_ok=True)
    def connect():
        db = sqlite3.connect(database)
        db.execute('CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, body TEXT NOT NULL)')
        return db
    with connect():
        pass

    def get_run(run_id: str) -> Run:
        with connect() as db:
            row = db.execute('SELECT body FROM runs WHERE id=?', (run_id,)).fetchone()
        if not row:
            raise HTTPException(404, 'Run not found')
        return Run.model_validate_json(row[0])

    @app.get('/api/health')
    def health():
        return {'status': 'ok', 'phase': 1, 'router': 'rules', 'generation_available': False}

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
        status = 'needs_clarification' if route.intent == 'clarification' else 'not_implemented'
        message = route.reason if status == 'needs_clarification' else f'{route.target.title()} production is not implemented yet. Your brief and context are saved; no output was generated.'
        run = Run(id=str(uuid4()), prompt=prompt, parent_id=parent.id if parent else None,
                  created_at=now, route=route, status=status, message=message,
                  events=[Event(time=now, stage='received', message='Prompt accepted.'),
                          Event(time=now, stage='context', message=f'Parent: {parent.id}' if parent else 'New independent brief.'),
                          Event(time=now, stage='routing', message=route.reason),
                          Event(time=now, stage=status, message=message)])
        with connect() as db:
            db.execute('INSERT INTO runs VALUES (?,?)', (run.id, run.model_dump_json()))
        return run

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
