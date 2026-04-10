import json

REQUIRED_KEYS = {'start', 'end', 'text', 'color', 'animation', 'emphasis'}


def _is_number(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def validate_timeline(data):
    errors = []
    if not isinstance(data, list):
        errors.append('Timeline must be a list')
        return False, errors, []

    normalized = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            errors.append(f'Item {i} must be an object')
            continue
        missing = REQUIRED_KEYS - set(item.keys())
        if missing:
            errors.append(f'Item {i} missing keys: {sorted(missing)}')
            continue
        try:
            start = float(item['start'])
            end = float(item['end'])
        except Exception:
            errors.append(f'Item {i} start/end must be numbers')
            continue
        text = item['text']
        color = item['color']
        animation = item['animation']
        emphasis = item['emphasis']
        if not isinstance(text, str):
            errors.append(f'Item {i} text must be string')
            continue
        if not isinstance(color, str):
            errors.append(f'Item {i} color must be string')
            continue
        if not isinstance(animation, str):
            errors.append(f'Item {i} animation must be string')
            continue
        if not isinstance(emphasis, bool):
            errors.append(f'Item {i} emphasis must be boolean')
            continue
        if end <= start:
            errors.append(f'Item {i} end must be > start')
            continue
        normalized.append({
            'start': start,
            'end': end,
            'text': text.strip(),
            'color': color.strip(),
            'animation': animation.strip(),
            'emphasis': emphasis,
        })

    if errors:
        return False, errors, []
    return True, [], normalized


def parse_timeline(text):
    try:
        data = json.loads(text)
    except Exception as e:
        raise ValueError(f'Invalid JSON: {e}')
    valid, errors, normalized = validate_timeline(data)
    if not valid:
        raise ValueError('; '.join(errors))
    return normalized


def validate_caption_groups(data):
    errors = []
    if not isinstance(data, list):
        return False, ['Caption groups must be a list'], []
    normalized = []
    for i, g in enumerate(data):
        if not isinstance(g, dict):
            errors.append(f'Group {i} must be object')
            continue
        if 'words' not in g or not isinstance(g['words'], list):
            errors.append(f'Group {i} must include words list')
            continue
        if not g['words']:
            errors.append(f'Group {i} words empty')
            continue
        try:
            start = float(g['start'])
            end = float(g['end'])
        except Exception:
            errors.append(f'Group {i} start/end must be numbers')
            continue
        norm_words = []
        for w in g['words']:
            if not isinstance(w, dict) or 'word' not in w:
                errors.append(f'Group {i} word invalid')
                continue
            norm_words.append({
                'word': str(w['word']),
                'start': float(w.get('start', start)),
                'end': float(w.get('end', end)),
            })
        normalized.append({
            'group_id': int(g.get('group_id', i)),
            'start': start,
            'end': end,
            'words': norm_words,
        })
    if errors:
        return False, errors, []
    return True, [], normalized


def validate_edit_decisions(data):
    errors = []
    if not isinstance(data, list):
        return False, ['Decisions must be list'], []
    normalized = []
    allowed = {'zoom_in', 'zoom_out', 'cut', 'emphasis_caption', 'meme_insert', 'broll', 'sfx_hit', 'silence_beat', 'visual_reset'}
    for i, d in enumerate(data):
        if not isinstance(d, dict):
            errors.append(f'Decision {i} must be object')
            continue
        try:
            start = float(d['start'])
            end = float(d['end'])
        except Exception:
            errors.append(f'Decision {i} start/end must be numbers')
            continue
        decision = d.get('decision')
        reason = d.get('reason', '')
        if decision not in allowed:
            errors.append(f'Decision {i} invalid decision')
            continue
        normalized.append({
            'start': start,
            'end': end,
            'decision': decision,
            'reason': str(reason),
        })
    if errors:
        return False, errors, []
    return True, [], normalized
