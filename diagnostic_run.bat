@echo off
setlocal enabledelayedexpansion

cd /d "E:\py learn\adversarial_attack_DRL\2024_dvcvqkd"

echo === STEP 1: Running python extract_pdf_data.py ===
python extract_pdf_data.py 2>&1

echo.
echo === STEP 2: File sizes ===
echo.actual_pdf_extraction_result.json size:
if exist "actual_pdf_extraction_result.json" (
    for %%A in (actual_pdf_extraction_result.json) do echo %%~zA bytes
) else (
    echo FILE NOT FOUND
)

echo.actual_pdf_extraction_log.txt size:
if exist "actual_pdf_extraction_log.txt" (
    for %%A in (actual_pdf_extraction_log.txt) do echo %%~zA bytes
) else (
    echo FILE NOT FOUND
)

echo.
echo === STEP 3: Confirming file existence ===
if exist "extract_pdf_data.py" (
    echo extract_pdf_data.py: EXISTS
) else (
    echo extract_pdf_data.py: NOT FOUND
)

if exist "run_fresh_extraction.bat" (
    echo run_fresh_extraction.bat: EXISTS
) else (
    echo run_fresh_extraction.bat: NOT FOUND
)

echo.
echo === STEP 4: Deleting files ===
del /f /q extract_pdf_data.py 2>&1
del /f /q run_fresh_extraction.bat 2>&1

echo.
echo === STEP 5: Verifying deletion ===
if exist "extract_pdf_data.py" (
    echo extract_pdf_data.py: STILL EXISTS
) else (
    echo extract_pdf_data.py: DELETED SUCCESSFULLY
)

if exist "run_fresh_extraction.bat" (
    echo run_fresh_extraction.bat: STILL EXISTS
) else (
    echo run_fresh_extraction.bat: DELETED SUCCESSFULLY
)

pause
