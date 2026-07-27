import unicodedata
from dataclasses import replace

from app_procesos.shared.date_utils import normalize_date_value
from app_procesos.shared.money_utils import parse_int, parse_money, parse_percent_number
from app_procesos.shared.text_utils import clean_human_text, clean_numeric_identifier

from .models import RegistroRuta, ResultadoNormalizacion


PERIODICIDAD_CODIGOS = {
    "diario": 1,
    "diaria": 1,
    "dia": 1,
    "dias": 1,
    "d": 1,
    "semanal": 2,
    "semana": 2,
    "semanas": 2,
    "s": 2,
    "quincenal": 3,
    "quincena": 3,
    "quincenas": 3,
    "q": 3,
    "mensual": 4,
    "mes": 4,
    "meses": 4,
    "m": 4,
}

PERIODICIDAD_INTERVALOS = {
    1: ("diario", 1),
    2: ("semanal", 7),
    3: ("quincenal", 15),
    4: ("mensual", 30),
}

DIRECCION_GENERICA = "SIN DIRECCION"
TELEFONO_GENERICO = "3000000000"
MAX_TEXTO_LISTO = 50


def normalizar_registros(
    preview,
    mapeo,
    *,
    interes_default=None,
    periodicidad_default_codigo=None,
    periodicidad_override_codigo=None,
):
    columna_por_campo = construir_columna_por_campo(mapeo)
    errores_generales = []
    requeridos = ["documento", "nombres", "valor_credito", "saldo_actual"]
    faltantes = [campo for campo in requeridos if campo not in columna_por_campo]
    if faltantes:
        errores_generales.append(
            "Faltan campos requeridos por mapear: " + ", ".join(faltantes)
        )

    registros = []
    direcciones_genericas = 0
    telefonos_genericos = 0
    fechas_normalizadas = 0
    textos_recortados = 0
    for index, fila in enumerate(preview.filas_muestra, start=2):
        fila_origen = parse_int(fila.get("__fila_origen")) or index
        registro = _normalizar_fila(
            fila_origen,
            fila,
            columna_por_campo,
            interes_default=interes_default,
            periodicidad_default_codigo=periodicidad_default_codigo,
            periodicidad_override_codigo=periodicidad_override_codigo,
        )
        if DIRECCION_GENERICA in registro.errores:
            direcciones_genericas += 1
        if TELEFONO_GENERICO in registro.errores:
            telefonos_genericos += 1
        if "Fecha escrita normalizada" in registro.errores:
            fechas_normalizadas += 1
        textos_recortados += sum(1 for error in registro.errores if error == "Texto recortado a 50 caracteres")
        registros.append(registro)

    registros, documentos_ajustados = normalizar_documentos_placeholder(registros)
    if documentos_ajustados:
        errores_generales.append(
            f"Se ajustaron {documentos_ajustados} documento(s) con valor 1 a consecutivos desde 2."
        )
    if direcciones_genericas:
        errores_generales.append(
            f"Se completaron {direcciones_genericas} direccion(es) vacias con '{DIRECCION_GENERICA}'."
        )
    if telefonos_genericos:
        errores_generales.append(
            f"Se completaron {telefonos_genericos} telefono(s) vacios con '{TELEFONO_GENERICO}'."
        )
    if fechas_normalizadas:
        errores_generales.append(
            f"Se normalizaron {fechas_normalizadas} fecha(s) escritas en texto al formato AAAA-MM-DD."
        )
    if textos_recortados:
        errores_generales.append(
            f"Se recortaron {textos_recortados} campo(s) de nombre, apellido o direccion al maximo de 50 caracteres permitido por LISTO."
        )

    registros = [
        replace(
            registro,
            errores=[
                error for error in registro.errores
                if error not in {DIRECCION_GENERICA, TELEFONO_GENERICO, "Fecha escrita normalizada", "Texto recortado a 50 caracteres"}
            ],
        )
        for registro in registros
    ]

    total_con_error = sum(1 for registro in registros if registro.errores)
    total_con_abono = sum(1 for registro in registros if registro.abono_estado == "informado")
    total_reconstruccion = sum(
        1 for registro in registros if registro.abono_estado == "requiere_reconstruccion"
    )

    return ResultadoNormalizacion(
        registros=registros,
        total_registros=len(registros),
        total_validos=len(registros) - total_con_error,
        total_con_error=total_con_error,
        total_con_abono_informado=total_con_abono,
        total_requiere_reconstruccion=total_reconstruccion,
        errores_generales=errores_generales,
    )


def normalizar_documentos_placeholder(registros):
    usados = {
        registro.documento
        for registro in registros
        if registro.documento and registro.documento != "1"
    }
    normalizados = []
    siguiente = 2
    ajustados = 0

    for registro in registros:
        if registro.documento != "1":
            normalizados.append(registro)
            continue

        while str(siguiente) in usados:
            siguiente += 1
        nuevo_documento = str(siguiente)
        usados.add(nuevo_documento)
        siguiente += 1
        ajustados += 1
        normalizados.append(replace(registro, documento=nuevo_documento))

    return normalizados, ajustados


def construir_columna_por_campo(mapeo):
    if isinstance(mapeo, dict):
        return {
            campo: columna
            for campo, columna in mapeo.items()
            if columna
        }

    return {
        item.campo.codigo: item.columna_origen
        for item in mapeo
        if item.columna_origen
    }


def _normalizar_fila(
    fila_origen,
    fila,
    columna_por_campo,
    *,
    interes_default=None,
    periodicidad_default_codigo=None,
    periodicidad_override_codigo=None,
):
    errores = []
    documento = clean_numeric_identifier(_valor(fila, columna_por_campo, "documento"))
    numero_credito = clean_numeric_identifier(_valor(fila, columna_por_campo, "numero_credito"))
    nombres = clean_human_text(_valor(fila, columna_por_campo, "nombres"))
    apellidos = clean_human_text(_valor(fila, columna_por_campo, "apellidos"))
    direccion_original = _valor(fila, columna_por_campo, "direccion")
    telefono_original = _valor(fila, columna_por_campo, "telefono")
    direccion = clean_human_text(direccion_original)
    telefono = clean_numeric_identifier(telefono_original)
    fecha_credito_original = _valor(fila, columna_por_campo, "fecha_credito")
    fecha_prox_pago_original = _valor(fila, columna_por_campo, "fecha_prox_pago")
    fecha_credito = normalize_date_value(fecha_credito_original) or clean_human_text(fecha_credito_original)
    fecha_prox_pago = normalize_date_value(fecha_prox_pago_original) or clean_human_text(fecha_prox_pago_original)
    tipo_pago = clean_human_text(_valor(fila, columna_por_campo, "tipo_pago"))
    periodicidad = clean_human_text(_valor(fila, columna_por_campo, "periodicidad"))
    periodicidad_codigo = _resolver_periodicidad_codigo(
        periodicidad or tipo_pago,
        periodicidad_default_codigo,
        override_codigo=periodicidad_override_codigo,
    )

    valor_credito = parse_money(_valor(fila, columna_por_campo, "valor_credito"))
    interes = parse_percent_number(_valor(fila, columna_por_campo, "interes"))
    if interes is None:
        interes = parse_percent_number(interes_default)
    cuotas = parse_int(_valor(fila, columna_por_campo, "cuotas"))
    dias_credito_original = parse_int(_valor(fila, columna_por_campo, "dias_credito"))
    dias_credito = resolver_dias_credito_por_cuotas(
        cuotas,
        dias_credito_original,
        periodicidad_codigo,
    )
    saldo_actual = parse_money(_valor(fila, columna_por_campo, "saldo_actual"))
    abono_informado = parse_money(_valor(fila, columna_por_campo, "abono"))

    if not documento:
        errores.append("Documento vacio")
    if not nombres:
        errores.append("Nombre vacio")
    nombres, nombres_recortado = _limitar_texto_listo(nombres)
    apellidos, apellidos_recortado = _limitar_texto_listo(apellidos)
    direccion, direccion_recortada = _limitar_texto_listo(direccion)
    for recortado in (nombres_recortado, apellidos_recortado, direccion_recortada):
        if recortado:
            errores.append("Texto recortado a 50 caracteres")
    if not direccion or _es_valor_vacio_operativo(direccion_original):
        direccion = DIRECCION_GENERICA
        errores.append(DIRECCION_GENERICA)
    if not telefono or _es_valor_vacio_operativo(telefono_original):
        telefono = TELEFONO_GENERICO
        errores.append(TELEFONO_GENERICO)
    if fecha_credito and normalize_date_value(fecha_credito_original):
        errores.append("Fecha escrita normalizada")
    if fecha_prox_pago and normalize_date_value(fecha_prox_pago_original):
        errores.append("Fecha escrita normalizada")
    if valor_credito is None:
        errores.append("Valor credito vacio o invalido")
    if saldo_actual is None:
        errores.append("Saldo actual vacio o invalido")
    if periodicidad_codigo is None:
        errores.append("Periodicidad vacia o no reconocida")
    errores.extend(validar_cuotas_vs_plazo(cuotas, dias_credito_original, periodicidad_codigo))

    abono_estado = "requiere_reconstruccion"
    if "abono" in columna_por_campo:
        if abono_informado is None:
            abono_estado = "requiere_reconstruccion"
        else:
            abono_estado = "informado"

    if abono_estado == "requiere_reconstruccion" and saldo_actual is None:
        errores.append("No se puede reconstruir abono sin saldo actual")

    return RegistroRuta(
        fila_origen=fila_origen,
        documento=documento,
        numero_credito=numero_credito,
        nombres=nombres,
        apellidos=apellidos,
        direccion=direccion,
        telefono=telefono,
        fecha_credito=fecha_credito,
        valor_credito=valor_credito,
        interes=interes,
        cuotas=cuotas,
        dias_credito=dias_credito,
        tipo_pago=tipo_pago,
        periodicidad=periodicidad,
        periodicidad_codigo=periodicidad_codigo,
        fecha_prox_pago=fecha_prox_pago,
        saldo_actual=saldo_actual,
        abono_informado=abono_informado,
        saldo_sin_abonos=None,
        abono_reconstruido=None,
        saldo_final_calculado=None,
        diferencia_saldo=None,
        abono_estado=abono_estado,
        errores=errores,
    )


def validar_cuotas_vs_plazo(cuotas, dias_credito, periodicidad_codigo):
    if cuotas is None and dias_credito is None:
        return []

    errores = []
    if cuotas is not None and cuotas <= 0:
        errores.append("Cantidad de cuotas debe ser mayor a 0")
    if dias_credito is not None and dias_credito <= 0:
        errores.append("Dias credito debe ser mayor a 0")
    if errores or cuotas is None or dias_credito is None or periodicidad_codigo not in PERIODICIDAD_INTERVALOS:
        return errores

    periodo, intervalo = PERIODICIDAD_INTERVALOS[periodicidad_codigo]
    if periodicidad_codigo == 1 and _es_rango_diario_mensual(cuotas, dias_credito):
        return errores

    dias_esperados = cuotas * intervalo
    if dias_credito != dias_esperados and not (periodicidad_codigo != 1 and dias_credito == cuotas):
        errores.append(
            "Dias credito inconsistente: "
            f"{cuotas} cuotas en periodo {periodo} equivalen a {dias_esperados} dias, "
            f"pero el archivo trae {dias_credito} dias. Confirmar con cliente."
        )
    return errores


def resolver_dias_credito_por_cuotas(cuotas, dias_credito, periodicidad_codigo):
    if cuotas is None or cuotas <= 0 or periodicidad_codigo not in PERIODICIDAD_INTERVALOS:
        return dias_credito

    _periodo, intervalo = PERIODICIDAD_INTERVALOS[periodicidad_codigo]
    dias_calculados = cuotas * intervalo
    if dias_credito is None:
        return dias_calculados

    if periodicidad_codigo == 1 and _es_rango_diario_mensual(cuotas, dias_credito):
        return cuotas

    if periodicidad_codigo != 1 and dias_credito == cuotas:
        return dias_calculados

    return dias_credito


def _es_rango_diario_mensual(cuotas, dias_credito):
    return cuotas in {28, 29, 30, 31} and dias_credito in {28, 29, 30, 31}


def _valor(fila, columna_por_campo, campo):
    columna = columna_por_campo.get(campo)
    if not columna:
        return ""
    return fila.get(columna, "")


def _resolver_periodicidad_codigo(value, default_codigo, *, override_codigo=None):
    if override_codigo in {1, 2, 3, 4}:
        return override_codigo
    codigo = _normalizar_codigo_periodicidad(value)
    if codigo is not None:
        return codigo
    return default_codigo


def _normalizar_codigo_periodicidad(value):
    text = _normalizar_texto(value)
    if not text:
        return None
    if text in {"1", "2", "3", "4"}:
        return int(text)
    return PERIODICIDAD_CODIGOS.get(text)


def _normalizar_texto(value):
    text = str(value or "").strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    for char in "._-/\\()[]{}:;,#":
        text = text.replace(char, " ")
    return " ".join(text.split())


def _es_valor_vacio_operativo(value):
    text = _normalizar_texto(value)
    return text in {
        "",
        "na",
        "n a",
        "no aplica",
        "no tiene",
        "sin dato",
        "sin datos",
        "sin informacion",
        "sin direccion",
        "ninguno",
        "ninguna",
        "null",
        "none",
        "vacio",
    }


def _limitar_texto_listo(value):
    text = str(value or "").strip()
    if len(text) <= MAX_TEXTO_LISTO:
        return text, False
    return text[:MAX_TEXTO_LISTO].rstrip(), True
