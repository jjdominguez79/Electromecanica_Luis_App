# ui/main_window.py
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog

import os

from db import connect
from ui.clientes_tab import ClientesTab
from ui.facturas_tab import FacturasTab
from ui.trabajos_tab import TrabajosTab
from config import load_config, save_config


class MainWindow(ttk.Window):
    def __init__(self):
        super().__init__(themename="cosmo")

        self.title("Aplicacion para consulta de facturas -  Electromecanica Luis)")
        self.geometry("1100x650")

        self.conn = None
        self.db_path = None

        self._build_top_bar()
        self._build_notebook()

        self.config_data = load_config()
        self.db_path_var.set(self.config_data.get("db_path", ""))


    def _build_top_bar(self):
        top = ttk.Frame(self, padding=10)
        top.pack(fill="x")

        ttk.Label(top, text="Base de datos Access (.mdb):").pack(side="left")
        self.db_path_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.db_path_var, width=60).pack(side="left", padx=5)

        ttk.Button(top, text="Examinar...", command=self.browse_db).pack(side="left", padx=5)
        ttk.Button(top, text="Conectar", command=self.connect_db).pack(side="left", padx=5)

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
