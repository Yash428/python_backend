# Pipeline Architecture with Speaker Diarization

## Data Flow Diagram

```
INPUT: video.mp4
   |
   v
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: EXTRACT AUDIO                                       │
│ (extract_audio.py)                                          │
│ - FFmpeg: MP4 → WAV                                         │
│ - Quality: 16kHz mono                                       │
└─────────────────────────────────────────────────────────────┘
   |
   v
   audio.wav
   |
   +─────────────────────────────────────────────────────────────┐
   |                                                             |
   v                                                             v
┌────────────────────────┐                      ┌──────────────────────────┐
│ STEP 2A: TRANSCRIBE    │                      │ STEP 2B: DIARIZE (NEW)   │
│ (transcribe.py)        │                      │ (diarize.py)             │
│ Whisper Transcription  │                      │ Speaker Identification   │
│ ↓                      │                      │ ↓                        │
│ text + timestamps      │                      │ speaker segments         │
└────────────────────────┘                      └──────────────────────────┘
   |                                             |
   v                                             v
segments.json                              diarization.json
   |                                             |
   |                         (parallel paths merge here)
   |                                             |
   +─────────────────────────────────────────────┤
                           |
                           v
┌──────────────────────────────────────────────────────────────┐
│ STEP 3: MERGE RESULTS                                        │
│ (diarize.py: merge_with_transcription)                       │
│ - Align speaker segments with transcription segments         │
│ - Add speaker labels to each segment                         │
└──────────────────────────────────────────────────────────────┘
   |
   v
merged_transcript.json (with speaker labels)
   |
   +─────────────────────────────────────────────────────────────┐
   |                                                             |
   v                                                             v
   original outputs                                    NEW diarized outputs
   (transcribe.py)                                   (diarize.py)
   ├─ text.txt                                       ├─ with_speakers.json
   ├─ timestamps.json                                ├─ with_speakers.srt
   ├─ subtitles.srt                                  └─ speaker_timeline.txt
   ├─ timeline.txt
   └─ markers.edl
```

## Module Interaction

```
┌─────────────────────────────────────────────────────────────────────┐
│                        run_pipeline.py                              │
│                    (Main Orchestrator)                              │
└─────────────────────────────────────────────────────────────────────┘
        |           |              |              |           |
        |           |              |              |           |
        v           v              v              v           v
   extract_    transcribe_    diarize_      segment_      utils
   audio.py    .py            .py           .py           .py
        |           |          |               |           |
        |           |          v               |           |
        |           |    SpeakerDiarizer       |           |
        |           |    - load_model()        |           |
        |           |    - diarize_audio()     |           |
        |           |    - merge_results()     |           |
        |           |    - save_outputs()      |           |
        |           |                          |           |
        +───────────┴──────────────┬───────────┴───────────┘
                                   |
                                   v
                            Output Formats
```

## Processing Pipeline with Diarization Enabled

```
VIDEO INPUT
    │
    ├─────────────────────────────┐
    │                             │
    v                             v
AUDIO EXTRACTION            (Optional)
    │                        Skip audio
    ├─ FFmpeg              extraction
    ├─ 16kHz mono
    ├─ 1-2 min
    │
    v
PARALLEL PROCESSING
    ├─────────────────────────────┐
    │                             │
    v                             v
TRANSCRIPTION             SPEAKER DIARIZATION
├─ Whisper Model          ├─ Pyannote 3.1
├─ Language auto-detect   ├─ Speaker segments
├─ ~1 min/hour audio      ├─ ~2-3 min/hour audio
├─ Output:                ├─ Output:
│  ├─ segments[]          │  ├─ speakers{}
│  ├─ timestamps          │  └─ segments[]
│  └─ language            │     └─ speaker_id
    │                             │
    └─────────────────┬───────────┘
                      │
                      v
            MERGE RESULTS
            ├─ Align segments
            ├─ Add speaker labels
            └─ Combine metadata
                      │
                      v
            GENERATE OUTPUTS
            ├─ with_speakers.json ✓
            ├─ with_speakers.srt  ✓
            ├─ speaker_timeline.txt ✓
            ├─ (+ original outputs)
            └─ Save to transcripts/
                      │
                      v
                   COMPLETE
```

## File Processing Timeline

For a 1-hour meeting:

```
00:00  ├─ Start
       │
01:00  ├─ Audio extraction complete
       │
       ├─ PARALLEL PROCESSING BEGINS
       │  ├─ Transcription path (1 min)
       │  └─ Diarization path (2-3 min)
       │
04:00  ├─ Both paths complete
       │  ├─ Transcription segments ✓
       │  ├─ Speaker segments ✓
       │
       ├─ Merge results (seconds)
       │  ├─ Align speakers to transcript
       │  ├─ Add speaker labels
       │
       ├─ Generate outputs
       │  ├─ with_speakers.json
       │  ├─ with_speakers.srt
       │  ├─ speaker_timeline.txt
       │  └─ (original formats)
       │
       v─ COMPLETE
```

## Output Format Comparison

### Standard Transcription (--no-diarization)
```json
{
  "segments": [
    {"start": 5.0, "end": 10.0, "text": "Hello"},
    {"start": 10.0, "end": 15.0, "text": "How are you?"}
  ]
}
```

### With Speaker Diarization
```json
{
  "total_speakers": 2,
  "speakers": {"SPEAKER_00": 0, "SPEAKER_01": 1},
  "segments": [
    {
      "start": 5.0,
      "end": 10.0,
      "text": "Hello",
      "speaker": "SPEAKER_00",      ← NEW
      "speaker_id": 0,              ← NEW
      "speaker_overlap": 4.8        ← NEW
    },
    {
      "start": 10.0,
      "end": 15.0,
      "text": "How are you?",
      "speaker": "SPEAKER_01",      ← NEW
      "speaker_id": 1,              ← NEW
      "speaker_overlap": 4.9        ← NEW
    }
  ]
}
```

## Error Handling & Fallback

```
USER: python run_pipeline.py recording.mp4
    │
    v
EXTRACT AUDIO
    │
    v─── SUCCESS ───> TRANSCRIBE ───> SUCCESS
    │
    └─── FAIL ──────> ERROR (exit)
                    

TRANSCRIBE ───> SUCCESS
    │
    v─── LOAD DIARIZATION MODEL
        │
        ├─ HF Token missing?
        │  └─> WARN (skip diarization, continue)
        │
        ├─ License not accepted?
        │  └─> WARN (skip diarization, continue)
        │
        ├─ GPU OOM?
        │  └─> FALLBACK CPU (may be slow)
        │
        └─ Success
           └─> DIARIZE ────> MERGE ────> SAVE
                             │
                             └─> Generate 3 new formats
                                 + original formats

OUTPUT: All transcript formats + speaker labels
```

## Processing Modes

```
DIARIZATION ENABLED (Default)
python run_pipeline.py recording.mp4
    │
    ├─ Extract audio
    ├─ Transcribe (1 min/hour)
    ├─ Diarize (2-3 min/hour)
    ├─ Merge results
    └─ Generate outputs (8 formats total)
       ├─ Original (5 formats)
       └─ With speakers (3 formats)


DIARIZATION DISABLED (Faster)
python run_pipeline.py recording.mp4 --no-diarization
    │
    ├─ Extract audio
    ├─ Transcribe (1 min/hour)
    └─ Generate outputs (5 formats)
       └─ Original formats only
```

## Requirements & Dependencies

```
run_pipeline.py
    │
    ├─ extract_audio.py (FFmpeg)
    │
    ├─ transcribe.py
    │   └─ whisper (OpenAI)
    │       └─ torch + torchaudio
    │
    └─ diarize.py (NEW)
        └─ pyannote.audio
            ├─ torch + torchaudio
            ├─ huggingface_hub
            └─ Pyannote Models (auto-downloaded)
                ├─ speaker-diarization-3.1
                └─ Requires HF authentication
```

---

This architecture provides:
- ✅ Parallel processing of transcription and diarization
- ✅ Clean separation of concerns
- ✅ Multiple output formats
- ✅ Graceful error handling and fallback
- ✅ GPU/CPU flexibility
- ✅ Easy enable/disable with CLI flag
