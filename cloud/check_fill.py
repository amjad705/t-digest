"""Print page count and how far down each page the content reaches.

Usage: python3 cloud/check_fill.py "T Digest - Broadsheet - YYYY-MM-DD.pdf"
Needs PyMuPDF (pip install pymupdf).
"""
import sys

import pymupdf

MARGIN_PT = 0.6 * 72

doc = pymupdf.open(sys.argv[1])
fills = []
for page in doc:
    bottom = max((b[3] for b in page.get_text("blocks")), default=MARGIN_PT)
    fills.append(f"{(bottom - MARGIN_PT) / (page.rect.height - 2 * MARGIN_PT):.0%}")
print(f"{len(doc)} pages, fill: {' / '.join(fills)}")
