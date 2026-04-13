from pydub import AudioSegment
from pydub.effects import normalize
from pydub.silence import detect_nonsilent
from pathlib import Path
import shutil


def trim_silence(audio, min_silence_len=500, silence_thresh=-40):
    ranges = detect_nonsilent(audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh)
    if not ranges:
        return audio
    start = ranges[0][0]
    end = ranges[-1][1]
    return audio[start:end]


def clean_audio(input_path, output_path, min_silence_len=500, silence_thresh=-40, max_duration_s=None):
    input_path = Path(input_path)
    output_path = Path(output_path)
    audio = AudioSegment.from_file(input_path)
    audio = normalize(audio)
    audio = trim_silence(audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh)
    if max_duration_s is not None:
        audio = audio[: int(max_duration_s * 1000)]

    try:
        audio.export(output_path, format='wav')
    except Exception:
        # Fallback: if export fails, copy original (keeps audio available)
        shutil.copyfile(input_path, output_path)
        return output_path, audio.duration_seconds

    duration_s = len(audio) / 1000.0
    return output_path, duration_s
