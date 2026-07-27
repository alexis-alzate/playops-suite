import contextlib
from datetime import datetime
from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import messagebox
import os

from app_procesos.config import APP_TITLE, BASE_DIR, LOGS_DIR, RESOURCE_DIR
from app_procesos.modules.procesos import service, validator
from app_procesos.shared.settings import load_settings, save_settings

from .theme import COLORS, FONT_BODY, FONT_BODY_BOLD, FONT_H2, FONT_MONO
from .widgets import RoundedButton


class QueueWriter:
    def __init__(self, output_queue, log_file=None):
        self.output_queue = output_queue
        self.log_file = log_file

    def write(self, text):
        if text:
            self.output_queue.put(text)
            if self.log_file:
                self.log_file.write(text)
                self.log_file.flush()

    def flush(self):
        pass


class ProcesosView(tk.Frame):
    def __init__(self, parent, running_label=None):
        super().__init__(parent, bg=COLORS["bg"])
        self.output_queue = queue.Queue()
        self.buttons = []
        self.is_running = False
        self.last_result_path = None
        self.last_log_path = None
        self.running_label = running_label
        self.status = tk.StringVar(value="Sin proceso activo")
        self._build()
        self.after(120, self._drain_output)

    def _build(self):
        body = tk.Frame(self, bg=COLORS["bg"])
        body.pack(fill="both", expand=True)

        sidebar = tk.Frame(body, bg=COLORS["panel"], width=280)
        sidebar.pack(side="left", fill="y", padx=(0, 18))
        sidebar.pack_propagate(False)

        tk.Frame(sidebar, bg=COLORS["accent"], height=3).pack(fill="x")
        tk.Label(
            sidebar,
            text="Acciones",
            bg=COLORS["panel"],
            fg=COLORS["text"],
            font=FONT_H2,
        ).pack(anchor="w", padx=20, pady=(22, 12))

        self._add_button(sidebar, "Probar instalacion", lambda: self._run_task("Probando instalacion", service.probar_instalacion), primary=True)
        self._add_button(sidebar, "Primera revision", lambda: self.run_revision("primera revision"))
        self._add_button(sidebar, "Segunda revision", lambda: self.run_revision("segunda revision"))
        self._add_button(sidebar, "Primera y segunda", self.run_both)
        self._add_button(sidebar, "Abrir ultimo resultado", self.open_last_result)
        self._add_button(sidebar, "Abrir ultimo log", self.open_last_log)
        self._add_button(sidebar, "Abrir carpeta", self.open_folder)
        self._add_button(sidebar, "Abrir manual", self.open_manual)

        tk.Frame(sidebar, bg=COLORS["panel"]).pack(fill="both", expand=True)
        status_box = tk.Frame(sidebar, bg=COLORS["panel_2"], padx=16, pady=14)
        status_box.pack(fill="x", padx=16, pady=16)
        tk.Label(
            status_box,
            text="Estado",
            bg=COLORS["panel_2"],
            fg=COLORS["muted"],
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w")
        tk.Label(
            status_box,
            textvariable=self.status,
            bg=COLORS["panel_2"],
            fg=COLORS["text"],
            font=FONT_BODY,
            wraplength=220,
            justify="left",
        ).pack(anchor="w", pady=(4, 0))

        console_panel = tk.Frame(body, bg=COLORS["panel"])
        console_panel.pack(side="left", fill="both", expand=True)

        tk.Frame(console_panel, bg=COLORS["line"], height=1).pack(fill="x")
        console_header = tk.Frame(console_panel, bg=COLORS["panel"])
        console_header.pack(fill="x", padx=20, pady=(18, 10))
        tk.Label(
            console_header,
            text="Salida del proceso",
            bg=COLORS["panel"],
            fg=COLORS["text"],
            font=("Segoe UI", 14, "bold"),
        ).pack(side="left")
        self._small_button(console_header, "Limpiar", self.clear_console).pack(side="right", ipadx=40)

        shell = tk.Frame(console_panel, bg=COLORS["line"], padx=1, pady=1)
        shell.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        text_frame = tk.Frame(shell, bg=COLORS["console"])
        text_frame.pack(fill="both", expand=True)
        self.console = tk.Text(
            text_frame,
            bg=COLORS["console"],
            fg=COLORS.get("console_text", COLORS["text"]),
            insertbackground=COLORS.get("console_text", COLORS["text"]),
            selectbackground="#1f6feb",
            relief="flat",
            font=FONT_MONO,
            wrap="word",
            padx=18,
            pady=18,
        )
        self.console.pack(side="left", fill="both", expand=True)
        scrollbar = tk.Scrollbar(text_frame, command=self.console.yview)
        scrollbar.pack(side="right", fill="y")
        self.console.configure(yscrollcommand=scrollbar.set)

        self._write("Soporte Playtech Help Desk listo.\n")
        self._write("Primero use 'Probar instalacion' en equipos nuevos.\n\n")

    def _add_button(self, parent, text, command, primary=False):
        button = RoundedButton(
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
            height=46,
            font=FONT_BODY_BOLD if primary else FONT_BODY,
        )
        button.pack(fill="x", padx=16, pady=6)
        self.buttons.append(button)

    def _small_button(self, parent, text, command):
        return RoundedButton(
            parent,
            text,
            command,
            bg=COLORS["panel_3"],
            fg=COLORS["text"],
            hover_bg="#2a4a5d",
            active_bg="#1a3342",
            disabled_bg=COLORS["disabled"],
            disabled_fg=COLORS["muted"],
            radius=13,
            height=40,
            font=("Segoe UI", 9, "bold"),
        )

    def _set_busy(self, busy, label=None):
        state = "disabled" if busy else "normal"
        for button in self.buttons:
            button.configure(state=state)
        text = label if busy and label else "Listo para ejecutar"
        if self.running_label is not None:
            self.running_label.set(text)
        self.status.set(label if busy and label else "Sin proceso activo")

    def _write(self, text):
        self.console.insert("end", text)
        self.console.see("end")

    def clear_console(self):
        self.console.delete("1.0", "end")

    def run_revision(self, revision):
        if not self._confirm_replace_if_exists([revision]):
            self._write(f"\nOperacion cancelada. Ya existia {revision} de hoy.\n")
            return
        self._run_task(f"Ejecutando {revision}", lambda: service.ejecutar_revision(revision))

    def run_both(self):
        if not self._confirm_replace_if_exists(["primera revision", "segunda revision"]):
            self._write("\nOperacion cancelada. Ya existia una revision de hoy.\n")
            return
        self._run_task("Ejecutando primera y segunda revision", service.ejecutar_primera_y_segunda)

    def _confirm_replace_if_exists(self, revisions):
        existing = []
        for revision in revisions:
            exists, path = validator.revision_ya_existe(datetime.now(), self._normalize_revision(revision))
            if exists:
                existing.append((self._normalize_revision(revision), path))
        if not existing:
            return True
        detalle = "\n\n".join(f"- {revision}:\n{path}" for revision, path in existing)
        return messagebox.askyesno(
            APP_TITLE,
            "La revision de hoy ya existe.\n\n"
            "Esto indica que probablemente ya fue realizada.\n\n"
            f"{detalle}\n\n"
            "Deseas reprocesar y reemplazar los archivos existentes?",
        )

    def _normalize_revision(self, revision):
        return {
            "primera revision": "primera revisión",
            "segunda revision": "segunda revisión",
        }.get(revision, revision)

    def _run_task(self, title, task):
        if self.is_running:
            messagebox.showwarning(APP_TITLE, "Ya hay un proceso en ejecucion.")
            return
        self._set_busy(True, title)
        self._write(f"\n=== {title} ===\n")
        threading.Thread(target=self._worker, args=(task, title), daemon=True).start()

    def _worker(self, task, title):
        self.is_running = True
        code = 0
        log_path = self._create_log_path(title)
        try:
            with open(log_path, "w", encoding="utf-8") as log_file:
                writer = QueueWriter(self.output_queue, log_file)
                with contextlib.redirect_stdout(writer), contextlib.redirect_stderr(writer):
                    result = task()
                if isinstance(result, tuple):
                    code = int(result[0] or 0)
                    self.last_result_path = result[1]
                    self._save_last_result_path(self.last_result_path)
                else:
                    code = int(result or 0)
        except Exception as error:
            self.output_queue.put(f"\n[ERROR] {error}\n")
            code = 1
        finally:
            self.last_log_path = log_path
            self.is_running = False
            self.output_queue.put(f"\n=== Finalizado: {title} | codigo {code} ===\n")
            self.output_queue.put(f"Log guardado en: {log_path}\n")
            self.output_queue.put(("__DONE__", code))

    def _create_log_path(self, title):
        LOGS_DIR.mkdir(exist_ok=True)
        safe_title = "".join(char if char.isalnum() else "_" for char in title.lower()).strip("_")
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        return LOGS_DIR / f"{timestamp}_{safe_title}.log"

    def _save_last_result_path(self, path):
        try:
            settings = load_settings()
            settings["last_monitor_result"] = str(path)
            save_settings(settings)
        except Exception:
            pass

    def _drain_output(self):
        try:
            while True:
                item = self.output_queue.get_nowait()
                if isinstance(item, tuple) and item[0] == "__DONE__":
                    self._set_busy(False)
                    self.status.set("Finalizado correctamente" if item[1] == 0 else "Finalizado con avisos/error")
                else:
                    self._write(item)
        except queue.Empty:
            pass
        self.after(120, self._drain_output)

    def open_last_result(self):
        if self.last_result_path and Path(self.last_result_path).is_dir():
            os.startfile(self.last_result_path)
            return
        messagebox.showinfo(APP_TITLE, "Todavia no hay un resultado disponible para abrir.")

    def open_last_log(self):
        if self.last_log_path and Path(self.last_log_path).exists():
            os.startfile(self.last_log_path)
            return
        messagebox.showinfo(APP_TITLE, "Todavia no hay un log disponible para abrir.")

    def open_folder(self):
        os.startfile(BASE_DIR)

    def open_manual(self):
        manual = RESOURCE_DIR / "MANUAL_EQUIPO.html"
        if manual.exists():
            os.startfile(manual)
        else:
            messagebox.showwarning(APP_TITLE, "No se encontro MANUAL_EQUIPO.html.")
