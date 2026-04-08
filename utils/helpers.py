from pathlib import Path

def ensure_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)


def clamp(value, low, high):
    return max(low, min(high, value))


def ms_to_s(ms):
    return ms / 1000.0


def s_to_ms(s):
    return int(s * 1000)
