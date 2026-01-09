# Speaker Diarization Guide

This document explains how to use speaker diarization (speaker segmentation) in your Jitsi transcription pipeline.

## What is Speaker Diarization?

Speaker diarization identifies **who spoke when** in an audio file. It answers the question: "Which speaker is speaking at each moment in time?"

When combined with transcription, you get output like:
```
00:00:05 - SPEAKER_00: Hello, thank you for joining the meeting.
00:00:10 - SPEAKER_01: Happy to be here!
00:00:15 - SPEAKER_00: Let's discuss the quarterly results.
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `pyannote.audio` - State-of-the-art speaker diarization
- `huggingface-hub` - Model management

### 2. Setup HuggingFace Authentication

Speaker diarization models are hosted on HuggingFace and require free authentication:

```bash
python setup_diarization.py
```

This script will guide you through:
1. Creating a free HuggingFace account (if you don't have one)
2. Generating an authentication token
3. Accepting the model license
4. Saving the token for future use

**Or manually authenticate:**

```bash
huggingface-cli login
```

### 3. Run Pipeline with Diarization

```bash
python run_pipeline.py recordings/meeting.mp4
```

Diarization is **enabled by default**. To disable it:

```bash
python run_pipeline.py recordings/meeting.mp4 --no-diarization
```

## Output Files

When diarization is enabled, you get additional output files:

| File | Content |
|------|---------|
| `{name}_with_speakers.json` | Transcript with speaker labels (JSON format) |
| `{name}_with_speakers.srt` | Subtitle format with speaker names |
| `{name}_speaker_timeline.txt` | Human-readable timeline with speakers |
| `{name}.json` | Original transcript (no speakers) |
| `{name}.srt` | Original subtitles (no speakers) |
| `{name}.txt` | Plain text transcript |

### Example JSON Output

```json
{
  "metadata": {
    "model": "base",
    "audio_file": "recordings/meeting.mp4",
    "language": "en",
    "duration": 300.5
  },
  "language": "en",
  "duration_seconds": 300.5,
  "total_speakers": 2,
  "speakers": {
    "SPEAKER_00": 0,
    "SPEAKER_01": 1
  },
  "segments": [
    {
      "id": 1,
      "start": 5.0,
      "end": 10.0,
      "text": "Hello, thank you for joining",
      "speaker": "SPEAKER_00",
      "speaker_id": 0,
      "speaker_overlap": 4.8
    },
    ...
  ]
}
```

### Example SRT Output

```srt
1
00:00:05,000 --> 00:00:10,000
[SPEAKER_00]
Hello, thank you for joining the meeting.

2
00:00:10,000 --> 00:00:15,000
[SPEAKER_01]
Happy to be here!

```

### Example Timeline Output

```
SPEAKER TIMELINE
============================================================

File: recordings/meeting.mp4
Language: en
Total Speakers: 2
Duration: 00:05:00

Speakers:
  [0] SPEAKER_00
  [1] SPEAKER_01

------------------------------------------------------------

00:00:05 - SPEAKER_00:
  Hello, thank you for joining the meeting.

00:00:10 - SPEAKER_01:
  Happy to be here!

00:00:15 - SPEAKER_00:
  Let's discuss the quarterly results.

```

## Advanced Usage

### Disable Diarization (Faster Processing)

If you only need transcription without speaker labels:

```bash
python run_pipeline.py recordings/meeting.mp4 --no-diarization
```

This skips the diarization step, making the pipeline 2-3x faster.

### Use with Batch Processing

Diarization works with batch transcription:

```bash
python batch_transcribe.py --no-diarization  # Skip diarization for all
python batch_transcribe.py                   # Include diarization
```

### Different Whisper Models

Diarization is independent of the Whisper model:

```bash
# Small model with diarization
python run_pipeline.py recordings/meeting.mp4 --model small

# Large model with diarization
python run_pipeline.py recordings/meeting.mp4 --model large

# Without diarization
python run_pipeline.py recordings/meeting.mp4 --no-diarization --model medium
```

## Troubleshooting

### Error: "HuggingFace token not found"

**Solution:** Run authentication setup:
```bash
python setup_diarization.py
```

Or set environment variable:
```bash
# Windows
set HF_TOKEN=your_token_here

# Linux/Mac
export HF_TOKEN=your_token_here
```

### Error: "License not accepted"

**Solution:** Accept the model license:
1. Visit https://huggingface.co/pyannote/speaker-diarization-3.1
2. Click "Agree and access repository"
3. Re-run diarization

### Error: "No module named 'pyannote'"

**Solution:** Install the package:
```bash
pip install pyannote.audio
```

### Out of Memory (OOM)

If you get GPU memory errors:
1. Diarization will automatically fall back to CPU
2. Or disable GPU: `set CUDA_VISIBLE_DEVICES=-1` (Windows)
3. Or use `--no-diarization` to skip this step

### Slow Processing

Diarization is slower than transcription. Processing times:
- Transcription: ~1 minute per hour of audio
- Diarization: ~2-3 minutes per hour of audio
- Total: ~3-4 minutes per hour of audio

To speed up:
- Use `--no-diarization` flag
- Use GPU if available (check with `python setup_diarization.py --verify`)
- Process in smaller chunks

## System Requirements

### Minimum
- 4GB RAM (CPU mode)
- Python 3.10+
- ~1GB disk space for models

### Recommended
- GPU with 4GB VRAM (NVIDIA RTX 3080+ or similar)
- 8GB+ RAM
- SSD for faster model loading

### Supported Devices
- NVIDIA GPUs (CUDA)
- AMD GPUs (ROCm)
- Apple Silicon (Metal Acceleration)
- CPU (slower but works)

## Verify Setup

Check if everything is installed correctly:

```bash
python setup_diarization.py --verify
```

Output should show:
```
✓ Installed (Pyannote.audio)
✓ GPU available or CPU mode
✓ Authenticated
```

## How It Works

The pipeline uses **Pyannote.audio 3.1**, a state-of-the-art speaker diarization model:

1. **Audio Analysis**: Analyzes voice characteristics, speech patterns
2. **Speaker Segmentation**: Identifies speaker boundaries (when one person stops, another starts)
3. **Speaker Clustering**: Groups similar voice patterns to identify speakers
4. **Timeline Merging**: Aligns diarization with transcription timestamps
5. **Output Generation**: Creates speaker-labeled transcripts

## Performance Notes

- **Accuracy**: Typically 85-95% accurate on clear audio
- **Multi-speaker**: Works with 2+ speakers
- **Accents**: Handles various accents and languages
- **Noise Tolerance**: Works with some background noise

Accuracy depends on:
- Audio quality (clearer = more accurate)
- Number of speakers (2-3 is easiest, 10+ harder)
- Speaker distinctiveness (very different voices easier)
- Recording conditions (clear room = better)

## Limitations

- Requires at least 2 speakers (single-speaker is trivial)
- Cannot identify speaker names (just "SPEAKER_00", "SPEAKER_01", etc.)
- Works best on professional-quality recordings
- Struggles with heavy background noise or overlapping speech

To identify speakers by name, you would need:
- Manual mapping file
- Speaker identification/verification model
- Metadata from meeting system

## For More Information

- Pyannote Documentation: https://github.com/pyannote/pyannote-audio
- HuggingFace Models: https://huggingface.co/models?search=diarization
- Research Paper: https://arxiv.org/abs/2110.04537

## Next Steps

1. ✅ Install and setup diarization
2. ✅ Run pipeline with your first video
3. Review the speaker timeline output
4. Adjust output format as needed (JSON, SRT, or text)
5. Integrate with your workflow
