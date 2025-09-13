#!/usr/bin/env python3
from __future__ import annotations

import os
from typing import List, Tuple

import fitz  # PyMuPDF

from step2_translate import translate_to_swahili


class PreserveLayoutConverter:
    def __init__(self, translate_concurrency: int = 3) -> None:
        self.translate_concurrency = translate_concurrency

    def convert(self, input_pdf: str, output_pdf: str) -> None:
        if not os.path.isfile(input_pdf):
            raise FileNotFoundError(input_pdf)

        doc = fitz.open(input_pdf)

        # Strategy:
        # 1) Extract text blocks with coordinates via page.get_text("blocks").
        # 2) Translate each block.
        # 3) Redact original text areas and draw translated text in-place.
        # Images/graphics are left untouched.

        # Collect blocks per page
        all_blocks: List[List[Tuple[float, float, float, float, str]]] = []
        for page in doc:
            blocks = page.get_text("blocks")  # (x0, y0, x1, y1, text, block_no, block_type)
            # Filter text blocks only (block_type=0 in practice)
            page_blocks: List[Tuple[float, float, float, float, str]] = []
            for b in blocks:
                if len(b) >= 5 and isinstance(b[4], str):
                    x0, y0, x1, y1, text = b[0], b[1], b[2], b[3], b[4]
                    if text.strip():
                        page_blocks.append((x0, y0, x1, y1, text))
            all_blocks.append(page_blocks)

        # Translate page by page to reduce API load and preserve order
        for page_index, page in enumerate(doc):
            page_blocks = all_blocks[page_index]
            if not page_blocks:
                continue

            original_text = "\n\n".join([blk[4] for blk in page_blocks])
            translated_text = translate_to_swahili(original_text, max_workers=self.translate_concurrency)
            translated_blocks = translated_text.split("\n\n")

            # Length mismatch fallback: pad or trim
            if len(translated_blocks) != len(page_blocks):
                # naive rescue: translate each block individually
                translated_blocks = []
                for _, _, _, _, txt in page_blocks:
                    translated_blocks.append(translate_to_swahili(txt, max_workers=self.translate_concurrency))

            # Redact only blocks that have a non-empty translation
            redact_rects = []
            for (x0, y0, x1, y1, _txt), new_text in zip(page_blocks, translated_blocks):
                if (new_text or "").strip():
                    rect = fitz.Rect(x0, y0, x1, y1)
                    page.add_redact_annot(rect, fill=(1, 1, 1))
                    redact_rects.append(rect)
            if redact_rects:
                page.apply_redactions()

            # Draw translated text roughly in original areas using fitted text
            for (x0, y0, x1, y1, _txt), new_text in zip(page_blocks, translated_blocks):
                if not (new_text or "").strip():
                    continue
                rect = fitz.Rect(x0, y0, x1, y1)
                self._draw_fit_text(page, rect, new_text)

        # Save to new file; keep images and vector graphics as-is
        os.makedirs(os.path.dirname(os.path.abspath(output_pdf)) or ".", exist_ok=True)
        doc.save(output_pdf, deflate=True, incremental=False)
        doc.close()

    @staticmethod
    def _draw_fit_text(page: fitz.Page, rect: fitz.Rect, text: str) -> None:
        # Try auto-fit first; if leftover remains, reduce font size gradually
        leftover = page.insert_textbox(rect, text, fontsize=0, fontname="helv", color=(0, 0, 0), align=0)
        if not leftover:
            return
        for size in (14, 12, 11, 10, 9, 8, 7, 6):
            leftover = page.insert_textbox(rect, text, fontsize=size, fontname="helv", color=(0, 0, 0), align=0)
            if not leftover:
                return
        # As a last resort, truncate to show at least something
        visible = text[: max(50, len(text) // 4)] + " …"
        page.insert_textbox(rect, visible, fontsize=6, fontname="helv", color=(0, 0, 0), align=0)