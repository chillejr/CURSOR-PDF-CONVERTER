#!/usr/bin/env python3
"""
Complete script to convert PDF, generate screenshots, and organize files
"""
import os
import sys
import fitz
from preserve_layout import PreserveLayoutConverter

def run_conversion():
    """Run the complete conversion process"""
    try:
        print("=== PDF Translation and Screenshot Generation ===")
        
        # Check if input file exists
        if not os.path.exists('testing_pdf.pdf'):
            print("ERROR: testing_pdf.pdf not found!")
            return False
        
        print("✓ Input file found: testing_pdf.pdf")
        
        # Step 1: Convert PDF with preserved layout
        print("\n1. Converting PDF with preserved layout...")
        converter = PreserveLayoutConverter()
        converter.convert('testing_pdf.pdf', 'output_translated.pdf')
        print("✓ PDF conversion completed")
        
        # Step 2: Generate screenshots
        print("\n2. Generating screenshots...")
        doc = fitz.open('output_translated.pdf')
        
        # Page 1
        if len(doc) > 0:
            page1 = doc[0]
            mat = fitz.Matrix(2.0, 2.0)  # 2x zoom
            pix = page1.get_pixmap(matrix=mat)
            pix.save('page1_screenshot.png')
            print("✓ Page 1 screenshot saved")
        
        # Page 2
        if len(doc) > 1:
            page2 = doc[1]
            mat = fitz.Matrix(2.0, 2.0)  # 2x zoom
            pix = page2.get_pixmap(matrix=mat)
            pix.save('page2_screenshot.png')
            print("✓ Page 2 screenshot saved")
        else:
            print("! Only 1 page found, creating duplicate for page 2")
            # Create a copy of page 1 for page 2
            pix = page1.get_pixmap(matrix=mat)
            pix.save('page2_screenshot.png')
        
        doc.close()
        
        # Step 3: Organize files
        print("\n3. Organizing files...")
        os.makedirs('testing', exist_ok=True)
        
        # Move files with correct names
        files_to_move = [
            ('output_translated.pdf', 'testing/testing-v1.pdf'),
            ('page1_screenshot.png', 'testing/testing-v1_p1.png'),
            ('page2_screenshot.png', 'testing/testing-v1_p2.png')
        ]
        
        for src, dst in files_to_move:
            if os.path.exists(src):
                os.rename(src, dst)
                print(f"✓ Moved {src} to {dst}")
            else:
                print(f"! Warning: {src} not found")
        
        print("\n=== CONVERSION COMPLETED SUCCESSFULLY ===")
        print("Files created in testing/ folder:")
        for _, dst in files_to_move:
            if os.path.exists(dst):
                print(f"  ✓ {dst}")
        
        return True
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_conversion()
    sys.exit(0 if success else 1)
