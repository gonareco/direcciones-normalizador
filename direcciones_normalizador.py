#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Última modificación Jun  4 18:12:01 2025

@author: Gonzalo Areco - 2025
"""
        
import re
import pandas as pd
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

class ProcesadorDirecciones:
    def __init__(self, root):
        self.root = root
        self.root.title("Procesador de Direcciones v1.0")
        self.root.geometry("600x400")
        
        # Variables
        self.input_file = tk.StringVar()
        self.output_file = tk.StringVar(value="direcciones_procesadas.csv")
        self.status = tk.StringVar(value="Listo para comenzar")
        
        # Crear interfaz
        self.crear_interfaz()

# Creación de interfaz        

    def crear_interfaz(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Sección de entrada
        ttk.Label(main_frame, text="CSV Entrada").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(main_frame, textvariable=self.input_file, width=50).grid(row=1, column=0, sticky=tk.EW)
        ttk.Button(main_frame, text="Examinar...", command=self.seleccionar_archivo).grid(row=1, column=1, padx=5)
        
        # Sección de salida
        ttk.Label(main_frame, text="Archivo de salida:").grid(row=2, column=0, sticky=tk.W, pady=(10,0))
        ttk.Entry(main_frame, textvariable=self.output_file, width=50).grid(row=3, column=0, sticky=tk.EW)
        ttk.Button(main_frame, text="Examinar...", command=self.seleccionar_destino).grid(row=3, column=1, padx=5)
        
        # Barra de progreso
        self.progress = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, mode='determinate')
        self.progress.grid(row=4, column=0, columnspan=2, pady=(20,5), sticky=tk.EW)
        
        # Botón de procesar
        ttk.Button(main_frame, text="Generar Variables de Direcciones", command=self.procesar).grid(row=5, column=0, columnspan=2, pady=10)
        
        # Estado
        ttk.Label(main_frame, textvariable=self.status).grid(row=6, column=0, columnspan=2)
        
        # Configurar expansión
        main_frame.columnconfigure(0, weight=1)
        
    def seleccionar_archivo(self):
        file = filedialog.askopenfilename(
            title="Seleccionar CSV con direcciones",
            filetypes=[("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*")]
        )
        if file:
            self.input_file.set(file)
            # Sugerir nombre de archivo de salida
            dirname, basename = os.path.split(file)
            self.output_file.set(f"{os.path.splitext(basename)[0]}_procesado.csv")
    
    def seleccionar_destino(self):
        file = filedialog.asksaveasfilename(
            title="Guardar resultados como",
            defaultextension=".csv",
            filetypes=[("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*")],
            initialfile=self.output_file.get()
        )
        if file:
            self.output_file.set(file)
    
    def separar_direccion(self, direccion):
        """Función para separar la dirección"""
        calle = altura = resto = sinsep = None
        condsep = 2  # Por defecto no separable
        
        if pd.isna(direccion) or not isinstance(direccion, str):
            sinsep = direccion
            return pd.Series([calle, altura, resto, sinsep, condsep])
        
        # Normalización
        direccion = re.sub(r'\s+', ' ', direccion.strip())
        direccion = re.sub(r'[/\-.,]', ' ', direccion)
        
        # Caso 1: Patrón numérico
        if re.match(r'^\d{3,5}\s+\d{1,5}(?:\s|$)', direccion):
            partes = re.split(r'\s+', direccion, maxsplit=2)
            calle, altura = partes[0], partes[1]
            resto = partes[2] if len(partes) > 2 else None
            condsep = 1
        
        # Caso 2: Direcciones complejas o dificiles de tratar (acá tenemos que ver más ejemplos de casos reales)
        elif any(palabra in direccion.lower() for palabra in ['calle','barrio','manzana','mzn','mza','manz','mz','mzna','casa','galpon','villa']):
            sinsep = direccion
        
        # Caso 3: Texto + número
        elif re.match(r'^[^\d]+\s+\d{1,5}(?:\s|$)', direccion, re.IGNORECASE):
            match = re.match(r'^(.*?)\s+(\d{1,5})\s*(.*)$', direccion)
            if match:
                calle, altura = match.group(1).strip(), match.group(2).strip()
                resto = match.group(3).strip() if match.group(3) else None
                condsep = 1
        
        # Caso 4: Intento fallback
        elif re.search(r'\d', direccion):
            match = re.match(r'^(.*?)(\d+)\s*$', direccion)
            if match and len(match.group(1).strip()) > 0:
                calle, altura = match.group(1).strip(), match.group(2).strip()
                condsep = 1
            else:
                sinsep = direccion
        else:
            sinsep = direccion
        
        if condsep == 2 and sinsep is None:
            sinsep = direccion
        
        return pd.Series([calle, altura, resto, sinsep, condsep])
    
    def procesar(self):
        """Procesa el archivo seleccionado"""
        if not self.input_file.get():
            messagebox.showerror("Error", "Debe seleccionar un archivo de entrada")
            return
        
        try:
            self.status.set("Leyendo archivo...")
            self.root.update_idletasks()
            
            # Leer archivo CSV
            df = pd.read_csv(self.input_file.get())
            
            if 'direccion' not in df.columns:
                messagebox.showerror("Error", "El archivo no contiene la columna 'direccion'")
                return
            
            total = len(df)
            self.progress["maximum"] = total
            self.status.set(f"Procesando {total} direcciones...")
            
            # Procesar en bloques para actualizar la interfaz
            resultados = []
            for i, row in enumerate(df.itertuples(), 1):
                resultados.append(self.separar_direccion(row.direccion))
                if i % 100 == 0 or i == total:
                    self.progress["value"] = i
                    self.status.set(f"Procesando {i}/{total} direcciones...")
                    self.root.update_idletasks()
            
            # Combinar resultados
            df[['calle', 'altura', 'resto', 'sinsep', 'condsep']] = pd.DataFrame(resultados)
            valores_unicos = list(df['direccion'].dropna().unique())

            
            # Guardar resultados
            self.status.set("Guardando resultados...")
            self.root.update_idletasks()
            
            output_path = self.output_file.get()
            df.to_csv(output_path, index=False)
            
            # Mostrar estadísticas
            separados = sum(df['condsep'] == 1)
            no_separados = total - separados
            
            messagebox.showinfo(
                "Proceso completado",
                f"Direcciones procesadas: {total}\n"
                f"Separadas correctamente: {separados} ({separados/total*100:.1f}%)\n"
                f"No separadas: {no_separados}\n\n"
                f"Resultados guardados en:\n{output_path}"
            )
            
            self.status.set(f"Listo. Procesadas {total} direcciones")
            self.progress["value"] = 0
            
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error:\n{str(e)}")
            self.status.set("Error al procesar")
        finally:
            self.progress["value"] = 0

if __name__ == '__main__':
    root = tk.Tk()
    app = ProcesadorDirecciones(root)
    
    # Centrar la ventana
    window_width = root.winfo_reqwidth()
    window_height = root.winfo_reqheight()
    position_right = int(root.winfo_screenwidth()/2 - window_width/2)
    position_down = int(root.winfo_screenheight()/2 - window_height/2)
    root.geometry(f"+{position_right}+{position_down}")
    
    root.mainloop()
