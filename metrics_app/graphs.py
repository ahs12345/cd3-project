from aggregate_metrics import *
from io_metrics import *
from get_metrics import *

import tkinter
from customtkinter import *

from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg
)
from matplotlib.pyplot import Figure
import matplotlib

class Graph:
    def __init__(self, duration: timedelta, root):
        self.duration = duration
        self.fig = matplotlib.pyplot.figure(figsize=(5, 4))
        self.ax = self.fig.add_subplot()
        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.data_config()
        self.refresh()

    def data_config(self):
        pass

    def refresh(self):

        self.ax.clear()
        maxlen_y = 0

        for key in self.data:
            y = self.aggregate_function(self.duration, self.data[key])
            y.reverse()

            x = [(self.data[key][0][0] - (self.duration * i)) for i in range(len(y))]
            x_ticks = [(self.data[key][0][0] - (self.duration * i)).strftime('%d/%m') for i in range(len(y))]
            x.reverse()
            x_ticks.reverse()

            if len(y) > maxlen_y:
                self.ax.set_xticks(x)
                self.ax.set_xticklabels(x_ticks)
                
                maxlen_y = len(y)

            self.ax.plot(x, y, label=key, marker='o')

        self.ax.set_xlabel(self.xlabel)
        self.ax.set_ylabel(self.ylabel)
        self.ax.grid(True)
        self.ax.legend()

        self.canvas.draw()

class DeploymentTime(Graph):
    def data_config(self):
        self.data = {
            "Lead Time": load_deployment_times(),
            "SAST Run Time": load_sast_times()
        }

        self.xlabel = 'Date'
        self.ylabel = 'Time (seconds)'

        self.aggregate_function = aggregate_deployment_time

class TestRate(Graph):
    def data_config(self):
        self.data = {
            "Test Pass Rate": load_test_pass_rates()
        }

        self.xlabel = 'Date'
        self.ylabel = 'Test pass rate (%)'

        self.aggregate_function = aggregate_test_results

class CvssNum(Graph):
    def data_config(self):
        self.data = {
            "cvss vuln": load_cvss_vulnerabilities()
        }

        self.xlabel = 'Date'
        self.ylabel = 'Number of vulnerabilities'

        self.aggregate_function = aggregate_cvss_vulnerabilities