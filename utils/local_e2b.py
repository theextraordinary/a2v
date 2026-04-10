import requests

_LAST_OUTPUTS = {'correction': None, 'important': None, 'decisions': None}


def get_last_output(kind: str):
    return _LAST_OUTPUTS.get(kind)


def _call_e2b_url(prompt: str, e2b_url: str, timeout: int = 120, debug: bool = False, max_new_tokens: int = 1024) -> str:
    url = e2b_url.rstrip('/') + '/generate'
    try:
        resp = requests.post(url, json={'prompt': prompt, 'max_new_tokens': max_new_tokens}, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict) and 'response' in data:
            return str(data['response']).strip()
        if debug:
            print(f'[e2b] URL response missing "response" field: {data}')
        return ''
    except Exception as e:
        if debug:
            print(f'[e2b] URL call failed: {e}')
        raise


def _strip_code_fences(text: str) -> str:
    t = text.strip()
    if t.startswith('```'):
        t = t.split('\n', 1)[-1]
        if t.endswith('```'):
            t = t[:-3]
    return t.strip()


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + '...'


def _build_prompt(text: str) -> str:
    return ('You are correcting an ASR transcript.'
        'Keep the original meaning exactly.'
        'Fix only obvious recognition errors.'
        'Do not add facts or paraphrase.'
        'Keep token count reasonably close.'
        'Return only the corrected transcript text.'
        f'Noisy transcript:{text}'
    )


def correct_transcript_local_e2b(text: str, model_id: str, cache_dir: str | None = None, debug: bool = False, e2b_url: str | None = None):
    try:
        if not e2b_url:
            raise RuntimeError('E2B_URL missing')
        prompt = _build_prompt(text)
        out_text = _call_e2b_url(prompt, e2b_url, debug=debug, max_new_tokens=1024)
        out_text = _strip_code_fences(out_text)
        _LAST_OUTPUTS['correction'] = out_text
        if debug:
            print('[e2b] correction output:', out_text[:300])
            print('[e2b] correction ok')
        return out_text.strip() or text
    except Exception as e:
        if debug:
            print(f'[e2b] correction failed: {e}')
        return text


def extract_important_words_local_e2b(text: str, model_id: str, cache_dir: str | None = None, max_words: int = 12, debug: bool = False, e2b_url: str | None = None):
    prompt = (
        'Extract the most important spoken words from this transcript.\\n'
        f'- Return at most {max_words} words.\\n'
        '- Return a JSON array only.\\n'
        '- Use lowercase words.\\n'
        '- No duplicates.\\n\\n'
        f'Transcript:\\n{text}'
    )
    try:
        if not e2b_url:
            raise RuntimeError('E2B_URL missing')
        out_text = _call_e2b_url(prompt, e2b_url, debug=debug, max_new_tokens=512)
        out_text = _strip_code_fences(out_text)
        _LAST_OUTPUTS['important'] = out_text
        if debug:
            print('[e2b] important words output:', out_text[:300])
            print('[e2b] important words ok')
        import json
        try:
            data = json.loads(out_text)
        except Exception:
            cleaned = out_text.replace('[', '').replace(']', '')
            parts = [p.strip(' "\'') for p in cleaned.replace('\n', ',').split(',')]
            data = [p for p in parts if p]
        if isinstance(data, list):
            out = []
            seen = set()
            for w in data:
                if isinstance(w, str):
                    w = w.strip().lower()
                    if w and w not in seen:
                        seen.add(w)
                        out.append(w)
            return out[:max_words]
    except Exception as e:
        if debug:
            print(f'[e2b] important words failed: {e}')
        return []
    return []


def generate_edit_decisions_local_e2b(text, words, captions, model_id: str, cache_dir: str | None = None, debug: bool = False, e2b_url: str | None = None):
    prompt = (
        'You are an expert short-form video editor.\\n'
        'Given transcript, word timings, and caption groups, return sparse edit decisions.\\n'
        'Allowed decisions: zoom_in, zoom_out, cut, emphasis_caption, meme_insert, broll, sfx_hit, silence_beat, visual_reset.\\n'
        'Return ONLY valid JSON list with: start, end, decision, reason.\\n\\n'
        f'Transcript:\\n{text}\\n\\nWords (compact):\\n{words}\\n\\nCaptions (compact):\\n{captions}'
    )
    try:
        if not e2b_url:
            raise RuntimeError('E2B_URL missing')
        compact = _truncate(prompt, 12000)
        out_text = _call_e2b_url(compact, e2b_url, debug=debug, max_new_tokens=1024)
        out_text = _strip_code_fences(out_text)
        _LAST_OUTPUTS['decisions'] = out_text
        if debug:
            print('[e2b] edit decisions output:', out_text[:300])
            print('[e2b] edit decisions ok')
        import json
        data = json.loads(out_text)
        if isinstance(data, list):
            return data
    except Exception as e:
        if debug:
            print(f'[e2b] edit decisions failed: {e}')
        return []
    return []
