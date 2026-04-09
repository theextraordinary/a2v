import json

SYSTEM_PROMPT = """You are a professional video editor AI.

Given audio segments with emotion, generate a caption timeline.

Rules:

* Keep captions short
* Highlight important words
* Match color with emotion
* Add animation only when needed

Return ONLY valid JSON. No explanation."""


def build_prompt(segments):
    payload = json.dumps(segments, ensure_ascii=True)
    return SYSTEM_PROMPT + "\n\nInput segments:\n" + payload
