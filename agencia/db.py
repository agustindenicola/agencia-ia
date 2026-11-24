"""Base SQLite: los negocios encontrados y en qué paso del embudo está cada uno."""
import json
import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.environ.get("AGENCIA_DATA") or os.path.join(BASE_DIR, "datos")
DB_PATH = os.path.join(DATA_DIR, "agencia.db")

# nuevo -> analizado -> aprobado -> contactado ; o descartado
ESTADOS = ("nuevo", "analizado", "aprobado", "contactado", "descartado")

ESQUEMA = """
CREATE TABLE IF NOT EXISTS negocios (
  id INTEGER PRIMARY KEY,
  campana TEXT NOT NULL,
  fuente TEXT NOT NULL,
  fuente_id TEXT NOT NULL,
  nombre TEXT NOT NULL,
  zona TEXT,
  direccion TEXT,
  telefono TEXT,
  web TEXT,
  instagram TEXT,
  email TEXT,
  rating REAL,
  resenas INTEGER,
  maps_url TEXT,
  datos TEXT,            -- lo que trajo la fuente, crudo (json)
  senales TEXT,          -- lo que detectó el investigador (json)
  puntaje INTEGER,
  diagnostico TEXT,
  mensaje TEXT,
  paquete TEXT,
  analizado_con TEXT,    -- 'ia' o 'reglas'
  estado TEXT NOT NULL DEFAULT 'nuevo',
  creado TEXT DEFAULT (datetime('now','localtime')),
  actualizado TEXT DEFAULT (datetime('now','localtime')),
  UNIQUE(fuente, fuente_id)
);
"""

JSON_COLS = ("datos", "senales")


def conectar():
    os.makedirs(DATA_DIR, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.executescript(ESQUEMA)
    return con


def a_dict(row):
    d = dict(row)
    for col in JSON_COLS:
        d[col] = json.loads(d[col]) if d.get(col) else {}
    return d


def guardar_nuevo(con, campana, zona, n):
    """Inserta un negocio encontrado; si ya estaba (misma fuente e id) no lo duplica. Devuelve True si es nuevo."""
    cur = con.execute(
        "INSERT OR IGNORE INTO negocios (campana, fuente, fuente_id, nombre, zona, direccion, telefono, web, instagram,"
        " email, rating, resenas, maps_url, datos) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (campana, n["fuente"], n["fuente_id"], n["nombre"], zona, n.get("direccion"), n.get("telefono"), n.get("web"),
         n.get("instagram"), n.get("email"), n.get("rating"), n.get("resenas"), n.get("maps_url"),
         json.dumps(n.get("datos") or {}, ensure_ascii=False)),
    )
    return cur.rowcount == 1


def actualizar(con, nid, **campos):
    for col in JSON_COLS:
        if col in campos and not isinstance(campos[col], str):
            campos[col] = json.dumps(campos[col], ensure_ascii=False)
    sets = ", ".join(f"{k}=?" for k in campos)
    con.execute(f"UPDATE negocios SET {sets}, actualizado=datetime('now','localtime') WHERE id=?", (*campos.values(), nid))
    con.commit()


def listar(con, campana=None, estado=None):
    q, args = "SELECT * FROM negocios WHERE 1=1", []
    if campana:
        q += " AND campana=?"; args.append(campana)
    if estado:
        q += " AND estado=?"; args.append(estado)
    q += " ORDER BY (puntaje IS NULL), puntaje DESC, id DESC"
    return [a_dict(r) for r in con.execute(q, args)]


def obtener(con, nid):
    row = con.execute("SELECT * FROM negocios WHERE id=?", (nid,)).fetchone()
    return a_dict(row) if row else None
