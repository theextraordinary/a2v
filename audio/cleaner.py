from pydub import AudioSegment
from pydub.effects import normalize
from pydub.silence import detect_nonsilent


def trim_silence(audio, min_silence_len=500, silence_thresh=-40):
    ranges = detect_nonsilent(audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh)
    if not ranges:
        return audio
    start = ranges[0][0]
    end = ranges[-1][1]
    return audio[start:end]


<<<<<<< HEAD
def clean_audio(input_path, output_path, min_silence_len=500, silence_thresh=-40):
    audio = AudioSegment.from_file(input_path)
    audio = normalize(audio)
    audio = trim_silence(audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh)
=======
def clean_audio(input_path, output_path, min_silence_len=500, silence_thresh=-40, max_duration_s=None):
    audio = AudioSegment.from_file(input_path)
    audio = normalize(audio)
    audio = trim_silence(audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh)
    if max_duration_s is not None:
        audio = audio[: int(max_duration_s * 1000)]
>>>>>>> a19e444 (Added basic files and folders)
    audio.export(output_path, format='wav')
    duration_s = len(audio) / 1000.0
    return output_path, duration_s
