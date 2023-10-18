from aggregate_metrics import *
from io_metrics import *
from get_metrics import *

import tkinter
from customtkinter import *
import matplotlib.dates as mdates
import numpy as np


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

            date_number = mdates.date2num(x)

            x_clean = [x for x, y in zip(date_number, y) if y is not None]
            y_clean = [y for y in y if y is not None]

            if len(y) > 2:
                coefficients = np.polyfit(x_clean, y_clean, 1)
                polynomial = np.poly1d(coefficients)

                last_date = x[-1]
                next_x_date = last_date + timedelta(days=1)
                next_x = mdates.date2num(next_x_date)
                next_y = polynomial(next_x)
                self.ax.plot(x, y, label=key, marker='o')
                self.ax.plot(next_x_date, next_y, marker='x', label=f'{key} (predicted)')
            else:
                self.ax.plot(x, y, label=key, marker='o')

            if len(y) > maxlen_y:
                self.ax.set_xticks(x)
                self.ax.set_xticklabels(x_ticks)
                maxlen_y = len(y)

        self.ax.set_xlabel(self.xlabel)
        self.ax.set_ylabel(self.ylabel)
        self.ax.grid(True)
        self.ax.legend()
        self.ax.legend(loc='best', prop={'size': 5})
        self.canvas.draw()


class DeploymentTime(Graph):
    def data_config(self):
        self.data = {
            "Lead Time": load_deployment_times(),
            "SAST Run Time": load_sast_times()
        }
        self.xlabel = 'Date'
        self.ylabel = 'Time (seconds)'

        self.ax.tick_params(axis='x', rotation=90)
        self.ax.tick_params(axis='x', labelsize=6) 
        self.aggregate_function = aggregate_deployment_time

class TestRate(Graph):
    def data_config(self):
        self.data = {
            "Test Pass Rate": load_test_pass_rates()
        }
        self.xlabel = 'Date'
        self.ylabel = 'Test pass rate (%)'
        
        self.ax.tick_params(axis='x', rotation=90)
        self.ax.tick_params(axis='x', labelsize=6) 
        self.aggregate_function = aggregate_test_results



class CvssNum(Graph):
    def data_config(self):
        self.data = {
            "cvss vuln": load_cvss_vulnerabilities()
        }

        self.xlabel = 'Date'
        self.ylabel = 'Number of vulnerabilities'

        self.ax.tick_params(axis='x', rotation=90)
        self.ax.tick_params(axis='x', labelsize=6) 
        self.aggregate_function = aggregate_cvss_vulnerabilities
    
    def refresh(self):
        self.ax.clear()
        maxlen_y = 0
        for key in self.data:

            y = self.aggregate_function(self.duration, self.data[key])
            y.reverse()
            #print(y)

            x = [(self.data[key][0][0] - (self.duration * i)) for i in range(len(y))]
            x_ticks = [(self.data[key][0][0] - (self.duration * i)).strftime('%d/%m') for i in range(len(y))]
            x.reverse()
            x_ticks.reverse()

            cvss_cats = ['none', 'low', 'medium', 'high', 'critical']

            new_y_data = {category: [entry[category] if entry is not None else None for entry in y] for category in cvss_cats}

            if len(y) > maxlen_y:
                self.ax.set_xticks(x)
                self.ax.set_xticklabels(x_ticks)
                maxlen_y = len(y)

            date_number = mdates.date2num(x)

            for category, values in new_y_data.items():
                x_clean = [x for x, y in zip(date_number, values) if y is not None]
                y_clean = [y for y in values if y is not None]

                self.ax.plot(x, values, label=category, marker='o',)

                if len(y_clean) > 2:
                    coefficients = np.polyfit(x_clean, y_clean, 1)
                    polynomial = np.poly1d(coefficients)

                    last_date = x[-1]
                    next_x_date = last_date + timedelta(days=1)
                    next_x = mdates.date2num(next_x_date)
                    next_y = polynomial(next_x)

                    self.ax.plot(next_x_date, next_y, marker='x', label=f'{category} (predicted)')

        self.ax.set_xlabel(self.xlabel)
        self.ax.set_ylabel(self.ylabel)
        self.ax.grid(True)
        self.ax.legend()
        self.ax.legend(loc='best', prop={'size': 5})

        self.canvas.draw()

class CvssDeployment(Graph):
    def data_config(self):
        self.data = {
            "cvss vuln": load_cvss_vulnerabilities()
        }
        #print (self.data)

        self.xlabel = 'Deployment Frequency (Deployments per day)'
        self.ylabel = 'Number of vulnerabilities'

        self.ax.tick_params(axis='x', labelsize=6) 
        self.aggregate_function = aggregate_cvvs_deployment
    
    def refresh(self):
        self.ax.clear()
        for key in self.data:

            avg_frequency_dict = self.aggregate_function(self.data[key])
            x_vals = sorted(avg_frequency_dict.keys())
            #print(avg_frequency_dict)

            x_ticks = [(i+1) for i in range (x_vals[-1])]
            #print(x_ticks)

            cvss_cats = ['none', 'low', 'medium', 'high', 'critical']

            print(x_vals)

            for cat in cvss_cats:
                y_values = [avg_frequency_dict[frequency][cat] for frequency in x_vals]
                print(y_values)
                self.ax.plot(x_vals, y_values, marker='o', label=cat)

                if len(x_vals) > 2 and len(y_values) > 2:
                    coefficients = np.polyfit(x_vals, y_values, 1)
                    polynomial = np.poly1d(coefficients)

                    next_x = x_vals[-1] + 1
                    next_y = polynomial(next_x)

                    self.ax.plot(next_x, next_y, marker='x', label=f'{cat} (predicted)')


        self.ax.set_xlabel(self.xlabel)
        self.ax.set_xticks(x_ticks)
        self.ax.set_ylabel(self.ylabel)
        self.ax.grid(True)
        self.ax.legend()
        self.ax.legend(loc='best', prop={'size': 5})

        self.canvas.draw()