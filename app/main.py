from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

import argparse
from utils.config import INPUT_AUDIO, CLEAN_AUDIO, OUTPUT_VIDEO, OUTPUT_DIR, load_env
from utils.helpers import ensure_dir, Timer
from audio.cleaner import clean_audio
from edge.processor import process_audio
from cloud.pipeline import run_cloud_pipeline
from video.renderer import render_video


def main():
    parser = argparse.ArgumentParser(description='A2V pipeline')
    parser.add_argument('--edge', action='store_true', help='Simulate edge device constraints')
    parser.add_argument('--edge-real-asr', action='store_true', help='Use real ASR in edge mode')
    parser.add_argument('--edge-max-duration', type=float, default=20.0, help='Max seconds to process in edge mode')
    parser.add_argument('--edge-latency', type=float, default=0.2, help='Simulated latency per step (seconds)')
    args = parser.parse_args()

    edge_mode = args.edge
    use_mock_asr = edge_mode and not args.edge_real_asr
    model_size = 'tiny' if edge_mode else 'base'
    max_duration_s = args.edge_max_duration if edge_mode else None
    latency_s = args.edge_latency if edge_mode else 0.0
    size = (540, 960) if edge_mode else (1080, 1920)
    fps = 24 if edge_mode else 30

    load_env()
    ensure_dir(OUTPUT_DIR)

    if not INPUT_AUDIO.exists():
        raise FileNotFoundError(f'Missing input audio: {INPUT_AUDIO}')

    with Timer('Audio clean'):
        cleaned_path, duration = clean_audio(INPUT_AUDIO, CLEAN_AUDIO, max_duration_s=max_duration_s)
    segments = process_audio(
        cleaned_path,
        model_size=model_size,
        use_mock_asr=use_mock_asr,
        max_duration_s=max_duration_s,
        latency_s=latency_s,
    )

    if not segments:
        segments = [{
            'start': 0.0,
            'end': duration,
            'text': 'Your caption goes here',
            'emotion': 'calm',
        }]

    with Timer('Cloud pipeline'):
        styled = run_cloud_pipeline(segments)
    with Timer('Render video'):
        render_video(styled, cleaned_path, OUTPUT_VIDEO, size=size, fps=fps)
    print(f'Video saved to: {OUTPUT_VIDEO}')


if __name__ == '__main__':
    main()
