import json
import requests

from utils.schema import parse_timeline, validate_timeline
from .prompt import build_prompt
from utils.config import load_env


def _timeline_schema_hint():
    return (
        'Return a JSON array of objects with keys: '
        'start (float), end (float), text (str), color (str), '
        'animation (str), emphasis (bool).'
    )


def call_llm(prompt: str) -> dict:
    env = load_env()
    api_key = env.get('GEMMA_API_KEY') or env.get('LLM_API_KEY')
    if not api_key:
        raise RuntimeError('GEMMA_API_KEY (or LLM_API_KEY) missing')

    base = env.get('LLM_API_URL', 'https://api-inference.huggingface.co/models').rstrip('/')
    model = env.get('LLM_MODEL', 'google/gemma-4-e4b-it')
    url = f'{base}/{model}'

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }

    payload = {
        'inputs': prompt,
        'parameters': {
            'temperature': 0.3,
            'max_new_tokens': 600,
            'return_full_text': False,
        },
    }

    resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
    resp.raise_for_status()
    return resp.json()


def _extract_text(resp_json):
    if isinstance(resp_json, list) and resp_json:
        return resp_json[0].get('generated_text', '')
    if isinstance(resp_json, dict) and 'generated_text' in resp_json:
        return resp_json['generated_text']
    return str(resp_json)


def _fallback_timeline(segments):
    color_map = {
        'motivational': 'yellow',
        'sad': 'blue',
        'energetic': 'red',
        'calm': 'white',
    }
    anim_map = {
        'motivational': 'pop',
        'sad': 'fade',
        'energetic': 'pop',
        'calm': 'minimal',
    }
    timeline = []
    for seg in segments:
        emo = seg.get('emotion', 'calm')
        timeline.append({
            'start': float(seg['start']),
            'end': float(seg['end']),
            'text': seg['text'],
            'color': color_map.get(emo, 'white'),
            'animation': anim_map.get(emo, 'minimal'),
            'emphasis': False,
        })
    return timeline


def generate_timeline(segments, max_retries=3):
    load_env()
    base_prompt = build_prompt(segments)
    prompt = base_prompt + "\n" + _timeline_schema_hint() + "\nReturn ONLY valid JSON. No explanation."

    last_err = None
    for _ in range(max_retries):
        try:
            resp_json = call_llm(prompt)
            text = _extract_text(resp_json)
            # Accept either a JSON array or {"timeline": [...]}
            try:
                parsed = json.loads(text)
                if isinstance(parsed, dict) and 'timeline' in parsed:
                    valid, errors, normalized = validate_timeline(parsed['timeline'])
                    if not valid:
                        raise ValueError('; '.join(errors))
                    return normalized
            except Exception:
                pass
            timeline = parse_timeline(text)
            return timeline
        except Exception as e:
            last_err = e
            prompt = base_prompt + "\n" + _timeline_schema_hint() + "\nReturn ONLY valid JSON. No explanation."
            continue

    # Fallback mode: deterministic output
    return _fallback_timeline(segments)
