#!/usr/bin/env python3
"""
Step 3: Create a simple text-only PDF from translated Swahili text using fpdf2.

- Reuses extract_text_from_pdf and translate_to_swahili.
- Adds create_translated_pdf(translated_text, output_path).
- CLI: prompts for input PDF and output PDF path, then writes the translated PDF.
"""
from __future__ import annotations

import os
import sys
from typing import Optional

from fpdf import FPDF  # fpdf2

from step1_extract import extract_text_from_pdf
from step2_translate import translate_to_swahili


def _to_latin1(text: str) -> str:
    """Best-effort conversion to Latin-1 for core PDF font compatibility.

    Swahili mostly uses ASCII/Latin characters, so core fonts typically suffice.
    Characters outside Latin-1 are replaced with '?'.
    """
    return text.encode("latin-1", "replace").decode("latin-1")


def create_translated_pdf(translated_text: str, output_path: str) -> None:
    if not translated_text:
        raise ValueError("No translated text provided.")

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Core fonts (like Arial) are built-in but limited to Latin-1.
    pdf.set_font("Arial", size=12)

    # Use multi_cell to wrap text across lines/pages.
    safe_text = _to_latin1(translated_text)
    pdf.multi_cell(w=0, h=8, txt=safe_text)

    # Ensure directory exists
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    pdf.output(output_path)


def _prompt_input_path() -> str:
    try:
        path = input("Enter the path to the source PDF file: ").strip()
    except EOFError:
        path = ""
    return path


def _prompt_output_path(default_path: str) -> str:
    try:
        path = input(f"Enter output PDF path [default: {default_path}]: ").strip()
    except EOFError:
        path = ""
    return path or default_path


if __name__ == "__main__":
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else _prompt_input_path()
    if not pdf_path:
        print("No PDF path provided.")
        sys.exit(1)

    abs_in = os.path.abspath(pdf_path)
    root, _ = os.path.splitext(abs_in)
    default_out = f"{root}_swahili.pdf"

    output_path = sys.argv[2] if len(sys.argv) > 2 else _prompt_output_path(default_out)

    try:
        source_text = extract_text_from_pdf(abs_in)
        if not source_text.strip():
            print("No text extracted from the PDF.")
            sys.exit(0)
        sw_text = translate_to_swahili(source_text)
        create_translated_pdf(sw_text, output_path)
        print(f"Translated PDF saved to: {output_path}")
    except Exception as exc:
        print(f"Error: {exc}")
        sys.exit(1)