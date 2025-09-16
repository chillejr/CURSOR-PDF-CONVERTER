#!/usr/bin/env python3
from __future__ import annotations

import os
from typing import List, Tuple, Dict

import fitz  # PyMuPDF
from PIL import Image

from step2_translate import translate_to_swahili


class PreserveLayoutConverter:
    def __init__(self, translate_concurrency: int = 3, translate_func=None) -> None:
        self.translate_concurrency = translate_concurrency
        self.translate_func = translate_func  # optional override

    def convert(self, input_pdf: str, output_pdf: str) -> None:
        if not os.path.isfile(input_pdf):
            raise FileNotFoundError(input_pdf)

        doc = fitz.open(input_pdf)

        # Collect line-level boxes per page (reduce overlap):
        # line tuple: (x0, y0, x1, y1, text, size, rgb_tuple)
        all_lines: List[List[Tuple[float, float, float, float, str, float, Tuple[float, float, float]]]] = []
        for page in doc:
            info = page.get_text("dict")
            page_lines: List[Tuple[float, float, float, float, str, float, Tuple[float, float, float]]] = []
            for blk in info.get("blocks", []):
                if blk.get("type", 0) != 0:
                    continue  # only text blocks
                for ln in blk.get("lines", []):
                    spans = ln.get("spans", [])
                    if not spans:
                        continue
                    # Compute a bounding box that covers all spans in the line
                    xs0 = []
                    ys0 = []
                    xs1 = []
                    ys1 = []
                    texts: List[str] = []
                    max_size: float = 0.0
                    col_rgb: Tuple[float, float, float] = (0, 0, 0)
                    for s in spans:
                        t = s.get("text", "") or ""
                        if not t.strip():
                            continue
                        bbox = s.get("bbox") or blk.get("bbox")
                        if not bbox:
                            continue
                        x0, y0, x1, y1 = bbox
                        xs0.append(x0); ys0.append(y0); xs1.append(x1); ys1.append(y1)
                        texts.append(t)
                        sz = float(s.get("size", 0) or 0)
                        if sz > max_size:
                            max_size = sz
                        col = s.get("color")
                        if isinstance(col, int):
                            r = ((col >> 16) & 255) / 255.0
                            g = ((col >> 8) & 255) / 255.0
                            b = (col & 255) / 255.0
                            col_rgb = (r, g, b)
                    if not xs0:
                        continue
                    # Join spans with a space to reduce collisions
                    line_text = " ".join(texts).strip()
                    if not line_text:
                        continue
                    lx0, ly0, lx1, ly1 = min(xs0), min(ys0), max(xs1), max(ys1)
                    # Small padding inside the line rect to allow wrapping
                    pad = 2.0
                    page_lines.append((lx0 + pad, ly0 + pad, lx1 - pad, ly1 - pad, line_text, max_size if max_size > 0 else 0.0, col_rgb))
            all_lines.append(page_lines)

        for page_index, page in enumerate(doc):
            page_lines = all_lines[page_index]
            if not page_lines:
                continue  # image-only page, keep as-is

            # Translate per line
            originals = [ln[4] for ln in page_lines]
            translated = []
            for txt in originals:
                if self.translate_func is not None:
                    try:
                        translated.append(self.translate_func(txt))
                    except Exception:
                        translated.append(txt)
                else:
                    translated.append(translate_to_swahili(txt, max_workers=1))

            if len(translated) != len(page_lines):
                if len(translated) < len(page_lines):
                    translated += [""] * (len(page_lines) - len(translated))
                else:
                    translated = translated[: len(page_lines)]

            # Redact only lines that will be redrawn; remove original glyphs to avoid overlap
            redact_rects = []
            for (x0, y0, x1, y1, _t, _sz, _rgb), new_text in zip(page_lines, translated):
                if (new_text or "").strip():
                    # Remove original text glyphs but keep backgrounds/shapes (no fill)
                    page.add_redact_annot(fitz.Rect(x0, y0, x1, y1), fill=None)
                    redact_rects.append(1)
            if redact_rects:
                page.apply_redactions()

            # Redraw translated text at line rectangles with auto-fit
            for (x0, y0, x1, y1, _t, sz, rgb), new_text in zip(page_lines, translated):
                if not (new_text or "").strip():
                    continue
                rect = fitz.Rect(x0, y0, x1, y1)
                # Use base-14 core alias 'helv' to avoid external font files
                self._draw_fit_text(page, rect, new_text, base_size=sz, color=rgb, fontname="helv")

        os.makedirs(os.path.dirname(os.path.abspath(output_pdf)) or ".", exist_ok=True)
        doc.save(output_pdf, deflate=True, incremental=False)
        doc.close()

    @staticmethod
    def _draw_fit_text(page: fitz.Page, rect: fitz.Rect, text: str, base_size: float | None = None, color: Tuple[float, float, float] = (0, 0, 0), fontname: str = "helv") -> None:
        # Try auto-fit first with left alignment and line wrapping
        leftover = page.insert_textbox(rect, text, fontsize=0, fontname=fontname, color=color, align=0)
        if not leftover:
            return
        # If still leftover, attempt progressive downsizing
        start = int(base_size) if base_size and base_size > 0 else 12
        for size in range(start, 5, -1):
            leftover = page.insert_textbox(rect, text, fontsize=size, fontname=fontname, color=color, align=0)
            if not leftover:
                return
        # As last resort, truncate with ellipsis to avoid overlap
        visible = text[: max(50, len(text) // 3)] + " …"
        page.insert_textbox(rect, visible, fontsize=6, fontname=fontname, color=color, align=0)