"""Agente buscador: encuentra negocios de una campaña en una zona.

Usa Google Maps (Places API) si hay GOOGLE_MAPS_API_KEY; si no, OpenStreetMap (gratis, menos datos de contacto).
Todas las fuentes devuelven el mismo formato de negocio.
"""
import os
import re

import requests

UA = {"User-Agent": "DGLab-agencia/0.1 (labdglab@gmail.com)"}
GOOGLE_URL = "https://places.googleapis.com/v1/places:searchText"
GOOGLE_CAMPOS = ",".join([
    "places.id", "places.displayName", "places.formattedAddress", "places.nationalPhoneNumber",
    "places.internationalPhoneNumber", "places.websiteUri", "places.rating", "places.userRatingCount",
    "places.googleMapsUri", "places.reviews", "places.businessStatus", "nextPageToken",
])
OVERPASS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]


def fuente_activa():
    return "google" if os.environ.get("GOOGLE_MAPS_API_KEY") else "osm"


def buscar(campana, zona, limite=40):
    if fuente_activa() == "google":
        return buscar_google(campana, zona, limite)
    return buscar_osm(campana, zona, limite)


# ---------- Google Maps ----------

def buscar_google(campana, zona, limite=40):
    vistos, salida = set(), []
    for rubro in campana["busqueda_google"]:
        token = None
        while len(salida) < limite:
            cuerpo = {"textQuery": f"{rubro} en {zona}", "languageCode": "es", "pageSize": 20}
            if token:
                cuerpo["pageToken"] = token
            r = requests.post(GOOGLE_URL, json=cuerpo, timeout=30, headers={
                "X-Goog-Api-Key": os.environ["GOOGLE_MAPS_API_KEY"], "X-Goog-FieldMask": GOOGLE_CAMPOS})
            r.raise_for_status()
            datos = r.json()
            for p in datos.get("places", []):
                if p["id"] in vistos or p.get("businessStatus") not in (None, "OPERATIONAL"):
                    continue
                vistos.add(p["id"])
                salida.append(desde_google(p))
            token = datos.get("nextPageToken")
            if not token:
                break
        if len(salida) >= limite:
            break
    return salida[:limite]


def desde_google(p):
    resenas = [
        {"texto": (r.get("text") or {}).get("text", ""), "estrellas": r.get("rating")}
        for r in p.get("reviews", []) if (r.get("text") or {}).get("text")
    ]
    web = p.get("websiteUri")
    return {
        "fuente": "google",
        "fuente_id": p["id"],
        "nombre": (p.get("displayName") or {}).get("text", "Sin nombre"),
        "direccion": p.get("formattedAddress"),
        "telefono": p.get("internationalPhoneNumber") or p.get("nationalPhoneNumber"),
        # Muchos negocios ponen su Instagram como "sitio web".
        "web": None if es_instagram(web) else web,
        "instagram": web if es_instagram(web) else None,
        "rating": p.get("rating"),
        "resenas": p.get("userRatingCount"),
        "maps_url": p.get("googleMapsUri"),
        "datos": {"resenas": resenas},
    }


# ---------- OpenStreetMap ----------

def buscar_osm(campana, zona, limite=40):
    consulta = (
        f'[out:json][timeout:60];area["name"="{zona}"]["boundary"="administrative"]->.a;'
        f'(nwr{campana["osm"]}(area.a););out center tags {limite * 3};'
    )
    ultimo_error = None
    for url in OVERPASS:
        try:
            r = requests.post(url, data={"data": consulta}, headers=UA, timeout=90)
            r.raise_for_status()
            elementos = r.json()["elements"]
            break
        except (requests.RequestException, ValueError) as e:
            ultimo_error = e
    else:
        raise RuntimeError(f"OpenStreetMap no respondió: {ultimo_error}")
    salida = [desde_osm(e) for e in elementos if e.get("tags", {}).get("name")]
    return salida[:limite]


def desde_osm(e):
    t = e["tags"]
    web = t.get("website") or t.get("contact:website")
    ig = t.get("contact:instagram") or (web if es_instagram(web) else None)
    calle = " ".join(x for x in (t.get("addr:street"), t.get("addr:housenumber")) if x)
    return {
        "fuente": "osm",
        "fuente_id": f'{e["type"]}/{e["id"]}',
        "nombre": t["name"],
        "direccion": ", ".join(x for x in (calle, t.get("addr:city")) if x) or None,
        "telefono": t.get("phone") or t.get("contact:phone") or t.get("contact:whatsapp"),
        "web": None if es_instagram(web) else web,
        "instagram": ig,
        "email": t.get("email") or t.get("contact:email"),
        "maps_url": f'https://www.openstreetmap.org/{e["type"]}/{e["id"]}',
        "datos": {"horario": t.get("opening_hours")},
    }


def es_instagram(url):
    return bool(url) and bool(re.search(r"instagram\.com", url, re.I))
