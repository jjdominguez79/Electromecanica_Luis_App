# ⚙️ Electromecánica Luis – Gestor de Facturas, Clientes y Trabajos

Aplicación de escritorio desarrollada en **Python** con **Tkinter + ttkbootstrap**, diseñada para talleres de electromecánica que utilizan bases de datos **Microsoft Access**.

Permite a los usuarios:

- Buscar clientes con un filtro dinámico.
- Ver sus facturas.
- Ver los trabajos realizados.
- Consultar el detalle de cada factura.
- Exportar facturas a **PDF profesional**, con logotipo, totales e IVA.
- Conectarse a cualquier base de datos Access (`.mdb` o `.accdb`).
- Generar un ejecutable para distribución en otros equipos.

Esta herramienta está adaptada especialmente para **Electromecánica Luis** y puede personalizarse fácilmente.

---

## 🚀 Tecnologías utilizadas

- **Python 3.10+**
- **Tkinter** (interfaz gráfica)
- **ttkbootstrap** (estilos modernos)
- **pyodbc** (conexión a Access)
- **reportlab** (generación de facturas en PDF)
- **PyInstaller** (para generar el ejecutable)

---

## 📂 Estructura del proyecto

.
├── app.py → Archivo principal de ejecución
├── db.py → Conexión y consultas a Access
├── config.py → Utilidades de configuración
├── invoice_pdf.py → Generación de facturas en PDF
│
├── ui/
│ ├── main_window.py → Ventana principal (Tkinter)
│ ├── clientes_tab.py → Pestaña de clientes
│ ├── facturas_tab.py → Pestaña de facturas
│ ├── trabajos_tab.py → Pestaña de trabajos
│ └── init.py
│
├── logo.jpg → Logo para el PDF
│
├── .gitignore → Ignora binarios y archivos generados
└── README.md → Este archivo


---

## 🧩 Instalación

### 1. Crear un entorno virtual

```
python -m venv venv
```

### 2. Activar el entorno virtualActivar:

Windows

``` 
venv\Scripts\activate
```

Linux / macOS

```
source venv/bin/activate
```

### 3. Instalar dependencias necesarias

````
pip install pyodbc reportlab ttkbootstrap pyinstaller
````

### 4. Conexión con la base de datos Access

La aplicación soporta:

.mdb / .accdb

Al iniciar, el usuario solo debe pulsar Examinar → seleccionar la base de datos → y el sistema la carga automáticamente.

### 5. Generación de facturas en PDF

El sistema genera PDFs profesionales con:

Logotipo corporativo
Datos del taller
Datos del cliente
Líneas de factura con descripción ajustada (multilínea)
Totales, IVA, Base imponible
Saltos de página automáticos

### 6. Crear versión ejecutable (.exe)

Ejecuta:
```
pyinstaller app.py --name "Electromecanica Luis" --noconsole --add-data "Logo.jpg;."
```

El ejecutable estará en: dist/Electromecanica Luis/Electromecanica Luis.exe

Este .exe puede copiarse y usarse en cualquier equipo Windows.


### 7. Licencia

Este software es propiedad de Electromecánica Luis y la implementación técnica por Asesoría Gestinem SL. No está permitido su uso, distribución o edición sin autorización expresa.

### 8. Autor

Aplicación desarrollada por Asesoría Gestinem SL, Santander, Cantabria – CIF B16916967