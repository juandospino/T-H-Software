from bokeh.plotting import figure
from bokeh.models import ColumnDataSource
from bokeh.layouts import column
import pandas as pd
import numpy as np
import time
import hashlib
import gc

class Plot:
    def __init__(self, parent, data):
        self.parent = parent
        self.data = data

    def create_plots_with_force_new(self):
        
        try:

            # 🔹 Forzar limpieza
            gc.collect()

            # 🔹 Preparar datos
            plot_data = self.prepare_fresh_data_corrected()

            if plot_data.empty:
                print("⚠️ No hay datos válidos para graficar.")
                return self.create_simple_empty_plots()

            # 🔹 Convertir columnas a listas
            source_data = {
                'time': plot_data['time'].tolist(),
                'localtemp': plot_data['localtemp'].tolist(),
                'localhum': plot_data['localhum'].tolist(),
                'temp1': plot_data['temp1'].tolist(),
                'hum1': plot_data['hum1'].tolist(),
                'temp2': plot_data['temp2'].tolist(),
                'hum2': plot_data['hum2'].tolist(),
                'temp3': plot_data['temp3'].tolist(),
                'hum3': plot_data['hum3'].tolist()
            }

            source = ColumnDataSource(data=source_data)

            # ✅ Crear figuras con rangos automáticos
            temp_plot = figure(
                title="Temperature vs Time",
                width=600, height=300,
                x_axis_label="Time",
                y_axis_label="Temperature (°C)",
                tools="pan,wheel_zoom,box_zoom,reset,save",
                sizing_mode="stretch_width"
            )

            hum_plot = figure(
                title="Humidity vs Time",
                width=600, height=300,
                x_axis_label="Time",
                y_axis_label="Humidity (%)",
                tools="pan,wheel_zoom,box_zoom,reset,save",
                sizing_mode="stretch_width"
            )

            colors = ['green', 'yellow', 'blue', 'red']
            sensors = ['Local', 'Sensor 1', 'Sensor 2', 'Sensor 3']

            # 🔹 Graficar solo si hay datos numéricos válidos
            def safe_line(fig, x, y, label, color):
                if np.isfinite(source.data[y]).any():
                    fig.line(x=x, y=y, source=source, legend_label=label, color=color, line_width=2)

            safe_line(temp_plot, 'time', 'localtemp', f'{sensors[0]} Temp', colors[0])
            safe_line(temp_plot, 'time', 'temp1', f'{sensors[1]} Temp', colors[1])
            safe_line(temp_plot, 'time', 'temp2', f'{sensors[2]} Temp', colors[2])
            safe_line(temp_plot, 'time', 'temp3', f'{sensors[3]} Temp', colors[3])

            safe_line(hum_plot, 'time', 'localhum', f'{sensors[0]} Hum', colors[0])
            safe_line(hum_plot, 'time', 'hum1', f'{sensors[1]} Hum', colors[1])
            safe_line(hum_plot, 'time', 'hum2', f'{sensors[2]} Hum', colors[2])
            safe_line(hum_plot, 'time', 'hum3', f'{sensors[3]} Hum', colors[3])

            # 🔹 Leyendas y estilos
            for p in (temp_plot, hum_plot):
                p.legend.location = "top_left"
                p.legend.click_policy = "hide"
                p.title.text_font_size = "14pt"
                p.xaxis.major_label_text_font_size = "9pt"
                p.yaxis.major_label_text_font_size = "9pt"

            print(f"✅ Gráficos creados correctamente con {len(plot_data)} puntos")
            return temp_plot, hum_plot

        except Exception as e:
            print(f"❌ Error creando gráficos: {e}")
            import traceback; traceback.print_exc()
            return self.create_emergency_plots()

    def prepare_fresh_data_corrected(self):
        """Preparar datos limpios y numéricos"""
        try:
            df = self.parent.data.copy()
            if df.empty:
                return pd.DataFrame()

            print(f"📊 Recibidos {len(df)} registros para graficar")

            # Asegurar columnas
            expected_cols = [
                'time', 'localtemp', 'localhum',
                'temp1', 'hum1', 'temp2', 'hum2', 'temp3', 'hum3'
            ]
            for col in expected_cols:
                if col not in df.columns:
                    df[col] = np.nan

            # Convertir tiempo a numérico
            df['time'] = pd.to_numeric(df['time'], errors='coerce')
            df = df.dropna(subset=['time'])
            df = df.sort_values('time')

            # Limpiar y rellenar valores
            for col in expected_cols[1:]:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                df[col] = df[col].interpolate().ffill().bfill()

            # Limitar a 100 puntos
            if len(df) > 100:
                df = df.tail(100)

            return df

        except Exception as e:
            print(f"❌ Error preparando datos: {e}")
            import traceback; traceback.print_exc()
            return pd.DataFrame()

    def create_simple_empty_plots(self):
        """Gráficos vacíos en espera de datos"""
        temp_plot = figure(width=600, height=300, title="Temperature - Waiting for Data")
        hum_plot = figure(width=600, height=300, title="Humidity - Waiting for Data")
        temp_plot.text(x=[0.5], y=[0.5], text=["⏳ Waiting for data..."], text_font_size="14pt", text_align="center")
        hum_plot.text(x=[0.5], y=[0.5], text=["⏳ Waiting for data..."], text_font_size="14pt", text_align="center")
        return temp_plot, hum_plot

    def create_emergency_plots(self):
        """Fallback si hay error"""
        temp_plot = figure(width=600, height=300, title="📈 Temperature (Error)")
        hum_plot = figure(width=600, height=300, title="💧 Humidity (Error)")
        x = [1, 2, 3, 4, 5]
        temp_plot.line(x=x, y=[25, 26, 25.5, 26.5, 25.8], line_width=2, color='red')
        hum_plot.line(x=x, y=[50, 51, 52, 51.5, 52.2], line_width=2, color='blue')
        return temp_plot, hum_plot

    def get_plots_html(self):
        """Exportar gráficos a HTML embebido"""
        from bokeh.embed import file_html
        from bokeh.resources import INLINE
        temp_plot, hum_plot = self.create_plots_with_force_new()
        html = file_html(column(temp_plot, hum_plot), INLINE, f"Sensor Data {time.time()}")
        print(f"✅ HTML generado correctamente ({len(html)} caracteres)")
        return html

    def get_plots(self):
        return self.create_plots_with_force_new()
