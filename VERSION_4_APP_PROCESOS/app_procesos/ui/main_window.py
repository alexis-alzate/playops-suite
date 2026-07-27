from datetime import datetime
import tkinter as tk
from tkinter import messagebox

from app_procesos.config import APP_TITLE, APP_VERSION, LOGO_ICO, LOGO_PNG
from app_procesos.shared.settings import load_settings, save_settings
from app_procesos.shared.updater import check_for_update, launch_update

from .cargue_rutas_view import CargueRutasView
from .dashboard_view import DashboardView
from .procesos_view import ProcesosView
from .theme import COLORS, FONT_BODY, FONT_BODY_BOLD, get_theme, get_theme_accent, get_theme_options, set_theme
from .widgets import RoundedButton


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        set_theme(load_settings().get("ui_theme", "dark"))
        self.title(APP_TITLE)
        self.geometry("1280x800")
        self.minsize(1100, 700)
        self.configure(bg=COLORS["bg"])
        self.logo_image = None
        self.about_logo_image = None
        self.logo_anim_job = None
        self.logo_anim_step = 0
        self.skin_hover = False
        self.skin_popup = None
        self.skin_menu_open = False
        self.skin_menu_button = None
        self.skin_menu_frame = None
        self.drawer_open = False
        self.control_menu_open = False
        self.control_menu_frame = None
        self.control_menu_button = None
        self.current_view = "procesos"
        self.running_label = tk.StringVar(value="Listo para ejecutar")
        self.clock_label = tk.StringVar(value="")
        self.clock_job = None
        self.views = {}
        self.update_prompt_shown = False

        self._set_icon()
        self._build()
        self.show_view(self.current_view)
        self.after(2500, self._check_updates_on_startup)

    def _set_icon(self):
        try:
            if LOGO_ICO.exists():
                self.iconbitmap(str(LOGO_ICO))
        except Exception:
            pass

    def _build(self):
        tk.Frame(self, bg=COLORS["accent"], height=3).pack(fill="x")

        header = tk.Frame(self, bg=COLORS["bg"])
        header.pack(fill="x", padx=30, pady=(24, 14))

        logo_box = tk.Frame(header, bg=COLORS["bg"])
        logo_box.pack(side="left", fill="x", expand=True)

        logo_slot = tk.Canvas(
            logo_box,
            width=96,
            height=96,
            bg=COLORS["bg"],
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        logo_slot.pack(side="left", padx=(0, 22))
        self.logo_canvas = logo_slot
        self._draw_logo(logo_slot, progress=0)
        logo_slot.bind("<Button-1>", lambda _event: self.show_about())
        logo_slot.bind("<Enter>", lambda _event: self._animate_logo(1))
        logo_slot.bind("<Leave>", lambda _event: self._animate_logo(0))

        title_box = tk.Frame(logo_box, bg=COLORS["bg"])
        title_box.pack(side="left", fill="x", expand=True)
        tk.Label(
            title_box,
            text="SOPORTE PLAYTECH",
            bg=COLORS["bg"],
            fg=COLORS["accent_2"],
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w")
        tk.Label(
            title_box,
            text="PlayOps Suite",
            bg=COLORS["bg"],
            fg=COLORS["text"],
            font=("Segoe UI", 25, "bold"),
        ).pack(anchor="w", pady=(2, 0))
        slogan_row = tk.Frame(title_box, bg=COLORS["bg"])
        slogan_row.pack(anchor="w", pady=(6, 0))
        tk.Frame(
            slogan_row,
            bg=COLORS["accent"],
            width=34,
            height=2,
        ).pack(side="left", padx=(0, 10), pady=(9, 0))
        tk.Label(
            slogan_row,
            text="Apostamos por la tecnologia",
            bg=COLORS["bg"],
            fg=COLORS["muted"],
            font=("Segoe UI", 10, "italic"),
        ).pack(side="left")

        header_actions = tk.Frame(header, bg=COLORS["bg"])
        header_actions.pack(side="right", anchor="n")

        top_actions = tk.Frame(header_actions, bg=COLORS["bg"])
        top_actions.pack(anchor="e")
        skin_slot = tk.Frame(top_actions, bg=COLORS["bg"], width=58, height=42)
        skin_slot.pack(side="left", padx=(0, 10))
        skin_slot.pack_propagate(False)
        self.skin_canvas = self._create_skin_canvas(skin_slot)
        self.skin_canvas.place(relx=0.5, rely=0.5, anchor="center")
        update_button = RoundedButton(
            top_actions,
            "Actualizar",
            self.check_updates_manually,
            bg=COLORS["panel_2"],
            fg=COLORS["text"],
            hover_bg=COLORS["panel_3"],
            active_bg=COLORS["accent_active"],
            disabled_bg=COLORS["disabled"],
            disabled_fg=COLORS["muted"],
            radius=13,
            height=38,
            width=112,
            font=("Segoe UI", 9, "bold"),
        )
        update_button.pack(side="left", padx=(0, 10))
        about_button = RoundedButton(
            top_actions,
            "Acerca de",
            self.show_about,
            bg=COLORS["panel_2"],
            fg=COLORS["text"],
            hover_bg=COLORS["panel_3"],
            active_bg=COLORS["accent_active"],
            disabled_bg=COLORS["disabled"],
            disabled_fg=COLORS["muted"],
            radius=13,
            height=38,
            width=112,
            font=("Segoe UI", 9, "bold"),
        )
        about_button.pack(side="left", padx=(0, 10))
        menu_slot = tk.Frame(top_actions, bg=COLORS["bg"], width=42, height=42)
        menu_slot.pack(side="left")
        menu_slot.pack_propagate(False)
        self.menu_button = self._create_hamburger_button(menu_slot)
        self.menu_button.place(x=0, y=0)

        self._tick_clock()

        self.body = tk.Frame(self, bg=COLORS["bg"])
        self.body.pack(fill="both", expand=True, padx=30, pady=(8, 28))

        self.content = tk.Frame(self.body, bg=COLORS["bg"])
        self.content.pack(fill="both", expand=True)

        self.views = {
            "procesos": ProcesosView(self.content, running_label=self.running_label),
            "dashboard": DashboardView(self.content),
            "cargue_rutas": CargueRutasView(self.content),
        }
        for view in self.views.values():
            view.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.drawer = tk.Frame(self, bg=COLORS["panel"], width=310)
        self.drawer.place_forget()
        self.drawer.pack_propagate(False)
        self._build_drawer()

    def _build_drawer(self):
        tk.Frame(self.drawer, bg=COLORS["accent"], height=3).pack(fill="x")
        header = tk.Frame(self.drawer, bg=COLORS["panel"])
        header.pack(fill="x", padx=18, pady=(18, 12))
        tk.Label(
            header,
            text="PlayOps Suite",
            bg=COLORS["panel"],
            fg=COLORS["text"],
            font=("Segoe UI", 15, "bold"),
        ).pack(side="left")
        close_btn = RoundedButton(
            header,
            "×",
            self.toggle_drawer,
            bg=COLORS["panel_2"],
            fg=COLORS["text"],
            hover_bg=COLORS["panel_3"],
            active_bg="#142734",
            disabled_bg=COLORS["disabled"],
            disabled_fg=COLORS["muted"],
            radius=12,
            height=36,
            font=("Segoe UI", 14, "bold"),
        )
        close_btn.pack(side="right", ipadx=14)

        self._drawer_button("Monitoreo procesos LISTO", "procesos")
        self._drawer_button("Dashboard", "dashboard")
        self._drawer_button("Cargue de rutas", "cargue_rutas")
        self._control_menu()
        self._theme_picker()

        tk.Frame(self.drawer, bg=COLORS["panel"]).pack(fill="both", expand=True)
        tk.Label(
            self.drawer,
            text="Menu modular",
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w", padx=18, pady=(0, 18))

    def _drawer_button(self, text, view_name):
        button = RoundedButton(
            self.drawer,
            text,
            lambda name=view_name: self._select_from_drawer(name),
            bg=COLORS["panel_2"],
            fg=COLORS["text"],
            hover_bg=COLORS["panel_3"],
            active_bg="#142734",
            disabled_bg=COLORS["disabled"],
            disabled_fg=COLORS["muted"],
            radius=14,
            height=46,
            font=FONT_BODY_BOLD,
        )
        button.pack(fill="x", padx=18, pady=6)

    def _control_menu(self):
        self.control_menu_button = RoundedButton(
            self.drawer,
            "Centro de control  +",
            self._toggle_control_menu,
            bg=COLORS["panel_2"],
            fg=COLORS["text"],
            hover_bg=COLORS["panel_3"],
            active_bg="#142734",
            disabled_bg=COLORS["disabled"],
            disabled_fg=COLORS["muted"],
            radius=14,
            height=44,
            font=FONT_BODY_BOLD,
        )
        self.control_menu_button.pack(fill="x", padx=18, pady=(16, 6))
        self.control_menu_frame = tk.Frame(self.drawer, bg=COLORS["panel"])

        self._dashboard_section_button("Historial operativo", "historial", parent=self.control_menu_frame)
        self._dashboard_section_button("Visor de logs", "logs", parent=self.control_menu_frame)
        self._dashboard_section_button("Configuracion", "configuracion", parent=self.control_menu_frame)
        self._dashboard_section_button("Teams", "teams", parent=self.control_menu_frame)
        self._dashboard_section_button("Diagnostico", "diagnostico", parent=self.control_menu_frame)
        self._dashboard_section_button("Actualizaciones", "actualizaciones", parent=self.control_menu_frame)
        self._dashboard_section_button("Acerca de la app", "acerca", parent=self.control_menu_frame)

    def _toggle_control_menu(self):
        self.control_menu_open = not self.control_menu_open
        if self.control_menu_frame is None:
            return
        if self.control_menu_open:
            self.control_menu_frame.pack(fill="x", padx=0, pady=(0, 8), after=self.control_menu_button)
        else:
            self.control_menu_frame.pack_forget()
        if self.control_menu_button is not None:
            self.control_menu_button.text = "Centro de control  -" if self.control_menu_open else "Centro de control  +"
            self.control_menu_button._draw()

    def _dashboard_section_button(self, text, section, parent=None):
        parent = parent or self.drawer
        button = RoundedButton(
            parent,
            text,
            lambda name=section: self._select_dashboard_section(name),
            bg=COLORS["panel_2"],
            fg=COLORS["text"],
            hover_bg=COLORS["panel_3"],
            active_bg="#142734",
            disabled_bg=COLORS["disabled"],
            disabled_fg=COLORS["muted"],
            radius=14,
            height=40,
            font=FONT_BODY,
        )
        button.pack(fill="x", padx=30, pady=3)

    def _theme_picker(self):
        self.skin_menu_button = RoundedButton(
            self.drawer,
            "Skins  +",
            self._toggle_drawer_skin_panel,
            bg=COLORS["panel_2"],
            fg=COLORS["text"],
            hover_bg=COLORS["panel_3"],
            active_bg=COLORS["accent_active"],
            disabled_bg=COLORS["disabled"],
            disabled_fg=COLORS["muted"],
            radius=14,
            height=46,
            font=FONT_BODY_BOLD,
        )
        self.skin_menu_button.pack(fill="x", padx=18, pady=(18, 6))

        self.skin_menu_frame = tk.Frame(self.drawer, bg=COLORS["panel"])

    def _toggle_drawer_skin_panel(self):
        self.skin_menu_open = not self.skin_menu_open
        if self.skin_menu_frame is None:
            return
        if self.skin_menu_open:
            self._build_drawer_skin_panel()
            self.skin_menu_frame.pack(fill="x", padx=18, pady=(0, 8), after=self.skin_menu_button)
        else:
            self.skin_menu_frame.pack_forget()
        if self.skin_menu_button is not None:
            self.skin_menu_button.text = "Skins  -" if self.skin_menu_open else "Skins  +"
            self.skin_menu_button._draw()

    def _build_drawer_skin_panel(self):
        if self.skin_menu_frame is None:
            return
        for child in self.skin_menu_frame.winfo_children():
            child.destroy()

        panel = tk.Frame(self.skin_menu_frame, bg=COLORS["panel_2"], padx=12, pady=12)
        panel.pack(fill="x")
        tk.Label(
            panel,
            text="Selecciona el estilo visual",
            bg=COLORS["panel_2"],
            fg=COLORS["accent_2"],
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w", pady=(0, 8))

        for theme_name, label in get_theme_options():
            selected = theme_name == get_theme()
            row_bg = COLORS["accent"] if selected else COLORS["panel"]
            row = tk.Frame(panel, bg=row_bg, padx=10, pady=9, cursor="hand2")
            row.pack(fill="x", pady=4)

            dot = tk.Canvas(row, width=24, height=24, bg=row_bg, highlightthickness=0, bd=0, cursor="hand2")
            dot.pack(side="left", padx=(0, 10))
            accent = get_theme_accent(theme_name)
            dot.create_oval(3, 3, 21, 21, fill=accent, outline="white" if selected else COLORS["line"], width=2)

            text = tk.Label(
                row,
                text=label,
                bg=row_bg,
                fg="white" if selected else COLORS["text"],
                font=FONT_BODY_BOLD,
                cursor="hand2",
            )
            text.pack(side="left", fill="x", expand=True)

            state = tk.Label(
                row,
                text="Activo" if selected else "Aplicar",
                bg=row_bg,
                fg="white" if selected else COLORS["muted"],
                font=("Segoe UI", 8, "bold"),
                cursor="hand2",
            )
            state.pack(side="right")

            def select_theme(_event=None, name=theme_name):
                self.switch_theme(name)

            for widget in (row, dot, text, state):
                widget.bind("<Button-1>", select_theme)

    def _create_skin_canvas(self, parent):
        canvas = tk.Canvas(
            parent,
            width=58,
            height=46,
            bg=COLORS["bg"],
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )

        def enter(_event):
            self.skin_hover = True
            self._draw_skin_canvas(canvas)

        def leave(_event):
            self.skin_hover = False
            self._draw_skin_canvas(canvas)

        def press(_event):
            canvas._pressed = True
            self._draw_skin_canvas(canvas)

        def release(event):
            inside = 0 <= event.x <= canvas.winfo_width() and 0 <= event.y <= canvas.winfo_height()
            canvas._pressed = False
            self._draw_skin_canvas(canvas)
            if inside:
                self._cycle_theme()

        canvas._pressed = False
        canvas.bind("<Enter>", enter)
        canvas.bind("<Leave>", leave)
        canvas.bind("<ButtonPress-1>", press)
        canvas.bind("<ButtonRelease-1>", release)
        canvas.bind("<Configure>", lambda _event: self._draw_skin_canvas(canvas))
        self._draw_skin_canvas(canvas)
        return canvas

    def _draw_skin_canvas(self, canvas):
        canvas.delete("all")
        width = max(canvas.winfo_width(), 58)
        height = max(canvas.winfo_height(), 46)
        pressed = bool(getattr(canvas, "_pressed", False))
        fill = COLORS["panel_3"] if self.skin_hover else COLORS["panel_2"]
        if pressed:
            fill = COLORS["accent_active"]
        offset = 1 if pressed else 0

        shadow = "#05090d" if get_theme() != "light" else "#d7e3eb"
        self._rounded_rect(canvas, 4, 5 + offset, width - 2, height - 1 + offset, 16, fill=shadow, outline="")
        self._rounded_rect(canvas, 2, 2 + offset, width - 4, height - 4 + offset, 15, fill=fill, outline=COLORS["line"])

        palette_x = 22
        palette_y = 23 + offset
        canvas.create_oval(
            palette_x - 15,
            palette_y - 14,
            palette_x + 14,
            palette_y + 14,
            fill=COLORS["panel"],
            outline=COLORS["accent"],
            width=2,
        )
        canvas.create_oval(
            palette_x + 5,
            palette_y - 11,
            palette_x + 13,
            palette_y - 3,
            fill=fill,
            outline=fill,
        )

        options = get_theme_options()
        current = get_theme()
        dot_positions = [(14, 18), (20, 13), (28, 16), (17, 28), (27, 29)]
        for index, (theme_name, _label) in enumerate(options[:5]):
            x, y = dot_positions[index]
            y += offset
            accent = get_theme_accent(theme_name)
            radius = 3
            if theme_name == current:
                canvas.create_oval(x - 6, y - 6, x + 6, y + 6, fill="", outline=COLORS["text"], width=1.5)
                radius = 3.5
            canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill=accent, outline="")

        brush_color = COLORS["accent_hover"] if self.skin_hover else COLORS["accent"]
        canvas.create_line(33, 32 + offset, 48, 15 + offset, fill=COLORS["muted"], width=5, capstyle="round")
        canvas.create_line(34, 31 + offset, 49, 14 + offset, fill=brush_color, width=2.4, capstyle="round")
        canvas.create_polygon(
            46,
            12 + offset,
            53,
            9 + offset,
            50,
            17 + offset,
            fill=COLORS["text"],
            outline="",
        )

    def _cycle_theme(self):
        options = [name for name, _label in get_theme_options()]
        current_index = options.index(get_theme()) if get_theme() in options else 0
        self.switch_theme(options[(current_index + 1) % len(options)])

    def _toggle_skin_menu(self):
        if self.skin_popup is not None and self.skin_popup.winfo_exists():
            self._hide_skin_menu()
            return
        self._show_skin_menu()

    def _hide_skin_menu(self):
        if self.skin_popup is not None and self.skin_popup.winfo_exists():
            self.skin_popup.destroy()
        self.skin_popup = None

    def _show_skin_menu(self):
        self._hide_skin_menu()
        popup = tk.Frame(self, bg=COLORS["accent"], padx=1, pady=1)
        shell = tk.Frame(popup, bg=COLORS["panel"], padx=12, pady=10)
        shell.pack(fill="both", expand=True)
        self.skin_popup = popup

        header = tk.Frame(shell, bg=COLORS["panel"])
        header.pack(fill="x", pady=(0, 8))
        tk.Label(
            header,
            text="Skins",
            bg=COLORS["panel"],
            fg=COLORS["accent_2"],
            font=("Segoe UI", 9, "bold"),
        ).pack(side="left")
        tk.Label(
            header,
            text="Elige un color",
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=("Segoe UI", 8),
        ).pack(side="right")

        for theme_name, label in get_theme_options():
            selected = theme_name == get_theme()
            row_bg = COLORS["panel_2"] if selected else COLORS["panel"]
            row = tk.Frame(shell, bg=row_bg, padx=8, pady=6, cursor="hand2")
            row.pack(fill="x", pady=3)

            dot = tk.Canvas(row, width=20, height=20, bg=row_bg, highlightthickness=0, bd=0, cursor="hand2")
            dot.pack(side="left", padx=(0, 8))
            accent = get_theme_accent(theme_name)
            dot.create_oval(3, 3, 17, 17, fill=accent, outline=COLORS["text"] if selected else "")

            text = tk.Label(
                row,
                text=label,
                bg=row_bg,
                fg=COLORS["text"],
                font=FONT_BODY_BOLD if selected else FONT_BODY,
                cursor="hand2",
            )
            text.pack(side="left", fill="x", expand=True)

            active = tk.Label(
                row,
                text="Activo" if selected else "",
                bg=row_bg,
                fg=COLORS["accent_2"],
                font=("Segoe UI", 8, "bold"),
            )
            active.pack(side="right")

            def select_theme(_event=None, name=theme_name):
                self._hide_skin_menu()
                self.switch_theme(name)

            for widget in (row, dot, text, active):
                widget.bind("<Button-1>", select_theme)

        self.update_idletasks()
        x = self.skin_canvas.winfo_rootx() - self.winfo_rootx() - 82
        y = self.skin_canvas.winfo_rooty() - self.winfo_rooty() + self.skin_canvas.winfo_height() + 8
        x = max(18, min(x, self.winfo_width() - 238))
        popup.place(x=x, y=y, width=220)
        popup.tkraise()

    def switch_theme(self, theme_name=None):
        if theme_name == get_theme():
            return
        view_name = self.current_view
        view_state = self._collect_view_state()
        running_text = self.running_label.get()
        if theme_name:
            set_theme(theme_name)
        else:
            options = [name for name, _label in get_theme_options()]
            current_index = options.index(get_theme()) if get_theme() in options else 0
            set_theme(options[(current_index + 1) % len(options)])
        save_settings({"ui_theme": get_theme()})
        if self.clock_job:
            self.after_cancel(self.clock_job)
            self.clock_job = None
        for child in self.winfo_children():
            child.destroy()
        self.configure(bg=COLORS["bg"])
        self.logo_image = None
        self.about_logo_image = None
        self.logo_anim_job = None
        self.logo_anim_step = 0
        self.skin_hover = False
        self.skin_popup = None
        self.skin_menu_open = False
        self.skin_menu_button = None
        self.skin_menu_frame = None
        self.drawer_open = False
        self.running_label = tk.StringVar(value=running_text)
        self.clock_label = tk.StringVar(value="")
        self.views = {}
        self._build()
        self._restore_view_state(view_state)
        self.show_view(view_name)

    def _tick_clock(self):
        self.clock_label.set(datetime.now().strftime("%Y-%m-%d  %H:%M:%S"))
        self.clock_job = self.after(1000, self._tick_clock)

    def _collect_view_state(self):
        state = {}
        for name, view in self.views.items():
            exporter = getattr(view, "export_state", None)
            if callable(exporter):
                state[name] = exporter()
        return state

    def _restore_view_state(self, state):
        for name, data in state.items():
            view = self.views.get(name)
            importer = getattr(view, "restore_state", None)
            if view is not None and callable(importer):
                importer(data)

    def toggle_drawer(self):
        if self.drawer_open:
            self.drawer.place_forget()
            self.drawer_open = False
            if hasattr(self, "menu_button"):
                self.menu_button.event_generate("<Leave>")
            return

        self.drawer.place(x=0, y=3, width=310, relheight=1)
        self.drawer.tkraise()
        self.drawer_open = True
        if hasattr(self, "menu_button"):
            self.menu_button.event_generate("<Enter>")

    def _select_from_drawer(self, name):
        self.show_view(name)
        self.toggle_drawer()

    def _select_dashboard_section(self, section):
        self.show_view("dashboard")
        dashboard = self.views.get("dashboard")
        if dashboard and hasattr(dashboard, "show_section"):
            dashboard.show_section(section)
        self.toggle_drawer()

    def show_view(self, name):
        view = self.views.get(name)
        if view:
            self.current_view = name
            view.tkraise()

    def _check_updates_on_startup(self):
        if self.update_prompt_shown:
            return
        try:
            info = check_for_update()
        except Exception:
            return
        if not info.available:
            return
        self.update_prompt_shown = True
        self._show_update_prompt(info)

    def check_updates_manually(self):
        try:
            info = check_for_update()
        except Exception as error:
            messagebox.showerror("Actualizaciones", f"No se pudo consultar la actualizacion:\n\n{error}")
            return

        if info.available:
            self.update_prompt_shown = True
            self._show_update_prompt(info)
            return

        manifest = str(info.manifest_path) if info.manifest_path else "No encontrado"
        messagebox.showinfo(
            "Actualizaciones",
            f"{info.message}\n\n"
            f"Version instalada: {info.current_version}\n"
            f"Version publicada: {info.latest_version}\n\n"
            f"Manifiesto:\n{manifest}",
        )

    def _show_update_prompt(self, info):
        modal = tk.Toplevel(self)
        modal.title("Actualizacion disponible")
        try:
            if LOGO_ICO.exists():
                modal.iconbitmap(str(LOGO_ICO))
        except Exception:
            pass
        modal.configure(bg=COLORS["accent"])
        modal.resizable(False, False)
        modal.transient(self)
        modal.grab_set()

        width = 600
        height = 430
        x = self.winfo_rootx() + max((self.winfo_width() - width) // 2, 0)
        y = self.winfo_rooty() + max((self.winfo_height() - height) // 2, 0)
        modal.geometry(f"{width}x{height}+{x}+{y}")

        shell = tk.Frame(modal, bg=COLORS["panel"], padx=30, pady=28)
        shell.pack(fill="both", expand=True, padx=1, pady=1)
        shell.grid_columnconfigure(0, weight=1)
        shell.grid_rowconfigure(2, weight=1)

        tk.Label(
            shell,
            text="Nueva actualizacion disponible",
            bg=COLORS["panel"],
            fg=COLORS["text"],
            font=("Segoe UI", 20, "bold"),
        ).grid(row=0, column=0, sticky="w")
        tk.Label(
            shell,
            text=(
                "Hay una version mas reciente de PlayOps Suite. "
                "La app se cerrara, mostrara el progreso de actualizacion y se abrira de nuevo al finalizar."
            ),
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=FONT_BODY,
            wraplength=520,
            justify="left",
        ).grid(row=1, column=0, sticky="ew", pady=(10, 16))

        info_box = tk.Frame(shell, bg=COLORS["panel_2"], padx=16, pady=14)
        info_box.grid(row=2, column=0, sticky="nsew")
        info_box.grid_columnconfigure(1, weight=1)
        for label, value in (
            ("Version instalada", info.current_version),
            ("Version nueva", info.latest_version),
            ("Detalle", info.message),
        ):
            row = tk.Frame(info_box, bg=COLORS["panel_2"])
            row.pack(fill="x", pady=4)
            tk.Label(
                row,
                text=f"{label}:",
                bg=COLORS["panel_2"],
                fg=COLORS["accent_2"],
                font=("Segoe UI", 9, "bold"),
                width=18,
                anchor="w",
            ).pack(side="left")
            tk.Label(
                row,
                text=value,
                bg=COLORS["panel_2"],
                fg=COLORS["text"],
                font=FONT_BODY,
                anchor="w",
                wraplength=340,
                justify="left",
            ).pack(side="left", fill="x", expand=True)

        actions = tk.Frame(shell, bg=COLORS["panel"])
        actions.grid(row=3, column=0, sticky="ew", pady=(22, 0))

        def update_now():
            try:
                if info.installer_path is None:
                    raise FileNotFoundError("El version.json no define el instalador.")
                launch_update(info.installer_path)
            except Exception as error:
                modal.destroy()
                messagebox.showerror("Actualizacion", f"No se pudo iniciar la actualizacion:\n\n{error}")
                return
            modal.destroy()
            self.after(300, self.destroy)

        button_row = tk.Frame(actions, bg=COLORS["panel"])
        button_row.pack(anchor="center")
        RoundedButton(
            button_row,
            "Actualizar ahora",
            update_now,
            bg=COLORS["accent"],
            fg="white",
            hover_bg=COLORS["accent_hover"],
            active_bg=COLORS["accent_active"],
            disabled_bg=COLORS["disabled"],
            disabled_fg=COLORS["muted"],
            radius=14,
            height=52,
            width=178,
            font=("Segoe UI", 10, "bold"),
        ).pack(side="left", padx=(0, 16))
        RoundedButton(
            button_row,
            "Despues",
            modal.destroy,
            bg=COLORS["panel_2"],
            fg=COLORS["text"],
            hover_bg=COLORS["panel_3"],
            active_bg="#142734",
            disabled_bg=COLORS["disabled"],
            disabled_fg=COLORS["muted"],
            radius=14,
            height=52,
            width=138,
            font=FONT_BODY_BOLD,
        ).pack(side="left")

    def _animate_logo(self, target):
        if not hasattr(self, "logo_canvas") or not self.logo_canvas.winfo_exists():
            return
        if self.logo_anim_job:
            self.after_cancel(self.logo_anim_job)
            self.logo_anim_job = None

        direction = 1 if target > self.logo_anim_step else -1

        def tick():
            self.logo_anim_step = max(0, min(8, self.logo_anim_step + direction))
            self._draw_logo(self.logo_canvas, progress=self.logo_anim_step / 8)
            if (direction > 0 and self.logo_anim_step < 8) or (direction < 0 and self.logo_anim_step > 0):
                self.logo_anim_job = self.after(14, tick)
            else:
                self.logo_anim_job = None

        tick()

    def _draw_logo(self, canvas, progress=0):
        canvas.delete("all")
        canvas.configure(bg=COLORS["bg"])
        pad = 7 - (4 * progress)
        inner_pad = 12 - (3 * progress)
        glow_pad = 13 - (9 * progress)
        outline = COLORS["accent"] if progress > 0.2 else "#e8f0f7"
        width = 1 + int(2 * progress)
        if progress > 0:
            canvas.create_oval(
                glow_pad,
                glow_pad,
                96 - glow_pad,
                96 - glow_pad,
                fill="",
                outline=COLORS["accent"],
                width=max(1, int(2 * progress)),
            )
        canvas.create_oval(pad, pad, 96 - pad, 96 - pad, fill="#f8fbff", outline=outline, width=width)
        canvas.create_oval(inner_pad, inner_pad, 96 - inner_pad, 96 - inner_pad, fill="#ffffff", outline="")
        if LOGO_PNG.exists():
            try:
                if self.logo_image is None:
                    self.logo_image = tk.PhotoImage(file=str(LOGO_PNG)).subsample(8, 8)
                offset = -1 if progress > 0.5 else 0
                canvas.create_image(48, 48 + offset, image=self.logo_image)
                return
            except Exception:
                self.logo_image = None
        canvas.create_text(48, 48, text="Play", fill=COLORS["accent"], font=("Segoe UI", 11, "bold"))

    def show_about(self):
        modal = tk.Toplevel(self)
        modal.title("Acerca de")
        try:
            if LOGO_ICO.exists():
                modal.iconbitmap(str(LOGO_ICO))
        except Exception:
            pass
        modal.configure(bg=COLORS["bg"])
        modal.resizable(False, False)
        modal.transient(self)
        modal.grab_set()

        width = 560
        height = 540
        x = self.winfo_rootx() + max((self.winfo_width() - width) // 2, 0)
        y = self.winfo_rooty() + max((self.winfo_height() - height) // 2, 0)
        modal.geometry(f"{width}x{height}+{x}+{y}")

        container = tk.Frame(modal, bg=COLORS["panel"], padx=34, pady=30)
        container.pack(fill="both", expand=True, padx=1, pady=1)

        brand = tk.Frame(container, bg=COLORS["panel"])
        brand.pack(fill="x")
        logo_canvas = tk.Canvas(
            brand,
            width=92,
            height=92,
            bg=COLORS["panel"],
            highlightthickness=0,
            bd=0,
        )
        logo_canvas.pack(side="left", padx=(0, 18))
        if LOGO_PNG.exists():
            try:
                self.about_logo_image = tk.PhotoImage(file=str(LOGO_PNG)).subsample(8, 8)
                logo_canvas.create_oval(7, 7, 85, 85, fill="#f8fbff", outline="#e8f0f7", width=1)
                logo_canvas.create_oval(13, 13, 79, 79, fill="#ffffff", outline="")
                logo_canvas.create_image(46, 46, image=self.about_logo_image)
            except Exception:
                logo_canvas.create_text(46, 46, text="Playtech", fill=COLORS["text"], font=("Segoe UI", 12, "bold"))

        brand_text = tk.Frame(brand, bg=COLORS["panel"])
        brand_text.pack(side="left", fill="x", expand=True)
        tk.Label(
            brand_text,
            text="PlayOps Suite",
            bg=COLORS["panel"],
            fg=COLORS["text"],
            font=("Segoe UI", 26, "bold"),
            anchor="w",
        ).pack(anchor="w")
        tk.Label(
            brand_text,
            text="Automatizacion operativa interna",
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=("Segoe UI", 10, "bold"),
            anchor="w",
        ).pack(anchor="w", pady=(2, 0))
        tk.Label(
            brand_text,
            text="Apostamos por la tecnologia",
            bg=COLORS["panel"],
            fg=COLORS["accent_2"],
            font=("Segoe UI", 11, "italic"),
            anchor="w",
        ).pack(anchor="w", pady=(6, 0))
        tk.Frame(brand_text, bg=COLORS["accent"], height=2, width=72).pack(anchor="w", pady=(12, 0))

        info = tk.Frame(container, bg=COLORS["panel_2"], padx=20, pady=18)
        info.pack(fill="x", pady=(26, 16))
        rows = [
            ("Desarrollado por", "Victor Alexis Alzate Cortes"),
            ("Version", APP_VERSION),
            ("Fecha y hora", self.clock_label.get() or datetime.now().strftime("%Y-%m-%d  %H:%M:%S")),
            ("Area responsable", "Soporte Playtech"),
            ("Empresa", "PLAY TECHNOLOGIES S.A.S."),
        ]
        for label, value in rows:
            row = tk.Frame(info, bg=COLORS["panel_2"])
            row.pack(fill="x", pady=5)
            tk.Label(
                row,
                text=f"{label}:",
                bg=COLORS["panel_2"],
                fg=COLORS["accent_2"],
                font=("Segoe UI", 9, "bold"),
                width=18,
                anchor="w",
            ).pack(side="left")
            tk.Label(
                row,
                text=value,
                bg=COLORS["panel_2"],
                fg=COLORS["text"],
                font=("Segoe UI", 10),
                anchor="w",
                wraplength=310,
                justify="left",
            ).pack(side="left", fill="x", expand=True)

        modules = tk.Frame(container, bg=COLORS["panel"])
        modules.pack(fill="x", pady=(2, 14))
        tk.Label(
            modules,
            text="Modulos activos",
            bg=COLORS["panel"],
            fg=COLORS["accent_2"],
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", pady=(0, 8))
        chip_row = tk.Frame(modules, bg=COLORS["panel"])
        chip_row.pack(fill="x")
        for text in ("Monitoreo LISTO", "Cargue de rutas", "Bitacoras"):
            chip = tk.Frame(chip_row, bg=COLORS["panel_3"], padx=15, pady=8)
            chip.pack(side="left", padx=(0, 10), pady=(0, 4))
            tk.Label(
                chip,
                text=text,
                bg=COLORS["panel_3"],
                fg=COLORS["text"],
                font=("Segoe UI", 9, "bold"),
            ).pack()

        tk.Label(
            container,
            text="Suite interna para automatizar procesos operativos, validar informacion y dejar evidencia trazable para el equipo de soporte.",
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=("Segoe UI", 10),
            wraplength=460,
            justify="center",
        ).pack(pady=(4, 20))

        close_button = RoundedButton(
            container,
            "Cerrar",
            modal.destroy,
            bg=COLORS["accent"],
            fg="white",
            hover_bg=COLORS["accent_hover"],
            active_bg=COLORS["accent_active"],
            disabled_bg=COLORS["disabled"],
            disabled_fg=COLORS["muted"],
            radius=14,
            height=42,
            font=FONT_BODY_BOLD,
        )
        close_button.pack(anchor="center", ipadx=45)
        modal.bind("<Escape>", lambda _event: modal.destroy())

    def _create_hamburger_button(self, parent):
        canvas = tk.Canvas(
            parent,
            width=42,
            height=42,
            bg=COLORS["bg"],
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        canvas._fill = COLORS["panel_2"]
        canvas._hover = False
        canvas._pressed = False

        def draw():
            canvas.delete("all")
            fill = COLORS["panel_3"] if canvas._hover else COLORS["panel_2"]
            outline = COLORS["accent"] if self.drawer_open or canvas._hover else COLORS["line"]
            if canvas._pressed:
                fill = COLORS["accent_active"]
            y_offset = 1 if canvas._pressed else 0

            self._rounded_rect(canvas, 4, 5 + y_offset, 38, 39 + y_offset, 13, fill="#061018", outline="")
            self._rounded_rect(canvas, 3, 3 + y_offset, 37, 37 + y_offset, 12, fill=fill, outline=outline)
            canvas.create_oval(8, 8 + y_offset, 15, 15 + y_offset, fill=COLORS["accent"], outline="")

            line_color = "white" if canvas._pressed else COLORS["text"]
            if self.drawer_open:
                canvas.create_line(14, 14 + y_offset, 28, 28 + y_offset, fill=line_color, width=2, capstyle="round")
                canvas.create_line(28, 14 + y_offset, 14, 28 + y_offset, fill=line_color, width=2, capstyle="round")
            else:
                for index, y in enumerate((15, 21, 27)):
                    left = 13 if index != 1 else 10
                    right = 29 if index != 1 else 32
                    canvas.create_line(left, y + y_offset, right, y + y_offset, fill=line_color, width=2, capstyle="round")

        def enter(_event):
            canvas._hover = True
            draw()

        def leave(_event):
            canvas._hover = False
            canvas._pressed = False
            draw()

        def press(_event):
            canvas._pressed = True
            draw()

        def release(event):
            inside = 0 <= event.x <= 42 and 0 <= event.y <= 42
            canvas._pressed = False
            if inside:
                self.toggle_drawer()
            draw()

        canvas.bind("<Enter>", enter)
        canvas.bind("<Leave>", leave)
        canvas.bind("<ButtonPress-1>", press)
        canvas.bind("<ButtonRelease-1>", release)
        draw()
        return canvas

    def _rounded_rect(self, canvas, x1, y1, x2, y2, radius, **kwargs):
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
        return canvas.create_polygon(points, smooth=True, splinesteps=24, **kwargs)
