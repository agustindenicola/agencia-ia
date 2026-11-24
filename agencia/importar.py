"""Carga negocios encontrados a mano (directorios, Instagram, búsquedas) desde un CSV.

Uso: python -m agencia.importar archivo.csv <campana>
Columnas: nombre,zona,direccion,telefono,web,instagram,rating,resenas,fuente_url[,mensaje]
Si la fila trae "mensaje", se usa ese (personalizado) en lugar de la plantilla.
"""
import csv
import sys

from . import db, investigador
from .campanas import CAMPANAS


def importar(ruta, campana_id):
    campana = CAMPANAS[campana_id]
    con = db.conectar()
    nuevos = 0
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        for fila in csv.DictReader(f):
            n = {
                "fuente": "manual",
                "fuente_id": f'{fila["nombre"].strip().lower()}|{fila.get("zona", "").strip().lower()}',
                "nombre": fila["nombre"].strip(),
                "direccion": fila.get("direccion") or None,
                "telefono": fila.get("telefono") or None,
                "web": fila.get("web") or None,
                "instagram": fila.get("instagram") or None,
                "rating": float(fila["rating"]) if fila.get("rating") else None,
                "resenas": int(fila["resenas"]) if fila.get("resenas") else None,
                "maps_url": fila.get("fuente_url") or None,
            }
            if not db.guardar_nuevo(con, campana_id, fila.get("zona") or None, n):
                continue
            nuevos += 1
            nid = con.execute("SELECT id FROM negocios WHERE fuente='manual' AND fuente_id=?", (n["fuente_id"],)).fetchone()[0]
            analisis = investigador.analizar(n, campana, usar_ia=False)
            if fila.get("mensaje"):
                analisis.update(mensaje=fila["mensaje"], analizado_con="manual")
            db.actualizar(con, nid, estado="analizado", **analisis)
    con.commit()
    return nuevos


if __name__ == "__main__":
    print(f"{importar(sys.argv[1], sys.argv[2])} negocios nuevos cargados.")
