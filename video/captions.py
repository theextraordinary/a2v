from moviepy.editor import TextClip


def make_caption_clip(text, color='white', font_size=64, width=900):
    return TextClip(
        txt=text,
        fontsize=font_size,
        color=color,
        size=(width, None),
        method='caption',
        align='center'
    )
