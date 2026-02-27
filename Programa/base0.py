import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

class TitleFrame(ttk.Frame):
    
    def __init__(self, master, image_path1=None, image_path2=None,image_path3=None,
                 title_text="ThermoHumid Tracker", **kwargs):
       
        super().__init__(master, **kwargs)

        
        self.columnconfigure(0, weight=1)
        content_frame = ttk.Frame(self)
        content_frame.grid(row=0, column=0) 


        self.title_image1 = None
        if image_path1:
            try:
                pil_image = Image.open(image_path1)
                pil_image = pil_image.resize((60, 60), Image.Resampling.LANCZOS)
                self.title_image1 = ImageTk.PhotoImage(pil_image)
                image_label1 = ttk.Label(content_frame, image=self.title_image1)
                image_label1.pack(side=tk.LEFT, padx=(0, 5))
            except Exception as e:
                print(f"No se pudo cargar la primera imagen: {e}")

        self.title_image2 = None
        if image_path2:
            try:
                pil_image2 = Image.open(image_path2)
                pil_image2 = pil_image2.resize((55, 55), Image.Resampling.LANCZOS)
                self.title_image2 = ImageTk.PhotoImage(pil_image2)
                image_label2 = ttk.Label(content_frame, image=self.title_image2)
                image_label2.pack(side=tk.LEFT, padx=(0, 5))
            except Exception as e:
                print(f"No se pudo cargar la segunda imagen: {e}")
        
        self.title_image3 = None
        if image_path3:
            try:
                pil_image3 = Image.open(image_path3)
                pil_image3 = pil_image3.resize((55, 55), Image.Resampling.LANCZOS)
                self.title_image3 = ImageTk.PhotoImage(pil_image3)
                image_label3 = ttk.Label(content_frame, image=self.title_image3)
                image_label3.pack(side=tk.LEFT, padx=(0, 5))
            except Exception as e:
                print(f"No se pudo cargar la segunda imagen: {e}")


        

        
        title_label = ttk.Label(content_frame, text=title_text, font=("Arial", 24, "bold"))
        title_label.pack(side=tk.LEFT, padx=(5, 5))