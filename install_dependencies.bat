@echo off
echo Installing dependencies...
pip install -r requirements.txt
echo.
echo verifying google-generativeai installation...
pip show google-generativeai
if %errorlevel% neq 0 (
    echo google-generativeai NOT found! Attempting direct install...
    pip install google-generativeai
) else (
    echo google-generativeai is installed.
)
echo.
echo Dependencies installed. You can now close this window and run 'python app.py'.
pause
