# ui/main_window.py
import os
import sys

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import messagebox, filedialog
from update_checker import is_update_available
from version import APP_VERSION, APP_NAME
import webbrowser
from PIL import Image, ImageTk

from db import connect
from ui.clientes_tab import ClientesTab
from ui.facturas_tab import FacturasTab
from ui.trabajos_tab import TrabajosTab
from config import load_config, save_config
from version import APP_NAME, APP_VERSION

def resource_path(relative_path: str) -> str:
    """
    Devuelve la ruta correcta tanto en modo script como empaquetado con PyInstaller.
    """
    if hasattr(sys, "_MEIPASS"):  # ejecutando dentro del .exe
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(__file__)  # carpeta ui
        base_path = os.path.dirname(base_path)  # subir a raíz del proyecto
    return os.path.join(base_path, relative_path)

class MainWindow(ttk.Window):
    
    def __init__(self):
        super().__init__(themename="cosmo")
        
        self.title("Aplicacion para consulta de facturas -  Electromecanica Luis)")
        self.title(f"{APP_NAME} - v{APP_VERSION}")
        self.geometry("1200x900")

        self.conn = None
        self.db_path = None

        # 1) Header con logo
        self._build_header()

        # 2) Barra superior (ruta BBDD)
        self._build_top_bar()

        # 3) Notebook con pestañas
        self._build_notebook()

        self.config_data = load_config()
        self.db_path_var.set(self.config_data.get("db_path", ""))

    def _build_header(self):
        
        header = ttk.Frame(self, padding=20)
        header.pack(fill="x")

        # Cargamos el logo redimensionado con Pillow
        logo_path = resource_path("logo.png")
        self.logo_image = None

        if os.path.exists(logo_path):
            try:
                img = Image.open(logo_path)
                # Ajusta aquí el tamaño deseado (ancho, alto) en píxeles
                img = img.resize((150, 80), Image.LANCZOS)
                self.logo_image = ImageTk.PhotoImage(img)
            except Exception as e:
                print("Error cargando el logo:", e)
                self.logo_image = None

        if self.logo_image:
            logo_label = ttk.Label(header, image=self.logo_image)
            logo_label.pack(side="left", padx=(0, 15))

        title_frame = ttk.Frame(header)
        title_frame.pack(side="left", fill="x", expand=True)

        ttk.Label(
            title_frame,
            text="Electromecánica Luis",
            font=("Segoe UI", 18, "bold")
        ).pack(anchor="w")

        ttk.Label(
            title_frame,
            text="Gestor de clientes, facturas y trabajos",
            font=("Segoe UI", 10)
        ).pack(anchor="w")

    def _build_top_bar(self):
        # Frame superior
        top = ttk.Frame(self, padding=10)
        top.pack(fill="x")
    
        # Etiqueta ruta
        ttk.Label(top, text="Base de datos:", font=("Segoe UI", 10, "bold")).pack(side="left")
    
        # Variable ruta
        self.db_path_var = tk.StringVar()
    
        # Entrada de texto
        entry = ttk.Entry(top, textvariable=self.db_path_var, width=60)
        entry.pack(side="left", padx=10)
    
        # Botón examinar
        ttk.Button(
            top,
            text="Examinar",
            bootstyle="secondary",
            command=self.browse_db
        ).pack(side="left", padx=5)
    
        # Botón conectar
        ttk.Button(
            top,
            text="Conectar",
            bootstyle="success",
            command=self.connect_db
        ).pack(side="left", padx=5)
    
        # Botón buscar actualizaciones (si existe check_updates)
        if hasattr(self, "check_updates"):
            ttk.Button(
                top,
                text="Buscar actualizaciones",
                bootstyle="info",
                command=self.check_updates
            ).pack(side="right", padx=5)
    
    def _build_notebook(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.notebook.configure(bootstyle="info")

        # Creamos las pestañas pero les pasamos self para que puedan llamar a métodos de la ventana
        self.clientes_tab = ClientesTab(self.notebook, self)
        self.facturas_tab = FacturasTab(self.notebook, self)
        self.trabajos_tab = TrabajosTab(self.notebook, self)

        self.notebook.add(self.clientes_tab, text="Clientes")
        self.notebook.add(self.facturas_tab, text="Facturas")
        self.notebook.add(self.trabajos_tab, text="Trabajos")

    def browse_db(self):
        filename = filedialog.askopenfilename(
            title="Seleccionar base de datos Access",
            filetypes=[("Base de datos Access", "*.mdb;*.accdb"), ("Todos", "*.*")],
        )
        if filename:
            self.db_path_var.set(filename)

    def connect_db(self):
        db_path = self.db_path_var.get().strip()
        if not db_path:
            messagebox.showwarning("Ruta vacía", "Indica la ruta del archivo .mdb")
            return
        if not os.path.isfile(db_path):
            messagebox.showerror("Archivo no encontrado", db_path)
            return

        try:
            if self.conn:
                self.conn.close()
            self.conn = connect(db_path)
            self.db_path = db_path
            messagebox.showinfo("Conexión", "Conexión correcta a la base de datos.")
            # Avisamos a las pestañas para que recarguen datos si quieren
            self.clientes_tab.on_db_connected()
            self.facturas_tab.on_db_connected()
            self.trabajos_tab.on_db_connected()
        except Exception as e:
            messagebox.showerror("Error de conexión", str(e))
            self.conn = None

    def get_conn(self):
        if self.conn is None:
            messagebox.showwarning("Sin conexión", "Conéctate primero a la base de datos.")
            return None
        return self.conn
    
    def check_updates(self):
        ok, remote_str = is_update_available()
        if remote_str is None:
            messagebox.showwarning(
                "Actualización",
                "No se ha podido comprobar si hay una versión nueva.\n"
                "Comprueba tu conexión a Internet o inténtalo más tarde.",
            )
            return

        if ok:
            # Hay una versión nueva
            resp = messagebox.askyesno(
                "Nueva versión disponible",
                f"Estás usando la versión {APP_VERSION}.\n"
                f"La versión más reciente es {remote_str}.\n\n"
                "¿Quieres abrir la página de descargas?",
            )
            if resp:
                # Abre tu página de releases o de descarga
                webbrowser.open("https://github.com/jjdominguez79/Electromecanica_Luis_App/releases")
        else:
            messagebox.showinfo(
                "Actualización",
                f"Estás usando la última versión ({APP_VERSION}).",
            )
