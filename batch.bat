@echo off
REM Batch transcription script for Windows
REM Processes all MP4 files in a directory

setlocal enabledelayedexpansion

REM Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo Error: Virtual environment not found
    echo Please run: python -m venv venv
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if directory provided
if "%1"=="" (
    echo.
    echo Batch Transcription Processor
    echo =============================
    echo.
    echo Usage:
    echo   batch.bat ^<directory^> [options]
    echo.
    echo Options:
    echo   --model [tiny^|base^|small^|medium^|large]  (default: base)
    echo   --cleanup                                     (remove temp files)
    echo.
    echo Examples:
    echo   batch.bat recordings\
    echo   batch.bat recordings\ --model tiny
    echo   batch.bat C:\videos\ --cleanup
    echo.
    pause
    exit /b 0
)

REM Run batch processor
python batch_transcribe.py %*

REM Pause for user to see results
pause
