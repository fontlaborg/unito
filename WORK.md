---
this_file: WORK.md
---

## 2026-02-10

### Scope
Build a spectacular minisite for the Unito font family inside `./docs/`.

### Changes made
- Created `docs/style.css`: full design system — dark theme (`#0a0a0f`), gold accents (`#e8c547`), Inter from Google Fonts for UI, `@font-face` for Unito specimens, fluid typography via `clamp()`, scroll-reveal animations, responsive breakpoints.
- Rewrote `docs/index.html`: complete single-page minisite with 7 sections:
  1. **Hero** — full-viewport, gradient-animated "Unito" title, key stats (6 families, 24 fonts, ∞ scripts, OFL)
  2. **About** — description of pan-Unicode coverage, feature highlight cards
  3. **Families** — 6 cards (Unito, JP, CN, HK, TW, KR) with sample text in each script
  4. **Type Tester** — live preview with family/style/size controls
  5. **Glyph Explorer** — uses opentype.js to parse TTF and render glyphs on canvas with pagination
  6. **Download** — direct download links to GitHub raw URLs for all 24 fonts
  7. **Footer** — GitHub, license, Fontlab Ltd links
- No build step required — all JS inline, opentype.js from jsDelivr CDN.

### Verification
- Opened `http://localhost:8765/docs/index.html` in browser
- All 7 sections render correctly with dark theme and scroll-reveal animations
- Hero shows gradient-animated "Unito" title rendered in Unito Bold
- Family cards display CJK sample text correctly
- Type tester updates live when changing family/style/size
- Glyph explorer loads font, renders glyphs on canvas with Unicode labels and pagination
- Download links point to correct GitHub raw URLs

### Previous (2026-02-09)
- Fixed Unifont source routing (`50unif` / `51unif`) — see previous WORK.md entry
