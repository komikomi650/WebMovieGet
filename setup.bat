@echo off
chcp 65001 > nul
cls
echo ===================================================
echo   WebMovieGet - Automated Setup & Environment Tool
echo ===================================================
echo.
echo This script will automatically set up the required dependencies
echo (yt-dlp and FFmpeg) on your Windows PC.
echo.
echo [Prerequisite Check] Is Python 3.8+ installed on your PC?
echo.
echo * If not yet installed, please install Python from python.org
echo   and ensure "Add python.exe to PATH" is checked before continuing.
echo.
set /p confirm="Ready to start setup? (Y/N): "
if /i "%confirm%" neq "Y" (
    echo Setup cancelled. Exiting...
    pause
    exit /b
)

echo.
echo ---------------------------------------------------
echo 1. Checking Python installation...
echo ---------------------------------------------------
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python was not found in your system PATH.
    echo.
    echo Possible causes:
    echo 1. Python is not installed yet.
    echo 2. "Add python.exe to PATH" was not checked during Python installation.
    echo.
    echo Please install Python from https://www.python.org/downloads/
    echo and re-run this setup script.
    echo.
    pause
    exit /b
)
python --version
echo Python detected successfully.
echo.

echo ---------------------------------------------------
echo 2. Installing / Updating yt-dlp...
echo ---------------------------------------------------
python -m pip install --upgrade pip
python -m pip install -U yt-dlp
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install yt-dlp.
    echo Please check your internet connection and try again.
    echo.
    pause
    exit /b
)
echo yt-dlp is ready.
echo.

echo ---------------------------------------------------
echo 3. Setting up FFmpeg (High Definition video muxing)...
echo ---------------------------------------------------
if exist ffmpeg.exe (
    echo ffmpeg.exe already exists in the current directory. Skipping download.
) else (
    echo Downloading FFmpeg package (~100MB) from official Gyan.dev builds...
    echo * Depending on your connection, this may take 1-3 minutes. Please wait...
    
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip' -OutFile 'ffmpeg.zip'"
    
    if not exist ffmpeg.zip (
        echo [ERROR] Download failed. Please check your internet connection.
        pause
        exit /b
    )
    
    echo Download complete. Extracting FFmpeg binaries...
    powershell -Command "Expand-Archive -Path 'ffmpeg.zip' -DestinationPath 'ffmpeg_temp' -Force"
    powershell -Command "Copy-Item 'ffmpeg_temp\ffmpeg-*\bin\ffmpeg.exe' '.\ffmpeg.exe' -Force"
    powershell -Command "Copy-Item 'ffmpeg_temp\ffmpeg-*\bin\ffprobe.exe' '.\ffprobe.exe' -Force"
    
    echo Cleaning up temporary files...
    del ffmpeg.zip
    rmdir /s /q ffmpeg_temp
    
    echo FFmpeg binaries placed successfully.
)
echo.

echo ===================================================
echo   Setup completed successfully!
echo   You can now launch the app by double-clicking "run.bat"
echo ===================================================
echo.
pause
