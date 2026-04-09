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
