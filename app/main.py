from pathlib import Path
import sys
import argparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from utils.config import INPUT_AUDIO, OUTPUT_VIDEO, OUTPUT_DIR, EDGE_URL, CLOUD_URL, load_env
from utils.helpers import ensure_dir, Timer
from video.renderer import render_video
from app.client import call_edge, call_cloud


def main():
    parser = argparse.ArgumentParser(description='A2V pipeline')
    args = parser.parse_args()

    load_env()
    ensure_dir(OUTPUT_DIR)

    if not INPUT_AUDIO.exists():
        raise FileNotFoundError(f'Missing input audio: {INPUT_AUDIO}')

    with Timer('Edge service'):
        segments = call_edge(INPUT_AUDIO, EDGE_URL)

    with Timer('Cloud service'):
        timeline = call_cloud(segments, CLOUD_URL)

    with Timer('Render video'):
        render_video(timeline, INPUT_AUDIO, OUTPUT_VIDEO)

    print(f'Video saved to: {OUTPUT_VIDEO}')


if __name__ == '__main__':
    main()
