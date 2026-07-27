import calendar
import getpass
import os
import re
import socket
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import date, datetime
from pathlib import Path

from app_procesos.config import LISTO_OUTPUT_DIR, REPORTS_DIR
from app_procesos.modules.cargue_rutas import service

from .theme import COLORS, FONT_BODY, FONT_BODY_BOLD, FONT_H2
from .widgets import RoundedButton, RoundedSelect


class CargueRutasView(tk.Frame):
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
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self.archivo_cliente = tk.StringVar(value="Sin archivo del cliente")
        self.archivo_soporte = tk.StringVar(value="Plantilla interna incluida")
        self.status = tk.StringVar(value="Cargue pendiente. Seleccione el archivo del cliente para continuar.")
        self.responsable = tk.StringVar(value="")
        self.responsable_correo = tk.StringVar(value="")
        self.nombre_bd = tk.StringVar(value="")
        self.tipo_cargue = tk.StringVar(value="Produccion")
        self.header_row = tk.StringVar(value="1")
        self.data_start_row = tk.StringVar(value="3")
        self.interes_default = tk.StringVar(value="20")
        self.dias_credito_default = tk.StringVar(value="30")
        self.fecha_prox_mode = tk.StringVar(value="Calcular")
        self.fecha_prox_manual = tk.StringVar(value="")
        self.fecha_prox_global = tk.StringVar(value="")
        self.periodicidad_default = tk.StringVar(value="Usar archivo")
        self.advanced_open = False
        self.audit_open = False
        self.csv_preview_open = False
        self.uploads_frame = None
        self.cliente_card = None
        self.soporte_card = None
        self.cards_stacked = None
        self.analysis_frame = None
        self.mapping_frame = None
        self.sample_frame = None
        self.corrections_frame = None
        self.mapping_vars = {}
        self.correction_vars = {}
        self.preview_edit_vars = {}
        self.preview_original_values = {}
        self.manual_preview_corrections = {}
        self.csv_preview_body = None
        self.csv_preview_toggle_button = None
        self.csv_preview_payload = None
        self.csv_preview_animating = False
        self.duplicate_vars = {}
        self.date_override_vars = {}
        self._calendar_popup = None
        self._calendar_outside_bind = None
        self._calendar_outside_bind_id = None
        self.warning_detail_frame = None
        self.warning_button = None
        self.warning_open = False
        self.warning_count = 0
        self.current_columns = []
        self._build()
        self.bind("<Configure>", self._on_resize)

    def _build(self):
        root = self.content_frame
        tk.Label(
            root,
            text="Cargue de rutas",
            bg=COLORS["bg"],
            fg=COLORS["text"],
            font=("Segoe UI", 22, "bold"),
        ).pack(anchor="w")
        tk.Label(
            root,
            text="Cargue el archivo del cliente. La plantilla soporte interna ya viene incluida en la aplicacion.",
            bg=COLORS["bg"],
            fg=COLORS["muted"],
            font=FONT_BODY,
        ).pack(anchor="w", pady=(6, 22))

        self.uploads_frame = tk.Frame(root, bg=COLORS["bg"])
        self.uploads_frame.pack(fill="x")

        self.cliente_card = self._upload_card(
            self.uploads_frame,
            title="Archivo del cliente",
            description="Excel recibido del cliente con documentos, saldos, creditos, telefonos y abonos si aplica.",
            path_var=self.archivo_cliente,
            command=self.select_cliente,
            button_text="Seleccionar archivo cliente",
            primary=True,
        )

        self.soporte_card = self._info_card(
            self.uploads_frame,
            title="Plantilla soporte interna",
            description="La app usa automaticamente formatoArchivoCreditosbase.xls. No es necesario cargarla cada vez.",
            text_var=self.archivo_soporte,
        )
        self._layout_upload_cards(stacked=False)

        actions = tk.Frame(root, bg=COLORS["panel"], padx=22, pady=18)
        actions.pack(fill="x", pady=(18, 0))
        header_row = tk.Frame(actions, bg=COLORS["panel"])
        header_row.pack(fill="x")
        tk.Label(
            header_row,
            text="Preparacion",
            bg=COLORS["panel"],
            fg=COLORS["text"],
            font=FONT_H2,
        ).pack(anchor="w")
        tk.Label(
            actions,
            textvariable=self.status,
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=FONT_BODY,
            wraplength=820,
            justify="left",
        ).pack(anchor="w", pady=(8, 16))

        action_row = tk.Frame(actions, bg=COLORS["panel"])
        action_row.pack(fill="x")
        self._button(
            action_row,
            "Procesar cargue",
            self.process_files,
            primary=True,
            width=178,
            height=42,
        ).pack(side="left", padx=(0, 12))
        self._button(
            action_row,
            "Validar datos",
            self.validate_data,
            width=142,
            height=42,
        ).pack(side="left", padx=(0, 12))
        self._button(
            action_row,
            "Limpiar seleccion",
            self.clear_selection,
            width=158,
            height=42,
        ).pack(side="left", padx=(0, 12))
        self.advanced_button = self._button(
            action_row,
            "Avanzado",
            self.toggle_advanced,
            width=164,
            height=42,
        )
        self.advanced_button.pack(side="left", padx=(0, 12))
        self.audit_button = self._button(
            action_row,
            "Datos del cargue",
            self.toggle_audit_panel,
            width=168,
            height=42,
        )
        self.audit_button.pack(side="left")

        self.audit_frame = tk.Frame(actions, bg=COLORS["panel"])
        utility_row = tk.Frame(self.audit_frame, bg=COLORS["panel"])
        utility_row.pack(fill="x", pady=(14, 0))
        self._wide_text_input(
            utility_row,
            "Nombre responsable",
            self.responsable,
            width=24,
        ).pack(side="left", padx=(0, 12))
        self._wide_text_input(
            utility_row,
            "Correo responsable",
            self.responsable_correo,
            width=28,
        ).pack(side="left", padx=(0, 12))
        self._button(
            utility_row,
            "Abrir carpeta C:\\Listo",
            self.open_listo_folder,
            width=178,
            height=38,
        ).pack(side="left", padx=(0, 12))
        self._button(
            utility_row,
            "Abrir ultima bitacora",
            self.open_latest_logbook,
            width=178,
            height=38,
        ).pack(side="left")

        audit_row = tk.Frame(self.audit_frame, bg=COLORS["panel"])
        audit_row.pack(fill="x", pady=(12, 0))
        self._wide_text_input(
            audit_row,
            "Nombre de BD",
            self.nombre_bd,
            width=24,
        ).pack(side="left", padx=(0, 12))
        self._tipo_cargue_input(audit_row).pack(side="left", padx=(0, 12))
        self._button(
            audit_row,
            "Eliminar prueba",
            self.delete_test_load,
            width=158,
            height=38,
        ).pack(side="left")

        self.advanced_frame = tk.Frame(actions, bg=COLORS["panel"])
        row_config = tk.Frame(self.advanced_frame, bg=COLORS["panel"])
        row_config.pack(fill="x")
        self._row_input(row_config, "Fila encabezados", self.header_row).pack(side="left", padx=(0, 12))
        self._row_input(row_config, "Fila inicial clientes", self.data_start_row).pack(side="left", padx=(0, 12))
        self._periodicidad_input(row_config).pack(side="left", padx=(0, 12))
        self._button(row_config, "Reanalizar archivo", self.analyze_cliente, width=156, height=40).pack(side="left")

        params_row = tk.Frame(self.advanced_frame, bg=COLORS["panel"])
        params_row.pack(fill="x", pady=(16, 0))
        self._row_input(params_row, "Interes por defecto", self.interes_default).pack(side="left", padx=(0, 12))
        self._row_input(params_row, "Dias credito si falta", self.dias_credito_default).pack(side="left", padx=(0, 12))
        self._fecha_prox_input(params_row).pack(side="left", padx=(0, 12))
        self._wide_text_input(params_row, "Fecha prox. manual", self.fecha_prox_manual).pack(side="left", padx=(0, 12))

        self.analysis_frame = tk.Frame(root, bg=COLORS["panel"], padx=20, pady=18)
        self.analysis_frame.pack(fill="both", expand=True, pady=(18, 0))
        tk.Label(
            self.analysis_frame,
            text="Analisis del archivo del cliente",
            bg=COLORS["panel"],
            fg=COLORS["text"],
            font=FONT_H2,
        ).pack(anchor="w")
        tk.Label(
            self.analysis_frame,
            text="Cuando seleccione el archivo del cliente, aqui apareceran las columnas detectadas y el mapeo sugerido.",
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=FONT_BODY,
            wraplength=900,
            justify="left",
        ).pack(anchor="w", pady=(8, 14))

        self.mapping_frame = tk.Frame(self.analysis_frame, bg=COLORS["panel"])
        self.mapping_frame.pack(fill="x")
        self.sample_frame = tk.Frame(self.analysis_frame, bg=COLORS["panel"])
        self.sample_frame.pack(fill="both", expand=True, pady=(16, 0))
        self.corrections_frame = tk.Frame(self.analysis_frame, bg=COLORS["panel"])
        self.corrections_frame.pack(fill="both", expand=True, pady=(18, 0))

    def _update_scroll_region(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _resize_canvas_window(self, event):
        self.canvas.itemconfigure(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        widget = self.winfo_containing(event.x_root, event.y_root)
        if not self._is_child_widget(widget):
            return
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _is_child_widget(self, widget):
        while widget is not None:
            if widget is self:
                return True
            widget = getattr(widget, "master", None)
        return False

    def _upload_card(self, parent, title, description, path_var, command, button_text, primary=False):
        card = tk.Frame(parent, bg=COLORS["panel"], padx=18, pady=18)
        tk.Frame(card, bg=COLORS["accent"] if primary else COLORS["line"], height=3).pack(fill="x", pady=(0, 16))
        tk.Label(card, text=title, bg=COLORS["panel"], fg=COLORS["text"], font=FONT_H2).pack(anchor="w")
        tk.Label(
            card,
            text=description,
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=FONT_BODY,
            wraplength=360,
            justify="left",
        ).pack(anchor="w", pady=(8, 14))

        path_box = tk.Frame(card, bg=COLORS["panel_2"], padx=12, pady=10)
        path_box.pack(fill="x", pady=(0, 14))
        tk.Label(
            path_box,
            textvariable=path_var,
            bg=COLORS["panel_2"],
            fg=COLORS["text"],
            font=("Segoe UI", 9),
            wraplength=340,
            justify="left",
        ).pack(side="left", fill="x", expand=True, anchor="w")

        self._button(
            path_box,
            "Subir archivo",
            command,
            primary=primary,
            width=142,
            height=38,
        ).pack(side="right", padx=(14, 0))
        return card

    def _info_card(self, parent, title, description, text_var):
        card = tk.Frame(parent, bg=COLORS["panel"], padx=18, pady=18)
        tk.Frame(card, bg=COLORS["line"], height=3).pack(fill="x", pady=(0, 16))
        tk.Label(card, text=title, bg=COLORS["panel"], fg=COLORS["text"], font=FONT_H2).pack(anchor="w")
        tk.Label(
            card,
            text=description,
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=FONT_BODY,
            wraplength=360,
            justify="left",
        ).pack(anchor="w", pady=(8, 14))
        path_box = tk.Frame(card, bg=COLORS["panel_2"], padx=12, pady=10)
        path_box.pack(fill="x")
        tk.Label(
            path_box,
            textvariable=text_var,
            bg=COLORS["panel_2"],
            fg=COLORS["text"],
            font=("Segoe UI", 9, "bold"),
            wraplength=340,
            justify="left",
        ).pack(anchor="w")
        return card

    def _on_resize(self, _event):
        width = self.winfo_width()
        if width <= 0:
            return
        self._layout_upload_cards(stacked=width < 860)

    def _layout_upload_cards(self, stacked):
        if self.cards_stacked == stacked or not self.cliente_card or not self.soporte_card:
            return

        self.cards_stacked = stacked
        self.cliente_card.pack_forget()
        self.soporte_card.pack_forget()

        if stacked:
            self.cliente_card.pack(fill="x", pady=(0, 12))
            self.soporte_card.pack(fill="x")
            return

        self.cliente_card.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.soporte_card.pack(side="left", fill="both", expand=True, padx=(10, 0))

    def _button(self, parent, text, command, primary=False, width=None, height=42):
        return RoundedButton(
            parent,
            text,
            command,
            bg=COLORS["accent"] if primary else COLORS["panel_2"],
            fg="white" if primary else COLORS["text"],
            hover_bg=COLORS["accent_hover"] if primary else COLORS["panel_3"],
            active_bg=COLORS["accent_active"] if primary else COLORS["panel_3"],
            disabled_bg=COLORS["disabled"],
            disabled_fg=COLORS["muted"],
            radius=16,
            height=height,
            width=width,
            font=FONT_BODY_BOLD if primary else FONT_BODY,
        )

    def _row_input(self, parent, label, variable):
        box = tk.Frame(parent, bg=COLORS["panel"])
        tk.Label(
            box,
            text=label,
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w", pady=(0, 4))
        entry = tk.Entry(
            box,
            textvariable=variable,
            width=8,
            bg=COLORS["panel_2"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            font=FONT_BODY_BOLD,
            justify="center",
        )
        entry.pack(ipady=9)
        return box

    def _periodicidad_input(self, parent):
        box = tk.Frame(parent, bg=COLORS["panel"])
        tk.Label(
            box,
            text="Periodicidad del cargue",
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w", pady=(0, 4))
        combo = RoundedSelect(
            box,
            variable=self.periodicidad_default,
            values=[
                "Usar archivo",
                "Todos: 1 - Diario",
                "Todos: 2 - Semanal",
                "Todos: 3 - Quincenal",
                "Todos: 4 - Mensual",
            ],
            bg=COLORS["panel_2"],
            fg=COLORS["text"],
            hover_bg=COLORS["panel_3"],
            active_bg=COLORS["accent_active"],
            width=188,
            height=40,
            radius=15,
            font=("Segoe UI", 9),
        )
        combo.pack()
        return box

    def _fecha_prox_input(self, parent):
        box = tk.Frame(parent, bg=COLORS["panel"])
        tk.Label(
            box,
            text="Fecha proximo pago",
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w", pady=(0, 4))
        combo = RoundedSelect(
            box,
            variable=self.fecha_prox_mode,
            values=[
                "Calcular",
                "Usar archivo",
                "Manual",
                "Vacia",
            ],
            bg=COLORS["panel_2"],
            fg=COLORS["text"],
            hover_bg=COLORS["panel_3"],
            active_bg=COLORS["accent_active"],
            width=130,
            height=40,
            radius=15,
            font=("Segoe UI", 9),
        )
        combo.pack()
        return box

    def _tipo_cargue_input(self, parent):
        box = tk.Frame(parent, bg=COLORS["panel"])
        tk.Label(
            box,
            text="Tipo de cargue",
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w", pady=(0, 4))
        combo = RoundedSelect(
            box,
            variable=self.tipo_cargue,
            values=["Produccion", "Prueba"],
            bg=COLORS["panel_2"],
            fg=COLORS["text"],
            hover_bg=COLORS["panel_3"],
            active_bg=COLORS["accent_active"],
            width=138,
            height=38,
            radius=15,
            font=("Segoe UI", 9),
        )
        combo.pack()
        return box

    def _wide_text_input(self, parent, label, variable, width=18):
        box = tk.Frame(parent, bg=COLORS["panel"])
        tk.Label(
            box,
            text=label,
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w", pady=(0, 4))
        entry = tk.Entry(
            box,
            textvariable=variable,
            width=width,
            bg=COLORS["panel_2"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            font=FONT_BODY,
            justify="center",
        )
        entry.pack(ipady=9)
        return box

    def select_cliente(self):
        path = filedialog.askopenfilename(
            title="Seleccionar archivo enviado por el cliente",
            filetypes=[
                ("Excel cliente", "*.xlsx *.xlsm *.csv"),
                ("Todos los archivos", "*.*"),
            ],
        )
        if path:
            suffix = Path(path).suffix.lower()
            if suffix == ".xls":
                messagebox.showwarning(
                    "Cargue de rutas",
                    "Ese archivo es .xls antiguo. Si es la plantilla soporte, carguelo en el panel derecho. "
                    "Si de verdad es el archivo del cliente, primero guardelo como .xlsx.",
                )
                return
            self.archivo_cliente.set(path)
            self.header_row.set("1")
            self.data_start_row.set("3")
            self.mapping_vars = {}
            self.correction_vars = {}
            self.duplicate_vars = {}
            self.date_override_vars = {}
            self._update_status()
            self.analyze_cliente()

    def select_soporte(self):
        path = filedialog.askopenfilename(
            title="Seleccionar archivo soporte interno",
            filetypes=[
                ("Excel soporte", "*.xlsx *.xls *.xlsm"),
                ("Todos los archivos", "*.*"),
            ],
        )
        if path:
            self.archivo_soporte.set(path)
            self._update_status()

    def _update_status(self):
        if self._has_cliente():
            self.status.set("Archivo del cliente cargado. Puede iniciar el procesamiento del cargue.")
        else:
            self.status.set("Cargue pendiente. Seleccione el archivo del cliente para continuar.")

    def _has_cliente(self):
        return self.archivo_cliente.get() != "Sin archivo del cliente"

    def _has_soporte(self):
        return True

    def _default_responsable(self):
        hostname = socket.gethostname().strip()
        if hostname:
            return hostname
        user = os.environ.get("USERNAME") or getpass.getuser()
        domain = os.environ.get("USERDOMAIN")
        return f"{domain}\\{user}" if domain and domain.upper() != user.upper() else user

    def _windows_user(self):
        user = os.environ.get("USERNAME") or getpass.getuser()
        domain = os.environ.get("USERDOMAIN")
        return f"{domain}\\{user}" if domain and domain.upper() != user.upper() else user

    def _local_ip(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.connect(("8.8.8.8", 80))
                return sock.getsockname()[0]
        except OSError:
            try:
                return socket.gethostbyname(socket.gethostname())
            except OSError:
                return "No detectada"

    def _audit_info(self):
        return {
            "responsable_nombre": self.responsable.get().strip(),
            "responsable_correo": self.responsable_correo.get().strip(),
            "nombre_bd": self.nombre_bd.get().strip(),
            "tipo_cargue": self.tipo_cargue.get().strip() or "Produccion",
            "hostname": socket.gethostname().strip() or "No detectado",
            "ip": self._local_ip(),
            "usuario_windows": self._windows_user(),
        }

    def export_state(self):
        return {
            "archivo_cliente": self.archivo_cliente.get(),
            "archivo_soporte": self.archivo_soporte.get(),
            "status": self.status.get(),
            "responsable": self.responsable.get(),
            "responsable_correo": self.responsable_correo.get(),
            "nombre_bd": self.nombre_bd.get(),
            "tipo_cargue": self.tipo_cargue.get(),
            "header_row": self.header_row.get(),
            "data_start_row": self.data_start_row.get(),
            "interes_default": self.interes_default.get(),
            "dias_credito_default": self.dias_credito_default.get(),
            "fecha_prox_mode": self.fecha_prox_mode.get(),
            "fecha_prox_manual": self.fecha_prox_manual.get(),
            "fecha_prox_global": self.fecha_prox_global.get(),
            "periodicidad_default": self.periodicidad_default.get(),
            "advanced_open": self.advanced_open,
            "csv_preview_open": self.csv_preview_open,
            "mapping": {
                campo: variable.get()
                for campo, variable in self.mapping_vars.items()
            },
            "corrections": {
                fila: {
                    campo: variable.get()
                    for campo, variable in campos.items()
                }
                for fila, campos in self.correction_vars.items()
            },
            "manual_preview_corrections": self.manual_preview_corrections,
            "duplicates": {
                documento: variable.get()
                for documento, variable in self.duplicate_vars.items()
            },
            "date_overrides": {
                fila: variable.get()
                for fila, variable in self.date_override_vars.items()
            },
            "had_analysis": bool(self.mapping_vars),
            "had_validation": bool(self.correction_vars or self.duplicate_vars or self.date_override_vars),
        }

    def restore_state(self, state):
        if not state:
            return
        self.archivo_cliente.set(state.get("archivo_cliente", "Sin archivo del cliente"))
        self.archivo_soporte.set(state.get("archivo_soporte", "Plantilla interna incluida"))
        self.status.set(state.get("status", self.status.get()))
        self.responsable.set(state.get("responsable", self.responsable.get()))
        self.responsable_correo.set(state.get("responsable_correo", self.responsable_correo.get()))
        self.nombre_bd.set(state.get("nombre_bd", self.nombre_bd.get()))
        self.tipo_cargue.set(state.get("tipo_cargue", self.tipo_cargue.get()))
        self.header_row.set(state.get("header_row", "1"))
        self.data_start_row.set(state.get("data_start_row", "3"))
        self.interes_default.set(state.get("interes_default", "20"))
        self.dias_credito_default.set(state.get("dias_credito_default", "30"))
        self.fecha_prox_mode.set(state.get("fecha_prox_mode", "Calcular"))
        self.fecha_prox_manual.set(state.get("fecha_prox_manual", ""))
        self.fecha_prox_global.set(state.get("fecha_prox_global", ""))
        self.periodicidad_default.set(state.get("periodicidad_default", "Usar archivo"))

        if state.get("advanced_open"):
            self.toggle_advanced()
        self.csv_preview_open = bool(state.get("csv_preview_open", self.csv_preview_open))

        if self._has_cliente() and state.get("had_analysis"):
            try:
                self.analyze_cliente()
                self._restore_mapping_state(state.get("mapping", {}))
                self.manual_preview_corrections = state.get("manual_preview_corrections", {})
                if state.get("had_validation"):
                    self.validate_data()
                    self._restore_correction_state(state.get("corrections", {}))
                    self._restore_duplicate_state(state.get("duplicates", {}))
                    self._restore_date_override_state(state.get("date_overrides", {}))
                self.status.set(state.get("status", self.status.get()))
            except Exception as error:
                self.status.set(f"No se pudo restaurar el cargue despues de cambiar tema: {error}")

    def _restore_mapping_state(self, mapping):
        for campo, value in mapping.items():
            variable = self.mapping_vars.get(campo)
            if variable is not None:
                variable.set(value)

    def _restore_correction_state(self, corrections):
        for fila, campos in corrections.items():
            variables = self.correction_vars.get(int(fila)) or self.correction_vars.get(fila)
            if not variables:
                continue
            for campo, value in campos.items():
                variable = variables.get(campo)
                if variable is not None:
                    variable.set(value)

    def _restore_duplicate_state(self, duplicates):
        for documento, value in duplicates.items():
            variable = self.duplicate_vars.get(documento)
            if variable is not None:
                variable.set(value)

    def _restore_date_override_state(self, date_overrides):
        for fila, value in date_overrides.items():
            variable = self.date_override_vars.get(int(fila)) or self.date_override_vars.get(fila)
            if variable is not None:
                variable.set(value)

    def clear_selection(self):
        self.archivo_cliente.set("Sin archivo del cliente")
        self.archivo_soporte.set("Plantilla interna incluida")
        self.responsable.set("")
        self.responsable_correo.set("")
        self.nombre_bd.set("")
        self.tipo_cargue.set("Produccion")
        self.header_row.set("1")
        self.data_start_row.set("3")
        self.interes_default.set("20")
        self.dias_credito_default.set("30")
        self.fecha_prox_mode.set("Calcular")
        self.fecha_prox_manual.set("")
        self.fecha_prox_global.set("")
        self.periodicidad_default.set("Usar archivo")
        self.csv_preview_open = False
        self.mapping_vars = {}
        self.correction_vars = {}
        self.preview_edit_vars = {}
        self.preview_original_values = {}
        self.manual_preview_corrections = {}
        self.duplicate_vars = {}
        self.date_override_vars = {}
        self.current_columns = []
        self._clear_analysis()
        self._update_status()

    def open_listo_folder(self):
        try:
            LISTO_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            os.startfile(str(LISTO_OUTPUT_DIR))
        except Exception as error:
            messagebox.showerror("Cargue de rutas", f"No se pudo abrir la carpeta C:\\Listo: {error}")

    def open_latest_logbook(self):
        folder = REPORTS_DIR / "cargue_rutas"
        try:
            files = sorted(folder.glob("bitacora_cargue_*.txt"), key=lambda path: path.stat().st_mtime, reverse=True)
        except Exception as error:
            messagebox.showerror("Cargue de rutas", f"No se pudo buscar la bitacora: {error}")
            return
        if not files:
            messagebox.showinfo(
                "Cargue de rutas",
                "Aun no hay bitacoras. Genere un cargue primero para crear la bitacora.",
            )
            return
        try:
            os.startfile(str(files[0]))
        except Exception as error:
            messagebox.showerror("Cargue de rutas", f"No se pudo abrir la bitacora: {error}")

    def delete_test_load(self):
        registros, mensaje = service.listar_cargues_prueba_central()
        if mensaje:
            messagebox.showwarning("Eliminar prueba", mensaje)
            return
        if not registros:
            messagebox.showinfo(
                "Eliminar prueba",
                "No hay cargues marcados como Prueba en la bitacora central.",
            )
            return
        self._open_delete_test_modal(registros)

    def _open_delete_test_modal(self, registros):
        modal = tk.Toplevel(self)
        modal.title("Eliminar cargue de prueba")
        modal.configure(bg=COLORS["panel"])
        modal.transient(self.winfo_toplevel())
        modal.grab_set()
        modal.resizable(False, False)

        container = tk.Frame(modal, bg=COLORS["panel"], padx=22, pady=18)
        container.pack(fill="both", expand=True)
        tk.Label(
            container,
            text="Eliminar cargue de prueba",
            bg=COLORS["panel"],
            fg=COLORS["text"],
            font=FONT_H2,
        ).pack(anchor="w")
        tk.Label(
            container,
            text=(
                "Puede eliminar una prueba seleccionada o borrar todas las pruebas registradas. "
                "Esto no borra archivos CSV ni archivos locales de LISTO."
            ),
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=FONT_BODY,
            wraplength=760,
            justify="left",
        ).pack(anchor="w", pady=(6, 14))

        header = tk.Frame(container, bg=COLORS["panel_3"], padx=12, pady=8)
        header.pack(fill="x", pady=(0, 2))
        for column, (text, weight) in enumerate(
            (("Fecha y hora", 2), ("Nombre de BD", 2), ("Responsable", 2), ("Archivo", 3))
        ):
            header.columnconfigure(column, weight=weight)
            tk.Label(
                header,
                text=text,
                bg=COLORS["panel_3"],
                fg=COLORS["accent_2"],
                font=("Segoe UI", 9, "bold"),
                anchor="w",
            ).grid(row=0, column=column, sticky="ew", padx=(0, 10))

        list_frame = tk.Frame(container, bg=COLORS["panel_2"], padx=10, pady=10)
        list_frame.pack(fill="both", expand=True)
        listbox = tk.Listbox(
            list_frame,
            height=min(10, max(4, len(registros))),
            width=112,
            bg=COLORS["console"],
            fg=COLORS["text"],
            selectbackground=COLORS["accent"],
            selectforeground="#ffffff",
            activestyle="none",
            relief="flat",
            borderwidth=0,
            highlightthickness=1,
            highlightbackground=COLORS["line"],
            highlightcolor=COLORS["accent"],
            font=("Consolas", 9),
        )
        scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=listbox.yview)
        listbox.configure(yscrollcommand=scrollbar.set)
        listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        for registro in registros:
            listbox.insert("end", self._format_test_load_row(registro))
        listbox.selection_set(0)

        selected = tk.StringVar(value=self._format_test_load_detail(registros[0]))
        tk.Label(
            container,
            textvariable=selected,
            bg=COLORS["panel_2"],
            fg=COLORS["text"],
            font=FONT_BODY,
            anchor="w",
            justify="left",
            padx=12,
            pady=9,
            wraplength=760,
        ).pack(fill="x", pady=(10, 0))

        def update_selected(_event=None):
            selection = listbox.curselection()
            if selection:
                selected.set(self._format_test_load_detail(registros[selection[0]]))

        listbox.bind("<<ListboxSelect>>", update_selected)
        listbox.bind("<Double-Button-1>", lambda _event: self._delete_selected_test_load(modal, listbox, registros))
        listbox.focus_set()

        buttons = tk.Frame(container, bg=COLORS["panel"])
        buttons.pack(fill="x", pady=(16, 0))
        buttons.columnconfigure(0, weight=1)
        RoundedButton(
            buttons,
            "Eliminar todas",
            lambda: self._delete_all_test_loads(modal, registros),
            bg="#7a2630",
            hover="#9d303c",
            width=180,
            height=42,
            radius=10,
        ).grid(row=0, column=0, sticky="w")
        RoundedButton(
            buttons,
            "Cancelar",
            modal.destroy,
            bg=COLORS["panel_2"],
            hover=COLORS["panel_3"],
            width=160,
            height=42,
            radius=10,
        ).grid(row=0, column=1, padx=(0, 10))
        RoundedButton(
            buttons,
            "Eliminar seleccionado",
            lambda: self._delete_selected_test_load(modal, listbox, registros),
            bg="#d94a4a",
            hover="#b93636",
            width=210,
            height=42,
            radius=10,
        ).grid(row=0, column=2)

        modal.update_idletasks()
        parent = self.winfo_toplevel()
        x = parent.winfo_rootx() + (parent.winfo_width() - modal.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - modal.winfo_height()) // 2
        modal.geometry(f"+{max(20, x)}+{max(20, y)}")

    def _delete_selected_test_load(self, modal, listbox, registros):
        selection = listbox.curselection()
        if not selection:
            messagebox.showwarning("Eliminar prueba", "Seleccione un cargue de prueba para eliminar.")
            return
        registro = registros[selection[0]]
        resumen = self._format_test_load_row(registro)
        confirm = messagebox.askyesno(
            "Eliminar prueba",
            "Se eliminara este registro de prueba del historico central:\n\n"
            f"{resumen}\n\nDesea continuar?",
            parent=modal,
        )
        if not confirm:
            return
        eliminado, mensaje = service.eliminar_cargue_prueba_por_id(registro.get("id_cargue"))
        if eliminado:
            messagebox.showinfo("Eliminar prueba", mensaje, parent=modal)
            modal.destroy()
        else:
            messagebox.showwarning("Eliminar prueba", mensaje, parent=modal)

    def _delete_all_test_loads(self, modal, registros):
        total = len(registros)
        confirm = messagebox.askyesno(
            "Eliminar todas las pruebas",
            "Esta accion eliminara TODOS los cargues marcados como Prueba en la bitacora central.\n\n"
            f"Total a eliminar: {total}\n\n"
            "No se borraran archivos CSV ni archivos locales de LISTO.\n\n"
            "Desea continuar?",
            parent=modal,
        )
        if not confirm:
            return
        eliminado, mensaje = service.eliminar_cargues_prueba_por_ids(
            [registro.get("id_cargue") for registro in registros]
        )
        if eliminado:
            messagebox.showinfo("Eliminar todas las pruebas", mensaje, parent=modal)
            modal.destroy()
        else:
            messagebox.showwarning("Eliminar todas las pruebas", mensaje, parent=modal)

    def _format_test_load_row(self, registro):
        fecha = registro.get("fecha") or "sin fecha"
        hora = registro.get("hora") or "sin hora"
        bd = registro.get("nombre_bd") or "sin BD"
        responsable = registro.get("responsable") or "sin responsable"
        archivo = Path(str(registro.get("archivo_cliente") or "sin archivo")).name
        return f"{fecha} {hora} | BD: {bd} | {responsable} | {archivo}"

    def _format_test_load_detail(self, registro):
        fecha = registro.get("fecha") or "sin fecha"
        hora = registro.get("hora") or "sin hora"
        bd = registro.get("nombre_bd") or "sin BD"
        responsable = registro.get("responsable") or "sin responsable"
        archivo = Path(str(registro.get("archivo_cliente") or "sin archivo")).name
        return f"Seleccionado: {fecha} {hora} | Nombre de BD: {bd} | Responsable: {responsable} | Archivo: {archivo}"

    def analyze_cliente(self):
        if not self._has_cliente():
            messagebox.showwarning("Cargue de rutas", "Seleccione primero el archivo del cliente.")
            return
        try:
            header_row, data_start_row = self._get_row_config()
            usar_deteccion = self.header_row.get() == "1" and self.data_start_row.get() == "3"
            if usar_deteccion:
                detectado = service.detectar_estructura_archivo_cliente(Path(self.archivo_cliente.get()))
                if detectado:
                    header_row = detectado["header_row"]
                    data_start_row = detectado["data_start_row"]
                    self.header_row.set(str(header_row))
                    self.data_start_row.set(str(data_start_row))
            preview, mapeo = service.analizar_archivo_cliente(
                Path(self.archivo_cliente.get()),
                header_row=header_row,
                data_start_row=data_start_row,
            )
        except Exception as error:
            self.status.set(f"No se pudo analizar el archivo del cliente: {error}")
            messagebox.showerror("Cargue de rutas", str(error))
            return

        self._render_analysis(preview, mapeo, header_row, data_start_row)
        pendientes = [item.campo.nombre for item in mapeo if item.campo.requerido and not item.columna_origen]
        if pendientes:
            self.status.set(
                "Archivo cliente analizado. Revise el mapeo de columnas abajo. "
                "Faltan campos requeridos por mapear: "
                + ", ".join(pendientes)
            )
        else:
            self.status.set(
                "Archivo cliente analizado. Revise el mapeo de columnas abajo; "
                "si todo esta bien, procese el cargue."
            )

    def _clear_analysis(self):
        for frame in (self.mapping_frame, self.sample_frame, self.corrections_frame):
            if frame:
                for child in frame.winfo_children():
                    child.destroy()

    def _render_analysis(self, preview, mapeo, header_row, data_start_row):
        self._clear_analysis()
        self.mapping_vars = {}
        self.current_columns = list(preview.columnas)

        info = tk.Frame(self.mapping_frame, bg=COLORS["panel_2"], padx=14, pady=12)
        info.pack(fill="x", pady=(0, 12))
        tk.Label(
            info,
            text=(
                f"Hoja: {preview.hoja}  |  Encabezados: fila {header_row}  |  "
                f"Clientes desde: fila {data_start_row}  |  "
                f"Columnas: {len(preview.columnas)}  |  Muestra: {preview.total_filas_muestra} filas"
            ),
            bg=COLORS["panel_2"],
            fg=COLORS["text"],
            font=FONT_BODY_BOLD,
        ).pack(anchor="w")

        help_box = tk.Frame(self.mapping_frame, bg=COLORS["panel_2"], padx=14, pady=12)
        help_box.pack(fill="x", pady=(0, 12))
        tk.Label(
            help_box,
            text=(
                "Revise el mapeo antes de procesar: a la izquierda esta el campo que necesita "
                "la app y en el selector esta la columna detectada en el Excel del cliente. "
                "Si una columna quedo mal, cambiela en el selector. Los campos con * son obligatorios."
            ),
            bg=COLORS["panel_2"],
            fg=COLORS["muted"],
            font=FONT_BODY,
            wraplength=1100,
            justify="left",
        ).pack(anchor="w")

        grid = tk.Frame(self.mapping_frame, bg=COLORS["panel"])
        grid.pack(fill="x")
        headers = ["Campo interno", "Columna del cliente", "Confianza"]
        for column, text in enumerate(headers):
            tk.Label(
                grid,
                text=text,
                bg=COLORS["panel"],
                fg=COLORS["accent_2"],
                font=("Segoe UI", 9, "bold"),
                anchor="w",
            ).grid(row=0, column=column, sticky="ew", padx=(0, 12), pady=(0, 6))

        grid.columnconfigure(0, weight=2)
        grid.columnconfigure(1, weight=3)
        grid.columnconfigure(2, weight=1)

        for row, item in enumerate(mapeo, start=1):
            required = " *" if item.campo.requerido else ""
            color = COLORS["text"] if item.columna_origen else "#ffcf70"
            tk.Label(
                grid,
                text=f"{item.campo.nombre}{required}",
                bg=COLORS["panel"],
                fg=COLORS["text"],
                font=FONT_BODY,
                anchor="w",
            ).grid(row=row, column=0, sticky="ew", padx=(0, 12), pady=3)

            selected = item.columna_origen or "Sin mapear"
            variable = tk.StringVar(value=selected)
            self.mapping_vars[item.campo.codigo] = variable
            combo = RoundedSelect(
                grid,
                variable,
                ["Sin mapear", *preview.columnas],
                bg=COLORS["panel_2"],
                fg=COLORS["text"],
                hover_bg=COLORS["panel_3"],
                active_bg=COLORS["accent_active"],
                radius=12,
                height=30,
                font=("Segoe UI", 9),
            )
            combo.grid(row=row, column=1, sticky="ew", padx=(0, 12), pady=3)

            tk.Label(
                grid,
                text=f"{item.confianza}%" if item.columna_origen else "-",
                bg=COLORS["panel"],
                fg=color,
                font=FONT_BODY,
                anchor="w",
            ).grid(row=row, column=2, sticky="ew", padx=(0, 12), pady=3)

        self._render_sample(preview)
        self._render_corrections_empty()

    def _render_sample(self, preview):
        tk.Label(
            self.sample_frame,
            text="Vista rapida de columnas",
            bg=COLORS["panel"],
            fg=COLORS["text"],
            font=FONT_H2,
        ).pack(anchor="w", pady=(0, 8))

        columns_text = ", ".join(preview.columnas[:12])
        if len(preview.columnas) > 12:
            columns_text += f" ... +{len(preview.columnas) - 12} columnas"
        tk.Label(
            self.sample_frame,
            text=columns_text or "Sin columnas detectadas",
            bg=COLORS["panel_2"],
            fg=COLORS["muted"],
            font=FONT_BODY,
            wraplength=900,
            justify="left",
            padx=12,
            pady=10,
        ).pack(fill="x")

    def validate_data(self):
        if not self._has_cliente():
            messagebox.showwarning("Cargue de rutas", "Seleccione primero el archivo del cliente.")
            return
        try:
            preview, _mapeo, normalizacion = self._build_validacion()
        except Exception as error:
            self.status.set(f"No se pudo validar el cargue: {error}")
            messagebox.showerror("Cargue de rutas", str(error))
            return

        self._render_corrections(normalizacion)
        if normalizacion.total_con_error:
            self.status.set(
                f"Validacion lista. Hay {normalizacion.total_con_error} fila(s) para revisar/corregir antes de generar."
            )
        else:
            self.status.set(
                f"Validacion lista. {normalizacion.total_registros} registro(s) sin diferencias bloqueantes."
            )

    def _render_corrections_empty(self):
        if not self.corrections_frame:
            return
        for child in self.corrections_frame.winfo_children():
            child.destroy()
        tk.Label(
            self.corrections_frame,
            text="Correcciones antes de generar",
            bg=COLORS["panel"],  
            fg=COLORS["text"],
            font=FONT_H2,
        ).pack(anchor="w", pady=(0, 8))
        tk.Label(
            self.corrections_frame,
            text=(
                "Use 'Validar datos' para detectar diferencias. Si algo no cuadra, podra corregir "
                "saldo, abono, credito, interes, dias o periodicidad antes de generar el archivo final."
            ),
            bg=COLORS["panel_2"],
            fg=COLORS["muted"],
            font=FONT_BODY,
            wraplength=1050,
            justify="left",
            padx=12,
            pady=10,
        ).pack(fill="x")

    def _render_corrections(self, normalizacion):
        previous_dates = {
            fila: variable.get()
            for fila, variable in self.date_override_vars.items()
        }
        for child in self.corrections_frame.winfo_children():
            child.destroy()
        self.correction_vars = {}
        self.date_override_vars = {}

        tk.Label(
            self.corrections_frame,
            text="Correcciones antes de generar",
            bg=COLORS["panel"],
            fg=COLORS["text"],
            font=FONT_H2,
        ).pack(anchor="w", pady=(0, 8))

        registros = [registro for registro in normalizacion.registros if registro.errores]
        duplicados = self._duplicados(normalizacion.registros)
        duplicados_pendientes = {
            documento: grupo
            for documento, grupo in duplicados.items()
            if not self._duplicado_confirmado(documento)
        }
        self._render_validation_overview(normalizacion)
        self._render_fecha_overrides(normalizacion.registros, previous_dates=previous_dates)
        if registros:
            actions = tk.Frame(self.corrections_frame, bg=COLORS["panel"])
            actions.pack(fill="x", pady=(0, 12))
            self._button(
                actions,
                "Aplicar correcciones",
                self.validate_data,
                primary=True,
                width=190,
                height=38,
            ).pack(side="left")
            tk.Label(
                actions,
                text="Despues de corregir o confirmar duplicados, aplique los cambios para volver a validar.",
                bg=COLORS["panel"],
                fg=COLORS["muted"],
                font=FONT_BODY,
            ).pack(side="left", padx=(12, 0))

        if duplicados_pendientes:
            self._render_duplicates(duplicados_pendientes)
        if not registros:
            tk.Label(
                self.corrections_frame,
                text="Sin diferencias bloqueantes. Puede generar el archivo final.",
                bg=COLORS["panel_2"],
                fg=COLORS["text"],
                font=FONT_BODY_BOLD,
                padx=12,
                pady=10,
            ).pack(fill="x")
            self._render_csv_preview(normalizacion)
            return

        tk.Label(
            self.corrections_frame,
            text=(
                "Edite solo el dato confirmado con el cliente. Luego presione 'Aplicar correcciones'. "
                "Esas correcciones quedan aplicadas al Excel de respaldo y al CSV final."
            ),
            bg=COLORS["panel_2"],
            fg=COLORS["muted"],
            font=FONT_BODY,
            wraplength=1050,
            justify="left",
            padx=12,
            pady=10,
        ).pack(fill="x", pady=(0, 12))

        table = tk.Frame(self.corrections_frame, bg=COLORS["panel"])
        table.pack(fill="x")
        headers = [
            "Fila",
            "Documento",
            "Cliente",
            "Credito",
            "Interes",
            "Saldo cliente",
            "Abono",
            "Dias credito",
            "Periodo",
            "Detalle",
        ]
        widths = [6, 12, 20, 12, 8, 12, 12, 10, 8, 42]
        for column, (text, width) in enumerate(zip(headers, widths)):
            tk.Label(
                table,
                text=text,
                bg=COLORS["panel"],
                fg=COLORS["accent_2"],
                font=("Segoe UI", 9, "bold"),
                anchor="w",
                width=width,
            ).grid(row=0, column=column, sticky="ew", padx=(0, 6), pady=(0, 6))

        for row, registro in enumerate(registros[:25], start=1):
            self._correction_row(table, row, registro)

        if len(registros) > 25:
            tk.Label(
                self.corrections_frame,
                text=f"Se muestran las primeras 25 diferencias de {len(registros)}. Corrija y vuelva a validar.",
                bg=COLORS["panel"],
                fg="#ffcf70",
                font=FONT_BODY,
            ).pack(anchor="w", pady=(10, 0))
        self._render_csv_preview(normalizacion)

    def _render_validation_overview(self, normalizacion):
        resumen = service.resumen_validacion(normalizacion)
        box = tk.Frame(self.corrections_frame, bg=COLORS["panel_2"], padx=14, pady=12)
        box.pack(fill="x", pady=(0, 12))
        tk.Label(
            box,
            text="Panel de validacion",
            bg=COLORS["panel_2"],
            fg=COLORS["text"],
            font=FONT_BODY_BOLD,
        ).pack(anchor="w", pady=(0, 10))

        cards = tk.Frame(box, bg=COLORS["panel_2"])
        cards.pack(fill="x")
        items = [
            ("Total", resumen["total"], COLORS["text"]),
            ("Validos", resumen["validos"], COLORS["accent_2"]),
            ("Errores", resumen["errores_bloqueantes"], "#ffcf70" if resumen["errores_bloqueantes"] else COLORS["accent_2"]),
            ("Advertencias", resumen["advertencias"], "#ffcf70" if resumen["advertencias"] else COLORS["muted"]),
            ("Ajustes auto", resumen["ajustes_automaticos"], COLORS["accent_2"] if resumen["ajustes_automaticos"] else COLORS["muted"]),
            ("Abonos reconstr.", resumen["abonos_reconstruidos"], COLORS["accent_2"] if resumen["abonos_reconstruidos"] else COLORS["muted"]),
        ]
        for index, (label, value, color) in enumerate(items):
            card = tk.Frame(cards, bg=COLORS["panel"], padx=12, pady=10)
            card.grid(row=0, column=index, sticky="ew", padx=(0, 10))
            cards.columnconfigure(index, weight=1)
            tk.Label(card, text=str(value), bg=COLORS["panel"], fg=color, font=("Segoe UI", 17, "bold")).pack(anchor="w")
            tk.Label(card, text=label, bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 9, "bold")).pack(anchor="w")

        self._render_warning_details(box, resumen["errores_generales"])

    def _render_warning_details(self, parent, mensajes):
        self.warning_detail_frame = None
        self.warning_button = None
        self.warning_count = len(mensajes)
        if not mensajes:
            return

        row = tk.Frame(parent, bg=COLORS["panel_2"])
        row.pack(fill="x", pady=(12, 0))
        self.warning_button = self._button(
            row,
            "Ocultar advertencias" if self.warning_open else f"Ver advertencias ({len(mensajes)})",
            self.toggle_warning_details,
            width=190,
            height=36,
        )
        self.warning_button.pack(side="left")
        tk.Label(
            row,
            text="Detalle de ajustes automaticos y mensajes de revision.",
            bg=COLORS["panel_2"],
            fg=COLORS["muted"],
            font=FONT_BODY,
            wraplength=620,
            justify="left",
        ).pack(side="left", fill="x", expand=True, padx=(12, 0))

        self.warning_detail_frame = tk.Frame(parent, bg=COLORS["panel"], padx=12, pady=10)
        for index, mensaje in enumerate(mensajes, start=1):
            item = tk.Frame(self.warning_detail_frame, bg=COLORS["panel_2"], padx=10, pady=8)
            item.pack(fill="x", pady=(0, 8))
            tk.Label(
                item,
                text=self._warning_category(mensaje),
                bg=COLORS["panel_2"],
                fg=COLORS["accent_2"],
                font=("Segoe UI", 9, "bold"),
                anchor="w",
            ).pack(anchor="w", pady=(0, 4))
            tk.Label(
                item,
                text=f"{index}. {mensaje}",
                bg=COLORS["panel_2"],
                fg=COLORS["text"],
                font=FONT_BODY,
                wraplength=760,
                justify="left",
                anchor="w",
            ).pack(fill="x", anchor="w")

        if self.warning_open:
            self.warning_detail_frame.pack(fill="x", pady=(10, 0))

    def _warning_category(self, mensaje):
        texto = mensaje.lower()
        if "completaron" in texto or "sin direccion" in texto or "3000000000" in texto:
            return "Datos completados"
        if "normalizaron" in texto or "formato" in texto or "aaaa-mm-dd" in texto:
            return "Normalizacion"
        if "ajustaron" in texto or "recortaron" in texto:
            return "Ajuste automatico"
        return "Revision"

    def toggle_warning_details(self):
        if not self.warning_detail_frame or not self.warning_button:
            return
        self.warning_open = not self.warning_open
        if self.warning_open:
            self.warning_detail_frame.pack(fill="x", pady=(10, 0))
            self.warning_button.text = "Ocultar advertencias"
        else:
            self.warning_detail_frame.pack_forget()
            self.warning_button.text = f"Ver advertencias ({self.warning_count})"
        self.warning_button._draw()
        self._update_scroll_region()

    def _render_csv_preview(self, normalizacion):
        self.preview_edit_vars = {}
        self.preview_original_values = {}
        try:
            columnas, filas = service.preview_csv_final(
                normalizacion,
                dias_credito_default=self._get_int_config(self.dias_credito_default, "dias credito"),
                fecha_prox_pago_mode=self._get_fecha_prox_mode(),
                fecha_prox_pago_manual=self.fecha_prox_manual.get(),
                limite=max(len(normalizacion.registros), 1),
            )
        except Exception as error:
            tk.Label(
                self.corrections_frame,
                text=f"No se pudo construir la vista previa del CSV: {error}",
                bg=COLORS["panel_2"],
                fg="#ffcf70",
                font=FONT_BODY,
                padx=12,
                pady=10,
            ).pack(fill="x", pady=(12, 0))
            return

        self.csv_preview_payload = (normalizacion, columnas, filas)
        box = tk.Frame(self.corrections_frame, bg=COLORS["panel_2"], padx=14, pady=12)
        box.pack(fill="x", pady=(12, 0))
        header = tk.Frame(box, bg=COLORS["panel_2"])
        header.pack(fill="x")
        tk.Label(
            header,
            text="CSV final",
            bg=COLORS["panel_2"],
            fg=COLORS["text"],
            font=FONT_BODY_BOLD,
        ).pack(side="left")
        self.csv_preview_toggle_button = self._button(
            header,
            "Ocultar tabla" if self.csv_preview_open else "Editar tabla completa",
            self._toggle_csv_preview,
            primary=True,
            width=190,
            height=34,
        )
        self.csv_preview_toggle_button.pack(side="right")
        tk.Label(
            box,
            text=(
                f"{len(filas)} registro(s) preparados para Listo_creditos.csv. "
                "Abra la tabla solo cuando necesite ajustar datos antes de generar."
            ),
            bg=COLORS["panel_2"],
            fg=COLORS["muted"],
            font=FONT_BODY,
            wraplength=1050,
            justify="left",
        ).pack(anchor="w", pady=(0, 10))

        self.csv_preview_body = tk.Frame(box, bg=COLORS["panel_2"])

        if self.csv_preview_open:
            self.csv_preview_body.pack(fill="x")
            self._build_csv_preview_body(self.csv_preview_body, normalizacion, columnas, filas)

    def _build_csv_preview_body(self, body, normalizacion, columnas, filas):
        for child in body.winfo_children():
            child.destroy()
        self.preview_edit_vars = {}
        self.preview_original_values = {}

        actions = tk.Frame(body, bg=COLORS["panel_2"])
        actions.pack(fill="x", pady=(0, 10))
        self._button(
            actions,
            "Aplicar cambios al cargue",
            self._apply_preview_edits,
            primary=True,
            width=190,
            height=34,
        ).pack(side="left")
        tk.Label(
            actions,
            text="Edite las celdas necesarias y aplique para volver a validar.",
            bg=COLORS["panel_2"],
            fg=COLORS["muted"],
            font=FONT_BODY,
        ).pack(side="left", padx=(12, 0))

        table = tk.Frame(body, bg=COLORS["panel_2"])
        table.pack(fill="x")
        widths = [13, 14, 15, 12, 12, 10, 6, 13, 10]
        for column, (header, width) in enumerate(zip(columnas, widths)):
            tk.Label(
                table,
                text=header,
                bg=COLORS["panel_2"],
                fg=COLORS["accent_2"],
                font=("Segoe UI", 8, "bold"),
                anchor="w",
                width=width,
            ).grid(row=0, column=column, sticky="ew", padx=(0, 6), pady=(0, 6))
            table.columnconfigure(column, weight=1)

        registros_preview = normalizacion.registros[:len(filas)]
        for row_index, (registro, row_values) in enumerate(zip(registros_preview, filas), start=1):
            self.preview_edit_vars[registro.fila_origen] = {}
            self.preview_original_values[registro.fila_origen] = {}
            for column, value in enumerate(row_values):
                variable = tk.StringVar(value=str(value))
                self.preview_edit_vars[registro.fila_origen][columnas[column]] = variable
                self.preview_original_values[registro.fila_origen][columnas[column]] = str(value)
                entry = tk.Entry(
                    table,
                    textvariable=variable,
                    bg=COLORS["panel"],
                    fg=COLORS["text"],
                    font=("Segoe UI", 8),
                    insertbackground=COLORS["text"],
                    relief="flat",
                    bd=0,
                    justify="left",
                )
                entry.grid(row=row_index, column=column, sticky="ew", padx=(0, 6), pady=2, ipady=5)

    def _toggle_csv_preview(self):
        if self.csv_preview_animating:
            return
        if not self.csv_preview_body or not self.csv_preview_payload:
            self.csv_preview_open = not self.csv_preview_open
            self.validate_data()
            return

        self.csv_preview_open = not self.csv_preview_open
        if self.csv_preview_toggle_button:
            self.csv_preview_toggle_button.text = "Ocultar tabla" if self.csv_preview_open else "Editar tabla completa"
            self.csv_preview_toggle_button._draw()

        if self.csv_preview_open:
            normalizacion, columnas, filas = self.csv_preview_payload
            self._build_csv_preview_body(self.csv_preview_body, normalizacion, columnas, filas)
            self._animate_csv_preview(opening=True)
        else:
            self._animate_csv_preview(opening=False)

    def _animate_csv_preview(self, opening):
        body = self.csv_preview_body
        if not body:
            return

        self.csv_preview_animating = True
        if opening:
            body.pack(fill="x")
            body.update_idletasks()
            target = max(body.winfo_reqheight(), 80)
            body.configure(height=0)
            body.pack_propagate(False)
            steps = 10
            duration = 12

            def expand(step=1):
                height = int(target * (1 - pow(1 - step / steps, 3)))
                body.configure(height=max(height, 1))
                self._update_scroll_region()
                if step < steps:
                    body.after(duration, lambda: expand(step + 1))
                else:
                    body.pack_propagate(True)
                    body.configure(height=target)
                    self.csv_preview_animating = False
                    self._update_scroll_region()

            expand()
            return

        body.update_idletasks()
        start = max(body.winfo_height(), body.winfo_reqheight(), 80)
        body.configure(height=start)
        body.pack_propagate(False)
        steps = 9
        duration = 12

        def collapse(step=1):
            height = int(start * pow(1 - step / steps, 3))
            body.configure(height=max(height, 1))
            self._update_scroll_region()
            if step < steps:
                body.after(duration, lambda: collapse(step + 1))
            else:
                body.pack_forget()
                body.pack_propagate(True)
                self.csv_preview_animating = False
                self._update_scroll_region()

        collapse()

    def _apply_preview_edits(self):
        if not self.preview_edit_vars:
            messagebox.showinfo("Cargue de rutas", "No hay filas visibles para aplicar.")
            return

        applied = 0
        for fila, campos_csv in self.preview_edit_vars.items():
            cambios = self._preview_fields_to_corrections(
                campos_csv,
                self.preview_original_values.get(fila, {}),
            )
            if not cambios:
                continue
            actuales = dict(self.manual_preview_corrections.get(fila, {}))
            actuales.update(cambios)
            self.manual_preview_corrections[fila] = actuales
            applied += 1

        if not applied:
            messagebox.showinfo("Cargue de rutas", "No se detectaron cambios aplicables.")
            return

        self.status.set(f"Se aplicaron cambios manuales en {applied} fila(s). Validando de nuevo...")
        self.validate_data()

    def _preview_fields_to_corrections(self, campos_csv, originales):
        get_value = lambda key: campos_csv.get(key).get().strip() if campos_csv.get(key) else ""
        raw_changes = {
            "documento": get_value("documento"),
            "nombres": get_value("PrimerNombre"),
            "apellidos": get_value("PrimerApellido"),
            "valor_credito": get_value("ValorCredito"),
            "saldo_actual": get_value("Saldo"),
            "dias_credito": get_value("DiasCredito"),
            "periodicidad_codigo": get_value("dia"),
            "fecha_prox_pago": get_value("FechaProxPago"),
            "abono_informado": get_value("Abono"),
        }
        csv_by_field = {
            "documento": "documento",
            "nombres": "PrimerNombre",
            "apellidos": "PrimerApellido",
            "valor_credito": "ValorCredito",
            "saldo_actual": "Saldo",
            "dias_credito": "DiasCredito",
            "periodicidad_codigo": "dia",
            "fecha_prox_pago": "FechaProxPago",
            "abono_informado": "Abono",
        }
        cambios = {}
        for campo, valor in raw_changes.items():
            csv_name = csv_by_field[campo]
            if valor != str(originales.get(csv_name, "")).strip():
                cambios[campo] = valor
        return cambios

    def _render_fecha_overrides(self, registros, previous_dates=None):
        if not registros:
            return
        previous_dates = previous_dates or {}

        box = tk.Frame(self.corrections_frame, bg=COLORS["panel_2"], padx=14, pady=12)
        box.pack(fill="x", pady=(0, 12))
        header = tk.Frame(box, bg=COLORS["panel_2"])
        header.pack(fill="x")
        tk.Label(
            header,
            text="Fecha proximo pago por cliente",
            bg=COLORS["panel_2"],
            fg=COLORS["text"],
            font=FONT_BODY_BOLD,
        ).pack(side="left")
        self._button(
            header,
            "Aplicar fechas",
            self.validate_data,
            width=130,
            height=34,
        ).pack(side="right")
        self._button(
            header,
            "Aplicar a todos",
            self._apply_global_date_to_rows,
            width=140,
            height=34,
        ).pack(side="right", padx=(0, 8))
        self._date_field(header, self.fecha_prox_global, width=130).pack(side="right", padx=(0, 8))
        tk.Label(
            header,
            text="Para todos",
            bg=COLORS["panel_2"],
            fg=COLORS["muted"],
            font=("Segoe UI", 9, "bold"),
        ).pack(side="right", padx=(0, 8))
        tk.Label(
            box,
            text=(
                "Seleccione una fecha en 'Para todos' si el cliente pide una misma fecha general. "
                "Luego ajuste solo las filas que necesiten una fecha diferente."
            ),
            bg=COLORS["panel_2"],
            fg=COLORS["muted"],
            font=FONT_BODY,
            wraplength=1050,
            justify="left",
        ).pack(anchor="w", pady=(6, 10))

        table = tk.Frame(box, bg=COLORS["panel_2"])
        table.pack(fill="x")
        headers = ("Fila", "Documento", "Cliente", "Fecha prox. pago")
        widths = (6, 18, 30, 18)
        for column, (text, width) in enumerate(zip(headers, widths)):
            tk.Label(
                table,
                text=text,
                bg=COLORS["panel_2"],
                fg=COLORS["accent_2"],
                font=("Segoe UI", 9, "bold"),
                anchor="w",
                width=width,
            ).grid(row=0, column=column, sticky="ew", padx=(0, 10), pady=(0, 6))
        table.columnconfigure(0, weight=0)
        table.columnconfigure(1, weight=1)
        table.columnconfigure(2, weight=2)
        table.columnconfigure(3, weight=1)

        for row, registro in enumerate(registros[:40], start=1):
            tk.Label(
                table,
                text=str(registro.fila_origen),
                bg=COLORS["panel_2"],
                fg=COLORS["text"],
                font=FONT_BODY,
                anchor="w",
            ).grid(row=row, column=0, sticky="ew", padx=(0, 10), pady=3)
            tk.Label(
                table,
                text=registro.documento,
                bg=COLORS["panel_2"],
                fg=COLORS["text"],
                font=FONT_BODY,
                anchor="w",
            ).grid(row=row, column=1, sticky="ew", padx=(0, 10), pady=3)
            tk.Label(
                table,
                text=self._nombre_cliente(registro),
                bg=COLORS["panel_2"],
                fg=COLORS["text"],
                font=FONT_BODY,
                anchor="w",
            ).grid(row=row, column=2, sticky="ew", padx=(0, 10), pady=3)
            previous = previous_dates.get(registro.fila_origen) or previous_dates.get(str(registro.fila_origen))
            variable = tk.StringVar(value=previous or self._fecha_prox_edit_value(registro))
            self.date_override_vars[registro.fila_origen] = variable
            self._date_field(table, variable, width=160).grid(row=row, column=3, sticky="ew", padx=(0, 10), pady=3)

        if len(registros) > 40:
            tk.Label(
                box,
                text=f"Se muestran las primeras 40 fechas de {len(registros)} registros.",
                bg=COLORS["panel_2"],
                fg=COLORS["muted"],
                font=FONT_BODY,
            ).pack(anchor="w", pady=(8, 0))

    def _render_duplicates(self, duplicados):
        box = tk.Frame(self.corrections_frame, bg=COLORS["panel_2"], padx=14, pady=12)
        box.pack(fill="x", pady=(0, 12))
        tk.Label(
            box,
            text="Clientes/documentos repetidos",
            bg=COLORS["panel_2"],
            fg=COLORS["text"],
            font=FONT_BODY_BOLD,
        ).pack(anchor="w")
        tk.Label(
            box,
            text=(
                "La app no une creditos repetidos. Si confirma que son creditos diferentes, "
                "dejan de aparecer abajo como errores pendientes. Si no esta seguro, consulte "
                "con el cliente antes de generar."
            ),
            bg=COLORS["panel_2"],
            fg=COLORS["muted"],
            font=FONT_BODY,
            wraplength=1050,
            justify="left",
        ).pack(anchor="w", pady=(4, 10))

        table = tk.Frame(box, bg=COLORS["panel_2"])
        table.pack(fill="x")
        for column, text in enumerate(("Documento", "Cliente", "Filas", "Creditos", "Decision")):
            tk.Label(
                table,
                text=text,
                bg=COLORS["panel_2"],
                fg=COLORS["accent_2"],
                font=("Segoe UI", 9, "bold"),
                anchor="w",
            ).grid(row=0, column=column, sticky="ew", padx=(0, 10), pady=(0, 6))
        table.columnconfigure(0, weight=1)
        table.columnconfigure(1, weight=2)
        table.columnconfigure(2, weight=1)
        table.columnconfigure(3, weight=2)
        table.columnconfigure(4, weight=2)

        for row, (documento, registros) in enumerate(duplicados.items(), start=1):
            tk.Label(table, text=documento, bg=COLORS["panel_2"], fg=COLORS["text"], font=FONT_BODY).grid(
                row=row, column=0, sticky="ew", padx=(0, 10), pady=3
            )
            tk.Label(
                table,
                text=self._nombre_cliente_duplicado(registros),
                bg=COLORS["panel_2"],
                fg=COLORS["text"],
                font=FONT_BODY,
            ).grid(row=row, column=1, sticky="ew", padx=(0, 10), pady=3)
            tk.Label(
                table,
                text=", ".join(str(registro.fila_origen) for registro in registros),
                bg=COLORS["panel_2"],
                fg=COLORS["text"],
                font=FONT_BODY,
            ).grid(row=row, column=2, sticky="ew", padx=(0, 10), pady=3)
            creditos = sorted({registro.numero_credito for registro in registros if registro.numero_credito})
            tk.Label(
                table,
                text=", ".join(creditos) if creditos else "Sin numero de credito detectado",
                bg=COLORS["panel_2"],
                fg=COLORS["muted"],
                font=FONT_BODY,
            ).grid(row=row, column=3, sticky="ew", padx=(0, 10), pady=3)
            variable = self.duplicate_vars.get(documento) or tk.StringVar(value="Pendiente")
            self.duplicate_vars[documento] = variable
            combo = ttk.Combobox(
                table,
                textvariable=variable,
                values=["Pendiente", "Son creditos diferentes"],
                state="readonly",
                font=("Segoe UI", 9),
            )
            combo.grid(row=row, column=4, sticky="ew", padx=(0, 10), pady=3)
            combo.bind("<MouseWheel>", self._on_combobox_mousewheel)

        confirmed = [
            documento
            for documento, variable in self.duplicate_vars.items()
            if variable.get() == "Son creditos diferentes"
        ]
        if confirmed:
            tk.Label(
                box,
                text=(
                    "Confirmado: estos documentos se mantienen como filas separadas en el archivo final "
                    "y ya no bajan a la tabla de correcciones."
                ),
                bg=COLORS["panel_2"],
                fg=COLORS["accent_2"],
                font=FONT_BODY_BOLD,
                wraplength=1050,
                justify="left",
                padx=10,
                pady=8,
            ).pack(fill="x", pady=(10, 0))

    def _duplicados(self, registros):
        grupos = {}
        for registro in registros:
            if not registro.documento:
                continue
            grupos.setdefault(registro.documento, []).append(registro)
        return {
            documento: grupo
            for documento, grupo in grupos.items()
            if len(grupo) > 1
        }

    def _duplicado_confirmado(self, documento):
        variable = self.duplicate_vars.get(documento)
        return bool(variable and variable.get() == "Son creditos diferentes")

    def _nombre_cliente(self, registro):
        nombre = " ".join(
            parte.strip()
            for parte in (registro.nombres, registro.apellidos)
            if parte and parte.strip()
        )
        return nombre or "Sin nombre"

    def _nombre_cliente_duplicado(self, registros):
        nombres = []
        for registro in registros:
            nombre = self._nombre_cliente(registro)
            if nombre != "Sin nombre" and nombre not in nombres:
                nombres.append(nombre)
        return " / ".join(nombres) if nombres else "Sin nombre"

    def _correction_row(self, table, row, registro):
        tk.Label(
            table,
            text=str(registro.fila_origen),
            bg=COLORS["panel"],
            fg=COLORS["text"],
            font=FONT_BODY,
            anchor="w",
        ).grid(row=row, column=0, sticky="ew", padx=(0, 6), pady=3)

        campos = [
            ("documento", registro.documento, 14),
            ("valor_credito", self._format_edit_value(registro.valor_credito), 12),
            ("interes", self._format_edit_value(registro.interes), 8),
            ("saldo_actual", self._format_edit_value(registro.saldo_actual), 12),
            ("abono_informado", self._format_edit_value(self._abono_visible(registro)), 12),
            ("dias_credito", self._format_edit_value(registro.dias_credito), 7),
            ("periodicidad_codigo", self._format_edit_value(registro.periodicidad_codigo), 8),
        ]
        self.correction_vars[registro.fila_origen] = {}
        for column, (campo, value, width) in enumerate(campos, start=1):
            variable = tk.StringVar(value=value)
            self.correction_vars[registro.fila_origen][campo] = variable
            entry = tk.Entry(
                table,
                textvariable=variable,
                width=width,
                bg=COLORS["panel_2"],
                fg=COLORS["text"],
                insertbackground=COLORS["text"],
                relief="flat",
                font=("Segoe UI", 9),
            )
            grid_column = column if column == 1 else column + 1
            entry.grid(row=row, column=grid_column, sticky="ew", padx=(0, 6), pady=3, ipady=4)

            if column == 1:
                tk.Label(
                    table,
                    text=self._nombre_cliente(registro),
                    bg=COLORS["panel"],
                    fg=COLORS["text"],
                    font=("Segoe UI", 9),
                    anchor="w",
                    wraplength=150,
                    justify="left",
                ).grid(row=row, column=2, sticky="ew", padx=(0, 6), pady=3)

        tk.Label(
            table,
            text="; ".join(registro.errores),
            bg=COLORS["panel"],
            fg="#ffcf70",
            font=("Segoe UI", 9),
            anchor="w",
            justify="left",
            wraplength=360,
        ).grid(row=row, column=9, sticky="ew", padx=(0, 6), pady=3)

    def _abono_visible(self, registro):
        if registro.abono_estado == "reconstruido":
            return registro.abono_reconstruido
        return registro.abono_informado

    def _fecha_prox_edit_value(self, registro):
        return self._normalize_date_text(registro.fecha_prox_pago)

    def _date_field(self, parent, variable, width=150):
        field = tk.Frame(parent, bg=COLORS["panel"], highlightthickness=0)
        entry = tk.Entry(
            field,
            textvariable=variable,
            width=12,
            bg=COLORS["panel"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            font=("Segoe UI", 9),
            justify="center",
        )
        entry.pack(side="left", fill="both", expand=True, ipady=5)
        button = tk.Button(
            field,
            text="▼",
            command=lambda: self._open_embedded_calendar(variable, field),
            bg=COLORS["panel_3"],
            fg=COLORS["text"],
            activebackground=COLORS["accent_active"],
            activeforeground="white",
            relief="flat",
            bd=0,
            width=3,
            cursor="hand2",
            font=("Segoe UI", 8, "bold"),
        )
        button.pack(side="right", fill="y")
        entry.bind("<Button-1>", lambda _event: self._open_embedded_calendar(variable, field))
        field.bind("<Button-1>", lambda _event: self._open_embedded_calendar(variable, field))
        field.configure(width=width, height=34)
        field.pack_propagate(False)
        return field

    def _apply_global_date_to_rows(self):
        fecha = self._normalize_date_text(self.fecha_prox_global.get())
        if not fecha:
            messagebox.showwarning(
                "Cargue de rutas",
                "Seleccione una fecha valida para aplicar a todos. Formato recomendado: AAAA-MM-DD.",
            )
            return
        self.fecha_prox_global.set(fecha)
        for variable in self.date_override_vars.values():
            variable.set(fecha)

    def _open_embedded_calendar(self, variable, anchor_widget=None):
        if self._calendar_popup is not None and self._calendar_popup.winfo_exists():
            self._calendar_popup.destroy()
        self._unbind_calendar_outside_click()

        initial = self._parse_date(variable.get()) or date.today()
        current = {"year": initial.year, "month": initial.month}

        popup = tk.Frame(self.content_frame, bg=COLORS["accent"], padx=1, pady=1)
        self._calendar_popup = popup
        container = tk.Frame(popup, bg=COLORS["panel"], padx=12, pady=10)
        container.pack(fill="both", expand=True)

        title_var = tk.StringVar()
        grid = tk.Frame(container, bg=COLORS["panel"])

        def close_popup():
            if popup.winfo_exists():
                popup.destroy()
            self._unbind_calendar_outside_click()

        def select_day(day):
            variable.set(f"{current['year']:04d}-{current['month']:02d}-{day:02d}")
            close_popup()

        def redraw():
            for child in grid.winfo_children():
                child.destroy()
            title_var.set(f"{calendar.month_name[current['month']]} {current['year']}")
            for column, label in enumerate(("L", "M", "M", "J", "V", "S", "D")):
                tk.Label(
                    grid,
                    text=label,
                    bg=COLORS["panel"],
                    fg=COLORS["accent_2"],
                    font=("Segoe UI", 8, "bold"),
                    width=4,
                ).grid(row=0, column=column, padx=1, pady=(0, 4))

            today = date.today()
            for row_index, week in enumerate(calendar.monthcalendar(current["year"], current["month"]), start=1):
                for column, day in enumerate(week):
                    if day == 0:
                        tk.Label(grid, text="", bg=COLORS["panel"], width=4).grid(row=row_index, column=column, padx=1, pady=1)
                        continue
                    is_today = current["year"] == today.year and current["month"] == today.month and day == today.day
                    normal_bg = COLORS["accent"] if is_today else COLORS["panel_2"]
                    normal_fg = "white" if is_today else COLORS["text"]
                    cell = tk.Label(
                        grid,
                        text=str(day),
                        bg=normal_bg,
                        fg=normal_fg,
                        font=("Segoe UI", 9),
                        width=4,
                        cursor="hand2",
                        padx=0,
                        pady=4,
                    )
                    cell.grid(row=row_index, column=column, padx=1, pady=1, sticky="nsew")
                    cell.bind("<Enter>", lambda _event, widget=cell: widget.configure(bg=COLORS["accent_hover"], fg="white"))
                    cell.bind("<Leave>", lambda _event, widget=cell, bg=normal_bg, fg=normal_fg: widget.configure(bg=bg, fg=fg))
                    cell.bind("<ButtonPress-1>", lambda _event, widget=cell: widget.configure(bg=COLORS["accent_active"], fg="white"))
                    cell.bind("<ButtonRelease-1>", lambda _event, selected=day: select_day(selected))

        def move_month(delta):
            month = current["month"] + delta
            year = current["year"]
            if month < 1:
                month = 12
                year -= 1
            elif month > 12:
                month = 1
                year += 1
            current["month"] = month
            current["year"] = year
            redraw()

        header = tk.Frame(container, bg=COLORS["panel"])
        header.pack(fill="x", pady=(0, 8))
        prev_label = tk.Label(header, text="<", bg=COLORS["panel_2"], fg=COLORS["text"], width=4, cursor="hand2", font=("Segoe UI", 9, "bold"))
        prev_label.pack(side="left")
        prev_label.bind("<Enter>", lambda _event: prev_label.configure(bg=COLORS["panel_3"]))
        prev_label.bind("<Leave>", lambda _event: prev_label.configure(bg=COLORS["panel_2"]))
        prev_label.bind("<ButtonPress-1>", lambda _event: prev_label.configure(bg=COLORS["accent_active"], fg="white"))
        prev_label.bind("<ButtonRelease-1>", lambda _event: (prev_label.configure(bg=COLORS["panel_3"], fg=COLORS["text"]), move_month(-1)))
        tk.Label(header, textvariable=title_var, bg=COLORS["panel"], fg=COLORS["text"], font=FONT_BODY_BOLD).pack(side="left", expand=True)
        close_label = tk.Label(header, text="x", bg=COLORS["panel"], fg=COLORS["muted"], width=3, cursor="hand2", font=("Segoe UI", 9, "bold"))
        close_label.pack(side="right", padx=(4, 0))
        close_label.bind("<Enter>", lambda _event: close_label.configure(bg=COLORS["panel_2"], fg=COLORS["text"]))
        close_label.bind("<Leave>", lambda _event: close_label.configure(bg=COLORS["panel"], fg=COLORS["muted"]))
        close_label.bind("<ButtonRelease-1>", lambda _event: close_popup())
        next_label = tk.Label(header, text=">", bg=COLORS["panel_2"], fg=COLORS["text"], width=4, cursor="hand2", font=("Segoe UI", 9, "bold"))
        next_label.pack(side="right")
        next_label.bind("<Enter>", lambda _event: next_label.configure(bg=COLORS["panel_3"]))
        next_label.bind("<Leave>", lambda _event: next_label.configure(bg=COLORS["panel_2"]))
        next_label.bind("<ButtonPress-1>", lambda _event: next_label.configure(bg=COLORS["accent_active"], fg="white"))
        next_label.bind("<ButtonRelease-1>", lambda _event: (next_label.configure(bg=COLORS["panel_3"], fg=COLORS["text"]), move_month(1)))
        grid.pack()
        redraw()
        self._place_embedded_calendar(popup, anchor_widget)
        self._bind_calendar_outside_click(popup)

    def _place_embedded_calendar(self, popup, anchor_widget=None):
        popup.update_idletasks()
        if anchor_widget is None:
            x = 80
            y = 120
        else:
            x = anchor_widget.winfo_rootx() - self.content_frame.winfo_rootx()
            y = anchor_widget.winfo_rooty() - self.content_frame.winfo_rooty() + anchor_widget.winfo_height() + 4

        width = popup.winfo_reqwidth()
        content_width = max(self.content_frame.winfo_width(), self.canvas.winfo_width(), width + 16)
        x = max(8, min(x, content_width - width - 8))
        popup.place(x=x, y=max(8, y))
        popup.lift()

    def _bind_calendar_outside_click(self, popup):
        def close_if_outside(event):
            if not popup.winfo_exists():
                self._unbind_calendar_outside_click()
                return
            widget = self.winfo_containing(event.x_root, event.y_root)
            current = widget
            while current is not None:
                if current is popup:
                    return
                current = getattr(current, "master", None)
            popup.destroy()
            self._unbind_calendar_outside_click()

        self._calendar_outside_bind = close_if_outside
        self.after(100, lambda: self._set_calendar_outside_bind(close_if_outside))

    def _set_calendar_outside_bind(self, callback):
        self._calendar_outside_bind_id = self.bind_all("<Button-1>", callback, add="+")

    def _unbind_calendar_outside_click(self):
        if self._calendar_outside_bind is None:
            return
        try:
            if self._calendar_outside_bind_id:
                self.unbind_all("<Button-1>")
        except tk.TclError:
            pass
        self._calendar_outside_bind = None
        self._calendar_outside_bind_id = None

    def _open_calendar(self, variable, anchor_widget=None):
        self._open_embedded_calendar(variable, anchor_widget)
        return

        if self._calendar_popup is not None and self._calendar_popup.winfo_exists():
            self._calendar_popup.destroy()

        initial = self._parse_date(variable.get()) or date.today()
        current = {"year": initial.year, "month": initial.month}

        popup = tk.Toplevel(self)
        self._calendar_popup = popup
        popup.title("Seleccionar fecha")
        popup.configure(bg=COLORS["panel"])
        popup.resizable(False, False)
        popup.transient(self.winfo_toplevel())
        popup.bind("<Escape>", lambda _event: popup.destroy())

        shell = tk.Frame(popup, bg=COLORS["accent"], padx=1, pady=1)
        shell.pack(fill="both", expand=True)
        container = tk.Frame(shell, bg=COLORS["panel"], padx=12, pady=10)
        container.pack(fill="both", expand=True)
        title_var = tk.StringVar()
        grid = tk.Frame(container, bg=COLORS["panel"])

        def select_day(day):
            variable.set(f"{current['year']:04d}-{current['month']:02d}-{day:02d}")
            popup.destroy()

        def redraw():
            for child in grid.winfo_children():
                child.destroy()
            title_var.set(f"{calendar.month_name[current['month']]} {current['year']}")
            for column, label in enumerate(("Lu", "Ma", "Mi", "Ju", "Vi", "Sa", "Do")):
                tk.Label(
                    grid,
                    text=label,
                    bg=COLORS["panel"],
                    fg=COLORS["accent_2"],
                    font=("Segoe UI", 8, "bold"),
                    width=4,
                ).grid(row=0, column=column, padx=1, pady=(0, 4))
            for row_index, week in enumerate(calendar.monthcalendar(current["year"], current["month"]), start=1):
                for column, day in enumerate(week):
                    if day == 0:
                        tk.Label(grid, text="", bg=COLORS["panel"], width=4).grid(row=row_index, column=column, padx=1, pady=1)
                        continue
                    tk.Button(
                        grid,
                        text=str(day),
                        command=lambda selected=day: select_day(selected),
                        bg=COLORS["panel_2"],
                        fg=COLORS["text"],
                        activebackground=COLORS["accent"],
                        activeforeground="white",
                        relief="flat",
                        bd=0,
                        width=4,
                        cursor="hand2",
                    ).grid(row=row_index, column=column, padx=1, pady=1, ipady=2)

        def move_month(delta):
            month = current["month"] + delta
            year = current["year"]
            if month < 1:
                month = 12
                year -= 1
            elif month > 12:
                month = 1
                year += 1
            current["month"] = month
            current["year"] = year
            redraw()

        header = tk.Frame(container, bg=COLORS["panel"])
        header.pack(fill="x", pady=(0, 8))
        tk.Button(header, text="‹", command=lambda: move_month(-1), bg=COLORS["panel_2"], fg=COLORS["text"], relief="flat", width=4).pack(side="left")
        tk.Label(header, textvariable=title_var, bg=COLORS["panel"], fg=COLORS["text"], font=FONT_BODY_BOLD).pack(side="left", expand=True)
        tk.Button(header, text="›", command=lambda: move_month(1), bg=COLORS["panel_2"], fg=COLORS["text"], relief="flat", width=4).pack(side="right")
        grid.pack()
        redraw()
        self._place_dropdown(popup, anchor_widget)

    def _place_dropdown(self, popup, anchor_widget=None):
        popup.update_idletasks()
        if anchor_widget is None:
            parent = self.winfo_toplevel()
            x = parent.winfo_rootx() + 80
            y = parent.winfo_rooty() + 120
        else:
            x = anchor_widget.winfo_rootx()
            y = anchor_widget.winfo_rooty() + anchor_widget.winfo_height() + 4

        width = popup.winfo_reqwidth()
        height = popup.winfo_reqheight()
        screen_width = popup.winfo_screenwidth()
        screen_height = popup.winfo_screenheight()

        x = max(8, min(x, screen_width - width - 8))
        if y + height > screen_height - 8 and anchor_widget is not None:
            y = anchor_widget.winfo_rooty() - height - 4
        y = max(8, min(y, screen_height - height - 8))
        popup.geometry(f"+{x}+{y}")
        popup.lift()
        popup.attributes("-topmost", True)
        popup.after(200, lambda: popup.attributes("-topmost", False) if popup.winfo_exists() else None)
        popup.focus_force()

    def _normalize_date_text(self, value):
        parsed = self._parse_date(value)
        return parsed.strftime("%Y-%m-%d") if parsed else ""

    def _parse_date(self, value):
        text = str(value or "").strip()
        if not text:
            return None
        compact_match = re.search(r"(\d{4})\D+(\d{1,2})\D+(\d{1,2})", text)
        if compact_match:
            year, month, day = compact_match.groups()
            try:
                return date(int(year), int(month), int(day))
            except ValueError:
                return None
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d", "%d-%m-%Y", "%m-%d-%Y"):
            try:
                return datetime.strptime(text[:10], fmt).date()
            except ValueError:
                continue
        return None

    def _format_edit_value(self, value):
        if value is None:
            return ""
        try:
            number = float(value)
            if number.is_integer():
                return str(int(number))
            return str(number)
        except (TypeError, ValueError):
            return str(value)

    def process_files(self):
        if not self._has_cliente():
            messagebox.showwarning(
                "Cargue de rutas",
                "Seleccione el archivo del cliente antes de procesar.",
            )
            return
        try:
            header_row, data_start_row = self._get_row_config()
            mapping = self._get_mapping_config()
            periodicidad_override_codigo = self._get_periodicidad_override_codigo()
            interes_default = self._get_number_config(self.interes_default, "interes por defecto")
            dias_credito_default = self._get_int_config(self.dias_credito_default, "dias credito")
            fecha_prox_mode = self._get_fecha_prox_mode()
            archivo_cliente = Path(self.archivo_cliente.get())
            fecha_prox_manual = self.fecha_prox_manual.get()
            auditoria = self._audit_info()
            if not auditoria["responsable_nombre"]:
                raise ValueError("Ingrese el nombre del responsable antes de procesar el cargue.")
            if auditoria["responsable_correo"] and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", auditoria["responsable_correo"]):
                raise ValueError("Ingrese un correo responsable valido o dejelo vacio.")
            if not auditoria["nombre_bd"]:
                raise ValueError("Ingrese el Nombre de BD antes de procesar el cargue.")
            correcciones = self._get_corrections_config()
            decisiones_duplicados = self._get_duplicate_decisions()
        except Exception as error:
            self.status.set(f"Error: {error}")
            messagebox.showerror("Cargue de rutas", str(error))
            return

        modal = self._show_processing_modal()

        def worker():
            try:
                salida = service.procesar_archivos(
                    archivo_cliente,
                    header_row=header_row,
                    data_start_row=data_start_row,
                    mapping=mapping,
                    interes_default=interes_default,
                    dias_credito_default=dias_credito_default,
                    fecha_prox_pago_mode=fecha_prox_mode,
                    fecha_prox_pago_manual=fecha_prox_manual,
                    periodicidad_override_codigo=periodicidad_override_codigo,
                    correcciones=correcciones,
                    decisiones_duplicados=decisiones_duplicados,
                    auditoria=auditoria,
                )
            except Exception as error:
                error_text = str(error)
                self.after(0, lambda error_text=error_text: self._finish_processing_modal(modal, False, error_text))
                return
            estado_onedrive = service.obtener_ultimo_estado_onedrive()
            resumen_ejecutivo = service.obtener_ultimo_resumen_ejecutivo()
            success_text = (
                f"Archivo generado correctamente.\nSalida: {salida}\n\n"
                + (f"Resumen ejecutivo:\n{resumen_ejecutivo}\n\n" if resumen_ejecutivo else "")
                + f"OneDrive/SharePoint:\n{estado_onedrive}"
            )
            self.after(0, lambda success_text=success_text: self._finish_processing_modal(modal, True, success_text))

        threading.Thread(target=worker, daemon=True).start()

    def _show_processing_modal(self):
        modal = tk.Toplevel(self)
        modal.title("Procesando cargue")
        modal.configure(bg=COLORS["panel"])
        modal.resizable(False, False)
        modal.transient(self.winfo_toplevel())
        modal.grab_set()
        modal.protocol("WM_DELETE_WINDOW", lambda: None)

        body = tk.Frame(modal, bg=COLORS["panel"], padx=30, pady=24)
        body.pack(fill="both", expand=True)
        title = tk.Label(
            body,
            text="Procesando cargue",
            bg=COLORS["panel"],
            fg=COLORS["text"],
            font=("Segoe UI", 16, "bold"),
        )
        title.pack(anchor="w")
        detail = tk.Label(
            body,
            text="Generando archivo para LISTO. Espere un momento...",
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=FONT_BODY,
            justify="left",
            wraplength=420,
        )
        detail.pack(anchor="w", pady=(8, 18))

        progress = tk.Canvas(
            body,
            width=420,
            height=22,
            bg=COLORS["panel"],
            highlightthickness=0,
            bd=0,
        )
        progress.pack(fill="x", pady=(0, 8))
        progress_state = {"offset": 0, "after_id": None}
        self._animate_processing_bar(progress, progress_state)

        modal.update_idletasks()
        parent = self.winfo_toplevel()
        x = parent.winfo_rootx() + max(0, (parent.winfo_width() - modal.winfo_reqwidth()) // 2)
        y = parent.winfo_rooty() + max(0, (parent.winfo_height() - modal.winfo_reqheight()) // 2)
        modal.geometry(f"+{x}+{y}")
        modal.focus_force()
        return {
            "modal": modal,
            "body": body,
            "title": title,
            "detail": detail,
            "progress": progress,
            "progress_state": progress_state,
        }

    def _animate_processing_bar(self, canvas, state):
        if not canvas.winfo_exists():
            return
        canvas.delete("all")
        width = max(canvas.winfo_width(), int(canvas.cget("width")))
        height = max(canvas.winfo_height(), int(canvas.cget("height")))
        radius = min(10, height // 2)
        self._rounded_canvas_rect(canvas, 0, 1, width, height - 1, radius, fill=COLORS["panel_2"], outline="")

        segment_width = max(90, width // 3)
        travel = width + segment_width
        x = (state["offset"] % travel) - segment_width
        self._rounded_canvas_rect(
            canvas,
            x,
            3,
            x + segment_width,
            height - 3,
            radius - 2,
            fill=COLORS["accent"],
            outline="",
        )
        state["offset"] += 10
        state["after_id"] = canvas.after(35, lambda: self._animate_processing_bar(canvas, state))

    def _rounded_canvas_rect(self, canvas, x1, y1, x2, y2, radius, **kwargs):
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1,
        ]
        return canvas.create_polygon(points, smooth=True, splinesteps=18, **kwargs)

    def _finish_processing_modal(self, modal_state, success, message):
        modal = modal_state["modal"]
        if not modal.winfo_exists():
            return

        after_id = modal_state.get("progress_state", {}).get("after_id")
        if after_id is not None:
            try:
                modal.after_cancel(after_id)
            except tk.TclError:
                pass
        modal_state["progress"].pack_forget()
        modal_state["title"].configure(text="Proceso exitoso" if success else "No se pudo procesar")
        modal_state["detail"].configure(
            text=message,
            fg=COLORS["muted"] if success else "#ffcf70",
        )
        button = self._button(
            modal_state["body"],
            "Aceptar",
            modal.destroy,
            primary=success,
            width=150,
            height=40,
        )
        button.pack(anchor="center", pady=(16, 0))
        if success:
            self.status.set(f"Cargue generado. {message.replace(chr(10), ' ')}")
        else:
            self.status.set(f"Error: {message}")

    def _get_row_config(self):
        try:
            header_row = int(self.header_row.get())
            data_start_row = int(self.data_start_row.get())
        except ValueError as error:
            raise ValueError("Las filas deben ser numeros enteros.") from error
        if header_row < 1 or data_start_row < 1:
            raise ValueError("Las filas deben ser mayores o iguales a 1.")
        if data_start_row <= header_row:
            raise ValueError("La fila inicial de clientes debe ser mayor que la fila de encabezados.")
        return header_row, data_start_row

    def _get_mapping_config(self):
        if not self.mapping_vars:
            return None

        mapping = {}
        for campo, variable in self.mapping_vars.items():
            value = variable.get()
            mapping[campo] = None if value == "Sin mapear" else value
        return mapping

    def _get_periodicidad_override_codigo(self):
        value = self.periodicidad_default.get()
        if "1 -" in value:
            return 1
        if "2 -" in value:
            return 2
        if "3 -" in value:
            return 3
        if "4 -" in value:
            return 4
        return None

    def _get_number_config(self, variable, label):
        value = variable.get().strip()
        if not value:
            return None
        try:
            return float(value.replace(",", "."))
        except ValueError as error:
            raise ValueError(f"El campo {label} debe ser numerico.") from error

    def _get_int_config(self, variable, label):
        value = self._get_number_config(variable, label)
        if value is None:
            return None
        if value < 0:
            raise ValueError(f"El campo {label} no puede ser negativo.")
        return int(value)

    def _get_fecha_prox_mode(self):
        value = self.fecha_prox_mode.get().strip().lower()
        if value == "usar archivo":
            return "archivo"
        if value == "calcular":
            return "calcular"
        if value == "manual":
            return "manual"
        return "vacia"

    def _build_validacion(self):
        header_row, data_start_row = self._get_row_config()
        mapping = self._get_mapping_config()
        periodicidad_override_codigo = self._get_periodicidad_override_codigo()
        interes_default = self._get_number_config(self.interes_default, "interes por defecto")
        return service.validar_cargue(
            Path(self.archivo_cliente.get()),
            header_row=header_row,
            data_start_row=data_start_row,
            mapping=mapping,
            interes_default=interes_default,
            periodicidad_override_codigo=periodicidad_override_codigo,
            correcciones=self._get_corrections_config(),
            decisiones_duplicados=self._get_duplicate_decisions(),
        )

    def _get_corrections_config(self):
        correcciones = {
            int(fila): dict(valores)
            for fila, valores in self.manual_preview_corrections.items()
            if valores
        }
        for fila, campos in self.correction_vars.items():
            valores = dict(correcciones.get(fila, {}))
            for campo, variable in campos.items():
                valores[campo] = variable.get()
            if valores:
                correcciones[fila] = valores
        for fila, variable in self.date_override_vars.items():
            value = self._normalize_date_text(variable.get())
            if not value:
                continue
            variable.set(value)
            valores = correcciones.setdefault(fila, {})
            valores["fecha_prox_pago"] = value
        return correcciones

    def _get_duplicate_decisions(self):
        decisiones = {}
        for documento, variable in self.duplicate_vars.items():
            if variable.get() == "Son creditos diferentes":
                decisiones[documento] = "creditos_diferentes"
        return decisiones

    def toggle_advanced(self):
        self.advanced_open = not self.advanced_open
        if self.advanced_open:
            self.advanced_frame.pack(fill="x", pady=(16, 0))
            self.advanced_button.text = "Ocultar avanzado"
        else:
            self.advanced_frame.pack_forget()
            self.advanced_button.text = "Avanzado"
        self.advanced_button._draw()

    def toggle_audit_panel(self):
        self.audit_open = not self.audit_open
        if self.audit_open:
            self.audit_frame.pack(fill="x")
            self.audit_button.text = "Ocultar datos"
        else:
            self.audit_frame.pack_forget()
            self.audit_button.text = "Datos del cargue"
        self.audit_button._draw()

    def _on_combobox_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"
