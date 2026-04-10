from .asr import transcribe_audio, transcribe_words
from .segmentation import segment_audio
from .emotion import classify_emotion
from utils.helpers import Timer, edge_sleep


def _overlap(a_start, a_end, b_start, b_end):
    return max(a_start, b_start) < min(a_end, b_end)


def process_audio(audio_path, model_size='base', use_mock_asr=False, max_duration_s=None, latency_s=0.0):
    with Timer('ASR'):
        asr_segments = transcribe_audio(
            audio_path,
            model_size=model_size,
            use_mock=use_mock_asr,
            latency_s=latency_s,
        )
    with Timer('Segmentation'):
        speech_segments = segment_audio(audio_path)
    edge_sleep(latency_s)

    refined = []
    for seg in asr_segments:
        start = seg['start']
        end = seg['end']
        if max_duration_s is not None:
            if start >= max_duration_s:
                continue
            end = min(end, max_duration_s)
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


def process_words(audio_path, model_size='base'):
    return transcribe_words(audio_path, model_size=model_size)
