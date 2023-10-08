import tkinter
from customtkinter import *
from graphs import *

from app_backend import *

graphs = []

def refresh():
    global graphs
    global reload_button
    global reload_label

    reload_button.configure(text='Reloading...')
    reload_metrics()
    for g in graphs:
        g.refresh()
    

    reload_button.configure(text='Reload')
    reload_label.configure(text=f'Last updated: {get_last_reload()}')


root = CTk()
root.geometry('1000x800')

root.title('CI Pipeline Analysis Tool')

reload_button = CTkButton(master=root, text='Reload', command=refresh)
reload_label = CTkLabel(master=root, text=f'Last updated: {get_last_reload()}')

reload_button.pack(side=tkinter.BOTTOM, pady=10)
reload_label.pack(side=tkinter.BOTTOM)

dt_fig = DeploymentTime(timedelta(days=1), root)
dt_fig.canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
graphs.append(dt_fig)

root.mainloop()