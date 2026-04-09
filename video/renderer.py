from moviepy import ColorClip, CompositeVideoClip, AudioFileClip
from .captions import make_caption_clips
from .animations import fade_in, pop, slide_up, minimal


def render_video(styled_segments, audio_path, output_path, size=(1080, 1920), fps=30):
    audio = AudioFileClip(str(audio_path))
    audio = audio.with_start(0)
    duration = audio.duration or 0.0
    if duration <= 0 and styled_segments:
        duration = max(float(s['end']) for s in styled_segments)
    if duration <= 0:
        duration = 1.0
    base = ColorClip(size=size, color=(0, 0, 0), duration=duration)
    clips = [base]

    if not styled_segments:
        styled_segments = [{
            'start': 0.0,
            'end': duration,
            'text': 'No captions generated',
            'color': 'white',
            'animation': 'minimal',
            'emphasis': False,
        }]

    for seg in styled_segments:
        start = max(0.0, float(seg['start']))
        end = min(duration, float(seg['end']))
        if end <= start:
            continue

        emphasis = bool(seg.get('emphasis', False))
        font_size = 76 if emphasis else 64
        caption_clips = make_caption_clips(
            seg['text'],
            color=seg['color'],
            font_size=font_size,
            emphasis=emphasis,
            width=int(size[0] * 0.8),
            center=(size[0] / 2, size[1] / 2),
        )

        for text_clip in caption_clips:
            text_clip = text_clip.with_start(start).with_duration(end - start)
            if not emphasis:
                text_clip = text_clip.with_position(('center', 'center'))

            anim = seg.get('animation', 'minimal')
            # Map emotion-like animation labels to effects
            if anim in ('energetic', 'motivational'):
                anim = 'pop'
            elif anim in ('sad',):
                anim = 'fade'
            elif anim in ('calm', 'neutral'):
                anim = 'minimal'

            if anim == 'pop':
                text_clip = pop(text_clip)
            elif anim == 'slide_up':
                text_clip = slide_up(text_clip, total_height=size[1])
            elif anim == 'fade':
                text_clip = fade_in(text_clip)
            else:
                text_clip = minimal(text_clip)

            clips.append(text_clip)

    comp = CompositeVideoClip(clips, size=size)
    comp = comp.with_audio(audio)
    comp.write_videofile(
        str(output_path),
        fps=fps,
        codec='libx264',
        audio_codec='aac',
        audio=True,
        audio_fps=44100,
    )
    comp.close()
    audio.close()
