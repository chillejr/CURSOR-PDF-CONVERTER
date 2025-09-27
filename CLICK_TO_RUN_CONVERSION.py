#!/usr/bin/env python3
"""
Manual execution of PDF conversion
This script can be run by double-clicking in Windows Explorer
"""

def run_conversion():
    try:
        print("Starting PDF conversion...")
        
        import os
        import sys
        import fitz
        from preserve_layout import PreserveLayoutConverter
        
        # Check if input exists
        if not os.path.exists('testing_pdf.pdf'):
            print("ERROR: testing_pdf.pdf not found!")
            input("Press Enter to exit...")
            return
        
        print("✓ Found testing_pdf.pdf")
        
        # Run conversion
        converter = PreserveLayoutConverter()
        converter.convert('testing_pdf.pdf', 'output_translated.pdf')
        print("✓ PDF conversion completed")
        
        # Generate screenshots
        doc = fitz.open('output_translated.pdf')
        print(f"✓ PDF opened ({len(doc)} pages)")
        
        # Page 1
        page1 = doc[0]
        mat = fitz.Matrix(2.0, 2.0)
        pix = page1.get_pixmap(matrix=mat)
        pix.save('page1_screenshot.png')
        print("✓ Page 1 screenshot saved")
        
        # Page 2
        if len(doc) > 1:
            page2 = doc[1]
            pix = page2.get_pixmap(matrix=mat)
            pix.save('page2_screenshot.png')
            print("✓ Page 2 screenshot saved")
        else:
            pix = page1.get_pixmap(matrix=mat)
            pix.save('page2_screenshot.png')
            print("✓ Page 2 screenshot saved (duplicate)")
        
        doc.close()
        
        # Organize files
        os.makedirs('testing', exist_ok=True)
        
        # Move files
        if os.path.exists('output_translated.pdf'):
            os.rename('output_translated.pdf', 'testing/testing-v1.pdf')
            print("✓ Moved to testing/testing-v1.pdf")
        
        if os.path.exists('page1_screenshot.png'):
            os.rename('page1_screenshot.png', 'testing/testing-v1_p1.png')
            print("✓ Moved to testing/testing-v1_p1.png")
        
        if os.path.exists('page2_screenshot.png'):
            os.rename('page2_screenshot.png', 'testing/testing-v1_p2.png')
            print("✓ Moved to testing/testing-v1_p2.png")
        
        print("\n✅ SUCCESS! Files created in testing/ folder:")
        print("  📄 testing-v1.pdf")
        print("  🖼️ testing-v1_p1.png")
        print("  🖼️ testing-v1_p2.png")
        
        input("\nConversion completed! Press Enter to exit...")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")

if __name__ == "__main__":
    run_conversion()
