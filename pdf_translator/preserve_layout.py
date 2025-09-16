#!/usr/bin/env python3
from __future__ import annotations

import os
from typing import List, Tuple

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

        # Collect text blocks per page using dict mode so we can preserve basic styling
        all_blocks: List[List[Tuple[float, float, float, float, str, float, Tuple[float, float, float]]]] = []
        for page in doc:
            info = page.get_text("dict")
            page_blocks: List[Tuple[float, float, float, float, str, float, Tuple[float, float, float]]] = []
            for blk in info.get("blocks", []):
                if blk.get("type", 0) != 0:
                    continue  # only text blocks
                x0, y0, x1, y1 = blk.get("bbox", (0, 0, 0, 0))
                lines = blk.get("lines", [])
                texts: List[str] = []
                max_size: float = 0.0
                rgb: Tuple[float, float, float] = (0, 0, 0)
                for ln in lines:
                    spans = ln.get("spans", [])
                    line_text = "".join(s.get("text", "") for s in spans)
                    if line_text.strip():
                        texts.append(line_text)
                    for s in spans:
                        sz = float(s.get("size", 0) or 0)
                        if sz > max_size:
                            max_size = sz
                        col = s.get("color")
                        if isinstance(col, int):
                            # color as int 0xRRGGBB
                            r = ((col >> 16) & 255) / 255.0
                            g = ((col >> 8) & 255) / 255.0
                            b = (col & 255) / 255.0
                            rgb = (r, g, b)
                text = "\n".join(texts).strip()
                if text:
                    page_blocks.append((x0, y0, x1, y1, text, max_size if max_size > 0 else 0.0, rgb))
            all_blocks.append(page_blocks)

        for page_index, page in enumerate(doc):
            page_blocks = all_blocks[page_index]
            # If no text blocks (image-only page), leave the page unchanged
            if not page_blocks:
                continue

            # Block-by-block translation for regular text pages
            original_texts = [blk[4] for blk in page_blocks]
            translated_blocks = []
            for txt in original_texts:
                if self.translate_func is not None:
                    try:
                        translated_blocks.append(self.translate_func(txt))
                    except Exception:
                        translated_blocks.append(txt)
                else:
                    translated_blocks.append(translate_to_swahili(txt, max_workers=self.translate_concurrency))

            if len(translated_blocks) != len(page_blocks):
                if len(translated_blocks) < len(page_blocks):
                    translated_blocks += [""] * (len(page_blocks) - len(translated_blocks))
                else:
                    translated_blocks = translated_blocks[: len(page_blocks)]

            # Redact only blocks that have a non-empty translation
            redact_rects = []
            for (x0, y0, x1, y1, _txt), new_text in zip(page_blocks, translated_blocks):
                if (new_text or "").strip():
                    rect = fitz.Rect(x0, y0, x1, y1)
                    page.add_redact_annot(rect, fill=(1, 1, 1))
                    redact_rects.append(rect)
            if redact_rects:
                page.apply_redactions()

            # Draw translated text roughly in original areas
            for (x0, y0, x1, y1, _txt, _sz, _rgb), new_text in zip(page_blocks, translated_blocks):
                if not (new_text or "").strip():
                    continue
                rect = fitz.Rect(x0, y0, x1, y1)
                self._draw_fit_text(page, rect, new_text, base_size=_sz, color=_rgb)

        os.makedirs(os.path.dirname(os.path.abspath(output_pdf)) or ".", exist_ok=True)
        doc.save(output_pdf, deflate=True, incremental=False)
        doc.close()

    @staticmethod
    def _draw_fit_text(page: fitz.Page, rect: fitz.Rect, text: str, base_size: float | None = None, color: Tuple[float, float, float] = (0, 0, 0)) -> None:
        # try with provided base size first (approximate original styling)
        if base_size and base_size > 0:
            leftover = page.insert_textbox(rect, text, fontsize=base_size, fontname="helv", color=color, align=0)
            if not leftover:
                return
        # then try auto-fit
        leftover = page.insert_textbox(rect, text, fontsize=0, fontname="helv", color=color, align=0)
        if not leftover:
            return
        for size in (14, 12, 11, 10, 9, 8, 7, 6):
            leftover = page.insert_textbox(rect, text, fontsize=size, fontname="helv", color=color, align=0)
            if not leftover:
                return
        visible = text[: max(50, len(text) // 4)] + " …"
        page.insert_textbox(rect, visible, fontsize=6, fontname="helv", color=color, align=0)