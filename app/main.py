from pathlib import Path
import sys
import argparse
import json
import csv

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from utils.config import INPUT_AUDIO, OUTPUT_VIDEO, OUTPUT_DIR, EDGE_WORDS_URL, CLEAN_AUDIO, load_env, E2B_URL
from dotenv import load_dotenv
import os
import re
from utils.helpers import ensure_dir, Timer
from app.client import call_edge_words
from utils.local_e2b import (
    correct_transcript_local_e2b,
    extract_important_words_local_e2b,
    generate_edit_decisions_local_e2b,
    get_last_output,
)
from audio.cleaner import clean_audio
from audio.mixer import mix_audio, mux_av
from video.word_renderer import render_word_video
from pydub import AudioSegment
from utils.text import align_corrected_words, align_corrected_words_with_map, segment_caption_groups


def main():
    parser = argparse.ArgumentParser(description='A2V pipeline')
    parser.add_argument('--bgm', type=str, default=None, help='Optional background music path')
    parser.add_argument('--fps', type=int, default=30, help='Video FPS')
    parser.add_argument('--width', type=int, default=1080, help='Video width')
    parser.add_argument('--height', type=int, default=1920, help='Video height')
    parser.add_argument('--font-size', type=int, default=64, help='Caption font size')
    parser.add_argument('--window', type=int, default=4, help='Caption window size (words)')
    parser.add_argument('--debug', action='store_true', help='Write debug logs')
    parser.add_argument('--sentence-gap', type=float, default=0.7, help='Seconds of silence that start a new sentence')
    parser.add_argument('--hold-last-caption', type=float, default=0.4, help='Seconds to hold last caption during silence')
    parser.add_argument('--bg-color', type=str, default='0,0,0', help='Background color as R,G,B or hex (#000000)')
    parser.add_argument('--font-path', type=str, default=None, help='Optional font path')
    parser.add_argument('--max-width-ratio', type=float, default=0.84, help='Max text width ratio before wrapping')
    parser.add_argument('--fade-in', type=float, default=0.12, help='Seconds for micro fade-in per word')
    parser.add_argument('--accent-color', type=str, default='53,184,199', help='Accent color for important words')
    parser.add_argument('--emphasis-seed', type=int, default=1337, help='Deterministic emphasis seed')
    args = parser.parse_args()

    # Ensure .env is loaded before reading E2B_URL
    env_path = ROOT / '.env'
    if env_path.exists():
        load_dotenv(env_path, override=True)
    env = load_env()
    ensure_dir(OUTPUT_DIR)

    if not INPUT_AUDIO.exists():
        raise FileNotFoundError(f'Missing input audio: {INPUT_AUDIO}')

    with Timer('Audio clean'):
        cleaned_path, _ = clean_audio(INPUT_AUDIO, CLEAN_AUDIO)
        if not cleaned_path.exists():
            # Fallback: keep original audio to avoid silent output
            cleaned_path = INPUT_AUDIO

    audio = AudioSegment.from_file(cleaned_path)
    audio_duration = len(audio) / 1000.0
    print(f'[debug] Audio duration: {audio_duration:.2f}s')

    with Timer('Edge service (word timestamps)'):
        words = call_edge_words(cleaned_path, EDGE_WORDS_URL)
        print(f'[debug] Word count: {len(words)}')

    # Correct transcript via Gemma E4B (cloud API) and map back to word timings
    with Timer('Cloud correction'):
        raw_text = ' '.join([w['word'] for w in words])
        e2b_url = os.getenv('E2B_URL', '') or E2B_URL or env.get('E2B_URL', '')
        if not e2b_url:
            raise RuntimeError('E2B_URL is missing in .env')
        print(f'[e2b] Using E2B_URL: {e2b_url}')
        corrected_text = correct_transcript_local_e2b(raw_text, '', None, debug=True, e2b_url=e2b_url)
        if corrected_text.strip() and corrected_text.strip() != raw_text.strip():
            print('[e2b] correction applied')
        else:
            print('[e2b] correction produced no changes (or failed)')
        if args.debug:
            logs_dir = OUTPUT_DIR.parent / 'logs'
            ensure_dir(logs_dir)
            (logs_dir / 'e2b_raw_transcript.txt').write_text(raw_text, encoding='utf-8')
            (logs_dir / 'e2b_corrected_transcript.txt').write_text(corrected_text, encoding='utf-8')
            raw_out = get_last_output('correction')
            if raw_out:
                (logs_dir / 'e2b_correction_raw.txt').write_text(raw_out, encoding='utf-8')
        if args.debug:
            corrected_words, mapping = align_corrected_words_with_map(words, corrected_text, sentence_gap_s=args.sentence_gap)
        else:
            corrected_words = align_corrected_words(words, corrected_text, sentence_gap_s=args.sentence_gap)

    # Important words (local E2B)
    important_words = extract_important_words_local_e2b(
        corrected_text,
        '',
        None,
        max_words=12,
        debug=True,
        e2b_url=e2b_url,
    )
    if important_words:
        print(f'[e2b] important words count: {len(important_words)}')
    else:
        print('[e2b] important words empty or failed')
    if args.debug:
        logs_dir = OUTPUT_DIR.parent / 'logs'
        ensure_dir(logs_dir)
        raw_out = get_last_output('important')
        if raw_out:
            (logs_dir / 'e2b_important_raw.txt').write_text(raw_out, encoding='utf-8')

    def _norm_token(s: str) -> str:
        return re.sub(r'[^a-z0-9]+', '', s.lower())

    important_tokens = set()
    for phrase in important_words:
        for part in str(phrase).split():
            tok = _norm_token(part)
            if tok:
                important_tokens.add(tok)

    for w in corrected_words:
        token = _norm_token(w['word'])
        w['important'] = token in important_tokens

    # Caption groups (deterministic)
    caption_groups = segment_caption_groups(
        corrected_words,
        silence_gap_s=args.sentence_gap,
        max_words_per_group=args.window,
        sentence_gap_s=args.sentence_gap,
        avoid_single_trailing_word=True,
    )

    # Edit decisions (local E2B) - non-fatal
    edit_decisions = generate_edit_decisions_local_e2b(
        corrected_text,
        corrected_words,
        caption_groups,
        '',
        None,
        debug=True,
        e2b_url=e2b_url,
    )
    if edit_decisions:
        print(f'[e2b] edit decisions: {len(edit_decisions)}')
    else:
        print('[e2b] edit decisions empty or failed')
    if args.debug:
        logs_dir = OUTPUT_DIR.parent / 'logs'
        ensure_dir(logs_dir)
        raw_out = get_last_output('decisions')
        if raw_out:
            (logs_dir / 'e2b_edit_decisions_raw.txt').write_text(raw_out, encoding='utf-8')

    sentence_count = len(set(w['sentence_id'] for w in corrected_words)) if corrected_words else 0
    avg_pause = 0.0
    if corrected_words and len(corrected_words) > 1:
        avg_pause = sum(w['pause_before'] for w in corrected_words[1:]) / (len(corrected_words) - 1)
    print(f'[debug] Corrected words: {len(corrected_words)} | Same length: {len(words) == len(corrected_words)}')
    print(f'[debug] Sentences: {sentence_count} | Avg pause: {avg_pause:.3f}s')

    def _parse_color(s):
        s = s.strip()
        if s.startswith('#') and len(s) == 7:
            return tuple(int(s[i:i+2], 16) for i in (1, 3, 5))
        parts = s.split(',')
        if len(parts) == 3:
            return tuple(int(p) for p in parts)
        return (0, 0, 0)

    def _invert_color(c):
        return (255 - c[0], 255 - c[1], 255 - c[2])

    def _accent_color(base, bg):
        # Keep contrast while ensuring accent differs from base
        if sum(base) > 600:
            # Light base (dark background) -> teal accent
            return (53, 184, 199)
        # Dark base (light background) -> warm accent
        return (235, 120, 60)

    if args.debug:
        logs_dir = OUTPUT_DIR.parent / 'logs'
        ensure_dir(logs_dir)
        (logs_dir / 'words_raw.json').write_text(json.dumps(words, ensure_ascii=False, indent=2), encoding='utf-8')
        (logs_dir / 'transcript_raw.txt').write_text(raw_text, encoding='utf-8')
        (logs_dir / 'transcript_corrected.txt').write_text(corrected_text, encoding='utf-8')
        (logs_dir / 'important_words.json').write_text(json.dumps(important_words, ensure_ascii=False, indent=2), encoding='utf-8')
        (logs_dir / 'caption_groups.json').write_text(json.dumps(caption_groups, ensure_ascii=False, indent=2), encoding='utf-8')
        (logs_dir / 'edit_decisions.json').write_text(json.dumps(edit_decisions, ensure_ascii=False, indent=2), encoding='utf-8')
        with open(logs_dir / 'words_raw.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['index', 'word', 'start', 'end'])
            for i, w in enumerate(words):
                writer.writerow([i, w['word'], w['start'], w['end']])
        with open(logs_dir / 'mapping.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['index', 'start', 'end', 'original', 'corrected', 'changed', 'sentence_id', 'pause_before', 'pause_after'])
            for m in mapping:
                writer.writerow([m['index'], m['start'], m['end'], m['original_word'], m['corrected_word'], m['changed'], m['sentence_id'], m['pause_before'], m['pause_after']])

        sentence_count = len(set(m['sentence_id'] for m in mapping)) if mapping else 0
        avg_pause = sum(m['pause_before'] for m in mapping[1:]) / max(1, len(mapping) - 1)
        (logs_dir / 'stats.json').write_text(json.dumps({
            'audio_duration_s': audio_duration,
            'video_fps': args.fps,
            'original_word_count': len(words),
            'corrected_word_count': len(corrected_words),
            'mapped_same_length': len(words) == len(corrected_words),
            'sentence_count': sentence_count,
            'average_pause_s': avg_pause,
        }, indent=2), encoding='utf-8')

    silent_video = OUTPUT_DIR / 'silent.mp4'
    with Timer('Render word video'):
        bg = _parse_color(args.bg_color)
        base_color = _invert_color(bg)
        accent_color = _accent_color(base_color, bg)
        video_duration, frames = render_word_video(
            caption_groups,
            silent_video,
            size=(args.width, args.height),
            fps=args.fps,
            font_size=args.font_size,
            duration=audio_duration,
            window=args.window,
            sentence_gap_s=args.sentence_gap,
            hold_last_caption_s=args.hold_last_caption,
            bg_color=bg,
            font_path=args.font_path,
            max_width_ratio=args.max_width_ratio,
            fade_in_s=args.fade_in,
            accent_color=accent_color,
            base_color=base_color,
            emphasis_seed=args.emphasis_seed,
        )
        print(f'[debug] Video duration: {video_duration:.2f}s | Frames: {frames}')

    mixed_audio = OUTPUT_DIR / 'mixed.m4a'
    with Timer('Mix audio'):
        mix_audio(cleaned_path, args.bgm, mixed_audio)

    with Timer('Mux A/V'):
        mux_av(silent_video, mixed_audio, OUTPUT_VIDEO)

    # Export final timeline/metadata JSON for re-rendering without models
    manifest = {
        'audio': {
            'speech_path': str(cleaned_path),
            'bgm_path': args.bgm,
            'mixed_audio_path': str(mixed_audio),
            'duration_s': audio_duration,
        },
        'video': {
            'output_path': str(OUTPUT_VIDEO),
            'silent_video_path': str(silent_video),
            'size': {'width': args.width, 'height': args.height},
            'fps': args.fps,
            'bg_color': bg,
            'font_path': args.font_path,
            'font_size': args.font_size,
            'base_color': base_color,
            'accent_color': accent_color,
        },
        'captions': {
            'window': args.window,
            'sentence_gap_s': args.sentence_gap,
            'hold_last_caption_s': args.hold_last_caption,
            'max_width_ratio': args.max_width_ratio,
            'fade_in_s': args.fade_in,
            'words': corrected_words,
            'groups': caption_groups,
            'important_words': sorted(list(important_tokens)),
        },
        'edit_decisions': edit_decisions,
        'timing': {
            'word_count': len(corrected_words),
            'sentence_count': sentence_count,
            'avg_pause_s': avg_pause,
        },
    }
    manifest_path = OUTPUT_DIR / 'video_manifest.json'
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f'Video saved to: {OUTPUT_VIDEO}')


if __name__ == '__main__':
    main()
