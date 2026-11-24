"""Agente investigador + ofertador.

1) Señales concretas (sin IA): ¿tiene web?, ¿ya usa un sistema de turnos?, ¿atiende por WhatsApp?, ¿qué dicen las reseñas?
2) Diagnóstico y mensaje: con Claude si hay credenciales; si no, con reglas y una plantilla.
"""
import os
import re

import requests

from .buscador import UA

# Quejas en reseñas que delatan el problema que resolvemos.
QUEJAS = {
    "no contestan": r"no (contestan|responden|atienden)|nunca (contestan|responden)|imposible comunicarse",
    "esperas": r"esper[ée]|demora|tard[aó]|mucha espera",
    "turnos": r"turno|reserva|me cancelaron|no ten[ií]an mi turno",
}


def investigar_web(url, campana):
    """Lee la web del negocio y busca pistas. Nunca falla: si no carga, lo anota."""
    if not url:
        return {"web_ok": False}
    try:
        r = requests.get(url, headers=UA, timeout=15)
        html = r.text.lower()
    except requests.RequestException as e:
        return {"web_ok": False, "web_error": type(e).__name__}
    return {
        "web_ok": r.ok,
        "ya_resuelto": [p for p in campana.get("ya_resuelto", []) if p in html],
        "whatsapp_en_web": bool(re.search(r"wa\.me/|api\.whatsapp\.com|whatsapp", html)),
        "email_en_web": sorted(set(re.findall(r"[\w.+-]+@[\w-]+\.[\w.]+", html)))[:3],
        "instagram_en_web": bool(re.search(r"instagram\.com/", html)),
    }


def quejas_en_resenas(resenas):
    encontradas = {}
    for nombre, patron in QUEJAS.items():
        citas = [r["texto"][:220] for r in resenas if re.search(patron, r["texto"], re.I)]
        if citas:
            encontradas[nombre] = citas[:2]
    return encontradas


def senales(negocio, campana):
    s = investigar_web(negocio.get("web"), campana)
    s["tiene_web"] = bool(negocio.get("web"))
    s["tiene_instagram"] = bool(negocio.get("instagram"))
    s["tiene_telefono"] = bool(negocio.get("telefono"))
    s["quejas"] = quejas_en_resenas((negocio.get("datos") or {}).get("resenas", []))
    return s


def puntaje_reglas(negocio, s):
    """0-100: qué tan probable es que necesite la solución y que podamos contactarlo."""
    if s.get("ya_resuelto"):
        return 10, "Su web ya muestra un sistema de reservas."
    p, motivos = 40, []
    if not s["tiene_web"]:
        p += 20; motivos.append("no tiene web propia")
    elif not s.get("web_ok"):
        p += 10; motivos.append("su web no carga bien")
    if s.get("whatsapp_en_web"):
        p += 10; motivos.append("atiende por WhatsApp")
    if s["quejas"]:
        p += 10 + 5 * len(s["quejas"]); motivos.append("hay reseñas que se quejan de " + ", ".join(s["quejas"]))
    if (negocio.get("resenas") or 0) >= 50:
        p += 10; motivos.append("tiene mucho movimiento (muchas reseñas)")
    if not (s["tiene_telefono"] or s["tiene_instagram"] or s.get("email_en_web")):
        p -= 30; motivos.append("no encontramos cómo contactarlo")
    return max(0, min(100, p)), "; ".join(motivos).capitalize() + "."


def mensaje_plantilla(negocio, campana):
    return (
        f"¡Hola {negocio['nombre']}! Soy Agustín, de DGLab. Ayudamos a negocios como el tuyo a ahorrar tiempo: "
        f"por ejemplo, {campana['pitch']}. "
        "¿Querés que te arme una demo con tu nombre para que veas cómo quedaría? Sin compromiso."
    )


def analizar(negocio, campana, usar_ia=None):
    """Devuelve los campos a guardar: senales, puntaje, diagnostico, mensaje, paquete, analizado_con."""
    s = senales(negocio, campana)
    puntaje, motivo = puntaje_reglas(negocio, s)
    resultado = {"senales": s, "puntaje": puntaje, "diagnostico": motivo,
                 "mensaje": mensaje_plantilla(negocio, campana), "paquete": campana["paquetes"][0]["nombre"],
                 "analizado_con": "reglas"}
    if usar_ia is None:
        usar_ia = ia_disponible()
    if usar_ia and puntaje > 10:
        from . import ia
        resultado.update(ia.diagnosticar(negocio, campana, s, puntaje))
        resultado["analizado_con"] = "ia"
    return resultado


def ia_disponible():
    return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"))
