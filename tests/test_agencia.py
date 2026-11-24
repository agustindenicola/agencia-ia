"""Pruebas sin red: el buscador, el investigador y el panel con respuestas simuladas."""
import pytest

from agencia import buscador, db, investigador
from agencia.campanas import CAMPANAS

TURNOS = CAMPANAS["estetica-turnos"]


@pytest.fixture(autouse=True)
def base_temporal(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "agencia.db"))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    monkeypatch.delenv("GOOGLE_MAPS_API_KEY", raising=False)


def test_google_separa_instagram_de_la_web():
    n = buscador.desde_google({
        "id": "abc", "displayName": {"text": "Barbería Uno"}, "websiteUri": "https://instagram.com/barberiauno",
        "reviews": [{"text": {"text": "Nunca contestan el WhatsApp"}, "rating": 2}], "userRatingCount": 80,
    })
    assert n["web"] is None and n["instagram"].endswith("barberiauno")
    assert n["datos"]["resenas"][0]["estrellas"] == 2


def test_osm_arma_direccion_y_contacto():
    n = buscador.desde_osm({"type": "node", "id": 7, "tags": {
        "name": "Peluquería Sol", "addr:street": "Mitre", "addr:housenumber": "100", "addr:city": "Campana",
        "contact:phone": "+54 3489 111111"}})
    assert n["direccion"] == "Mitre 100, Campana" and n["telefono"] == "+54 3489 111111"


def test_quejas_en_resenas():
    q = investigador.quejas_en_resenas([{"texto": "Excelente corte pero nunca responden los mensajes"}, {"texto": "Todo bien"}])
    assert "no contestan" in q


def test_puntaje_sin_web_con_quejas_es_alto(monkeypatch):
    negocio = {"nombre": "X", "telefono": "123", "resenas": 120,
               "datos": {"resenas": [{"texto": "Imposible comunicarse para sacar turno"}]}}
    r = investigador.analizar(negocio, TURNOS)
    assert r["analizado_con"] == "reglas" and r["puntaje"] >= 80
    assert "DGLab" in r["mensaje"]


def test_si_ya_usa_reservas_queda_bajo(monkeypatch):
    monkeypatch.setattr(investigador, "investigar_web", lambda url, c: {"web_ok": True, "ya_resuelto": ["booksy"]})
    r = investigador.analizar({"nombre": "Y", "web": "https://y.com", "telefono": "1"}, TURNOS)
    assert r["puntaje"] == 10


def test_sin_forma_de_contacto_baja(monkeypatch):
    r = investigador.analizar({"nombre": "Z"}, TURNOS)
    assert r["puntaje"] < 50


def test_whatsapp_usa_el_primer_telefono():
    from agencia.server import link_whatsapp

    assert link_whatsapp("+54 341 297-6104; +54 341 662-2312", "Hola").startswith("https://wa.me/5493412976104?")
    assert link_whatsapp(None, "Hola") is None


def test_whatsapp_agrega_9_a_celulares_argentinos():
    from agencia.server import link_whatsapp

    assert link_whatsapp("+543489599932", "x").startswith("https://wa.me/5493489599932?")   # celular Campana
    assert link_whatsapp("+543489430645", "x").startswith("https://wa.me/543489430645?")    # fijo (empieza con 4)
    assert link_whatsapp("+5493489594230", "x").startswith("https://wa.me/5493489594230?")  # ya tenía el 9
    assert link_whatsapp("+541132924812", "x").startswith("https://wa.me/5491132924812?")   # celular CABA


def test_importar_csv(tmp_path):
    from agencia import importar

    csv_ = tmp_path / "p.csv"
    csv_.write_text("nombre,zona,telefono,resenas,mensaje\nBarbería X,Campana,+543489555475,40,Hola X!\nPelu Y,Zárate,,,\n", encoding="utf-8")
    assert importar.importar(str(csv_), "estetica-turnos") == 2
    assert importar.importar(str(csv_), "estetica-turnos") == 0
    lista = {n["nombre"]: n for n in db.listar(db.conectar(), estado="analizado")}
    assert lista["Barbería X"]["mensaje"] == "Hola X!" and lista["Barbería X"]["analizado_con"] == "manual"
    assert "DGLab" in lista["Pelu Y"]["mensaje"]


def test_no_duplica_negocios():
    con = db.conectar()
    n = {"fuente": "osm", "fuente_id": "node/1", "nombre": "A"}
    assert db.guardar_nuevo(con, "estetica-turnos", "Campana", n)
    assert not db.guardar_nuevo(con, "estetica-turnos", "Campana", n)


def test_panel_busca_investiga_y_aprueba(monkeypatch):
    from agencia import server

    falsos = [buscador.desde_osm({"type": "node", "id": i, "tags": {"name": f"Peluquería {i}", "phone": "+54 9 11 5555 000" + str(i)}})
              for i in range(3)]
    monkeypatch.setattr(buscador, "buscar", lambda c, z, l: falsos)
    # Corre la tarea en el mismo hilo para poder verificar el resultado.
    monkeypatch.setattr(server.threading, "Thread", lambda target, args, daemon: type("T", (), {"start": lambda self: target(*args)})())
    cliente = server.create_app().test_client()

    assert cliente.post("/api/buscar", json={"campana": "estetica-turnos", "zona": "Campana"}).status_code == 200
    lista = cliente.get("/api/negocios?estado=analizado").get_json()
    assert len(lista) == 3 and all(n["whatsapp_url"].startswith("https://wa.me/549115555") for n in lista)

    nid = lista[0]["id"]
    r = cliente.post(f"/api/negocios/{nid}", json={"estado": "aprobado", "mensaje": "Hola!"}).get_json()
    assert r["estado"] == "aprobado" and r["whatsapp_url"].endswith("text=Hola%21")
    assert cliente.post(f"/api/negocios/{nid}", json={"estado": "cualquiera"}).status_code == 400
    assert cliente.post("/api/buscar", json={"campana": "estetica-turnos", "zona": " "}).status_code == 400
