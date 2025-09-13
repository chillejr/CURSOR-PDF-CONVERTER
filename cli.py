#!/usr/bin/env python3
"""
Unified CLI for the PDF English→Swahili converter.

Subcommands:
- extract:   Extract text from a PDF and print to stdout
- translate: Extract and translate to Swahili, print to stdout
- convert:   Extract, translate, and save to a new PDF (simple text-only)
- preserve:  Translate text while preserving layout and images (PyMuPDF)
- gui:       Launch the Tkinter GUI

Examples:
  python cli.py extract input.pdf
  python cli.py translate input.pdf
  python cli.py convert input.pdf output.pdf
  python cli.py preserve input.pdf output.pdf
  python cli.py gui
"""
from __future__ import annotations

import argparse
import os
import sys

from step1_extract import extract_text_from_pdf
from step2_translate import translate_to_swahili
from step3_create_pdf import create_translated_pdf


def _cmd_extract(args: argparse.Namespace) -> int:
    text = extract_text_from_pdf(args.input)
    if not text.strip():
        print("", end="")
        return 0
    print(text)
    return 0


def _cmd_translate(args: argparse.Namespace) -> int:
    text = extract_text_from_pdf(args.input)
    if not text.strip():
        print("", end="")
        return 0
    sw = translate_to_swahili(text)
    print(sw)
    return 0


def _cmd_convert(args: argparse.Namespace) -> int:
    abs_in = os.path.abspath(args.input)
    output = args.output
    if not output:
        root, _ = os.path.splitext(abs_in)
        output = f"{root}_swahili.pdf"

    text = extract_text_from_pdf(abs_in)
    if not text.strip():
        print("No text extracted from the PDF.")
        return 2
    sw = translate_to_swahili(text)
    create_translated_pdf(sw, output)
    print(f"Saved: {output}")
    return 0


def _cmd_preserve(args: argparse.Namespace) -> int:
    abs_in = os.path.abspath(args.input)
    output = args.output
    if not output:
        root, _ = os.path.splitext(abs_in)
        output = f"{root}_swahili_preserve.pdf"

    from preserve_layout import PreserveLayoutConverter

    converter = PreserveLayoutConverter()
    converter.convert(abs_in, output)
    print(f"Saved (preserve layout): {output}")
    return 0


def _cmd_gui(_: argparse.Namespace) -> int:
    from step4_gui import main as gui_main

    gui_main()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="English→Swahili PDF converter")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_extract = subparsers.add_parser("extract", help="Extract text from PDF to stdout")
    p_extract.add_argument("input", help="Path to input PDF")
    p_extract.set_defaults(func=_cmd_extract)

    p_translate = subparsers.add_parser("translate", help="Extract and translate to Swahili")
    p_translate.add_argument("input", help="Path to input PDF")
    p_translate.set_defaults(func=_cmd_translate)

    p_convert = subparsers.add_parser("convert", help="Extract, translate, and save a new PDF (simple text-only)")
    p_convert.add_argument("input", help="Path to input PDF")
    p_convert.add_argument("output", nargs="?", help="Path to output PDF (default: *_swahili.pdf)")
    p_convert.set_defaults(func=_cmd_convert)

    p_preserve = subparsers.add_parser("preserve", help="Translate while preserving layout and images (PyMuPDF)")
    p_preserve.add_argument("input", help="Path to input PDF")
    p_preserve.add_argument("output", nargs="?", help="Path to output PDF (default: *_swahili_preserve.pdf)")
    p_preserve.set_defaults(func=_cmd_preserve)

    p_gui = subparsers.add_parser("gui", help="Launch GUI app")
    p_gui.set_defaults(func=_cmd_gui)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        return int(args.func(args))
    except FileNotFoundError as exc:
        print(f"Error: {exc}")
        return 1
    except Exception as exc:
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())