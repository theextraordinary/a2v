from moviepy.editor import ColorClip, CompositeVideoClip, AudioFileClip
from .captions import make_caption_clip
from .animations import fade_in, pop, slide_up


def render_video(styled_segments, audio_path, output_path, size=(1080, 1920), fps=30):
    audio = AudioFileClip(str(audio_path))
    duration = audio.duration
    base = ColorClip(size=size, color=(0, 0, 0), duration=duration)
    clips = [base]

    for seg in styled_segments:
        start = max(0.0, float(seg['start']))
        end = min(duration, float(seg['end']))
        if end <= start:
            continue
        text_clip = make_caption_clip(seg['text'], color=seg['color'])
        text_clip = text_clip.set_start(start).set_duration(end - start)
        text_clip = text_clip.set_position(('center', 'center'))

        anim = seg.get('animation', 'fade_in')
        if anim == 'pop':
            text_clip = pop(text_clip)
        elif anim == 'slide_up':
            text_clip = slide_up(text_clip, total_height=size[1])
        else:
            text_clip = fade_in(text_clip)

        clips.append(text_clip)

    comp = CompositeVideoClip(clips, size=size)
    comp = comp.set_audio(audio)
    comp.write_videofile(str(output_path), fps=fps, codec='libx264', audio_codec='aac')
    comp.close()
    audio.close()
