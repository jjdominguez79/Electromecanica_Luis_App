# update_checker.py
import urllib.request
from version import APP_VERSION

GITHUB_LATEST_VERSION_URL = "https://raw.githubusercontent.com/jjdominguez79/Electromecanica_Luis_App/refs/heads/main/latest_version.txt"


def parse_version(ver_str: str):
    """
    Convierte '1.2.3' en (1,2,3) para poder comparar.
    Si hay problemas, devuelve (0,0,0).
    """
    try:
        parts = ver_str.strip().split(".")
        return tuple(int(p) for p in parts)
    except Exception:
        return (0, 0, 0)


def get_remote_version() -> str | None:
    """
    Descarga la versión remota desde GitHub.
    Devuelve una cadena 'X.Y.Z' o None si falla.
    """
    try:
        with urllib.request.urlopen(GITHUB_LATEST_VERSION_URL, timeout=5) as resp:
            data = resp.read().decode("utf-8")
        ver = data.strip()
        if ver:
            return ver
        return None
    except Exception:
        return None


def is_update_available() -> tuple[bool, str | None]:
    """
    Compara la versión local con la remota.
    Devuelve (True, 'X.Y.Z') si hay versión nueva, o (False, None) si no.
    """
    local = parse_version(APP_VERSION)
    remote_str = get_remote_version()
    if not remote_str:
        return False, None

    remote = parse_version(remote_str)

    if remote > local:
        return True, remote_str
    else:
        return False, remote_str
