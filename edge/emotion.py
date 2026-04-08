def classify_emotion(text):
    t = text.lower()
    if 'success' in t or 'win' in t:
        return 'motivational'
    if 'sad' in t or 'lost' in t:
        return 'sad'
    return 'calm'
