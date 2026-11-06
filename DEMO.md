# Five-minute Promptelier demo

Before the interview, follow README setup, start both servers, and run:

```powershell
.\.venv\Scripts\python.exe tools/generate_examples.py
```

This prepares real examples and downloads all output types. Their IDs are in `outputs/examples.json`; files are in `outputs/<id>/`. Reload the website afterward so history includes the prepared examples. Keep a file-browser window open at `outputs` for the preservation proof. Do not publish screenshots or output media containing proprietary material.

## 0:00–0:45 — Explain the architecture

“Promptelier runs on my computer. React is the browser interface. FastAPI is the Python service that validates requests and runs tools. SQLite is a small local database file that remembers briefs, revisions and logs. A background worker does the heavy work, while the interface reads its real progress.”

State the zero-cost choices: original procedural card drawing, FFmpeg video editing, local voices, and a deterministic symbolic video agent. No paid APIs or GPU models are involved.

## 0:45–1:45 — Card production

Choose the Ramadan card example and Create. Explain that a validated design specification describes palette and motifs; Pillow draws original artwork and overlays the official supplied frame. Show all three PNG previews and download `cards.zip`.

Open the ZIP and show exactly `Source/b.png` (250×346), `cardPreview.png` (208×261), and `Symbols/cardIcon.png` (46×64). Show the botanical example from Recent work to demonstrate a different focal motif and geometry, not just recoloring.

## 1:45–2:30 — Targeted card revision

Select a Ramadan result and submit `Change only the colors to purple and silver`. Explain that the immutable parent specification is copied and only palette fields are patched. Geometry and seed remain the same; the supplied premium frame remains gold because original frame pixels are preserved. Open the parent from Recent work to show it still exists unchanged.

## 2:30–3:30 — Real Arabic video

Select the prepared Arabic video. Play the actual 20-second MP4 with voice, fictional illustrated host, table gameplay, scene captions and CTA. Show `validation.json`: duration, 540×960 resolution, audio, H.264, checksum and full-decode validation.

Be candid: this is an illustrated local presenter with simple mouth animation. Arabic uses robotic eSpeak speech, not a neural voice or a real actor. The script is templated; arbitrary instructions are not interpreted.

## 3:30–4:30 — Agent and hook revision

Select the hook-revision result, or submit `Change only the opening hook to "جاهز لتحدي بلوت جديد؟"` with the video selected. Open Work details and its execution log and `decisions.json`.

Explain the decisions: inspect source; identify unmet scene goals; generate missing voice and inspect its duration; render/decode a scene; retry failure with a bounded budget; reuse matching verified parent clips; assemble only after scene goals pass. The revision generates one new hook and reuses gameplay/challenge/CTA scenes. Show `reused_scenes` in validation. Automated tests prove these scene bytes match their parent and prove injected-failure recovery.

“This is a symbolic goal-directed agent, not an LLM. Its choices depend on inspected state and failures rather than a prewritten list of unconditional tool calls. Its scope is deliberately small.”

## 4:30–5:00 — Verification and tradeoffs

Show the passing test result and explain the checks: invalid input, persistence, exact PNG contracts, download boundaries, decoded video, retry exhaustion, original-file integrity and targeted-revision reuse. All 85 supplied original file hashes remain unchanged.

Close with tradeoffs: one local worker keeps the project understandable; preset scripts and finite motifs limit creative breadth; future work could add better licensed voices, richer presenter animation and an optional local LLM behind the same validated tool contracts.

## If something fails live

Open the explicit failed run and its log; do not describe it as success. The prepared completed examples remain available. A backend restart marks interrupted jobs failed; resubmit rather than waiting for automatic resume. Keep the app bound to loopback and use one backend process.
