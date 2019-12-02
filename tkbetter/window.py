import tkinter as tk

from .exceptions import *
from .core import Core

class Window(tk.Toplevel):
    """Used insted of Tk and TopLevel.
    The master (parent) must be a Core or another Window object.
    """

    def __init__(self, master, *args, **kwargs): # master replaced by boligatory parent
        if not isinstance(master, (Core, Window)):
            raise TkBetterException("'master' parameter of Window is obligatory and must be a Core object or another Window object.")

        super().__init__(master, *args, **kwargs)

        def find_core(window):
            if window.master:
                return find_core(window.master)
            else:
                return window

        self.core = find_core(self)