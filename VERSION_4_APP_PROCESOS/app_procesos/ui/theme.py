THEMES = {
    "dark": {
        "label": "Playtech oscuro",
        "bg": "#0b1219",
        "panel": "#111f2a",
        "panel_2": "#172b38",
        "panel_3": "#203746",
        "console": "#050b10",
        "console_text": "#e6edf3",
        "accent": "#08a9d6",
        "accent_hover": "#12bfe9",
        "accent_active": "#078bb3",
        "accent_2": "#77e4f6",
        "line": "#25485b",
        "text": "#f5f7fb",
        "muted": "#aab7c4",
        "disabled": "#263846",
        "danger": "#ff595e",
        "ok": "#3ddc84",
    },
    "light": {
        "label": "Playtech claro",
        "bg": "#f4f8fb",
        "panel": "#ffffff",
        "panel_2": "#e9f3f8",
        "panel_3": "#d8edf6",
        "console": "#ffffff",
        "console_text": "#10202b",
        "accent": "#079dcc",
        "accent_hover": "#08b5e6",
        "accent_active": "#067da4",
        "accent_2": "#007fa7",
        "line": "#b9d5e2",
        "text": "#0b1720",
        "muted": "#49616f",
        "disabled": "#d6e3ea",
        "danger": "#d9343f",
        "ok": "#148f55",
    },
    "rose": {
        "label": "Rosa elegante",
        "bg": "#160d16",
        "panel": "#241222",
        "panel_2": "#351a31",
        "panel_3": "#492241",
        "console": "#090509",
        "console_text": "#fff3fb",
        "accent": "#e84ca5",
        "accent_hover": "#ff67ba",
        "accent_active": "#c73286",
        "accent_2": "#ff9ed1",
        "line": "#663056",
        "text": "#fff7fb",
        "muted": "#d8b8cc",
        "disabled": "#3c2a38",
        "danger": "#ff5f7f",
        "ok": "#57e0a1",
    },
    "emerald": {
        "label": "Verde premium",
        "bg": "#07140f",
        "panel": "#0f241b",
        "panel_2": "#153527",
        "panel_3": "#1e4936",
        "console": "#030b08",
        "console_text": "#ebfff7",
        "accent": "#10b981",
        "accent_hover": "#34d399",
        "accent_active": "#059669",
        "accent_2": "#8df5ca",
        "line": "#2f6f55",
        "text": "#f3fff9",
        "muted": "#a9cdbc",
        "disabled": "#243b31",
        "danger": "#ff646d",
        "ok": "#45f0a5",
    },
    "violet": {
        "label": "Violeta executive",
        "bg": "#100f1f",
        "panel": "#19172d",
        "panel_2": "#25213e",
        "panel_3": "#332c56",
        "console": "#080711",
        "console_text": "#f4f1ff",
        "accent": "#8b5cf6",
        "accent_hover": "#a78bfa",
        "accent_active": "#6d43d6",
        "accent_2": "#c4b5fd",
        "line": "#4b4275",
        "text": "#fbfaff",
        "muted": "#c6c1db",
        "disabled": "#302d42",
        "danger": "#ff647c",
        "ok": "#4ade80",
    },
}

CURRENT_THEME = "dark"
COLORS = THEMES[CURRENT_THEME].copy()


def set_theme(name):
    global CURRENT_THEME
    if name not in THEMES:
        return
    CURRENT_THEME = name
    COLORS.clear()
    COLORS.update(THEMES[name])


def toggle_theme():
    set_theme("light" if CURRENT_THEME == "dark" else "dark")
    return CURRENT_THEME


def get_theme():
    return CURRENT_THEME


def get_theme_label(name=None):
    theme_name = name or CURRENT_THEME
    return THEMES.get(theme_name, THEMES["dark"]).get("label", theme_name)


def get_theme_options():
    return [(name, data.get("label", name)) for name, data in THEMES.items()]


def get_theme_accent(name):
    return THEMES.get(name, THEMES["dark"]).get("accent", THEMES["dark"]["accent"])


FONT_TITLE = ("Segoe UI", 24, "bold")
FONT_H2 = ("Segoe UI", 15, "bold")
FONT_BODY = ("Segoe UI", 10)
FONT_BODY_BOLD = ("Segoe UI", 10, "bold")
FONT_MONO = ("Consolas", 10)
