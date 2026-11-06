# Implementation notes and interview defense

## What the application delivers

A local React/FastAPI workstation creates original procedural card backs and real vertical video ads without paid services. The chosen fallback is CPU-only: Pillow for drawings, FFmpeg for encoding, Windows SAPI for English speech, portable eSpeak NG for Arabic speech, and a small symbolic agent for production decisions.

React handles prompts, revision context, status polling, saved history and actual media previews/downloads. FastAPI validates and stores each run, then queues a local thread behind one worker lock. SQLite stores JSON records and events. Small jobs do not need an external queue, Redis or a second database. Connections are explicitly closed after each transaction. Long work has persisted processing/completed/failed states; after a process restart unfinished work is marked failed.

## Card implementation

`backend/cards/specification.py` is a deterministic prompt compiler, with validated immutable Pydantic data structures. Revisions clone a parent's data and validate the patched result. A color-only request changes palette fields, while preserving seed and geometry. Parent files are never edited.

`backend/cards/render.py` creates artwork at 4× resolution. Explicit motif geometry creates a crescent, crown, leaves, vines or rosette. Restrained gradients/texture, borders and ornament provide a coherent shared layout. The botanical leaf shapes were changed from angular polygons to curved leaves after inspecting actual output. A separate simplified icon omits dense background detail.

The official frame is not replaced with a generic rounded rectangle. Flood filling identifies exterior transparent pixels, leaving the enclosed center as the artwork safe region. The original native frame pixels are then overlaid, including their asymmetric offsets. Opaque frame pixels must match exactly. The king-of-clubs source is composed behind the new back for the store preview.

Strict validation enforces the exact three-case-sensitive-path delivery tree, dimensions, RGBA PNG decoding, transparent/opaque alpha extrema and SHA-256 hashes. The ZIP contains those three images only; validation/specification intermediates stay outside it. No download is exposed until the run succeeds. Unexpected or missing outputs yield 404s.

## Video implementation and agent boundaries

`backend/video.py` plans four goals: hook, gameplay, challenge and CTA. Each has text, duration and a source offset. Original source inspection measured 247.32s, 890×1914, H.264 at 60fps with no audio. Actual table-play intervals around 120/220 seconds were selected after frame inspection; early menus were rejected.

The controller inspects state on every loop and chooses a tool. If a matching parent scene exists, it tries verified byte-preserving reuse. If that media is invalid it rejects reuse and generates the scene. Missing speech selects synthesis; decoded speech duration must fit the scene, otherwise a faster-rate retry is chosen. Verified speech allows rendering, with a faster encoder retry after failures. Rendering is followed by full decoding and scene duration/audio checks. Three failed attempts for one goal or the overall step budget stops production. Four satisfied scene goals allow assembly and final validation. This is a bounded reactive symbolic agent, not a general autonomous LLM or a claim of creative reasoning.

English speech runs in an isolated Windows SAPI process so a blocked voice cannot block the server indefinitely. Arabic uses the portable eSpeak C API with synchronous audio callbacks to a WAV; no system Arabic voice installation is needed. Caption shaping joins Arabic characters and orders text right-to-left because this Windows Pillow build lacks Raqm text layout. A fictional illustrated host has two mouth poses. FFmpeg composites host/captions, actual gameplay and speech, then encodes H.264/AAC MP4 with browser-friendly faststart metadata.

Hook revisions copy the validated parent plan and replace only hook text. Other three scene definitions must remain identical. Clips are decoded before reuse and copied bytes are checked by hash. A final report lists reused scenes. Parent clips and final video stay untouched.

## Verified on 6 November 2026

- Backend suite: 30 passing tests, including real card output and real Arabic video generation, injected render failure/repair, retry budget exhaustion, persistence and legacy records, download boundaries, strict ZIP contents, repeatable card rendering and unchanged alpha geometry on recolor.
- Frontend: Vite production build passed, 23 modules transformed.
- Real HTTP examples: two distinct cards, a color revision, a 20-second Arabic video and a hook revision completed, with every advertised output downloaded successfully. `outputs/examples.json` identifies them locally; `execution.json` is saved beside each example.
- The live hook revision's gameplay, challenge and CTA clips are byte-for-byte identical to their parent; its hook bytes differ. Final MP4: 20.02s, 540×960, audio present, H.264, successful full decode.
- Browser checks through Playwright: card example generation, color revision, result/specification display, ZIP link, execution-log expansion, history selection and video preview were exercised. Desktop and 390px mobile screenshots were inspected. Final media playback and layout details are recorded below after final checks.
- All 85 original asset SHA-256 hashes were rechecked and remain unchanged. Originals are never written by production tools. Git excludes original material, all generated media, local database, inventories and browser captures.
- One upstream Starlette/httpx deprecation warning remains; it does not fail tests.

## Deliberate limitations

There is no diffusion model, photorealistic or neural talking head, word-level lip synchronization, or LLM scriptwriter. Arabic speech is robotic; no native-speaker auditory quality review has been completed. Captions are scene-aligned. Card motifs/script language are limited; video supports requested duration/language and quoted custom hooks. Other free-form video instructions are not interpreted. Unknown card details produce compiler warnings.

The initial renderer does not fully realize all schema-level lighting/material/symmetry controls. Store-preview placement follows the supplied visual layout but is not certified pixel-identical to Illustrator vectors. The original premium frame remains gold even for a silver artwork palette. Large-model hardware suitability is not established: about 25.6GB RAM was detected and the GPU inventory returned no usable adapter, so this delivery uses portable CPU tools.

This is a single-user local app with one backend process. Jobs cannot resume after a crash, no cancellation UI exists, media retention is manual, and authentication/multi-user hosting are out of scope. Proprietary assets and font remain local; public redistribution rights are unverified. Keep the GitHub repository private.

## Useful interview answers

**Why use rules instead of an LLM?** They are free, repeatable and easy to explain. They provide a reliable baseline with explicit vocabulary limits. The existing validated specification interface can accept a future local model without letting unvalidated model output bypass file contracts.

**Why is the video controller an agent?** It observes tool results, tracks unmet goals, selects among generation/reuse/repair tools, and can change its next action after failure. It has explicit budgets and a final success test. It is a small symbolic agent; it is not general reasoning intelligence.

**Why keep validation separate from rendering?** A tool can finish without producing the right deliverable. File structure, PNG alpha, clip decoding and final duration/audio must independently pass before success/downloads are exposed.

**How do revisions preserve work?** Each run gets a new directory and explicit parent ID. Palette revisions preserve geometry in validated data. Hook revisions regenerate one scene and copy verified unchanged clips, rather than rendering the entire video again.

**What would you improve next?** Better licensed Arabic voice and presenter animation, full renderer support for material/light controls, exact vector preview extraction, then optional local-model interpretation. Operational improvements would be resumable jobs and media cleanup; distributed services are unnecessary for one workstation.

## Final browser and release checks

Browser playback succeeded: readyState 4, paused=false, 20.02322s, decoded 540×960, and playback time advanced. At a 390px viewport, document width was also 390px: no horizontal overflow. Desktop and mobile views were captured and visually inspected. Card ZIP clicking initiated the download. Final backend verification passed all 30 tests in 89.13s; final frontend build passed. The private GitHub repository was verified through its API using the existing Git credentials; the connected GitHub app did not have access to this repository, so release uses the existing Git remote.

Source release `3296343` was pushed successfully to private `Shefaa-atef/promptelier` on `main`. Documentation release details follow in Git history.
