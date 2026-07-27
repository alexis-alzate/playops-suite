import os
import socket
import tkinter as tk
from tkinter import messagebox
from pathlib import Path

from app_procesos.config import APP_TITLE, APP_VERSION, BASE_DIR, LISTO_OUTPUT_DIR, LOGS_DIR, REPORTS_DIR, USER_CONFIG_FILE
from app_procesos.shared.activity import obtener_historial_dashboard
from app_procesos.shared.diagnostics import abrir_carpeta_diagnosticos, exportar_diagnostico
from app_procesos.shared.executive_report import exportar_resumen_ejecutivo
from app_procesos.shared.settings import load_settings, save_settings
from app_procesos.shared.teams_summary import (
    copiar_ultima_imagen_para_teams,
    copiar_ultimo_resumen_para_teams,
)
from app_procesos.shared.updater import check_for_update, launch_update

from .theme import COLORS, FONT_BODY, FONT_BODY_BOLD, FONT_H2, FONT_MONO
from .widgets import RoundedButton


class DashboardView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLORS["bg"])
        self.canvas = tk.Canvas(self, bg=COLORS["bg"], highlightthickness=0, bd=0)
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.content_frame = tk.Frame(self.canvas, bg=COLORS["bg"])
        self.canvas_window = self.canvas.create_window((0, 0), window=self.content_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.content_frame.bind("<Configure>", self._update_scroll_region)
        self.canvas.bind("<Configure>", self._resize_canvas_window)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)

        settings = load_settings()
        self.teams_enabled = tk.BooleanVar(value=bool(settings.get("teams_enabled")))
        self.teams_url = tk.StringVar(value=settings.get("teams_webhook_url", ""))
        self.monitor_demo_enabled = tk.BooleanVar(value=bool(settings.get("monitor_demo_enabled")))
        self.monitor_config_status = tk.StringVar(value=f"Configuracion local: {USER_CONFIG_FILE}")
        self.teams_status = tk.StringVar(value=f"Configuracion local: {USER_CONFIG_FILE}")
        self.update_status = tk.StringVar(value="Presione buscar actualizacion para consultar la version disponible.")
        self.update_info = None
        self.history_rows = []
        self.log_text = None
        self.log_shell = None
        self.logs_toggle_button = None
        self.logs_visible = False
        self.section_panels = {}
        self._build()

    def _build(self):
        root = self.content_frame
        tk.Label(
            root,
            text="Dashboard",
            bg=COLORS["bg"],
            fg=COLORS["text"],
            font=("Segoe UI", 22, "bold"),
        ).pack(anchor="w")
        tk.Label(
            root,
            text="Centro de operaciones para los procesos internos del equipo.",
            bg=COLORS["bg"],
            fg=COLORS["muted"],
            font=FONT_BODY,
        ).pack(anchor="w", pady=(6, 22))

        grid = tk.Frame(root, bg=COLORS["bg"])
        grid.pack(fill="x")
        self._card(grid, "Monitoreo LISTO", "Revision 7 AM, reportes y SharePoint.").pack(
            side="left", fill="x", expand=True, padx=(0, 12)
        )
        self._card(grid, "Cargue de rutas", "Modulo nuevo para limpiar, validar y exportar rutas.").pack(
            side="left", fill="x", expand=True, padx=(12, 0)
        )

        self.section_panels = {
            "historial": self._history_panel(),
            "logs": self._logs_panel(),
            "configuracion": self._monitor_settings_panel(),
            "teams": self._teams_panel(),
            "diagnostico": self._diagnostics_panel(),
            "actualizaciones": self._updates_panel(),
            "acerca": self._about_panel(),
        }
        self.show_section("historial")

    def _update_scroll_region(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _resize_canvas_window(self, event):
        self.canvas.itemconfigure(self.canvas_window, width=event.width)
        self._update_scroll_region()

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def show_section(self, section):
        for panel in self.section_panels.values():
            panel.pack_forget()
        panel = self.section_panels.get(section) or self.section_panels.get("historial")
        if panel:
            panel.pack(fill="x", pady=(22, 0))
        self.canvas.yview_moveto(0)
        self._update_scroll_region()

    def _card(self, parent, title, description):
        card = tk.Frame(parent, bg=COLORS["panel"], padx=18, pady=18)
        tk.Label(card, text=title, bg=COLORS["panel"], fg=COLORS["text"], font=FONT_H2).pack(anchor="w")
        tk.Label(
            card,
            text=description,
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=FONT_BODY,
            wraplength=320,
            justify="left",
        ).pack(anchor="w", pady=(8, 0))
        return card

    def _history_panel(self):
        panel = tk.Frame(self.content_frame, bg=COLORS["panel"], padx=18, pady=18)
        header = tk.Frame(panel, bg=COLORS["panel"])
        header.pack(fill="x")
        tk.Label(header, text="Historial operativo", bg=COLORS["panel"], fg=COLORS["text"], font=FONT_H2).pack(
            side="left"
        )
        self._button(header, "Actualizar", self._refresh_history).pack(side="right", ipadx=18)
        self._button(header, "Exportar resumen ejecutivo", self._export_executive_report, primary=True).pack(
            side="right", ipadx=18, padx=(0, 10)
        )

        tk.Label(
            panel,
            text="Resumen rapido de las ultimas actividades. Desde aqui tambien puede generar el informe ejecutivo.",
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=FONT_BODY,
            wraplength=880,
            justify="left",
        ).pack(anchor="w", pady=(8, 14))

        table = tk.Frame(panel, bg=COLORS["panel"])
        table.pack(fill="x")
        self._history_header(table)
        self.history_rows = []
        for _ in range(4):
            row = self._history_row(table)
            self.history_rows.append(row)
        self._refresh_history()
        return panel

    def _executive_panel(self):
        panel = tk.Frame(self.content_frame, bg=COLORS["panel"], padx=18, pady=18)
        tk.Label(panel, text="Resumen ejecutivo", bg=COLORS["panel"], fg=COLORS["text"], font=FONT_H2).pack(anchor="w")
        tk.Label(
            panel,
            text="Genera un Excel organizado con responsable, hora, version, equipo, historial reciente y estado operativo.",
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=FONT_BODY,
            wraplength=880,
            justify="left",
        ).pack(anchor="w", pady=(8, 14))

        actions = tk.Frame(panel, bg=COLORS["panel"])
        actions.pack(fill="x")
        self._button(actions, "Exportar resumen ejecutivo", self._export_executive_report, primary=True).pack(
            side="left", ipadx=28, padx=(0, 12)
        )
        return panel

    def _logs_panel(self):
        panel = tk.Frame(self.content_frame, bg=COLORS["panel"], padx=18, pady=18)
        header = tk.Frame(panel, bg=COLORS["panel"])
        header.pack(fill="x")
        tk.Label(header, text="Visor de logs", bg=COLORS["panel"], fg=COLORS["text"], font=FONT_H2).pack(side="left")
        self.logs_toggle_button = self._button(header, "Mostrar visor", self._toggle_log_viewer)
        self.logs_toggle_button.pack(side="right", ipadx=20)

        actions = tk.Frame(panel, bg=COLORS["panel"])
        actions.pack(fill="x", pady=(12, 10))
        self._button(actions, "Ultimo log monitoreo", self._show_latest_monitor_log, primary=True).pack(
            side="left", ipadx=18, padx=(0, 10)
        )
        self._button(actions, "Ultima bitacora cargue", self._show_latest_cargue_log).pack(
            side="left", ipadx=18, padx=(0, 10)
        )
        self._button(actions, "Limpiar visor", self._clear_log_viewer).pack(side="left", ipadx=18)

        self.log_shell = tk.Frame(panel, bg=COLORS["line"], padx=1, pady=1)
        text_frame = tk.Frame(self.log_shell, bg=COLORS["console"])
        text_frame.pack(fill="both")
        self.log_text = tk.Text(
            text_frame,
            height=12,
            bg=COLORS["console"],
            fg=COLORS.get("console_text", COLORS["text"]),
            insertbackground=COLORS.get("console_text", COLORS["text"]),
            selectbackground="#1f6feb",
            relief="flat",
            font=FONT_MONO,
            wrap="word",
            padx=14,
            pady=12,
        )
        self.log_text.pack(side="left", fill="both", expand=True)
        scrollbar = tk.Scrollbar(text_frame, command=self.log_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=scrollbar.set)
        self.log_text.insert("end", "Seleccione un log para revisar aqui los detalles tecnicos.\n")
        self.log_text.configure(state="disabled")
        return panel

    def _monitor_settings_panel(self):
        panel = tk.Frame(self.content_frame, bg=COLORS["panel"], padx=18, pady=18)
        tk.Label(panel, text="Configuracion de monitoreo", bg=COLORS["panel"], fg=COLORS["text"], font=FONT_H2).pack(anchor="w")
        tk.Label(
            panel,
            text=(
                "Ajustes locales para pruebas y presentaciones. El modo demo agrega una novedad simulada "
                "al reporte sin modificar las excepciones reales de produccion."
            ),
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=FONT_BODY,
            wraplength=880,
            justify="left",
        ).pack(anchor="w", pady=(8, 14))

        tk.Checkbutton(
            panel,
            text="Activar modo demo de novedades",
            variable=self.monitor_demo_enabled,
            bg=COLORS["panel"],
            fg=COLORS["text"],
            activebackground=COLORS["panel"],
            activeforeground=COLORS["text"],
            selectcolor=COLORS["panel_2"],
            font=FONT_BODY_BOLD,
        ).pack(anchor="w", pady=(0, 12))

        actions = tk.Frame(panel, bg=COLORS["panel"])
        actions.pack(fill="x")
        self._button(actions, "Guardar monitoreo", self._save_monitor_settings, primary=True).pack(
            side="left", ipadx=26, padx=(0, 12)
        )
        self._button(actions, "Desactivar demo", self._disable_monitor_demo).pack(side="left", ipadx=22)

        tk.Label(
            panel,
            textvariable=self.monitor_config_status,
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=("Segoe UI", 9),
            wraplength=880,
            justify="left",
        ).pack(anchor="w", pady=(12, 0))
        return panel

    def _history_header(self, parent):
        row = tk.Frame(parent, bg=COLORS["panel_2"], padx=12, pady=8)
        row.pack(fill="x", pady=(0, 2))
        for text, width in (("Proceso", 22), ("Estado", 16), ("Detalle", 54), ("Ruta", 42)):
            tk.Label(
                row,
                text=text,
                bg=COLORS["panel_2"],
                fg=COLORS["accent_2"],
                font=("Segoe UI", 9, "bold"),
                width=width,
                anchor="w",
            ).pack(side="left", padx=(0, 8))

    def _history_row(self, parent):
        row = tk.Frame(parent, bg=COLORS["panel_2"], padx=12, pady=9)
        row.pack(fill="x", pady=2)
        labels = {}
        for key, width in (("proceso", 22), ("estado", 16), ("detalle", 54), ("ruta", 42)):
            label = tk.Label(
                row,
                text="",
                bg=COLORS["panel_2"],
                fg=COLORS["text"] if key != "estado" else COLORS["muted"],
                font=FONT_BODY_BOLD if key == "proceso" else FONT_BODY,
                width=width,
                anchor="w",
            )
            label.pack(side="left", padx=(0, 8))
            labels[key] = label
        return labels

    def _teams_panel(self):
        panel = tk.Frame(self.content_frame, bg=COLORS["panel"], padx=18, pady=18)
        tk.Label(panel, text="Teams", bg=COLORS["panel"], fg=COLORS["text"], font=FONT_H2).pack(anchor="w")
        tk.Label(
            panel,
            text="Envio automatico del resumen al canal del equipo al finalizar el monitoreo LISTO.",
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=FONT_BODY,
            wraplength=880,
            justify="left",
        ).pack(anchor="w", pady=(8, 14))

        tk.Checkbutton(
            panel,
            text="Activar envio automatico a Teams",
            variable=self.teams_enabled,
            bg=COLORS["panel"],
            fg=COLORS["text"],
            activebackground=COLORS["panel"],
            activeforeground=COLORS["text"],
            selectcolor=COLORS["panel_2"],
            font=FONT_BODY_BOLD,
        ).pack(anchor="w", pady=(0, 12))

        tk.Label(
            panel,
            text="URL de Power Automate / Webhook",
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w", pady=(0, 5))

        tk.Entry(
            panel,
            textvariable=self.teams_url,
            bg=COLORS["panel_2"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            font=FONT_BODY,
        ).pack(fill="x", ipady=10)

        actions = tk.Frame(panel, bg=COLORS["panel"])
        actions.pack(fill="x", pady=(14, 0))
        self._button(actions, "Guardar configuracion", self._save_teams_settings, primary=True).pack(
            side="left", ipadx=26, padx=(0, 12)
        )
        self._button(actions, "Copiar texto Teams", self._copy_teams_summary).pack(
            side="left", ipadx=18, padx=(0, 12)
        )
        self._button(actions, "Copiar imagen Teams", self._copy_teams_image).pack(side="left", ipadx=18)

        tk.Label(
            panel,
            textvariable=self.teams_status,
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=("Segoe UI", 9),
            wraplength=880,
            justify="left",
        ).pack(anchor="w", pady=(12, 0))
        return panel

    def _about_panel(self):
        panel = tk.Frame(self.content_frame, bg=COLORS["panel"], padx=18, pady=18)
        tk.Label(panel, text="Acerca de", bg=COLORS["panel"], fg=COLORS["text"], font=FONT_H2).pack(anchor="w")

        info = tk.Frame(panel, bg=COLORS["panel"])
        info.pack(fill="x", pady=(10, 12))
        items = [
            ("Aplicacion", APP_TITLE),
            ("Desarrollado por", "Victor Alexis Alzate Cortes"),
            ("Version", APP_VERSION),
            ("Equipo", socket.gethostname()),
            ("Instalacion", str(BASE_DIR)),
            ("Logs", str(LOGS_DIR)),
            ("Salida LISTO", str(LISTO_OUTPUT_DIR)),
        ]
        for label, value in items:
            row = tk.Frame(info, bg=COLORS["panel"])
            row.pack(fill="x", pady=2)
            tk.Label(
                row,
                text=f"{label}:",
                bg=COLORS["panel"],
                fg=COLORS["muted"],
                font=("Segoe UI", 9, "bold"),
                width=14,
                anchor="w",
            ).pack(side="left")
            tk.Label(
                row,
                text=value,
                bg=COLORS["panel"],
                fg=COLORS["text"],
                font=FONT_BODY,
                anchor="w",
                wraplength=760,
                justify="left",
            ).pack(side="left", fill="x", expand=True)

        actions = tk.Frame(panel, bg=COLORS["panel"])
        actions.pack(fill="x", pady=(4, 0))
        self._button(actions, "Abrir instalacion", lambda: self._open_path(BASE_DIR), primary=True).pack(
            side="left", ipadx=24, padx=(0, 12)
        )
        self._button(actions, "Abrir logs", lambda: self._open_path(LOGS_DIR)).pack(side="left", ipadx=24)
        return panel

    def _updates_panel(self):
        panel = tk.Frame(self.content_frame, bg=COLORS["panel"], padx=18, pady=18)
        tk.Label(panel, text="Actualizaciones", bg=COLORS["panel"], fg=COLORS["text"], font=FONT_H2).pack(anchor="w")
        tk.Label(
            panel,
            text=(
                "Consulta la version publicada por el equipo y, si existe una mas reciente, "
                "ejecuta la actualizacion con barra de progreso."
            ),
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=FONT_BODY,
            wraplength=880,
            justify="left",
        ).pack(anchor="w", pady=(8, 14))

        actions = tk.Frame(panel, bg=COLORS["panel"])
        actions.pack(fill="x")
        self._button(actions, "Buscar actualizacion", self._check_updates, primary=True).pack(
            side="left", ipadx=26, padx=(0, 12)
        )
        self._button(actions, "Actualizar ahora", self._run_update).pack(side="left", ipadx=24)

        tk.Label(
            panel,
            textvariable=self.update_status,
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=("Segoe UI", 9),
            wraplength=880,
            justify="left",
        ).pack(anchor="w", pady=(14, 0))
        return panel

    def _diagnostics_panel(self):
        panel = tk.Frame(self.content_frame, bg=COLORS["panel"], padx=18, pady=18)
        tk.Label(panel, text="Diagnostico", bg=COLORS["panel"], fg=COLORS["text"], font=FONT_H2).pack(anchor="w")
        tk.Label(
            panel,
            text=(
                "Genera un ZIP para soporte con version, equipo, usuario Windows, IP local, "
                "estado de OneDrive, configuracion sin secretos y ultimos logs."
            ),
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=FONT_BODY,
            wraplength=880,
            justify="left",
        ).pack(anchor="w", pady=(8, 14))

        actions = tk.Frame(panel, bg=COLORS["panel"])
        actions.pack(fill="x")
        self._button(actions, "Exportar diagnostico", self._export_diagnostics, primary=True).pack(
            side="left", ipadx=30, padx=(0, 12)
        )
        self._button(actions, "Abrir carpeta", self._open_diagnostics_folder).pack(side="left", ipadx=24)
        return panel

    def _button(self, parent, text, command, primary=False):
        return RoundedButton(
            parent,
            text,
            command,
            bg=COLORS["accent"] if primary else COLORS["panel_2"],
            fg="white" if primary else COLORS["text"],
            hover_bg=COLORS["accent_hover"] if primary else COLORS["panel_3"],
            active_bg=COLORS["accent_active"] if primary else "#142734",
            disabled_bg=COLORS["disabled"],
            disabled_fg=COLORS["muted"],
            radius=14,
            height=44,
            font=FONT_BODY_BOLD if primary else FONT_BODY,
        )

    def _save_teams_settings(self):
        url = self.teams_url.get().strip()
        if self.teams_enabled.get() and not url:
            messagebox.showwarning(
                "Teams",
                "Para activar Teams debe pegar la URL de Power Automate o del webhook.",
            )
            return

        path = save_settings({
            "teams_enabled": bool(self.teams_enabled.get()),
            "teams_webhook_url": url,
        })
        self.teams_status.set(f"Configuracion guardada: {path}")
        messagebox.showinfo("Teams", "Configuracion guardada.")

    def _save_monitor_settings(self):
        path = save_settings({
            "monitor_demo_enabled": bool(self.monitor_demo_enabled.get()),
        })
        estado = "activo" if self.monitor_demo_enabled.get() else "inactivo"
        self.monitor_config_status.set(f"Modo demo {estado}. Configuracion guardada: {path}")
        messagebox.showinfo("Configuracion de monitoreo", f"Modo demo {estado}.")

    def _disable_monitor_demo(self):
        self.monitor_demo_enabled.set(False)
        self._save_monitor_settings()

    def _refresh_history(self):
        try:
            items = obtener_historial_dashboard()
        except Exception as error:
            messagebox.showerror("Historial operativo", f"No se pudo leer el historial:\n\n{error}")
            return

        for labels, item in zip(self.history_rows, items):
            labels["proceso"].configure(text=item.get("proceso", ""))
            labels["estado"].configure(text=item.get("estado", ""), fg=self._status_color(item.get("estado", "")))
            labels["detalle"].configure(text=item.get("detalle", ""))
            labels["ruta"].configure(text=self._short_path(item.get("ruta", "")))

    def _export_executive_report(self):
        try:
            path = exportar_resumen_ejecutivo()
        except Exception as error:
            messagebox.showerror("Resumen ejecutivo", f"No se pudo generar el resumen:\n\n{error}")
            return
        abrir = messagebox.askyesno(
            "Resumen ejecutivo",
            f"Resumen generado correctamente:\n\n{path}\n\nDesea abrir la carpeta?",
        )
        if abrir:
            self._open_path(path.parent)

    def _show_latest_monitor_log(self):
        self._show_latest_text_file(LOGS_DIR, "*.log", "Aun no hay logs de monitoreo.")

    def _show_latest_cargue_log(self):
        self._show_latest_text_file(REPORTS_DIR, "bitacora_cargue_*.txt", "Aun no hay bitacoras de cargue.")

    def _show_latest_text_file(self, folder, pattern, empty_message):
        file_path = self._latest_file(folder, pattern)
        if not file_path:
            messagebox.showinfo("Visor de logs", empty_message)
            return
        try:
            text = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception as error:
            messagebox.showerror("Visor de logs", f"No se pudo leer el archivo:\n\n{error}")
            return
        if len(text) > 18000:
            text = text[-18000:]
            text = "[Mostrando las ultimas lineas del archivo]\n\n" + text
        self._set_logs_visible(True)
        self._set_log_text(f"{file_path}\n{'=' * 90}\n\n{text}")

    def _toggle_log_viewer(self):
        self._set_logs_visible(not self.logs_visible)

    def _set_logs_visible(self, visible):
        if self.log_shell is None:
            return
        self.logs_visible = visible
        if visible:
            self.log_shell.pack(fill="x")
        else:
            self.log_shell.pack_forget()
        if self.logs_toggle_button is not None:
            self.logs_toggle_button.text = "Ocultar visor" if visible else "Mostrar visor"
            self.logs_toggle_button._draw()

    def _set_log_text(self, text):
        if self.log_text is None:
            return
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.insert("end", text)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _clear_log_viewer(self):
        self._set_log_text("Seleccione un log para revisar aqui los detalles tecnicos.\n")

    def _latest_file(self, folder, pattern):
        folder = Path(folder)
        if not folder.exists():
            return None
        files = [path for path in folder.glob(pattern) if path.is_file()]
        if not files:
            return None
        return max(files, key=lambda path: path.stat().st_mtime)

    def _status_color(self, status):
        normalized = (status or "").lower()
        if normalized in {"correcto", "registrado", "generado", "activo"}:
            return COLORS["accent_2"]
        if "error" in normalized or "no detectado" in normalized:
            return "#f59e0b"
        return COLORS["muted"]

    def _short_path(self, path):
        text = str(path or "")
        if len(text) <= 48:
            return text
        return "..." + text[-45:]

    def _copy_teams_summary(self):
        try:
            path, _mensaje = copiar_ultimo_resumen_para_teams(self.winfo_toplevel())
        except Exception as error:
            messagebox.showwarning(
                "Teams",
                "No se pudo copiar el resumen.\n\n"
                "Ejecute primero una revision de monitoreo o abra un resultado existente.\n\n"
                f"Detalle: {error}",
            )
            return
        messagebox.showinfo("Teams", f"Texto copiado al portapapeles.\n\nFuente:\n{path}")

    def _copy_teams_image(self):
        try:
            path, imagen = copiar_ultima_imagen_para_teams()
        except Exception as error:
            messagebox.showwarning(
                "Teams",
                "No se pudo copiar la imagen.\n\n"
                "Ejecute primero una revision de monitoreo o abra un resultado existente.\n\n"
                f"Detalle: {error}",
            )
            return
        messagebox.showinfo(
            "Teams",
            "Imagen copiada al portapapeles.\n\n"
            "Ahora pegue en Teams con Ctrl+V.\n\n"
            f"Fuente:\n{path}\n\nImagen:\n{imagen}",
        )

    def _export_diagnostics(self):
        try:
            path = exportar_diagnostico()
        except Exception as error:
            messagebox.showerror("Diagnostico", f"No se pudo generar el diagnostico:\n\n{error}")
            return

        abrir = messagebox.askyesno(
            "Diagnostico",
            f"Diagnostico generado correctamente:\n\n{path}\n\nDesea abrir la carpeta?",
        )
        if abrir:
            try:
                os.startfile(str(path.parent))
            except OSError as error:
                messagebox.showerror("Diagnostico", f"No se pudo abrir la carpeta:\n\n{error}")

    def _open_diagnostics_folder(self):
        try:
            abrir_carpeta_diagnosticos()
        except Exception as error:
            messagebox.showerror("Diagnostico", f"No se pudo abrir la carpeta:\n\n{error}")

    def _check_updates(self):
        try:
            info = check_for_update()
        except Exception as error:
            self.update_info = None
            messagebox.showerror("Actualizaciones", f"No se pudo consultar la actualizacion:\n\n{error}")
            return

        self.update_info = info
        manifest = str(info.manifest_path) if info.manifest_path else "No encontrado"
        installer = str(info.installer_path) if info.installer_path else "No definido"
        if info.available:
            self.update_status.set(
                "Nueva version disponible.\n"
                f"- Version instalada: {info.current_version}\n"
                f"- Version nueva: {info.latest_version}\n"
                f"- Instalador: {installer}\n"
                f"- Manifiesto: {manifest}\n\n"
                f"{info.message}"
            )
            messagebox.showinfo(
                "Actualizaciones",
                f"Hay una nueva version disponible.\n\n"
                f"Instalada: {info.current_version}\n"
                f"Nueva: {info.latest_version}",
            )
            return

        self.update_status.set(
            f"{info.message}\n"
            f"- Version instalada: {info.current_version}\n"
            f"- Version publicada: {info.latest_version}\n"
            f"- Manifiesto: {manifest}"
        )
        messagebox.showinfo("Actualizaciones", info.message)

    def _run_update(self):
        info = self.update_info
        if info is None:
            try:
                info = check_for_update()
            except Exception as error:
                messagebox.showerror("Actualizaciones", f"No se pudo consultar la actualizacion:\n\n{error}")
                return
            self.update_info = info

        if not info.available:
            messagebox.showinfo("Actualizaciones", info.message)
            return

        if info.installer_path is None:
            messagebox.showerror("Actualizaciones", "El version.json no define el instalador de actualizacion.")
            return

        if not Path(info.installer_path).exists():
            messagebox.showerror(
                "Actualizaciones",
                "No se encontro el instalador publicado.\n\n"
                f"Ruta esperada:\n{info.installer_path}",
            )
            return

        confirm = messagebox.askyesno(
            "Actualizar PlayOps Suite",
            "La aplicacion se cerrara para instalar la nueva version.\n\n"
            f"Version instalada: {info.current_version}\n"
            f"Version nueva: {info.latest_version}\n\n"
            "El actualizador abrira la app al terminar.\n\n"
            "Desea continuar?",
        )
        if not confirm:
            return

        try:
            launch_update(info.installer_path)
        except Exception as error:
            messagebox.showerror("Actualizaciones", f"No se pudo iniciar el actualizador:\n\n{error}")
            return

        self.winfo_toplevel().after(300, self.winfo_toplevel().destroy)

    def _open_path(self, path):
        try:
            path.mkdir(parents=True, exist_ok=True)
            os.startfile(str(path))
        except Exception as error:
            messagebox.showerror("Acerca de", f"No se pudo abrir la ruta:\n\n{error}")
