# DGLab · Agencia

Máquina de conseguir clientes: agentes que **buscan** negocios, los **investigan**, arman la **propuesta** y
(próximamente) la **demo** personalizada. Vos solo revisás, aprobás y cerrás.

Cada **campaña** es un micro-nicho (rubro + problema + oferta), definida en `agencia/campanas.py`.
Hoy hay dos: *Estética y peluquerías → turnos online* y *Pymes con planillas → sistema de gestión*.

## Cómo se usa

```bash
pip install -r requirements.txt
python run.py            # panel en http://127.0.0.1:8790
python -m pytest -q      # pruebas (no usan Internet)
```

En el panel: elegís campaña y zona → **Buscar e investigar** → revisás cada negocio (puntaje, señales,
diagnóstico y mensaje editable) → **Aprobar / Enviar por WhatsApp / Descartar**.

### Claves (opcionales, mejoran mucho los resultados)

| Variable | Para qué | Sin ella |
|---|---|---|
| `GOOGLE_MAPS_API_KEY` | Buscar en Google Maps: teléfono, web, rating y reseñas | Usa OpenStreetMap (gratis, pocos contactos en Argentina) |
| `ANTHROPIC_API_KEY` | Diagnóstico y mensaje personalizado con IA | Puntaje por reglas y mensaje de plantilla |

## Etapas

1. **Buscador + investigador + panel** ✅
2. **Demos automáticas**: a partir de las plantillas (turnos, gestión), una demo con nombre, logo y colores del
   negocio publicada en `demo.dglab-ar.com/<negocio>`, y el link en el mensaje.
3. **Contacto y seguimiento**: mail desde una casilla propia, recordatorio si no responde, aviso cuando contesta.
   WhatsApp solo con quien ya respondió (para no quemar el número).
4. **Que aprenda**: qué campañas, zonas y mensajes responden mejor; nuevas campañas.
5. **En la nube**: corre sola todos los días y te deja la lista lista a la mañana.

## Costos estimados (por mes, al arrancar)

- Google Maps: dentro del crédito gratuito mensual para algunos cientos de búsquedas.
- IA (Claude): unos centavos de dólar por negocio investigado.
- Servidor (etapa 5): ~USD 5–10.

Regla: nunca mandar mensajes masivos automáticos. Todo contacto en frío pasa por tu aprobación.
