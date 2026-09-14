import ctypes

SPI_GETWORKAREA = 0x0030


class _RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


def get_work_area():
    rect = _RECT()
    ok = ctypes.windll.user32.SystemParametersInfoW(SPI_GETWORKAREA, 0, ctypes.byref(rect), 0)
    if not ok:
        sw = ctypes.windll.user32.GetSystemMetrics(0)
        sh = ctypes.windll.user32.GetSystemMetrics(1)
        return 0, 0, sw, sh
    return rect.left, rect.top, rect.right, rect.bottom


def position_for(name, width, height):
    left, top, right, bottom = get_work_area()
    sw = right - left
    sh = bottom - top
    margin = max(20, int(min(sw, sh) * 0.035))
    slots = {
        "center": (left + (sw - width) // 2, top + (sh - height) // 2),
        "left": (left + margin, top + (sh - height) // 2),
        "right": (left + sw - width - margin, top + (sh - height) // 2),
        "top-left": (left + margin, top + margin),
        "top-right": (left + sw - width - margin, top + margin),
        "bottom-left": (left + margin, top + sh - height - margin),
        "bottom-right": (left + sw - width - margin, top + sh - height - margin),
    }
    return slots.get(name, slots["center"])
