import unicodedata


def normalize_text(value):
    return str(value or "").strip().lower()


def clean_human_text(value):
    text = str(value or "").strip()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = "".join(char if char.isalnum() or char.isspace() else " " for char in text)
    return " ".join(text.split())


def clean_identifier(value):
    text = clean_human_text(value)
    return "".join(char for char in text if char.isalnum())


def clean_numeric_identifier(value):
    text = clean_human_text(value)
    return "".join(char for char in text if char.isdigit())
