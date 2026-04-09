import whisper
from pydub import AudioSegment
from utils.helpers import edge_sleep


def _mock_segments(audio_path):
    audio = AudioSegment.from_file(audio_path)
    duration = len(audio) / 1000.0
    if duration <= 1.0:
        return [{'start': 0.0, 'end': duration, 'text': 'Edge mode sample'}]
    mid = duration / 2.0
    return [
        {'start': 0.0, 'end': mid, 'text': 'Edge mode sample'},
        {'start': mid, 'end': duration, 'text': 'Simulated transcription'},
    ]


def transcribe_audio(audio_path, model_size='base', use_mock=False, latency_s=0.0):
    if use_mock:
        edge_sleep(latency_s)
        return _mock_segments(audio_path)
    model = whisper.load_model(model_size)
    result = model.transcribe(str(audio_path), fp16=False)
    segments = []
    for seg in result.get('segments', []):
        segments.append({
            'start': float(seg['start']),
            'end': float(seg['end']),
            'text': seg['text'].strip(),
        })
    return segments
