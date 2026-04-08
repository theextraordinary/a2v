from .asr import transcribe_audio
from .segmentation import segment_audio
from .emotion import classify_emotion
<<<<<<< HEAD
=======
from utils.helpers import Timer, edge_sleep
>>>>>>> a19e444 (Added basic files and folders)


def _overlap(a_start, a_end, b_start, b_end):
    return max(a_start, b_start) < min(a_end, b_end)


<<<<<<< HEAD
def process_audio(audio_path):
    asr_segments = transcribe_audio(audio_path)
    speech_segments = segment_audio(audio_path)
=======
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
>>>>>>> a19e444 (Added basic files and folders)

    refined = []
    for seg in asr_segments:
        start = seg['start']
        end = seg['end']
<<<<<<< HEAD
=======
        if max_duration_s is not None:
            if start >= max_duration_s:
                continue
            end = min(end, max_duration_s)
>>>>>>> a19e444 (Added basic files and folders)
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
