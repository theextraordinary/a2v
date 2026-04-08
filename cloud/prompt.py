import json


def build_prompt(segments):
    system = (
        'You are a caption styling model. Return JSON array with keys: '
        'start, end, text, color, animation.'
    )
    payload = json.dumps(segments, ensure_ascii=True)
    return system + '
Input segments:
' + payload
