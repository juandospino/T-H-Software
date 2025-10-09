from bokeh.plotting import figure
from bokeh.models import ColumnDataSource


class Plot:
    def __init__(self, parent, data):
        super().__init__()
        self.parent = parent
        self.data = data

        self.source = ColumnDataSource(self.data)

        self.t = figure(title = "Temperature vs Time",width=1010, height=290, y_range = (0,100) , x_axis_label = "Time", y_axis_label = "Temperature")
        self.h = figure(title = "Humidity vs Time",width=1010, height=290, y_range = (0,100) , x_axis_label = "Time", y_axis_label = "Humidity")

        self.t.line(source= self.source,
               x = "time", 
               y = "localtemp", 
               legend_label = "Local Temperature", 
               color = "green")
        
        self.t.line(source= self.source,
               x = "time", 
               y = "temp1", 
               legend_label = "Sensor 1 Temperature", 
               color = "yellow")
        
        self.t.line(source= self.source,
               x = "time", 
               y = "temp2", 
               legend_label = "Sensor 2 Temperature", 
               color = "blue")
        
        self.t.line(source= self.source,
               x = "time", 
               y = "temp3", 
               legend_label = "Sensor 3 Temperature", 
               color = "red")
        
        self.h.line(source= self.source,
               x = "time", 
               y = "localhum", 
               legend_label = "Local Humidity", 
               color = "green")
        
        self.h.line(source= self.source,
               x = "time", 
               y = "hum1", 
               legend_label = "Sensor 1 Humidity", 
               color = "yellow")
        
        self.h.line(source= self.source,
               x = "time", 
               y = "hum2", 
               legend_label = "Sensor 2 Humidity", 
               color = "blue")
        
        self.h.line(source= self.source,
               x = "time", 
               y = "hum3", 
               legend_label = "Sensor 3 Humidity", 
               color = "red")
    
    def refresh_plot(self):
        self.source.data = ColumnDataSource.from_df(self.data)

    def get_plots(self):
        return self.t, self.h