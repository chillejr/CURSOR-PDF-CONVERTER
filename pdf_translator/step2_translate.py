#!/usr/bin/env python3
"""
Step 2: Translate extracted text to Swahili using deep-translator.

- Reuses extract_text_from_pdf from step 1.
- Adds translate_to_swahili(text) with simple chunking and retries.
- CLI: asks for a PDF path, extracts, translates, and prints the Swahili text.
"""
from __future__ import annotations

import os
import sys
import time
from typing import Iterable, List

from deep_translator import GoogleTranslator

from step1_extract import extract_text_from_pdf


def _chunk_text(text: str, max_chars: int = 4500) -> Iterable[str]:
    """Yield chunks of text no longer than max_chars, splitting on paragraph/sentence boundaries.

    This is a heuristic to avoid hitting size limits or timeouts.
    """
    if not text:
        return []

    paragraphs: List[str] = text.split("\n\n")
    buffer: List[str] = []
    current_len = 0

    def flush_buffer():
        if buffer:
            yield "\n\n".join(buffer)
            buffer.clear()

    for paragraph in paragraphs:
        if len(paragraph) > max_chars:
            # Further split long paragraph by sentences.
            sentences = paragraph.split(". ")
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                if current_len + len(sentence) + 1 > max_chars:
                    # flush
                    for chunk in flush_buffer():
                        yield chunk
                    buffer.append(sentence)
                    current_len = len(sentence)
                else:
                    buffer.append(sentence)
                    current_len += len(sentence) + 1
            # paragraph boundary -> flush
            for chunk in flush_buffer():
                yield chunk
            current_len = 0
        else:
            if current_len + len(paragraph) + 2 > max_chars:
                for chunk in flush_buffer():
                    yield chunk
                buffer.append(paragraph)
                current_len = len(paragraph)
            else:
                buffer.append(paragraph)
                current_len += len(paragraph) + 2

    for chunk in flush_buffer():
        yield chunk


def translate_to_swahili(text: str, max_retries: int = 3, backoff_seconds: float = 1.5) -> str:
    """Translate English text to Swahili using deep-translator's GoogleTranslator.

    Handles chunking and simple retries for transient failures.
    """
    if not text:
        return ""

    translator = GoogleTranslator(source="auto", target="sw")
    translated_chunks: List[str] = []

    for chunk in _chunk_text(text, max_chars=4500):
        last_error: Exception | None = None
        for attempt in range(1, max_retries + 1):
            try:
                translated_chunks.append(translator.translate(chunk))
                last_error = None
                break
            except Exception as exc:
                last_error = exc
                time.sleep(backoff_seconds * (2 ** (attempt - 1)))
        if last_error is not None:
            raise RuntimeError(f"Translation failed after {max_retries} attempts: {last_error}")

    return "\n\n".join(translated_chunks)


def _prompt_path_from_stdin() -> str:
    try:
        path = input("Enter the path to the PDF file: ").strip()
    except EOFError:
        path = ""
    return path


if __name__ == "__main__":
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else _prompt_path_from_stdin()
    if not pdf_path:
        print("No PDF path provided.")
        sys.exit(1)

    try:
        source_text = extract_text_from_pdf(pdf_path)
        if not source_text.strip():
            print("No text extracted from the PDF.")
            sys.exit(0)
        sw_text = translate_to_swahili(source_text)
        print("\n===== Swahili Translation Start =====\n")
        print(sw_text)
        print("\n===== Swahili Translation End =====\n")
    except Exception as exc:
        print(f"Error: {exc}")
        sys.exit(1)