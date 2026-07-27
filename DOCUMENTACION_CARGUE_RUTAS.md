# Plantilla de Documentacion de Automatizaciones y mejoras

## 1. Informacion General

**Nombre de la automatizacion:** Automatizacion Cargue de rutas LISTO  
**Area responsable:** Soporte  
**Responsable:** Equipo de Soporte / Help Desk  
**Fecha de creacion:** 17-07-2026  
**Estado:** En estabilizacion operativa

## 2. Objetivo

Automatizar la preparacion de archivos de cargue de rutas enviados por clientes, con el fin de limpiar la informacion, validar datos, detectar inconsistencias, generar el archivo CSV requerido por LISTO y dejar trazabilidad del proceso ejecutado.

Con esta automatizacion se busca reducir la intervencion manual sobre archivos Excel, minimizar errores de copia y pegado, evitar rechazos por formato en LISTO y apoyar al analista en la validacion de datos financieros que requieren revision.

## 3. Alcance

- Procesar archivos Excel enviados por clientes para cargue de rutas.
- Detectar y mapear columnas del archivo del cliente.
- Limpiar documentos, nombres, valores, telefonos y textos.
- Eliminar tildes, puntos, simbolos y caracteres especiales no permitidos.
- Validar saldos, abonos, intereses, fechas, documentos y periodicidad.
- Reconstruir abonos cuando el cliente no los informa y existe saldo actual.
- Detectar duplicados para que el analista confirme si corresponden a creditos diferentes.
- Permitir correcciones antes de generar el archivo final.
- Generar el archivo CSV final requerido para cargar en LISTO.
- Registrar la ejecucion en una bitacora central sincronizada por OneDrive/SharePoint.
- Diferenciar cargues de prueba y cargues de produccion.
- Permitir eliminar registros de prueba desde la aplicacion.

## 4. Problema que mitiga

- El cargue de rutas se realizaba manualmente mediante archivos Excel enviados por clientes. El analista debia identificar columnas, copiar documentos, nombres, telefonos, valores de credito, saldos, abonos, periodicidad y fechas, limpiar informacion, validar diferencias y generar el archivo final para LISTO.

- Este proceso podia consumir alrededor de 1 hora operativa por cargue, dependiendo de la calidad del archivo recibido y de las diferencias que se encontraran.

- El proceso manual estaba expuesto a errores como copiar datos incorrectos, dejar caracteres no permitidos, interpretar mal una columna, generar saldos inconsistentes, duplicar clientes sin validacion o crear un archivo que LISTO rechazara.

- La automatizacion mitiga estos riesgos al guiar el proceso, limpiar datos, validar inconsistencias, generar el CSV final, separar pruebas de produccion y registrar la trazabilidad del cargue.

## Relacion de ahorro tiempo area de soporte

| Proceso | Tiempo manual estimado | Tiempo actual automatizado | Ahorro estimado |
|---|---:|---:|---:|
| Cargue de rutas | 1 hora | Maximo 5 minutos | 55 minutos por cargue |

## Relacion de tiempo

| Periodo | Diario | Semanal | Mensual | Semestral | Anual |
|---|---:|---:|---:|---:|---:|
| Tiempo manual | 1 hora | 5 horas | 20 horas | 120 horas | 240 horas |
| Tiempo automatizado | 5 minutos | 25 minutos | 1 hora 40 minutos | 10 horas | 20 horas |
| Ahorro estimado | 55 minutos | 4 horas 35 minutos | 18 horas 20 minutos | 110 horas | 220 horas |

## Observaciones

- Si el archivo del cliente trae datos incompletos o inconsistentes, el tiempo puede aumentar por revision humana.
- La automatizacion no reemplaza la confirmacion con el cliente cuando existen diferencias financieras.
- Los cargues de prueba pueden eliminarse desde la aplicacion sin afectar los registros de produccion.
