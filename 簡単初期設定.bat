@echo off
chcp 65001 > nul
cls
echo ===================================================
echo   YouTube動画保存ツール 初期設定 (簡単セットアップ)
echo ===================================================
echo.
echo このプログラムは、動画保存に必要なツールを自動でダウンロードし、
echo 別のパソコンでもすぐに使えるように準備します。
echo.
echo [確認] パソコンに「Python」はインストールされていますか？
echo.
echo ※ まだインストールしていない場合は、先にREADME.mdの手順1を参考に
echo    Pythonをインストールしてからこのファイルを実行してください。
echo.
set /p confirm="準備はよろしいですか？ (Y/N): "
if /i "%confirm%" neq "Y" (
    echo キャンセルしました。画面を閉じます。
    pause
    exit /b
)

echo.
echo ---------------------------------------------------
echo 1. Python の状態を確認しています...
echo ---------------------------------------------------
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 【エラー】Python が見つかりませんでした。
    echo.
    echo 理由として以下の可能性があります：
    echo 1. Python がまだインストールされていない
    echo 2. インストール時に「Add python.exe to PATH」のチェックを忘れた
    echo.
    echo README.md の手順1を再度確認し、Pythonをインストールしてから再実行してください。
    echo.
    pause
    exit /b
)
python --version
echo Python は正常に認識されています。
echo.

echo ---------------------------------------------------
echo 2. 動画ダウンロード部品 (yt-dlp) を準備しています...
echo ---------------------------------------------------
python -m pip install --upgrade pip
python -m pip install yt-dlp
if %errorlevel% neq 0 (
    echo 【エラー】yt-dlp のインストールに失敗しました。
    echo インターネット接続を確認し、もう一度実行してください。
    echo.
    pause
    exit /b
)
echo yt-dlp の準備が完了しました。
echo.

echo ---------------------------------------------------
echo 3. 高画質化ツール (FFmpeg) を自動ダウンロードしています...
echo ---------------------------------------------------
if exist ffmpeg.exe (
    echo すでにフォルダ内に ffmpeg.exe が配置されているため、ダウンロードをスキップします。
) else (
    echo インターネットから必要なファイル（約100MB）をダウンロードしています。
    echo ※回線の速度によって1〜3分程度かかります。この画面を閉じずにしばらくお待ちください...
    
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip' -OutFile 'ffmpeg.zip'"
    
    if not exist ffmpeg.zip (
        echo 【エラー】ダウンロードに失敗しました。インターネット接続を確認してください。
        pause
        exit /b
    )
    
    echo ダウンロード完了。ファイルを解凍して配置しています...
    powershell -Command "Expand-Archive -Path 'ffmpeg.zip' -DestinationPath 'ffmpeg_temp' -Force"
    powershell -Command "Copy-Item 'ffmpeg_temp\ffmpeg-*\bin\ffmpeg.exe' '.\ffmpeg.exe' -Force"
    powershell -Command "Copy-Item 'ffmpeg_temp\ffmpeg-*\bin\ffprobe.exe' '.\ffprobe.exe' -Force"
    
    echo 不要になった一時ファイルを削除しています...
    del ffmpeg.zip
    rmdir /s /q ffmpeg_temp
    
    echo FFmpeg の配置が完了しました。
)
echo.

echo ===================================================
echo   初期設定がすべて完了しました！
echo   今後は「run.bat」をダブルクリックしてツールを起動できます。
echo ===================================================
echo.
pause
