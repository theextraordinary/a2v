from pydub import AudioSegment
from pydub.silence import detect_nonsilent


def segment_audio(audio_path, min_silence_len=500, silence_thresh=-40):
    audio = AudioSegment.from_file(audio_path)
    ranges = detect_nonsilent(audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh)
    segments = []
    for start_ms, end_ms in ranges:
        segments.append({
            'start': start_ms / 1000.0,
            'end': end_ms / 1000.0,
        })
    return segments
