from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from pathlib import Path
import tempfile
import shutil
import os

from edge.processor import process_audio

app = FastAPI(title='A2V Edge Service')

_base_dir = Path(__file__).resolve().parents[1]
_cache_dir = _base_dir / '.hf_cache'
_cache_dir.mkdir(parents=True, exist_ok=True)
os.environ['HF_HOME'] = str(_cache_dir)
os.environ['HF_HUB_CACHE'] = str(_cache_dir)
os.environ['TRANSFORMERS_CACHE'] = str(_cache_dir)

@app.post('/process_audio')
async def process_audio_endpoint(file: UploadFile = File(...)):
    suffix = Path(file.filename).suffix or '.wav'
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        with tmp as f:
            shutil.copyfileobj(file.file, f)
        tmp_path = tmp.name

    try:
        segments = process_audio(tmp_path, model_size='base', use_mock_asr=False)
        return {'segments': segments}
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': str(e)})
