# The Brief

A weekly investing brief designed to teach how to read markets and understand why
stocks move, rather than tell anyone what to buy.

## What's here

- `issue-2-reference.html` — Issue No. 2 (week of May 12, 2026). The design reference
  the archive should match. Not edited going forward; serves as the visual + structural
  source of truth.

## What comes next

1. Multi-issue archive: single HTML file holding past + current issues, with top-nav
   pill switcher between issues. Empty daily slot inside each weekly issue ready for
   manual paste-in content.
2. (Later, only after the archive is in real use) Python + Anthropic SDK script that
   generates a daily brief and appends it to the archive.

## Conventions

- No build step. Single self-contained HTML files. Vanilla JS only.
- Fonts: Fraunces, JetBrains Mono, Inter via Google Fonts.
- Design tokens defined in `:root` (see Issue No. 2 reference).
- Every claim tagged by confidence: Fact / Interp / Spec.
- No stock picks — frameworks only.
