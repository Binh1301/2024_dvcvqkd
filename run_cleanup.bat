@echo off
cd /d "E:\py learn\adversarial_attack_DRL\2024_dvcvqkd"
python cleanup_task_files.py
if %errorlevel% equ 0 (
  echo Cleanup completed successfully
  del cleanup_task_files.py
  if exist actual_pdf_extraction_result.json (
    echo actual_pdf_extraction_result.json exists
  ) else (
    echo actual_pdf_extraction_result.json NOT FOUND
  )
  if exist actual_pdf_extraction_log.txt (
    echo actual_pdf_extraction_log.txt exists
  ) else (
    echo actual_pdf_extraction_log.txt NOT FOUND
  )
) else (
  echo Cleanup failed with error code %errorlevel%
)
