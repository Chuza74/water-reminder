import tkinter as tk

import cv2
from PIL import Image, ImageTk

from screen_utils import position_for

MAX_W, MAX_H = 480, 360


def _contrast_color(hex_color):
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return "#ffffff"
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return "#000000" if luminance > 0.6 else "#ffffff"


class AnimationWindow(tk.Toplevel):
    def __init__(self, master, video_path, position, background_color="#111111", duration_seconds=8, on_close=None):
        super().__init__(master)
        self._closed = False
        self._job = None
        self.on_close = on_close

        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            self.after(1, self.destroy)
            return

        fps = self.cap.get(cv2.CAP_PROP_FPS) or 24
        self.delay = max(int(1000 / fps), 15)

        src_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or MAX_W
        src_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or MAX_H
        scale = min(MAX_W / src_w, MAX_H / src_h, 1.0)
        self.frame_w = max(int(src_w * scale), 1)
        self.frame_h = max(int(src_h * scale), 1)

        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(bg=background_color)

        text_color = _contrast_color(background_color)
        border = tk.Frame(self, bg=background_color, padx=3, pady=3)
        border.pack()
        self.label = tk.Label(border, bg=background_color, cursor="hand2")
        self.label.pack()

        close_btn = tk.Label(
            border, text="✕", bg=background_color, fg=text_color, cursor="hand2", font=("Segoe UI", 10, "bold")
        )
        close_btn.place(relx=1.0, x=-6, y=6, anchor="ne")
        close_btn.bind("<Button-1>", lambda e: self.close())
        self.label.bind("<Button-1>", lambda e: self.close())
        self.bind("<Escape>", lambda e: self.close())

        self._place(position)
        duration_ms = max(int(duration_seconds * 1000), 1000)
        self._job = self.after(duration_ms, self.close)
        self._update_frame()

    def _place(self, position):
        self.update_idletasks()
        w, h = self.frame_w + 6, self.frame_h + 6
        x, y = position_for(position, w, h)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _update_frame(self):
        if self._closed:
            return
        ok, frame = self.cap.read()
        if not ok:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok, frame = self.cap.read()
            if not ok:
                self.close()
                return
        frame = cv2.resize(frame, (self.frame_w, self.frame_h), interpolation=cv2.INTER_AREA)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(frame)
        photo = ImageTk.PhotoImage(image=image)
        self.label.configure(image=photo)
        self.label.image = photo
        self.after(self.delay, self._update_frame)

    def close(self):
        if self._closed:
            return
        self._closed = True
        if self._job is not None:
            self.after_cancel(self._job)
        self.cap.release()
        if self.on_close is not None:
            self.on_close()
        self.destroy()
