from .prompt import build_prompt
from .stylist import style_segments


def run_cloud_pipeline(segments):
    _ = build_prompt(segments)
    return style_segments(segments)
