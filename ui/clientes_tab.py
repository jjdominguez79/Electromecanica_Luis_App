# ui/clientes_tab.py
import tkinter as tk
from tkinter import ttk, messagebox
from db import get_clientes

class ClientesTab(ttk.Frame):
    def __init__(self, parent, main_window):
        super().__init__(parent)
        self.main_window = main_window  # para acceder a get_conn(), notebook, etc.
        self.lista_clientes_completa = []

        self._build_ui()

    def _build_ui(self):
        filtro = ttk.LabelFrame(self, text="Buscar cliente", padding=10)
        filtro.pack(fill="x", padx=10, pady=5)

        ttk.Label(filtro, text="Nombre contiene:").pack(side="left")

        self.cliente_busqueda_var = tk.StringVar()
        entry = ttk.Entry(filtro, textvariable=self.cliente_busqueda_var, width=40)
        entry.pack(side="left", padx=5)
        entry.bind("<KeyRelease>", self.filtrar_clientes)

        cont = ttk.Frame(self)
        cont.pack(fill="both", expand=True, padx=10, pady=10)

        cols = ("nombre", "cif", "direccion")
        self.tree_clientes = ttk.Treeview(cont, columns=cols, show="headings")

        self.tree_clientes.heading("nombre", text="Nombre")
        self.tree_clientes.heading("cif", text="CIF")
        self.tree_clientes.heading("direccion", text="Dirección")

        self.tree_clientes.column("nombre", width=300, anchor="w")
        self.tree_clientes.column("cif", width=120, anchor="center")
        self.tree_clientes.column("direccion", width=350, anchor="w")

        self.tree_clientes.pack(side="left", fill="both", expand=True)

        scroll = ttk.Scrollbar(cont, orient="vertical", command=self.tree_clientes.yview)
        self.tree_clientes.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")

        acciones = ttk.Frame(self)
        acciones.pack(fill="x", pady=5)

        ttk.Button(
            acciones,
            text="Ver facturas del cliente",
            command=self.ver_facturas_cliente,
        ).pack(side="left", padx=5)

        ttk.Button(
            acciones,
            text="Ver trabajos del cliente",
            command=self.ver_trabajos_cliente,
        ).pack(side="left", padx=5)

    def on_db_connected(self):
        """Llamado desde MainWindow cuando se conecta a la BBDD."""
        conn = self.main_window.get_conn()
        if conn:
            self.cargar_clientes(conn)

    def cargar_clientes(self, conn):
        try:
            rows = get_clientes(conn)
        except Exception as e:
            messagebox.showerror("Error cargando clientes", str(e))
            return

        self.lista_clientes_completa = rows
        self.tree_clientes.delete(*self.tree_clientes.get_children())

        for r in rows:
            dom = r.DIRECCION if r.DIRECCION not in (None, "None") else ""
            self.tree_clientes.insert(
                "",
                "end",
                 values=(r.NOMBRE, r.CIF, dom)
            )

    def filtrar_clientes(self, event=None):
        texto = self.cliente_busqueda_var.get().lower()
        self.tree_clientes.delete(*self.tree_clientes.get_children())

        for r in self.lista_clientes_completa:
            if texto in (r.NOMBRE or "").lower():
                self.tree_clientes.insert("", "end", values=(r.NOMBRE, r.CIF, r.DIRECCION))

    def cliente_seleccionado(self):
        sel = self.tree_clientes.selection()
        if not sel:
            messagebox.showwarning("Sin selección", "Selecciona un cliente.")
            return None
        item = sel[0]
        return self.tree_clientes.item(item, "values")  # (nombre, cif, direccion)

    def ver_facturas_cliente(self):
        data = self.cliente_seleccionado()
        if not data:
            return
        nombre, cif, _ = data

        # Llamamos a la pestaña de facturas para que se filtre
        fact_tab = self.main_window.facturas_tab
        fact_tab.mostrar_facturas_de_cliente(nombre)

        # Cambiamos a la pestaña facturas
        self.main_window.notebook.select(fact_tab)

    def ver_trabajos_cliente(self):
        data = self.cliente_seleccionado()
        if not data:
            return
        nombre, cif, _ = data

        trab_tab = self.main_window.trabajos_tab
        trab_tab.mostrar_trabajos_de_cliente(nombre)
        self.main_window.notebook.select(trab_tab)
