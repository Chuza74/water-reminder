import ctypes
import os
import threading

_mci = ctypes.windll.winmm.mciSendStringW
_ALIAS = "water_reminder_sound"
_lock = threading.Lock()


def _send(command):
    buf = ctypes.create_unicode_buffer(260)
    _mci(command, buf, 259, 0)
    return buf.value


def stop_sound():
    with _lock:
        _send(f"stop {_ALIAS}")
        _send(f"close {_ALIAS}")


def play_sound(path):
    if not path or not os.path.exists(path):
        return False
    ext = os.path.splitext(path)[1].lower()
    device = "mpegvideo" if ext == ".mp3" else "waveaudio"
    with _lock:
        _send(f"close {_ALIAS}")
        error = _mci(f'open "{path}" type {device} alias {_ALIAS}', None, 0, None)
        if error:
            return False
        _mci(f"play {_ALIAS}", None, 0, None)
    return True
