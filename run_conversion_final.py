#!/usr/bin/env python3
"""
Direct execution script for PDF conversion - no terminal dependency
"""
import os
import sys

def main():
    print("=== PDF Translation and Screenshot Generation ===")
    
    # Check if input file exists
    if not os.path.exists('testing_pdf.pdf'):
        print("ERROR: testing_pdf.pdf not found!")
        return False
    
    print("✓ Input file found: testing_pdf.pdf")
    
    try:
        # Import and run conversion
        from preserve_layout import PreserveLayoutConverter
        converter = PreserveLayoutConverter()
        converter.convert('testing_pdf.pdf', 'output_translated.pdf')
        print("✓ PDF conversion completed")
        
        # Generate screenshots
        import fitz
        doc = fitz.open('output_translated.pdf')
        print(f"✓ PDF opened, {len(doc)} pages")
        
        # Page 1
        page1 = doc[0]
        mat = fitz.Matrix(2.0, 2.0)
        pix = page1.get_pixmap(matrix=mat)
        pix.save('page1_screenshot.png')
        print("✓ Page 1 screenshot saved")
        
        # Page 2 (or duplicate of page 1)
        if len(doc) > 1:
            page2 = doc[1]
            pix = page2.get_pixmap(matrix=mat)
            pix.save('page2_screenshot.png')
            print("✓ Page 2 screenshot saved")
        else:
            pix = page1.get_pixmap(matrix=mat)
            pix.save('page2_screenshot.png')
            print("✓ Page 2 screenshot saved (duplicate of page 1)")
        
        doc.close()
        
        # Move files to testing folder
        os.makedirs('testing', exist_ok=True)
        
        os.rename('output_translated.pdf', 'testing/testing-v1.pdf')
        print("✓ Moved to testing/testing-v1.pdf")
        
        os.rename('page1_screenshot.png', 'testing/testing-v1_p1.png')
        print("✓ Moved to testing/testing-v1_p1.png")
        
        os.rename('page2_screenshot.png', 'testing/testing-v1_p2.png')
        print("✓ Moved to testing/testing-v1_p2.png")
        
        print("\n=== SUCCESS ===")
        print("All files created in testing/ folder:")
        print("  - testing-v1.pdf")
        print("  - testing-v1_p1.png")
        print("  - testing-v1_p2.png")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
