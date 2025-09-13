#!/usr/bin/env python3
"""
Step 4 (Optional): Tkinter GUI for selecting a PDF, translating to Swahili, and saving a new PDF.

- Provides a simple UI with a "Select PDF" and "Process" button.
- Saves the translated PDF next to the original with a _swahili.pdf suffix.
"""
from __future__ import annotations

import os
import threading
import traceback
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from step1_extract import extract_text_from_pdf
from step2_translate import translate_to_swahili
from step3_create_pdf import create_translated_pdf


class TranslatorApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("PDF English→Swahili Converter")
        self.root.geometry("480x220")

        self.selected_file: str | None = None

        self.status_var = tk.StringVar(value="Select a file")

        frm = ttk.Frame(root, padding=12)
        frm.pack(fill=tk.BOTH, expand=True)

        self.file_label = ttk.Label(frm, text="No file selected")
        self.file_label.pack(anchor=tk.W, pady=(0, 8))

        btn_row = ttk.Frame(frm)
        btn_row.pack(fill=tk.X, pady=(0, 8))

        self.select_btn = ttk.Button(btn_row, text="Select PDF", command=self.on_select_file)
        self.select_btn.pack(side=tk.LEFT)

        self.process_btn = ttk.Button(btn_row, text="Process", command=self.on_process)
        self.process_btn.pack(side=tk.LEFT, padx=(8, 0))

        self.progress = ttk.Progressbar(frm, mode="indeterminate")
        self.progress.pack(fill=tk.X, pady=(8, 8))

        self.status_label = ttk.Label(frm, textvariable=self.status_var)
        self.status_label.pack(anchor=tk.W)

    def on_select_file(self) -> None:
        path = filedialog.askopenfilename(title="Select PDF", filetypes=[("PDF files", "*.pdf")])
        if path:
            self.selected_file = path
            self.file_label.config(text=os.path.basename(path))
            self.status_var.set("Ready to process")

    def on_process(self) -> None:
        if not self.selected_file or not os.path.isfile(self.selected_file):
            messagebox.showwarning("No file", "Please select a valid PDF file first.")
            return
        # Basic check for Tk availability on headless systems
        try:
            _ = tk.Toplevel(self.root)
            _.destroy()
        except Exception:
            messagebox.showerror("GUI Error", "Tkinter GUI is not available in this environment.")
            return

        self.progress.start(10)
        self.status_var.set("Processing...")
        self.select_btn.config(state=tk.DISABLED)
        self.process_btn.config(state=tk.DISABLED)

        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self) -> None:
        try:
            abs_in = os.path.abspath(self.selected_file)
            root, _ = os.path.splitext(abs_in)
            out_path = f"{root}_swahili.pdf"

            source_text = extract_text_from_pdf(abs_in)
            if not source_text.strip():
                raise RuntimeError("No text extracted from the PDF.")

            sw_text = translate_to_swahili(source_text)
            create_translated_pdf(sw_text, out_path)

            self._on_done(success=True, message=f"Saved: {out_path}")
        except Exception as exc:
            traceback.print_exc()
            self._on_done(success=False, message=str(exc))

    def _on_done(self, success: bool, message: str) -> None:
        def ui_update():
            self.progress.stop()
            self.select_btn.config(state=tk.NORMAL)
            self.process_btn.config(state=tk.NORMAL)
            self.status_var.set("Done!" if success else "Error")
            if success:
                messagebox.showinfo("Completed", message)
            else:
                messagebox.showerror("Failed", message)
        self.root.after(0, ui_update)


def main() -> None:
    root = tk.Tk()
    app = TranslatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()