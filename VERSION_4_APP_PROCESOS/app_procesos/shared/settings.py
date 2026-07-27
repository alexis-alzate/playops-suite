import json

from app_procesos.config import USER_CONFIG_DIR, USER_CONFIG_FILE


DEFAULT_SETTINGS = {
    "teams_webhook_url": "",
    "teams_enabled": False,
    "last_monitor_result": "",
    "monitor_demo_enabled": False,
    "ui_theme": "dark",
}


def load_settings():
    ensure_settings_file()
    try:
        with USER_CONFIG_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError):
        data = {}

    settings = DEFAULT_SETTINGS.copy()
    settings.update({key: value for key, value in data.items() if key in DEFAULT_SETTINGS})
    return settings


def save_settings(settings):
    USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    data = DEFAULT_SETTINGS.copy()
    if USER_CONFIG_FILE.exists():
        try:
            with USER_CONFIG_FILE.open("r", encoding="utf-8") as file:
                current = json.load(file)
            data.update({key: value for key, value in current.items() if key in DEFAULT_SETTINGS})
        except (OSError, json.JSONDecodeError):
            pass
    data.update({key: value for key, value in settings.items() if key in DEFAULT_SETTINGS})
    with USER_CONFIG_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)
    return USER_CONFIG_FILE


def ensure_settings_file():
    USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not USER_CONFIG_FILE.exists():
        save_settings(DEFAULT_SETTINGS)
    return USER_CONFIG_FILE
