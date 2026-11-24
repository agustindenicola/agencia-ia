"""Campañas: cada una es un micro-nicho (rubro + problema + oferta) que la máquina sale a buscar.

Para sumar un nicho nuevo alcanza con agregar un dict a CAMPANAS.
"""

CAMPANAS = {
    "estetica-turnos": {
        "nombre": "Estética y peluquerías → turnos online",
        "busqueda_google": ["peluquería", "barbería", "centro de estética", "salón de uñas"],
        "osm": '["shop"~"hairdresser|beauty"]',
        "problema": (
            "Coordina los turnos a mano por WhatsApp o teléfono: pierde tiempo respondiendo, "
            "tiene superposiciones y clientes que se olvidan del turno."
        ),
        "solucion": (
            "Sistema de turnos online con su marca: el cliente reserva, modifica o cancela solo, "
            "recibe recordatorio automático y el profesional maneja la agenda desde el celular."
        ),
        # Una línea, tuteando, para el mensaje de contacto.
        "pitch": "que tus clientes saquen, cambien o cancelen el turno solos, con recordatorio automático, y vos manejes la agenda desde el celular",
        "paquetes": [
            {"nombre": "Básico", "detalle": "Turnos online con su marca, recordatorios por mail y panel de agenda.", "precio": "instalación baja + abono mensual"},
            {"nombre": "Completo", "detalle": "Básico + página Web del negocio, servicios con precios y estadísticas.", "precio": "instalación + abono mensual"},
        ],
        # Si la web ya tiene alguna de estas, el negocio probablemente ya resolvió los turnos.
        "ya_resuelto": ["booksy", "fresha", "agendapro", "calendly", "setmore", "simplybook", "treatwell", "reservio", "turnos online", "reservar turno", "reservá tu turno", "book now"],
        "demo": "turnos",
    },
    "pymes-planillas": {
        "nombre": "Pymes con planillas → sistema de gestión",
        "busqueda_google": ["distribuidora", "agencia de autos", "corralón", "mayorista", "estudio contable"],
        "osm": '["shop"~"car|hardware|wholesale|doityourself"]',
        "problema": (
            "Lleva stock, ventas, cuentas o liquidaciones en Excel y mensajes: los números tardan en salir, "
            "hay errores y la información depende de una sola persona."
        ),
        "solucion": (
            "Sistema de gestión a medida que reemplaza las planillas: datos en un solo lugar, cálculos automáticos, "
            "reportes claros y acceso desde la compu o el celular."
        ),
        "pitch": "pasar las planillas a un sistema simple, con los números al día y sin depender de una sola persona",
        "paquetes": [
            {"nombre": "Tablero", "detalle": "Tablero con sus números claros a partir de sus planillas actuales.", "precio": "pago único + abono opcional"},
            {"nombre": "Sistema", "detalle": "Sistema de gestión a medida con usuarios, reportes y copias de seguridad.", "precio": "proyecto + abono mensual"},
        ],
        "ya_resuelto": [],
        "demo": "gestion",
    },
}
