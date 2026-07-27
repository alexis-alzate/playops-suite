from dataclasses import dataclass
from pathlib import Path


@dataclass
class CargueRutasJob:
    archivo_origen: Path
    salida: Path | None = None


@dataclass(frozen=True)
class ArchivoClientePreview:
    path: Path
    hoja: str
    columnas: list[str]
    filas_muestra: list[dict[str, str]]
    total_filas_muestra: int


@dataclass(frozen=True)
class CampoInterno:
    codigo: str
    nombre: str
    requerido: bool = False


@dataclass(frozen=True)
class MapeoSugerido:
    campo: CampoInterno
    columna_origen: str | None
    confianza: int


@dataclass(frozen=True)
class RegistroRuta:
    fila_origen: int
    documento: str
    numero_credito: str
    nombres: str
    apellidos: str
    direccion: str
    telefono: str
    fecha_credito: str
    valor_credito: float | None
    interes: float | None
    cuotas: int | None
    dias_credito: int | None
    tipo_pago: str
    periodicidad: str
    periodicidad_codigo: int | None
    fecha_prox_pago: str
    saldo_actual: float | None
    abono_informado: float | None
    saldo_sin_abonos: float | None
    abono_reconstruido: float | None
    saldo_final_calculado: float | None
    diferencia_saldo: float | None
    abono_estado: str
    errores: list[str]


@dataclass(frozen=True)
class ResultadoNormalizacion:
    registros: list[RegistroRuta]
    total_registros: int
    total_validos: int
    total_con_error: int
    total_con_abono_informado: int
    total_requiere_reconstruccion: int
    errores_generales: list[str]
