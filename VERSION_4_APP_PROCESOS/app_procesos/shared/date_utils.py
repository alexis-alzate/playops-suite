from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime


MESES = {
    "enero": 1,
    "ene": 1,
    "febrero": 2,
    "feb": 2,
    "marzo": 3,
    "mar": 3,
    "abril": 4,
    "abr": 4,
    "mayo": 5,
    "may": 5,
    "junio": 6,
    "jun": 6,
    "julio": 7,
    "jul": 7,
    "agosto": 8,
    "ago": 8,
    "septiembre": 9,
    "setiembre": 9,
    "sep": 9,
    "sept": 9,
    "octubre": 10,
    "oct": 10,
    "noviembre": 11,
    "nov": 11,
    "diciembre": 12,
    "dic": 12,
}

DIAS_TEXTO = {
    "primero": 1,
    "uno": 1,
    "dos": 2,
    "tres": 3,
    "cuatro": 4,
    "cinco": 5,
    "seis": 6,
    "siete": 7,
    "ocho": 8,
    "nueve": 9,
    "diez": 10,
    "once": 11,
    "doce": 12,
    "trece": 13,
    "catorce": 14,
    "quince": 15,
    "dieciseis": 16,
    "diecisiete": 17,
    "dieciocho": 18,
    "diecinueve": 19,
    "veinte": 20,
    "veintiuno": 21,
    "veintidos": 22,
    "veintitres": 23,
    "veinticuatro": 24,
    "veinticinco": 25,
    "veintiseis": 26,
    "veintisiete": 27,
    "veintiocho": 28,
    "veintinueve": 29,
    "treinta": 30,
    "treinta uno": 31,
}


def normalize_date_value(value, *, default_year: int | None = None) -> str:
    text = str(value or "").strip()
    if not text:
        return ""

    default_year = default_year or date.today().year

    if isinstance(value, (datetime, date)):
        return value.strftime("%Y-%m-%d")

    compact_match = re.search(r"(\d{4})\D+(\d{1,2})\D+(\d{1,2})", text)
    if compact_match:
        year, month, day = compact_match.groups()
        return _safe_date(int(year), int(month), int(day))

    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d", "%d-%m-%Y", "%m-%d-%Y"):
        try:
            return datetime.strptime(text[:10], fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue

    return _parse_spanish_date(text, default_year=default_year)


def _parse_spanish_date(text: str, *, default_year: int) -> str:
    normalized = _normalize_text(text)
    if not normalized:
        return ""

    for mes_texto, mes_numero in MESES.items():
        if mes_texto not in normalized:
            continue

        year = default_year
        year_match = re.search(r"\b(20\d{2}|19\d{2})\b", normalized)
        if year_match:
            year = int(year_match.group(1))

        patterns = [
            rf"\b(\d{{1,2}})\s+de\s+{mes_texto}\b",
            rf"\b(\d{{1,2}})\s+{mes_texto}\b",
            rf"\b{mes_texto}\s+(\d{{1,2}})\b",
        ]
        for pattern in patterns:
            match = re.search(pattern, normalized)
            if match:
                return _safe_date(year, mes_numero, int(match.group(1)))

        for dia_texto, dia_numero in DIAS_TEXTO.items():
            if re.search(rf"\b{dia_texto}\s+de\s+{mes_texto}\b", normalized):
                return _safe_date(year, mes_numero, dia_numero)

    return ""


def _safe_date(year: int, month: int, day: int) -> str:
    try:
        return date(year, month, day).strftime("%Y-%m-%d")
    except ValueError:
        return ""


def _normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKD", str(text or "").lower())
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return " ".join(text.split())
