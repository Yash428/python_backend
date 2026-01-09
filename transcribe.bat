@echo off
REM Jitsi Transcription Pipeline - Windows Batch Script
REM Activates virtual environment and runs the pipeline

setlocal enabledelayedexpansion

REM Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo Error: Virtual environment not found
    echo Please run: python -m venv venv
    echo Then: venv\Scripts\activate
    echo Then: pip install -r requirements.txt
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if argument provided
if "%1"=="" (
    echo.
    echo Jitsi Transcription Pipeline
    echo =============================
    echo.
    echo Usage:
    echo   transcribe.bat ^<path\to\meeting.mp4^> [options]
    echo.
    echo Options:
    echo   --model [tiny^|base^|small^|medium^|large]  (default: base)
    echo   --language [en^|es^|fr^|etc]                (default: auto-detect)
    echo   --cleanup                                     (remove temp files)
    echo.
    echo Examples:
    echo   transcribe.bat recordings\meeting.mp4
    echo   transcribe.bat recordings\meeting.mp4 --model small
    echo   transcribe.bat recordings\meeting.mp4 --cleanup
    echo.
    pause
    exit /b 0
)

REM Run pipeline with arguments
python run_pipeline.py %*

REM Keep window open on error
if errorlevel 1 (
    echo.
    echo Transcription failed. Check the error messages above.
    pause
    exit /b 1
)

echo.
echo Transcription complete! Check the transcripts folder.
echo.
pause
