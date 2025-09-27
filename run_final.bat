@echo off
echo Starting PDF conversion...
python run_conversion_final.py
if %errorlevel% equ 0 (
    echo Conversion completed successfully!
) else (
    echo Conversion failed!
)
pause
