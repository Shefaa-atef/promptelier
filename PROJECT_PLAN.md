# Promptelier project plan

Scope agreed: complete Phases 0–1, then STOP for review. Phases 2–5 are roadmap only. All core work must run locally without paid APIs or billing.

## Architecture

React workstation → same-origin `/api` requests through Vite's development proxy → FastAPI validation → deterministic intent router → SQLite run record. Each run includes original prompt, classification, target, parent ID, UTC creation time, explicit status, outputs, and structured execution events. Parent chains preserve revision briefs without flattening or losing the original request. No local LLM is required for routing.

Future FastAPI dispatch will invoke card tools or the video planner. A design specification is structured creative data, distinct from image bytes. The future video agent must select tools from inspected state, with explicit retry limits and reasons; a fixed pipeline alone does not meet that requirement.

## Roadmap and acceptance criteria

| Phase | Status | Dependencies | Acceptance criteria |
|---|---|---|---|
| 0 Asset audit | Complete with documented manual checks | Supplied originals; local inspection tools | Recursive inventory; PNG dimensions and true alpha checked; reference/template distinctions; AI PDF inspection; manual instructions and missing-resource list; originals preserved. |
| 1 Foundation | Implemented; validation recorded in README | Python, Node, React, Vite, FastAPI, SQLite | One prompt and submit action; real router; explicit ambiguity; revision context; persistent history; errors and processing states; supplied reference preview; expandable execution log and run-record download; truthful unimplemented generation; passing tests and frontend build. |
| 2 Card pipeline | Not started; review gate | Phase 1; frame mask and preview placement confirmation; Pillow/SVG rasterizer | Structured specification; prompt-dependent original procedural art; two visibly different prompts including premium example; exact three-file contract; dimension, casing and integrity validation; natural-language revisions; production preview/download. |
| 3 UGC video | Not started | Phase 2 review; FFmpeg/ffprobe; voice and presenter feasibility | Real 15–30s vertical MP4; fictional presenter; coherent Arabic-option voice and captions; supplied gameplay/branding; real preview/download; declared creative limitations. |
| 4 Autonomous video agent | Not started | Reliable Phase 3 tools; optional local reasoning model after hardware assessment | Inspect/decide/tool loop, meaningful branching and bounded retries; original plus hook-only revision reusing presenter and unaffected scenes; logs and final validation. |
| 5 Submission | Not started | All production criteria met | Reproducible setup, dependency files, source, assets/videos/logs, architecture/cost/limitations notes, five-minute demo, private repository; no proprietary public assets. |

## Phase 1 implementation milestones

1. Audit supplied folders, alpha, page boxes, hashes, and visual references.
2. Implement pure routing function and typed FastAPI records. Store each run transactionally in local SQLite. Reject empty briefs and unknown parent references.
3. Build navy/gold responsive React studio, context reset, history and reference library. Show actual network progress; never fabricate render stages.
4. Test route cases and API validation/persistence. Build production frontend; smoke-test live proxy and inspect browser if available.

## Dependencies now versus later

Now: React/React DOM for UI; Vite for development and bundling; FastAPI/Pydantic for HTTP and typed validation; Uvicorn for serving; standard-library SQLite for durable local history; pytest/httpx for tests. Pillow and pypdf are audit-only tools, not required by the app. Exact installed versions are captured in lock/snapshot files.

Later: Pillow plus an SVG rasterizer for procedural artwork and alpha composition; FFmpeg/ffprobe for media editing and inspection; an evaluated free local Arabic TTS engine; optional Ollama after checking RAM/VRAM and acceptable model latency. No model or cloud API is required now. Avoid GPU-heavy model recommendations until actual hardware is inspected.

## Trade-offs and next review

Rules are transparent and testable but do not offer general language understanding. Ambiguous and unsupported prompts ask for clarification. Phase 1 context refers to saved briefs, not rendered assets. Runs are short synchronous route operations; long production tasks will need persisted job states and polling before introducing expensive generation. SQLite is suitable for one local studio, without authentication or microservices. Never expose this unauthenticated development app publicly.

Next step after Phase 1 review: confirm normal/premium artboard pairing and frame masks, then implement one independently testable card-specification milestone. Do not begin card artwork generation before review.

## Verification result
13 backend tests passed; Vite production build passed; live proxy/reference/submit/revision HTTP checks passed; all 85 original hashes unchanged. Browser host unavailable: visual and click-through QA remains pending manual review. No Phase 2 work started.

