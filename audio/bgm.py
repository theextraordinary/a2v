from pydub import AudioSegment
from collections import Counter

EMOTION_BGM = {
    'motivational': 'upbeat.mp3',
    'sad': 'slow.mp3',
    'calm': 'ambient.mp3',
    'energetic': 'fast.mp3',
}


def dominant_emotion(segments):
    emotions = [s.get('emotion', 'calm') for s in segments]
    if not emotions:
        return 'calm'
    return Counter(emotions).most_common(1)[0][0]


def select_bgm_file(segments, bgm_dir):
    emo = dominant_emotion(segments)
    return bgm_dir / EMOTION_BGM.get(emo, 'ambient.mp3')


def load_bgm(path, target_duration_s, gain_db=-10):
    bgm = AudioSegment.from_file(path)
    bgm = bgm + gain_db
    if len(bgm) <= 0:
        return bgm
    target_ms = int(target_duration_s * 1000)
    loops = (target_ms // len(bgm)) + 1
    bgm = (bgm * loops)[:target_ms]
    return bgm
