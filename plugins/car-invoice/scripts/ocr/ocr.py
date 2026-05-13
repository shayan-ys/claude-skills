"""PaddleOCR-VL 1.5 4-bit OCR wrapper using mlx_vlm.

Mac/Apple Silicon only. Requires: mlx-vlm, pypdfium2, numpy, Pillow.
Bootstrap: cd scripts/ocr && uv venv && uv sync
"""

from __future__ import annotations

import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Optional

os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")

MODEL_ID = "mlx-community/PaddleOCR-VL-1.5-4bit"
OCR_PROMPT = (
    "Read all the text in this document image and output it as Markdown, "
    "preserving tables, lists, headings, and form fields. "
    "If the page contains only a header, footer, or is essentially blank, "
    "output just those elements — do not add any other content."
)

_RENDER_SCALE = 300 / 72  # 300 DPI (was 144 DPI at scale=2.0)
# Cap before VLM. At 300 DPI a US Letter page is 2550×3300px (~8MP) — far above the ~2MP
# budget where this model's image-token count starts crowding out text generation.
# 1500px wide → 1500×1942px (~2.9MP) matches the working 144 DPI area (1224×1584).
_MAX_IMAGE_WIDTH = 1500

# PaddleOCR-VL 1.5 emits layout-coordinate tokens (<|LOC_NNN|>) into generation output.
# mlx_vlm has no generation flag to suppress them, so we strip in post-processing.
_LOC_TOKEN_RE = re.compile(r"<\|LOC_\d+\|>")

# Detect the earliest cyclic repetition: substring of 5–500 chars repeated 3+ consecutive times.
_CYCLIC_RE = re.compile(r"(.{5,500}?)\1{2,}", re.DOTALL)

# Known hallucination strings (inlined from quality module to keep this package self-contained).
HALLUCINATION_STRINGS = [
    "download your product",
    "service part 04",
    "download free",
    "update to the latest version",
]


def _truncate_cyclic_repetition(text: str, max_passes: int = 3) -> str:
    """Remove VLM generation loops while preserving all leading valid content.

    Finds the earliest point where a substring (5–500 chars) repeats 3+ times
    consecutively, keeps the content up to and including ONE copy of the pattern,
    then appends an HTML comment. Runs up to *max_passes* times to handle pages
    with multiple distinct loops.

    Examples::

        >>> t = "Good content\\nGreen / Yellow / Red\\n" + "Green / Yellow / Red\\n" * 50
        >>> out = _truncate_cyclic_repetition(t)
        >>> out.startswith("Good content")
        True
        >>> "<!-- [OCR loop detected" in out
        True
        >>> out.count("Green / Yellow / Red") == 1
        True

        >>> _truncate_cyclic_repetition("No loops here") == "No loops here"
        True
    """
    for _ in range(max_passes):
        m = _CYCLIC_RE.search(text)
        if not m:
            break
        pattern = m.group(1)
        repeat_count = (len(m.group(0)) // len(pattern))
        # Keep everything up to and including one copy of the pattern
        keep_end = m.start() + len(pattern)
        text = (
            text[:keep_end]
            + f"\n\n<!-- [OCR loop detected and truncated: pattern of length "
            f"{len(pattern)} chars, repeated {repeat_count} times] -->\n"
        )
    return text


def _looks_hallucinated(text: str) -> bool:
    """Return True when VLM output is too short, contains known hallucination strings,
    or was almost entirely consumed by a sanitizer loop truncation."""
    stripped = text.strip()
    if len(stripped) < 100:
        return True
    lower = stripped.lower()
    if any(s in lower for s in HALLUCINATION_STRINGS):
        return True
    # If the sanitizer fired and the truncation marker makes up >30% of the text, little real
    # content survived — treat as hallucinated.
    marker = "<!-- [ocr loop detected"
    marker_chars = sum(len(line) for line in stripped.splitlines() if marker in line.lower())
    if marker_chars / len(stripped) > 0.30:
        return True
    return False


def _pdf_page_text_layer(pdf_path: Path, page_index: int) -> str:
    """Extract embedded text-layer text from a single PDF page (0-indexed)."""
    import pypdfium2 as pdfium
    doc = pdfium.PdfDocument(str(pdf_path))
    try:
        return doc[page_index].get_textpage().get_text_range() or ""
    finally:
        doc.close()


_model = None
_processor = None


def _load_model():
    global _model, _processor
    if _model is None:
        import mlx_vlm
        print(f"Loading {MODEL_ID} ...", file=sys.stderr)
        _model, _processor = mlx_vlm.load(MODEL_ID)
        print("Model loaded.", file=sys.stderr)
    return _model, _processor


def _pdf_to_images(pdf_path: Path, tmp_dir: Path) -> list[Path]:
    import pypdfium2 as pdfium
    from PIL import Image
    doc = pdfium.PdfDocument(str(pdf_path))
    paths = []
    for i, page in enumerate(doc):
        bitmap = page.render(scale=_RENDER_SCALE)
        img = bitmap.to_pil()
        if img.width > _MAX_IMAGE_WIDTH:
            ratio = _MAX_IMAGE_WIDTH / img.width
            img = img.resize((_MAX_IMAGE_WIDTH, int(img.height * ratio)), Image.LANCZOS)
        out = tmp_dir / f"page_{i}.png"
        img.save(str(out))
        paths.append(out)
    doc.close()
    return paths


def _is_mostly_blank(img_path: Path, threshold: float = 0.98) -> bool:
    """Return True if >threshold of pixels are near-white — skip VLM for blank pages."""
    import numpy as np
    from PIL import Image
    arr = np.array(Image.open(img_path).convert("L"))
    return (arr > 240).sum() / arr.size > threshold


def _ocr_image(img_path: Path, model, processor) -> str:
    # Blank-page gate: skip VLM entirely for near-white pages
    if _is_mostly_blank(img_path):
        return ""

    import mlx_vlm
    prompt = mlx_vlm.apply_chat_template(
        processor,
        model.config,
        prompt=OCR_PROMPT,
        num_images=1,
    )
    result = mlx_vlm.generate(
        model,
        processor,
        prompt=prompt,
        image=[str(img_path)],
        max_tokens=8192,
        # 1.3 with 256-token window: narrower context + slightly stronger penalty
        # better suppresses tight cycles without over-penalizing recurring column
        # headers across a full page. Defense-in-depth behind the cyclic sanitizer.
        repetition_penalty=1.3,
        repetition_context_size=256,
        verbose=False,
    )
    raw = result.text if hasattr(result, "text") else str(result)
    # Strip PaddleOCR-VL layout-coordinate tokens — they bleed into output and waste token budget
    return _truncate_cyclic_repetition(_LOC_TOKEN_RE.sub("", raw))


def _merge_page(vlm_text: str, layer_text: str) -> str:
    """Merge VLM OCR and PDF text-layer output into one labeled markdown page.

    Both signals are included whenever available so the downstream extractor can
    cross-reference them. When the VLM output looks hallucinated we annotate it
    and drop it if the text layer is strong enough to stand alone.
    """
    vlm_stripped = vlm_text.strip()
    layer_stripped = layer_text.strip()

    vlm_section: str | None
    if not vlm_stripped:
        vlm_section = None  # blank page — VLM was skipped
    elif _looks_hallucinated(vlm_stripped) and len(layer_stripped) >= 200:
        vlm_section = None  # text layer is strong; drop the garbage VLM output
    elif _looks_hallucinated(vlm_stripped):
        vlm_section = (
            "<!-- [VLM output looks unreliable — prefer the PDF text layer below] -->\n"
            + vlm_stripped
        )
    else:
        vlm_section = vlm_stripped

    layer_section = layer_stripped if layer_stripped else None

    parts: list[str] = []
    if vlm_section is not None:
        parts.append("<!-- === VLM OCR (PaddleOCR-VL) === -->\n" + vlm_section)
    if layer_section is not None:
        parts.append("<!-- === PDF text layer === -->\n" + layer_section)
    if not parts:
        return ""
    return "\n\n".join(parts) + "\n"


def ocr_pdf(pdf_path: Path, out_dir: Path) -> list[Path]:
    pdf_path = Path(pdf_path).resolve()
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    model, processor = _load_model()

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        print(f"Rendering pages for {pdf_path.name} ...", file=sys.stderr)
        img_paths = _pdf_to_images(pdf_path, tmp_dir)
        page_files: list[Path] = []
        for i, img_path in enumerate(img_paths, start=1):
            print(f"  OCR page {i}/{len(img_paths)} ...", file=sys.stderr)
            vlm_text = _ocr_image(img_path, model, processor)
            layer_text = _pdf_page_text_layer(pdf_path, i - 1)
            text = _merge_page(vlm_text, layer_text)
            out_file = out_dir / f"page_{i}.md"
            out_file.write_text(text, encoding="utf-8")
            page_files.append(out_file)
            print(
                f"  wrote {out_file} (vlm={len(vlm_text.strip())} chars, "
                f"layer={len(layer_text.strip())} chars)",
                file=sys.stderr,
            )
    return page_files


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: python -m ocr <pdf-path> <output-dir>", file=sys.stderr)
        sys.exit(1)
    pages = ocr_pdf(Path(sys.argv[1]), Path(sys.argv[2]))
    for p in pages:
        print(p)
