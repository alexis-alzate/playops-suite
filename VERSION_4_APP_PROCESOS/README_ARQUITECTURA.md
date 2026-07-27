# Procesos AM V4

Esta version separa la aplicacion en capas para permitir nuevos modulos sin mezclar logica de negocio con interfaz.

## Capas

- `ui/`: solo pantallas, navegacion y componentes visuales.
- `modules/`: procesos funcionales independientes.
- `shared/`: utilidades reutilizables entre modulos.
- `assets/`: imagenes e iconos.
- `output/`: salidas generadas por modulos.

## Modulos iniciales

- `modules/procesos`: monitoreo LISTO actual. Usa `legacy_monitor.py` por compatibilidad mientras migramos pieza por pieza.
- `modules/cargue_rutas`: esqueleto para seleccionar, limpiar, calcular, validar y exportar archivos de rutas.

## Regla de arquitectura

La UI no debe contener reglas de negocio. La UI llama servicios del modulo y muestra resultados.

## Ejecucion en desarrollo

```powershell
cd C:\Automatizaciones\procesoAM\VERSION_4_APP_PROCESOS
python main.py
```

## Build

```powershell
cd C:\Automatizaciones\procesoAM\VERSION_4_APP_PROCESOS\build
.\build_exe.bat
```

La version estable actual sigue siendo `C:\Automatizaciones\procesoAM\Procesos Am.exe`.
