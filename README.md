# Promptelier

A private, local creative studio for the Tamatem assessment. React sends briefs to FastAPI; SQLite remembers runs and revisions. One background worker generates and validates the media before exposing downloads.

The final examples contain two AI card designs and original/revised 20-second Arabic advertisements with a realistic fictional talking presenter. Actual browser generation, previews, playback, and downloads were exercised. See [implementation evidence](docs/IMPLEMENTATION_NOTES.md), [demo](docs/DEMO.md), and [project status](PROJECT_PLAN.md).

## Run this installed workstation

From the project root, in two PowerShell terminals:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8002
```

```powershell
cd frontend
npm.cmd run dev
```

Open **http://127.0.0.1:5173**. Choose **Recent work** to open prepared outputs; reloading starts with an empty composer, not an automatic generation. The frontend proxies `/api` to port 8002. `PROMPTELIER_BACKEND_URL` can override this when starting Vite. Port 8002 avoids the older development servers on this workstation.

No additional installation is needed here. Keep the existing environments and models. Close unused applications before heavy generation; approximately 8 GB free system RAM is a practical target. Jobs run serially. Never start two backend workers against the same database.

## Fresh environment setup

Tested on Windows, Python 3.13, Node 22, GTX 1660 SUPER 6 GB, NVIDIA driver 610.88. Use Python 3.13 for the supplied locks. Put the supplied private originals under `task material/`, preserving their directory names.

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-lock.txt
cd frontend
npm.cmd ci
cd ..
py -3.13 -m venv .venv-media
.\.venv-media\Scripts\python.exe -m pip install torch==2.8.0 torchvision==0.23.0 --index-url https://download.pytorch.org/whl/cu126
.\.venv-media\Scripts\python.exe -m pip install -r backend/requirements-media.txt
.\.venv\Scripts\python.exe tools/download_media_models.py --kind all
```

The optional media environment isolates PyTorch from the web server. Model downloads are several GB and require internet once; generation uses local files, with no API keys or paid service. The downloader pins revisions and records hashes. `requirements-media-lock.txt` records the tested environment; install CUDA wheels from the official index above rather than the default CPU index.

A fresh installation must also create its fictional portrait and verify a SadTalker talking sample before enabling presenter auto mode. This workstation already has both under ignored `models/presenter/`. See implementation notes for this manual provisioning limitation; the downloader alone does not reproduce that identity.

## What generates the media

- **Cards:** DreamShaper 8 generates 512×704 artwork. ControlNet Canny guides crescent/crown outlines. Pillow fits the artwork beneath the supplied frame and assembles the exact PNG exports. The original procedural renderer remains available.
- **Video:** DreamShaper created the saved fictional portrait once. Piper produces Arabic speech. SadTalker animates that same portrait from each speech clip. FFmpeg combines it with inspected Baloot footage, Arabic captions, logo, and CTA.
- **Agent:** a bounded symbolic policy chooses missing speech, animation, scene rendering, inspected reuse, repair, or assembly. It is not an LLM. Hooks can be revised while other encoded scenes remain byte-identical.

Every card ZIP contains exactly:

| Path | Size |
|---|---|
| `Source/b.png` | 250×346 |
| `cardPreview.png` | 208×261 |
| `Symbols/cardIcon.png` | 46×64 |

Video delivery is 540×960 H.264/AAC, 24fps, approximately 20.02 seconds. Logs and validation JSON are downloadable under **Work details**. Each run has a private folder under `outputs/<run-id>/`; detailed model stdout is retained there too.

## Verify

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider --basetemp data/verification
cd frontend
npm.cmd run build
cd ..
.\.venv\Scripts\python.exe tools/verify_submission.py
```

`outputs/examples.json` identifies the final local examples. The verifier downloads every advertised file, compares bytes, checks PNG/ZIP contracts, fully decodes both videos, proves hook-only reuse and parent preservation, and checks all 85 original hashes. `tools/generate_examples.py` can create fresh examples through HTTP; it takes time and is not part of the five-minute demo.

## Structure and limits

`backend/main.py` owns the API and persistence; `backend/cards/` owns card specifications and exports. `backend/video.py` owns the agent, `video_audio.py` speech, and `video_render.py` composition. `media_tools.py` launches optional GPU workers. `frontend/`, `tests/`, `tools/`, and `docs/` contain the interface, tests, utilities, and documentation respectively. Models, vendor code, environments, database, original assets, and generated outputs are local ignored folders.

The presenter is a realistic animated portrait with approximate lip synchronization, not a filmed actor or full-body performance. Arabic speech needs human listening review. Captions follow scenes, not individual words. Scripts and routing are limited rules/templates; arbitrary instructions are not fully understood. Local AI can produce artifacts or safety-classifier false positives. The native 512px animation has no GFPGAN restoration. Slow GPU generation and one local worker are deliberate constraints.

All API/model usage costs are **$0**; local electricity, disk, and download bandwidth are still required. Model licenses and voice/dataset terms are separate: see implementation notes. Tamatem assets, derived outputs, databases, weights, and browser captures remain private and excluded from Git. This is a local workstation app, not a public multi-user service.
