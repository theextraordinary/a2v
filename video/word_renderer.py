from pathlib import Path
import math
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import imageio


def _load_font(font_size, font_path=None, bold=False):
    if font_path:
        try:
            return ImageFont.truetype(font_path, font_size)
        except Exception:
            pass
    if bold:
        candidates = ['C:/Windows/Fonts/segoeuib.ttf', 'C:/Windows/Fonts/arialbd.ttf']
    else:
        candidates = ['C:/Windows/Fonts/segoeui.ttf', 'C:/Windows/Fonts/arial.ttf']
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, font_size)
        except Exception:
            continue
    return ImageFont.load_default()


def _measure_text(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _font_metrics(font):
    try:
        ascent, descent = font.getmetrics()
        return ascent, descent
    except Exception:
        return font.size, int(font.size * 0.25)


def _get_active_sentence(sentences, t, hold_last_caption_s):
    active = None
    for s in sentences:
        if s['start'] <= t <= s['end']:
            return s
        if s['end'] < t:
            active = s
        if s['start'] > t:
            break
    if active is not None and t - active['end'] <= hold_last_caption_s:
        return active
    return None


def get_visible_window_for_time(words, sentence, t, window_size):
    indices = sentence['indices']
    started = [i for i in indices if words[i]['start'] <= t]
    if not started:
        return []
    # Non-overlapping groups: once we move to next group, we do not show previous words.
    started_count = len(started)
    chunk_idx = (started_count - 1) // window_size
    chunk_start = chunk_idx * window_size
    chunk_end = min(len(indices), chunk_start + window_size)
    chunk_indices = indices[chunk_start:chunk_end]
    # Show only words in current chunk that have started
    return [i for i in chunk_indices if words[i]['start'] <= t]


def _blend_color(bg, fg, alpha):
    return (
        int(bg[0] * (1 - alpha) + fg[0] * alpha),
        int(bg[1] * (1 - alpha) + fg[1] * alpha),
        int(bg[2] * (1 - alpha) + fg[2] * alpha),
    )


def render_one_word(draw, word, font, color, width, height):
    w, h = _measure_text(draw, word, font)
    x = (width - w) / 2
    y = (height - h) / 2
    draw.text((x, y), word, font=font, fill=color)


def render_two_words(draw, w1, w2, font, color, width, height, space_w):
    w1_size = _measure_text(draw, w1, font)
    w2_size = _measure_text(draw, w2, font)
    total_w = w1_size[0] + space_w + w2_size[0]
    x = (width - total_w) / 2
    y = (height - max(w1_size[1], w2_size[1])) / 2
    draw.text((x, y), w1, font=font, fill=color)
    x += w1_size[0] + space_w
    draw.text((x, y), w2, font=font, fill=color)


def render_line_caption(draw, words, current_idx, fonts, colors, width, height, space_w, bg_color, t, word_times, word_colors):
    f_base, _ = fonts
    c_text, _ = colors
    sizes = [_measure_text(draw, w, f_base) for i, w in enumerate(words)]
    total_w = sum(s[0] for s in sizes) + space_w * (len(words) - 1)
    line_h = max(s[1] for s in sizes)
    x = (width - total_w) / 2
    y = (height - line_h) / 2

    for i, w in enumerate(words):
        font = f_base
        text_w, text_h = sizes[i]
        color = word_colors[i] if word_colors is not None else c_text
        draw.text((x, y), w, font=font, fill=color)
        x += text_w + space_w


def render_word_video(
    words,
    output_path,
    size=(1080, 1920),
    fps=30,
    font_size=64,
    duration=None,
    window=3,
    sentence_gap_s=0.7,
    hold_last_caption_s=0.4,
    bg_color=(0, 0, 0),
    font_path=None,
    base_color=(255, 255, 255),
    accent_color=(255, 255, 255),
    max_width_ratio=0.84,
    fade_in_s=0.12,
    emphasis_seed=1337,
    highlight_fill=(255, 255, 255),
):
    output_path = Path(output_path)
    width, height = size
    bg = bg_color

    # Accept either list of words or grouped captions
    groups = None
    if words and isinstance(words, list) and isinstance(words[0], dict) and 'words' in words[0]:
        groups = words
        words = [w for g in groups for w in g.get('words', [])]

    if not words:
        words = [{'word': 'No words', 'start': 0.0, 'end': 1.0, 'sentence_id': 0}]

    if duration is None:
        duration = max(w['end'] for w in words)
    total_frames = int(math.ceil(duration * fps))

    # Build sentence groups (fallback mode)
    sentences = []
    if groups is None:
        current_id = None
        current_indices = []
        for i, w in enumerate(words):
            sid = w.get('sentence_id', 0)
            if current_id is None:
                current_id = sid
            if sid != current_id:
                if current_indices:
                    sentences.append({
                        'id': current_id,
                        'indices': current_indices,
                        'start': words[current_indices[0]]['start'],
                        'end': words[current_indices[-1]]['end'],
                    })
                current_id = sid
                current_indices = []
            current_indices.append(i)
        if current_indices:
            sentences.append({
                'id': current_id,
                'indices': current_indices,
                'start': words[current_indices[0]]['start'],
                'end': words[current_indices[-1]]['end'],
            })
    else:
        # Convert groups into sentence-like list for timing
        sentences = [{'id': g.get('group_id', i), 'idx': i, 'indices': [idx for idx in range(len(g.get('words', [])))], 'start': g['start'], 'end': g['end']} for i, g in enumerate(groups)]

    writer = imageio.get_writer(
        str(output_path),
        fps=fps,
        codec='libx264',
        format='ffmpeg',
        ffmpeg_params=['-pix_fmt', 'yuv420p'],
    )

    base_font = _load_font(font_size, font_path=font_path, bold=True)
    bold_font = _load_font(int(font_size * 1.05), font_path=font_path, bold=True)
    space_w, _ = _measure_text(ImageDraw.Draw(Image.new('RGB', (10, 10))), ' ', base_font)

    for i in range(total_frames):
        t = i / fps
        frame = Image.new('RGB', (width, height), bg)
        draw = ImageDraw.Draw(frame)

        sentence = _get_active_sentence(sentences, t, hold_last_caption_s)
        if sentence is None:
            writer.append_data(np.array(frame))
            continue

        if groups is None:
            visible_indices = get_visible_window_for_time(words, sentence, t, window)
            group_words = words
            group_indices = visible_indices
        else:
            # sentence here is a group; show words that have started in this group
            g = groups[sentence['idx']]
            group_words = g.get('words', [])
            group_indices = [i for i, w in enumerate(group_words) if w['start'] <= t]
            visible_indices = group_indices
        if not visible_indices:
            writer.append_data(np.array(frame))
            continue

        # Partial states: 1 or 2 words visible (highlight current word)
        if len(visible_indices) == 1:
            words_text = [group_words[i]['word'] for i in visible_indices]
            times = [(group_words[i]['start'], group_words[i]['end']) for i in visible_indices]
            current_idx = 0
            render_line_caption(
                draw,
                words_text,
                current_idx,
                (base_font, bold_font),
                (base_color, highlight_fill),
                width,
                height,
                space_w,
                bg,
                t,
                times,
                [accent_color if group_words[i].get('important') else base_color for i in visible_indices],
            )
            writer.append_data(np.array(frame))
            continue
        if len(visible_indices) == 2:
            words_text = [group_words[i]['word'] for i in visible_indices]
            times = [(group_words[i]['start'], group_words[i]['end']) for i in visible_indices]
            current_idx = len(visible_indices) - 1
            render_line_caption(
                draw,
                words_text,
                current_idx,
                (base_font, bold_font),
                (base_color, highlight_fill),
                width,
                height,
                space_w,
                bg,
                t,
                times,
                [accent_color if group_words[i].get('important') else base_color for i in visible_indices],
            )
            writer.append_data(np.array(frame))
            continue

        # 3-word chunk (strict order preserved, highlight current word)
        if len(visible_indices) == 3:
            words_text = [group_words[i]['word'] for i in visible_indices]
            times = [(group_words[i]['start'], group_words[i]['end']) for i in visible_indices]
            current_idx = len(visible_indices) - 1
            render_line_caption(
                draw,
                words_text,
                current_idx,
                (base_font, bold_font),
                (base_color, highlight_fill),
                width,
                height,
                space_w,
                bg,
                t,
                times,
                [accent_color if group_words[i].get('important') else base_color for i in visible_indices],
            )
            writer.append_data(np.array(frame))
            continue

        # If more than 3 visible, enforce last 3 (order preserved)
        last3 = visible_indices[-3:]
        words_text = [group_words[i]['word'] for i in last3]
        times = [(group_words[i]['start'], group_words[i]['end']) for i in last3]
        current_idx = len(last3) - 1
        render_line_caption(
            draw,
            words_text,
            current_idx,
            (base_font, bold_font),
            (base_color, highlight_fill),
            width,
            height,
            space_w,
            bg,
            t,
            times,
            [accent_color if group_words[i].get('important') else base_color for i in last3],
        )
        writer.append_data(np.array(frame))

    writer.close()
    return duration, total_frames
