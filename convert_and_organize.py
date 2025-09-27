#!/usr/bin/env python3
"""
Script to run the preserve layout conversion and generate screenshots
"""
import os
import sys
import fitz  # PyMuPDF

def main():
    try:
        print("Starting preserve layout conversion...")
        
        # Import and run the conversion
        from preserve_layout import PreserveLayoutConverter
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
        else:
            print("Only 1 page found")
        
        doc.close()
        
        # Move files to testing folder
        print("Moving files to testing folder...")
        os.makedirs('testing', exist_ok=True)
        
        if os.path.exists('output_translated.pdf'):
            os.rename('output_translated.pdf', 'testing/testing-v1.pdf')
            print("Moved output_translated.pdf to testing/testing-v1.pdf")
        
        if os.path.exists('page1_screenshot.png'):
            os.rename('page1_screenshot.png', 'testing/testing-v1_p1.png')
            print("Moved page1_screenshot.png to testing/testing-v1_p1.png")
        
        if os.path.exists('page2_screenshot.png'):
            os.rename('page2_screenshot.png', 'testing/testing-v1_p2.png')
            print("Moved page2_screenshot.png to testing/testing-v1_p2.png")
        
        print("All operations completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
