# T Digest Broadsheet — cloud version

Use this folder when building the Broadsheet from a Claude Code cloud session
(web or mobile). The desktop files in `templates/` and `scripts/` stay tuned for
the Windows PC and are not changed.

## Why a separate copy

Cloud sessions run on Linux with different fonts from Windows, so the same page
zoom values fill the page differently. `cloud/T Digest.html` is the desktop
template with its own zoom values at the bottom of the `<script>`:

| | Desktop | Cloud |
|---|---|---|
| Page 1 (`af1.style.zoom`) | 0.64 | 0.70 |
| Page 2 (`af2.style.zoom`) | 0.58 | 0.64 |

Calibrated 2026-09-29: page 1 spills onto a 3rd page at 0.73 and page 2 at
0.68, so both values keep a safety margin. Result: 2 pages, both ~93–95% full.

## Build a PDF

```bash
npm ci --prefix scripts
pip install pymupdf
node cloud/render_broadsheet.js --html "cloud/T Digest.html" --out "T Digest - Broadsheet - YYYY-MM-DD.pdf"
python3 cloud/check_fill.py "T Digest - Broadsheet - YYYY-MM-DD.pdf"
```

## When the content changes

Follow `tasks/t-digest-daily-email/SKILL.md` for content and styling, but edit
`cloud/T Digest.html`. New content can change how the page fills, so after
rendering, check the output of `check_fill.py`: it should be exactly 2 pages with
both pages roughly 85–95% full. If not, nudge `af1`/`af2` in 0.02 steps, re-render,
and keep a margin below the value that first tips into 3 pages. Also look at the
PDF itself before sending it.
