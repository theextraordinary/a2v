from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from pathlib import Path
import tempfile
import shutil

from edge.processor import process_audio

app = FastAPI(title='A2V Edge Service')


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
