import subprocess


def run_ffmpeg(cmd):
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if result.returncode != 0:
        raise RuntimeError(f'FFmpeg failed: {result.stdout}')
    return result.stdout
