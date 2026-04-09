import json
import os
import requests
from utils.schema import parse_timeline
from .prompt import build_prompt
from utils.config import load_env

OPENAI_ENDPOINT = 'https://api.openai.com/v1/responses'


def _openai_generate(prompt, schema):
    env = load_env()
    api_key = env.get('OPENAI_API_KEY')
    if not api_key:
        raise RuntimeError('OPENAI_API_KEY missing')

    payload = {
        'model': 'gpt-4.1',
        'input': prompt,
        'text': {
            'format': {
                'type': 'json_schema',
                'name': 'caption_timeline',
                'schema': schema,
                'strict': True,
            }
        },
        'temperature': 0.3,
    }

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }
    resp = requests.post(OPENAI_ENDPOINT, headers=headers, data=json.dumps(payload), timeout=60)
    resp.raise_for_status()
    data = resp.json()
    # Extract output text from response items
    output_text = ''
    for item in data.get('output', []):
        if item.get('type') == 'message':
            for c in item.get('content', []):
                if c.get('type') == 'output_text':
                    output_text += c.get('text', '')
    if not output_text:
        # fallback to sdk convenience key if present
        output_text = data.get('output_text', '')
    return output_text


def _gemma_generate(prompt):
    env = load_env()
    api_key = env.get('GEMMA_API_KEY')
    if not api_key:
        raise RuntimeError('GEMMA_API_KEY missing')
    model = env.get('GEMMA_MODEL')
    base = env.get('GEMMA_API_URL').rstrip('/')
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
        }
    }
    resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, list) and data:
        return data[0].get('generated_text', '')
    if isinstance(data, dict) and 'generated_text' in data:
        return data['generated_text']
    raise RuntimeError(f'Unexpected Gemma response: {data}')


def _timeline_schema():
    return {
        'type': 'array',
        'items': {
            'type': 'object',
            'properties': {
                'start': {'type': 'number'},
                'end': {'type': 'number'},
                'text': {'type': 'string'},
                'color': {'type': 'string'},
                'animation': {'type': 'string'},
                'emphasis': {'type': 'boolean'},
            },
            'required': ['start', 'end', 'text', 'color', 'animation', 'emphasis'],
            'additionalProperties': False,
        }
    }


def generate_timeline(segments, max_retries=3):
    load_env()
    prompt = build_prompt(segments)
    schema = _timeline_schema()

    last_err = None
    for _ in range(max_retries):
        try:
            if os.getenv('GEMMA_API_KEY'):
                raw = _gemma_generate(prompt)
            else:
                raw = _openai_generate(prompt, schema)
            return parse_timeline(raw)
        except Exception as e:
            last_err = e
            prompt = prompt + "

The previous JSON was invalid. Return ONLY valid JSON." 
            continue
    raise RuntimeError(f'LLM failed after retries: {last_err}')
