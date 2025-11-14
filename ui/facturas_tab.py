# ui/facturas_tab.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from invoice_pdf import generar_pdf_factura
import os

from db import get_facturas, get_lineas_factura


class FacturasTab(ttk.Frame):
    """
    Pestaña de gestión y consulta de facturas.

    - Permite buscar por cliente y nº de factura.
    - Muestra listado de facturas.
    - Al seleccionar una factura, muestra cabecera + líneas.
    - Se puede invocar desde la pestaña de clientes o trabajos
      para mostrar facturas de un cliente o una factura concreta.
    """

    def __init__(self, parent, main_window):
        super().__init__(parent)
        self.main_window = main_window  # referencia a MainWindow

        # Variables de filtros
        self.fact_cliente_var = tk.StringVar()
        self.fact_numero_var = tk.StringVar()

        # Estructuras de datos en memoria
        self.lista_facturas = []  # para guardar el resultado de la última búsqueda

        self.factura_actual_numero = None

        self._build_ui()

    # ---------------------------------------------------------
    # Construcción de la interfaz
    # ---------------------------------------------------------
    def _build_ui(self):
        # ----- Filtros -----
        filtros = ttk.LabelFrame(self, text="Filtros de búsqueda", padding=10)
        filtros.pack(fill="x", pady=5, padx=5)

        ttk.Label(filtros, text="Cliente contiene:").grid(row=0, column=0, sticky="w")
        ttk.Entry(filtros, textvariable=self.fact_cliente_var, width=30).grid(
            row=0, column=1, padx=5
        )

        ttk.Label(filtros, text="Nº factura:").grid(row=0, column=2, sticky="w")
        ttk.Entry(filtros, textvariable=self.fact_numero_var, width=15).grid(
            row=0, column=3, padx=5
        )

        ttk.Button(filtros, text="Buscar", command=self.buscar_facturas).grid(
            row=0, column=4, padx=5
        )
        ttk.Button(filtros, text="Limpiar", command=self.limpiar_filtros_facturas).grid(
            row=0, column=5, padx=5
        )

        for i in range(6):
            filtros.columnconfigure(i, weight=0)
        filtros.columnconfigure(1, weight=1)

        # ----- Split listado / detalle -----
        split = ttk.PanedWindow(self, orient="vertical")
        split.pack(fill="both", expand=True, padx=5, pady=5)

        # ----- Listado de facturas -----
        frame_lista = ttk.Frame(split)
        split.add(frame_lista, weight=3)

        columnas = ("numero", "fecha", "cliente", "cif", "total")
        self.tree_facturas = ttk.Treeview(
            frame_lista,
            columns=columnas,
            show="headings",
            selectmode="browse",
        )
        self.tree_facturas.heading("numero", text="Nº factura")
        self.tree_facturas.heading("fecha", text="Fecha")
        self.tree_facturas.heading("cliente", text="Cliente")
        self.tree_facturas.heading("cif", text="CIF")
        self.tree_facturas.heading("total", text="Total")

        self.tree_facturas.column("numero", width=100, anchor="center")
        self.tree_facturas.column("fecha", width=90, anchor="center")
        self.tree_facturas.column("cliente", width=350, anchor="w")
        self.tree_facturas.column("cif", width=120, anchor="center")
        self.tree_facturas.column("total", width=100, anchor="e")

        self.tree_facturas.pack(side="left", fill="both", expand=True)

        scroll_f = ttk.Scrollbar(
            frame_lista, orient="vertical", command=self.tree_facturas.yview
        )
        self.tree_facturas.configure(yscrollcommand=scroll_f.set)
        scroll_f.pack(side="right", fill="y")

        self.tree_facturas.bind("<<TreeviewSelect>>", self.on_factura_select)

        # ----- Detalle factura -----
        frame_detalle = ttk.Frame(split)
        split.add(frame_detalle, weight=2)

        # Cabecera
        self.detalle_cabecera = ttk.LabelFrame(
            frame_detalle, text="Cabecera factura", padding=10
        )
        self.detalle_cabecera.pack(fill="x", padx=5, pady=5)

        self.lbl_factura_info = ttk.Label(
            self.detalle_cabecera,
            text="Seleccione una factura...",
            justify="left",
        )
        self.lbl_factura_info.pack(anchor="w")

        # Botón para PDF
        self.btn_pdf = ttk.Button(
            self.detalle_cabecera,
            text="Guardar factura en PDF",
            command=self.exportar_pdf_factura,
        )
        self.btn_pdf.pack(anchor="e", pady=(5, 0))

        self.lbl_factura_info = ttk.Label(
            self.detalle_cabecera,
            text="Seleccione una factura...",
            justify="left",
        )
        self.lbl_factura_info.pack(anchor="w")

        # Líneas
        self.detalle_lineas = ttk.LabelFrame(
            frame_detalle, text="Líneas / trabajos", padding=5
        )
        self.detalle_lineas.pack(fill="both", expand=True, padx=5, pady=5)

        cols_lin = ("codigo", "descripcion", "cantidad", "precio", "importe")
        self.tree_lineas = ttk.Treeview(
            self.detalle_lineas,
            columns=cols_lin,
            show="headings",
            selectmode="browse",
        )

        for col, txt, w, anchor in [
            ("codigo", "Código", 80, "center"),
            ("descripcion", "Descripción", 400, "w"),
            ("cantidad", "Cant.", 60, "e"),
            ("precio", "Precio", 80, "e"),
            ("importe", "Importe", 90, "e"),
        ]:
            self.tree_lineas.heading(col, text=txt)
            self.tree_lineas.column(col, width=w, anchor=anchor)

        self.tree_lineas.pack(side="left", fill="both", expand=True)

        scroll_l = ttk.Scrollbar(
            self.detalle_lineas, orient="vertical", command=self.tree_lineas.yview
        )
        self.tree_lineas.configure(yscrollcommand=scroll_l.set)
        scroll_l.pack(side="right", fill="y")

    # ---------------------------------------------------------
    # Hooks llamados desde MainWindow
    # ---------------------------------------------------------
    def on_db_connected(self):
        """
        Llamado desde MainWindow cuando se establece conexión con la BBDD.
        De momento no cargamos nada automáticamente.
        """
        self.limpiar_filtros_facturas(reset_campos=False)

    # ---------------------------------------------------------
    # LÓGICA DE BÚSQUEDA Y DETALLE
    # ---------------------------------------------------------
    def limpiar_filtros_facturas(self, reset_campos: bool = True):
        if reset_campos:
            self.fact_cliente_var.set("")
            self.fact_numero_var.set("")

        # Limpiar tablas
        self.tree_facturas.delete(*self.tree_facturas.get_children())
        self.tree_lineas.delete(*self.tree_lineas.get_children())
        self.lbl_factura_info.config(text="Seleccione una factura...")

        self.lista_facturas = []

    def buscar_facturas(self):
        conn = self.main_window.get_conn()
        if conn is None:
            return

        cliente = self.fact_cliente_var.get().strip()
        numero = self.fact_numero_var.get().strip()

        try:
            rows = get_facturas(conn, cliente=cliente or None, numero=numero or None)
        except Exception as e:
            messagebox.showerror("Error al buscar facturas", str(e))
            return

        # Guardamos para posible uso posterior
        self.lista_facturas = rows

        # Limpiar listado
        self.tree_facturas.delete(*self.tree_facturas.get_children())
        self.tree_lineas.delete(*self.tree_lineas.get_children())
        self.lbl_factura_info.config(text="Seleccione una factura...")

        for r in rows:
            fecha = r.FECHA
            fecha_str = ""
            if fecha is not None:
                try:
                    fecha_str = fecha.strftime("%d/%m/%Y")
                except Exception:
                    fecha_str = str(fecha)
                    
            total = round(float(r.TOTAL or 0), 2),
            self.tree_facturas.insert(
                "",
                "end",
                values=(r.NUMERO, fecha_str, r.CLIENTE, r.CIF, total),
            )

        if not rows:
            messagebox.showinfo("Sin resultados", "No se han encontrado facturas.")

    def on_factura_select(self, event=None):
        sel = self.tree_facturas.selection()
        if not sel:
            return
        item = sel[0]
        numero = self.tree_facturas.item(item, "values")[0]
        self.cargar_detalle_factura(numero)
        
        # Guardamos el número seleccionado
        self.factura_actual_numero = numero   # ← AÑADIDO

    def cargar_detalle_factura(self, numero):
        """
        Carga cabecera + líneas de la factura seleccionada.
        """
        conn = self.main_window.get_conn()
        if conn is None:
            return
        
        # Aseguramos que queda guardado
        self.factura_actual_numero = numero   # ← AÑADIDO

        # 1) Cabecera: intentamos cogerla de la lista ya cargada
        cabecera = None
        for r in self.lista_facturas:
            if str(r.NUMERO) == str(numero):
                cabecera = r
                break

        # Si no estaba en lista_facturas (por ejemplo, llamada directa)
        if cabecera is None:
            try:
                filas = get_facturas(conn, cliente=None, numero=numero)
                if filas:
                    cabecera = filas[0]
            except Exception as e:
                messagebox.showerror("Error cabecera factura", str(e))
                return

        if cabecera is None:
            self.lbl_factura_info.config(
                text=f"No se ha encontrado la factura {numero}"
            )
            return

        fecha = cabecera.FECHA
        fecha_str = ""
        if fecha is not None:
            try:
                fecha_str = fecha.strftime("%d/%m/%Y")
            except Exception:
                fecha_str = str(fecha)

        txt = (
            f"Nº factura: {cabecera.NUMERO}    Fecha: {fecha_str}\n"
            f"Cliente: {cabecera.CLIENTE}\n"
            f"CIF: {cabecera.CIF}\n"
            f"Base: {cabecera.BASE1}   IVA: {cabecera.IVA1}   Total: {cabecera.TOTAL}"
        )
        self.lbl_factura_info.config(text=txt)

        # 2) Líneas
        try:
            lineas = get_lineas_factura(conn, numero)
        except Exception as e:
            messagebox.showerror("Error líneas factura", str(e))
            return

        self.tree_lineas.delete(*self.tree_lineas.get_children())

        for r in lineas:
            cantidad = r.CANTIDAD if r.CANTIDAD is not None else 0
            precio = r.PRECIO if r.PRECIO is not None else 0
            importe = getattr(r, "Importe", None)
            if importe is None:
                try:
                    importe = round(cantidad * precio, 2)
                except Exception:
                    importe = 0.00

            self.tree_lineas.insert(
                "",
                "end",
                values=(r.Codigo, r.Datos, cantidad, precio, importe),
            )

    # ---------------------------------------------------------
    # Métodos llamados desde otras pestañas
    # ---------------------------------------------------------
    def mostrar_facturas_de_cliente(self, nombre_cliente: str):
        """
        Llamado desde ClientesTab para mostrar todas las facturas
        de un cliente concreto.
        """
        self.fact_cliente_var.set(nombre_cliente)
        self.fact_numero_var.set("")
        self.buscar_facturas()

    def mostrar_factura_por_numero(self, numero):
        """
        Llamado desde TrabajosTab (p.ej. doble clic en un trabajo)
        para ir directamente a una factura concreta.
        """
        self.fact_cliente_var.set("")
        self.fact_numero_var.set(str(numero))
        self.buscar_facturas()
        self.cargar_detalle_factura(numero)

    def exportar_pdf_factura(self):
        conn = self.main_window.get_conn()
        if conn is None:
            return

        numero = getattr(self, "factura_actual_numero", None)
        if not numero:
            messagebox.showwarning(
                "Sin factura",
                "Primero selecciona una factura para poder generar el PDF.",
            )
            return

        # Elegir ruta de guardado
        default_name = f"Factura_{numero}.pdf"
        ruta = filedialog.asksaveasfilename(
            title="Guardar factura en PDF",
            defaultextension=".pdf",
            initialfile=default_name,
            filetypes=[("PDF", "*.pdf"), ("Todos los archivos", "*.*")],
        )
        if not ruta:
            return  # usuario ha cancelado

        try:
            generar_pdf_factura(conn, numero, ruta)
        except Exception as e:
            messagebox.showerror(
                "Error al generar PDF",
                f"No se ha podido generar el PDF de la factura {numero}.\n\n{e}",
            )
            return

        messagebox.showinfo(
            "PDF generado",
            f"Se ha generado el PDF de la factura {numero}:\n{ruta}",
        )

        # En Windows, abrir directamente el PDF
        try:
            if os.name == "nt":
                os.startfile(ruta)
        except Exception:
            pass