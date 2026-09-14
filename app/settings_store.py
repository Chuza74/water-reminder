import json
import os

APP_DIR = os.path.join(os.environ["APPDATA"], "WaterReminder")
SETTINGS_PATH = os.path.join(APP_DIR, "settings.json")
ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
DEFAULT_ANIMATION = os.path.join(ASSETS_DIR, "default_animation.mp4")

DEFAULTS = {
    "enabled": True,
    "interval_minutes": 45,
    "autostart": False,
    "animation_path": DEFAULT_ANIMATION,
    "position": "center",
    "display_seconds": 8,
    "background_color": "#111111",
    "sound_enabled": False,
    "sound_path": "",
    "theme": "dark",
}


def load():
    os.makedirs(APP_DIR, exist_ok=True)
    if not os.path.exists(SETTINGS_PATH):
        save(DEFAULTS)
        return dict(DEFAULTS)
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        merged = dict(DEFAULTS)
        merged.update(data)
        if not merged.get("animation_path") or not os.path.exists(merged["animation_path"]):
            merged["animation_path"] = DEFAULT_ANIMATION
        return merged
    except (json.JSONDecodeError, OSError):
        return dict(DEFAULTS)


def save(settings):
    os.makedirs(APP_DIR, exist_ok=True)
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)
