# Agencia IA

Herramienta de prospección de clientes: busca negocios de un rubro en una zona, investiga cada uno (sitio web, reseñas, señales de que necesita el servicio), le asigna un puntaje y redacta un mensaje de contacto personalizado. Todo contacto pasa por aprobación manual antes de enviarse.

## Cómo funciona

1. **Campañas**: cada campaña define un micro-nicho (rubro + problema + oferta), por ejemplo *peluquerías → turnos online* o *pymes con planillas → sistema de gestión*.
2. **Búsqueda**: consulta la API de Google Places si hay clave configurada; si no, usa OpenStreetMap (Overpass), sin costo.
3. **Investigación**: analiza el sitio web y las reseñas del negocio y detecta señales (por ejemplo, turnos solo por WhatsApp o quejas por demoras).
4. **Puntaje y diagnóstico**: un puntaje por reglas y, si está disponible, un diagnóstico con un modelo de lenguaje que devuelve **salida estructurada** validada con Pydantic.
5. **Panel de revisión**: cada negocio queda en una bandeja (*para revisar, aprobados, contactados, descartados*), con el mensaje editable y un link directo a WhatsApp.

## Stack

| Capa | Tecnología |
|---|---|
| Backend | Python 3, Flask, Waitress |
| Base de datos | SQLite |
| Integraciones | Google Places API, OpenStreetMap (Overpass), API de Claude |
| Validación | Pydantic (respuesta estructurada del modelo) |
| Calidad | pytest (11 tests, sin acceso a internet) |

## Arquitectura

```
agencia/
  campanas.py      definición de campañas (rubro, señales, oferta, plantilla)
  buscador.py      búsqueda en Google Places u OpenStreetMap
  investigador.py  señales, puntaje por reglas y mensaje de plantilla
  ia.py            diagnóstico con modelo de lenguaje (salida estructurada)
  importar.py      importación de listas de negocios
  db.py            persistencia SQLite
  server.py        API y panel
  static/          interfaz web
tests/
```

## Cómo correrlo

```bash
pip install -r requirements.txt
python run.py          # panel en http://127.0.0.1:8790
python -m pytest -q
```

Variables opcionales (ver `.env.ejemplo`): `GOOGLE_MAPS_API_KEY` para buscar en Google Maps y `ANTHROPIC_API_KEY` para el diagnóstico con modelo de lenguaje. Sin ellas funciona con OpenStreetMap y plantillas.

## Hoja de ruta

Próximas etapas (demos automáticas, seguimiento, aprendizaje y ejecución diaria en la nube): [docs/HOJA_DE_RUTA.md](docs/HOJA_DE_RUTA.md).
