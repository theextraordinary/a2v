from moviepy import TextClip


def make_caption_clip(text, color='white', font_size=64, width=900):
    return TextClip(
        text=text,
        font_size=font_size,
        color=color,
        size=(width, None),
        method='caption',
        text_align='center',
        horizontal_align='center',
        vertical_align='center'
    )
