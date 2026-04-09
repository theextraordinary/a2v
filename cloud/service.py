from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List

from cloud.pipeline import run_cloud_pipeline

app = FastAPI(title='A2V Cloud Service')


class Segment(BaseModel):
    start: float
    end: float
    text: str
    emotion: str


class SegmentsIn(BaseModel):
    segments: List[Segment]


@app.post('/generate_timeline')
def generate_timeline(payload: SegmentsIn):
    try:
        timeline = run_cloud_pipeline([s.dict() for s in payload.segments])
        return {'timeline': timeline}
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': str(e)})
