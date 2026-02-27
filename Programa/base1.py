
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import pandas as pd
import shutil

class ReportManager:

    def __init__(self, parent):
        self.parent = parent

    def save_data(self):
        if not hasattr(self.parent, 'csv_file') or not self.parent.csv_file:
            messagebox.showwarning("Advertencia", "No hay datos para guardar")
            return

        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialfile=f"sensor_data_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )

            if filename:
                shutil.copy2(self.parent.csv_file, filename)
                messagebox.showinfo("Éxito", f"Datos guardados en:\n{filename}")

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {str(e)}")

    def show_report(self):
        try:
            report_window = tk.Toplevel(self.parent.root)
            report_window.title("Reporte de Datos")
            report_window.geometry("700x500")

            report_frame = ttk.Frame(report_window, padding="10")
            report_frame.pack(fill=tk.BOTH, expand=True)

            notebook = ttk.Notebook(report_frame)
            notebook.pack(fill=tk.BOTH, expand=True)

            # Pestaña de resumen
            summary_frame = ttk.Frame(notebook)
            notebook.add(summary_frame, text="📊 Resumen")

            summary_text = tk.Text(summary_frame, wrap=tk.WORD, padx=10, pady=10, font=("New York Semibold", 11))
            summary_text.pack(fill=tk.BOTH, expand=True)

            report_text = " " * 50 + "\n"
            report_text += "REPORTE DE DATOS\n"
            report_text = "-" * 50 + "\n"

            report_text += f" Fecha del reporte: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            report_text += f" Archivo de datos: {self.parent.csv_file if hasattr(self.parent, 'csv_file') else 'No disponible'}\n\n"
            report_text += f" Datos recibidos: {self.parent.data_count if hasattr(self.parent, 'data_count') else 0}\n\n"
            report_text += f" Unidad actual: {self.parent.temp_unit_var.get().title()}\n\n"
            report_text += f" Tiempo transcurrido: {self.parent.get_time_text(self.parent.elapsed_time)}\n\n"
            report_text += f" Estado: {'En ejecución' if self.parent.is_running else 'Detenido'}\n\n"

            # Pestañas de datos por sensor
            for sensor_idx in range(5):
                sensor_frame = ttk.Frame(notebook)
                sensor_name = f"Sensor {sensor_idx}" if sensor_idx > 0 else "Sensor Local"
                notebook.add(sensor_frame, text=f" {sensor_name}")

                sensor_text = tk.Text(sensor_frame, wrap=tk.WORD, padx=10, pady=10, font=("New York Semibold", 11))
                sensor_text.pack(fill=tk.BOTH, expand=True)

                sensor_key = f'sensor{sensor_idx}'
                temps_c = list(self.parent.data[sensor_key]['temp_c'])
                hums = list(self.parent.data[sensor_key]['hum'])

                valid_temps_c = [t for t in temps_c if not pd.isna(t)]
                valid_hums = [h for h in hums if not pd.isna(h)]

                sensor_report = f"{sensor_name}\n"
                sensor_report += "-" * 50 + "\n\n"

                if valid_temps_c:
                    sensor_report += " Temperatura:\n"
                    sensor_report += f"   Mínima: {min(valid_temps_c):.1f} °C\n"
                    sensor_report += f"   Máxima: {max(valid_temps_c):.1f} °C\n"
                    sensor_report += f"   Promedio: {sum(valid_temps_c) / len(valid_temps_c):.1f} °C\n\n"

                    sensor_report += " Humedad:\n"
                    sensor_report += f"   Mínima: {min(valid_hums):.1f} %\n"
                    sensor_report += f"   Máxima: {max(valid_hums):.1f} %\n"
                    sensor_report += f"   Promedio: {sum(valid_hums) / len(valid_hums):.1f} %\n\n"

                    sensor_report += f" Lecturas válidas: {len(valid_temps_c)}\n"
                    sensor_report += f" Tiempo total: {self.parent.get_time_text(self.parent.elapsed_time)}\n"
                else:
                    sensor_report += "Sin datos válidos\n"

                sensor_text.insert(1.0, sensor_report)
                sensor_text.config(state=tk.DISABLED)

            summary_text.insert(1.0, report_text)
            summary_text.config(state=tk.DISABLED)

            button_frame = ttk.Frame(report_frame)
            button_frame.pack(pady=10)

            ttk.Button(button_frame, text=" Exportar Reporte",
                       command=lambda: self.export_report(report_window)).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Cerrar",
                       command=report_window.destroy).pack(side=tk.LEFT, padx=5)

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el reporte: {str(e)}")

    def export_report(self, parent_window):
        "Exporta el reporte a un archivo de texto."
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                initialfile=f"reporte_sensores_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )

            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("Reporte De Datos Por Sensores\n")
                    f.write("=" * 60 + "\n\n")
                    f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Archivo CSV: {self.parent.csv_file if hasattr(self.parent, 'csv_file') else 'N/A'}\n")
                    f.write(f"Datos recibidos: {self.parent.data_count}\n")
                    f.write(f"Unidad actual: {self.parent.temp_unit_var.get().title()}\n")
                    f.write(f"Tiempo transcurrido: {self.parent.get_time_text(self.parent.elapsed_time)}\n\n")

                    for i in range(5):
                        sensor_key = f'sensor{i}'
                        sensor_name = f"Sensor {i}" if i > 0 else "Sensor Local"

                        temps_c = list(self.parent.data[sensor_key]['temp_c'])
                        hums = list(self.parent.data[sensor_key]['hum'])

                        valid_temps_c = [t for t in temps_c if not pd.isna(t)]
                        valid_hums = [h for h in hums if not pd.isna(h)]

                        f.write(f"\n{sensor_name}\n")
                        f.write("-" * 40 + "\n")

                        if valid_temps_c:
                            f.write(f"Celsius: Min={min(valid_temps_c):.1f}°C, "
                                    f"Max={max(valid_temps_c):.1f}°C, "
                                    f"Avg={sum(valid_temps_c) / len(valid_temps_c):.1f}°C\n")
                            f.write(f"Humedad: Min={min(valid_hums):.1f}%, "
                                    f"Max={max(valid_hums):.1f}%, "
                                    f"Avg={sum(valid_hums) / len(valid_hums):.1f}%\n")
                            f.write(f"Lecturas: {len(valid_temps_c)}\n")
                        else:
                            f.write("Sin datos válidos\n")

                messagebox.showinfo("Éxito", f"Reporte exportado a:\n{filename}")
                parent_window.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar: {str(e)}")