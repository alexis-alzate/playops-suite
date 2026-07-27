# Plantilla de Documentacion de Automatizaciones y mejoras

## 1. Informacion General

**Nombre de la automatizacion:** Automatizacion Monitoreo procesos LISTO 7 AM  
**Area responsable:** Soporte  
**Responsable:** Equipo de Soporte / Help Desk  
**Fecha de creacion:** 17-07-2026  
**Estado:** En estabilizacion operativa

## 2. Objetivo

Automatizar la revision de los procesos LISTO que se valida diariamente en el monitoreo de las 7 AM, con el fin de reducir el tiempo de ejecucion, disminuir errores manuales, generar evidencia organizada y entregar un resumen confiable del estado de la infraestructura.

Con esta automatizacion se busca que el analista no tenga que ingresar manualmente a cada servidor, revisar cada tabla, identificar novedades una por una y organizar evidencias de forma manual.

## 3. Alcance

- Ejecutar el monitoreo de procesos LISTO desde una aplicacion de escritorio.
- Validar conexion VPN antes de iniciar el monitoreo.
- Consultar los servidores internos y externos definidos para la revision 7 AM.
- Detectar novedades reales en los procesos LISTO.
- Omitir alertas que correspondan a excepciones previamente identificadas.
- Generar evidencia HTML por servidor consultado.
- Generar resumen del estado de los procesos.
- Organizar los reportes por fecha y tipo de revision.
- Dejar evidencia para seguimiento operativo del area de Soporte.

## 4. Problema que mitiga

- El monitoreo de procesos LISTO se realizaba de forma manual, lo que podia requerir que un analista ingresara a diferentes servidores, validara estados, identificara novedades, revisara excepciones, guardara evidencias y compartiera el resultado con el equipo.

- Este proceso podia consumir alrededor de 30 minutos en condiciones normales. Cuando existian novedades, fallas de VPN, fallas de acceso o necesidad de revisar excepciones, el tiempo podia aumentar aproximadamente entre 40 y 50 minutos.

- El proceso manual estaba expuesto a errores humanos como omitir servidores, interpretar mal una novedad, no guardar evidencia, retrasar el reporte o reportar alertas que correspondian a excepciones conocidas.

- La automatizacion mitiga estos riesgos al ejecutar la revision de forma guiada, generar evidencia automaticamente, aplicar excepciones conocidas y reducir la actividad manual del analista.

## Relacion de ahorro tiempo area de soporte

| Proceso | Tiempo manual estimado | Tiempo actual automatizado | Ahorro estimado |
|---|---:|---:|---:|
| Monitoreo procesos LISTO 7 AM | 30 minutos | Maximo 2 minutos | 28 minutos por ejecucion |

## Relacion de tiempo

| Periodo | Diario | Semanal | Mensual | Semestral | Anual |
|---|---:|---:|---:|---:|---:|
| Tiempo manual | 30 minutos | 2,5 horas | 10 horas | 60 horas | 120 horas |
| Tiempo automatizado | 2 minutos | 10 minutos | 40 minutos | 4 horas | 8 horas |
| Ahorro estimado | 28 minutos | 2 horas 20 minutos | 9 horas 20 minutos | 56 horas | 112 horas |

## Observaciones

- Si existen novedades, fallas de acceso o desconexion de VPN, el tiempo puede aumentar porque se requiere revision humana.
- La automatizacion no elimina la responsabilidad del analista de revisar alertas reales.
- La evidencia generada debe conservarse como soporte operativo.
