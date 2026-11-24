"""Panel de la agencia: buscar, revisar y aprobar prospectos."""
import logging
import re
import threading
from urllib.parse import quote

from flask import Flask, jsonify, request, send_from_directory

from . import buscador, db, investigador
from .campanas import CAMPANAS

log = logging.getLogger("agencia")

# Una sola tarea larga a la vez (buscar + analizar), con su progreso para mostrar en el panel.
TAREA = {"activa": False, "texto": "", "error": None}
_lock = threading.Lock()


def link_whatsapp(telefono, mensaje):
    # Algunos negocios cargan varios teléfonos ("+54 341 111; +54 341 222"): se usa el primero.
    primero = re.split(r"[;,/]", telefono or "")[0]
    numero = "".join(c for c in primero if c.isdigit())
    # WhatsApp necesita el 9 de celular en Argentina (54 9 ...). Los fijos suelen empezar con 4 después
    # de la característica: a esos no se les agrega (igual casi nunca tienen WhatsApp).
    if numero.startswith("54") and not numero.startswith("549") and len(numero) == 12:
        resto = numero[2:]
        caracteristica = 2 if resto.startswith("11") else 4 if resto[:1] in "23" else 3
        if resto[caracteristica] != "4":
            numero = "549" + resto
    return f"https://wa.me/{numero}?text={quote(mensaje or '')}" if numero else None


def para_panel(n):
    n["whatsapp_url"] = link_whatsapp(n.get("telefono"), n.get("mensaje"))
    n.pop("datos", None)
    return n


def correr_busqueda(campana_id, zona, limite, analizar):
    campana = CAMPANAS[campana_id]
    try:
        TAREA.update(texto=f"Buscando en {zona} ({buscador.fuente_activa()})…", error=None)
        encontrados = buscador.buscar(campana, zona, limite)
        con = db.conectar()
        nuevos = [n for n in encontrados if db.guardar_nuevo(con, campana_id, zona, n)]
        con.commit()
        TAREA["texto"] = f"{len(encontrados)} encontrados, {len(nuevos)} nuevos."
        if analizar:
            correr_analisis(con, campana_id)
    except Exception as e:  # noqa: BLE001 - se muestra en el panel
        log.exception("Falló la búsqueda")
        TAREA["error"] = str(e)
    finally:
        TAREA["activa"] = False


def correr_analisis(con, campana_id):
    pendientes = db.listar(con, campana_id, "nuevo")
    for i, n in enumerate(pendientes, 1):
        TAREA["texto"] = f"Investigando {i} de {len(pendientes)}: {n['nombre']}"
        try:
            db.actualizar(con, n["id"], estado="analizado", **investigador.analizar(n, CAMPANAS[n["campana"]]))
        except Exception as e:  # noqa: BLE001 - un negocio que falla no frena al resto
            log.warning("No se pudo analizar %s: %s", n["nombre"], e)
    TAREA["texto"] = f"Listo: {len(pendientes)} negocios investigados."


def create_app():
    app = Flask(__name__, static_folder="static")

    @app.get("/")
    def inicio():
        return send_from_directory(app.static_folder, "index.html")

    @app.get("/api/estado")
    def estado():
        return jsonify(
            tarea=TAREA, fuente=buscador.fuente_activa(), ia=investigador.ia_disponible(),
            campanas=[{"id": k, "nombre": v["nombre"]} for k, v in CAMPANAS.items()],
        )

    @app.get("/api/negocios")
    def negocios():
        con = db.conectar()
        return jsonify([para_panel(n) for n in db.listar(con, request.args.get("campana"), request.args.get("estado"))])

    @app.post("/api/buscar")
    def buscar():
        d = request.get_json(force=True)
        if d.get("campana") not in CAMPANAS or not (d.get("zona") or "").strip():
            return jsonify(error="Elegí una campaña y escribí una zona."), 400
        with _lock:
            if TAREA["activa"]:
                return jsonify(error="Ya hay una búsqueda en curso."), 409
            TAREA.update(activa=True, texto="Arrancando…", error=None)
        limite = max(1, min(60, int(d.get("limite") or 20)))
        threading.Thread(target=correr_busqueda, args=(d["campana"], d["zona"].strip(), limite, True), daemon=True).start()
        return jsonify(ok=True)

    @app.post("/api/negocios/<int:nid>")
    def editar(nid):
        d = request.get_json(force=True)
        campos = {k: d[k] for k in ("estado", "mensaje") if k in d}
        if campos.get("estado") and campos["estado"] not in db.ESTADOS:
            return jsonify(error="Estado inválido"), 400
        con = db.conectar()
        if not db.obtener(con, nid):
            return jsonify(error="No existe"), 404
        db.actualizar(con, nid, **campos)
        return jsonify(para_panel(db.obtener(con, nid)))

    return app
