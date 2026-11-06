# Promptelier — asset audit

Audited 6 November 2026. Originals remain unchanged under `task material/`. No working copies are needed in Phase 1. `asset_inventory.json` records every file, byte count, SHA-256, and PNG dimensions/mode/alpha. `asset_contact_sheet.png` is a derived visual inspection sheet; both contain proprietary information and are ignored by Git.

## Supplied folder contents

| Original folder/file | Findings | Intended use |
|---|---|---|
| Card Frames-20261106T115438Z-1-001/Card Frames | 2 RGBA PNGs, 250 × 346: Cardback-n1.png (white), Cardback-p2.png (gold). Both have actual transparent pixels, alpha extrema 0–255. | Preserve as official normal/premium overlays. |
| Cards Design-20261106T115436Z-1-001/Cards Design | 15 RGBA PNGs: b.png and b (1).png through b (14).png; all 250 × 346 with actual transparent pixels. | Flattened visual references; not editable vector templates. |
| source-20261106T115624Z-1-001/source | 52 card faces and b.png, all 250 × 346. Faces use palette mode with transparency; b.png is RGBA. | Supplied faces for preview composition; convert copies to RGBA before assembly. |
| symbols-20261106T115628Z-1-001/symbols | cardIcon.png: 46 × 64 RGBA. Four suit PNGs at 200 × 200 and four _small PNGs at 70 × 70, palette mode with transparency. | Icon reference and reusable suit elements. |
| Game Brand-20261106T115439Z-1-001/Game Brand | Logo.png: 1080 × 1080 RGBA with actual transparency; Alexandria-Medium.ttf (172,796 bytes); Gameplay.mp4 (271,800,605 bytes); End Card.webm (629,286 bytes). | Branding, font, future gameplay and end-card video sources. |
| cardPreview.png | 208 × 261 RGBA, actual transparency. Visual inspection shows overlapping decorative back and king face. | Store-composition reference, not a blank template. |
| Cardback Tamplate.ai | 9,754,685 bytes, PDF 1.6 compatible, Illustrator 30.2 metadata; six readable pages with boxes 250 × 346, 208 × 261, 46 × 64 repeated twice. | Candidate editable source; PDF parsing does not prove Illustrator layers are editable. |

## Naming and integrity

Faces use rank plus suit: 2–9, t, j, q, k, a plus c/d/h/s. `source/b.png` is byte-identical to `Cards Design/b (4).png`. Original directory names use lowercase `source` and `symbols`; the required delivery names use uppercase `Source` and `Symbols`. Future validation must enforce exact casing even though Windows is case-insensitive.

All 81 supplied PNGs decoded successfully with Pillow. Alpha checks used RGBA conversion, so palette transparency was checked too. Refer to the inventory for per-file pixel counts. PNGs are raster assets: resizing or changing a filename cannot recover layers.

## Illustrator inspection still required

Open `task material/Cardback Tamplate.ai` in Illustrator. Inspect all six artboards, their names, pixel dimensions, and normal/premium pairing. Open Layers and Links: check which objects are vectors, which are embedded/linked rasters, clipping masks, missing links, font substitution, and frame placement. Confirm whether the card background and frame can be selected independently. Export each artboard as a transparent PNG at 1× using the artboard bounds, to a NEW working directory. Confirm 250 × 346 / 208 × 261 / 46 × 64 exports; do not save over the original. Export a working SVG of reusable vector geometry only if needed. No Adobe purchase is required for the baseline PNG workflow.

## Pipeline and constraints

Future flow: prompt → structured design specification → original procedural SVG → raster artwork → alpha composition beneath the supplied frame → store preview using supplied face → simplified icon → strict validation → versioned download folder. The frame has a transparent center, so artwork needs an explicit mask and safe region. Rounded corners must stay transparent; inspect edges after compositing. Use supersampling for clean small exports. Never present a supplied reference as generated artwork.

Delivery contract: `Source/b.png` 250 × 346 PNG; `cardPreview.png` 208 × 261 PNG; `Symbols/cardIcon.png` 46 × 64 PNG. Validate exact filenames, dimensions, decoding, alpha expectations, and complete directory structure.

## Missing or unverified resources

- FFmpeg/ffprobe not found on PATH: gameplay duration, dimensions, codecs, audio, and WebM transparency remain unverified. Inspect these before Phase 3 editing.
- No presenter, Arabic voice model, approved script, font license, or redistribution license was supplied. Keep supplied material private; establish rights before any public portfolio release.
- No editable-layer verification or exact preview positioning measurements yet. PDF page sizes match required outputs, but do not establish layer structure.
- Local image/video model hardware suitability is unassessed. No model downloads or cloud integrations are needed for Phase 1.

Audit tooling uses existing local Pillow and pypdf. Optional reproducibility dependencies: `python -m pip install Pillow pypdf`; then `python tools/audit_assets.py`. The tool writes only derived inventory and contact sheet, and never modifies originals.

## Phase 2 reinspection (6 November 2026)

Both original frames were viewed on a contrasting background with the default back, a supplied king face, preview, and icon. Alpha bounds use Pillow's exclusive right/bottom coordinates: normal `(1,5,242,344)`, premium `(1,6,242,345)`. Centers are fully transparent. They are not centered generic rounded rectangles; native offsets must be preserved during assembly. Default back bounds `(0,5,242,344)`; preview bounds `(0,25,208,242)`.

No separately named **Default Deck** was found recursively. The 52 faces plus `source/b.png` are the working default-deck candidate, not a confirmed alternative asset package. Store preview visibly uses a king of clubs; use the matching original `source/kc.png` when resolving exact preview placement in 2.3. The inspection sheet also includes `ks.png` as a card-face transparency example, not the claimed preview face.

PDF-level inspection of the original AI found image XObjects on every page (counts 1/3/1/1/5/3) plus actual vector path commands. The preview pages contain king text. This establishes mixed vector/raster PDF content, not editability of Adobe layers. Exact placement and normal/premium artboard pairing will be resolved during template assembly. No manual Illustrator export is required for 2.1. Original exports and templates were not modified.

## Production implementation update — 6 November 2026

Original assets remain private and read-only. The production renderer uses native normal/premium frame PNGs, flood-fills only the exterior, fills the enclosed center, and verifies every opaque frame pixel after composition. Preview assembly uses the original `kc.png`; 208×261 placement recreates the supplied overlapping-card layout, without claiming exact Illustrator vector/pixel equivalence. Export dimensions/casing and alpha are validated automatically. No manual Illustrator export was needed for this local PNG workflow.

FFmpeg is now available through the local imageio-ffmpeg wheel. Actual supplied gameplay: 247.32 seconds, 890×1914 H.264, 60fps, no audio stream. Inspection of samples at 10/40/80/120/180/220 seconds identified menus/ads in earlier intervals and visible table play near 120 and 220 seconds; production selects table-play intervals. The supplied WebM end card is not used; a local branded CTA is generated with the original logo.

Arabic speech is generated with portable eSpeak NG; English uses installed Windows voices. The Alexandria font remains local for captions. Font/asset public redistribution rights remain unverified, so originals and derived media stay ignored and local. No large AI model was downloaded. About 25.6GB RAM was detected; a subsequent nvidia-smi check confirmed a GTX 1660 SUPER with 6144 MiB VRAM, correcting the earlier incomplete hardware assessment. CPU-only tools were selected for reproducibility.
