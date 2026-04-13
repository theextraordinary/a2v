import json
import requests

from utils.schema import parse_timeline, validate_timeline, validate_edit_decisions
from .prompt import build_prompt, build_correction_prompt, build_edit_decision_prompt
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

    base = env.get('LLM_API_URL', 'https://router.huggingface.co/hf-inference/models').rstrip('/')
    model = env.get('LLM_MODEL', 'google/gemma-4-E4B-it')

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }

    payload = {
        'inputs': prompt,
        'parameters': {
            'temperature': 0.1,
            'top_p': 1.0,
            'max_new_tokens': 700,
            'return_full_text': False,
            'do_sample': False,
        },
    }

    def _try(model_id):
        url = f'{base}/{model_id}'
        resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
        if resp.status_code == 410:
            return None, resp
        resp.raise_for_status()
        return resp.json(), resp

    data, resp = _try(model)
    if data is not None:
        return data

    # Try toggling -it suffix if model not found/gated
    if model.endswith('-it'):
        alt = model[:-3]
    else:
        alt = model + '-it'

    data, resp = _try(alt)
    if data is not None:
        return data

    resp.raise_for_status()
    return {}


def _extract_text(resp_json):
    if isinstance(resp_json, list) and resp_json:
        return resp_json[0].get('generated_text', '')
    if isinstance(resp_json, dict) and 'generated_text' in resp_json:
        return resp_json['generated_text']
    return str(resp_json)


def correct_transcript(raw_text: str) -> str:
    prompt = build_correction_prompt(raw_text)
    try:
        resp_json = call_llm(prompt)
        text = _extract_text(resp_json)
        return text.strip()
    except Exception:
        # Fallback: return original transcript to keep pipeline running
        return raw_text


def extract_important_words(text: str, max_words: int = 12):
    prompt = (
        'You are a transcript keyword selector.\\n'
        'Given a transcript, return a JSON array of the most important spoken words.\\n'
        f'- Return at most {max_words} words.\\n'
        '- Use lower-case words only.\\n'
        '- No duplicates.\\n'
        '- Do not add words that were not spoken.\\n'
        '- Return ONLY the JSON array.\\n\\n'
        f'Transcript:\\n{text}'
    )
    try:
        resp_json = call_llm(prompt)
        raw = _extract_text(resp_json)
        data = json.loads(raw)
        if isinstance(data, list):
            out = []
            for w in data:
                if isinstance(w, str) and w.strip():
                    out.append(w.strip().lower())
            # de-dup preserve order
            seen = set()
            result = []
            for w in out:
                if w not in seen:
                    seen.add(w)
                    result.append(w)
            return result[:max_words]
    except Exception:
        pass
    return []


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


def generate_edit_decisions(text, words, captions, max_retries=3):
    prompt = build_edit_decision_prompt(text, words, captions)
    last_err = None
    for _ in range(max_retries):
        try:
            resp_json = call_llm(prompt)
            raw = _extract_text(resp_json)
            data = json.loads(raw)
            valid, errors, normalized = validate_edit_decisions(data)
            if not valid:
                raise ValueError('; '.join(errors))
            return normalized
        except Exception as e:
            last_err = e
            prompt = build_edit_decision_prompt(text, words, captions)
            continue
    return []
