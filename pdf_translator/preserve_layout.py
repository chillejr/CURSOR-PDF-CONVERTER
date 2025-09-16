#!/usr/bin/env python3
from __future__ import annotations

import os
from typing import List, Tuple

import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io

from step2_translate import translate_to_swahili


class PreserveLayoutConverter:
    def __init__(self, translate_concurrency: int = 3) -> None:
        self.translate_concurrency = translate_concurrency

    def convert(self, input_pdf: str, output_pdf: str) -> None:
        if not os.path.isfile(input_pdf):
            raise FileNotFoundError(input_pdf)

        doc = fitz.open(input_pdf)

        # Collect blocks per page
        all_blocks: List[List[Tuple[float, float, float, float, str]]] = []
        for page in doc:
            blocks = page.get_text("blocks")  # (x0, y0, x1, y1, text, block_no, block_type)
            page_blocks: List[Tuple[float, float, float, float, str]] = []
            for b in blocks:
                if len(b) >= 5 and isinstance(b[4], str):
                    x0, y0, x1, y1, text = b[0], b[1], b[2], b[3], b[4]
                    if text.strip():
                        page_blocks.append((x0, y0, x1, y1, text))
            all_blocks.append(page_blocks)

        for page_index, page in enumerate(doc):
            page_blocks = all_blocks[page_index]

            if not page_blocks:
                # OCR fallback: rasterize page, OCR, and overlay text
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x scale for better OCR
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                ocr_text = pytesseract.image_to_string(img, lang="eng") or ""
                if ocr_text.strip():
                    sw_text = translate_to_swahili(ocr_text, max_workers=self.translate_concurrency)
                    # Draw a semi-transparent white box and write text top-left; keep images
                    rect = fitz.Rect(36, 36, page.rect.width - 36, page.rect.height - 36)
                    page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1), fill_opacity=0.8)
                    self._draw_fit_text(page, rect, sw_text)
                continue

            # Block-by-block translation for regular text pages
            original_texts = [blk[4] for blk in page_blocks]
            translated_blocks = []
            for txt in original_texts:
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
            for (x0, y0, x1, y1, _txt), new_text in zip(page_blocks, translated_blocks):
                if not (new_text or "").strip():
                    continue
                rect = fitz.Rect(x0, y0, x1, y1)
                self._draw_fit_text(page, rect, new_text)

        os.makedirs(os.path.dirname(os.path.abspath(output_pdf)) or ".", exist_ok=True)
        doc.save(output_pdf, deflate=True, incremental=False)
        doc.close()

    @staticmethod
    def _draw_fit_text(page: fitz.Page, rect: fitz.Rect, text: str) -> None:
        leftover = page.insert_textbox(rect, text, fontsize=0, fontname="helv", color=(0, 0, 0), align=0)
        if not leftover:
            return
        for size in (14, 12, 11, 10, 9, 8, 7, 6):
            leftover = page.insert_textbox(rect, text, fontsize=size, fontname="helv", color=(0, 0, 0), align=0)
            if not leftover:
                return
        visible = text[: max(50, len(text) // 4)] + " …"
        page.insert_textbox(rect, visible, fontsize=6, fontname="helv", color=(0, 0, 0), align=0)