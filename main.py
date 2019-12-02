#!/usr/bin/env python3

# pylint: disable=unused-wildcard-import

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox # Why

import tkbetter as tkb

import subprocess as sp
from pathlib import Path
from threading import Thread

from time import sleep

class LogWindow(tkb.Window):
    def __init__(self, parent=None):
        super().__init__(parent)

        #self.geometry("600x400")
        #self.resizable(False, False)
        #self.title("Logged Window")

        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.X, expand=0, padx=10, pady=(10, 0))

        self.log_frame = ttk.LabelFrame(self, text="Log")
        self.log_frame.pack(fill=tk.BOTH, expand=1, padx=10, pady=10)

        self.log_text = tk.Text(self.log_frame)
        self.log_text.config(state="disabled")
        self.log_text.pack(fill=tk.BOTH, expand=1, padx=7, pady=5)

    def log_label(self, label):
        self.log_frame.config(text=str(label))

    def log_write(self, line=""):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, str(line) + "\n")
        self.log_text.config(state="disabled")

    def log_get(self):
        return self.log_text.get("1.0", tk.END)

    def log_clear(self):
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state="disabled")

class AppWindow(LogWindow):
    def __init__(self, parent=None, avds=[]):
        super().__init__(parent)

        # GUI

        self.geometry("600x400")
        self.title("AVD TkLuncher")

        avd_label = ttk.Label(self.main_frame, text="AVD:")
        avd_label.pack(side=tk.LEFT)

        self.avd_variable = tk.StringVar()

        self.avd_select = ttk.OptionMenu(self.main_frame, self.avd_variable, avds[0], *avds)
        self.avd_select.pack(side=tk.LEFT, fill=tk.X, expand=1, padx=10, pady=10)

        self.avd_run = ttk.Button(self.main_frame, text="Run", command=self.handle_run)
        self.avd_run.pack(side=tk.RIGHT)

    def handle_run(self):
        self.log_clear()

        def target():
            #self.core.run_queued(print, self.avd_variable.get())

            tkb.run_queued(self.avd_select.config, state="disabled")
            tkb.run_queued(self.avd_run.config, state="disabled")

            # temporal fix

            try:
                adbp = sp.Popen(["adb", "start-server"], stdout=sp.PIPE, stderr=sp.STDOUT)

                while not adbp.poll():
                    line = adbp.stdout.readline()
                    if not line:
                        break
                    if line:
                        tkb.run_queued(self.log_write, line.decode('utf-8'))

            except FileNotFoundError:
                messagebox.showerror("ADB required", "'adb' command not found. Please add its location to the PATH.\n\n"
                                    "adb is necesary to fix a bug in this program. adb will not be necesary after fixing "
                                    "it but I have no time for fixing this project.")

                return
            except Exception as e:
                messagebox.showerror("Unexpected error", str(e))

                return
            
            # end of temporal fix

            process = sp.Popen(["emulator", "-avd", self.avd_variable.get()], stdout=sp.PIPE, stderr=sp.STDOUT)

            while not process.poll():
                line = process.stdout.readline()
                if not line:
                    break
                if line:
                    tkb.run_queued(self.log_write, line.decode('utf-8'))

            tkb.run_queued(self.avd_select.config, state="normal")
            tkb.run_queued(self.avd_run.config, state="normal")

        tkb.run_thread(target)

class EmptyListAvdsException(Exception):
    pass

def main():
    core = tkb.Core()

    # List AVDs

    avds = None

    try:
        avds = sp.Popen(["emulator", "-list-avds"], stdout=sp.PIPE, stderr=sp.STDOUT) \
            .communicate()[0] \
            .decode("utf-8") \
            .strip() \
            .split()

        if len(avds) == 0:
            raise EmptyListAvdsException

        AppWindow(core, avds)
        core.mainloop()
    except FileNotFoundError:
        messagebox.showerror("Emulator AVD list failed", "Can't get list of AVDs. Make sure that 'emulator' executable is in PATH and works correctly.\nTry running 'emulator -list-avds' command by your self.")
    except EmptyListAvdsException:
        messagebox.showerror("Empty List AVDs", "No AVDs found. Please create a new AVD from Android Studio.")
    except Exception as e:
        messagebox.showerror("Unexpected error", str(e))

if __name__ == "__main__":
    main()