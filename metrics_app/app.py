import tkinter
from customtkinter import *
from graphs import *

from app_backend import *

import time

from threading import Thread
import queue

graphs = []

request_queue =  queue.Queue()
response_queue = queue.Queue()


def submit_request(callable, *args, **kwargs):
    request_queue.put((callable, args, kwargs))

def app():
    def send_reload_request():
        nonlocal reload_button
        reload_button.configure(text='Reloading...')
        submit_request(reload_metrics)

    def handle_reload_response():
        nonlocal reload_button
        nonlocal reload_label
        global graphs

        for g in graphs:
            g.refresh()

        reload_button.configure(text='Reload')
        reload_label.configure(text=f'Last updated: {get_last_reload()}')

    def tick():
        try:
            ob = response_queue.get_nowait()
        except:
            pass
        else:
            handle_reload_response()
        
        root.after(250, tick)

    root = CTk()
    root.geometry('1000x800')

    root.title('CI Pipeline Analysis Tool')

    reload_button = CTkButton(master=root, text='Reload', command=send_reload_request)
    reload_label = CTkLabel(master=root, text=f'Last updated: {get_last_reload()}')

    reload_button.pack(side=tkinter.BOTTOM, pady=10)
    reload_label.pack(side=tkinter.BOTTOM)

    dt_fig = DeploymentTime(timedelta(days=1), root)
    dt_fig.canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
    graphs.append(dt_fig)
    tick()
    root.mainloop()

def backgrounf_func():
    while 1:
        try:
            callable, args, kwargs = request_queue.get_nowait()
        except queue.Empty:
            pass
        else:
            print("Reloading metrics...")
            retval = callable(*args, **kwargs)
            response_queue.put(retval)
            print("Done!")

        time.sleep(0.2)

if __name__ == "__main__":
    app_thread = Thread(target=backgrounf_func)  # Define your background tasks in this function
    app_thread.start()
    app()


