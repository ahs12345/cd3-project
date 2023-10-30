import tkinter
from customtkinter import *
from graphs import *

from app_backend import *

import time

from threading import Thread

import math
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

    def send_simulate_request():
        nonlocal simulate_button
        nonlocal commits_per_day
        nonlocal sim_config_choice
        simulate_button.configure(text='Simulating...')
        submit_request(simulate_pipeline, commits_per_day.get(), sim_config_choice)

    def handle_response(param: str):
        nonlocal reload_button
        nonlocal reload_label

        nonlocal simulate_button
        nonlocal simulation_results

        global graphs

        if param[0] == "graph":
            for g in graphs:
                g.do_refresh()

            reload_button.configure(text='Reload')
            reload_label.configure(text=f'Last updated: {get_last_reload()}')
        
        if param[0] == "simulate":
            simulate_button.configure(text="Simulate")
            simulation_results.configure(
                text=f"Simulation Results:\n" +
                     f"Lead Time to Changes: {math.floor(param[1])}\n" +
                     f"Deployment Frequency: {param[2]}" 
            )
            print(param)


    def tick():
        try:
            ob = response_queue.get_nowait()
        except:
            pass
        else:
            handle_response(ob)
        
        root.after(250, tick)

    root = CTk()
    root.geometry('1500x1000')

    root.title('CI Pipeline Analysis Tool')

    reload_button = CTkButton(master=root, text='Reload', command=send_reload_request)
    reload_label = CTkLabel(master=root, text=f'Last updated: {get_last_reload()}')

    reload_button.pack(side=tkinter.BOTTOM, pady=10)
    reload_label.pack(side=tkinter.BOTTOM)
  

    tabview = CTkTabview(root, height=root._max_height, width=root._max_width)
    tabview.pack(fill=tkinter.Y, expand=True, padx=20, pady=0)


    perf_tab = tabview.add("Pipeline Performance")
    qual_tab = tabview.add("Code Quality")

    dt_fig = DeploymentTime("Deployment Times", timedelta(days=1), perf_tab)
    tp_fig = TestRate("Test Pass Rate", timedelta(days=1), qual_tab)
    cvss_fig = CvssNum("CVSS Vulnerability Count", timedelta(days=1), qual_tab)
    cvss_deployment = CvssDeployment("CVSS Vulnerabilities based on Deployment Frequency", timedelta(days=1), qual_tab)


    dt_fig.canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1) 
    tp_fig.canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1) 
    cvss_fig.canvas.get_tk_widget().pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=1)
    cvss_deployment.canvas.get_tk_widget().pack(side=tkinter.RIGHT, fill=tkinter.BOTH, expand=1)

    # Simulation UI
    sim_tab = tabview.add("Simulation")
    
    sim_config_choices = {
        "Sequential Execution" : "seq",
        "Parralel Execution" : "par"
    }
    sim_config_choice = "seq"
    commits_per_day = StringVar(value="5")

    def sim_config_update(choice):
        nonlocal sim_config_choice
        nonlocal sim_config_choices
        sim_config_choice = sim_config_choices[choice]
        print(f"choice: {sim_config_choice}")

    title = CTkLabel(
        master=sim_tab,
        text="Pipeline Simulation"
    ).grid(row=0,column=0,columnspan=2)

    CTkLabel(
        master=sim_tab,
        text="Commits per Day"
    ).grid(row=1,column=0)
    commits_per_day_entry = CTkEntry(
        master=sim_tab,
        placeholder_text="Commits per Day",
        width=300,
        height=30,
        textvariable=commits_per_day,
    ).grid(row=1,column=1, padx=10, pady=10)

    CTkLabel(
        master=sim_tab,
        text="SAST Configuration"
    ).grid(row=2,column=0)
    config_select_box = CTkOptionMenu(
        master=sim_tab,
        values=list(sim_config_choices.keys()),
        command=sim_config_update
    ).grid(row=2,column=1)

    simulate_button = CTkButton(
        master=sim_tab,
        width=90,
        height=25,
        corner_radius=10,
        text="Simulate",
        command=send_simulate_request
    )
    simulate_button.grid(row=3,column=0,columnspan=2,pady=10)

    simulation_results = CTkLabel(
        master=sim_tab,
        text=""
    )
    simulation_results.grid(row=4,column=0,columnspan=2)

    graphs.append(dt_fig)
    graphs.append(tp_fig)
    graphs.append(cvss_fig)
    graphs.append(cvss_deployment)
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


