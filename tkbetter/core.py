# mainlopp must be in same as inited: change

import tkinter as tk
import threading
from queue import Queue

from .exceptions import *

class Task:
    """Represents a task.
    A task is an object containing a function and its arguments.
    To run the task use the run() method.
    """

    def __init__(self, function, args=(), kwargs={}):
        self.function = function
        self.args = args
        self.kwargs = kwargs

    def run(self):
        self.function(*self.args, **self.kwargs)

class QueuedAfter:
    """QueuedAfter objects are objects representing a call to '.after'."""
    def __init__(self, ms, func, args):
        self.ms = ms
        self.func = func
        self.args = args

class CoreThread(threading.Thread):
    """CoreThread obects are Thread objects with a 'core' attribute.
    'core' shoud be a reference to the Core object from where the thread was created.
    """

    def __init__(self, core, function, args=(), kwargs={}):
        super().__init__(target=function, args=args, kwargs=kwargs, daemon=True)
        
        self.core = core

WINDOWS_HANDLER_INTERVAL = 300
TASKS_HANDLER_INTERVAL = 50

class Core(tk.Tk):
    """A Core object is the base of a Tkbetter application.
    It provides the Tk event loop without showing a window.
    It also provides additional features, methods and threading facilities
    """

    def __init__(self):
        super().__init__()
        self.withdraw()

        current_thread = threading.current_thread()

        if hasattr(current_thread, "core"):
            raise TkBetterException("Current thread has a 'core' property already defined. Only one instance of Core is allowed"
                                    "per thread and Core can not be instantiated inside a thread created by the 'run_thread' method.")

        current_thread.core = self
        self.init_thread = current_thread

        self.mainlooped = False
        self.after_queue = Queue()

        self.tasks = Queue()

        self.set_after(TASKS_HANDLER_INTERVAL, self.tasks_handler)
        self.set_after(WINDOWS_HANDLER_INTERVAL, self.windows_handler)

    def flush_after(self):
        while not self.after_queue.empty():
            qa = self.after_queue.get()

            super().after(qa.ms, qa.func, *qa.args)

    def set_after(self, ms, func=None, *args):
        """Should be used insted of after() method.
        It works like after() but waits for the mainloop before calling functions.

        This method has a global version for easy of use that can be called from
        the thread where the Core object has been initialised.
        """

        current_thread = threading.current_thread()

        if self.mainlooped:
            if self.mainloop_thread != current_thread:
                raise TkBetterException("If the mainloop has been started in a thread then you can not call 'set_after' from a"
                                        "different thread. If you want to modify the GUI maybe you are looking for 'run_queued'.")

            super().after(ms, func, *args)
        else:
            self.after_queue.put(QueuedAfter(ms, func, args))

    def mainloop(self, n=0):
        """Modified version of the original mainloop of Tk objects.
        Works the same but must be used in the same thread where the Core object is.
        """

        current_thread = threading.current_thread()

        if not hasattr(current_thread, "core"):
            raise TkBetterException("mainloop must be started from the same thread where Core was instantiated.")
        else:
            if not ( isinstance(current_thread.core, Core) and current_thread.core.init_thread == current_thread ):
                raise TkBetterException("mainloop must be started from the same thread where Core was instantiated.")
        
        current_thread.core = self
        self.mainloop_thread = current_thread

        self.mainlooped = True
        self.flush_after()

        super().mainloop(n)

    def windows_handler(self):
        windows = self.winfo_children()

        if not windows:
            print('Core: No windows left.')
            self.destroy()

        self.after(WINDOWS_HANDLER_INTERVAL, self.windows_handler)

    def tasks_handler(self):
        while not self.tasks.empty():
            self.tasks.get().run()

        self.after(TASKS_HANDLER_INTERVAL, self.tasks_handler)

    def run_thread(self, function, *args, **kwargs):
        """Run a function in a separete thread.
        The thread is related to the Core object so you can use run_queued() inside
        of it for safely call Tkinter functions and modify the GUI.

        Returns a CoreThread object which is like a normal Thread object but with a 'core'
        attribute that references the Core object related to the thread.

        You can access the 'core' attribute from inside the thread using the standard 'threading'
        library like this: threading.current_thread().core

        This method has a global version for easy of use that can be called from
        the thread where the Core object has been initialised or from another thread created by this method.
        """

        t = CoreThread(self, function, args, kwargs)
        t.start()
        return t

    def run_queued(self, function, *args, **kwargs):
        """Queue a function that will be called by the Core object after a very small time.

        Use it for safely call Tkinter function from threads created by the run_thread() method.

        Warning: The execution doesn't wait for the function to be called.
        (NEXT VERSION) To wait use the wait() method of the object returned by this function.
        Use it like this:

            core_object.run_queued(some_function, arg1, arg2, ...)
            core_object.run_queued(other_function, arg1, arg2, ...)
            core_object.run_queued(last_function).wait()

        This method has a global version for easy of use that can be called from
        the thread where the Core object has been initialised or from another thread created by the run_thread() method.
        """

        self.tasks.put(Task(function, args, kwargs))

def run_thread(function, *args, **kwargs):
    """Run a function in a separete thread.

    This method must be called from the thread where the Core object has been initialised or
    from another thread created by this method.

    The thread is related to the Core object so you can use run_queued() inside
    of it for safely call Tkinter functions and modify the GUI.

    Returns a CoreThread object which is like a normal Thread object but with a 'core'
    attribute that references the Core object related to the thread.

    You can access the 'core' attribute from inside the thread using the standard 'threading'
    library like this: threading.current_thread().core
    """

    current_thread = threading.current_thread()

    if hasattr(current_thread, "core"):
        if isinstance(current_thread.core, Core):
            current_thread.core.run_thread(function, *args, **kwargs)
        else:
            raise TkBetterException("The current thread has a 'core' property but is not a Core.")
    else:
        raise TkBetterException("This thread does not have a 'core' property. Please use 'run_thread' method in the same thread of Core's"
                                "mainloop or where Core was initialised or in a thread created by another 'run_thread' method.")


def run_queued(function, *args, **kwargs):
    """Queue a function that will be called by the Core object after a very small time.

    This method must be called from the thread where the Core object has been initialised or
    from another thread created by the run_thread() method.

    Use it for safely call Tkinter function from threads created by the run_thread() method.

    Warning: The execution doesn't wait for the function to be called.
    (NEXT VERSION) To wait use the wait() method of the object returned by this function.
    Use it like this:

        run_queued(some_function, arg1, arg2, ...)
        run_queued(other_function, arg1, arg2, ...)
        run_queued(last_function).wait()
    """

    current_thread = threading.current_thread()

    if hasattr(current_thread, "core"):
        if isinstance(current_thread.core, Core):
            current_thread.core.run_queued(function, *args, **kwargs)
        else:
            raise TkBetterException("The current thread has a 'core' property but is not a Core.")
    else:
        raise TkBetterException("This thread does not have a 'core' property. Please use 'run_queued' method in the same thread of"
                                "Core's mainloop or where Core was initialised or in a thread created by another 'run_thread' method.")

def set_after(self, ms, func=None, *args):
    """Should be used insted of after() method.
    It works like after() but waits for the mainloop before calling functions.

    This method must be called from the thread where the Core object has been initialised.
    """

    current_thread = threading.current_thread()

    if hasattr(current_thread, "core"):
        if isinstance(current_thread.core, Core):
            current_thread.core.set_after(ms, func, *args)
        else:
            raise TkBetterException("The current thread has a 'core' property but is not a Core.")
    else:
        raise TkBetterException("This thread does not have a 'core' property. Please use 'set_after' method in the same"
                                "thread of Core's mainloop or where Core was initialised.")