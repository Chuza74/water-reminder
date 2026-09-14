import threading

import pystray

from icon_gen import droplet_image


class TrayIcon:
    def __init__(self, on_show, on_toggle, on_quit, is_enabled):
        self.on_show = on_show
        self.on_toggle = on_toggle
        self.on_quit = on_quit
        self.is_enabled = is_enabled
        self.icon = pystray.Icon(
            "WaterReminder",
            droplet_image(size=64),
            "Water Reminder",
            menu=pystray.Menu(
                pystray.MenuItem("Show Water Reminder", self._show, default=True),
                pystray.MenuItem("Reminders Enabled", self._toggle, checked=lambda item: self.is_enabled()),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Quit", self._quit),
            ),
        )

    def _show(self, icon, item):
        self.on_show()

    def _toggle(self, icon, item):
        self.on_toggle()

    def _quit(self, icon, item):
        self.on_quit()

    def start(self):
        threading.Thread(target=self.icon.run, daemon=True).start()

    def stop(self):
        self.icon.stop()
