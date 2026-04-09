from moviepy import TextClip


def _measure_word(word, font_size, font=None, color='white'):
    clip = TextClip(text=word, font=font, font_size=font_size, color=color, method='label')
    w, h = clip.w, clip.h
    clip.close()
    return w, h


def make_caption_clips(text, color='white', font_size=64, width=900, emphasis=False, font=None, center=(0, 0)):
    if not emphasis:
        clip = TextClip(
            text=text,
            font=font,
            font_size=font_size,
            color=color,
            size=(width, None),
            method='caption',
            text_align='center',
            horizontal_align='center',
            vertical_align='center'
        )
        return [clip]

    words = text.split()
    if not words:
        return []

    # Emphasize the longest word
    emphasis_word = max(words, key=len)

    sizes = []
    for w in words:
        size = int(font_size * (1.2 if w == emphasis_word else 1.0))
        ww, hh = _measure_word(w, size, font=font, color=color)
        sizes.append((w, size, ww, hh))

    space_w, space_h = _measure_word(' ', font_size, font=font, color=color)
    total_w = sum(s[2] for s in sizes) + space_w * (len(words) - 1)

    cx, cy = center
    x = cx - total_w / 2
    clips = []
    for w, size, ww, hh in sizes:
        clip = TextClip(text=w, font=font, font_size=size, color=color, method='label')
        clip = clip.with_position((x, cy - hh / 2))
        clips.append(clip)
        x += ww + space_w

    return clips
