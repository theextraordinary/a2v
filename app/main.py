from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from utils.config import INPUT_AUDIO, CLEAN_AUDIO, OUTPUT_VIDEO, OUTPUT_DIR, load_env
from utils.helpers import ensure_dir
from audio.cleaner import clean_audio
from edge.processor import process_audio
from cloud.pipeline import run_cloud_pipeline
from video.renderer import render_video


def main():
    load_env()
    ensure_dir(OUTPUT_DIR)

    if not INPUT_AUDIO.exists():
        raise FileNotFoundError(f'Missing input audio: {INPUT_AUDIO}')

    cleaned_path, duration = clean_audio(INPUT_AUDIO, CLEAN_AUDIO)
    segments = process_audio(cleaned_path)

    if not segments:
        segments = [{
            'start': 0.0,
            'end': duration,
            'text': 'Your caption goes here',
            'emotion': 'calm',
        }]

    styled = run_cloud_pipeline(segments)
    render_video(styled, cleaned_path, OUTPUT_VIDEO)
    print(f'Video saved to: {OUTPUT_VIDEO}')


if __name__ == '__main__':
    main()
