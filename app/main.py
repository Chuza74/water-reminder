import os
import sys
from tkinter import colorchooser, filedialog, messagebox

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import customtkinter as ctk

import audio
import autostart
import settings_store
from animation_window import AnimationWindow
from icon_gen import save_icon_files
from tray import TrayIcon

ctk.set_default_color_theme("blue")

ACCENT = "#38a1e6"
ACCENT_TEXT = "#ffffff"

THEMES = {
    "dark": {
        "mode": "dark",
        "bg_app": "#141924",
        "bg_card": "#1e2430",
        "bg_inset": "#2a3244",
        "text_secondary": "#8a93a6",
        "swatch_border": "#4a5468",
        "divider": "#2a3244",
    },
    "light": {
        "mode": "light",
        "bg_app": "#eef1f7",
        "bg_card": "#ffffff",
        "bg_inset": "#eef1f7",
        "text_secondary": "#5b6577",
        "swatch_border": "#d3d9e6",
        "divider": "#e6e9f2",
    },
}

POSITION_LAYOUT = [
    ["top-left", None, "top-right"],
    ["left", "center", "right"],
    ["bottom-left", None, "bottom-right"],
]

POSITION_GLYPHS = {
    "top-left": "↖",
    "top-right": "↗",
    "bottom-left": "↙",
    "bottom-right": "↘",
    "left": "◀",
    "right": "▶",
    "center": "●",
}

POSITION_NAMES = {
    "top-left": "Top Left",
    "top-right": "Top Right",
    "bottom-left": "Bottom Left",
    "bottom-right": "Bottom Right",
    "left": "Left",
    "right": "Right",
    "center": "Center",
}

PRESET_MINUTES = [15, 30, 45, 60, 90, 120]
PRESET_SECONDS = [5, 8, 10, 15, 20, 30]

BACKGROUND_PRESETS = ["#111111", "#ffffff", "#1b2735", "#0f3d3e", "#2d1b3d", "#38a1e6"]

TAB_DEFS = [("general", "⚙", "General"), ("animation", "🎬", "Animation"), ("sound", "🔔", "Sound")]


class WaterReminderApp(ctk.CTk):
    def __init__(self, start_minimized=False):
        super().__init__()
        self.settings = settings_store.load()
        self.remaining_seconds = self.settings["interval_minutes"] * 60
        self.animation_window = None
        self.position_buttons = {}
        self.background_swatches = {}
        self.tab_buttons = {}
        self.tab_frames = {}
        self.active_tab = "general"
        self.colors = THEMES[self.settings.get("theme", "dark")]

        ctk.set_appearance_mode(self.colors["mode"])

        self.title("Water Reminder")
        self.geometry("500x780")
        self.resizable(False, False)

        assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
        try:
            _, ico_path = save_icon_files(assets_dir)
            self.iconbitmap(ico_path)
        except Exception:
            pass

        self._build_ui()
        self._sync_ui_from_settings()

        self.protocol("WM_DELETE_WINDOW", self.hide_to_tray)

        self.tray = TrayIcon(
            on_show=lambda: self.after(0, self._show_window_main_thread),
            on_toggle=lambda: self.after(0, self.toggle_enabled),
            on_quit=lambda: self.after(0, self._quit_main_thread),
            is_enabled=lambda: self.settings["enabled"],
        )
        self.tray.start()

        self._center_on_screen()
        if start_minimized:
            self.withdraw()

        self._tick()

    def _build_ui(self):
        self.configure(fg_color=self.colors["bg_app"])

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 6))

        top_row = ctk.CTkFrame(header, fg_color="transparent")
        top_row.pack(fill="x")
        ctk.CTkLabel(top_row, text="", width=36).pack(side="left")
        title_col = ctk.CTkFrame(top_row, fg_color="transparent")
        title_col.pack(side="left", expand=True)
        ctk.CTkLabel(title_col, text="💧", font=("Segoe UI Emoji", 34)).pack()
        ctk.CTkLabel(title_col, text="Water Reminder", font=("Segoe UI", 20, "bold")).pack(pady=(4, 0))
        ctk.CTkLabel(
            title_col, text="Stay hydrated, stay sharp", font=("Segoe UI", 12), text_color=self.colors["text_secondary"]
        ).pack()
        self.theme_button = ctk.CTkButton(
            top_row,
            text=self._theme_icon(),
            width=36,
            height=36,
            corner_radius=18,
            fg_color=self.colors["bg_card"],
            hover_color=ACCENT,
            font=("Segoe UI Emoji", 14),
            command=self._toggle_theme,
        )
        self.theme_button.pack(side="right")

        status_card = ctk.CTkFrame(self, fg_color=self.colors["bg_card"], corner_radius=18)
        status_card.pack(fill="x", padx=24, pady=8)
        row = ctk.CTkFrame(status_card, fg_color="transparent")
        row.pack(fill="x", padx=18, pady=(14, 4))
        ctk.CTkLabel(row, text="Reminders", font=("Segoe UI", 14, "bold")).pack(side="left")
        self.enabled_switch = ctk.CTkSwitch(
            row, text="", command=self._on_toggle_enabled, progress_color=ACCENT
        )
        self.enabled_switch.pack(side="right")
        bottom_row = ctk.CTkFrame(status_card, fg_color="transparent")
        bottom_row.pack(fill="x", padx=18, pady=(0, 14))
        self.countdown_label = ctk.CTkLabel(
            bottom_row, text="Next reminder in --:--", font=("Segoe UI", 13), text_color=self.colors["text_secondary"]
        )
        self.countdown_label.pack(side="left")
        ctk.CTkButton(
            bottom_row, text="Preview Now", width=110, corner_radius=14, fg_color=ACCENT, command=self._test_now
        ).pack(side="right")

        tabbar_card = ctk.CTkFrame(self, fg_color=self.colors["bg_card"], corner_radius=20)
        tabbar_card.pack(fill="x", padx=24, pady=(6, 10))
        tab_inner = ctk.CTkFrame(tabbar_card, fg_color="transparent")
        tab_inner.pack(fill="x", padx=6, pady=6)
        for i, _ in enumerate(TAB_DEFS):
            tab_inner.grid_columnconfigure(i, weight=1)
        for i, (key, icon, label) in enumerate(TAB_DEFS):
            selected = key == self.active_tab
            btn = ctk.CTkButton(
                tab_inner,
                text=f"{icon}  {label}",
                corner_radius=16,
                height=38,
                font=("Segoe UI", 13, "bold" if selected else "normal"),
                fg_color=ACCENT if selected else "transparent",
                text_color=ACCENT_TEXT if selected else self.colors["text_secondary"],
                hover_color=ACCENT,
                command=lambda k=key: self._select_tab(k),
            )
            btn.grid(row=0, column=i, sticky="ew", padx=3)
            self.tab_buttons[key] = btn

        self.content_area = ctk.CTkFrame(self, fg_color=self.colors["bg_card"], corner_radius=18)
        self.content_area.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        for key, _, _ in TAB_DEFS:
            self.tab_frames[key] = ctk.CTkScrollableFrame(self.content_area, fg_color="transparent")

        self._build_general_tab(self.tab_frames["general"])
        self._build_animation_tab(self.tab_frames["animation"])
        self._build_sound_tab(self.tab_frames["sound"])
        self.tab_frames[self.active_tab].pack(fill="both", expand=True, padx=2, pady=2)

    def _select_tab(self, key):
        if key != self.active_tab:
            self.tab_frames[self.active_tab].pack_forget()
            self.tab_frames[key].pack(fill="both", expand=True, padx=2, pady=2)
            self.active_tab = key
        for k, btn in self.tab_buttons.items():
            selected = k == key
            btn.configure(
                fg_color=ACCENT if selected else "transparent",
                text_color=ACCENT_TEXT if selected else self.colors["text_secondary"],
                font=("Segoe UI", 13, "bold" if selected else "normal"),
            )

    def _section_label(self, parent, text, first=False):
        ctk.CTkLabel(parent, text=text, font=("Segoe UI", 13, "bold")).pack(
            anchor="w", padx=16, pady=(18 if not first else 16, 6)
        )

    def _hint(self, parent, text):
        ctk.CTkLabel(parent, text=text, font=("Segoe UI", 12), text_color=self.colors["text_secondary"]).pack(
            anchor="w", padx=16
        )

    def _build_general_tab(self, tab):
        self._section_label(tab, "⏱  Remind me every", first=True)
        entry_row = ctk.CTkFrame(tab, fg_color="transparent")
        entry_row.pack(fill="x", padx=16)
        self.interval_entry = ctk.CTkEntry(entry_row, width=70, justify="center", font=("Segoe UI", 14))
        self.interval_entry.pack(side="left")
        ctk.CTkLabel(entry_row, text="minutes", font=("Segoe UI", 13), text_color=self.colors["text_secondary"]).pack(
            side="left", padx=(10, 0)
        )
        ctk.CTkButton(
            entry_row, text="Apply", width=70, corner_radius=12, fg_color=ACCENT, command=self._apply_interval_entry
        ).pack(side="right")

        presets_row = ctk.CTkFrame(tab, fg_color="transparent")
        presets_row.pack(fill="x", padx=16, pady=12)
        self.preset_buttons = {}
        for minutes in PRESET_MINUTES:
            btn = ctk.CTkButton(
                presets_row,
                text=f"{minutes}m",
                width=54,
                corner_radius=12,
                fg_color=self.colors["bg_inset"],
                hover_color=ACCENT,
                command=lambda m=minutes: self._set_interval(m),
            )
            btn.pack(side="left", expand=True, padx=3)
            self.preset_buttons[minutes] = btn

        self._divider(tab)

        self._section_label(tab, "🖥  Start with Windows")
        self._hint(tab, "Launch automatically at sign-in")
        srow = ctk.CTkFrame(tab, fg_color="transparent")
        srow.pack(fill="x", padx=16, pady=(8, 18))
        self.autostart_switch = ctk.CTkSwitch(
            srow, text="", command=self._on_toggle_autostart, progress_color=ACCENT
        )
        self.autostart_switch.pack(side="left")

    def _divider(self, parent):
        ctk.CTkFrame(parent, fg_color=self.colors["divider"], height=1).pack(fill="x", padx=16, pady=(10, 0))

    def _build_animation_tab(self, tab):
        self._section_label(tab, "🎞  Animation File", first=True)
        self.animation_label = ctk.CTkLabel(
            tab, text="", font=("Segoe UI", 12), text_color=self.colors["text_secondary"], wraplength=400, justify="left"
        )
        self.animation_label.pack(anchor="w", padx=16)
        ctk.CTkButton(
            tab, text="Change Animation...", corner_radius=12, fg_color=ACCENT, command=self._choose_animation
        ).pack(anchor="w", padx=16, pady=10)

        self._divider(tab)

        self._section_label(tab, "⏳  Stay on Screen For")
        dur_row = ctk.CTkFrame(tab, fg_color="transparent")
        dur_row.pack(fill="x", padx=16)
        self.duration_entry = ctk.CTkEntry(dur_row, width=70, justify="center", font=("Segoe UI", 14))
        self.duration_entry.pack(side="left")
        ctk.CTkLabel(dur_row, text="seconds", font=("Segoe UI", 13), text_color=self.colors["text_secondary"]).pack(
            side="left", padx=(10, 0)
        )
        ctk.CTkButton(
            dur_row, text="Apply", width=70, corner_radius=12, fg_color=ACCENT, command=self._apply_duration_entry
        ).pack(side="right")

        dur_presets_row = ctk.CTkFrame(tab, fg_color="transparent")
        dur_presets_row.pack(fill="x", padx=16, pady=12)
        self.duration_buttons = {}
        for seconds in PRESET_SECONDS:
            btn = ctk.CTkButton(
                dur_presets_row,
                text=f"{seconds}s",
                width=54,
                corner_radius=12,
                fg_color=self.colors["bg_inset"],
                hover_color=ACCENT,
                command=lambda s=seconds: self._set_duration(s),
            )
            btn.pack(side="left", expand=True, padx=3)
            self.duration_buttons[seconds] = btn

        self._divider(tab)

        self._section_label(tab, "📍  Position on Screen")
        self.position_status_label = ctk.CTkLabel(
            tab, text="", font=("Segoe UI", 12), text_color=self.colors["text_secondary"]
        )
        self.position_status_label.pack(anchor="w", padx=16)
        grid_wrap = ctk.CTkFrame(tab, fg_color="transparent")
        grid_wrap.pack(padx=16, pady=10)
        for r, row_positions in enumerate(POSITION_LAYOUT):
            for c, pos in enumerate(row_positions):
                if pos is None:
                    spacer = ctk.CTkFrame(grid_wrap, width=64, height=64, fg_color="transparent")
                    spacer.grid(row=r, column=c, padx=6, pady=6)
                    continue
                btn = ctk.CTkButton(
                    grid_wrap,
                    text=POSITION_GLYPHS[pos],
                    width=64,
                    height=64,
                    corner_radius=14,
                    font=("Segoe UI", 18, "bold"),
                    fg_color=self.colors["bg_inset"],
                    hover_color=ACCENT,
                    command=lambda p=pos: self._set_position(p),
                )
                btn.grid(row=r, column=c, padx=6, pady=6)
                self.position_buttons[pos] = btn

        self._divider(tab)

        self._section_label(tab, "🎨  Popup Background")
        swatch_row = ctk.CTkFrame(tab, fg_color="transparent")
        swatch_row.pack(fill="x", padx=16, pady=(0, 8))
        for color in BACKGROUND_PRESETS:
            swatch = ctk.CTkButton(
                swatch_row,
                text="",
                width=36,
                height=36,
                corner_radius=10,
                fg_color=color,
                hover_color=color,
                border_width=2,
                border_color=self.colors["swatch_border"],
                command=lambda c=color: self._set_background(c),
            )
            swatch.pack(side="left", padx=4)
            self.background_swatches[color] = swatch
        ctk.CTkButton(
            tab,
            text="Custom Color...",
            corner_radius=12,
            fg_color=self.colors["bg_inset"],
            hover_color=ACCENT,
            command=self._choose_custom_background,
        ).pack(anchor="w", padx=16, pady=(8, 18))

    def _build_sound_tab(self, tab):
        self._section_label(tab, "🔔  Reminder Sound", first=True)
        self._hint(tab, "Play a sound alongside the animation")
        srow = ctk.CTkFrame(tab, fg_color="transparent")
        srow.pack(fill="x", padx=16, pady=(8, 4))
        self.sound_switch = ctk.CTkSwitch(
            srow, text="", command=self._on_toggle_sound, progress_color=ACCENT
        )
        self.sound_switch.pack(side="left")

        self._divider(tab)

        self.sound_label = ctk.CTkLabel(
            tab, text="", font=("Segoe UI", 12), text_color=self.colors["text_secondary"], wraplength=400, justify="left"
        )
        self.sound_label.pack(anchor="w", padx=16, pady=(14, 8))

        btn_row = ctk.CTkFrame(tab, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 18))
        ctk.CTkButton(
            btn_row, text="Choose Sound...", corner_radius=12, fg_color=ACCENT, command=self._choose_sound
        ).pack(side="left")
        ctk.CTkButton(
            btn_row,
            text="Preview Sound",
            corner_radius=12,
            fg_color=self.colors["bg_inset"],
            hover_color=ACCENT,
            command=self._preview_sound,
        ).pack(side="right")

    def _sync_ui_from_settings(self):
        if self.settings["enabled"]:
            self.enabled_switch.select()
        else:
            self.enabled_switch.deselect()

        if self.settings["autostart"]:
            self.autostart_switch.select()
        else:
            self.autostart_switch.deselect()

        if self.settings["sound_enabled"]:
            self.sound_switch.select()
        else:
            self.sound_switch.deselect()

        self.interval_entry.delete(0, "end")
        self.interval_entry.insert(0, str(self.settings["interval_minutes"]))
        self._refresh_preset_highlight()

        self.duration_entry.delete(0, "end")
        self.duration_entry.insert(0, str(self.settings["display_seconds"]))
        self._refresh_duration_highlight()

        name = os.path.basename(self.settings["animation_path"])
        self.animation_label.configure(text=name)

        sound_path = self.settings["sound_path"]
        self.sound_label.configure(text=os.path.basename(sound_path) if sound_path else "No sound selected")

        self._refresh_position_highlight()
        self._refresh_background_highlight()

    def _refresh_preset_highlight(self):
        current = self.settings["interval_minutes"]
        for minutes, btn in self.preset_buttons.items():
            btn.configure(fg_color=ACCENT if minutes == current else self.colors["bg_inset"])

    def _refresh_duration_highlight(self):
        current = self.settings["display_seconds"]
        for seconds, btn in self.duration_buttons.items():
            btn.configure(fg_color=ACCENT if seconds == current else self.colors["bg_inset"])

    def _refresh_position_highlight(self):
        current = self.settings["position"]
        for pos, btn in self.position_buttons.items():
            btn.configure(fg_color=ACCENT if pos == current else self.colors["bg_inset"])
        self.position_status_label.configure(text=f"Currently: {POSITION_NAMES[current]}")

    def _refresh_background_highlight(self):
        current = self.settings["background_color"].lower()
        for color, swatch in self.background_swatches.items():
            swatch.configure(border_color=ACCENT if color.lower() == current else self.colors["swatch_border"])

    def _persist(self):
        settings_store.save(self.settings)

    def _theme_icon(self):
        return "☀" if self.settings.get("theme", "dark") == "dark" else "🌙"

    def _toggle_theme(self):
        new_theme = "light" if self.settings.get("theme", "dark") == "dark" else "dark"
        self.settings["theme"] = new_theme
        self._persist()
        self.colors = THEMES[new_theme]
        ctk.set_appearance_mode(self.colors["mode"])
        for child in self.winfo_children():
            child.destroy()
        self.position_buttons = {}
        self.background_swatches = {}
        self.tab_buttons = {}
        self.tab_frames = {}
        self._build_ui()
        self._sync_ui_from_settings()

    def _on_toggle_enabled(self):
        self.settings["enabled"] = bool(self.enabled_switch.get())
        self._persist()

    def toggle_enabled(self):
        self.settings["enabled"] = not self.settings["enabled"]
        if self.settings["enabled"]:
            self.enabled_switch.select()
        else:
            self.enabled_switch.deselect()
        self._persist()

    def _on_toggle_autostart(self):
        enabled = bool(self.autostart_switch.get())
        try:
            autostart.set_autostart(enabled)
            self.settings["autostart"] = enabled
        except OSError:
            messagebox.showerror("Water Reminder", "Could not update Windows startup setting.")
            if enabled:
                self.autostart_switch.deselect()
            else:
                self.autostart_switch.select()
        self._persist()

    def _on_toggle_sound(self):
        self.settings["sound_enabled"] = bool(self.sound_switch.get())
        self._persist()

    def _set_interval(self, minutes):
        self.settings["interval_minutes"] = minutes
        self.remaining_seconds = minutes * 60
        self.interval_entry.delete(0, "end")
        self.interval_entry.insert(0, str(minutes))
        self._refresh_preset_highlight()
        self._persist()

    def _apply_interval_entry(self):
        raw = self.interval_entry.get().strip()
        if not raw.isdigit() or int(raw) <= 0:
            messagebox.showwarning("Water Reminder", "Enter a whole number of minutes greater than 0.")
            return
        self._set_interval(int(raw))

    def _set_duration(self, seconds):
        self.settings["display_seconds"] = seconds
        self.duration_entry.delete(0, "end")
        self.duration_entry.insert(0, str(seconds))
        self._refresh_duration_highlight()
        self._persist()

    def _apply_duration_entry(self):
        raw = self.duration_entry.get().strip()
        if not raw.isdigit() or int(raw) <= 0:
            messagebox.showwarning("Water Reminder", "Enter a whole number of seconds greater than 0.")
            return
        self._set_duration(int(raw))

    def _choose_animation(self):
        path = filedialog.askopenfilename(
            title="Choose reminder animation",
            filetypes=[("Video files", "*.mp4 *.mov *.avi *.mkv *.webm"), ("All files", "*.*")],
        )
        if path:
            self.settings["animation_path"] = path
            self.animation_label.configure(text=os.path.basename(path))
            self._persist()

    def _choose_sound(self):
        path = filedialog.askopenfilename(
            title="Choose reminder sound",
            filetypes=[("Audio files", "*.wav *.mp3"), ("All files", "*.*")],
        )
        if path:
            self.settings["sound_path"] = path
            self.sound_label.configure(text=os.path.basename(path))
            self._persist()

    def _preview_sound(self):
        path = self.settings["sound_path"]
        if not path or not os.path.exists(path) or not audio.play_sound(path):
            messagebox.showwarning("Water Reminder", "Select a valid sound file first.")

    def _set_position(self, position):
        self.settings["position"] = position
        self._refresh_position_highlight()
        self._persist()

    def _set_background(self, color):
        self.settings["background_color"] = color
        self._refresh_background_highlight()
        self._persist()

    def _choose_custom_background(self):
        rgb, hex_color = colorchooser.askcolor(color=self.settings["background_color"], title="Popup Background Color")
        if hex_color:
            self._set_background(hex_color)

    def _test_now(self):
        self._show_animation()
        self.remaining_seconds = self.settings["interval_minutes"] * 60

    def _show_animation(self):
        path = self.settings["animation_path"]
        if not path or not os.path.exists(path):
            messagebox.showwarning("Water Reminder", "Select a valid animation file first.")
            return
        if self.animation_window is not None and self.animation_window.winfo_exists():
            self.animation_window.close()

        sound_active = self.settings["sound_enabled"] and bool(self.settings["sound_path"])
        if sound_active:
            audio.play_sound(self.settings["sound_path"])

        self.animation_window = AnimationWindow(
            self,
            path,
            self.settings["position"],
            background_color=self.settings["background_color"],
            duration_seconds=self.settings["display_seconds"],
            on_close=audio.stop_sound if sound_active else None,
        )

    def _tick(self):
        if self.settings["enabled"]:
            self.remaining_seconds -= 1
            if self.remaining_seconds <= 0:
                self._show_animation()
                self.remaining_seconds = self.settings["interval_minutes"] * 60
            mins, secs = divmod(max(self.remaining_seconds, 0), 60)
            self.countdown_label.configure(text=f"Next reminder in {mins:02d}:{secs:02d}")
        else:
            self.countdown_label.configure(text="Reminders paused")
        self.after(1000, self._tick)

    def _center_on_screen(self):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (sw - w) // 2
        y = (sh - h) // 3
        self.geometry(f"+{x}+{y}")

    def _show_window_main_thread(self):
        self.deiconify()
        self.lift()
        self.focus_force()

    def hide_to_tray(self):
        self.withdraw()

    def _quit_main_thread(self):
        try:
            self.tray.stop()
        except Exception:
            pass
        self.destroy()
        os._exit(0)


def main():
    start_minimized = "--minimized" in sys.argv
    app = WaterReminderApp(start_minimized=start_minimized)
    app.mainloop()


if __name__ == "__main__":
    main()
