# Implementation, evidence, and disclosure

## Architecture and important files

`backend/main.py` validates requests, routes briefs, persists SQLite records, runs one worker, and serves allowlisted validated files. React polls those records. A restart marks interrupted production failed rather than claiming success. Use one backend process and loopback addresses; there is no multi-user hosting or job resumption.

`backend/cards/specification.py` is a readable rule-based specification compiler. `backend/media_tools.py` passes the original brief and composition settings to the isolated worker `backend/ai_media.py`. DreamShaper generates the actual bitmap; a Canny ControlNet input guides the crescent/crown geometry. The guide is a simple outline input, not the delivered art. `backend/cards/render.py` fits neural art beneath the native official frame, composes the preview with the supplied king face, and validates the exact delivery tree, dimensions, alpha and opaque frame pixels. Palette revisions change saved artwork colors without redrawing its geometry. The original Pillow renderer remains available.

`backend/video.py` contains planning and the symbolic inspect/choose/repair loop. `video_audio.py` owns speech and its cache. `video_render.py` owns FFmpeg inspection, captions and composition. `animate_presenter.py` launches pinned upstream SadTalker with small Python 3.13/NumPy 2 compatibility fixes. It does not install or claim a face enhancer. The compatibility layer uses base Arabic isolated glyphs supported by the supplied Alexandria font, avoiding missing-glyph boxes.

The agent chooses according to inspected state, not an unconditional sequence: validated parent scenes can be copied; rejected reuse triggers regeneration; speech duration failures change rate; unavailable or invalid outputs consume a bounded retry budget; assembly requires all scene goals. The policy has no LLM, semantic critic, or general planning ability. Animation retries use separate directories, and cached clips must pass decoding before reuse/storage.

## Models and actual hardware

| Component | Actual local implementation | Terms / reference |
|---|---|---|
| Card art and saved presenter portrait | DreamShaper 8, revision a7e52b98680b1ba8ff7bce97c7f9f2e2e5337917 | [Model card, OpenRAIL-M](https://huggingface.co/Lykon/dreamshaper-8) |
| Composition guide | ControlNet Canny SD1.5, revision 115a470d547982438f70198e353a921996e2e819 | [Model card, OpenRAIL](https://huggingface.co/lllyasviel/control_v11p_sd15_canny) |
| Talking presenter | SadTalker code cd4c0465ae0b54a6f85af57f5c65fec9fe23e7f8; native 512 checkpoint and mapping weights | [Official source and license/exceptions](https://github.com/OpenTalker/SadTalker) |
| Arabic speech | Piper 1.8.0, ar_JO-kareem-medium | [Piper GPL-3.0](https://github.com/OHF-Voice/piper1-gpl), [voice model/dataset terms](https://huggingface.co/rhasspy/piper-voices/blob/main/ar/ar_JO/kareem/medium/MODEL_CARD) |
| Assembly | Pillow, FFmpeg from imageio-ffmpeg | [FFmpeg](https://ffmpeg.org/ffmpeg.html) |

Voice model terms point to dataset provenance; GPL code licensing does not establish blanket commercial rights to the voice dataset. Review upstream terms and supplied-asset/font rights before public redistribution. No proprietary originals, generated branded media, model weights, or third-party binaries are committed.

The GTX 1660 SUPER has 6144 MiB VRAM. PyTorch 2.8.0+cu126 and an actual CUDA operation were verified. Float16 sampling produced non-finite latents on this card; float32 with layer-level CPU offload is the working profile. Guided image jobs used about 2417 MiB peak allocated VRAM, 512×704 pixels, 28 DPM++ 2M Karras steps, guidance 7.5. This also needs system RAM; roughly 8 GB free is a practical target. Full-model offload and a stalled earlier installation were not repeatedly retried. No additional model was introduced during final assessment delivery.

Uncached talking animation for the initial full advertisement took roughly ten minutes on this workstation; cached recomposition took under a minute. The hook revision took roughly two minutes. Individual guided cards took a few minutes including cold imports/loading; warm sampling was about 1–1.5 minutes. These are measurements, not latency guarantees.

## Actual output verification

Final run IDs are in ignored `outputs/examples.json`; prepared material is local under `outputs/`. The final original and hook revision are approximately 20.02s, 540×960, H.264/AAC, 24fps. Both were submitted, previewed and downloaded through the website. Playback advanced to completion without an error for the revised video. Downloaded MP4 bytes matched the originals. Frames from all four scenes were visually inspected, including changed mouth positions. Audio has real signal (original mean volume -22.1 dB, peak -4.3 dB); this is not a listening review.

The first full composition exposed missing Arabic glyphs and accidentally selected a different game from the multi-game source. It was retained as a diagnostic. The final composition uses inspected Baloot intervals 118, 124, 130 and 136 seconds and corrected glyph shaping. The final botanical prompt/negative prompt removed the earlier unwanted lettering. Both actual-size cards, previews and icons were inspected. Quality is substantially richer than the old procedural examples; professional creative approval is not inferred from passing tests.

The hook revision uses the same presenter image SHA-256. Only hook.mp4 changes; gameplay.mp4, challenge.mp4 and cta.mp4 are byte-identical. Parent final-video and scene checksums still match their completion records. Validation JSON includes scene hashes; execution logs include inspected reuse decisions. All 85 original supplied file hashes are unchanged.

`tools/verify_submission.py` downloads all listed outputs, compares them with disk files, validates exact PNG/ZIP structure, fully decodes both MP4s, checks reuse/parent preservation, and checks original integrity. ZIP responses use explicit attachment/no-store headers; a separate download URL avoids the stale browser request observed during testing. Browser ZIP download succeeded after that fix.

Final regression/build results are appended below after execution. GPU examples are separate from the deterministic test suite; tests do not pretend to re-run heavy AI inference.

## Fallbacks and manual-work disclosure

Set environment variables before starting the backend (the .env.example file is illustrative, not auto-loaded):

- `PROMPTELIER_CARD_ENGINE=procedural` keeps the original card renderer; `diffusion` requires the installed model; `auto` uses diffusion when installed.
- `PROMPTELIER_PRESENTER_ENGINE=voiceover` produces actual gameplay and speech without a talking person. `legacy` keeps the old cartoon for compatibility; it is not used for the final examples. `sadtalker` explicitly requires local presenter components. `auto` requires the saved talking verification marker before choosing it.
- `PROMPTELIER_VOICE_ENGINE=legacy` retains eSpeak Arabic / Windows SAPI English. Arabic auto mode uses installed Piper.

Ordinary run failures are visible; a failed SadTalker job is not silently relabeled as a realistic presenter. Explicit voiceover is the honest fallback. Generation logs stay under each run folder.

The fictional identity was manually provisioned once by selecting an inspected DreamShaper portrait (seed 82041), copying it to `models/presenter/nour.png`, and recording its identity/hash. A decoded/visually reviewed SadTalker sample established `talking-verified.json`. Downloads do not recreate these two provisioning steps automatically. This workstation already contains them. Future installations can copy the private provisioned portrait/metadata or generate and inspect a new fictional identity with the existing worker. No manual lip animation, external actor, paid API, or photo of a real person was used.

Captions are scene-level, not word-timed. Mouth motion is audio-driven and approximate; the actor's appearance is realistic but motion can be restrained/soft. The final Arabic speech still needs native-speaker listening approval. The optional GFPGAN enhancer is excluded because its legacy BasicSR installation failed on Python 3.13. Card symmetry and prompt compliance are not guaranteed; model safety filtering remains enabled and can reject benign ornament. Exact Illustrator layers/preview pixel parity are unverified. These are disclosed limitations, not hidden completed features.

## Final checks — 6 November 2026

After restructuring: 34 backend tests passed in 101.34 seconds. The frontend production build passed (23 modules). The HTTP submission verifier passed for both final cards and both final videos, including exact ZIP entries, all download bytes, complete video decoding, scene/presenter reuse, parent preservation, and 85 unchanged originals. Two upstream deprecation warnings remain (Starlette/httpx and Pillow getdata); they do not affect these outputs. The final private source release follows the secret/proprietary-content check.
