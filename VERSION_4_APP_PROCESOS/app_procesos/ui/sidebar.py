import tkinter as tk

from .theme import COLORS, FONT_BODY_BOLD, FONT_H2
from .widgets import RoundedButton


class Sidebar(tk.Frame):
    def __init__(self, parent, on_select):
        super().__init__(parent, bg=COLORS["panel"], width=280)
        self.on_select = on_select
        self.buttons = {}
        self.pack_propagate(False)
        self._build()

    def _build(self):
        tk.Frame(self, bg=COLORS["accent"], height=3).pack(fill="x")
        tk.Label(
            self,
            text="Menu",
            bg=COLORS["panel"],
            fg=COLORS["text"],
            font=FONT_H2,
        ).pack(anchor="w", padx=20, pady=(22, 12))

        self._add_nav("dashboard", "Dashboard")
        self._add_nav("procesos", "Monitoreo procesos LISTO")
        self._add_nav("cargue_rutas", "Cargue de rutas")

        tk.Frame(self, bg=COLORS["panel"]).pack(fill="both", expand=True)
        tk.Label(
            self,
            text="Procesos AM",
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w", padx=20, pady=(0, 18))

    def _add_nav(self, view_name, label):
        button = RoundedButton(
            self,
            label,
            lambda name=view_name: self.on_select(name),
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
        button.pack(fill="x", padx=16, pady=6)
        self.buttons[view_name] = button
