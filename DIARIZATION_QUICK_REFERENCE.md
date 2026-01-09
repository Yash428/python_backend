# Speaker Diarization - Quick Reference

## One-Line Summary
**Speaker diarization identifies WHO spoke WHEN in your audio files.**

## Installation (One-Time Setup)

```bash
# 1. Install packages (already in requirements.txt)
pip install -r requirements.txt

# 2. Setup authentication (interactive)
python setup_diarization.py
```

## Basic Commands

```bash
# Transcribe WITH speaker identification (default)
python run_pipeline.py recordings/meeting.mp4

# Transcribe WITHOUT speaker ID (faster)
python run_pipeline.py recordings/meeting.mp4 --no-diarization

# Check setup status
python setup_diarization.py --verify
```

## Output Example

**Original output:**
```
Hello, thank you for joining the meeting.
Happy to be here!
Let's discuss the quarterly results.
```

**With diarization:**
```
00:00:05 - SPEAKER_00: Hello, thank you for joining the meeting.
00:00:10 - SPEAKER_01: Happy to be here!
00:00:15 - SPEAKER_00: Let's discuss the quarterly results.
```

## New Output Files

When diarization is enabled, you get 3 new files:

| File | Format | Best For |
|------|--------|----------|
| `{name}_with_speakers.json` | JSON | Machine processing, detailed data |
| `{name}_with_speakers.srt` | Subtitles | Video editing, synchronization |
| `{name}_speaker_timeline.txt` | Text | Reading, humans, documentation |

## Troubleshooting

| Error | Solution |
|-------|----------|
| "HuggingFace token not found" | Run: `python setup_diarization.py` |
| "License not accepted" | Visit model page, click "Agree and access" |
| "No module pyannote" | Run: `pip install pyannote.audio` |
| Out of memory | Run with: `--no-diarization` |
| Slow processing | Use: `--no-diarization` (2-3x faster) |

## Features

- ✅ Automatic speaker detection
- ✅ Handles 2-10+ speakers
- ✅ Works with various languages
- ✅ GPU acceleration (auto-detects)
- ✅ Graceful fallback to CPU

## Processing Time

For 1 hour of audio:
- Transcription: ~1 min
- Diarization: ~2-3 min
- **Total: ~3-4 min**

Disable with `--no-diarization` for faster (transcription only) processing.

## System Needs

- Python 3.10+
- 4GB RAM minimum
- ~1GB disk space for models
- GPU recommended (NVIDIA RTX 3060+) but not required

## What You Can't Do (Yet)

❌ Identify speaker names (gets "SPEAKER_00", "SPEAKER_01")  
❌ Distinguish between very similar voices  
❌ Handle extremely noisy environments  

To get speaker names, you'd need a separate speaker identification model or manual mapping.

## Common Scenarios

### "I just want text, no speaker info"
```bash
python run_pipeline.py recordings/meeting.mp4 --no-diarization
```

### "I need speaker info for a 2-person meeting"
```bash
python run_pipeline.py recordings/meeting.mp4
```
Default settings work great for 2-3 speakers.

### "I need faster processing"
```bash
python run_pipeline.py recordings/meeting.mp4 --model tiny --no-diarization
```
Use smaller Whisper model + skip diarization.

### "I have a GPU and want best quality"
```bash
python run_pipeline.py recordings/meeting.mp4 --model large
```
GPU is auto-detected. Both transcription and diarization accelerate.

## Python Usage

```python
from pathlib import Path
from run_pipeline import JitsiTranscriptionPipeline

pipeline = JitsiTranscriptionPipeline()

# With diarization (default)
pipeline.run(Path("recordings/meeting.mp4"))

# Without diarization
pipeline.run(Path("recordings/meeting.mp4"), enable_diarization=False)

# With options
pipeline.run(
    Path("recordings/meeting.mp4"),
    model="small",
    language="en",
    enable_diarization=True,
    cleanup_wav=True
)
```

## Technical Details

**Models used:**
- Transcription: OpenAI Whisper (base, small, medium, large)
- Diarization: Pyannote.audio 3.1

**How it works:**
1. Whisper transcribes audio → text with timestamps
2. Pyannote identifies speaker segments (who spoke when)
3. Pipeline merges them → speaker labels on each segment

**Accuracy:**
- 85-95% accurate on clear audio
- Best with 2-3 distinct speakers
- Degrades with noise or heavily overlapping speech

## For More Info

- Full guide: [DIARIZATION_GUIDE.md](DIARIZATION_GUIDE.md)
- Implementation details: [src/diarize.py](src/diarize.py)
- Setup script: [setup_diarization.py](setup_diarization.py)

---

**Still stuck?** Check the full guide:
```bash
cat DIARIZATION_GUIDE.md
```
