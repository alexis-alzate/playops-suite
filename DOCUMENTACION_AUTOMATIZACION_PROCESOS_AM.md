# Plantilla de Documentacion de Automatizaciones y mejoras

## 1. Informacion General

**Nombre de la automatizacion:** Automatizacion Procesos AM - Monitoreo LISTO y Cargue de Rutas  
**Area responsable:** Soporte  
**Responsable:** Equipo de Soporte / Help Desk  
**Fecha de creacion:** 17-07-2026  
**Estado:** En estabilizacion operativa

## 2. Objetivo

Automatizar procesos operativos internos del area de Soporte relacionados con el monitoreo de infraestructura LISTO y la preparacion de archivos para cargue de rutas en el sistema LISTO.

Con esta automatizacion se busca optimizar el tiempo de ejecucion, reducir la intervencion manual, minimizar el riesgo de errores operativos, mejorar la trazabilidad de los procesos ejecutados y asegurar que la informacion generada sea consistente, validada y organizada.

La aplicacion permite centralizar en una misma herramienta la revision diaria de procesos LISTO y el procesamiento de archivos Excel enviados por clientes para generar el archivo final requerido por el sistema.

## 3. Alcance

- Ejecutar el monitoreo de procesos LISTO desde una aplicacion de escritorio.
- Validar conexion VPN antes de iniciar el monitoreo.
- Consultar los servidores internos y externos definidos para la revision 7 AM.
- Detectar novedades reales en los procesos LISTO.
- Omitir alertas que correspondan a excepciones previamente identificadas.
- Generar evidencia HTML y resumen del estado de los procesos.
- Organizar los reportes por fecha y tipo de revision.
- Procesar archivos Excel enviados por clientes para cargue de rutas.
- Detectar y mapear columnas del archivo del cliente.
- Limpiar documentos, nombres, valores, telefonos y textos.
- Eliminar tildes, puntos, simbolos y caracteres especiales no permitidos.
- Validar saldos, abonos, intereses, fechas, documentos y periodicidad.
- Reconstruir abonos cuando el cliente no los informa y existe saldo actual.
- Detectar duplicados para que el analista confirme si corresponden a creditos diferentes.
- Generar el archivo CSV final requerido para cargar en LISTO.
- Registrar la ejecucion en una bitacora central sincronizada por OneDrive/SharePoint.
- Diferenciar cargues de prueba y cargues de produccion.
- Permitir eliminar registros de prueba desde la aplicacion.

## 4. Problema que mitiga

- El monitoreo de procesos LISTO podia requerir que un analista revisara manualmente diferentes servidores, validara estados, identificara novedades, guardara evidencias y compartiera el resultado con el equipo. Este proceso podia consumir alrededor de 30 minutos en condiciones normales. Cuando se presentaban novedades, desconexion de VPN, fallas de acceso o necesidad de revisar excepciones, el tiempo podia aumentar aproximadamente entre 40 y 50 minutos.

- El cargue de rutas tambien se realizaba de forma manual mediante archivos Excel enviados por clientes. El analista debia identificar columnas, copiar documentos, nombres, telefonos, valores de credito, saldos, abonos, periodicidad y fechas, limpiar informacion, validar diferencias y generar el archivo final para LISTO. Este proceso podia consumir alrededor de 1 hora operativa por cargue, dependiendo de la calidad del archivo recibido.

- Ambos procesos estaban expuestos a errores humanos como omisiones, datos mal copiados, formatos incorrectos, archivos rechazados por LISTO, falta de evidencia, retrasos en la entrega y poca trazabilidad sobre quien ejecuto cada actividad.

- La automatizacion mitiga estos riesgos al ejecutar validaciones guiadas, generar archivos estandarizados, dejar bitacoras, separar pruebas de produccion y reducir la dependencia de tareas repetitivas manuales.

## Relacion de ahorro tiempo area de soporte

### Tiempo mitigado por ejecucion

| Proceso | Tiempo manual estimado | Control automatizado |
|---|---:|---|
| Monitoreo procesos LISTO 7 AM | 30 minutos | Revision guiada, evidencia y resumen automatico |
| Cargue de rutas | 1 hora | Validacion, limpieza, generacion CSV y bitacora |

### Relacion de tiempo estimada

> Calculo referencial si ambos procesos se ejecutan una vez por dia laboral.

#### Monitoreo procesos LISTO 7 AM

| Periodo | Diario | Semanal | Mensual | Semestral | Anual |
|---|---:|---:|---:|---:|---:|
| Tiempo | 30 minutos | 2,5 horas | 10 horas | 60 horas | 120 horas |

> Si existen novedades o fallas de acceso, el monitoreo puede tardar entre 40 y 50 minutos por ejecucion.

#### Cargue de rutas

| Periodo | Diario | Semanal | Mensual | Semestral | Anual |
|---|---:|---:|---:|---:|---:|
| Tiempo | 1 hora | 5 horas | 20 horas | 120 horas | 240 horas |

## Observaciones

- Los tiempos son estimados operativos y pueden variar segun novedades, calidad del archivo recibido, disponibilidad de VPN, estado de OneDrive y respuesta del sistema LISTO.
- La automatizacion no reemplaza la revision humana cuando existen diferencias financieras, duplicados, informacion ambigua o datos que requieren confirmacion del cliente.
- La bitacora central permite llevar control de fecha, hora, responsable, equipo, nombre de base de datos, tipo de cargue y resultado generado.
