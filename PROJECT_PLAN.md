# Quality correction — reopened

The user rejected the initial artwork, presenter, and overloaded website. Functional tests did not establish acceptable creative quality. The earlier completion claims below describe file-level functionality only; media quality is not accepted.

Current corrections: replace the crowded dashboard with one prompt, one result, and primary downloads; move history and technical records behind explicit controls. Reassess image/video generation rather than presenting basic procedural drawings and a placeholder cartoon as finished creative work.

Hardware correction: nvidia-smi confirms an NVIDIA GTX 1660 SUPER with 6144 MiB VRAM. Earlier documentation saying no usable GPU was reported was an incorrect assessment.

---

# Promptelier project plan

Updated 6 November 2026. All work remains local and free. Core end-to-end delivery is implemented, with the explicit fallback limits below. The original Phase 2 plan is retained in `PHASE_2_PLAN.md` as historical acceptance guidance.

| Phase | Current result |
|---|---|
| 0 Asset audit | Completed inventory and alpha checks. Original 85-file hashes are the preservation baseline. |
| 1 Application | React, FastAPI, SQLite, routing, saved context/history, errors and execution-log downloads implemented. |
| 2 Card production | Original Pillow renderer, official normal/premium frames, exact three PNGs, ZIP, validation, previews and scoped revisions implemented. Two distinct designs visually inspected. Direct PNG rendering replaces the originally proposed SVG intermediary to reduce dependencies. |
| 3 Video production | Real local 15–30s 540×960 MP4 with supplied gameplay, fictional illustrated host, English/Arabic offline speech, captions and CTA implemented. Arabic uses portable eSpeak NG rather than a large neural model. |
| 4 Video agent | Bounded symbolic state-based policy chooses inspect, synthesize, render, reuse, repair and assemble. Actual injected-failure recovery and hook-only reuse tests pass. No LLM or general reasoning model is claimed. |
| 5 Submission | Setup, locks, tests, examples, interview notes and five-minute demo instructions implemented. Source release committed and pushed to the verified private GitHub repository. |

## Architecture and operational choices

React → same-origin Vite proxy → FastAPI validation/router → persisted SQLite run → single background worker → card renderer or video agent → validation → allowlisted output downloads. React polls actual stored state. Restarted production becomes an explicit failed run rather than falsely successful or permanently processing. The app is intended for one local backend process; long jobs are not resumed automatically.

Pillow renders high-resolution procedural card artwork and downsamples. Native frame offsets and alpha are preserved by exterior flood-fill masks and an opaque-frame equality check. Production ZIP entries have exact case and dimensions. Supplied king-of-clubs face is used in the preview. Icon artwork is simplified separately.

Video uses four scene goals and FFmpeg, provided by the imageio-ffmpeg wheel. The agent inspects the actual source duration and streams. Selected intervals show table play rather than earlier menu screens. It inspects voice duration and full scene decoding, adapts speech rate or encoder settings on retry, rejects invalid parent clips and regenerates them, and validates the assembled MP4. Unaffected clips are copied after verification; parent files are never overwritten.

## Verification

30 backend tests passed on 6 November 2026. They include real renderer outputs, strict ZIP validation, persistence/legacy compatibility, failure status and download boundaries, real Arabic video generation, an injected render fault, retry exhaustion, and hook revision preservation by SHA-256. Frontend production build passed. Browser card generation completed through the website. Final browser/mobile/output/integrity results are recorded in `IMPLEMENTATION_NOTES.md`.

## Remaining limitations and future work

- No photorealistic presenter, neural Arabic voice, diffusion model or LLM planner. The functional fallback is an original illustrated host, local formant Arabic speech and symbolic agent policy.
- Limited card vocabulary and video script templates; only quoted hook text is directly controllable in video. Video revisions support hooks only.
- Material/light/symmetry styling is simplified; reference-level decorative refinement and exact Illustrator preview pixel parity are not claimed.
- Arabic audio needs native-speaker quality review; visual/video frames can be inspected here, but auditory quality has not been independently rated.
- Optional neural voices, better presenter animation, exact vector template extraction, job resume, multi-user hosting and public redistribution review remain future work, not completed features.

## Release verification

Final backend suite: 30 passed in 89.13s; frontend build passed. Actual browser MP4 playback succeeded and advanced. Desktop and 390px mobile layouts were inspected; no horizontal overflow at 390px. Two cards and their palette revision plus Arabic video and hook revision are available in local history and `outputs/examples.json`. All advertised files were downloaded through the real HTTP routes. All 85 original hashes are unchanged. Source release `3296343` was committed and pushed to the verified private GitHub repository. Proprietary originals and derived media are excluded.
