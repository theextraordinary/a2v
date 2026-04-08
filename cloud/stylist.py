EMOTION_MAP = {
    'motivational': {'color': 'yellow', 'animation': 'pop'},
    'sad': {'color': 'blue', 'animation': 'fade_in'},
    'calm': {'color': 'white', 'animation': 'fade_in'},
}


def style_segments(segments):
    styled = []
    for seg in segments:
        style = EMOTION_MAP.get(seg.get('emotion', 'calm'), EMOTION_MAP['calm'])
        styled.append({
            'start': seg['start'],
            'end': seg['end'],
            'text': seg['text'],
            'color': style['color'],
            'animation': style['animation'],
        })
    return styled
