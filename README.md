# Jitsi Meeting Transcription Pipeline

Professional-grade, offline transcription system for Jitsi Meet recordings. Converts MP4 video files to accurate text transcripts with segment-level timestamps, perfect for SaaS products and enterprise deployments.

## Features

✅ **Offline Transcription** - All processing happens locally, no API calls  
✅ **Fast & Accurate** - Uses OpenAI Whisper with automatic language detection  
✅ **Speaker Diarization** - Identifies who spoke when (NEW!)  
✅ **Multiple Output Formats** - Text, JSON with timestamps, SRT subtitles  
✅ **Speaker-Labeled Transcripts** - Know who said what in multi-speaker meetings  
✅ **Windows Compatible** - Optimized for Windows CPU (fp16 disabled)  
✅ **Production Ready** - Clean, modular, well-documented code  
✅ **SaaS Ready** - Easily integrate segment timestamps into your platform  
✅ **Extensible** - Foundation for advanced features  

## System Requirements

- **OS**: Windows 10/11 (or Linux/macOS)
- **Python**: 3.10 or higher
- **FFmpeg**: Required for audio extraction
- **RAM**: 8GB minimum (16GB+ recommended for large files)
- **CPU**: Any modern processor (GPU optional)

## Installation

### Step 1: Install Python 3.10+

Download from [python.org](https://www.python.org/downloads/) and ensure "Add Python to PATH" is checked during installation.

Verify installation:
```bash
python --version
```

### Step 2: Install FFmpeg

**Windows:**
1. Download from [ffmpeg.org](https://ffmpeg.org/download.html)
2. Extract to a folder (e.g., `C:\ffmpeg`)
3. Add to PATH:
   - Press `Win + X` → System → Advanced system settings
   - Click "Environment Variables"
   - Under "System variables", select "Path" → Edit
   - Add the FFmpeg bin folder (e.g., `C:\ffmpeg\bin`)
   - Click OK and restart your terminal

Verify installation:
```bash
ffmpeg -version
ffprobe -version
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

### Step 3: Clone or Download This Project

```bash
git clone <repository-url>
cd jitsi
```

Or download and extract the ZIP file.

### Step 4: Create Virtual Environment (Recommended)

```bash
python -m venv venv
venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # Linux/macOS
```

### Step 5: Install Python Dependencies

```bash
pip install -r requirements.txt
```

**Note**: The first time you run the transcription, Whisper will download the model (~141MB for 'base' model). This happens automatically.

## Usage

### Basic Usage (With Speaker Diarization)

```bash
python run_pipeline.py recordings/meeting.mp4
```

This will:
1. Extract audio from video
2. Transcribe audio to text
3. **Identify speakers** (who said what)
4. Generate multiple output formats

### Without Speaker Diarization (Faster)

```bash
python run_pipeline.py recordings/meeting.mp4 --no-diarization
```

Use this if you only need the transcript without speaker labels (2-3x faster).

### With Options

```bash
# Specify language (auto-detect by default)
python run_pipeline.py recordings/meeting.mp4 --language en

# Use different model (tiny, base, small, medium, large)
python run_pipeline.py recordings/meeting.mp4 --model small

# Clean up temporary WAV file after completion
python run_pipeline.py recordings/meeting.mp4 --cleanup

# Combine options
python run_pipeline.py recordings/meeting.mp4 --model base --language en --cleanup

# Disable diarization for faster processing
python run_pipeline.py recordings/meeting.mp4 --no-diarization --model small
```

### First Time Setup for Speaker Diarization

Run this once to authenticate with HuggingFace:

```bash
python setup_diarization.py
```

This will guide you through:
1. Creating a free HuggingFace account (if needed)
2. Generating an authentication token
3. Accepting the model license
4. Saving credentials for future use

### Using as a Python Module

```python
from pathlib import Path
from run_pipeline import JitsiTranscriptionPipeline

# Create pipeline
pipeline = JitsiTranscriptionPipeline()

# Run transcription with diarization (default)
success = pipeline.run(
    input_mp4=Path("recordings/meeting.mp4"),
    model="base",
    language="en",
    cleanup_wav=True,
    enable_diarization=True  # Include speaker identification
)

if success:
    print("Transcription complete!")
```

## Output Files

### Without Diarization
- `{name}.txt` - Plain text transcript
- `{name}.json` - JSON with timestamps
- `{name}.srt` - SRT subtitle format
- `{name}_timestamps.txt` - Timestamped timeline
- `{name}_markers.edl` - Video editing markers

### With Diarization (Additional Files)
- `{name}_with_speakers.json` - **Transcript with speaker labels**
- `{name}_with_speakers.srt` - **Subtitles with speaker names**
- `{name}_speaker_timeline.txt` - **Human-readable speaker timeline**

### Example Speaker Timeline Output

```
00:00:05 - SPEAKER_00: Hello, thank you for joining the meeting.
00:00:10 - SPEAKER_01: Happy to be here!
00:00:15 - SPEAKER_00: Let's discuss the quarterly results.
```

## Speaker Diarization

For detailed information on speaker diarization, see [DIARIZATION_GUIDE.md](DIARIZATION_GUIDE.md).

**Key points:**
- ✅ Automatic speaker detection
- ✅ Works in multiple languages
- ✅ GPU-accelerated (falls back to CPU)
- ✅ Identifies speaker boundaries and changes
- ✅ Generates speaker-labeled transcripts

**Typical processing time:**
- Transcription: ~1 minute per hour
- Diarization: ~2-3 minutes per hour
- Total: ~3-4 minutes per hour

To skip diarization and process faster:
```bash
python run_pipeline.py recordings/meeting.mp4 --no-diarization
```

## Project Structure

```
jitsi/
├── recordings/              # Store MP4 files here
│   └── meeting.mp4
│
├── transcripts/            # Output files generated here
│   ├── meeting.txt
│   ├── meeting.json
│   ├── meeting_with_speakers.json    # NEW: With speaker labels
│   ├── meeting_with_speakers.srt     # NEW: With speaker names
│   ├── meeting_speaker_timeline.txt  # NEW: Speaker timeline
│   ├── meeting.srt
│   ├── meeting_timestamps.txt
│   └── meeting_markers.edl
│
├── src/
│   ├── __init__.py
│   ├── diarize.py           # NEW: Speaker diarization module
│   ├── transcribe.py
│   ├── extract_audio.py
│   ├── segment.py
│   └── utils.py
│
├── setup_diarization.py     # NEW: HuggingFace authentication
├── DIARIZATION_GUIDE.md     # NEW: Complete diarization docs
├── run_pipeline.py
│   ├── extract_audio.py    # MP4 → WAV audio extraction
│   ├── transcribe.py       # Whisper transcription
│   ├── segment.py          # Timestamp generation
│   └── utils.py            # Helper functions
│
├── run_pipeline.py         # Main orchestrator
├── requirements.txt        # Dependencies
└── README.md              # This file
```

## Output Files

### 1. **meeting.txt** - Plain Text Transcript
Full transcription without timestamps. Best for:
- Quick reading
- Searching and archiving
- Export to documents

```
This is the full meeting transcript. All the audio content
has been converted to text format. Multiple lines of dialogue...
```

### 2. **meeting.json** - Structured Data with Timestamps
Segment-level data with precise timestamps. Best for:
- Integration with SaaS platforms
- Building searchable interfaces
- Data analysis

```json
{
  "metadata": {
    "model": "base",
    "language": "en",
    "duration": 1234.5,
    "processing_time": 45.2
  },
  "segments": [
    {
      "id": 0,
      "start": 0.0,
      "end": 2.5,
      "text": "Good morning everyone, welcome to today's meeting.",
      "confidence": 0.95
    },
    {
      "id": 1,
      "start": 2.5,
      "end": 5.8,
      "text": "Let's start with the agenda.",
      "confidence": 0.92
    }
  ]
}
```

### 3. **meeting.srt** - SRT Subtitle Format
For use in video players and editing software:

```
1
00:00:00.000 --> 00:00:02.500
Good morning everyone, welcome to today's meeting.

2
00:00:02.500 --> 00:00:05.800
Let's start with the agenda.
```

### 4. **meeting_timestamps.txt** - Human-Readable Timeline

```
DETAILED TRANSCRIPT
================================================================================
[00:00:00.000 - 00:00:02.500] Good morning everyone, welcome to today's meeting.
[00:00:02.500 - 00:00:05.800] Let's start with the agenda.
[00:00:05.800 - 00:00:08.200] First item: Q3 results review

TIMELINE VIEW
================================================================================
00:00:00.000 | Good morning everyone, welcome to today's meeting.
00:00:02.500 | Let's start with the agenda.
00:00:05.800 | First item: Q3 results review
```

### 5. **meeting.srt** - Video Subtitle Format
Ready to embed in video or use with video players.

### 6. **meeting_markers.edl** - EDL Markers
For video editing software (Premiere, Final Cut, etc.):

```
# EDL Segment Markers
001  SEG_0001     V     C        00:00:00:00    00:00:02:50
* TEXT: Good morning everyone, welcome to today's meeting.
```

## Whisper Model Options

| Model | Size | Speed | Accuracy | Best For |
|-------|------|-------|----------|----------|
| tiny | 39M | Very Fast | Good | Quick tests, low-resource |
| base | 141M | Fast | Very Good | **Production standard** |
| small | 244M | Medium | Excellent | High accuracy needed |
| medium | 769M | Slow | Excellent | Multilingual, complex audio |
| large | 2.9GB | Very Slow | Best | Maximum accuracy |

**Recommendation**: Start with `base` model. Use `small` if accuracy is critical.

## Language Support

Whisper automatically detects language from audio. Supported languages include:

English, Spanish, French, German, Italian, Portuguese, Dutch, Russian, Chinese (Simplified/Traditional), Japanese, Korean, Turkish, Polish, Swedish, and 80+ more languages.

To specify language:
```bash
python run_pipeline.py recordings/meeting.mp4 --language en
```

Language codes: `en`, `es`, `fr`, `de`, `it`, `pt`, `nl`, `ru`, `zh`, `ja`, `ko`, etc.

## Performance & Timing

**Typical processing times (base model, Windows 10):**

| Video Duration | Processing Time | Notes |
|---|---|---|
| 5 minutes | 2-3 minutes | Fast |
| 30 minutes | 10-15 minutes | Standard meeting |
| 1 hour | 25-35 minutes | Full session |
| 2 hours | 50-70 minutes | Long conference |

*Times vary by hardware. CPU-only processing is slower than GPU, but more universal.*

## Architecture & Design

### Data Flow

```
MP4 Video
    ↓
[extract_audio.py] → Extract mono 16kHz WAV
    ↓
WAV Audio
    ↓
[transcribe.py] → Run Whisper model locally
    ↓
Transcription Result (JSON)
    ↓
[segment.py] → Generate timestamps & formats
    ↓
Output: TXT + JSON + SRT + Timestamps + Markers
```

### Module Overview

**extract_audio.py**
- FFmpeg wrapper for audio extraction
- Validates FFmpeg installation
- Converts MP4 → mono 16kHz WAV
- Error handling and logging

**transcribe.py**
- Loads Whisper model locally
- Runs transcription (fp16 disabled for Windows)
- Auto-language detection
- Generates multiple output formats

**segment.py**
- Processes Whisper segments
- Creates timestamped views
- Exports for video editing software
- Keyword search capabilities

**utils.py**
- Time conversion utilities
- File operations
- Logging setup
- Safe filename generation

**run_pipeline.py**
- Orchestrates entire workflow
- CLI interface
- Progress logging
- Error handling and recovery

## Troubleshooting

### "FFmpeg not found"
**Solution**: Install FFmpeg and add to PATH (see Installation section)

```bash
# Verify FFmpeg
ffmpeg -version
```

### "No module named 'whisper'"
**Solution**: Install Python dependencies

```bash
pip install -r requirements.txt
```

### "CUDA out of memory" (GPU users)
**Solution**: Use CPU mode (default) or smaller model

```bash
python run_pipeline.py recordings/meeting.mp4 --model tiny
```

### Slow transcription
**Solution**: Use smaller model or check system resources

```bash
# Check RAM usage
python run_pipeline.py recordings/meeting.mp4 --model tiny

# Monitor CPU
# Task Manager → Performance tab
```

### "UnicodeDecodeError" with non-English audio
**Solution**: Specify language explicitly

```bash
python run_pipeline.py recordings/meeting.mp4 --language es  # Spanish
```

## Integration Examples

### 1. SaaS Platform Integration

```python
from pathlib import Path
import json
from run_pipeline import JitsiTranscriptionPipeline

# Process recording
pipeline = JitsiTranscriptionPipeline()
pipeline.run(Path("meeting.mp4"))

# Load results
with open("transcripts/meeting.json") as f:
    transcript_data = json.load(f)

# Store in database
for segment in transcript_data["segments"]:
    db.Transcript.create(
        start_time=segment["start"],
        end_time=segment["end"],
        text=segment["text"],
        confidence=segment["confidence"]
    )
```

### 2. Batch Processing

```bash
# Create script: process_all.bat
for %%F in (recordings\*.mp4) do (
    python run_pipeline.py "%%F" --cleanup
)
```

### 3. Web Service Integration

```python
from fastapi import FastAPI, UploadFile
from pathlib import Path

app = FastAPI()

@app.post("/transcribe/")
async def transcribe_upload(file: UploadFile):
    # Save uploaded file
    video_path = Path(f"recordings/{file.filename}")
    with open(video_path, "wb") as f:
        f.write(await file.read())
    
    # Process
    pipeline = JitsiTranscriptionPipeline()
    success = pipeline.run(video_path, cleanup_wav=True)
    
    # Return results
    if success:
        with open(f"transcripts/{video_path.stem}.json") as f:
            return json.load(f)
```

## Future Enhancements

**Currently Available:**
- ✅ Offline transcription
- ✅ Multi-format output
- ✅ Auto language detection
- ✅ Segment timestamps
- ✅ Windows optimization

**Planned Features:**
- 🔄 Speaker diarization (identify who spoke when)
- 🔄 Named entity recognition (extract names, topics)
- 🔄 Sentiment analysis per segment
- 🔄 Custom vocabulary/domain terms
- 🔄 Multi-audio stream support
- 🔄 Batch processing UI
- 🔄 REST API server

## License

[Specify your license here - MIT, Apache 2.0, GPL, Proprietary, etc.]

## Support

For issues or questions:
1. Check the Troubleshooting section above
2. Review FFmpeg and Whisper documentation
3. Open an issue on GitHub
4. Contact: [your-contact-info]

## Credits

Built with:
- [OpenAI Whisper](https://github.com/openai/whisper) - Speech recognition
- [FFmpeg](https://ffmpeg.org/) - Audio extraction
- [PyTorch](https://pytorch.org/) - Deep learning framework
- [Jitsi Meet](https://jitsi.org/) - Video conferencing

---

**Version**: 1.0.0  
**Last Updated**: 2024  
**Python**: 3.10+  
**Status**: Production Ready
