# config.py
import json
import os

CONFIG_FILE = "config.json"

# ----------------------------
# VALORES PREDETERMINADOS
# ----------------------------
DEFAULT_CONFIG = {
    "db_path": ""     # ruta al archivo MDB
}


# ----------------------------
# Cargar configuración
# ----------------------------
def load_config():
    if not os.path.exists(CONFIG_FILE):
        # Si no existe, lo creamos con valores por defecto
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Garantiza que no falte ninguna clave por si actualizamos el formato
        for k, v in DEFAULT_CONFIG.items():
            data.setdefault(k, v)

        return data
    except Exception:
        # Si algo falla, devolvemos valores por defecto
        return DEFAULT_CONFIG.copy()


# ----------------------------
# Guardar configuración
# ----------------------------
def save_config(cfg: dict):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print("Error guardando config:", e)
