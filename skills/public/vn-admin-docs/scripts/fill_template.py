#!/usr/bin/env python3
"""Fill {{TOKEN}} placeholders in a vn-admin-docs template.

Usage:
    python3 fill_template.py --template <t.docx> --data <d.json> --out <o.docx>

data.json: {"SO_KY_HIEU": "[...]", "NOI_DUNG": "Đoạn 1.\nĐoạn 2.", ...}
- Formatting is preserved: each token lives in its own run in the template.
- ANY token whose value contains "\n" expands into multiple paragraphs,
  each cloning the template paragraph's format (alignment, indent, spacing,
  italic...). Used for NOI_DUNG, CAN_CU, NOI_NHAN.
- Paragraphs starting with "Điều N." get that prefix auto-bolded (Quyết định).
- Missing keys are left as {{TOKEN}} so the audit step can report them.
"""
import argparse, copy, json, re, sys

from docx import Document
from docx.text.paragraph import Paragraph

TOKEN = re.compile(r"\{\{([A-Z_]+)\}\}")
DIEU = re.compile(r"^(Điều\s+\d+\.)\s*")


def iter_paragraphs(doc):
    for p in doc.paragraphs:
        yield p
    for t in doc.tables:
        for row in t.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    yield p


def expand_multiline(doc, data):
    """Split any \n-containing token value into cloned paragraphs."""
    multi = {k: [s.strip() for s in str(v).split("\n") if s.strip()]
             for k, v in data.items() if "\n" in str(v)}
    for key, parts in multi.items():
        marker = "{{%s}}" % key
        target = None
        for p in iter_paragraphs(doc):
            if any(marker in r.text for r in p.runs):
                target = p
                break
        if target is None:
            continue
        anchor = target._p
        for part in reversed(parts[1:]):
            clone = copy.deepcopy(target._p)
            anchor.addnext(clone)
            cp = Paragraph(clone, target._parent)
            for r in cp.runs:
                if marker in r.text:
                    r.text = r.text.replace(marker, part)
        for r in target.runs:
            if marker in r.text:
                r.text = r.text.replace(marker, parts[0])
        data[key] = parts[0]  # already applied; avoid re-substitution issues


def fill_runs(p, data):
    for r in p.runs:
        def sub(m):
            return str(data[m.group(1)]) if m.group(1) in data else m.group(0)
        new = TOKEN.sub(sub, r.text)
        if new != r.text:
            r.text = new


def bold_dieu_prefix(doc):
    """'Điều N.' at paragraph start becomes bold, rest keeps its format."""
    for p in iter_paragraphs(doc):
        if not p.runs:
            continue
        m = DIEU.match(p.text)
        if not m:
            continue
        r0 = p.runs[0]
        if not r0.text.startswith(m.group(1)):
            continue  # prefix split across runs — skip rather than corrupt
        rest = r0.text[len(m.group(0)):]
        prefix_r = copy.deepcopy(r0._r)
        r0._r.addprevious(prefix_r)
        pr = None
        for r in p.runs:
            if r._r is prefix_r:
                pr = r
                break
        pr.text = m.group(1) + " "
        pr.font.bold = True
        r0.text = rest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    with open(args.data, encoding="utf-8") as f:
        data = json.load(f)

    doc = Document(args.template)
    expand_multiline(doc, data)
    for p in iter_paragraphs(doc):
        fill_runs(p, data)
    bold_dieu_prefix(doc)
    doc.save(args.out)

    leftover = sorted({m for p in iter_paragraphs(Document(args.out))
                       for r in p.runs for m in TOKEN.findall(r.text)})
    print(f"Saved: {args.out}")
    if leftover:
        print("UNFILLED TOKENS (placeholders kept intentionally or missing data):")
        for tk in leftover:
            print(f"  - {{{{{tk}}}}}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
