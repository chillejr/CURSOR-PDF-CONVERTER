#!/usr/bin/env python3
"""
Minimal test to verify the conversion works
"""
import os
import sys

def test_conversion():
    print("Testing PDF conversion...")
    
    # Check if input file exists
    if not os.path.exists('testing_pdf.pdf'):
        print("ERROR: testing_pdf.pdf not found!")
        return False
    
    print("✓ Input file found")
    
    try:
        # Import the converter
        from preserve_layout import PreserveLayoutConverter
        print("✓ PreserveLayoutConverter imported")
        
        # Create converter instance
        converter = PreserveLayoutConverter()
        print("✓ Converter instance created")
        
        # Run conversion
        print("Running conversion...")
        converter.convert('testing_pdf.pdf', 'output_translated.pdf')
        print("✓ Conversion completed")
        
        # Check if output was created
        if os.path.exists('output_translated.pdf'):
            print("✓ Output PDF created")
            
            # Generate screenshots
            import fitz
            doc = fitz.open('output_translated.pdf')
            print(f"✓ PDF opened, {len(doc)} pages")
            
            # Page 1
            if len(doc) > 0:
                page1 = doc[0]
                mat = fitz.Matrix(2.0, 2.0)
                pix = page1.get_pixmap(matrix=mat)
                pix.save('page1_screenshot.png')
                print("✓ Page 1 screenshot saved")
            
            # Page 2
            if len(doc) > 1:
                page2 = doc[1]
                mat = fitz.Matrix(2.0, 2.0)
                pix = page2.get_pixmap(matrix=mat)
                pix.save('page2_screenshot.png')
                print("✓ Page 2 screenshot saved")
            else:
                # Create duplicate of page 1
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
        else:
            print("ERROR: Output PDF not created")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_conversion()
    if success:
        print("\nConversion completed successfully!")
    else:
        print("\nConversion failed!")
    sys.exit(0 if success else 1)
