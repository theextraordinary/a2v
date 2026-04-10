from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List

from cloud.pipeline import run_cloud_pipeline
from cloud.stylist import correct_transcript, extract_important_words, generate_edit_decisions

app = FastAPI(title='A2V Cloud Service')


class Segment(BaseModel):
    start: float
    end: float
    text: str
    emotion: str


class SegmentsIn(BaseModel):
    segments: List[Segment]


class TranscriptIn(BaseModel):
    text: str


class EditDecisionIn(BaseModel):
    text: str
    words: list
    captions: list


@app.post('/generate_timeline')
def generate_timeline(payload: SegmentsIn):
    try:
        timeline = run_cloud_pipeline([s.dict() for s in payload.segments])
        return {'timeline': timeline}
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': str(e)})


@app.post('/correct_transcript')
def correct_transcript_endpoint(payload: TranscriptIn):
    try:
        corrected = correct_transcript(payload.text)
        return {'text': corrected}
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': str(e)})


@app.post('/important_words')
def important_words_endpoint(payload: TranscriptIn):
    try:
        words = extract_important_words(payload.text)
        return {'words': words}
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': str(e)})


@app.post('/generate_edit_decisions')
def generate_edit_decisions_endpoint(payload: EditDecisionIn):
    try:
        decisions = generate_edit_decisions(payload.text, payload.words, payload.captions)
        return {'decisions': decisions}
    except Exception as e:
        return JSONResponse(status_code=500, content={'error': str(e)})
