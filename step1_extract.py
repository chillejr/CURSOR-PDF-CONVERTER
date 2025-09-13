#!/usr/bin/env python3
"""
Step 1: Extract text from a PDF using pdfplumber.

- Defines extract_text_from_pdf(pdf_path) that returns concatenated text from all pages.
- Provides a simple CLI that asks for a PDF path and prints the extracted text.

Note: For scanned/image-only PDFs, text extraction may return empty text. In such
cases, OCR would be required (not included in this simple starter).
"""
from __future__ import annotations

import os
import sys
from typing import List

import pdfplumber


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract and return all text from the given PDF file path.

    Args:
        pdf_path: Absolute or relative path to a .pdf file.

    Returns:
        A single string with text concatenated from all pages.
    """
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    extracted_chunks: List[str] = []

    # x_tolerance/y_tolerance can help merge text fragments more naturally.
    with pdfplumber.open(pdf_path) as pdf:
        for page_index, page in enumerate(pdf.pages, start=1):
            text = page.extract_text(x_tolerance=1, y_tolerance=1) or ""
            if text.strip():
                extracted_chunks.append(text)
            else:
                extracted_chunks.append(f"\n[Page {page_index}: No extractable text]")

    return "\n\n".join(extracted_chunks).strip()


def _prompt_path_from_stdin() -> str:
    try:
        path = input("Enter the path to the PDF file: ").strip()
    except EOFError:
        path = ""
    return path


if __name__ == "__main__":
    # Allow either CLI arg or interactive prompt
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else _prompt_path_from_stdin()
    if not pdf_path:
        print("No PDF path provided.")
        sys.exit(1)

    try:
        text = extract_text_from_pdf(pdf_path)
        print("\n===== Extracted Text Start =====\n")
        print(text)
        print("\n===== Extracted Text End =====\n")
    except Exception as exc:
        print(f"Error: {exc}")
        sys.exit(1)