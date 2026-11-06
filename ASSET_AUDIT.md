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
