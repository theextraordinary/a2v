from pathlib import Path
import time

def ensure_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)


def clamp(value, low, high):
    return max(low, min(high, value))


def ms_to_s(ms):
    return ms / 1000.0


def s_to_ms(s):
    return int(s * 1000)


class Timer:
    def __init__(self, label):
        self.label = label
        self.start = None

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb):
        end = time.perf_counter()
        ms = (end - self.start) * 1000.0
        print(f'[edge] {self.label} took {ms:.1f} ms')


def edge_sleep(seconds):
    if seconds and seconds > 0:
        time.sleep(seconds)
