from pathlib import Path
import sys


APP_NAME = "Procesos AM"
APP_TITLE = "PlayOps Suite - Playtech Help Desk"
APP_VERSION = "14.4.6"

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
    RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", BASE_DIR))
    ASSETS_DIR = RESOURCE_DIR / "app_procesos" / "assets"
else:
    BASE_DIR = Path(__file__).resolve().parent
    RESOURCE_DIR = BASE_DIR
    ASSETS_DIR = RESOURCE_DIR / "assets"

if not ASSETS_DIR.exists():
    ASSETS_DIR = BASE_DIR / "_internal" / "app_procesos" / "assets"
LOGO_PNG = ASSETS_DIR / "logo.png"
LOGO_ICO = ASSETS_DIR / "logo.ico"
TEMPLATES_DIR = ASSETS_DIR / "templates"
CARGUE_RUTAS_TEMPLATE = TEMPLATES_DIR / "formatoArchivoCreditosbase.xls"
OUTPUT_DIR = BASE_DIR.parent / "output"
REPORTS_DIR = OUTPUT_DIR / "reportes"
TEMP_DIR = OUTPUT_DIR / "temporales"
LOGS_DIR = BASE_DIR / "logs"
LISTO_OUTPUT_DIR = Path("C:/Listo")
USER_CONFIG_DIR = Path.home() / "AppData" / "Local" / "Procesos AM V2"
USER_CONFIG_FILE = USER_CONFIG_DIR / "config.json"
