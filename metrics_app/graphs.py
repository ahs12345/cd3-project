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
    pass

class DeploymentTime(Graph):
    def __init__(self, duration: timedelta, root):
        self.duration = duration
        self.fig = matplotlib.pyplot.figure(figsize=(5, 4))
        self.ax = self.fig.add_subplot()
        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.refresh()


    def refresh(self):
        data = load_deployment_times()

        y = aggregate_deployment_time(self.duration, data)
        y.reverse()

        x = range(len(y))

        x_ticks = [(data[0][0] - (self.duration * i)).strftime('%d/%m/%Y') for i in range(len(y))]
        x_ticks.reverse()

        self.ax.clear()

        self.ax.plot(x, y)
        self.ax.set_xlabel('Date')
        self.ax.set_xticks(x)
        self.ax.set_xticklabels(x_ticks)
        self.ax.set_ylabel('Average Deployment Time (seconds)')
        self.ax.grid(True)

        self.canvas.draw()