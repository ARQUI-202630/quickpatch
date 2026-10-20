"""Genera scrum-478-cancelacion.postman_collection.json: cancelación de la solicitud de punta a punta en QA (SCRUM-478).

Uso: python tests/e2e/generar-scrum478-cancelacion.py
La colección se edita aquí y se regenera, para que el JSON siempre sea válido y revisable en los PR.

Cubre RF-36 (SCRUM-472) contra los servicios desplegados: ServiceRequest cancela y publica service-request.cancelled;
Matching retira la oferta pendiente y libera al técnico asignado (SCRUM-476). Los pasos que necesitan al administrador
del tenant (categoría propia, técnico aprobado, ofertas y cancelación del administrador) se omiten si no llegan
adminEmail y adminPassword, para poder correr el resto sin secretos.
"""
import json
import pathlib

JSON = {"key": "Content-Type", "value": "application/json"}
CORR = {"key": "X-Correlation-Id", "value": "{{$guid}}"}
CANAL = {"key": "X-Channel-Id", "value": "quickpatch-mobile"}
# El Nginx de VM1 fija el canal (y con él el tenant) por el nombre del host (quickpatch-api-gateway#16).
BETA = {"key": "Host", "value": "beta.qa.quickpatch.internal"}


def auth(var):
    return {"key": "Authorization", "value": "Bearer {{" + var + "}}"}


def req(nombre, metodo, ruta, headers, cuerpo=None, pruebas=(), previo=()):
    ruta_sin_query, _, query = ruta.partition("?")
    url = {"raw": "{{baseUrl}}/api" + ruta, "host": ["{{baseUrl}}"], "path": ["api"] + ruta_sin_query.strip("/").split("/")}
    if query:
        url["query"] = [{"key": k, "value": v} for k, v in (p.split("=") for p in query.split("&"))]
    item = {"name": nombre, "request": {"method": metodo, "header": list(headers), "url": url}, "event": []}
    if cuerpo is not None:
        item["request"]["body"] = {"mode": "raw", "raw": json.dumps(cuerpo, ensure_ascii=False, indent=2)}
    if previo:
        item["event"].append({"listen": "prerequest", "script": {"type": "text/javascript", "exec": list(previo)}})
    if pruebas:
        item["event"].append({"listen": "test", "script": {"type": "text/javascript", "exec": list(pruebas)}})
    return item


# Sin el administrador del tenant no hay técnico aprobado ni ofertas: esos pasos se omiten.
CON_ADMIN = ["if (!pm.variables.get('adminEmail')) { pm.execution.skipRequest(); }"]
CON_PLATAFORMA = ["if (!pm.variables.get('platformAdminEmail')) { pm.execution.skipRequest(); }"]

problem = [
    "pm.test('Problem Details (RFC 9457) con correlationId', () => {",
    "  pm.expect(pm.response.headers.get('Content-Type')).to.include('application/problem+json');",
    "  pm.expect(pm.response.json()).to.have.property('correlationId');",
    "});",
]


def tipo(nombre):
    return [f"pm.test('tipo {nombre}', () => pm.expect(pm.response.json().type).to.match(/\\/{nombre}$/));"]


def estado(codigo):
    return [f"pm.test('{codigo}', () => pm.response.to.have.status({codigo}));"]


def reintentar(condicion, pruebas, maximo=15, espera=2000):
    """Repite la petición mientras `condicion` (JS) sea falsa: los efectos llegan por Kafka y no son inmediatos."""
    return [
        "const intento = Number(pm.collectionVariables.get('intentos') || 0);",
        f"if (!({condicion}) && intento < {maximo}) {{",
        "  pm.collectionVariables.set('intentos', intento + 1);",
        f"  setTimeout(() => {{}}, {espera});",
        "  // Por id y no por nombre: la colección repite pasos parecidos en varias carpetas.",
        "  pm.execution.setNextRequest(pm.info.requestId);",
        "} else {",
        "  pm.collectionVariables.unset('intentos');",
        *("  " + linea for linea in pruebas),
        "}",
    ]


def registro_cliente(nombre, prefijo, headers=(JSON, CORR, CANAL)):
    return req(f"Registro del {nombre}", "POST", "/v1/auth/register/client", list(headers),
               {"email": prefijo + ".{{sufijo}}@quickpatch.test", "password": "{{clave}}", "fullName": f"Prueba 478 {nombre}"},
               pruebas=estado(201))


def tenant_del_token(variable):
    """`tenant_id` del JWT de acceso (el tenant sale del token, nunca de la petición)."""
    return [
        "const partes = pm.response.json().accessToken.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');",
        "const carga = JSON.parse(CryptoJS.enc.Base64.parse(partes + '='.repeat((4 - partes.length % 4) % 4)).toString(CryptoJS.enc.Utf8));",
        f"pm.collectionVariables.set('{variable}', carga.tenant_id);",
    ]


def login(nombre, prefijo, variable, rol, headers=(JSON, CORR, CANAL), previo=(), extra=()):
    return req(f"Login del {nombre}", "POST", "/v1/auth/login", list(headers),
               {"email": prefijo + ".{{sufijo}}@quickpatch.test", "password": "{{clave}}"},
               previo=previo,
               pruebas=[
                   f"pm.test('200 con rol {rol}', () => {{",
                   "  pm.response.to.have.status(200);",
                   f"  pm.expect(pm.response.json().user.role).to.eql('{rol}');",
                   "});",
                   f"pm.collectionVariables.set('{variable}', pm.response.json().accessToken);",
                   *extra,
               ])


def crear_solicitud(variable, nombre, previo=()):
    return req(f"Crear la {nombre} (espera la réplica de la categoría)", "POST", "/v1/service-requests",
               [JSON, CORR, auth("clienteToken")],
               {"categoryId": "{{categoriaId}}", "description": "Prueba de cancelación de punta a punta (SCRUM-478)",
                "location": {"latitude": 4.6486, "longitude": -74.063}, "addressText": "Calle 63 # 9-45, apto 201"},
               previo=previo,
               pruebas=reintentar("pm.response.code !== 422", [
                   "pm.test('201 en buscando_tecnico', () => {",
                   "  pm.response.to.have.status(201);",
                   "  pm.expect(pm.response.json().status).to.eql('buscando_tecnico');",
                   "});",
                   f"pm.collectionVariables.set('{variable}', pm.response.json().id);",
               ], maximo=10))


def oferta_pendiente(solicitud, variable, nombre):
    """El técnico ve la oferta de la solicitud: Matching la crea al consumir service-request.created."""
    return req(f"El técnico ve la oferta de la {nombre}", "GET", "/v1/matching/offers?status=pendiente",
               [CORR, auth("tecnicoToken")], previo=CON_ADMIN,
               pruebas=[
                   f"const oferta = pm.response.code === 200 && pm.response.json().items.find(o => o.serviceRequestId === pm.collectionVariables.get('{solicitud}'));",
                   *reintentar("oferta", [
                       "pm.test('la oferta está pendiente para el técnico', () => pm.expect(oferta).to.be.ok);",
                       f"if (oferta) {{ pm.collectionVariables.set('{variable}', oferta.attemptId); }}",
                   ]),
               ])


def disponibilidad(esperado, nombre):
    return req(nombre, "GET", "/v1/technicians/me/availability", [CORR, auth("tecnicoToken")], previo=CON_ADMIN,
               pruebas=reintentar(f"pm.response.code === 200 && pm.response.json().status === '{esperado}'", [
                   f"pm.test('técnico {esperado}', () => pm.expect(pm.response.json().status).to.eql('{esperado}'));",
               ]))


def cancelar(nombre, solicitud, token, motivo, pruebas, headers=(JSON, CORR), previo=()):
    hs = list(headers) + ([auth(token)] if token else [])
    return req(nombre, "POST", "/v1/service-requests/{{" + solicitud + "}}/cancel", hs, {"reason": motivo},
               pruebas=pruebas, previo=previo)


cancelada_por = lambda quien: [  # noqa: E731
    "pm.test('200 con el contrato CancelledServiceRequest', () => {",
    "  pm.response.to.have.status(200);",
    "  const r = pm.response.json();",
    "  pm.expect(Object.keys(r).sort()).to.eql(['cancelledAt', 'cancelledByType', 'id', 'status']);",
    "  pm.expect(r.status).to.eql('cancelado');",
    f"  pm.expect(r.cancelledByType).to.eql('{quien}');",
    "});",
]

preparar = [
    "if (!pm.collectionVariables.get('sufijo')) {",
    "  pm.collectionVariables.set('sufijo', Date.now().toString(36));",
    "  // Clave de las cuentas de prueba de esta corrida; no se guarda en ningún lado.",
    "  pm.collectionVariables.set('clave', 'Qp' + Math.random().toString(36).slice(2, 12) + '7Z');",
    "}",
]

coleccion = {
    "info": {
        "name": "QUICKPATCH — SCRUM-478 Cancelación de la solicitud de punta a punta",
        "description": (
            "RF-36 (SCRUM-472) contra QA: el cliente cancela con una oferta pendiente y el técnico deja de verla; el "
            "administrador del tenant cancela con el técnico asignado y el técnico vuelve a disponible (SCRUM-475, "
            "SCRUM-476). Casos negativos: motivo inválido (400), sin token (401), técnico (403), otro cliente (404), "
            "cliente de otro tenant (404), administrador de la plataforma (403) y cancelar dos veces (409). "
            "Variables: baseUrl, adminEmail, adminPassword, platformAdminEmail y platformAdminPassword (secretos de QA, "
            "nunca en el repositorio). Sin el administrador se omiten los pasos de técnico, ofertas y administrador. "
            "Contratos: service-request.v1.yaml 1.5.0, matching.v1.yaml, identity.v1.yaml."
        ),
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
    },
    "variable": [
        {"key": "baseUrl", "value": "https://qa.quickpatch.internal"},
        {"key": "adminEmail", "value": ""},
        {"key": "adminPassword", "value": ""},
        {"key": "platformAdminEmail", "value": ""},
        {"key": "platformAdminPassword", "value": ""},
    ],
    "item": [
        {
            "name": "0. Preparación: categoría propia y técnico aprobado",
            "item": [
                req("Login del administrador del tenant", "POST", "/v1/auth/login", [JSON, CORR, CANAL],
                    {"email": "{{adminEmail}}", "password": "{{adminPassword}}"},
                    previo=preparar + CON_ADMIN,
                    pruebas=[
                        "pm.test('200 con rol admin_tenant', () => {",
                        "  pm.response.to.have.status(200);",
                        "  pm.expect(pm.response.json().user.role).to.eql('admin_tenant');",
                        "});",
                        "pm.collectionVariables.set('adminToken', pm.response.json().accessToken);",
                    ]),
                req("Categoría solo para esta corrida", "POST", "/v1/catalog/admin/categories", [JSON, CORR, auth("adminToken")],
                    {"name": "Cancelación {{sufijo}}", "description": "Categoría de la prueba SCRUM-478; se desactiva al final"},
                    previo=CON_ADMIN,
                    pruebas=estado(201) + ["pm.collectionVariables.set('categoriaPropia', pm.response.json().id);"]),
                req("Registro del técnico con esa especialidad", "POST", "/v1/auth/register/technician", [JSON, CORR, CANAL],
                    {"email": "tecnico478.{{sufijo}}@quickpatch.test", "password": "{{clave}}", "fullName": "Técnico 478",
                     "phone": "3007654321", "documentId": "{{documento}}", "specialtyId": "{{categoriaPropia}}", "role": "tecnico"},
                    previo=CON_ADMIN + ["pm.collectionVariables.set('documento', String(Date.now()).slice(-10));"],
                    pruebas=estado(201) + ["pm.collectionVariables.set('tecnicoId', pm.response.json().id);"]),
                req("El administrador aprueba al técnico", "POST", "/v1/admin/technicians/{{tecnicoId}}/approve",
                    [CORR, auth("adminToken")], previo=CON_ADMIN, pruebas=estado(200)),
                login("técnico", "tecnico478", "tecnicoToken", "tecnico", previo=CON_ADMIN),
                req("Localidades de Bogotá", "GET", "/v1/localities", [CORR, auth("tecnicoToken")], previo=CON_ADMIN,
                    pruebas=estado(200) + [
                        "pm.collectionVariables.set('localidades', JSON.stringify(pm.response.json().slice(0, 20).map(l => l.code)));",
                    ]),
                req("El técnico cubre toda Bogotá (espera a que Matching lo conozca)", "PUT", "/v1/technicians/me/coverage",
                    [JSON, CORR, auth("tecnicoToken")], previo=CON_ADMIN + [
                        "pm.request.body.raw = JSON.stringify({ localityCodes: JSON.parse(pm.collectionVariables.get('localidades')) });",
                    ], cuerpo={"localityCodes": []},
                    pruebas=reintentar("pm.response.code === 200", estado(200))),
                req("El técnico queda disponible", "PUT", "/v1/technicians/me/availability", [JSON, CORR, auth("tecnicoToken")],
                    {"status": "disponible"}, previo=CON_ADMIN,
                    pruebas=reintentar("pm.response.code === 200", estado(200) + [
                        "pm.test('disponible', () => pm.expect(pm.response.json().status).to.eql('disponible'));",
                    ])),
            ],
        },
        {
            "name": "1. Cliente: cancelar con la oferta pendiente",
            "item": [
                {**registro_cliente("cliente", "cliente478"), "event": [
                    {"listen": "prerequest", "script": {"type": "text/javascript", "exec": preparar}},
                    {"listen": "test", "script": {"type": "text/javascript", "exec": estado(201)}},
                ]},
                login("cliente", "cliente478", "clienteToken", "cliente", extra=tenant_del_token("tenantCliente")),
                req("Categoría de la solicitud", "GET", "/v1/catalog/categories", [CORR, auth("clienteToken")],
                    pruebas=estado(200) + [
                        "// Con administrador, la categoría propia (solo el técnico de la prueba la atiende); sin él, una cualquiera.",
                        "const propia = pm.collectionVariables.get('categoriaPropia');",
                        "const ids = pm.response.json().map(c => c.id);",
                        "pm.collectionVariables.set('categoriaId', propia || ids[0]);",
                    ]),
                crear_solicitud("solicitudId", "solicitud 1"),
                oferta_pendiente("solicitudId", "ofertaId", "solicitud 1"),
                cancelar("Motivo de 4 caracteres → 400", "solicitudId", "clienteToken", " no ",
                         estado(400) + problem + tipo("validacion") + [
                             "pm.test('error en reason', () => pm.expect(pm.response.json().errors).to.have.property('reason'));",
                         ]),
                cancelar("Sin token → 401", "solicitudId", None, "Ya no necesito el servicio.", estado(401) + problem),
                registro_cliente("otro cliente", "otro478"),
                login("otro cliente", "otro478", "otroToken", "cliente"),
                cancelar("Otro cliente del mismo tenant → 404", "solicitudId", "otroToken", "Ya no necesito el servicio.",
                         estado(404) + problem + tipo("no-encontrado")),
                registro_cliente("cliente del tenant Beta", "beta478", headers=(JSON, CORR, BETA)),
                login("cliente del tenant Beta", "beta478", "betaToken", "cliente", headers=(JSON, CORR, BETA),
                      extra=tenant_del_token("tenantBeta") + [
                          "pm.test('el token es de otro tenant', () => {",
                          "  pm.expect(pm.collectionVariables.get('tenantBeta')).to.be.a('string');",
                          "  pm.expect(pm.collectionVariables.get('tenantBeta')).to.not.eql(pm.collectionVariables.get('tenantCliente'));",
                          "});",
                      ]),
                cancelar("Cliente de otro tenant → 404 (RLS)", "solicitudId", "betaToken", "Ya no necesito el servicio.",
                         estado(404) + problem + tipo("no-encontrado")),
                req("Registro de un técnico sin aprobar", "POST", "/v1/auth/register/technician", [JSON, CORR, CANAL],
                    {"email": "tecpend478.{{sufijo}}@quickpatch.test", "password": "{{clave}}", "fullName": "Técnico pendiente 478",
                     "phone": "3007654322", "documentId": "{{documento2}}", "specialtyId": "{{categoriaId}}", "role": "tecnico"},
                    previo=["pm.collectionVariables.set('documento2', String(Date.now() + 7).slice(-10));"],
                    pruebas=estado(201)),
                login("técnico sin aprobar", "tecpend478", "tecPendToken", "tecnico"),
                cancelar("Un técnico no cancela → 403", "solicitudId", "tecPendToken", "Ya no necesito el servicio.",
                         estado(403) + problem),
                req("La solicitud sigue buscando técnico", "GET", "/v1/service-requests/{{solicitudId}}", [CORR, auth("clienteToken")],
                    pruebas=estado(200) + [
                        "// Sin el técnico de la prueba, Matching no encuentra candidato y la deja en en_espera.",
                        "pm.test('nadie la canceló', () => pm.expect(pm.response.json().status).to.be.oneOf(['buscando_tecnico', 'en_espera']));",
                    ]),
                cancelar("El cliente cancela", "solicitudId", "clienteToken", "  Ya no necesito el servicio.  ",
                         cancelada_por("cliente")),
                req("El detalle trae la cancelación", "GET", "/v1/service-requests/{{solicitudId}}", [CORR, auth("clienteToken")],
                    pruebas=estado(200) + [
                        "pm.test('cancelado con fecha y motivo sin espacios', () => {",
                        "  const s = pm.response.json();",
                        "  pm.expect(s.status).to.eql('cancelado');",
                        "  pm.expect(s.cancellationReason).to.eql('Ya no necesito el servicio.');",
                        "  pm.expect(s.cancelledAt).to.be.a('string');",
                        "});",
                    ]),
                cancelar("Cancelar otra vez → 409", "solicitudId", "clienteToken", "Ya no necesito el servicio.",
                         estado(409) + problem + tipo("transicion-invalida")),
                req("El técnico ya no ve la oferta (Matching consumió service-request.cancelled)", "GET",
                    "/v1/matching/offers?status=pendiente", [CORR, auth("tecnicoToken")], previo=CON_ADMIN,
                    pruebas=[
                        "const sigue = pm.response.code !== 200 || pm.response.json().items.some(o => o.serviceRequestId === pm.collectionVariables.get('solicitudId'));",
                        *reintentar("!sigue", ["pm.test('la oferta se retiró', () => pm.expect(sigue).to.eql(false));"]),
                    ]),
                req("Aceptar la oferta retirada → 409", "POST", "/v1/matching/offers/{{ofertaId}}/accept",
                    [CORR, auth("tecnicoToken")], previo=CON_ADMIN,
                    pruebas=estado(409) + problem + tipo("oferta-no-disponible")),
                disponibilidad("disponible", "El técnico sigue disponible después de la solicitud 1"),
            ],
        },
        {
            "name": "2. Administrador del tenant: cancelar con el técnico asignado",
            "item": [
                crear_solicitud("solicitud2Id", "solicitud 2", previo=CON_ADMIN),
                oferta_pendiente("solicitud2Id", "oferta2Id", "solicitud 2"),
                req("El técnico acepta la oferta", "POST", "/v1/matching/offers/{{oferta2Id}}/accept", [CORR, auth("tecnicoToken")],
                    previo=CON_ADMIN,
                    pruebas=estado(200) + ["pm.test('aceptado', () => pm.expect(pm.response.json().response).to.eql('aceptado'));"]),
                req("La solicitud queda asignada (ServiceRequest consumió matching.technician-assigned)", "GET",
                    "/v1/service-requests/{{solicitud2Id}}", [CORR, auth("clienteToken")], previo=CON_ADMIN,
                    pruebas=reintentar("pm.response.json().status === 'asignado'", [
                        "pm.test('asignado al técnico de la prueba', () => {",
                        "  pm.expect(pm.response.json().status).to.eql('asignado');",
                        "  pm.expect(pm.response.json().technicianId).to.eql(pm.collectionVariables.get('tecnicoId'));",
                        "});",
                    ])),
                disponibilidad("ocupado", "El técnico queda ocupado"),
                req("Login del administrador de la plataforma", "POST", "/v1/auth/login", [JSON, CORR, CANAL],
                    {"email": "{{platformAdminEmail}}", "password": "{{platformAdminPassword}}"}, previo=CON_PLATAFORMA,
                    pruebas=estado(200) + ["pm.collectionVariables.set('plataformaToken', pm.response.json().accessToken);"]),
                cancelar("El administrador de la plataforma no cancela → 403", "solicitud2Id", "plataformaToken",
                         "Prueba de rol.", estado(403) + problem, previo=CON_PLATAFORMA),
                cancelar("El administrador del tenant cancela", "solicitud2Id", "adminToken", "El cliente no respondió.",
                         cancelada_por("admin_tenant"), previo=CON_ADMIN),
                req("El cliente ve la cancelación con el motivo del administrador", "GET", "/v1/service-requests/{{solicitud2Id}}",
                    [CORR, auth("clienteToken")], previo=CON_ADMIN,
                    pruebas=estado(200) + [
                        "pm.test('cancelado con el motivo', () => {",
                        "  pm.expect(pm.response.json().status).to.eql('cancelado');",
                        "  pm.expect(pm.response.json().cancellationReason).to.eql('El cliente no respondió.');",
                        "});",
                    ]),
                disponibilidad("disponible", "El técnico vuelve a disponible (Matching lo liberó)"),
            ],
        },
        {
            "name": "3. Release 0.4.0 de ServiceRequest: geocodificación y panel",
            "item": [
                req("Vista previa de la ubicación (Nominatim de QA, SCRUM-457)", "POST", "/v1/service-requests/location-preview",
                    [JSON, CORR, auth("clienteToken")], {"addressText": "Calle 63 # 9-45, Bogotá"},
                    pruebas=estado(200) + [
                        "pm.test('punto en Bogotá con localidad', () => {",
                        "  const r = pm.response.json();",
                        "  pm.expect(r.location.latitude).to.be.within(4.45, 4.85);",
                        "  pm.expect(r.location.longitude).to.be.within(-74.25, -73.98);",
                        "  pm.expect(r.locality.code).to.be.a('string');",
                        "});",
                    ]),
                req("Conteos del tenant para su administrador (SCRUM-103)", "GET", "/v1/admin/service-requests/summary",
                    [CORR, auth("adminToken")], previo=CON_ADMIN,
                    pruebas=estado(200) + [
                        "pm.test('los 9 estados y al menos las 2 canceladas de esta corrida', () => {",
                        "  const r = pm.response.json();",
                        "  pm.expect(Object.keys(r.byStatus)).to.have.lengthOf(9);",
                        "  pm.expect(r.byStatus.cancelado).to.be.at.least(2);",
                        "});",
                    ]),
                req("Conteos por tenant para la plataforma (rol service_request_platform)", "GET",
                    "/v1/platform/service-requests/summary", [CORR, auth("plataformaToken")], previo=CON_PLATAFORMA,
                    pruebas=estado(200) + [
                        "pm.test('incluye el tenant del cliente, sin datos de las solicitudes', () => {",
                        "  const t = pm.response.json().tenants.find(x => x.tenantId === pm.collectionVariables.get('tenantCliente'));",
                        "  pm.expect(t).to.be.ok;",
                        "  pm.expect(Object.keys(t).sort()).to.eql(['byStatus', 'createdToday', 'tenantId']);",
                        "});",
                    ]),
                req("El cliente no ve los conteos del tenant → 403", "GET", "/v1/admin/service-requests/summary",
                    [CORR, auth("clienteToken")], pruebas=estado(403) + problem),
            ],
        },
        {
            "name": "4. Limpieza",
            "item": [
                req("Suspender al técnico de la prueba", "POST", "/v1/admin/technicians/{{tecnicoId}}/suspend",
                    [JSON, CORR, auth("adminToken")], {"reason": "Cuenta de la prueba SCRUM-478."}, previo=CON_ADMIN,
                    pruebas=estado(200)),
                req("Desactivar la categoría de la prueba", "PATCH", "/v1/catalog/admin/categories/{{categoriaPropia}}",
                    [JSON, CORR, auth("adminToken")], {"active": False}, previo=CON_ADMIN, pruebas=estado(200)),
            ],
        },
    ],
}

destino = pathlib.Path(__file__).with_name("scrum-478-cancelacion.postman_collection.json")
destino.write_text(json.dumps(coleccion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Colección escrita en {destino}")
