"""Genera scrum-511-tenant-desactivado.postman_collection.json: tenant desactivado contra QA (SCRUM-511, RN-T1).

Uso: python tests/e2e/generar-scrum511-tenant-desactivado.py
La colección se edita aquí y se regenera, para que el JSON siempre sea válido y revisable en los PR.

Cubre la HU SCRUM-348 (RF-21, RN-T1, ADR-017): con el tenant desactivado, un token que sigue vigente ya no crea
solicitudes (422 tenant-inactivo en segundos, sin esperar los 60 minutos del token), y al reactivar vuelve a crear.
Usa datos propios: el tenant Beta de QA (beta.qa.quickpatch.internal) y un cliente nuevo de ese tenant, con correo y
clave generados en la corrida. Nunca toca el tenant principal de QA. Todos los pasos se omiten si no llegan
platformAdminEmail y platformAdminPassword (secretos de QA, nunca en el repositorio).

Beta no tiene categorías, así que la solicitud no llega a crearse con 201: el contraste se hace con el tipo de error
(categoría no disponible con el tenant activo, tenant-inactivo desactivado y otra vez categoría al reactivar), igual
que en la corrida manual del 2 de noviembre (evidencias/tenant-desactivado-qa-2026-11-02.txt).

Newman no se detiene cuando falla una aserción, así que la carpeta 4 (reactivar Beta) siempre corre. La carpeta 0
también deja Beta activo antes de empezar, por si una corrida anterior se cortó con el tenant desactivado.
"""
import json
import pathlib

JSON = {"key": "Content-Type", "value": "application/json"}
CORR = {"key": "X-Correlation-Id", "value": "{{$guid}}"}
CANAL = {"key": "X-Channel-Id", "value": "quickpatch-mobile"}
# El Nginx de VM1 fija el canal (y con él el tenant) por el nombre del host (quickpatch-api-gateway#16).
BETA = {"key": "Host", "value": "beta.qa.quickpatch.internal"}
# NIT del tenant Beta de QA (evidencias/tenant-desactivado-qa-2026-11-02.txt).
NIT_BETA = "900999001-1"


def auth(var):
    return {"key": "Authorization", "value": "Bearer {{" + var + "}}"}


def req(nombre, metodo, ruta, headers, cuerpo=None, pruebas=(), previo=()):
    url = {"raw": "{{baseUrl}}/api" + ruta, "host": ["{{baseUrl}}"], "path": ["api"] + ruta.strip("/").split("/")}
    item = {"name": nombre, "request": {"method": metodo, "header": list(headers), "url": url}, "event": []}
    if cuerpo is not None:
        item["request"]["body"] = {"mode": "raw", "raw": json.dumps(cuerpo, ensure_ascii=False, indent=2)}
    if previo:
        item["event"].append({"listen": "prerequest", "script": {"type": "text/javascript", "exec": list(previo)}})
    if pruebas:
        item["event"].append({"listen": "test", "script": {"type": "text/javascript", "exec": list(pruebas)}})
    return item


# Sin el administrador de la plataforma no se puede desactivar Beta: se omite todo.
CON_PLATAFORMA = ["if (!pm.variables.get('platformAdminEmail')) { pm.execution.skipRequest(); }"]
# Si no se encontró Beta (o resultó ser el tenant de la plataforma) no se sigue: nunca se toca otro tenant.
CON_BETA = CON_PLATAFORMA + [
    "if (!pm.collectionVariables.get('betaId')) { pm.execution.skipRequest(); }",
]

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


def reintentar(condicion, pruebas, maximo=20, espera=500):
    """Repite la petición mientras `condicion` (JS) sea falsa: el estado del tenant llega a ServiceRequest por Kafka."""
    return [
        "const intento = Number(pm.collectionVariables.get('intentos') || 0);",
        f"if (!({condicion}) && intento < {maximo}) {{",
        "  pm.collectionVariables.set('intentos', intento + 1);",
        f"  setTimeout(() => {{}}, {espera});",
        "  pm.execution.setNextRequest(pm.info.requestId);",
        "} else {",
        "  pm.collectionVariables.unset('intentos');",
        f"  console.log('intentos: ' + intento + ' (cada {espera} ms)');",
        *("  " + linea for linea in pruebas),
        "}",
    ]


# Lee `type` sin romper si la respuesta no es JSON (por ejemplo, un 502 del Ingress mientras se reintenta).
es_tenant_inactivo = ("pm.response.code === 422 && /\\/tenant-inactivo$/.test((() => { try { return pm.response.json().type || ''; } "
                      "catch (e) { return ''; } })())")

preparar = [
    "if (!pm.collectionVariables.get('sufijo')) {",
    "  pm.collectionVariables.set('sufijo', Date.now().toString(36));",
    "  // Clave de la cuenta de prueba de esta corrida; no se guarda en ningún lado.",
    "  pm.collectionVariables.set('clave', 'Qp' + Math.random().toString(36).slice(2, 12) + '7Z');",
    "}",
]


def cambiar_beta(nombre, nuevo):
    return req(nombre, "PATCH", "/v1/platform/tenants/{{betaId}}", [JSON, CORR, auth("plataformaToken")],
               {"status": nuevo}, previo=CON_BETA,
               pruebas=[
                   f"pm.test('200 y Beta queda {nuevo}', () => {{",
                   "  pm.response.to.have.status(200);",
                   f"  pm.expect(pm.response.json().status).to.eql('{nuevo}');",
                   "});",
               ])


# Cuerpo válido de una solicitud en Bogotá. La categoría no existe en Beta: con el tenant activo la petición llega a
# esa validación; con el tenant inactivo se rechaza antes.
SOLICITUD = {"categoryId": "{{categoriaInexistente}}", "description": "Prueba de tenant desactivado (SCRUM-511)",
             "location": {"latitude": 4.6486, "longitude": -74.063}, "addressText": "Calle 63 # 9-45, apto 201"}


def crear(nombre, pruebas, previo=()):
    return req(nombre, "POST", "/v1/service-requests", [JSON, CORR, BETA, auth("clienteToken")], SOLICITUD,
               previo=CON_BETA + list(previo), pruebas=pruebas)


def no_bloqueada_por_tenant(momento):
    return [
        "pm.test('422 por la categoría, no por el tenant', () => {",
        "  pm.response.to.have.status(422);",
        "  pm.expect(pm.response.json().type).to.not.match(/\\/tenant-inactivo$/);",
        "});",
        f"console.log('tipo con el tenant {momento}: ' + pm.response.json().type);",
    ]

coleccion = {
    "info": {
        "name": "QUICKPATCH — SCRUM-511 Tenant desactivado contra QA (RN-T1)",
        "description": (
            "HU SCRUM-348 (RF-21, RN-T1, ADR-017) contra QA con datos propios: un cliente nuevo del tenant Beta conserva "
            "su token; el administrador de la plataforma desactiva Beta y el MISMO token recibe 422 tenant-inactivo al "
            "crear una solicitud en segundos (TNT-003). El token sigue sirviendo para otras operaciones (GET "
            "/v1/users/me, 200); un login nuevo y un registro nuevo en Beta se rechazan con 403 tenant-inactivo. Al "
            "reactivar, la creación deja de responder tenant-inactivo. Beta siempre queda activo al terminar. "
            "Variables: baseUrl, platformAdminEmail y platformAdminPassword (secretos de QA, nunca en el repositorio); "
            "sin ellos se omiten todos los pasos. Contratos: identity.v1.yaml 1.5.0, service-request.v1.yaml 1.11.0."
        ),
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
    },
    "variable": [
        {"key": "baseUrl", "value": "https://qa.quickpatch.internal"},
        {"key": "platformAdminEmail", "value": ""},
        {"key": "platformAdminPassword", "value": ""},
    ],
    "item": [
        {
            "name": "0. Preparación: Beta activo y un cliente nuevo con su token",
            "item": [
                req("Login del administrador de la plataforma", "POST", "/v1/auth/login", [JSON, CORR, CANAL],
                    {"email": "{{platformAdminEmail}}", "password": "{{platformAdminPassword}}"},
                    previo=preparar + CON_PLATAFORMA + [
                        "pm.collectionVariables.set('categoriaInexistente', pm.variables.replaceIn('{{$guid}}'));",
                    ],
                    pruebas=[
                        "pm.test('200 con rol admin_plataforma', () => {",
                        "  pm.response.to.have.status(200);",
                        "  pm.expect(pm.response.json().user.role).to.eql('admin_plataforma');",
                        "});",
                        "pm.collectionVariables.set('plataformaToken', pm.response.json().accessToken);",
                    ]),
                req("Ubicar el tenant Beta por su NIT", "GET", "/v1/platform/tenants", [CORR, auth("plataformaToken")],
                    previo=CON_PLATAFORMA,
                    pruebas=[
                        "pm.test('200', () => pm.response.to.have.status(200));",
                        f"const beta = pm.response.json().find(t => t.nit === '{NIT_BETA}');",
                        "const partes = pm.collectionVariables.get('plataformaToken').split('.')[1].replace(/-/g, '+').replace(/_/g, '/');",
                        "const yo = JSON.parse(CryptoJS.enc.Base64.parse(partes + '='.repeat((4 - partes.length % 4) % 4)).toString(CryptoJS.enc.Utf8));",
                        "pm.test('Beta existe y no es el tenant de la plataforma', () => {",
                        "  pm.expect(beta, 'tenant Beta de QA').to.be.ok;",
                        "  pm.expect(beta.id).to.not.eql(yo.tenant_id);",
                        "});",
                        "// Sin Beta no se sigue: la colección nunca desactiva otro tenant.",
                        "if (beta && beta.id !== yo.tenant_id) { pm.collectionVariables.set('betaId', beta.id); }",
                        "else { pm.collectionVariables.unset('betaId'); }",
                    ]),
                cambiar_beta("Beta activo antes de empezar (idempotente)", "activo"),
                req("Registro de un cliente nuevo en Beta", "POST", "/v1/auth/register/client", [JSON, CORR, CANAL, BETA],
                    {"email": "qa-tenant-inactivo.{{sufijo}}@quickpatch.test", "password": "{{clave}}",
                     "fullName": "Prueba 511 cliente Beta"},
                    previo=CON_BETA, pruebas=estado(201)),
                req("Login del cliente de Beta: su token queda vigente 60 min", "POST", "/v1/auth/login",
                    [JSON, CORR, CANAL, BETA],
                    {"email": "qa-tenant-inactivo.{{sufijo}}@quickpatch.test", "password": "{{clave}}"},
                    previo=CON_BETA,
                    pruebas=[
                        "pm.test('200 con rol cliente', () => {",
                        "  pm.response.to.have.status(200);",
                        "  pm.expect(pm.response.json().user.role).to.eql('cliente');",
                        "});",
                        "pm.collectionVariables.set('clienteToken', pm.response.json().accessToken);",
                        "const partes = pm.response.json().accessToken.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');",
                        "const carga = JSON.parse(CryptoJS.enc.Base64.parse(partes + '='.repeat((4 - partes.length % 4) % 4)).toString(CryptoJS.enc.Utf8));",
                        "pm.test('el token es del tenant Beta', () => pm.expect(carga.tenant_id).to.eql(pm.collectionVariables.get('betaId')));",
                    ]),
            ],
        },
        {
            "name": "1. Tenant activo: la creación no se bloquea por el tenant",
            "item": [
                crear("Crear con el tenant activo → 422 de categoría", no_bloqueada_por_tenant("activo")),
            ],
        },
        {
            "name": "2. Tenant desactivado: el MISMO token ya no crea (TNT-003)",
            "item": [
                cambiar_beta("El administrador de la plataforma desactiva Beta", "inactivo"),
                crear("MISMO token: crear → 422 tenant-inactivo en segundos",
                      previo=["if (!pm.collectionVariables.get('inicio')) { pm.collectionVariables.set('inicio', Date.now()); }"],
                      pruebas=reintentar(es_tenant_inactivo, [
                          "const segundos = (Date.now() - Number(pm.collectionVariables.get('inicio'))) / 1000;",
                          "pm.collectionVariables.unset('inicio');",
                          "console.log('rechazo con tenant-inactivo en ' + segundos.toFixed(1) + ' s');",
                          "pm.test('422 tenant-inactivo', () => pm.response.to.have.status(422));",
                          *tipo("tenant-inactivo"),
                          "pm.test('detalle tenant is disabled', () => pm.expect(pm.response.json().detail).to.eql('tenant is disabled'));",
                          *problem,
                          "pm.test('llega en segundos, no al vencer el token (menos de 15 s)', () => pm.expect(segundos).to.be.below(15));",
                      ], maximo=30)),
                req("MISMO token: GET /v1/users/me sigue respondiendo 200", "GET", "/v1/users/me",
                    [CORR, BETA, auth("clienteToken")], previo=CON_BETA, pruebas=estado(200)),
                req("Login nuevo del cliente de Beta → 403 tenant-inactivo", "POST", "/v1/auth/login", [JSON, CORR, CANAL, BETA],
                    {"email": "qa-tenant-inactivo.{{sufijo}}@quickpatch.test", "password": "{{clave}}"},
                    previo=CON_BETA, pruebas=estado(403) + tipo("tenant-inactivo") + problem),
                req("Registro nuevo en Beta → 403 tenant-inactivo", "POST", "/v1/auth/register/client", [JSON, CORR, CANAL, BETA],
                    {"email": "qa-tenant-inactivo-2.{{sufijo}}@quickpatch.test", "password": "{{clave}}",
                     "fullName": "Prueba 511 segundo cliente"},
                    previo=CON_BETA, pruebas=estado(403) + tipo("tenant-inactivo") + problem),
            ],
        },
        {
            "name": "3. Tenant reactivado: la creación deja de responder tenant-inactivo",
            "item": [
                cambiar_beta("El administrador de la plataforma reactiva Beta", "activo"),
                crear("MISMO token: crear → ya no es tenant-inactivo",
                      pruebas=reintentar(f"!({es_tenant_inactivo})", no_bloqueada_por_tenant("reactivado"), maximo=30)),
            ],
        },
        {
            "name": "4. Cierre: Beta queda activo",
            "item": [
                cambiar_beta("Beta activo al terminar (aunque algo haya fallado antes)", "activo"),
            ],
        },
    ],
}

destino = pathlib.Path(__file__).with_name("scrum-511-tenant-desactivado.postman_collection.json")
destino.write_text(json.dumps(coleccion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Escrita {destino.name}")
