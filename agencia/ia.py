"""Diagnóstico y propuesta personalizada con Claude."""
import json

import anthropic
from pydantic import BaseModel, Field

MODELO = "claude-opus-5-5"

SISTEMA = """Sos el analista comercial de DGLab, una consultora que crea soluciones digitales a medida \
(sistemas de gestión, turnos online, automatizaciones con IA) para ahorrarle tiempo a los negocios.

Recibís los datos públicos de un negocio y las señales que detectó un investigador automático. Tu trabajo:
1. Diagnosticar, en una o dos oraciones concretas, qué problema probablemente tiene y por qué lo creés \
(citá la señal: reseñas, ausencia de web, etc.). No inventes datos que no estén en la información.
2. Puntuar de 0 a 100 qué tan buen prospecto es (necesidad clara + posibilidad de contactarlo).
3. Elegir el paquete más adecuado de la lista.
4. Escribir el primer mensaje de contacto, listo para mandar por WhatsApp o Instagram:
   - castellano rioplatense, cálido y directo, tuteando; firma Agustín de DGLab;
   - máximo 5 líneas, sin precios, sin tecnicismos, sin exagerar;
   - mencioná algo específico del negocio para que se note que no es un mensaje masivo;
   - cerrá ofreciendo armarle una demo con su nombre, sin compromiso (todavía no está hecha: no digas que ya la tenés).
"""


class Diagnostico(BaseModel):
    diagnostico: str = Field(description="Problema probable y en qué señal se basa, 1-2 oraciones")
    puntaje: int = Field(description="0 a 100")
    paquete: str = Field(description="Nombre exacto de uno de los paquetes ofrecidos")
    mensaje: str = Field(description="Primer mensaje de contacto, listo para enviar")


def diagnosticar(negocio, campana, senales, puntaje_reglas):
    info = {
        "negocio": {k: negocio.get(k) for k in ("nombre", "zona", "direccion", "web", "instagram", "rating", "resenas")},
        "resenas_destacadas": (negocio.get("datos") or {}).get("resenas", [])[:5],
        "senales": senales,
        "puntaje_por_reglas": puntaje_reglas,
        "campana": {k: campana[k] for k in ("nombre", "problema", "solucion", "paquetes")},
    }
    client = anthropic.Anthropic()
    respuesta = client.messages.parse(
        model=MODELO,
        max_tokens=8000,
        system=SISTEMA,
        messages=[{"role": "user", "content": json.dumps(info, ensure_ascii=False, indent=1)}],
        output_format=Diagnostico,
    )
    if respuesta.stop_reason == "refusal" or respuesta.parsed_output is None:
        raise RuntimeError(f"La IA no devolvió un diagnóstico (motivo: {respuesta.stop_reason})")
    d = respuesta.parsed_output
    return {"diagnostico": d.diagnostico, "puntaje": max(0, min(100, d.puntaje)), "paquete": d.paquete, "mensaje": d.mensaje}
