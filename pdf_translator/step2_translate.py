#!/usr/bin/env python3
"""
Step 2: Translate extracted text to Swahili using deep-translator.

- Reuses extract_text_from_pdf from step 1.
- Adds translate_to_swahili(text) with simple chunking, retries, and concurrency.
- CLI: asks for a PDF path, extracts, translates, and prints the Swahili text.
"""
from __future__ import annotations

import os
import sys
import time
from typing import Iterable, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from deep_translator import GoogleTranslator, MyMemoryTranslator, LibreTranslator

from step1_extract import extract_text_from_pdf


def _chunk_text(text: str, max_chars: int = 2500) -> Iterable[str]:
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


def _provider_try_all(chunk: str) -> str:
    # 1) Google (auto -> sw)
    try:
        res = GoogleTranslator(source="auto", target="sw").translate(chunk)
        if (res or "").strip() and res.strip() != chunk.strip():
            return res
    except Exception:
        pass

    # 2) MyMemory with locale codes (more accepted): en-GB -> sw-KE
    try:
        mm_code = MyMemoryTranslator(source="en-GB", target="sw-KE")
        res = mm_code.translate(chunk)
        if (res or "").strip() and res.strip() != chunk.strip():
            return res
    except Exception:
        pass

    # 3) MyMemory with language names
    try:
        mm_name = MyMemoryTranslator(source="english", target="swahili")
        res = mm_name.translate(chunk)
        if (res or "").strip() and res.strip() != chunk.strip():
            return res
    except Exception:
        pass

    # 4) LibreTranslate (public or user-provided)
    try:
        lt_url = os.getenv("LT_API_URL", "https://libretranslate.de")
        lt = LibreTranslator(source="en", target="sw", api_url=lt_url)
        res = lt.translate(chunk)
        if (res or "").strip() and res.strip() != chunk.strip():
            return res
    except Exception:
        pass

    # Fallback: return original so pipeline continues
    return chunk


def _translate_chunk(chunk: str, translator: GoogleTranslator, max_retries: int, backoff_seconds: float) -> str:
    last_error: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            # First try the preferred translator
            result = translator.translate(chunk)
            if not (result or "").strip():
                raise RuntimeError("Empty translation response")
            if result.strip() == chunk.strip():
                # Drive fallbacks immediately if unchanged
                fb = _provider_try_all(chunk)
                if fb.strip() == chunk.strip():
                    raise RuntimeError("Unchanged translation from providers")
                return fb
            return result
        except Exception as exc:
            last_error = exc
            time.sleep(backoff_seconds * (2 ** (attempt - 1)))
    # Last-chance: try all providers once before giving up
    fb = _provider_try_all(chunk)
    if fb.strip() != chunk.strip():
        return fb
    raise RuntimeError(f"Translation failed after {max_retries} attempts: {last_error}")


def translate_to_swahili(
    text: str,
    max_retries: int = 4,
    backoff_seconds: float = 1.5,
    max_workers: int = 2,
) -> str:
    """Translate English text to Swahili using deep-translator's GoogleTranslator.

    Concurrency speeds up long texts while preserving original order.
    """
    if not text:
        return ""

    translator = GoogleTranslator(source="en", target="sw")

    indexed_chunks: List[Tuple[int, str]] = [(i, c) for i, c in enumerate(_chunk_text(text, max_chars=3000))]
    if not indexed_chunks:
        return ""

    results: List[str] = [""] * len(indexed_chunks)

    # Limit concurrency to avoid rate limiting
    with ThreadPoolExecutor(max_workers=max(1, max_workers)) as executor:
        future_to_index = {
            executor.submit(_translate_chunk, chunk, translator, max_retries, backoff_seconds): idx
            for idx, chunk in indexed_chunks
        }
        for future in as_completed(future_to_index):
            idx = future_to_index[future]
            try:
                results[idx] = future.result()
            except Exception:
                # Fallback: split the chunk by sentences/lines and translate sequentially
                _, original_chunk = indexed_chunks[idx]
                parts: List[str] = []
                for piece in original_chunk.split("\n"):
                    if not piece.strip():
                        parts.append("")
                        continue
                    parts.append(_provider_try_all(piece))
                merged = "\n".join(parts)
                results[idx] = merged if merged.strip() else original_chunk

    return "\n\n".join(results)


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