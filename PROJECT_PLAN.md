# Promptelier — final assessment status

Updated 6 November 2026. This file describes the current implementation; `docs/PHASE_2_PLAN.md` and the staged asset audit are historical records.

## Production evidence

- React → FastAPI → SQLite → one background worker is working through the actual website.
- DreamShaper 8 + ControlNet produced the final premium Ramadan and botanical artwork. Both framed designs, previews, and native-size icons were visually inspected. The botanical correction removes the unwanted lettering seen in its earlier candidate.
- Both designs export exactly `Source/b.png` 250×346, `cardPreview.png` 208×261, and `Symbols/cardIcon.png` 46×64, with transparency and supplied-frame preservation checks.
- A realistic fictional presenter, actual SadTalker mouth motion, Piper Arabic voice, supplied Baloot gameplay, captions, branding, and CTA are integrated into a 20.02-second vertical MP4. A rejected first composition exposed font glyphs and mixed-game footage; the final composition fixes both. Earlier outputs remain intact.
- The hook-only revision preserves presenter bytes and the gameplay/challenge/CTA scene bytes. SHA-256 proof and decisions are saved in validation and execution records.
- Original and revised videos played and downloaded through the browser. Card previews and ZIP downloads were exercised. ZIP responses now use attachment/no-store headers and a distinct download URL to avoid a stale browser request.
- `outputs/examples.json` identifies the final local examples. `outputs/submission-verification.json` contains HTTP/output/reuse/integrity evidence. All 85 supplied original hashes match.

## Cleanup and release

Video logic is separated into agent, audio, and rendering modules. Tests are under `tests/`; detailed documentation is under `docs/`. Runtime/model/vendor folders were not reorganized. A stable source checkpoint exists at `checkpoint-before-quality-upgrade-20261106` (7f620fc).

Final regression and source release results are recorded in `docs/IMPLEMENTATION_NOTES.md`. Source-only commit/push follows verification; generated assessment material stays ignored and local.

## Explicit limitations

No claim of professional acting, perfect phoneme alignment, native-speaker audio approval, exact Illustrator layer/pixel parity, or general autonomous reasoning is made. Presenter identity was provisioned manually once using a saved local AI portrait. The policy is symbolic; scripts are templated; video revisions support hooks. Fresh installation requires presenter provisioning. Automatic jobs do not resume after restart. See README and implementation notes for setup, fallback controls, licenses, and manual-work disclosure.
