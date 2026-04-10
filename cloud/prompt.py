import json

SYSTEM_PROMPT = """You are a professional video editor AI.

Given audio segments with emotion, generate a caption timeline.

Rules:

* Keep captions short
* Highlight important words
* Match color with emotion
* Add animation only when needed

Return ONLY valid JSON. No explanation."""


CORRECTION_PROMPT = """You are correcting an ASR transcript.
Keep the original meaning exactly.
Fix only obvious recognition errors.
Do not add facts.
Do not paraphrase unless necessary.
Keep token count reasonably close to source when possible.
Return only the corrected transcript text."""


EDIT_DECISION_PROMPT = """You are an expert short-form video editor.
Given transcript, word timings, and caption groups, produce sparse editing decisions.
Allowed decisions: zoom_in, zoom_out, cut, emphasis_caption, meme_insert, broll, sfx_hit, silence_beat, visual_reset.
Decisions must be grounded in the transcript/timings.
Be selective. No spam.
Return ONLY valid JSON list of objects with: start, end, decision, reason."""


def build_prompt(segments):
    payload = json.dumps(segments, ensure_ascii=True)
    return SYSTEM_PROMPT + "\n\nInput segments:\n" + payload


def build_correction_prompt(text):
    return CORRECTION_PROMPT + "\n\nNoisy transcript:\n" + text


def build_edit_decision_prompt(text, words, captions):
    payload = json.dumps({
        "text": text,
        "words": words,
        "captions": captions,
    }, ensure_ascii=True)
    return EDIT_DECISION_PROMPT + "\n\nInput:\n" + payload
