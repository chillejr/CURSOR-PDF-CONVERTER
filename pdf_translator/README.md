# English → Swahili PDF Converter

A simple toolchain to:
- extract text from a PDF (`pdfplumber`),
- translate English → Swahili (`googletrans` 4.0.0-rc1),
- write a new text-based PDF (`fpdf2`),
- optionally use a Tkinter GUI.

> Note: This approach handles text-only PDFs. Scanned PDFs (images) require OCR (not included).

## Requirements
- Python 3.10+ recommended
- Ability to create a virtual environment (PEP 668-safe)

## Setup
```bash
cd /workspace/pdf_translator
python3 -m venv .venv           # if not available, install system package e.g. python3-venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

If your system forbids `pip` in the base interpreter (PEP 668), always use the venv.

## CLI Usage
The unified CLI exposes subcommands: `extract`, `translate`, `convert`, `gui`.

```bash
# Show help
python cli.py -h

# 1) Extract text to stdout
python cli.py extract /path/to/input.pdf

# 2) Translate to Swahili and print to stdout
python cli.py translate /path/to/input.pdf

# 3) Convert: extract + translate + save a new PDF
python cli.py convert /path/to/input.pdf /path/to/output.pdf
# Output path is optional; defaults to <input>_swahili.pdf

# 4) GUI (Tkinter)
python cli.py gui
```

## Scripts
- `step1_extract.py`: Extraction using `pdfplumber`.
- `step2_translate.py`: Translation using `googletrans` with chunking + retries.
- `step3_create_pdf.py`: Simple text PDF via `fpdf2` using built-in fonts.
- `step4_gui.py`: Optional Tkinter GUI wrapping the full flow.
- `cli.py`: Single entry point bundling all steps.

## Notes & Limitations
- Translation quality: best-effort via Google Translate web client; may rate-limit.
- Long documents: the CLI chunking mitigates size limits but may be slower.
- Layout preservation: this writes plain text PDFs (no original layout/images).
- Character set: built-in PDF fonts are Latin-1; non‑Latin characters are replaced.

## Troubleshooting
- "externally-managed-environment": create and use a virtualenv, then install requirements.
- Empty extraction: your PDF might be scanned; you’ll need OCR (e.g., Tesseract + pytesseract).
- Tkinter errors on headless servers: GUI requires a desktop environment; use CLI instead.