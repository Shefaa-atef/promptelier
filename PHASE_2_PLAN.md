# Delivery status — 6 November 2026

Card production milestones are implemented using direct Pillow rendering instead of the proposed SVG intermediary. See PROJECT_PLAN.md and IMPLEMENTATION_NOTES.md for actual acceptance evidence and remaining visual/template limitations. The plan below is the original proposal, not a claim that every proposed aesthetic feature is complete.

# Phase 2 implementation plan

Authorized scope: Phase 2, beginning with milestone 2.1. No video work. Existing React → FastAPI → rule router → SQLite flow stays in place. No new service, paid API, GPU model, or database migration is needed for 2.1.

## Milestones and acceptance tests

### 2.1 Design specification — current milestone

Files: new `backend/cards/specification.py`, `backend/cards/test_specification.py`; update API, router, API tests, React result panel, README, PROJECT_PLAN, ASSET_AUDIT. Use existing Pydantic only. Input: prompt and optional validated parent specification. Output: versioned structured specification plus applied fields and interpretation warnings. A provider Protocol reserves the same interface for an optional local LLM adapter; no model is installed or called.

Specification includes tier, theme, palette roles and gradient, motif vocabulary, central focal point, symmetry, ornament density, composition, metallic treatment, decorative layers, lighting, texture, and deterministic layout seed. Named defaults are disclosed. Recognized revisions patch only intended fields; color-only revisions preserve every non-palette field including seed. New runs preserve old specifications and parent IDs. Existing runs without specifications remain readable; legacy revisions require specification context rather than inventing prior design details.

Acceptance: Ramadan and botanical briefs yield meaningfully different structured art direction; explicit normal/premium selection; exact color roles; deterministic repeated input; motif addition/removal; isolated color-only revisions and chained revisions; unknown requests produce warnings; immutable parents; schema rejects invalid colors/settings; API persistence/restart/legacy compatibility; real spec visible and downloadable inside run JSON; no artwork or production-success claim. Run full pytest suite and frontend production build.

### 2.2 Original artwork renderer

Proposed modules: renderer interface, SVG composition, motifs, materials, and rasterization. Select an installable free local rasterizer after a Windows compatibility probe (prefer resvg binding or CairoSVG only if native dependencies work). Pillow for image operations. Explain selected dependency before installation.

Use one parametric composition system rather than prompt-specific image files: background/material → restrained repeated ornament → corner/border detail → focal medallion → crescent or botanical focal geometry → highlights. Motif generators own intentional geometry; seed varies controlled detail, never substitutes randomness for hierarchy. Palette, density and symmetry govern shared modules. Render high resolution then downsample. SVG must be self-contained and escape text; no remote resources.

Acceptance: validated spec produces valid SVG and decoded PNG locally; deterministic render; density and motif changes affect visible geometry; compare actual Ramadan and botanical images at card size and enlarged; no reference copying; measure generation latency and document renderer limitations.

### 2.3 Official template assembly

Proposed modules: asset manifest, masks, composition/export. Resolve frame masks by distinguishing enclosed center from transparent exterior; preserve asymmetric native offsets and alpha. Derive exact preview transforms from Illustrator PDF content and supplied preview. Use supplied king-of-clubs face if confirmed, keeping original pixels untouched. Simplify ornament at icon scale rather than blindly shrinking dense details.

Acceptance: original frame pixels verified against composited output where opaque; rounded exterior stays transparent; no gaps/artwork spill; correct face/back overlap and padding; exports at exact sizes; inspect alpha over light/dark backgrounds and icon at actual size. If safe extraction cannot resolve geometry, request precisely scoped Illustrator exports into a new working folder; never overwrite original files.

### 2.4 Validation and delivery

Proposed modules: output validator, run directories, ZIP builder; extend API output metadata and safe allowlisted download routes; React generated preview/downloads. Persist intermediate specification and source SVG alongside production exports in versioned run directories, but package the exact delivery tree separately.

Acceptance: exact case-sensitive paths `Source/b.png`, `cardPreview.png`, `Symbols/cardIcon.png`; dimensions 250×346, 208×261, 46×64; PNG decoding/alpha and integrity; reject missing/corrupt/extra delivery files; ZIP entries exact; safe paths; failure produces explicit failed status and no success claim; individual PNG and ZIP downloads match actual bytes; history retains previous designs. Extend typed statuses only when execution exists.

### 2.5 Quality and revision proof

Generate A: premium midnight-blue/gold Ramadan, crescent, stars, Islamic geometric ornament. Generate B: premium emerald royal botanical, leaf/vine ornament and royal focal point. Review focal hierarchy, edge detail, material restraint, motif identity, actual-size icon readability and template alignment; iterate on observed defects.

Acceptance: inspect exported images side by side; significantly different palette and geometry, not merely different random seeds; color-only revision retains layout/geometry/seed and parent assets; parent checksums unchanged; output validation passes for all runs; record actual tests and images. No video implementation.

## Assembly research remaining

Original frame bounds: normal (1,5,242,344), premium (1,6,242,345), within a 250×346 image. Center pixels are transparent. Native offsets are meaningful. Default source back alpha bounds (0,5,242,344); preview bounds (0,25,208,242). Preview visibly uses a king of clubs, whereas initial spot inspection included king of spades; choose the actual matching face in 2.3. No separately named Default Deck found; source/ contains all 52 faces plus default b.png.

Illustrator has six PDF-compatible pages: gameplay/preview/icon twice. Vector paths and image XObjects are present; editable Adobe layer structure remains unproven. No manual export is required to construct or test a design specification. Public redistribution rights and video-related missing tools remain unresolved, but do not block local 2.1.

## Milestone 2.1 verification — 6 November 2026

26 backend tests passed (one upstream Starlette/httpx deprecation warning). Frontend production build passed, 23 modules transformed. Live HTTP checks through Vite confirmed milestone 2.1 health, persisted Ramadan and botanical specifications, and a linked color-only revision preserving the Ramadan geometry and seed. Three example runs are in local history and `data/phase2-specification-examples.json` (ignored by Git). All 85 original hashes remain unchanged. Browser visual/click-through QA was not performed for this milestone. Artwork rendering and visual design-quality acceptance remain pending 2.2–2.5. No dependencies were added.
