"""Genera las colecciones del panel operativo (SCRUM-105) y de la geocodificación con el buzón (SCRUM-458) contra QA.

Uso: python tests/e2e/generar-scrum105-458.py
Escribe scrum-105-panel-operativo.postman_collection.json y scrum-458-geocodificacion-buzon.postman_collection.json.
Reutiliza la preparación de generar-scrum490-96-cotizacion-evidencia.py (administrador, categoría propia, técnico aprobado
y disponible, dos clientes y un cliente del tenant Beta), que también regenera sus dos colecciones sin cambios.

Contratos: service-request.v1.yaml 1.8.0 (resumen y lista del administrador, vista de plataforma, location-preview y
creación con solo la dirección) y communication.v1.yaml 1.2.0 (buzón). Necesita al administrador del tenant
(adminEmail y adminPassword); la vista de plataforma se prueba solo si llegan platformAdminEmail y platformAdminPassword.
Son secretos de QA que nunca van al repositorio. Correr con --reporters cli: el reporte JSON de Newman guarda tokens.
"""
import importlib.util
import json
import pathlib

AQUI = pathlib.Path(__file__).parent
_spec = importlib.util.spec_from_file_location("base", AQUI / "generar-scrum490-96-cotizacion-evidencia.py")
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)

JSON, CORR, CANAL, auth, req, estado, error = base.JSON, base.CORR, base.CANAL, base.auth, base.req, base.estado, base.error
reintentar = base.reintentar

WEB = {"key": "X-Channel-Id", "value": "quickpatch-web"}
ESTADOS = ["asignado", "buscando_tecnico", "cancelado", "completado", "cotizacion_aceptada", "cotizado", "en_espera",
           "en_progreso", "pagado"]
# Desde service-request 1.9.0 la lista suma clientType, companyId, siteName y description (SCRUM-73); sigue sin dirección ni ubicación.
CAMPOS_LISTA = ["assignedAt", "categoryId", "clientId", "clientType", "companyId", "createdAt", "description", "id", "siteName", "status",
                "technicianId"]
CON_PLATAFORMA = ["if (!pm.variables.get('platformAdminEmail')) { pm.execution.skipRequest(); }"]
DIRECCION = "Calle 63 # 9-45, Chapinero"
INEXISTENTE = "Avenida Zzqxw Inexistente 98765 # 999-99, Narnia"


def cancelar(variable, nombre="El cliente cancela la solicitud de la prueba"):
    return req(nombre, "POST", "/v1/service-requests/{{" + variable + "}}/cancel", [JSON, CORR, auth("clienteToken")],
               {"reason": "Limpieza de la prueba de QA."}, pruebas=estado(200))


def crear(variable, cuerpo, nombre):
    """Crea la solicitud; reintenta mientras la réplica de la categoría no llega (422 que no es de la dirección)."""
    return req(nombre, "POST", "/v1/service-requests", [JSON, CORR, auth("clienteToken")], cuerpo,
               pruebas=reintentar(
                   "pm.response.code !== 422 || /direccion-no-encontrada$/.test(pm.response.json().type)",
                   estado(201) + [f"pm.collectionVariables.set('{variable}', pm.response.json().id);"], maximo=10))


resumen = [
    "pm.test('200 con los 9 estados y createdToday', () => {",
    "  pm.response.to.have.status(200);",
    "  const r = pm.response.json();",
    f"  pm.expect(Object.keys(r.byStatus).sort()).to.eql({json.dumps(ESTADOS)});",
    "  Object.values(r.byStatus).forEach(v => pm.expect(v).to.be.a('number'));",
    "  pm.expect(r.createdToday).to.be.a('number');",
    "});",
]

panel = base.coleccion(
    "QUICKPATCH — SCRUM-105 Panel operativo del administrador del tenant",
    "RF-18 (SCRUM-38) contra QA, con service-request.v1.yaml 1.8.0. El administrador del tenant ve el resumen por estado "
    "y la lista de su tenant: la solicitud que crea el cliente de la prueba aparece en la lista, sin dirección ni "
    "ubicación, y suma a createdToday. Ningún otro rol entra al panel (cliente, técnico y el cliente del tenant Beta "
    "reciben 403) y el administrador del tenant no usa la vista de plataforma (403). Con platformAdminEmail, la vista de "
    "plataforma solo trae conteos por tenant (tenantId, byStatus y createdToday). Variables: baseUrl, adminEmail y "
    "adminPassword; opcionales platformAdminEmail y platformAdminPassword (secretos de QA, nunca en el repositorio).",
    [
        base.preparacion("SCRUM-105"),
        {
            "name": "1. Resumen y lista del administrador del tenant",
            "item": [
                req("Resumen antes de la solicitud", "GET", "/v1/admin/service-requests/summary", [CORR, auth("adminToken")],
                    pruebas=resumen + ["pm.collectionVariables.set('creadasAntes', pm.response.json().createdToday);"]),
                crear("solicitud1Id", {"categoryId": "{{categoriaId}}", "description": "Prueba del panel operativo SCRUM-105",
                                       "location": {"latitude": 4.6486, "longitude": -74.063},
                                       "addressText": "Calle 63 # 9-45, apto 201"},
                      "El cliente crea una solicitud"),
                req("El resumen suma la solicitud del día", "GET", "/v1/admin/service-requests/summary",
                    [CORR, auth("adminToken")],
                    pruebas=reintentar(
                        "pm.response.json().createdToday > Number(pm.collectionVariables.get('creadasAntes'))",
                        resumen + [
                            "pm.test('createdToday sube', () => pm.expect(pm.response.json().createdToday)"
                            ".to.be.above(Number(pm.collectionVariables.get('creadasAntes'))));",
                        ])),
                req("La lista del tenant trae la solicitud, sin dirección ni ubicación", "GET",
                    "/v1/service-requests?page=1&size=50", [CORR, auth("adminToken")],
                    pruebas=[
                        "pm.test('200 con la solicitud de la prueba y solo los campos del contrato', () => {",
                        "  pm.response.to.have.status(200);",
                        "  const items = pm.response.json().items;",
                        "  const s = items.find(x => x.id === pm.collectionVariables.get('solicitud1Id'));",
                        "  pm.expect(s, 'la solicitud de la prueba').to.be.ok;",
                        f"  items.forEach(x => pm.expect(Object.keys(x).sort()).to.eql({json.dumps(CAMPOS_LISTA)}));",
                        "});",
                    ]),
                req("La lista filtra por estado", "GET", "/v1/service-requests?status=cancelado&page=1&size=20",
                    [CORR, auth("adminToken")],
                    pruebas=estado(200) + [
                        "pm.test('solo canceladas', () => pm.response.json().items.forEach(x => pm.expect(x.status).to.eql('cancelado')));",
                    ]),
            ],
        },
        {
            "name": "2. Ningún otro rol entra al panel",
            "item": [
                req("El cliente no ve el resumen → 403", "GET", "/v1/admin/service-requests/summary",
                    [CORR, auth("clienteToken")], pruebas=error(403)),
                req("El técnico no ve la lista → 403", "GET", "/v1/service-requests?page=1&size=20",
                    [CORR, auth("tecnicoToken")], pruebas=error(403)),
                req("El cliente del tenant Beta no ve el resumen → 403", "GET", "/v1/admin/service-requests/summary",
                    [CORR, auth("betaToken")], pruebas=error(403)),
                req("El administrador del tenant no usa la vista de plataforma → 403", "GET",
                    "/v1/platform/service-requests/summary", [CORR, auth("adminToken")], pruebas=error(403)),
            ],
        },
        {
            "name": "3. Vista de plataforma (solo con platformAdminEmail)",
            "item": [
                req("Login del administrador de la plataforma", "POST", "/v1/auth/login", [JSON, CORR, WEB],
                    {"email": "{{platformAdminEmail}}", "password": "{{platformAdminPassword}}"}, previo=CON_PLATAFORMA,
                    pruebas=[
                        "pm.test('200 con rol admin_plataforma', () => {",
                        "  pm.response.to.have.status(200);",
                        "  pm.expect(pm.response.json().user.role).to.eql('admin_plataforma');",
                        "});",
                        "pm.collectionVariables.set('plataformaToken', pm.response.json().accessToken);",
                    ]),
                req("Solo conteos por tenant", "GET", "/v1/platform/service-requests/summary",
                    [CORR, auth("plataformaToken")], previo=CON_PLATAFORMA,
                    pruebas=[
                        "pm.test('200 con tenantId, byStatus y createdToday por tenant', () => {",
                        "  pm.response.to.have.status(200);",
                        "  const tenants = pm.response.json().tenants;",
                        "  pm.expect(tenants.length).to.be.above(0);",
                        "  tenants.forEach(t => pm.expect(Object.keys(t).sort()).to.eql(['byStatus', 'createdToday', 'tenantId']));",
                        "});",
                    ]),
            ],
        },
        {
            "name": "Limpieza de la solicitud",
            "item": [cancelar("solicitud1Id")],
        },
        base.limpieza,
    ],
)

notificaciones = "/v1/notifications?page=1&size=50"
ajena = [
    "pm.test('200 sin las notificaciones de la solicitud de otro usuario', () => {",
    "  pm.response.to.have.status(200);",
    "  const id = pm.collectionVariables.get('solicitud1Id');",
    "  pm.expect(pm.response.json().items.filter(n => n.serviceRequestId === id)).to.have.length(0);",
    "});",
]

geocodificacion = base.coleccion(
    "QUICKPATCH — SCRUM-458 Geocodificación propia y buzón de notificaciones (ADR-024)",
    "RIE-02 y RIE-03 contra QA (ADR-024), con service-request.v1.yaml 1.8.0 y communication.v1.yaml 1.2.0. "
    "Geocodificación: location-preview con una dirección de Bogotá (punto y localidad) y con una inexistente (422 "
    "direccion-no-encontrada); la solicitud se crea solo con la dirección, sin GPS, y una dirección inexistente da 422. "
    "El caso del geocodificador sin respuesta no se puede provocar en QA sin apagar Nominatim: lo cubren las pruebas de "
    "ServiceRequest. Buzón: el cliente recibe solicitud-creada y el técnico oferta-recibida; otro cliente, el "
    "administrador y el cliente de Beta no las ven y no pueden marcarlas como leídas (404); marcar como leída es "
    "idempotente. Variables: baseUrl, adminEmail y adminPassword (secretos de QA, nunca en el repositorio).",
    [
        base.preparacion("SCRUM-458"),
        {
            "name": "1. Geocodificación",
            "item": [
                req("Vista previa de una dirección de Bogotá", "POST", "/v1/service-requests/location-preview",
                    [JSON, CORR, auth("clienteToken")], {"addressText": DIRECCION},
                    pruebas=[
                        "pm.test('200 con punto dentro de Bogotá, localidad y dirección reconocida', () => {",
                        "  pm.response.to.have.status(200);",
                        "  const r = pm.response.json();",
                        "  pm.expect(r.location.latitude).to.be.within(4.4, 4.9);",
                        "  pm.expect(r.location.longitude).to.be.within(-74.3, -73.9);",
                        "  pm.expect(r.locality.code).to.match(/^[0-9]{2}$/);",
                        "  pm.expect(r.matchedAddress).to.be.a('string');",
                        "});",
                    ]),
                req("Vista previa de una dirección inexistente → 422", "POST", "/v1/service-requests/location-preview",
                    [JSON, CORR, auth("clienteToken")], {"addressText": INEXISTENTE},
                    pruebas=error(422, "direccion-no-encontrada")),
                req("El técnico no usa la vista previa → 403", "POST", "/v1/service-requests/location-preview",
                    [JSON, CORR, auth("tecnicoToken")], {"addressText": DIRECCION}, pruebas=error(403)),
                crear("solicitud1Id", {"categoryId": "{{categoriaId}}", "description": "Prueba de geocodificación SCRUM-458",
                                       "addressText": DIRECCION},
                      "El cliente crea la solicitud solo con la dirección (sin GPS)"),
                req("La solicitud quedó con la ubicación de la dirección", "GET", "/v1/service-requests/{{solicitud1Id}}",
                    [CORR, auth("clienteToken")],
                    pruebas=[
                        "pm.test('200 con location calculada y la dirección escrita', () => {",
                        "  pm.response.to.have.status(200);",
                        "  const s = pm.response.json();",
                        "  pm.expect(s.location.latitude).to.be.within(4.4, 4.9);",
                        f"  pm.expect(s.addressText).to.eql('{DIRECCION}');",
                        "});",
                    ]),
                req("Crear con una dirección inexistente y sin GPS → 422", "POST", "/v1/service-requests",
                    [JSON, CORR, auth("clienteToken")],
                    {"categoryId": "{{categoriaId}}", "description": "Prueba de dirección inexistente SCRUM-458",
                     "addressText": INEXISTENTE},
                    pruebas=error(422, "direccion-no-encontrada")),
            ],
        },
        {
            "name": "2. Buzón de notificaciones",
            "item": [
                req("El cliente recibe solicitud-creada en su buzón", "GET", notificaciones, [CORR, auth("clienteToken")],
                    pruebas=[
                        "const n = pm.response.code === 200 && pm.response.json().items.find(x =>"
                        " x.serviceRequestId === pm.collectionVariables.get('solicitud1Id') && x.type === 'solicitud-creada');",
                        *reintentar("n", [
                            "pm.test('solicitud-creada sin leer, con el contrato Notification', () => {",
                            "  pm.expect(n).to.be.ok;",
                            "  pm.expect(Object.keys(n).sort()).to.eql(['createdAt', 'id', 'message', 'readAt', 'serviceRequestId', 'title', 'type']);",
                            "  pm.expect(n.readAt).to.eql(null);",
                            "  pm.expect(pm.response.json().unreadCount).to.be.above(0);",
                            "});",
                            "if (n) { pm.collectionVariables.set('notificacionId', n.id); }",
                        ]),
                    ]),
                req("El técnico recibe oferta-recibida", "GET", notificaciones, [CORR, auth("tecnicoToken")],
                    pruebas=[
                        "const n = pm.response.code === 200 && pm.response.json().items.find(x =>"
                        " x.serviceRequestId === pm.collectionVariables.get('solicitud1Id') && x.type === 'oferta-recibida');",
                        *reintentar("n", ["pm.test('oferta-recibida para el técnico', () => pm.expect(n).to.be.ok);"]),
                    ]),
                req("Otro cliente no ve las notificaciones del cliente", "GET", notificaciones,
                    [CORR, auth("otroClienteToken")], pruebas=ajena),
                req("El administrador no ve las notificaciones del cliente", "GET", notificaciones,
                    [CORR, auth("adminToken")], pruebas=ajena),
                req("El cliente de Beta no ve las notificaciones del cliente (RLS)", "GET", notificaciones,
                    [CORR, auth("betaToken")], pruebas=ajena),
                req("Otro cliente no la marca como leída → 404", "POST", "/v1/notifications/{{notificacionId}}/read",
                    [CORR, auth("otroClienteToken")], pruebas=error(404)),
                req("El cliente de Beta no la marca como leída → 404 (RLS)", "POST",
                    "/v1/notifications/{{notificacionId}}/read", [CORR, auth("betaToken")], pruebas=error(404)),
                req("El cliente la marca como leída", "POST", "/v1/notifications/{{notificacionId}}/read",
                    [CORR, auth("clienteToken")],
                    pruebas=estado(200) + [
                        "pm.test('readAt con fecha', () => pm.expect(pm.response.json().readAt).to.be.a('string'));",
                        "pm.collectionVariables.set('leidaEn', pm.response.json().readAt);",
                    ]),
                req("Marcarla otra vez conserva la fecha (idempotente)", "POST", "/v1/notifications/{{notificacionId}}/read",
                    [CORR, auth("clienteToken")],
                    pruebas=estado(200) + [
                        "pm.test('mismo readAt', () => pm.expect(pm.response.json().readAt).to.eql(pm.collectionVariables.get('leidaEn')));",
                    ]),
                req("Ya no aparece entre las no leídas", "GET", "/v1/notifications?unread=true&page=1&size=50",
                    [CORR, auth("clienteToken")],
                    pruebas=estado(200) + [
                        "pm.test('sin la leída', () => pm.expect(pm.response.json().items.map(n => n.id))"
                        ".to.not.include(pm.collectionVariables.get('notificacionId')));",
                    ]),
            ],
        },
        {
            "name": "Limpieza de la solicitud",
            "item": [cancelar("solicitud1Id")],
        },
        base.limpieza,
    ],
)

for nombre, coleccion in [("scrum-105-panel-operativo", panel), ("scrum-458-geocodificacion-buzon", geocodificacion)]:
    destino = AQUI / f"{nombre}.postman_collection.json"
    destino.write_text(json.dumps(coleccion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Colección escrita en {destino}")
