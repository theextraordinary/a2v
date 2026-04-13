from pathlib import Path
from utils.ffmpeg import run_ffmpeg


def mix_audio(speech_path, bgm_path, output_path):
    speech_path = Path(speech_path)
    output_path = Path(output_path)

    if bgm_path is None:
        cmd = [
            'ffmpeg', '-y',
            '-i', str(speech_path),
            '-c:a', 'aac',
            str(output_path),
        ]
        run_ffmpeg(cmd)
        return output_path

    cmd = [
        'ffmpeg', '-y',
        '-i', str(speech_path),
        '-i', str(bgm_path),
        '-filter_complex', '[0:a][1:a]amix=inputs=2:duration=first[a]',
        '-map', '[a]',
        '-c:a', 'aac',
        str(output_path),
    ]
    run_ffmpeg(cmd)
    return output_path


def mux_av(video_path, audio_path, output_path):
    cmd = [
        'ffmpeg', '-y',
        '-i', str(video_path),
        '-i', str(audio_path),
        '-map', '0:v',
        '-map', '1:a',
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-shortest',
        str(output_path),
    ]
    run_ffmpeg(cmd)
    return output_path
