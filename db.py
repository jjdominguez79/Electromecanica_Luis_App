# db.py
import pyodbc

def connect(db_path: str):
    conn_str = (
        r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
        rf"DBQ={db_path};"
    )
    return pyodbc.connect(conn_str)

def get_clientes(conn):
    cur = conn.cursor()
    cur.execute("SELECT NOMBRE, CIF, DIRECCION FROM Clientes ORDER BY NOMBRE;")
    rows = cur.fetchall()
    cur.close()
    return rows

def get_facturas(conn, cliente=None, numero=None):
    where = []
    params = []
    if cliente:
        where.append("CLIENTE LIKE ?")
        params.append(f"%{cliente}%")
    if numero:
        where.append("NUMERO = ?")
        params.append(numero)

    where_clause = ""
    if where:
        where_clause = "WHERE " + " AND ".join(where)

    query = f"""
        SELECT NUMERO, FECHA, CLIENTE, CIF, TOTAL, BASE1, IVA1
        FROM Facting
        {where_clause}
        ORDER BY FECHA DESC;
    """

    cur = conn.cursor()
    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close()
    return rows

def get_lineas_factura(conn, numero):
    query = """
        SELECT
            Codigo,
            Datos,
            CANTIDAD,
            PRECIO,
            (CANTIDAD * PRECIO) AS Importe
        FROM Contenid
        WHERE REFERENCIA = ?
    """
    cur = conn.cursor()
    cur.execute(query, (numero,))
    rows = cur.fetchall()
    cur.close()
    return rows

def get_trabajos(conn, cliente=None, texto=None):
    where = []
    params = []
    if cliente:
        where.append("f.CLIENTE LIKE ?")
        params.append(f"%{cliente}%")
    if texto:
        where.append("c.Datos LIKE ?")
        params.append(f"%{texto}%")
    where_clause = ""
    if where:
        where_clause = "WHERE " + " AND ".join(where)

    query = f"""
        SELECT f.FECHA, c.REFERENCIA, f.CLIENTE, c.Datos,
               c.CANTIDAD, c.PRECIO,
               (c.CANTIDAD * c.PRECIO) AS Importe
        FROM Contenid AS c
        INNER JOIN Facting AS f ON c.REFERENCIA = f.NUMERO
        {where_clause}
        ORDER BY f.FECHA DESC;
    """
    cur = conn.cursor()
    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close()
    return rows
