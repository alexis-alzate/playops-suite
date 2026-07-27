import tkinter as tk


class RoundedButton(tk.Canvas):
    def __init__(
        self,
        parent,
        text,
        command,
        *,
        bg,
        fg,
        hover_bg,
        active_bg,
        disabled_bg,
        disabled_fg,
        radius=14,
        height=46,
        width=None,
        font=("Segoe UI", 10, "bold"),
    ):
        options = {
            "height": height,
            "bg": parent.cget("bg"),
            "highlightthickness": 0,
            "bd": 0,
            "cursor": "hand2",
        }
        if width is not None:
            options["width"] = width
        super().__init__(parent, **options)
        self.text = text
        self.command = command
        self.colors = {
            "normal": bg,
            "hover": hover_bg,
            "active": active_bg,
            "disabled": disabled_bg,
            "fg": fg,
            "disabled_fg": disabled_fg,
        }
        self.radius = radius
        self.font = font
        self.state = "normal"
        self.current_bg = bg

        self.bind("<Configure>", lambda _event: self._draw())
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

    def configure(self, cnf=None, **kwargs):
        state = kwargs.pop("state", None)
        if state is not None:
            self.state = state
            self.current_bg = self.colors["disabled"] if state == "disabled" else self.colors["normal"]
            super().configure(cursor="arrow" if state == "disabled" else "hand2")
            self._draw()
        if kwargs:
            super().configure(cnf or {}, **kwargs)

    config = configure

    def _rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):
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
        return self.create_polygon(points, smooth=True, splinesteps=24, **kwargs)

    def _draw(self):
        self.delete("all")
        width = max(self.winfo_width(), 2)
        height = max(self.winfo_height(), 2)
        fg = self.colors["disabled_fg"] if self.state == "disabled" else self.colors["fg"]
        self._rounded_rect(1, 1, width - 1, height - 1, self.radius, fill=self.current_bg, outline="")
        self.create_text(width / 2, height / 2, text=self.text, fill=fg, font=self.font)

    def _on_enter(self, _event):
        if self.state == "disabled":
            return
        self.current_bg = self.colors["hover"]
        self._draw()

    def _on_leave(self, _event):
        if self.state == "disabled":
            return
        self.current_bg = self.colors["normal"]
        self._draw()

    def _on_press(self, _event):
        if self.state == "disabled":
            return
        self.current_bg = self.colors["active"]
        self._draw()

    def _on_release(self, event):
        if self.state == "disabled":
            return
        inside = 0 <= event.x <= self.winfo_width() and 0 <= event.y <= self.winfo_height()
        self.current_bg = self.colors["hover"] if inside else self.colors["normal"]
        self._draw()
        if inside and self.command:
            command = self.command
            self.winfo_toplevel().after_idle(command)


class RoundedSelect(tk.Canvas):
    def __init__(
        self,
        parent,
        variable,
        values,
        *,
        bg,
        fg,
        hover_bg,
        active_bg,
        radius=14,
        width=160,
        height=42,
        font=("Segoe UI", 10),
    ):
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=parent.cget("bg"),
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self.variable = variable
        self.values = list(values)
        self.colors = {
            "normal": bg,
            "hover": hover_bg,
            "active": active_bg,
            "fg": fg,
        }
        self.radius = radius
        self.font = font
        self.current_bg = bg
        self.menu = tk.Menu(self, tearoff=False, bg=bg, fg=fg, activebackground=hover_bg, activeforeground=fg)

        for value in self.values:
            self.menu.add_command(label=value, command=lambda item=value: self._select(item))

        self.variable.trace_add("write", lambda *_args: self._draw())
        self.bind("<Configure>", lambda _event: self._draw())
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self._draw()

    def _select(self, value):
        self.variable.set(value)
        self.current_bg = self.colors["hover"]
        self._draw()

    def _rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):
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
        return self.create_polygon(points, smooth=True, splinesteps=24, **kwargs)

    def _draw(self):
        self.delete("all")
        width = max(self.winfo_width(), 2)
        height = max(self.winfo_height(), 2)
        self._rounded_rect(1, 1, width - 1, height - 1, self.radius, fill=self.current_bg, outline="")
        text = self.variable.get()
        max_chars = max(8, int((width - 42) / 7))
        if len(text) > max_chars:
            text = text[: max_chars - 3].rstrip() + "..."
        self.create_text(
            14,
            height / 2,
            text=text,
            fill=self.colors["fg"],
            font=self.font,
            anchor="w",
        )
        x = width - 24
        y = height / 2
        self.create_line(x - 4, y - 2, x, y + 3, x + 4, y - 2, fill=self.colors["fg"], width=1.5)

    def _on_enter(self, _event):
        self.current_bg = self.colors["hover"]
        self._draw()

    def _on_leave(self, _event):
        self.current_bg = self.colors["normal"]
        self._draw()

    def _on_press(self, _event):
        self.current_bg = self.colors["active"]
        self._draw()

    def _on_release(self, event):
        self.current_bg = self.colors["hover"]
        self._draw()
        if 0 <= event.x <= self.winfo_width() and 0 <= event.y <= self.winfo_height():
            self.menu.tk_popup(self.winfo_rootx(), self.winfo_rooty() + self.winfo_height())
