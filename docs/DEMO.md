# Five-minute assessment demonstration

Start the two servers using [README](../README.md). Open http://127.0.0.1:5173 and **Recent work**. Use the prepared examples; uncached local generation takes longer than five minutes. `outputs/examples.json` contains the authoritative IDs.

## 0:00–0:40 — Architecture

“React is the interface. FastAPI is the Python service. SQLite is a local file that remembers requests and logs. One background worker calls the media tools, validates their real outputs, and reports progress to the browser.”

All models and editing tools run locally. No paid API is used.

## 0:40–1:40 — Two cards

Open the premium midnight-blue Ramadan brief, ID `10246029-0aef-4465-9866-4d2ccf9a9c7f`. Show Card, Store preview, and Icon; download the ZIP. Open it and show the exact three paths and dimensions.

Open the premium emerald botanical brief, ID `d2f9deaf-ba58-45dc-98fe-cd4e887fef9d`. Show its crown/leaf design. Explain: DreamShaper makes the artwork; ControlNet guides the focal silhouette; Pillow adds the original official frame and assembles the required exports. The outline guide is not being presented as finished AI artwork.

## 1:40–2:25 — Original advertisement

Open video ID `c2f0c73f-9b26-4be5-bd45-c4b63a46ddaf` and play the complete 20-second advertisement. Show the realistic fictional presenter, Arabic speech/captions, actual Baloot footage, branding and CTA. Download the MP4.

“The presenter is a generated portrait animated with SadTalker from Piper speech. It is a real talking-head animation, but it is not filmed acting and its lip synchronization is approximate.”

## 2:25–3:30 — Targeted revision

Open ID `7b98f575-dbda-4ab7-aea2-278ffb194ea1`: `Change only the opening hook to “جاهز لتحدي بلوت جديد؟”`. Play its opening, then show Work details → validation.json and the execution log.

The hook hash differs. Gameplay, challenge and CTA hashes match their parent. The presenter SHA-256 matches too. The original output remains unchanged. The prepared verification report includes both sides of every comparison.

## 3:30–4:25 — Agent decisions

Show decisions.json. Explain that the policy looks at missing or invalid work: synthesize speech, inspect duration, adjust rate if it does not fit, animate missing talking clips, render/decode scenes, reuse matching parent clips, and assemble only after inspections pass. In the original run, gameplay speech exceeded six seconds; recorded retries increased the speech rate before animation.

“This is a bounded symbolic agent with meaningful state-dependent choices and repair. It is not an LLM or a system that can invent new tools.”

## 4:25–5:00 — Verification and limits

Show the final test/build results and `outputs/submission-verification.json`. Mention exact PNG/ZIP validation, complete MP4 decoding, HTTP byte equality, parent preservation and 85 unchanged originals. Explain that generated media and proprietary assets stay local and out of Git.

Disclose human review needs: listen to Arabic speech; assess acting/lip synchronization and final creative suitability. No paid service or undisclosed manual animation was used. Generation is slow, so prepared examples are intentional.

For a live request, start a fresh card brief and show its real progress, then return to a prepared result. Do not promise completion during the demo. If a run fails, show its error/log; do not call it successful.
