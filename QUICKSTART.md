# Jitsi Transcription Pipeline - Quick Start Guide

## 5-Minute Setup for Windows

### Prerequisites Check
- ✅ Windows 10/11
- ✅ At least 8GB RAM
- ✅ 20GB free disk space (for models and output)

### Installation Steps

#### 1. Install Python 3.10+
```bash
# Visit https://www.python.org/downloads/
# Download Python 3.10 or later
# During installation: ✓ Check "Add Python to PATH"

# Verify installation
python --version
# Should show Python 3.10.x or higher
```

#### 2. Install FFmpeg
```bash
# Download from: https://ffmpeg.org/download.html
# Get the full build (includes ffmpeg and ffprobe)

# Extract to C:\ffmpeg (or your preferred location)

# Add to Windows PATH:
# 1. Press Win + X → System
# 2. Click "Advanced system settings"
# 3. Click "Environment Variables"
# 4. Under System Variables, select "Path" → Edit
# 5. Click "New" and add: C:\ffmpeg\bin
# 6. Click OK, then close and restart terminal

# Verify installation
ffmpeg -version
ffprobe -version
# Both should show version info
```

#### 3. Setup Python Virtual Environment
```bash
cd path\to\jitsi
python -m venv venv
venv\Scripts\activate

# On Linux/macOS:
# source venv/bin/activate
```

#### 4. Install Dependencies
```bash
pip install -r requirements.txt
# This will take 5-10 minutes on first run
# Whisper model (~141MB) downloads automatically on first use
```

#### 5. Test Installation
```bash
# Verify all modules load correctly
python -c "import whisper; print('✓ Whisper OK')"
python -c "from src.utils import setup_logger; print('✓ Project OK')"
python -c "import ffmpeg; print('✓ ffmpeg OK')"
```

### First Transcription

```bash
# Place your MP4 file in recordings/ folder
# Or reference it directly:

python run_pipeline.py recordings/meeting.mp4

# Options:
# --model [tiny|base|small|medium|large]  (default: base)
# --language en                             (default: auto-detect)
# --cleanup                                 (remove temp WAV file)

# Example with options:
python run_pipeline.py recordings/meeting.mp4 --model base --language en --cleanup
```

### Check Output
```
transcripts/
├── meeting.txt              # Plain text
├── meeting.json            # With timestamps
├── meeting.srt             # Subtitle format
├── meeting_timestamps.txt  # Human-readable
└── meeting_markers.edl     # For video editing
```

---

## Troubleshooting

### Issue: "FFmpeg not found"
```bash
# Make sure FFmpeg is in PATH
where ffmpeg
# Should show: C:\ffmpeg\bin\ffmpeg.exe
```

### Issue: "ModuleNotFoundError: No module named 'whisper'"
```bash
# Activate virtual environment and reinstall
venv\Scripts\activate
pip install --upgrade openai-whisper torch
```

### Issue: Slow Processing
```bash
# Use smaller model for faster results
python run_pipeline.py meeting.mp4 --model tiny
```

### Issue: High RAM Usage
```bash
# Unload model between batches
# Or use system memory monitor to track
```

---

## Performance Notes

**Model Size vs Speed:**
- `tiny` (39MB): 1-2 min per hour
- `base` (141MB): 2-3 min per hour ⭐ RECOMMENDED
- `small` (244MB): 4-6 min per hour
- `medium` (769MB): 8-12 min per hour
- `large` (2.9GB): 15-25 min per hour

**RAM Requirements by Model:**
- `tiny`: 2-3 GB
- `base`: 4-5 GB
- `small`: 6-7 GB
- `medium`: 10-12 GB
- `large`: 14+ GB

---

## Next Steps

1. **Read the full README.md** for detailed documentation
2. **Review output formats** in the README
3. **Integrate with your SaaS** using JSON output
4. **Set up batch processing** for multiple files
5. **Consider advanced features** (speaker diarization, etc.)

---

## Support Files

- `README.md` - Complete documentation
- `requirements.txt` - Python dependencies
- `src/` - Source code modules
- `recordings/` - Input MP4 files
- `transcripts/` - Output files

Happy transcribing! 🎙️
