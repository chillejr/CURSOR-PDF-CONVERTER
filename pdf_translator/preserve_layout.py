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

        # Collect text spans per page using dict mode (preserve per-span styling)
        # span tuple: (x0, y0, x1, y1, text, size, rgb_tuple, is_bold, is_italic)
        all_spans: List[List[Tuple[float, float, float, float, str, float, Tuple[float, float, float], bool, bool]]] = []
        for page in doc:
            info = page.get_text("dict")
            page_spans: List[Tuple[float, float, float, float, str, float, Tuple[float, float, float], bool, bool]] = []
            for blk in info.get("blocks", []):
                if blk.get("type", 0) != 0:
                    continue  # only text blocks
                for ln in blk.get("lines", []):
                    for s in ln.get("spans", []):
                        text = s.get("text", "") or ""
                        if not text.strip():
                            continue
                        bbox = s.get("bbox") or blk.get("bbox")
                        if not bbox:
                            continue
                        x0, y0, x1, y1 = bbox
                        size = float(s.get("size", 0) or 0)
                        col = s.get("color")
                        if isinstance(col, int):
                            r = ((col >> 16) & 255) / 255.0
                            g = ((col >> 8) & 255) / 255.0
                            b = (col & 255) / 255.0
                            rgb = (r, g, b)
                        else:
                            rgb = (0, 0, 0)
                        font_name = (s.get("font", "") or "").lower()
                        is_bold = ("bold" in font_name)
                        is_italic = ("italic" in font_name) or ("oblique" in font_name)
                        page_spans.append((x0, y0, x1, y1, text, size, rgb, is_bold, is_italic))
            all_spans.append(page_spans)

        for page_index, page in enumerate(doc):
            page_spans = all_spans[page_index]
            if not page_spans:
                continue  # image-only page, keep as-is

            # Translate per span
            originals = [sp[4] for sp in page_spans]
            translated = []
            for txt in originals:
                if self.translate_func is not None:
                    try:
                        translated.append(self.translate_func(txt))
                    except Exception:
                        translated.append(txt)
                else:
                    translated.append(translate_to_swahili(txt, max_workers=self.translate_concurrency))

            if len(translated) != len(page_spans):
                if len(translated) < len(page_spans):
                    translated += [""] * (len(page_spans) - len(translated))
                else:
                    translated = translated[: len(page_spans)]

            # Redact only spans that will be redrawn; keep backgrounds/images
            redact_rects = []
            for (x0, y0, x1, y1, _t, _sz, _rgb, _b, _i), new_text in zip(page_spans, translated):
                if (new_text or "").strip():
                    page.add_redact_annot(fitz.Rect(x0, y0, x1, y1), fill=None)
                    redact_rects.append(1)
            if redact_rects:
                page.apply_redactions()

            # Redraw translated text at original span rectangles with approximate styling
            for (x0, y0, x1, y1, _t, sz, rgb, is_bold, is_italic), new_text in zip(page_spans, translated):
                if not (new_text or "").strip():
                    continue
                rect = fitz.Rect(x0, y0, x1, y1)
                fontname = "helv"
                if is_bold and is_italic:
                    fontname = "helv-BoldOblique"
                elif is_bold:
                    fontname = "helv-Bold"
                elif is_italic:
                    fontname = "helv-Oblique"
                self._draw_fit_text(page, rect, new_text, base_size=sz, color=rgb, fontname=fontname)

        os.makedirs(os.path.dirname(os.path.abspath(output_pdf)) or ".", exist_ok=True)
        doc.save(output_pdf, deflate=True, incremental=False)
        doc.close()

    @staticmethod
    def _draw_fit_text(page: fitz.Page, rect: fitz.Rect, text: str, base_size: float | None = None, color: Tuple[float, float, float] = (0, 0, 0), fontname: str = "helv") -> None:
        # try with provided base size first (approximate original styling)
        if base_size and base_size > 0:
            leftover = page.insert_textbox(rect, text, fontsize=base_size, fontname=fontname, color=color, align=0)
            if not leftover:
                return
        # then try auto-fit
        leftover = page.insert_textbox(rect, text, fontsize=0, fontname=fontname, color=color, align=0)
        if not leftover:
            return
        for size in (14, 12, 11, 10, 9, 8, 7, 6):
            leftover = page.insert_textbox(rect, text, fontsize=size, fontname=fontname, color=color, align=0)
            if not leftover:
                return
        visible = text[: max(50, len(text) // 4)] + " …"
        page.insert_textbox(rect, visible, fontsize=6, fontname=fontname, color=color, align=0)