#!/usr/bin/env python3
"""Decree 30/2020/ND-CP compliance audit for generated .docx files.

Usage: python3 audit_docx.py <file.docx> [--strict]
Exit code 0 = pass, 1 = violations found.
Checks: A4 page size, margin ranges, font family, font size range,
        leftover {{TOKEN}} placeholders.
"""
import re, sys

from docx import Document

TOKEN = re.compile(r"\{\{[A-Z_]+\}\}")
ERR, WARN = [], []


def cm(v):
    return round(v.cm, 2) if v is not None else None


def iter_paragraphs(doc):
    for p in doc.paragraphs:
        yield p
    for t in doc.tables:
        for row in t.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    yield p


def main(path, strict=False):
    doc = Document(path)
    sec = doc.sections[0]

    # 1. A4
    w, h = cm(sec.page_width), cm(sec.page_height)
    if not (20.9 <= w <= 21.1 and 29.6 <= h <= 29.8):
        ERR.append(f"Khổ giấy {w}x{h}cm — KHÔNG phải A4 (21.0x29.7)")

    # 2. Margins per ND30: top 2-2.5, bottom 2-2.5, left 3-3.5, right 1.5-2
    for name, val, lo, hi in [
        ("Lề trên", cm(sec.top_margin), 2.0, 2.5),
        ("Lề dưới", cm(sec.bottom_margin), 2.0, 2.5),
        ("Lề trái", cm(sec.left_margin), 3.0, 3.5),
        ("Lề phải", cm(sec.right_margin), 1.5, 2.0),
    ]:
        if val is None or not (lo - 0.01 <= val <= hi + 0.01):
            ERR.append(f"{name} = {val}cm — ngoài khung NĐ30 [{lo}-{hi}]cm")

    # 3. Fonts + sizes on runs
    bad_font, bad_size = set(), set()
    for p in iter_paragraphs(doc):
        for r in p.runs:
            if not r.text.strip():
                continue
            name = r.font.name
            if name is not None and name != "Times New Roman":
                bad_font.add(name)
            sz = r.font.size.pt if r.font.size else None
            if sz is not None and not (11 <= sz <= 16):
                bad_size.add(sz)
    if bad_font:
        ERR.append(f"Font khác Times New Roman: {sorted(bad_font)}")
    if bad_size:
        WARN.append(f"Cỡ chữ ngoài khung 11-16pt: {sorted(bad_size)}")

    # 4. Leftover tokens
    leftover = sorted({m for p in iter_paragraphs(doc)
                       for r in p.runs for m in TOKEN.findall(r.text)})
    if leftover:
        (ERR if strict else WARN).append(
            f"Token chưa điền: {leftover} — phải là chủ đích (placeholder cho user) "
            f"và được liệt kê trong Output Contract")

    print(f"=== AUDIT: {path} ===")
    print(f"Trang: {w}x{h}cm | Lề T/B/L/R: {cm(sec.top_margin)}/"
          f"{cm(sec.bottom_margin)}/{cm(sec.left_margin)}/{cm(sec.right_margin)}cm")
    for e in ERR:
        print(f"[FAIL] {e}")
    for wn in WARN:
        print(f"[WARN] {wn}")
    if not ERR and not WARN:
        print("[PASS] Không phát hiện vi phạm.")
    return 1 if ERR else 0


if __name__ == "__main__":
    strict = "--strict" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--strict"]
    if not args:
        print("Usage: audit_docx.py <file.docx> [--strict]"); sys.exit(2)
    sys.exit(main(args[0], strict))
