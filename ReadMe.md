# AI Audio-to-Video (A2V) Pipeline

Production-grade, edge-cloud separated A2V system:

```
Audio -> Edge Processing (E2B) -> Cloud Reasoning (E4B) -> Timeline JSON -> Video Rendering
```

## Architecture Diagram

```
        +---------------------+          +---------------------+
        |   Edge Service      |          |   Cloud Service     |
        |  /process_audio     |          | /generate_timeline  |
        +----------+----------+          +----------+----------+
                   |                                |
               segments JSON                  timeline JSON
                   |                                |
                   +-------------+  +--------------+
                                 |  |
                              app/main.py
                                 |
                           video renderer
```

## Setup

```bash
pip install -r requirements.txt
```

Ensure FFmpeg and ImageMagick are installed (MoviePy uses them for video and text rendering).

If you are on Python 3.13+, `audioop-lts` is required for `pydub` (included in `requirements.txt`).
FastAPI file uploads require `python-multipart` (included in `requirements.txt`).

## Run Edge + Cloud

```bash
bash run_edge.sh
```

```bash
bash run_cloud.sh
```

## Run Pipeline

```bash
python app/main.py
```

## Environment Variables

Set these in `.env`:
- `GEMMA_API_KEY` (recommended) or `LLM_API_KEY` for cloud LLM access
- `LLM_API_URL` (optional) default `https://api-inference.huggingface.co/models`
- `LLM_MODEL` (optional) default `google/gemma-4-e4b-it`
- `EDGE_URL` (optional) default `http://127.0.0.1:8000/process_audio`
- `CLOUD_URL` (optional) default `http://127.0.0.1:9000/generate_timeline`

## Why Cloud API For E4B

- avoids memory issues on local machines
- scales independently of edge devices
- production-ready and easy to monitor

## API Endpoints

### Edge
- `POST /process_audio`
- Input: audio file
- Output: `{ "segments": [ { "start", "end", "text", "emotion" } ] }`

### Cloud
- `POST /generate_timeline`
- Input: `{ "segments": [...] }`
- Output: `{ "timeline": [ { "start", "end", "text", "color", "animation", "emphasis" } ] }`

## Notes

- Cloud uses LLM to produce strictly validated JSON timeline.
- Edge uses HuggingFace emotion model `j-hartmann/emotion-english-distilroberta-base`.
- Default output size is 1080x1920 with centered captions.
