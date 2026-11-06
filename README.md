# Promptelier

A local creative production workstation. **Phases 0–1 only.** Prompt routing, revision briefs, persistent history, supplied reference previews, and execution-log downloads are implemented. Card/video generation is deliberately not implemented. No API keys, cloud billing, or model downloads are required.

## Run locally (Windows PowerShell)

Prerequisites: Node.js 20.19+ or 22.12+ (tested with 24.20.0), Python 3.11+ (tested with 3.13). Keep the supplied `task material` folder in this project root. Do not publish that folder.

From the project root, first-time setup:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-lock.txt
cd frontend
npm.cmd ci
cd ..
```

Terminal 1, from project root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Terminal 2:

```powershell
cd frontend
npm.cmd run dev
```

Open http://127.0.0.1:5173. API documentation: http://127.0.0.1:8000/docs. Stop a server with Ctrl+C. `npm.cmd` avoids PowerShell's unsigned-script restriction without changing execution policy. No virtual-environment activation is necessary.

Optional configuration: `.env.example` documents `PROMPTELIER_DB`. Set it as a shell environment variable before starting the backend; the app does not automatically load `.env` files. Default SQLite storage is `data/promptelier.sqlite3`. Prompt history remains on your computer across restarts. The application has no authentication and binds to loopback; it is intended for local development.

## Verify

```powershell
.\.venv\Scripts\python.exe -m pytest backend -q -p no:cacheprovider --basetemp data/test-tmp
cd frontend
npm.cmd run build
npm.cmd run preview
```

Build preview also needs the backend running. `frontend/dist` is a production static build; its `/api` requests require a same-origin proxy if served outside Vite.

Actual checks on 6 November 2026: **13 backend tests passed** (12 routing cases plus an API integration test covering validation, revisions, persisted history after app recreation, allowlisted references, and log downloads). **Vite production build passed**, 23 modules transformed. npm reported **0 dependency vulnerabilities** at installation. The test environment emitted an httpx deprecation warning from Starlette and a Windows pytest cache-write warning; neither failed the tests. The default Windows pytest temp folder was inaccessible, so verification used a project-local temp folder.

Browser visual/interaction QA could not run: the browser host was unavailable, and native app inventory timed out. Responsive CSS and accessible labels/focus states are implemented but have not been visually verified here. Manually verify desktop and narrow-mobile layouts, keyboard navigation, history selection, and log expansion before treating Phase 1 visual QA as complete.

Manual walkthrough:

1. Click the Ramadan-card example and submit. Expect `card`, `not_implemented`, and no generated outputs.
2. Enter “Make the previous card blue instead of green.” Expect a revision linked to the previous brief. Expand the log and download its JSON record.
3. Choose New brief, enter “Make it blue.” Expect a clarification request because no parent is selected.
4. Submit the UGC example. Expect video routing with an explicit unavailable-production message.
5. Open Run history and select a saved run. Reload and confirm history persists. Asset library displays only labelled supplied references.
6. Stop FastAPI and submit a brief. Expect a clear request error. Restart it and retry.

## How the pieces connect

`frontend/src.jsx` owns prompt text, selected run, revision context, history, network status, and current view using React state. Submit sends `{prompt, parent_id}` to `/api/runs`. Vite proxies that path to FastAPI, keeping browser requests same-origin. FastAPI validates the request with Pydantic, loads the parent if present, calls the pure router, saves the result transactionally in SQLite, and returns a typed run. React renders that actual response without simulated progress or generation success.

`backend/router.py` checks explicit card/video words, revision signals, and ambiguity. Conflicting targets or missing context produce clarification. English and a small set of Arabic keywords are supported, not general multilingual understanding. Negation and complex instructions can be misclassified; this baseline deliberately avoids claiming LLM-level comprehension.

`parent_id` is an explicit link to a saved brief. Follow-ups preserve a chain of instructions for future tools to resolve. There are no generated assets to revise yet. The app makes no agent decisions in Phase 1.

| Endpoint | Purpose |
|---|---|
| GET /api/health | Router/backend readiness and truthful generation availability |
| POST /api/runs | Validate, classify, persist, return run |
| GET /api/runs | Persistent history, newest first |
| GET /api/runs/{id} | Inspect saved run |
| GET /api/runs/{id}/download | JSON execution record; not a production asset |
| GET /api/references/{name} | Two allowlisted supplied PNG references only |

Run statuses are `not_implemented` and `needs_clarification`. Network failures appear separately in the UI. Production-success states, output previews, validation reports, and asset-download endpoints belong to later phases; fabricating them now would hide missing work.

## Files and decisions to defend in an interview

- `ASSET_AUDIT.md`, private derived inventory/contact sheet, and `tools/audit_assets.py`: distinguish measured properties from assumptions. SHA-256 makes preservation checkable.
- `PROJECT_PLAN.md`: dependencies, acceptance criteria, review gate, and all future phases.
- `backend/main.py`: API, typed contracts, storage, allowlisted reference serving; SQLite avoids extra infrastructure for a single local workstation.
- `backend/router.py`, `backend/test_app.py`: pure decision logic can be tested independently of HTTP; API integration tests verify persistence and boundaries.
- `frontend/src.jsx`, `style.css`, `vite.config.js`: responsive navy/gold workstation and same-origin API integration. System fonts avoid external font requests.
- `backend/requirements-lock.txt`, `frontend/package-lock.json`: installed dependency snapshots for reproducibility. Range-based backend files separate runtime from development requirements.

Meaningful lessons: classification is separate from execution; a saved brief is not a generated asset; revision context should be explicit and durable; alpha metadata needs actual pixel checks; proprietary references must stay separate from source and generated exports.

Documentation consulted: [Vite server proxy](https://vite.dev/config/server-options#server-proxy), [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/).

## Privacy and next milestone

Original assets, private derived sheets/inventory, local database, and future outputs are ignored by Git. Private source repository: https://github.com/Shefaa-atef/promptelier. No cloud deployment was created. A future public portfolio needs original or appropriately licensed replacements; `.gitignore` alone cannot remove files already committed elsewhere.

Phase 2 has not started. Review this foundation, confirm Illustrator artboard/layer details and preview placement, then add structured card specifications and a validated procedural SVG/Pillow pipeline in small milestones. FFmpeg, Arabic TTS, presenter tools, and optional Ollama hardware evaluation come later.

Live HTTP verification also passed: UI, health and both reference routes returned 200 through Vite; card submission and linked revision returned 201 with truthful statuses. All 85 original file SHA-256 values remained unchanged (81 PNGs). Two smoke-test briefs are saved in local history.


