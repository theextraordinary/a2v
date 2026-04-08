from pydub import AudioSegment


def load_bgm(path, target_duration_s, gain_db=-10):
    bgm = AudioSegment.from_file(path)
    bgm = bgm + gain_db
    if len(bgm) <= 0:
        return bgm
    target_ms = int(target_duration_s * 1000)
    loops = (target_ms // len(bgm)) + 1
    bgm = (bgm * loops)[:target_ms]
    return bgm
