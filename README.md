**English** | [日本語](README.ja.md)

---

<div align="center">

# WebMovieGet

### 🎬 A Clean, Modern & Ad-Free Desktop Video Downloader GUI
**Powered by `yt-dlp` and `FFmpeg` for Windows**

[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![yt-dlp](https://img.shields.io/badge/Powered%20by-yt--dlp-FF0000?logo=youtube&logoColor=white)](https://github.com/yt-dlp/yt-dlp)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows&logoColor=white)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Ad-Free](https://img.shields.io/badge/Ad--Free-100%25-brightgreen.svg)](#)

<p align="center">
  <b>No ads. No trackers. No bloatware.</b><br>
  Just a fast, reliable, and beautifully straightforward tool to download and archive web videos on your PC.
</p>

</div>

---

## 🌟 Why WebMovieGet?

Online web-based video downloaders are notorious for **shady pop-up ads, fake download buttons, and malware warnings**. Meanwhile, the gold standard command-line tool `yt-dlp` can feel intimidating for non-technical users, and recent platform anti-bot measures often throw frustrating `HTTP 403: Forbidden` or `Sign in to confirm you're not a bot` errors.

**WebMovieGet** bridges that gap:
It packages the raw power of `yt-dlp` and `FFmpeg` into a **sleek, intuitive Windows desktop GUI**, complete with automated bot-evasion and cookie-handling out of the box.

---

## ✨ Key Features

* **🛡️ Smart Bot & 403 Verification Bypass**  
  Built-in mobile client spoofing (iOS, Android, mweb) and automated browser cookie integration (Edge, Chrome, Firefox) to smoothly resolve YouTube's *"Sign in to confirm you're not a bot"* challenges.
* **📦 Sequential Queue & Batch Download**  
  Paste multiple video URLs or entire playlist links. The app fetches titles, queues them up, and downloads them one by one in the background.
* **🎥 Crystal Clear 1080p, 4K, 8K & Audio Merging**  
  Leverages embedded `FFmpeg` to seamlessly merge the highest quality adaptive video and audio streams into clean `.mp4` or `.mkv` files.
* **🎵 MP4 Video & MP3 Audio Extraction**  
  Easily toggle between full video (`.mp4`) and audio-only extraction (`.mp3` at 192 kbps) with a single click — perfect for music, podcasts, and offline listening.
* **📊 Real-Time Progress & Speed Metrics**  
  Live download progress bar, current transfer speed, ETA, and real-time console log view so you always know what's happening.
* **⚡ 100% Free & Open Source**  
  Zero monetization, zero telemetry, and zero ads. Your data and downloads remain strictly on your local machine.

---

## 🚀 Quick Start (Setup Guide)

### Prerequisites
* Windows 10 / 11
* **[Python 3.8+](https://www.python.org/downloads/)** installed
  > ⚠️ **IMPORTANT**: Make sure to check **"Add python.exe to PATH"** at the bottom of the Python installer before installing!

---

### Option A: One-Click Automated Setup (Recommended)

1. Clone or download this repository as a `.zip` and extract it.
2. Double-click **`簡単初期設定.bat`** (or `setup.bat`).
3. Press `Y` when prompted. The script will automatically:
   - Install/update `yt-dlp`
   - Download the official `FFmpeg` essentials package
   - Extract and place `ffmpeg.exe` and `ffprobe.exe` directly into the app directory
4. Once completed, you are ready to go!

---

### Option B: Manual Setup

If you prefer to set up dependencies manually:

1. Install `yt-dlp` via command prompt:
   ```cmd
   pip install -U yt-dlp
   ```
2. Download the latest `ffmpeg-release-essentials.zip` from [Gyan.dev](https://www.gyan.dev/ffmpeg/builds/).
3. Extract and copy **`ffmpeg.exe`** and **`ffprobe.exe`** from the `bin/` folder directly into the `WebMovieGet` root folder (next to `WebMovieGet.pyw`).

---

## 🖥️ How to Run

1. Open the project folder.
2. Double-click **`run.bat`** (or run `python WebMovieGet.pyw` in your terminal).
3. The desktop GUI will launch immediately!

```cmd
python WebMovieGet.pyw
```

---

## 🔧 Troubleshooting

### Q: Download fails or throws "Sign in to confirm you're not a bot"
Video platforms frequently update their APIs. Run the following command in Command Prompt to update `yt-dlp` to the latest engine:
```cmd
pip install -U yt-dlp
```
If bot checks persist, enable the **Browser Cookie** setting in the app and select your active browser (Edge / Chrome).

### Q: "FFmpeg not found" or downloaded video is low resolution (360p)
Ensure that `ffmpeg.exe` and `ffprobe.exe` are placed directly in the same folder as `WebMovieGet.pyw`. Without FFmpeg, high-definition streams (1080p+) cannot be muxed with audio.

---

## ☕ Support & Buy Me a Coffee

If WebMovieGet saved you time, protected you from shady downloader websites, or made archiving videos easier, consider supporting its maintenance!

<a href="https://buymeacoffee.com/komikomi" target="_blank">
  <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" width="180">
</a>

---

## ⚖️ Disclaimer & License

* **Disclaimer**: This tool is designed strictly for personal use, educational purposes, and legal archival of public media. Please respect copyright laws and the terms of service of each respective content platform. The author assumes no liability for misuse.
* **License**: Released under the [MIT License](LICENSE).
