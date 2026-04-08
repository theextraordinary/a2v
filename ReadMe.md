# AI Audio-to-Video (A2V) Pipeline

This project converts an input audio file into a vertical video with styled captions. It simulates an edge-to-cloud (E2B/E4B) workflow:

- Edge (E2B): ASR, silence segmentation, and emotion classification
- Cloud (E4B): Caption styling based on emotions

## Setup

1. Create a virtual environment and install dependencies:

```bash
pip install -r requirements.txt
```

2. Ensure FFmpeg and ImageMagick are installed (MoviePy uses them for video and text rendering).

## Run

Place your audio at:

```
data/input_audio/sample.wav
```

Then run:

```bash
python app/main.py
```

The output video will be written to:

```
data/output/final.mp4
```

## Pipeline Overview

1. **Edge (E2B)**
   - `edge/asr.py`: Whisper transcription
   - `edge/segmentation.py`: Silence-based segmentation
   - `edge/emotion.py`: Rule-based emotion tagging
   - `edge/processor.py`: Combines the above into structured segments

2. **Cloud (E4B)**
   - `cloud/prompt.py`: Builds an LLM-friendly prompt
   - `cloud/stylist.py`: Simulates styling decisions
   - `cloud/pipeline.py`: Produces styled captions

3. **Audio & Video**
   - `audio/cleaner.py`: Normalize and trim silence
   - `video/renderer.py`: Creates a vertical black video and overlays captions

## Notes

- Default output size is 1080x1920 with centered captions.
- Styling rules are rule-based for now, but can be swapped with an API call later.
