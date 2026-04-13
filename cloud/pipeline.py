from .stylist import generate_timeline, generate_edit_decisions


def _fallback_style(segments):
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


def run_cloud_pipeline(segments):
    timeline = generate_timeline(segments)
    # Ensure timing sync with original segments
    if len(timeline) != len(segments):
        return _fallback_style(segments)

    aligned = []
    for seg, styled in zip(segments, timeline):
        aligned.append({
            'start': float(seg['start']),
            'end': float(seg['end']),
            'text': styled.get('text', seg['text']),
            'color': styled.get('color', 'white'),
            'animation': styled.get('animation', 'minimal'),
            'emphasis': bool(styled.get('emphasis', False)),
        })
    return aligned


def run_edit_decisions(text, words, captions):
    return generate_edit_decisions(text, words, captions)
