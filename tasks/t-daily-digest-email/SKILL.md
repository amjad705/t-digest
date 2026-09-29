---
name: t-daily-digest-email
description: Build today's T Daily Digest (India/Pakistan/Global, A4 PDF) and email it to <YOUR_EMAIL>
---

Build today's edition of "T Daily Digest" and email it as a PDF attachment to <YOUR_EMAIL>. Run fully autonomously end to end — do not ask the user any clarifying questions.

This is a DISTINCT report from the pre-existing "T Digest" skill/task (taskId t-digest-daily-email, files T Digest.html / T Digest - Briefing.html). Never touch those files or that task — they are a separate report the user runs in parallel.

SCOPE (do not drift outside this — no general world news):
- India: Political, Economic, Military, Technology Advancements
- Pakistan: Political, Economic, Military, Technology Advancements
- Global: AI, Military Development, Technology Advancements

Every news item must have exactly 4 labeled fields:
1. News — one-sentence headline of what happened.
2. Facts — verifiable detail: numbers, dates, named officials/programs, dollar figures. Cross-check across at least two sources where possible.
3. Ideal Case — a neutral, one-sentence best-case/desired-resolution framing (analytical, not advocacy for either side).
4. Impact — state whether the effect is Global or Pakistan specifically, grounded in the facts given.

Do not invent facts, figures, or sources.

STEP 1 — Research broadly (WebSearch, today's actual date in each query): run separate searches for India political/economic/military/technology, Pakistan political/economic/military/technology, and global AI/military development/technology advancements. Also check X/Twitter for relevant OSINT and reporter accounts. Pull only stories from the last 1-3 days; prefer today's date. Only mark a topic "no confirmed developments today" after genuinely exhausting searches — then use the most recent dated item instead of leaving the block empty.

STEP 2 — Update the template (DO NOT redesign — reuse the exact existing template, edit text only): `C:\Users\User\Desktop\claude data\T Daily Digest.html`, a single-flow A4 HTML document (`<div class="sheet">`) with a `<!-- SECTION -->`-commented masthead, then India (break-first section), Pakistan (page break), Global (page break) — each with their topic blocks (`.topic-block.pol/.eco/.mil/.tech`) and `.item-card` items (`.item-headline` / `.item-field` News/Facts/Ideal Case/Impact). Update the masthead date and bump `Vol. 2026 · No. 0XX` by one from the prior run. Update each country's `.country-header` pulled stat. Keep one `.item-card` per topic block unless there are genuinely 2+ distinct well-sourced stories. Update the footer source list to outlets actually used. Do not touch the `<style>` block or any class names.

STEP 3 — Render and send. Run this exact command (Bash or PowerShell), substituting today's actual date:

node "C:\Users\User\Desktop\claude data\brain\brain\.claude\skills\daily-tech-report\scripts\t_daily_digest_render_and_send.js" --html "C:\Users\User\Desktop\claude data\T Daily Digest.html" --out "C:\Users\User\Desktop\claude data\T Daily Digest - <YYYY-MM-DD>.pdf" --to <YOUR_EMAIL> --from <YOUR_EMAIL> --password-file "C:\Users\User\.claude\secrets\war-report-gmail-app-password.txt"

If `node` isn't found, prepend its install dir to PATH first (Bash: `export PATH="/c/Program Files/nodejs:$PATH"`; PowerShell: `$env:Path += ";C:\Program Files\nodejs"`).

SUCCESS CRITERIA: the command prints "Wrote ..." then "Emailed T Daily Digest to <YOUR_EMAIL>" with no errors. This is a real SMTP send (nodemailer + Gmail app password) — it actually delivers. Verify the PDF is exactly 3 pages via `grep -a -o "/Count [0-9]*" "<file>.pdf"` before considering the run done. If the command errors, report the exact error rather than retrying blindly — a transient DNS/network error is safe to retry once.

one more thing every news must be of same date the report is generated. the latest


This task is scheduled to fire at 09:00 local time sharp. The scheduler itself may add a few minutes of dispatch jitter beyond this skill's control — that is a platform-level constraint, not something to work around here.