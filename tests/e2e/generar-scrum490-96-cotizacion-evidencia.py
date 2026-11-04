"""Genera las colecciones de la cotización (SCRUM-490) y de la ejecución con evidencia (SCRUM-96) contra QA.

Uso: python tests/e2e/generar-scrum490-96-cotizacion-evidencia.py
Escribe scrum-490-cotizacion.postman_collection.json, scrum-96-evidencia.postman_collection.json y las fotos de prueba de
fixtures/. Las colecciones se editan aquí y se regeneran, como la de SCRUM-478.

Contratos: service-request.v1.yaml 1.6.0 (cotización) y 1.7.0 (iniciar, evidencia y completar), matching.v1.yaml e
identity.v1.yaml. Necesitan al administrador del tenant (adminEmail y adminPassword, secretos de QA que nunca van al
repositorio): sin él no hay técnico aprobado ni oferta, y la colección no hace nada. Las cuentas de la corrida tienen
correo y contraseña generados al vuelo. Correr con --reporters cli: el reporte JSON de Newman guarda los cuerpos y los
tokens, y no debe subirse.

Newman resuelve las fotos de fixtures/ desde su carpeta de trabajo: en pruebas-sistema.yml es tests/e2e (/etc/newman).
"""
import base64
import json
import pathlib

AQUI = pathlib.Path(__file__).parent

JSON = {"key": "Content-Type", "value": "application/json"}
CORR = {"key": "X-Correlation-Id", "value": "{{$guid}}"}
CANAL = {"key": "X-Channel-Id", "value": "quickpatch-mobile"}
# El Nginx de VM1 fija el canal (y con él el tenant) por el nombre del host (quickpatch-api-gateway#16).
BETA = {"key": "Host", "value": "beta.qa.quickpatch.internal"}

# Las 20 localidades de Bogotá (DD 5.18): el técnico cubre toda la ciudad sin depender de la ruta de la lista.
LOCALIDADES = [f"{n:02d}" for n in range(1, 21)]

# PNG de 1 × 1 px y un archivo de texto con nombre de foto: el backend reconoce el tipo por el contenido.
PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==")
FOTO = "fixtures/evidencia-1x1.png"
NO_FOTO = "fixtures/no-es-foto.jpg"


def auth(var):
    return {"key": "Authorization", "value": "Bearer {{" + var + "}}"}


def url(ruta):
    sin_query, _, query = ruta.partition("?")
    u = {"raw": "{{baseUrl}}/api" + ruta, "host": ["{{baseUrl}}"], "path": ["api"] + sin_query.strip("/").split("/")}
    if query:
        u["query"] = [{"key": k, "value": v} for k, v in (p.split("=") for p in query.split("&"))]
    return u


def req(nombre, metodo, ruta, headers, cuerpo=None, pruebas=(), previo=(), archivo=None):
    item = {"name": nombre, "request": {"method": metodo, "header": list(headers), "url": url(ruta)}, "event": []}
    if cuerpo is not None:
        item["request"]["body"] = {"mode": "raw", "raw": json.dumps(cuerpo, ensure_ascii=False, indent=2)}
    if archivo is not None:
        item["request"]["body"] = {"mode": "formdata", "formdata": [{"key": "file", "type": "file", "src": archivo}]}
    # Sin el administrador del tenant no hay técnico aprobado ni oferta: todo se omite.
    item["event"].append({"listen": "prerequest", "script": {"type": "text/javascript", "exec": CON_ADMIN + list(previo)}})
    if pruebas:
        item["event"].append({"listen": "test", "script": {"type": "text/javascript", "exec": list(pruebas)}})
    return item


CON_ADMIN = ["if (!pm.variables.get('adminEmail')) { pm.execution.skipRequest(); }"]

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


def error(codigo, problema=None):
    return estado(codigo) + problem + (tipo(problema) if problema else [])


def reintentar(condicion, pruebas, maximo=15, espera=2000):
    """Repite la petición mientras `condicion` (JS) sea falsa: los efectos llegan por Kafka y no son inmediatos."""
    return [
        "const intento = Number(pm.collectionVariables.get('intentos') || 0);",
        f"if (!({condicion}) && intento < {maximo}) {{",
        "  pm.collectionVariables.set('intentos', intento + 1);",
        f"  setTimeout(() => {{}}, {espera});",
        "  pm.execution.setNextRequest(pm.info.requestId);",
        "} else {",
        "  pm.collectionVariables.unset('intentos');",
        *("  " + linea for linea in pruebas),
        "}",
    ]


preparar = [
    "if (!pm.collectionVariables.get('sufijo')) {",
    "  pm.collectionVariables.set('sufijo', Date.now().toString(36));",
    "  // Clave de las cuentas de esta corrida: se genera al vuelo y no se guarda en ningún lado.",
    "  pm.collectionVariables.set('clave', 'Qp_' + Math.random().toString(36).slice(2, 12) + '!Aa7');",
    "}",
]


def registro_cliente(nombre, prefijo, headers=(JSON, CORR, CANAL)):
    return req(f"Registro del {nombre}", "POST", "/v1/auth/register/client", list(headers),
               {"email": prefijo + ".{{sufijo}}@quickpatch.test", "password": "{{clave}}", "fullName": f"Prueba QA {nombre}"},
               pruebas=estado(201))


def login(nombre, prefijo, variable, rol, headers=(JSON, CORR, CANAL)):
    return req(f"Login del {nombre}", "POST", "/v1/auth/login", list(headers),
               {"email": prefijo + ".{{sufijo}}@quickpatch.test", "password": "{{clave}}"},
               pruebas=[
                   f"pm.test('200 con rol {rol}', () => {{",
                   "  pm.response.to.have.status(200);",
                   f"  pm.expect(pm.response.json().user.role).to.eql('{rol}');",
                   "});",
                   f"pm.collectionVariables.set('{variable}', pm.response.json().accessToken);",
               ])


def preparacion(historia):
    """Administrador, categoría propia, técnico aprobado con cobertura en toda Bogotá y disponible, y clientes."""
    return {
        "name": "0. Preparación: categoría propia, técnico aprobado y clientes",
        "item": [
            req("Login del administrador del tenant", "POST", "/v1/auth/login", [JSON, CORR, CANAL],
                {"email": "{{adminEmail}}", "password": "{{adminPassword}}"}, previo=preparar,
                pruebas=[
                    "pm.test('200 con rol admin_tenant', () => {",
                    "  pm.response.to.have.status(200);",
                    "  pm.expect(pm.response.json().user.role).to.eql('admin_tenant');",
                    "});",
                    "// El token solo vive en memoria durante la corrida.",
                    "pm.collectionVariables.set('adminToken', pm.response.json().accessToken);",
                ]),
            req("Categoría solo para esta corrida (solo el técnico de la prueba la atiende)", "POST",
                "/v1/catalog/admin/categories", [JSON, CORR, auth("adminToken")],
                {"name": f"{historia} {{{{sufijo}}}}", "description": f"Categoría de la prueba {historia}; se desactiva al final"},
                pruebas=estado(201) + ["pm.collectionVariables.set('categoriaId', pm.response.json().id);"]),
            req("Registro del técnico con esa especialidad", "POST", "/v1/auth/register/technician", [JSON, CORR, CANAL],
                {"email": "tecnico.qa.{{sufijo}}@quickpatch.test", "password": "{{clave}}", "fullName": f"Técnico {historia}",
                 "phone": "3007654321", "documentId": "{{documento}}", "specialtyId": "{{categoriaId}}", "role": "tecnico"},
                previo=["pm.collectionVariables.set('documento', String(Date.now()).slice(-10));"],
                pruebas=estado(201) + ["pm.collectionVariables.set('tecnicoId', pm.response.json().id);"]),
            req("El administrador aprueba al técnico", "POST", "/v1/admin/technicians/{{tecnicoId}}/approve",
                [CORR, auth("adminToken")], pruebas=estado(200)),
            login("técnico", "tecnico.qa", "tecnicoToken", "tecnico"),
            req("El técnico cubre toda Bogotá (espera a que Matching lo conozca)", "PUT", "/v1/technicians/me/coverage",
                [JSON, CORR, auth("tecnicoToken")], {"localityCodes": LOCALIDADES},
                pruebas=reintentar("pm.response.code === 200", estado(200))),
            req("El técnico queda disponible", "PUT", "/v1/technicians/me/availability", [JSON, CORR, auth("tecnicoToken")],
                {"status": "disponible"},
                pruebas=reintentar("pm.response.code === 200", estado(200))),
            req("Registro de otro técnico, sin aprobar", "POST", "/v1/auth/register/technician", [JSON, CORR, CANAL],
                {"email": "tecnico2.qa.{{sufijo}}@quickpatch.test", "password": "{{clave}}", "fullName": "Otro técnico QA",
                 "phone": "3007654322", "documentId": "{{documento2}}", "specialtyId": "{{categoriaId}}", "role": "tecnico"},
                previo=["pm.collectionVariables.set('documento2', String(Date.now() + 7).slice(-10));"],
                pruebas=estado(201) + ["pm.collectionVariables.set('tecnico2Id', pm.response.json().id);"]),
            login("otro técnico", "tecnico2.qa", "otroTecnicoToken", "tecnico"),
            registro_cliente("cliente", "cliente.qa"),
            login("cliente", "cliente.qa", "clienteToken", "cliente"),
            registro_cliente("otro cliente", "cliente2.qa"),
            login("otro cliente", "cliente2.qa", "otroClienteToken", "cliente"),
            registro_cliente("cliente del tenant Beta", "beta.qa", headers=(JSON, CORR, BETA)),
            login("cliente del tenant Beta", "beta.qa", "betaToken", "cliente", headers=(JSON, CORR, BETA)),
        ],
    }


def asignar(n, historia):
    """Crea la solicitud n, el técnico de la prueba acepta la oferta y ServiceRequest la pasa a asignado."""
    s = f"solicitud{n}Id"
    o = f"oferta{n}Id"
    return [
        req(f"Crear la solicitud {n} (espera la réplica de la categoría)", "POST", "/v1/service-requests",
            [JSON, CORR, auth("clienteToken")],
            {"categoryId": "{{categoriaId}}", "description": f"Prueba de punta a punta {historia}, solicitud {n}",
             "location": {"latitude": 4.6486, "longitude": -74.063}, "addressText": "Calle 63 # 9-45, apto 201"},
            pruebas=reintentar("pm.response.code !== 422", estado(201) + [
                f"pm.collectionVariables.set('{s}', pm.response.json().id);",
            ], maximo=10)),
        req(f"El técnico ve la oferta de la solicitud {n}", "GET", "/v1/matching/offers?status=pendiente",
            [CORR, auth("tecnicoToken")],
            pruebas=[
                f"const oferta = pm.response.code === 200 && pm.response.json().items.find(x => x.serviceRequestId === pm.collectionVariables.get('{s}'));",
                *reintentar("oferta", [
                    "pm.test('la oferta está pendiente para el técnico', () => pm.expect(oferta).to.be.ok);",
                    f"if (oferta) {{ pm.collectionVariables.set('{o}', oferta.attemptId); }}",
                ]),
            ]),
        req(f"El técnico acepta la oferta de la solicitud {n}", "POST", "/v1/matching/offers/{{" + o + "}}/accept",
            [CORR, auth("tecnicoToken")], pruebas=estado(200)),
        req(f"La solicitud {n} queda asignada (matching.technician-assigned)", "GET", "/v1/service-requests/{{" + s + "}}",
            [CORR, auth("clienteToken")],
            pruebas=reintentar("pm.response.json().status === 'asignado'", [
                "pm.test('asignado al técnico de la prueba', () => {",
                "  pm.expect(pm.response.json().status).to.eql('asignado');",
                "  pm.expect(pm.response.json().technicianId).to.eql(pm.collectionVariables.get('tecnicoId'));",
                "});",
            ])),
    ]


def quotes(n):
    return f"/v1/service-requests/{{{{solicitud{n}Id}}}}/quotes"


def emitir(n, nombre, mano, materiales, numero, variable, detalle="Cambio de sifón y empaques."):
    total = f"{float(mano) + float(materiales):.2f}"
    return req(nombre, "POST", quotes(n), [JSON, CORR, auth("tecnicoToken")],
               {"laborAmount": mano, "materialsAmount": materiales, "detail": detalle},
               pruebas=[
                   "pm.test('201 con el contrato Quote', () => {",
                   "  pm.response.to.have.status(201);",
                   "  const q = pm.response.json();",
                   f"  pm.expect(q.quoteNumber).to.eql({numero});",
                   "  pm.expect(q.status).to.eql('pendiente');",
                   f"  pm.expect(q.totalAmount).to.eql('{total}');",
                   "  pm.expect(new Date(q.expiresAt) > new Date(q.createdAt)).to.eql(true);",
                   "  pm.expect(q.respondedAt).to.eql(null);",
                   "});",
                   f"pm.collectionVariables.set('{variable}', pm.response.json().id);",
               ])


def responder(n, cotizacion, accion, nombre, token="clienteToken", motivo=None, pruebas=()):
    cuerpo = {"reason": motivo} if motivo is not None else None
    hs = [CORR, auth(token)] + ([JSON] if cuerpo else [])
    return req(nombre, "POST", quotes(n) + "/{{" + cotizacion + "}}/" + accion, hs, cuerpo, pruebas=pruebas)


def decision(estado_cotizacion, estado_solicitud, restantes):
    return [
        "pm.test('200 con el contrato QuoteDecision', () => {",
        "  pm.response.to.have.status(200);",
        "  const d = pm.response.json();",
        "  pm.expect(Object.keys(d).sort()).to.eql(['quoteId', 'quoteStatus', 'remainingQuotes', 'serviceRequestStatus']);",
        f"  pm.expect(d.quoteStatus).to.eql('{estado_cotizacion}');",
        f"  pm.expect(d.serviceRequestStatus).to.eql('{estado_solicitud}');",
        f"  pm.expect(d.remainingQuotes).to.eql({restantes});",
        "});",
    ]


def disponibilidad(esperado, nombre):
    return req(nombre, "GET", "/v1/technicians/me/availability", [CORR, auth("tecnicoToken")],
               pruebas=reintentar(f"pm.response.code === 200 && pm.response.json().status === '{esperado}'", [
                   f"pm.test('técnico {esperado}', () => pm.expect(pm.response.json().status).to.eql('{esperado}'));",
               ]))


def detalle(n, estado_esperado, nombre, extra=()):
    return req(nombre, "GET", "/v1/service-requests/{{solicitud" + str(n) + "Id}}", [CORR, auth("clienteToken")],
               pruebas=reintentar(f"pm.response.json().status === '{estado_esperado}'", [
                   f"pm.test('{estado_esperado}', () => pm.expect(pm.response.json().status).to.eql('{estado_esperado}'));",
                   *extra,
               ]))


limpieza = {
    "name": "Limpieza",
    "item": [
        req("Suspender al técnico de la prueba", "POST", "/v1/admin/technicians/{{tecnicoId}}/suspend",
            [JSON, CORR, auth("adminToken")], {"reason": "Cuenta de una prueba de QA."}, pruebas=estado(200)),
        req("Desactivar la categoría de la prueba", "PATCH", "/v1/catalog/admin/categories/{{categoriaId}}",
            [JSON, CORR, auth("adminToken")], {"active": False}, pruebas=estado(200)),
    ],
}


def coleccion(nombre, descripcion, carpetas):
    return {
        "info": {"name": nombre, "description": descripcion,
                 "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"},
        "variable": [
            {"key": "baseUrl", "value": "https://qa.quickpatch.internal"},
            {"key": "adminEmail", "value": ""},
            {"key": "adminPassword", "value": ""},
        ],
        "item": carpetas,
    }


cotizacion = coleccion(
    "QUICKPATCH — SCRUM-490 Cotización de punta a punta",
    "RF-34 y RF-35 (SCRUM-486) contra QA, con service-request.v1.yaml 1.6.0. Solicitud 1: el técnico cotiza y el cliente "
    "rechaza las 3 cotizaciones; la tercera cancela la solicitud (RN-Q7) y Matching libera al técnico. Solicitud 2: el "
    "cliente rechaza la primera y acepta la segunda. Casos negativos: monto sin decimales (400), cliente que cotiza (403), "
    "segunda pendiente (409 transicion-invalida), otro cliente (404), cliente de otro tenant (404 por RLS), técnico que "
    "acepta (403) y responder dos veces (409). El vencimiento (RN-Q6) no entra: QUOTE_TTL es de 24 horas en QA. "
    "Variables: baseUrl, adminEmail y adminPassword (secretos de QA, nunca en el repositorio). "
    "Correr con --reporters cli: el reporte JSON de Newman guarda tokens.",
    [
        preparacion("SCRUM-490"),
        {
            "name": "1. Tres cotizaciones rechazadas: la solicitud se cancela (RN-Q7)",
            "item": [
                *asignar(1, "SCRUM-490"),
                req("Sin cotizaciones, la lista está vacía", "GET", quotes(1), [CORR, auth("clienteToken")],
                    pruebas=estado(200) + ["pm.test('[]', () => pm.expect(pm.response.json()).to.eql([]));"]),
                req("Monto sin decimales → 400", "POST", quotes(1), [JSON, CORR, auth("tecnicoToken")],
                    {"laborAmount": "120000", "materialsAmount": "0.00"},
                    pruebas=error(400, "validacion") + [
                        "pm.test('error en laborAmount', () => pm.expect(pm.response.json().errors).to.have.property('laborAmount'));",
                    ]),
                req("El cliente no cotiza → 403", "POST", quotes(1), [JSON, CORR, auth("clienteToken")],
                    {"laborAmount": "1.00", "materialsAmount": "0.00"}, pruebas=error(403)),
                emitir(1, "Cotización 1", "120000.00", "65000.00", 1, "cot1"),
                detalle(1, "cotizado", "La solicitud pasa a cotizado"),
                req("Otra cotización con una pendiente → 409", "POST", quotes(1), [JSON, CORR, auth("tecnicoToken")],
                    {"laborAmount": "1.00", "materialsAmount": "0.00"}, pruebas=error(409, "transicion-invalida")),
                responder(1, "cot1", "accept", "El técnico no acepta → 403", token="tecnicoToken", pruebas=error(403)),
                responder(1, "cot1", "accept", "Otro cliente del mismo tenant → 404", token="otroClienteToken",
                          pruebas=error(404)),
                req("El cliente de otro tenant no ve las cotizaciones → 404 (RLS)", "GET", quotes(1), [CORR, auth("betaToken")],
                    pruebas=error(404)),
                responder(1, "cot1", "reject", "Motivo de 3 caracteres → 400", motivo="no", pruebas=error(400, "validacion")),
                responder(1, "cot1", "reject", "El cliente rechaza la cotización 1 con motivo",
                          motivo="El valor de los materiales es muy alto.",
                          pruebas=decision("rechazada", "asignado", 2)),
                responder(1, "cot1", "reject", "Rechazarla otra vez → 409", pruebas=error(409, "transicion-invalida")),
                emitir(1, "Cotización 2", "110000.00", "60000.00", 2, "cot2"),
                responder(1, "cot2", "reject", "El cliente rechaza la cotización 2 sin motivo",
                          pruebas=decision("rechazada", "asignado", 1)),
                emitir(1, "Cotización 3", "100000.00", "55000.00", 3, "cot3"),
                responder(1, "cot3", "reject", "El cliente rechaza la tercera: la solicitud se cancela",
                          pruebas=decision("rechazada", "cancelado", 0)),
                detalle(1, "cancelado", "La solicitud queda cancelada por el sistema", extra=[
                    "pm.test('motivo de RN-Q7', () => pm.expect(pm.response.json().cancellationReason).to.eql('Cotizaciones rechazadas.'));",
                ]),
                req("El técnico ve las 3 cotizaciones rechazadas, la primera con su motivo", "GET", quotes(1),
                    [CORR, auth("tecnicoToken")],
                    pruebas=estado(200) + [
                        "pm.test('3 rechazadas en orden', () => {",
                        "  const l = pm.response.json();",
                        "  pm.expect(l.map(q => q.quoteNumber)).to.eql([1, 2, 3]);",
                        "  pm.expect(l.every(q => q.status === 'rechazada')).to.eql(true);",
                        "  pm.expect(l[0].rejectionReason).to.eql('El valor de los materiales es muy alto.');",
                        "  pm.expect(l[1].rejectionReason).to.eql(null);",
                        "});",
                    ]),
                disponibilidad("disponible", "El técnico vuelve a disponible (Matching consumió service-request.cancelled)"),
            ],
        },
        {
            "name": "2. Rechazar una y aceptar la siguiente",
            "item": [
                *asignar(2, "SCRUM-490"),
                emitir(2, "Cotización 1 de la solicitud 2", "120000.00", "65000.00", 1, "cot4"),
                responder(2, "cot4", "reject", "El cliente la rechaza", motivo="Prefiero otra marca de sifón.",
                          pruebas=decision("rechazada", "asignado", 2)),
                emitir(2, "Cotización 2 de la solicitud 2", "120000.00", "40000.00", 2, "cot5"),
                responder(2, "cot5", "accept", "El cliente acepta la cotización 2",
                          pruebas=decision("aceptada", "cotizacion_aceptada", 1)),
                responder(2, "cot5", "accept", "Aceptarla otra vez → 409", pruebas=error(409, "transicion-invalida")),
                detalle(2, "cotizacion_aceptada", "La solicitud queda en cotizacion_aceptada"),
                req("El técnico ve la aceptada con el total a cobrar", "GET", quotes(2), [CORR, auth("tecnicoToken")],
                    pruebas=estado(200) + [
                        "pm.test('rechazada y aceptada', () => {",
                        "  const l = pm.response.json();",
                        "  pm.expect(l.map(q => q.status)).to.eql(['rechazada', 'aceptada']);",
                        "  pm.expect(l[1].totalAmount).to.eql('160000.00');",
                        "  pm.expect(l[1].respondedAt).to.be.a('string');",
                        "});",
                    ]),
                req("Cotizar con la aceptada → 409", "POST", quotes(2), [JSON, CORR, auth("tecnicoToken")],
                    {"laborAmount": "1.00", "materialsAmount": "0.00"}, pruebas=error(409, "transicion-invalida")),
                disponibilidad("ocupado", "El técnico sigue ocupado con la solicitud 2"),
            ],
        },
        {
            "name": "3. Cerrar la solicitud 2",
            "item": [
                req("El cliente cancela la solicitud 2 (cotizacion_aceptada aún se puede cancelar, RN-SR7)", "POST",
                    "/v1/service-requests/{{solicitud2Id}}/cancel", [JSON, CORR, auth("clienteToken")],
                    {"reason": "Fin de la prueba SCRUM-490."}, pruebas=estado(200)),
                disponibilidad("disponible", "El técnico queda libre"),
            ],
        },
        limpieza,
    ],
)

evidencia = coleccion(
    "QUICKPATCH — SCRUM-96 Iniciar, evidencia y completar de punta a punta",
    "RF-14 y RF-15 (SCRUM-35) contra QA, con service-request.v1.yaml 1.7.0: cotizacion_aceptada → en_progreso → foto en "
    "Garage → completado, y Matching libera al técnico al consumir service-request.completed. Casos negativos: subir o "
    "completar antes de iniciar (409), cliente que inicia (403), otro técnico (404), completar sin evidencia (422 "
    "evidencia-requerida), archivo que no es imagen (400 en file), cliente de otro tenant (404 por RLS) y subir después de "
    "completar (409). El límite de 10 MB y de 10 fotos lo cubren las pruebas del backend. Variables: baseUrl, adminEmail y "
    "adminPassword (secretos de QA, nunca en el repositorio). Las fotos están en fixtures/ (carpeta de trabajo: "
    "tests/e2e). Correr con --reporters cli: el reporte JSON de Newman guarda tokens.",
    [
        preparacion("SCRUM-96"),
        {
            "name": "1. Hasta la cotización aceptada",
            "item": [
                *asignar(1, "SCRUM-96"),
                emitir(1, "El técnico cotiza", "150000.00", "35000.00", 1, "cot1"),
                responder(1, "cot1", "accept", "El cliente acepta", pruebas=decision("aceptada", "cotizacion_aceptada", 2)),
            ],
        },
        {
            "name": "2. Iniciar",
            "item": [
                req("Subir una foto antes de iniciar → 409", "POST", "/v1/service-requests/{{solicitud1Id}}/evidence",
                    [CORR, auth("tecnicoToken")], archivo=FOTO, pruebas=error(409, "transicion-invalida")),
                req("Completar antes de iniciar → 409", "POST", "/v1/service-requests/{{solicitud1Id}}/complete",
                    [CORR, auth("tecnicoToken")], pruebas=error(409, "transicion-invalida")),
                req("El cliente no inicia → 403", "POST", "/v1/service-requests/{{solicitud1Id}}/start",
                    [CORR, auth("clienteToken")], pruebas=error(403)),
                req("Otro técnico no inicia → 404", "POST", "/v1/service-requests/{{solicitud1Id}}/start",
                    [CORR, auth("otroTecnicoToken")], pruebas=error(404)),
                req("El técnico asignado inicia", "POST", "/v1/service-requests/{{solicitud1Id}}/start",
                    [CORR, auth("tecnicoToken")],
                    pruebas=[
                        "pm.test('200 con el contrato StartedServiceRequest', () => {",
                        "  pm.response.to.have.status(200);",
                        "  const r = pm.response.json();",
                        "  pm.expect(Object.keys(r).sort()).to.eql(['id', 'startedAt', 'status']);",
                        "  pm.expect(r.status).to.eql('en_progreso');",
                        "});",
                    ]),
                req("Iniciar otra vez → 409", "POST", "/v1/service-requests/{{solicitud1Id}}/start",
                    [CORR, auth("tecnicoToken")], pruebas=error(409, "transicion-invalida")),
                req("El cliente ya no puede cancelar → 409 (RN-SR7)", "POST", "/v1/service-requests/{{solicitud1Id}}/cancel",
                    [JSON, CORR, auth("clienteToken")], {"reason": "Ya no lo necesito."}, pruebas=error(409, "transicion-invalida")),
            ],
        },
        {
            "name": "3. Evidencia en Garage",
            "item": [
                req("Completar sin fotos → 422 evidencia-requerida", "POST", "/v1/service-requests/{{solicitud1Id}}/complete",
                    [CORR, auth("tecnicoToken")], pruebas=error(422, "evidencia-requerida")),
                req("Un archivo que no es imagen → 400 en file", "POST", "/v1/service-requests/{{solicitud1Id}}/evidence",
                    [CORR, auth("tecnicoToken")], archivo=NO_FOTO,
                    pruebas=error(400, "validacion") + [
                        "pm.test('error en file', () => pm.expect(pm.response.json().errors).to.have.property('file'));",
                    ]),
                req("Otro técnico no sube → 404", "POST", "/v1/service-requests/{{solicitud1Id}}/evidence",
                    [CORR, auth("otroTecnicoToken")], archivo=FOTO, pruebas=error(404)),
                req("El técnico asignado sube la foto", "POST", "/v1/service-requests/{{solicitud1Id}}/evidence",
                    [CORR, auth("tecnicoToken")], archivo=FOTO,
                    pruebas=[
                        "pm.test('201 con el contrato Evidence, sin la clave del objeto', () => {",
                        "  pm.response.to.have.status(201);",
                        "  pm.expect(Object.keys(pm.response.json()).sort()).to.eql(['id', 'uploadedAt']);",
                        "});",
                        "pm.collectionVariables.set('evidenciaId', pm.response.json().id);",
                    ]),
                req("El cliente lista las fotos", "GET", "/v1/service-requests/{{solicitud1Id}}/evidence",
                    [CORR, auth("clienteToken")],
                    pruebas=estado(200) + [
                        "pm.test('una foto, solo id y fecha', () => {",
                        "  const items = pm.response.json().items;",
                        "  pm.expect(items).to.have.lengthOf(1);",
                        "  pm.expect(items[0].id).to.eql(pm.collectionVariables.get('evidenciaId'));",
                        "  pm.expect(Object.keys(items[0]).sort()).to.eql(['id', 'uploadedAt']);",
                        "});",
                    ]),
                req("El cliente descarga la foto desde Garage", "GET",
                    "/v1/service-requests/{{solicitud1Id}}/evidence/{{evidenciaId}}/file", [CORR, auth("clienteToken")],
                    pruebas=estado(200) + [
                        "pm.test('image/png con los mismos bytes', () => {",
                        "  pm.expect(pm.response.headers.get('Content-Type')).to.include('image/png');",
                        f"  pm.expect(pm.response.responseSize).to.eql({len(PNG)});",
                        "});",
                        "pm.test('caché privada', () => pm.expect(pm.response.headers.get('Cache-Control')).to.include('private'));",
                    ]),
                req("El administrador del tenant ve las fotos", "GET", "/v1/service-requests/{{solicitud1Id}}/evidence",
                    [CORR, auth("adminToken")],
                    pruebas=estado(200) + ["pm.test('una foto', () => pm.expect(pm.response.json().items).to.have.lengthOf(1));"]),
                req("Otro cliente no ve las fotos → 404", "GET", "/v1/service-requests/{{solicitud1Id}}/evidence",
                    [CORR, auth("otroClienteToken")], pruebas=error(404)),
                req("El cliente de otro tenant no descarga la foto → 404 (RLS)", "GET",
                    "/v1/service-requests/{{solicitud1Id}}/evidence/{{evidenciaId}}/file", [CORR, auth("betaToken")],
                    pruebas=error(404)),
            ],
        },
        {
            "name": "4. Completar",
            "item": [
                req("El técnico completa", "POST", "/v1/service-requests/{{solicitud1Id}}/complete",
                    [CORR, auth("tecnicoToken")],
                    pruebas=[
                        "pm.test('200 con el contrato CompletedServiceRequest', () => {",
                        "  pm.response.to.have.status(200);",
                        "  const r = pm.response.json();",
                        "  pm.expect(Object.keys(r).sort()).to.eql(['completedAt', 'id', 'status']);",
                        "  pm.expect(r.status).to.eql('completado');",
                        "});",
                    ]),
                detalle(1, "completado", "El detalle trae el inicio y el fin", extra=[
                    "pm.test('startedAt y completedAt', () => {",
                    "  const s = pm.response.json();",
                    "  pm.expect(new Date(s.completedAt) >= new Date(s.startedAt)).to.eql(true);",
                    "});",
                ]),
                req("Subir después de completar → 409", "POST", "/v1/service-requests/{{solicitud1Id}}/evidence",
                    [CORR, auth("tecnicoToken")], archivo=FOTO, pruebas=error(409, "transicion-invalida")),
                req("Completar otra vez → 409", "POST", "/v1/service-requests/{{solicitud1Id}}/complete",
                    [CORR, auth("tecnicoToken")], pruebas=error(409, "transicion-invalida")),
                disponibilidad("disponible", "El técnico vuelve a disponible (Matching consumió service-request.completed)"),
            ],
        },
        limpieza,
    ],
)

(AQUI / "fixtures").mkdir(exist_ok=True)
(AQUI / FOTO).write_bytes(PNG)
(AQUI / NO_FOTO).write_text("Esto no es una foto: el backend reconoce el tipo por el contenido.\n", encoding="utf-8")
for nombre, datos in [("scrum-490-cotizacion.postman_collection.json", cotizacion),
                      ("scrum-96-evidencia.postman_collection.json", evidencia)]:
    destino = AQUI / nombre
    destino.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Colección escrita en {destino}")
