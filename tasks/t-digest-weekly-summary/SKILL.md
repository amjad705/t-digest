---
name: t-digest-weekly-summary
description: Build "T Digest - Weekly Summary" (A4, 1 page) from the past 7 daily T Digest Broadsheet PDFs and send via WhatsApp
---

Build this week's "T Digest — Weekly Summary" and send it via WhatsApp. Run fully autonomously end to end — do not ask the user any clarifying questions.

This is a companion to the daily T Digest Broadsheet (`t-digest-daily-email` scheduled task, fires 08:30 daily). This task fires Sunday 18:00 and covers the same calendar week's 7 daily editions (Mon–Sun), which by 18:00 Sunday will all have been rendered to disk already.

SCOPE — same topic set as the daily edition, do not drift outside it:
- India: Political, Military, Economy, Technology
- Pakistan: Political, Military, Economy, Technology
- Global: AI & Technology, Military Development, UAS & Counter-UAS

STEP 1 — Gather source material from disk (do NOT re-run fresh web research — this report synthesizes what was already published, it doesn't replace it):
The daily task saves one dated PDF per day at `C:\Users\User\Desktop\claude data\T Digest - Broadsheet - <YYYY-MM-DD>.pdf`. Identify this week's Monday–Sunday date range (the 7 calendar days ending today, Sunday) and extract text from all 7 files:

pdftotext -layout "T Digest - Broadsheet - <YYYY-MM-DD>.pdf" -

(`pdftotext` is available at `/mingw64/bin/pdftotext`.) If any daily PDF for the week is missing (e.g. the daily task failed that day), proceed with however many are available and note the gap rather than blocking — do not fabricate a missing day's content.

STEP 2 — Analyze and synthesize (this is the core value of the report — do not just concatenate daily items):
For each of the 8 India/Pakistan topics and 3 Global topics, read across all 7 days and write ONE synthesis paragraph (~180–260 characters) that captures the week's throughline — what developed, how it moved day to day, and where it stood by week's end. Favor trajectory and connective tissue ("X escalated from Day 19 to Day 22, ending in Y" / "forecasts kept climbing even as Z built through the week") over a flat list of headlines. Cite 3–4 of the most relevant outlets used that week per topic (aggregate, not one citation per day). Also produce:
- A one-line week headline (the 2–3 biggest throughlines of the week, editorial voice) with a one-line byline
- A 5-stat "By the Numbers" strip pulling the week's most striking figures (funding rounds, casualty/duration counts, dollar figures, pledges) with a short label and which topic each belongs to

STEP 3 — Update the template (reuse the exact existing template, edit text only — do not redesign):
`C:\Users\User\Desktop\claude data\T Digest - Weekly Summary.html` — A4, single page. Masthead date range, headline/byline, the India/Pakistan two-column grid (4 topics each, `.brief` blocks, body text only — no per-day items), the Global three-column row (`.global-row`, one block each for AI / Military Development / UAS-Ctr-UAS), the "By the Numbers" `.stat-strip` (5 stats), and the footer date range. Keep CSS/class names and page structure unchanged — this is a fixed one-page format, not a multi-page one. If content overflows to a 2nd page (STEP 4 will catch this), trim body paragraph lengths first, then stat-strip label lengths, before touching layout/CSS.

STEP 4 — Render to PDF and verify exactly 1 page:
node "C:\Users\User\Desktop\claude data\brain\brain\.claude\skills\daily-tech-report\scripts\t_digest_weekly_render.js" --html "C:\Users\User\Desktop\claude data\T Digest - Weekly Summary.html" --out "C:\Users\User\Desktop\claude data\T Digest - Weekly Summary - <week-start>-to-<week-end>.pdf"

Verify with `grep -a -o "/Count [0-9]*" "<file>.pdf"` — must show `/Count 1`. If it renders to 2+ pages, trim text per STEP 3's guidance and re-render. Do not send an over-length PDF.

STEP 5 — Send via WhatsApp to all three numbers, no confirmation needed:
The WhatsApp bridge is a local process (`C:\Users\User\whatsapp-mcp\whatsapp-bridge\whatsapp-bridge.exe`) that must be running. Check first (`Get-Process | Where-Object { $_.ProcessName -match "whatsapp-bridge" }` via PowerShell); if not running, start it (`cd "C:\Users\User\whatsapp-mcp\whatsapp-bridge"` then run `.\whatsapp-bridge.exe` in the background) and wait for "Connected to WhatsApp" before sending. If the session appears expired (re-link/QR required), report that and stop rather than retrying blindly.

Call `mcp__whatsapp__send_file` once per recipient with `media_path` set to this week's rendered PDF, for each of:
- "<RECIPIENT_1>"
- "<RECIPIENT_2>"
- "<RECIPIENT_3>"

This report is pre-authorized for autonomous sending, same as the daily Broadsheet — do not ask for confirmation before sending.

SUCCESS CRITERIA: `send_file` returns `{"success": true, ...}` for all three recipients, and the PDF is confirmed 1 page before sending.