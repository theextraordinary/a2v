from .asr import transcribe_audio
from .segmentation import segment_audio
from .emotion import classify_emotion


def _overlap(a_start, a_end, b_start, b_end):
    return max(a_start, b_start) < min(a_end, b_end)


def process_audio(audio_path):
    asr_segments = transcribe_audio(audio_path)
    speech_segments = segment_audio(audio_path)

    refined = []
    for seg in asr_segments:
        start = seg['start']
        end = seg['end']
        for s in speech_segments:
            if _overlap(start, end, s['start'], s['end']):
                start = max(start, s['start'])
                end = min(end, s['end'])
                break
        text = seg['text']
        emotion = classify_emotion(text)
        refined.append({
            'start': start,
            'end': end,
            'text': text,
            'emotion': emotion,
        })

    return refined
