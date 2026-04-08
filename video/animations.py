<<<<<<< HEAD
import numpy as np


def fade_in(clip, duration=0.3):
    return clip.crossfadein(duration)
=======
from moviepy import vfx


def fade_in(clip, duration=0.3):
    return clip.with_effects([vfx.FadeIn(duration)])
>>>>>>> a19e444 (Added basic files and folders)


def pop(clip, duration=0.2, strength=0.2):
    def scaler(t):
        if t < 0:
            return 1.0
        if t > duration:
            return 1.0
        x = t / duration
        return 1.0 + strength * (1 - (1 - x) ** 2)
<<<<<<< HEAD
    return clip.resize(scaler)
=======
    return clip.resized(scaler)
>>>>>>> a19e444 (Added basic files and folders)


def slide_up(clip, total_height, start_y=0.65, end_y=0.5, duration=0.4):
    def pos(t):
        if t < 0:
            y = start_y
        elif t > duration:
            y = end_y
        else:
            x = t / duration
            y = start_y + (end_y - start_y) * (1 - (1 - x) ** 2)
        return ('center', int(total_height * y))
<<<<<<< HEAD
    return clip.set_position(pos)
=======
    return clip.with_position(pos)
>>>>>>> a19e444 (Added basic files and folders)
