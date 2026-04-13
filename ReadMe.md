# A2V (Audio‑to‑Video) Pipeline

End‑to‑end A2V system that turns speech audio into a captioned video with synced word timing, optional background music, and structured edit metadata. The pipeline is designed for edge ASR + cloud text intelligence, with a clean rendering stage that can be replayed from a saved manifest.

```
audio.wav
  → word timestamps (WhisperX, Edge)
  → transcript correction + important words + edit decisions (E2B URL)
  → caption grouping
  → frame rendering (silent.mp4)
  → mix speech + bgm
  → mux final video
  → video_manifest.json (re‑render input)
```

## Architecture (Current)

```
          +--------------------+                 +----------------------+
          |    Edge Service    |                 |   E2B Endpoint URL   |
          |  /process_words    |                 |   /generate (JSON)   |
          +---------+----------+                 +----------+-----------+
                    |                                       |
         word timestamps (WhisperX)              transcript / important / edits
                    |                                       |
                    +------------------+--------------------+
                                       |
                                   app/main.py
                                       |
                     caption grouping + renderer + mux
                                       |
                             final.mp4 + manifest
```

## What Each Stage Does

**Edge (E2B in name only here = edge)**
- Runs ASR with WhisperX
- Produces word‑level timestamps:
  ```
  [{"word": "...", "start": 0.10, "end": 0.32}, ...]
  ```

**Cloud (E2B URL)**
- Corrects transcript
- Extracts important words (for coloring)
- Generates optional edit decisions (zoom/cut/etc.)
- Endpoint: `POST /generate` with `{"prompt": "...", "max_new_tokens": N}`

**Renderer**
- Groups words into short phrases
- Renders centered captions with consistent font
- Highlights important words by color
- Produces `silent.mp4`, then muxes audio

**Manifest**
Creates `data/output/video_manifest.json` so another model can re‑render without re‑running ASR or E2B.

---

# Setup

## 1) Install dependencies

```bash
pip install -r requirements.txt
```

## 2) Install FFmpeg
Movie rendering uses FFmpeg. Make sure it is available on PATH.

## 3) Configure `.env`

Create `.env` at repo root:

```
E2B_URL=https://your-ngrok-or-server-url
EDGE_WORDS_URL=http://127.0.0.1:8000/process_words
```

---

# Run

## Edge service (WhisperX)
```bash
bash run_edge.sh
```

## Main pipeline
```bash
python app/main.py --debug
```

Output:

```
data/output/final.mp4
data/output/video_manifest.json
```

---

# Output Manifest

`data/output/video_manifest.json` contains:

- audio paths + duration
- video size, fps, background, font
- per‑word timestamps (with important flag)
- caption groups
- edit decisions

This allows re‑rendering without running E2B or WhisperX again.

---

# Important Notes

- WhisperX provides word‑level timestamps.
- Captions are rendered in strict spoken order.
- Important words are colored using E2B‑generated keywords.
- Edit decisions are optional and non‑fatal if missing.

---

# License

**Copyright (c) 2026 ANIGMA Incorporation**

All rights reserved.

