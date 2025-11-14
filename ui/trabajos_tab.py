# ui/trabajos_tab.py
import tkinter as tk
from tkinter import ttk, messagebox

from db import get_trabajos


class TrabajosTab(ttk.Frame):
    """
    Pestaña para buscar y ver trabajos (líneas de factura).

    - Permite filtrar por cliente y texto en la descripción.
    - Muestra fecha, nº factura, cliente, descripción, cantidad, precio, importe.
    - Doble clic en un trabajo → salta a la pestaña de Facturas y muestra esa factura.
    """

    def __init__(self, parent, main_window):
        super().__init__(parent)
        self.main_window = main_window  # referencia a MainWindow

        # Variables de filtros
        self.trab_cliente_var = tk.StringVar()
        self.trab_texto_var = tk.StringVar()

        # Últimos trabajos cargados (por si se quiere reutilizar)
        self.lista_trabajos = []

        self._build_ui()

    # ---------------------------------------------------------
    # Construcción de la interfaz
    # ---------------------------------------------------------
    def _build_ui(self):
        filtros = ttk.LabelFrame(self, text="Filtros de trabajos", padding=10)
        filtros.pack(fill="x", padx=5, pady=5)

        ttk.Label(filtros, text="Cliente contiene:").grid(row=0, column=0, sticky="w")
        ttk.Entry(filtros, textvariable=self.trab_cliente_var, width=30).grid(
            row=0, column=1, padx=5
        )

        ttk.Label(filtros, text="Texto en descripción:").grid(
            row=0, column=2, sticky="w"
        )
        ttk.Entry(filtros, textvariable=self.trab_texto_var, width=30).grid(
            row=0, column=3, padx=5
        )

        ttk.Button(filtros, text="Buscar", command=self.buscar_trabajos).grid(
            row=0, column=4, padx=5
        )
        ttk.Button(filtros, text="Limpiar", command=self.limpiar_filtros_trabajos).grid(
            row=0, column=5, padx=5
        )

        for i in range(6):
            filtros.columnconfigure(i, weight=0)
        filtros.columnconfigure(1, weight=1)
        filtros.columnconfigure(3, weight=1)

        # ----- Listado de trabajos -----
        frame_lista = ttk.Frame(self)
        frame_lista.pack(fill="both", expand=True, padx=5, pady=5)

        cols = ("fecha", "numero", "cliente", "descripcion", "cantidad", "precio", "importe")
        self.tree_trabajos = ttk.Treeview(
            frame_lista, columns=cols, show="headings", selectmode="browse"
        )

        self.tree_trabajos.heading("fecha", text="Fecha")
        self.tree_trabajos.heading("numero", text="Nº factura")
        self.tree_trabajos.heading("cliente", text="Cliente")
        self.tree_trabajos.heading("descripcion", text="Descripción")
        self.tree_trabajos.heading("cantidad", text="Cant.")
        self.tree_trabajos.heading("precio", text="Precio")
        self.tree_trajos_heading_importe = self.tree_trabajos.heading("importe", text="Importe")

        self.tree_trabajos.column("fecha", width=90, anchor="center")
        self.tree_trabajos.column("numero", width=100, anchor="center")
        self.tree_trabajos.column("cliente", width=230, anchor="w")
        self.tree_trabajos.column("descripcion", width=320, anchor="w")
        self.tree_trabajos.column("cantidad", width=60, anchor="e")
        self.tree_trabajos.column("precio", width=80, anchor="e")
        self.tree_trabajos.column("importe", width=90, anchor="e")

        self.tree_trabajos.pack(side="left", fill="both", expand=True)

        scroll_t = ttk.Scrollbar(
            frame_lista, orient="vertical", command=self.tree_trabajos.yview
        )
        self.tree_trabajos.configure(yscrollcommand=scroll_t.set)
        scroll_t.pack(side="right", fill="y")

        # Doble clic en trabajo → ir a factura
        self.tree_trabajos.bind("<Double-1>", self.on_trabajo_dobleclick)

    # ---------------------------------------------------------
    # Hooks llamados desde MainWindow
    # ---------------------------------------------------------
    def on_db_connected(self):
        """
        Llamado desde MainWindow cuando se establece conexión con la BBDD.
        De momento no cargamos nada automáticamente.
        """
        self.limpiar_filtros_trabajos(reset_campos=False)

    # ---------------------------------------------------------
    # Lógica de búsqueda
    # ---------------------------------------------------------
    def limpiar_filtros_trabajos(self, reset_campos: bool = True):
        if reset_campos:
            self.trab_cliente_var.set("")
            self.trab_texto_var.set("")

        self.tree_trabajos.delete(*self.tree_trabajos.get_children())
        self.lista_trabajos = []

    def buscar_trabajos(self):
        conn = self.main_window.get_conn()
        if conn is None:
            return

        cliente = self.trab_cliente_var.get().strip()
        texto = self.trab_texto_var.get().strip()

        try:
            rows = get_trabajos(
                conn,
                cliente=cliente or None,
                texto=texto or None,
            )
        except Exception as e:
            messagebox.showerror(
                "Error al buscar trabajos",
                f"Revisa que la tabla Contenid y sus campos existan.\n\n{e}",
            )
            return

        self.lista_trabajos = rows
        self.tree_trabajos.delete(*self.tree_trabajos.get_children())

        for r in rows:
            fecha = r.FECHA
            fecha_str = ""
            if fecha is not None:
                try:
                    fecha_str = fecha.strftime("%d/%m/%Y")
                except Exception:
                    fecha_str = str(fecha)

            cantidad = r.CANTIDAD if r.CANTIDAD is not None else 0
            precio = r.PRECIO if r.PRECIO is not None else 0
            importe = getattr(r, "Importe", None)
            if importe is None:
                try:
                    importe = round(cantidad * precio, 2)
                except Exception:
                    importe = 0.00

            self.tree_trabajos.insert(
                "",
                "end",
                values=(
                    fecha_str,
                    r.REFERENCIA,
                    r.CLIENTE,
                    r.Datos,
                    cantidad,
                    precio,
                    importe,
                ),
            )

        if not rows:
            messagebox.showinfo("Sin resultados", "No se han encontrado trabajos.")

    # ---------------------------------------------------------
    # Doble clic: ir a factura
    # ---------------------------------------------------------
    def on_trabajo_dobleclick(self, event=None):
        sel = self.tree_trabajos.selection()
        if not sel:
            return
        item = sel[0]
        valores = self.tree_trabajos.item(item, "values")
        if not valores:
            return

        numero = valores[1]  # columna Nº factura

        # Cambiar a pestaña facturas y mostrar la factura
        fact_tab = self.main_window.facturas_tab
        fact_tab.mostrar_factura_por_numero(numero)
        self.main_window.notebook.select(fact_tab)

    # ---------------------------------------------------------
    # Métodos llamados desde otras pestañas
    # ---------------------------------------------------------
    def mostrar_trabajos_de_cliente(self, nombre_cliente: str):
        """
        Llamado desde ClientesTab para mostrar los trabajos
        de un cliente concreto.
        """
        self.trab_cliente_var.set(nombre_cliente)
        self.trab_texto_var.set("")
        self.buscar_trabajos()
