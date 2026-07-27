from __future__ import annotations

import re
import unicodedata


def parse_money(value) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()
    if not text:
        return None

    negative = False
    text = text.replace("\u00a0", " ").replace("\u202f", " ")
    text = text.replace("−", "-").replace("–", "-").replace("—", "-")
    if text.startswith("(") and text.endswith(")"):
        negative = True
        text = text[1:-1]

    text = text.lower()
    text = re.sub(r"\b(cop|col|peso|pesos|mn|mcte|moneda|valor)\b", "", text)
    scaled_number = _parse_scaled_numeric_amount(text)
    if scaled_number is not None:
        return -scaled_number if negative else scaled_number

    word_number = _parse_spanish_number(text)
    if word_number is not None and not re.search(r"\d", text):
        return -word_number if negative else word_number

    text = text.replace("$", "").replace("'", "").replace(" ", "")
    text = re.sub(r"[^0-9,.\-+]", "", text)
    if not text:
        return None

    if text[0] in {"-", "+"}:
        negative = negative or text[0] == "-"
        text = text[1:]
    text = text.replace("-", "").replace("+", "")
    if not text or not re.search(r"\d", text):
        return None

    text = _normalizar_separadores(text)
    try:
        number = float(text)
    except ValueError:
        return None
    return -number if negative else number


def parse_percent_number(value) -> float | None:
    number = parse_money(value)
    if number is None:
        return None

    if "%" in str(value or ""):
        return number

    if _looks_like_ratio(value, number):
        return number * 100

    return number


def parse_int(value) -> int | None:
    number = parse_money(value)
    if number is None:
        return None
    return int(number)


def _normalizar_separadores(text: str) -> str:
    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            return text.replace(".", "").replace(",", ".")
        return text.replace(",", "")

    if text.count(".") > 1:
        return text.replace(".", "")
    if text.count(",") > 1:
        return text.replace(",", "")

    if "." in text:
        entero, decimal = text.rsplit(".", 1)
        if len(decimal) == 3 and entero.isdigit() and decimal.isdigit():
            return entero + decimal
        return text

    if "," in text:
        entero, decimal = text.rsplit(",", 1)
        if len(decimal) == 3 and entero.isdigit() and decimal.isdigit():
            return entero + decimal
        return entero + "." + decimal

    return text


def _parse_scaled_numeric_amount(text: str) -> float | None:
    normalized = _normalize_scaled_text(text)
    match = re.search(
        r"(?<!\d)(\d+(?:[.,]\d+)?)\s*(mil|miles|millon|millones)\b",
        normalized,
    )
    if not match:
        return None

    number_text, scale_text = match.groups()
    number = parse_money(number_text)
    if number is None:
        return None

    scale = 1000 if scale_text in {"mil", "miles"} else 1000000
    return number * scale


def _looks_like_ratio(value, number: float) -> bool:
    if not (0 < abs(number) < 1):
        return False
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return True

    text = str(value or "").strip()
    if not text:
        return False
    text = re.sub(r"[^0-9,.\-+]", "", text)
    return bool(re.fullmatch(r"[-+]?[0][,.]\d+", text))


def _parse_spanish_number(text: str) -> float | None:
    normalized = _normalize_words(text)
    if not normalized:
        return None

    normalized = normalized.replace(" y ", " ")
    tokens = [
        token
        for token in normalized.split()
        if token not in {"de", "del", "el", "la", "los", "las", "un", "una"}
    ]
    if not tokens:
        return None

    unidades = {
        "cero": 0, "uno": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5,
        "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10,
        "once": 11, "doce": 12, "trece": 13, "catorce": 14, "quince": 15,
        "dieciseis": 16, "diecisiete": 17, "dieciocho": 18, "diecinueve": 19,
        "veinte": 20, "veintiuno": 21, "veintidos": 22, "veintitres": 23,
        "veinticuatro": 24, "veinticinco": 25, "veintiseis": 26,
        "veintisiete": 27, "veintiocho": 28, "veintinueve": 29,
    }
    decenas = {
        "treinta": 30, "cuarenta": 40, "cincuenta": 50, "sesenta": 60,
        "setenta": 70, "ochenta": 80, "noventa": 90,
    }
    centenas = {
        "cien": 100, "ciento": 100, "doscientos": 200, "trescientos": 300,
        "cuatrocientos": 400, "quinientos": 500, "seiscientos": 600,
        "setecientos": 700, "ochocientos": 800, "novecientos": 900,
    }

    total = 0
    current = 0
    recognized = False
    for token in tokens:
        if token in unidades:
            current += unidades[token]
            recognized = True
        elif token in decenas:
            current += decenas[token]
            recognized = True
        elif token in centenas:
            current += centenas[token]
            recognized = True
        elif token in {"mil", "miles"}:
            total += (current or 1) * 1000
            current = 0
            recognized = True
        elif token in {"millon", "millones"}:
            total += (current or 1) * 1000000
            current = 0
            recognized = True
        else:
            return None

    if not recognized:
        return None
    return float(total + current)


def _normalize_words(text: str) -> str:
    text = unicodedata.normalize("NFKD", str(text or "").lower())
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = re.sub(r"[^a-z\s]", " ", text)
    return " ".join(text.split())


def _normalize_scaled_text(text: str) -> str:
    text = unicodedata.normalize("NFKD", str(text or "").lower())
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.replace("$", " ")
    text = re.sub(r"[^a-z0-9,.\s]", " ", text)
    return " ".join(text.split())
