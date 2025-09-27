#!/usr/bin/env python3
"""
Script to run the preserve layout conversion and generate screenshots
"""
import os
import fitz  # PyMuPDF
from preserve_layout import PreserveLayoutConverter

def main():
    # Run the preserve layout conversion
    print("Starting preserve layout conversion...")
    converter = PreserveLayoutConverter()
    converter.convert('testing_pdf.pdf', 'output_translated.pdf')
    print("Conversion completed!")
    
    # Generate screenshots of first two pages
    print("Generating screenshots...")
    doc = fitz.open('output_translated.pdf')
    
    # Page 1 screenshot
    if len(doc) > 0:
        page1 = doc[0]
        mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better quality
        pix = page1.get_pixmap(matrix=mat)
        pix.save('page1_screenshot.png')
        print("Page 1 screenshot saved")
    
    # Page 2 screenshot
    if len(doc) > 1:
        page2 = doc[1]
        mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better quality
        pix = page2.get_pixmap(matrix=mat)
        pix.save('page2_screenshot.png')
        print("Page 2 screenshot saved")
    
    doc.close()
    print("All operations completed!")

if __name__ == "__main__":
    main()
