@echo off
echo Starting PDF conversion...
python -c "from preserve_layout import PreserveLayoutConverter; converter = PreserveLayoutConverter(); converter.convert('testing_pdf.pdf', 'output_translated.pdf'); print('Conversion completed')"
echo Generating screenshots...
python -c "import fitz; doc = fitz.open('output_translated.pdf'); page1 = doc[0]; mat = fitz.Matrix(2.0, 2.0); pix = page1.get_pixmap(matrix=mat); pix.save('page1_screenshot.png'); print('Page 1 saved'); page2 = doc[1] if len(doc) > 1 else None; pix2 = page2.get_pixmap(matrix=mat) if page2 else None; pix2.save('page2_screenshot.png') if pix2 else None; print('Page 2 saved') if pix2 else print('Only 1 page'); doc.close()"
echo Moving files to testing folder...
move output_translated.pdf testing\testing-v1.pdf
move page1_screenshot.png testing\testing-v1_p1.png
move page2_screenshot.png testing\testing-v1_p2.png
echo All files moved to testing folder!
pause
