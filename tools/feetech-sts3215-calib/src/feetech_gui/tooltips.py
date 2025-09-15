import tkinter as tk

class Tooltip:
    def __init__(self, widget, text: str, delay_ms: int = 480, wraplength: int = 320):
        self.widget = widget
        self.text = text
        self.delay_ms = delay_ms
        self.wraplength = wraplength
        self._id = None
        self._tw = None
        widget.bind("<Enter>", self._schedule)
        widget.bind("<Leave>", self._hide)
        widget.bind("<ButtonPress>", self._hide)

    def _schedule(self, _=None):
        self._unschedule()
        self._id = self.widget.after(self.delay_ms, self._show)

    def _unschedule(self):
        if self._id:
            try:
                self.widget.after_cancel(self._id)
            except Exception:
                pass
            self._id = None

    def _show(self, _=None):
        if self._tw or not self.text:
            return
        try:
            x = self.widget.winfo_rootx() + 12
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 8
        except Exception:
            x, y = 0, 0
        self._tw = tk.Toplevel(self.widget)
        self._tw.wm_overrideredirect(True)
        self._tw.wm_geometry(f"+{x}+{y}")
        lbl = tk.Label(
            self._tw,
            text=self.text,
            justify="left",
            relief="solid",
            borderwidth=1,
            background="#ffffe0",
            padx=8,
            pady=6,
            wraplength=self.wraplength,
        )
        lbl.pack(ipadx=1)

    def _hide(self, _=None):
        self._unschedule()
        if self._tw:
            try:
                self._tw.destroy()
            except Exception:
                pass
            self._tw = None


def attach_tooltip(widget, text: str):
    if widget is not None:
        Tooltip(widget, text)
