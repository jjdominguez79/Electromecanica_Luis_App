# invoice_pdf.py
import os, sys
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

from db import get_facturas, get_lineas_factura

def resource_path(relative_path: str) -> str:
    """
    Devuelve la ruta correcta tanto en modo script como empaquetado con PyInstaller.
    """
    if hasattr(sys, "_MEIPASS"):  # ejecutando dentro del .exe
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(__file__)
    return os.path.join(base_path, relative_path)


def generar_pdf_factura(conn, numero_factura: str | int, ruta_salida: str):
    """
    Genera un PDF de la factura indicada en ruta_salida.
    Usa los datos de Facting y Contenid a través de db.py
    """
    numero_factura = str(numero_factura)

    # 1) Obtener cabecera
    facturas = get_facturas(conn, cliente=None, numero=numero_factura)
    if not facturas:
        raise ValueError(f"No se ha encontrado la factura {numero_factura}")

    cab = facturas[0]

    # 2) Obtener líneas
    lineas = get_lineas_factura(conn, numero_factura)

    # 3) Crear PDF
    c = canvas.Canvas(ruta_salida, pagesize=A4)
    width, height = A4

    margen_izq = 20 * mm
    margen_der = width - 20 * mm
    y = height - 20 * mm

    # ---- LOGOTIPO (arriba a la derecha) ----
    logo_ancho = 35 * mm      # ← los definimos SIEMPRE
    logo_alto = 35 * mm

    # Ruta del logo (ajusta el nombre de archivo)
    logo_path = resource_path("logo.jpg")

    if os.path.exists(logo_path):
        c.drawImage(
            logo_path,
            x=margen_der - logo_ancho,
            y=y - logo_alto + 5 * mm,
            width=logo_ancho,
            height=logo_alto,
            preserveAspectRatio=True,
            mask="auto",
        )
    
    # ahora puedes seguir usando y, margen_izq, etc. sin tocar logo_ancho más
    y -= 5 * mm

    # Cabecera empresa (puedes personalizarlo con tus datos)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margen_izq, y, "ELECTROMECANICA LUIS")
    y -= 5 * mm
    c.setFont("Helvetica", 9)
    c.drawString(margen_izq, y, "Luis Alfonso Jorge Portilla")
    y -= 5 * mm
    c.setFont("Helvetica", 9)
    c.drawString(margen_izq, y, "Crta. Gama 32")
    y -= 4 * mm
    c.drawString(margen_izq, y, "39360 Barcena de Cicero (Cantabria)")
    y -= 4 * mm
    c.drawString(margen_izq, y, "NIF: 72179705R")
    y -= 10 * mm

    # Título FACTURA
    c.setFont("Helvetica-Bold", 16)
    c.drawString(margen_izq, y, "FACTURA")
    y -= 10 * mm

    # Datos de factura
    c.setFont("Helvetica", 10)
    fecha = cab.FECHA
    if fecha is not None:
        try:
            fecha_str = fecha.strftime("%d/%m/%Y")
        except Exception:
            fecha_str = str(fecha)
    else:
        fecha_str = ""

    c.drawString(margen_izq, y, f"Nº: {cab.NUMERO}")
    c.drawString(margen_izq + 60 * mm, y, f"Fecha: {fecha_str}")
    y -= 8 * mm

    # Datos del cliente
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margen_izq, y, "Cliente:")
    y -= 5 * mm
    c.setFont("Helvetica", 10)
    c.drawString(margen_izq, y, f"{cab.CLIENTE}")
    y -= 5 * mm
    if getattr(cab, "CIF", None):
        c.drawString(margen_izq, y, f"CIF/NIF: {cab.CIF}")
        y -= 5 * mm

    y -= 5 * mm

    # Cabecera de la tabla de líneas
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margen_izq, y, "Código")
    c.drawString(margen_izq + 25 * mm, y, "Descripción")
    c.drawRightString(margen_der - 50 * mm, y, "Cantidad")
    c.drawRightString(margen_der - 30 * mm, y, "Precio")
    c.drawRightString(margen_der, y, "Importe")
    y -= 4 * mm
    c.line(margen_izq, y, margen_der, y)
    y -= 6 * mm

    c.setFont("Helvetica", 9)

    base_total = 0.0

    for lin in lineas:
        # Cambio de página si no cabe
        if y < 30 * mm:
            c.showPage()
            y = height - 20 * mm
            c.setFont("Helvetica-Bold", 10)
            c.drawString(margen_izq, y, "Continuación factura")
            y -= 10 * mm
            c.setFont("Helvetica", 9)

        codigo = getattr(lin, "Codigo", "") or ""
        desc = getattr(lin, "Datos", "") or ""
        cantidad = lin.CANTIDAD if lin.CANTIDAD is not None else 0
        precio = lin.PRECIO if lin.PRECIO is not None else 0
        try:
            cantidad_f = float(cantidad)
        except Exception:
            cantidad_f = 0.0
        try:
            precio_f = float(precio)
        except Exception:
            precio_f = 0.0

        importe = round(cantidad_f * precio_f, 2)
        base_total += importe

         # ---- WRAP DE LA DESCRIPCIÓN ----
        col_desc_x = margen_izq + 25 * mm
        # ancho máximo para la descripción (desde col_desc_x hasta antes de las columnas numéricas)
        max_desc_width = (margen_der - 55 * mm) - col_desc_x

        desc_lines = wrap_text(desc, "Helvetica", 9, max_desc_width, c)

        # Altura que va a ocupar esta línea de factura (puede ser varias líneas de texto)
        line_height = 5 * mm
        total_height = line_height * max(1, len(desc_lines))

        # Salto de página si no cabe
        if y - total_height < 30 * mm:
            c.showPage()
            y = height - 20 * mm
            c.setFont("Helvetica-Bold", 10)
            c.drawString(margen_izq, y, "Continuación factura")
            y -= 10 * mm
            c.setFont("Helvetica", 9)

        # Dibuja código, cantidades y precios alineados a la primera línea
        c.drawString(margen_izq, y, str(codigo)[:10])
        c.drawRightString(margen_der - 50 * mm, y, f"{cantidad_f:.2f}")
        c.drawRightString(margen_der - 30 * mm, y, f"{precio_f:.2f}")
        c.drawRightString(margen_der, y, f"{importe:.2f}")

        # Dibuja las líneas de descripción, una debajo de otra
        desc_y = y
        for line in desc_lines:
            c.drawString(col_desc_x, desc_y, line)
            desc_y -= line_height

        # Actualizamos y al final de este bloque
        y = desc_y - 2 * mm

    # Totales
    y -= 10 * mm
    c.setFont("Helvetica-Bold", 10)

    base = getattr(cab, "BASE1", None)
    iva = getattr(cab, "IVA1", None)
    total = getattr(cab, "TOTAL", None)

    # Si la base está a None usamos la suma calculada
    try:
        base_val = float(base) if base is not None else base_total
    except Exception:
        base_val = base_total

    # Intentamos calcular IVA si no viene
    if iva is None:
        # ejemplo 21% aproximado
        iva_val = round(base_val * 0.21, 2)
    else:
        try:
            iva_val = float(iva)
        except Exception:
            iva_val = 0.0

    if total is None:
        total_val = round(base_val + iva_val, 2)
    else:
        try:
            total_val = float(total)
        except Exception:
            total_val = round(base_val + iva_val, 2)

    c.drawRightString(margen_der - 30 * mm, y, "Base imponible:")
    c.drawRightString(margen_der, y, f"{base_val:.2f}")
    y -= 6 * mm
    c.drawRightString(margen_der - 30 * mm, y, "IVA:")
    c.drawRightString(margen_der, y, f"{iva_val:.2f}")
    y -= 6 * mm
    c.drawRightString(margen_der - 30 * mm, y, "TOTAL:")
    c.drawRightString(margen_der, y, f"{total_val:.2f}")

    c.showPage()
    c.save()

def wrap_text(text, font_name, font_size, max_width, canvas_obj):
    """
    Parte 'text' en varias líneas para que cada una no supere max_width.
    Devuelve una lista de líneas.
    """
    if not text:
        return [""]

    canvas_obj.setFont(font_name, font_size)
    words = str(text).split()
    lines = []
    current_line = ""

    for w in words:
        test_line = (current_line + " " + w).strip()
        if canvas_obj.stringWidth(test_line, font_name, font_size) <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = w

    if current_line:
        lines.append(current_line)

    return lines
