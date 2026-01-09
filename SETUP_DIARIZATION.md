# Speaker Diarization Setup Guide

## Overview

The Jitsi transcription pipeline now includes **speaker diarization** - automatically identifying and labeling who spoke when in your recordings.

### Technology Stack

This implementation uses a fully **open-source, license-free** approach:

- **Silero VAD**: Voice Activity Detection (detects speech segments)
- **SpeechBrain ECAPA-TDNN**: Speaker embedding extraction (converts speech to speaker vectors)
- **Agglomerative Clustering**: Groups speakers by embedding similarity (cosine distance)

**No HuggingFace authentication or gated model access required.**

---

## Installation

### 1. Update Dependencies

```bash
pip install -r requirements.txt
```

Key new packages:
- `silero-vad>=1.0.0` - Voice activity detection
- `speechbrain>=0.5.13` - Speaker embeddings (ECAPA-TDNN model)
- `scikit-learn>=1.2.0` - Clustering algorithm
- `torch>=2.0.0`, `torchaudio>=2.0.0` - Deep learning framework

### 2. Verify Installation

```bash
python test_installation.py
```

Or manually test imports:

```python
from silero_vad import load_silero_vad, get_speech_timestamps
from speechbrain.pretrained import SpeakerRecognition
from sklearn.cluster import AgglomerativeClustering
import torch
import torchaudio
```

All should import without errors.

---

## Usage

### Run Pipeline with Diarization (Default)

```bash
# Diarization is ENABLED by default
python run_pipeline.py recordings/meeting.mp4
```

This will generate:
- `meeting.json` - Full transcription
- `meeting_with_speakers.json` - Transcription + speaker labels
- `meeting_speaker_timeline.txt` - Readable speaker timeline
- `meeting_with_speakers.srt` - SRT subtitle file with speakers

### Run Without Diarization

```bash
python run_pipeline.py recordings/meeting.mp4 --no-diarization
```

### Specify Whisper Model

```bash
python run_pipeline.py recordings/meeting.mp4 --model large
```

---

## Output Formats

### 1. JSON with Speaker Labels (`*_with_speakers.json`)

```json
{
  "metadata": { ... },
  "language": "en",
  "duration_seconds": 120.5,
  "total_speakers": 2,
  "speakers": {
    "SPEAKER_00": 0,
    "SPEAKER_01": 1
  },
  "segments": [
    {
      "id": 0,
      "start": 0.0,
      "end": 5.2,
      "text": "Hello, welcome to the meeting.",
      "speaker": "SPEAKER_00",
      "speaker_id": 0,
      "speaker_overlap": 5.2
    },
    {
      "id": 1,
      "start": 5.3,
      "end": 8.1,
      "text": "Thanks for joining us.",
      "speaker": "SPEAKER_01",
      "speaker_id": 1,
      "speaker_overlap": 2.8
    }
  ]
}
```

### 2. Speaker Timeline (`*_speaker_timeline.txt`)

```
SPEAKER TIMELINE
============================================================

File: recordings/meeting.mp4
Total Speakers: 2

Speakers:
  [0] SPEAKER_00
  [1] SPEAKER_01

------------------------------------------------------------

00:00:00 - SPEAKER_00:
  Hello, welcome to the meeting.

00:00:05 - SPEAKER_01:
  Thanks for joining us.

00:00:08 - SPEAKER_00:
  Let's begin the agenda.
```

### 3. SRT Subtitles with Speakers (`*_with_speakers.srt`)

```
1
00:00:00 --> 00:00:05
[SPEAKER_00]
Hello, welcome to the meeting.

2
00:00:05 --> 00:00:08
[SPEAKER_01]
Thanks for joining us.
```

---

## How It Works

### Pipeline Steps

1. **Audio Extraction** (FFmpeg)
   - Extract audio from MP4 → 16kHz mono WAV

2. **Voice Activity Detection** (Silero VAD)
   - Detect speech segments, filter out silence
   - Default minimum segment: 0.5 seconds

3. **Speaker Embedding Extraction** (SpeechBrain ECAPA-TDNN)
   - For each speech segment, generate a 192-dimensional speaker vector
   - Model pre-trained on VoxCeleb dataset (covers diverse accents/languages)

4. **Clustering** (Agglomerative Clustering)
   - Group embeddings by cosine distance
   - Auto-detect number of speakers using silhouette score
   - Maximum default: 10 speakers

5. **Merge with Transcription** (Whisper)
   - Match each transcribed segment with its speaker
   - Combine into single output JSON

6. **Output Generation**
   - Save as JSON, readable timeline, SRT format

---

## Configuration

### Diarization Parameters

Edit in `src/diarize.py` → `diarize_audio()` method:

```python
# Minimum speech duration in seconds (skip shorter segments)
min_speech_duration: float = 0.5

# Maximum expected speakers
max_speakers: int = 10
```

For meetings with many participants, increase `max_speakers`:

```python
diarization_result = diarizer.diarize_audio(
    wav_path,
    min_speech_duration=0.3,  # More sensitive
    max_speakers=15           # Handle more speakers
)
```

---

## Troubleshooting

### ImportError: No module named 'silero_vad'

```bash
pip install silero-vad
```

### ImportError: No module named 'speechbrain'

```bash
pip install speechbrain
```

### CUDA out of memory

The pipeline defaults to CPU. For GPU:

```python
from diarize import SpeakerDiarizer

diarizer = SpeakerDiarizer(device="cuda")
```

Or revert to CPU if GPU fails:

```python
diarizer = SpeakerDiarizer(device="cpu")
```

### Poor Speaker Separation

If speakers are being confused, adjust clustering:

```python
# More sensitive (assume more speakers)
max_speakers=15

# Less sensitive (assume fewer speakers)
max_speakers=3
```

### Models Not Downloaded

The first run will auto-download models (~2GB total):
- Silero VAD: ~50 MB
- SpeechBrain ECAPA-TDNN: ~100 MB

Models are cached in `pretrained_models/` directory.

---

## Performance

Typical processing times (CPU, Windows):

| File Duration | Diarization Time | Total Time |
|---|---|---|
| 1 minute | ~15s | ~30s |
| 5 minutes | ~30s | ~60s |
| 30 minutes | ~3 min | ~5 min |
| 1 hour | ~6 min | ~10 min |

GPU (CUDA) is ~3-5x faster.

---

## Advanced Usage

### Run on Specific Audio File

```python
from pathlib import Path
from diarize import SpeakerDiarizer

diarizer = SpeakerDiarizer(device="cpu")
diarizer.load_model()

# Diarize
result = diarizer.diarize_audio(
    Path("audio.wav"),
    min_speech_duration=0.5,
    max_speakers=10
)

# Save outputs
diarizer.save_diarization_json(result, Path("output.json"))
diarizer.save_speaker_timeline(result, Path("timeline.txt"))
diarizer.save_speaker_srt(result, Path("speakers.srt"))

diarizer.unload_model()
```

### Merge with External Transcription

```python
import json
from diarize import SpeakerDiarizer

diarizer = SpeakerDiarizer()
diarizer.load_model()

# Your transcription
with open("transcription.json") as f:
    transcription = json.load(f)

# Diarize
diarization = diarizer.diarize_audio(Path("audio.wav"))

# Merge
merged = diarizer.merge_with_transcription(diarization, transcription)

diarizer.save_diarization_json(merged, Path("merged.json"))
```

---

## Accuracy Notes

### Factors Affecting Accuracy

✅ **Good accuracy with:**
- 2-4 speakers
- Clear audio, low background noise
- Distinct voices (different genders/ages help)
- Sufficient speaking time per speaker (>5 seconds)

⚠️ **May struggle with:**
- 5+ speakers (harder to separate)
- Overlapping speech
- Heavy accents or non-English
- Very short speeches (<1 second)
- Background noise/music

### Improving Accuracy

1. **Denoise audio before processing** - Remove background noise
2. **Use larger Whisper model** - `--model large` for better transcription
3. **Longer minimum segment duration** - Skip very short utterances
4. **Fewer max speakers** - Help clustering focus on dominant speakers

---

## FAQ

**Q: Do I need HuggingFace authentication?**
A: No! Unlike Pyannote, this uses fully open-source models.

**Q: Can I use GPU?**
A: Yes, pass `device="cuda"` to SpeakerDiarizer.

**Q: How many speakers can it handle?**
A: Reliably 2-4 speakers. Up to 10 with careful tuning.

**Q: Does it support languages other than English?**
A: SpeechBrain ECAPA-TDNN is language-agnostic (works on speaker embeddings, not language).

**Q: Can I run on very long files (2+ hours)?**
A: Yes, but expect 15-30 minutes processing time on CPU.

---

## Uninstalling Diarization

To remove diarization (revert to transcription-only):

```bash
# Edit run_pipeline.py
python run_pipeline.py recording.mp4 --no-diarization

# Or uninstall packages
pip uninstall silero-vad speechbrain scikit-learn -y
```

---

## Support

For issues:

1. Check `requirements.txt` - ensure all dependencies installed
2. Run `test_installation.py` - verify environment
3. Check logs - detailed error messages in console output
4. Review troubleshooting section above

---

Last Updated: 2024
