import unicodedata

from .models import CampoInterno, MapeoSugerido


CAMPOS_INTERNOS = [
    CampoInterno("documento", "Documento", True),
    CampoInterno("numero_credito", "Numero de credito", False),
    CampoInterno("nombres", "Nombres", True),
    CampoInterno("apellidos", "Apellidos", False),
    CampoInterno("direccion", "Direccion", False),
    CampoInterno("telefono", "Telefono", False),
    CampoInterno("fecha_credito", "Fecha credito", False),
    CampoInterno("valor_credito", "Valor credito", True),
    CampoInterno("interes", "Interes", False),
    CampoInterno("cuotas", "Cantidad de cuotas", False),
    CampoInterno("dias_credito", "Dias credito", False),
    CampoInterno("tipo_pago", "Tipo de pago", False),
    CampoInterno("saldo_actual", "Saldo actual", True),
    CampoInterno("abono", "Abono", False),
    CampoInterno("periodicidad", "Periodicidad", False),
    CampoInterno("fecha_prox_pago", "Fecha proximo pago", False),
]


SINONIMOS = {
    "documento": [
        "documento",
        "cedula",
        "cedula cliente",
        "cc",
        "identificacion",
        "identificacion cliente",
        "id cliente",
        "numero documento",
        "num documento",
        "nro documento",
        "nit",
    ],
    "numero_credito": [
        "numero credito",
        "nro credito",
        "num credito",
        "credito numero",
        "id credito",
        "codigo credito",
        "consecutivo credito",
        "referencia credito",
        "obligacion",
        "numero obligacion",
    ],
    "nombres": ["nombre", "nombres", "cliente", "nombre cliente", "primer nombre", "razon social", "titular"],
    "apellidos": ["apellido", "apellidos", "primer apellido", "segundo apellido"],
    "direccion": ["direccion", "domicilio", "barrio", "ubicacion"],
    "telefono": ["telefono", "celular", "movil", "whatsapp", "contacto", "telefono cliente", "celular cliente"],
    "fecha_credito": ["fecha credito", "fecha creacion credito", "fecha de creacion del credito", "fecha prestamo", "fecha desembolso", "fecha venta"],
    "valor_credito": [
        "valor credito",
        "valor inicial del credito sin interes",
        "credito",
        "prestamo",
        "capital",
        "capital prestado",
        "valor inicial",
        "valor inicial credito",
        "valor prestamo",
        "valor prestado",
        "monto",
        "monto credito",
        "monto prestamo",
    ],
    "interes": ["interes", "interes del credito", "porcentaje", "tasa"],
    "cuotas": ["cantidad de cuotas", "cuotas a pagar", "numero cuotas", "cantidad de cuotas a pagar"],
    "dias_credito": ["dias credito", "dias de credito", "plazo dias", "dias plazo", "plazo"],
    "tipo_pago": ["tipo pago", "modalidad", "metodo pago"],
    "saldo_actual": [
        "saldo",
        "saldo actual",
        "saldo actual del credito",
        "saldo cliente",
        "saldo pendiente",
        "saldo capital",
        "deuda",
        "valor adeudado",
        "saldo cartera",
    ],
    "abono": [
        "abono",
        "abonos",
        "pagos",
        "recaudo",
        "valor abonado",
        "valor total de lo que ha pagado al credito",
        "valor total pagado al credito",
        "total de lo que ha pagado al credito",
        "lo que ha pagado al credito",
        "total pagado",
        "total pagado credito",
        "pagado al credito",
        "ha pagado al credito",
        "valor pagado",
        "valor pago",
        "pagado",
        "abono acumulado",
        "pagos realizados",
    ],
    "periodicidad": ["periodicidad", "frecuencia", "forma pago", "forma de pago", "tipo periodo", "periodo", "diario", "semanal", "quincenal", "mensual"],
    "fecha_prox_pago": ["fecha proximo pago", "fecha prox pago", "proximo pago", "fecha siguiente pago", "fecha prox", "siguiente pago", "fecha pago"],
}


def sugerir_mapeo(columnas):
    normalizadas = [(columna, _normalizar(columna)) for columna in columnas]
    sugerencias = []
    for campo in CAMPOS_INTERNOS:
        mejor_columna = None
        mejor_puntaje = 0
        for columna, columna_norm in normalizadas:
            puntaje = _puntaje(campo.codigo, columna_norm)
            if puntaje > mejor_puntaje:
                mejor_columna = columna
                mejor_puntaje = puntaje
        if mejor_puntaje < 55:
            mejor_columna = None
            mejor_puntaje = 0
        sugerencias.append(MapeoSugerido(campo, mejor_columna, mejor_puntaje))
    return sugerencias


def puntaje_columnas_requeridas(columnas):
    normalizadas = [_normalizar(columna) for columna in columnas]
    puntaje_total = 0
    encontrados = 0
    for campo in CAMPOS_INTERNOS:
        if not campo.requerido:
            continue
        mejor = max((_puntaje(campo.codigo, columna) for columna in normalizadas), default=0)
        if mejor >= 55:
            encontrados += 1
        puntaje_total += mejor
    return encontrados, puntaje_total


def _puntaje(codigo, columna_norm):
    mejor = 0
    for sinonimo in SINONIMOS.get(codigo, []):
        sinonimo_norm = _normalizar(sinonimo)
        if columna_norm == sinonimo_norm:
            mejor = max(mejor, 100)
        elif sinonimo_norm in columna_norm or columna_norm in sinonimo_norm:
            mejor = max(mejor, 80)
        else:
            palabras = set(sinonimo_norm.split())
            columna_palabras = set(columna_norm.split())
            if palabras and palabras <= columna_palabras:
                mejor = max(mejor, 70)
    return mejor


def _normalizar(texto):
    texto = str(texto or "").strip().lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(char for char in texto if not unicodedata.combining(char))
    for char in "._-/\\()[]{}:;,#":
        texto = texto.replace(char, " ")
    return " ".join(texto.split())
