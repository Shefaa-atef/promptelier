# Promptelier

A free local creative production studio: React + FastAPI + SQLite, original procedural card artwork, and 15–30-second vertical video advertisements with a fictional illustrated presenter, offline voice, gameplay, captions and CTA. Production runs asynchronously; the UI polls real persisted status and exposes files only after validation.

No paid APIs, cloud accounts, GPU, diffusion model or LLM is required. The video controller is a bounded symbolic agent that inspects state, chooses tools, validates results, reuses unaffected scenes and repairs failures. Its decision policy and script vocabulary are deliberately limited and inspectable.

## Run on Windows

Requires Python 3.11+ and Node.js 20.19+ or 22.12+. Tested here with Python 3.13 and Node 24. Keep the original private `task material` folder in the project root. Dependencies need an internet connection once; generation runs offline afterward.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-lock.txt
cd frontend
npm.cmd ci
cd ..
```

Terminal 1, project root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Terminal 2:

```powershell
cd frontend
npm.cmd run dev
```

Open http://127.0.0.1:5173. API documentation: http://127.0.0.1:8000/docs. Use one backend process. Restart it after Python changes; Vite reloads frontend changes automatically. Stop the server process before starting a replacement. In this Windows environment a terminal interrupt did not always terminate its child Python process.

Optional environment variables are documented in `.env.example`: `PROMPTELIER_DB` and `PROMPTELIER_OUTPUTS`. Set them in your shell; `.env` is not automatically loaded. Defaults are `data/promptelier.sqlite3` and `outputs/`. Paths are local to the machine. The app has no authentication: bind to loopback as shown.

## Generate and revise

- Click either card example, then **Generate asset**. A new run stores a validated design specification, renders artwork, composes official frames, validates exports and creates the ZIP.
- With the card selected, submit `Change only the colors to purple and silver`. Palette changes preserve specification geometry and seed; old files remain unchanged.
- Click the Arabic video example and generate. Choose 15–30 seconds in English, such as `Create a 20-second Arabic UGC video for VIP Baloot`. With no duration, the default is 20 seconds. English narration is also supported.
- With a completed video selected, submit `Change only the opening hook to "جاهز لتحدي بلوت جديد؟"`. Quotes supply exact hook text; without quotes the agent uses its alternative hook. The other three scene MP4s are reused after decoding and hash checks.
- Use **New brief** to clear revision context. Use **Run history** to select earlier results. Expand execution logs to see actual decisions and failures.

Card delivery ZIP contains exactly:

| Path | Dimensions |
|---|---|
| `Source/b.png` | 250 × 346 |
| `cardPreview.png` | 208 × 261 |
| `Symbols/cardIcon.png` | 46 × 64 |

The run folder also stores `specification.json` and `validation.json`. Videos deliver `video.mp4` (540 × 960, H.264/AAC, 24fps), `poster.png`, `plan.json`, `decisions.json`, and `validation.json`. Scene clips, speech WAVs and presenter frames remain private intermediates. Download the run log separately for the full timestamped execution record.

## Verify and reproduce examples

```powershell
.\.venv\Scripts\python.exe -m pytest backend -q -p no:cacheprovider --basetemp data/verification
cd frontend
npm.cmd run build
cd ..
.\.venv\Scripts\python.exe tools/generate_examples.py
```

The example command needs both servers running. It exercises the real HTTP application, generates two visually different cards, a palette revision, an Arabic video and a hook revision, checks every download, and saves IDs in ignored `outputs/examples.json`. Execution JSON is also saved beside those examples. Outputs and history persist locally across restarts. Interrupted runs become explicit failures at startup; submit again to retry. There is no automatic job resume.

Latest verification on 6 November 2026: 30 backend tests passed, including actual PNG/ZIP generation, video decoding, Arabic speech, injected encoder failure, retry exhaustion, and byte-identical unaffected scene reuse. Frontend production build passed. Desktop browser generation and reference/result rendering were checked; see `DEMO.md` and `IMPLEMENTATION_NOTES.md` for final verification and limitations. One upstream Starlette/httpx deprecation warning remains.

## Architecture

The browser sends a prompt and optional parent ID. FastAPI validates the request and stores a queued run in SQLite. A single local worker processes production while React polls saved history. The rule router selects card, video, revision or clarification.

For cards, the specification compiler selects supported colors, motifs and composition. Pillow draws original high-resolution geometry and downsamples it. A flood-fill mask distinguishes the official frame's enclosed center from transparent exterior. The frame is composited above the artwork; every opaque original frame pixel is checked. Separate preview and simplified-icon compositions produce the three delivery images. The validator checks the exact file tree, sizes, decoding, alpha and checksums before allowing downloads.

For videos, a planner prepares four scene goals. The agent inspects the supplied gameplay, then chooses between reusing a valid parent scene, synthesizing missing speech, rendering a scene, repairing a failure, and assembling validated scenes. English uses installed Windows SAPI voices; Arabic uses portable eSpeak NG. Pillow creates presenter and caption frames, including Arabic shaping and text direction. FFmpeg combines these with actual gameplay and voice. Final validation decodes the entire MP4 and checks duration, resolution, audio and codec. Failed work never gets a successful-output status.

Important files:

- `backend/main.py`: API contracts, persistence, worker, progress events, safe downloads.
- `backend/cards/specification.py`: supported prompt controls and scoped specification revisions.
- `backend/cards/render.py`: artwork, template masks, composition, PNG/ZIP validation.
- `backend/video.py`: video planning, offline speech, presenter/captions, FFmpeg tools, agent policy.
- `frontend/src.jsx` and `frontend/style.css`: submission, polling, previews, history and downloads.
- `backend/test_production.py`: actual output, recovery and reuse proofs.

## Honest limits and privacy

Cards are procedural illustrations, not diffusion-generated images. They use a finite motif vocabulary. Video scripts use preset Arabic/English copy plus quoted custom hooks; arbitrary product facts or creative instructions are not understood. The host is a simple original cartoon with looping mouth animation, not a photorealistic actor or phoneme-aligned lip sync. Arabic formant speech is intelligible synthetic output but robotic; it has not had a native-speaker quality review. Captions follow scene boundaries, not individual words. Preview placement recreates the supplied two-card layout; exact Illustrator vector/pixel parity is not claimed. Fine material, lighting and symmetry controls are only partially realized by this first renderer.

The agent is deterministic and goal-directed, not an LLM planner. It can choose reuse, generation, fallback from invalid reuse, and bounded retry; it cannot invent new tools or understand arbitrary editing requests. Video revisions currently support the opening hook only. One worker and local SQLite keep the code simple; this is a single-user workstation, not a multi-user hosted production service.

All supplied Tamatem material, generated media containing it, database records, inventories, contact sheets and browser captures are ignored by Git. The repository is private: https://github.com/Shefaa-atef/promptelier. No cloud deployment was created. Redistribution rights for supplied assets/font were not established; they stay on this machine.

Primary implementation references: [Pillow](https://pillow.readthedocs.io/), [FFmpeg](https://ffmpeg.org/ffmpeg.html), [imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg), [eSpeak NG API](https://github.com/espeak-ng/espeak-ng/blob/master/src/include/espeak-ng/speak_lib.h), [pyttsx3](https://pyttsx3.readthedocs.io/en/latest/engine.html). Dependency licenses remain with their upstream projects; no third-party binaries or model weights are vendored into the repository.
