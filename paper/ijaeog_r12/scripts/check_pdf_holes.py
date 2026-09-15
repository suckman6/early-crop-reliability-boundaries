"""Measure column-bottom whitespace in the compiled two-column manuscript.

Usage: python check_pdf_holes.py <pdf>

The check ignores page-number/footer text below 770 pt and reports pages 2
through N-1. It is a regression diagnostic, not a semantic layout engine.
"""

from __future__ import annotations

import sys

import pdfplumber


FOOTER_Y = 770.0


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    maximum = (0.0, 0, "")
    with pdfplumber.open(sys.argv[1]) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            if page_number in (1, len(pdf.pages)):
                continue
            words = page.extract_words(use_text_flow=False, keep_blank_chars=False)
            width = float(page.width)
            for name, left, right in (("L", 0.0, width / 2), ("R", width / 2, width)):
                bottoms = [
                    float(word["bottom"])
                    for word in words
                    if left <= (float(word["x0"]) + float(word["x1"])) / 2 < right
                    and float(word["top"]) < FOOTER_Y
                ]
                if not bottoms:
                    continue
                hole = max(0.0, FOOTER_Y - max(bottoms))
                print(f"p{page_number:02d} col{name}: bottom_hole={hole:.1f} pt")
                if hole > maximum[0]:
                    maximum = (hole, page_number, name)
    print(f"MAX_NONFIRST_NONLAST={maximum[0]:.1f} pt (p{maximum[1]:02d} col{maximum[2]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
