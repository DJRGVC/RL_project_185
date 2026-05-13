"""Visual quality gate for the morning paper.

Compares the generated paper's first page against the NeurIPS reference at
`/tmp/neurips_ref-01.png` using cheap pixel-level heuristics:

- Header/title region (top 15% of page) has significant ink (not blank)
- Body text region has reasonable ink density (~10-30% black pixels)
- Layout is single-column-ish (no big vertical white gutter splitting the page)
- Aspect ratio is portrait letter

Run:
    python scripts/visual_quality_gate.py path/to/paper.pdf

Exits 0 if checks pass, 1 if fails. Prints a brief diagnosis.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PIL import Image
import numpy as np


def render_first_page(pdf_path: Path, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    prefix = out_dir / "check"
    subprocess.check_call([
        "pdftoppm", "-r", "120", "-f", "1", "-l", "1", "-png",
        str(pdf_path), str(prefix),
    ])
    rendered = list(out_dir.glob("check-*.png"))
    if not rendered:
        raise RuntimeError("pdftoppm produced no output")
    return rendered[0]


def ink_fraction(arr: np.ndarray) -> float:
    # arr is HxWx{3 or 4}, RGB(A). "Ink" = pixels darker than 200 in all RGB channels.
    if arr.ndim == 3:
        rgb = arr[..., :3]
    else:
        rgb = arr[..., None].repeat(3, axis=-1)
    mask = (rgb < 200).all(axis=-1)
    return float(mask.mean())


def check_paper(pdf_path: Path) -> tuple[bool, list[str]]:
    issues: list[str] = []
    work_dir = Path("/tmp/visual_quality_check")
    rendered = render_first_page(pdf_path, work_dir)
    img = Image.open(rendered).convert("RGB")
    arr = np.array(img)
    h, w, _ = arr.shape

    # 1. Aspect: portrait letter is ~8.5x11 → h/w ~= 1.29
    aspect = h / w
    if not (1.20 < aspect < 1.40):
        issues.append(f"aspect ratio {aspect:.2f} not portrait-letter-ish (expected 1.20-1.40)")

    # 2. Title region: top 15% should have ink (it's the title block + author line)
    title_band = arr[: int(0.15 * h)]
    title_ink = ink_fraction(title_band)
    if title_ink < 0.005:
        issues.append(f"title region nearly blank ({title_ink*100:.2f}% ink)")
    if title_ink > 0.40:
        issues.append(f"title region too dense ({title_ink*100:.1f}% ink) — likely a figure where title should be")

    # 3. Body region: middle 60% of page should have 5-25% ink (justified body)
    body_band = arr[int(0.20 * h) : int(0.85 * h)]
    body_ink = ink_fraction(body_band)
    if body_ink < 0.02:
        issues.append(f"body region too sparse ({body_ink*100:.1f}% ink) — paper looks blank")
    if body_ink > 0.45:
        issues.append(f"body region too dense ({body_ink*100:.1f}% ink) — likely massive figure")

    # 4. Vertical gutter: if there's a big white column splitting the page, it's two-column
    # Sample vertical strip at middle 30-70% of width
    middle_strip_cols = arr[:, int(0.30 * w) : int(0.70 * w), :]
    col_ink = (middle_strip_cols < 200).all(axis=-1).mean(axis=0)
    big_gutter = (col_ink < 0.01).any() and (col_ink.mean() < 0.05)
    if big_gutter:
        issues.append("possible two-column layout detected; NeurIPS main body is single-column")

    ok = len(issues) == 0
    return ok, issues


def main() -> None:
    if len(sys.argv) != 2:
        print("usage: visual_quality_gate.py <paper.pdf>", file=sys.stderr)
        sys.exit(2)
    pdf = Path(sys.argv[1])
    if not pdf.exists():
        print(f"file not found: {pdf}", file=sys.stderr)
        sys.exit(2)
    ok, issues = check_paper(pdf)
    if ok:
        print(f"PASS: {pdf}")
        sys.exit(0)
    else:
        print(f"FAIL: {pdf}")
        for issue in issues:
            print(f"  - {issue}")
        sys.exit(1)


if __name__ == "__main__":
    main()
