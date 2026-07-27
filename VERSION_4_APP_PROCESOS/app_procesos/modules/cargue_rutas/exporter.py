from pathlib import Path


def exportar_resultado(contenido, destino):
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(str(contenido), encoding="utf-8")
    return destino
