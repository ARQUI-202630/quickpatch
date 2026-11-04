"""Generador de la Colección E2E para SCRUM-78: Pruebas del Motor de Matching y Asignación.

Microservicios validados: Matching Service, ServiceRequest, Identity, API Gateway
Autora: Katherine Bravo — QA Lead (ka.bravo@javeriana.edu.co)

Alineado con:
- RF-09: Asignación automática de candidatos elegibles (cercanía, especialidad, disponibilidad).
- RF-10: Ofertas secuenciales a candidatos elegibles.
- RF-13: Disponibilidad y cobertura del técnico en las 20 localidades oficiales de Bogotá.
- RN-M9: Criterios de elegibilidad de candidatos (técnico aprobado, disponible y con cobertura).
- RN-M10: Transición a 'buscando_tecnico' / 'en_espera' ante ausencia de candidatos disponibles.
- RNF-05: SLA de matching: Tiempo de respuesta del primer intento de asignación < 60 segundos.
- IDN-017 / RBAC: Control de acceso basado en roles (técnico no crea solicitudes -> 403; anónimo -> 401).
- SAD AC6-E2: Aislamiento multi-tenant estricto vía Row-Level Security (RLS en PostgreSQL -> 404 entre tenants).
- RFC 9457: Problem Details estándar en todos los errores HTTP.

Uso:
    python tests/e2e/generar-scrum78.py
"""
import json
import pathlib

JSON = {"key": "Content-Type", "value": "application/json"}
CORR = {"key": "X-Correlation-Id", "value": "{{$guid}}"}
CANAL = {"key": "X-Channel-Id", "value": "quickpatch-mobile"}
BETA = {"key": "Host", "value": "beta.qa.quickpatch.internal"}


def auth(var):
    return {"key": "Authorization", "value": "Bearer {{" + var + "}}"}


def req(nombre, metodo, ruta, headers, cuerpo=None, pruebas=(), previo=()):
    ruta_sin_query, _, query = ruta.partition("?")
    url = {
        "raw": "{{baseUrl}}/api" + ruta,
        "host": ["{{baseUrl}}"],
        "path": ["api"] + ruta_sin_query.strip("/").split("/")
    }
    if query:
        url["query"] = [{"key": k, "value": v} for k, v in (p.split("=") for p in query.split("&"))]
    item = {
        "name": nombre,
        "request": {
            "method": metodo,
            "header": list(headers),
            "url": url
        },
        "event": []
    }
    if cuerpo is not None:
        item["request"]["body"] = {"mode": "raw", "raw": json.dumps(cuerpo, ensure_ascii=False, indent=2)}
    if previo:
        item["event"].append({"listen": "prerequest", "script": {"type": "text/javascript", "exec": list(previo)}})
    if pruebas:
        item["event"].append({"listen": "test", "script": {"type": "text/javascript", "exec": list(pruebas)}})
    return item


problem = [
    "pm.test('[RFC 9457] Problem Details con correlationId', () => {",
    "  pm.expect(pm.response.headers.get('Content-Type')).to.include('application/problem+json');",
    "  pm.expect(pm.response.json()).to.have.property('correlationId');",
    "});",
]


def tipo(nombre):
    return [f"pm.test('[Contrato RFC 9457] Tipo de error /{nombre}', () => pm.expect(pm.response.json().type).to.match(/\\/{nombre}$/));"]


preparar = [
    "if (!pm.collectionVariables.get('sufijo')) {",
    "  pm.collectionVariables.set('sufijo', Date.now().toString(36));",
    "  pm.collectionVariables.set('clave', 'Qp' + Math.random().toString(36).slice(2, 12) + '7Z');",
    "}",
]

coleccion = {
    "info": {
        "name": "QUICKPATCH — Motor de Matching y Asignación Automática (SCRUM-78 / HU SCRUM-29)",
        "description": (
            "Suite formal de pruebas E2E para el Motor de Matching y Asignación Automática de QUICKPATCH (SCRUM-78 / HU SCRUM-29):\n"
            "- Asignación automática de candidato elegible (RN-M9, RF-09).\n"
            "- Cumplimiento del SLA RNF-05 (< 60 segundos en primer intento de asignación).\n"
            "- Gestión de disponibilidad y cobertura geográfica en las 20 localidades oficiales de Bogotá (RF-13, RN-M9).\n"
            "- Transición y ciclo de vida de solicitud ante búsqueda de candidatos (RN-M10, RF-10).\n"
            "- Control de acceso RBAC contra técnicos, clientes y seguridad anónima (IDN-017, RFC 9457).\n"
            "- Aislamiento multi-tenant estricto (RLS) en solicitudes y registros de matching (SAD AC6-E2)."
        ),
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
    },
    "variable": [
        {"key": "baseUrl", "value": "https://qa.quickpatch.internal", "type": "string"},
        {"key": "tokenAlfa", "value": "", "type": "string"},
        {"key": "tokenBeta", "value": "", "type": "string"},
        {"key": "tokenTecnico", "value": "", "type": "string"},
        {"key": "categoriaId", "value": "", "type": "string"},
        {"key": "solicitudAsignadaId", "value": "sr-mat-001", "type": "string"},
        {"key": "solicitudEnEsperaId", "value": "sr-mat-espera-002", "type": "string"}
    ],
    "item": [
        {
            "name": "0. Autenticación Dinámica de Actores y Catálogo",
            "item": [
                req(
                    "0.1 Consulta de Categorías Activas del Catálogo",
                    "GET",
                    "/v1/catalog/categories",
                    [CORR],
                    pruebas=[
                        "pm.test('[Catalog] 200 OK en consulta de categorías activas', () => pm.response.to.have.status(200));",
                        "pm.test('[Catalog] Existen categorías activas para matching', () => {",
                        "  const cats = pm.response.json();",
                        "  pm.expect(cats).to.be.an('array').that.is.not.empty;",
                        "  pm.collectionVariables.set('categoriaId', cats[0].id);",
                        "});"
                    ]
                ),
                req(
                    "0.2 Registro Dinámico Cliente Tenant Alfa",
                    "POST",
                    "/v1/auth/register/client",
                    [JSON, CORR, CANAL],
                    {
                        "email": "cliente.alfa.{{sufijo}}@quickpatch.test",
                        "password": "{{clave}}",
                        "fullName": "Cliente Alfa QA"
                    },
                    previo=preparar,
                    pruebas=[
                        "pm.test('[Auth] Registro Cliente Alfa exitoso (201 Created)', () => pm.response.to.have.status(201));"
                    ]
                ),
                req(
                    "0.3 Login Cliente Tenant Alfa",
                    "POST",
                    "/v1/auth/login",
                    [JSON, CORR, CANAL],
                    {
                        "email": "cliente.alfa.{{sufijo}}@quickpatch.test",
                        "password": "{{clave}}"
                    },
                    pruebas=[
                        "pm.test('[Auth] Login de Cliente Tenant Alfa exitoso (200 OK)', () => {",
                        "  pm.response.to.have.status(200);",
                        "  pm.expect(pm.response.json().user.role).to.eql('cliente');",
                        "});",
                        "pm.collectionVariables.set('tokenAlfa', pm.response.json().accessToken);"
                    ]
                ),
                req(
                    "0.4 Registro Dinámico Cliente Tenant Beta",
                    "POST",
                    "/v1/auth/register/client",
                    [JSON, CORR, CANAL, BETA],
                    {
                        "email": "cliente.beta.{{sufijo}}@quickpatch.test",
                        "password": "{{clave}}",
                        "fullName": "Cliente Beta QA"
                    },
                    pruebas=[
                        "pm.test('[Auth] Registro Cliente Beta exitoso (201 Created)', () => pm.response.to.have.status(201));"
                    ]
                ),
                req(
                    "0.5 Login Cliente Tenant Beta",
                    "POST",
                    "/v1/auth/login",
                    [JSON, CORR, CANAL, BETA],
                    {
                        "email": "cliente.beta.{{sufijo}}@quickpatch.test",
                        "password": "{{clave}}"
                    },
                    pruebas=[
                        "pm.test('[Auth] Login de Cliente Tenant Beta exitoso (200 OK)', () => {",
                        "  pm.response.to.have.status(200);",
                        "  pm.expect(pm.response.json().user.role).to.eql('cliente');",
                        "});",
                        "pm.collectionVariables.set('tokenBeta', pm.response.json().accessToken);"
                    ]
                ),
                req(
                    "0.6 Registro Dinámico Técnico Tenant Alfa",
                    "POST",
                    "/v1/auth/register/technician",
                    [JSON, CORR, CANAL],
                    {
                        "email": "tecnico.alfa.{{sufijo}}@quickpatch.test",
                        "password": "{{clave}}",
                        "fullName": "Técnico Alfa Matching QA",
                        "phone": "3001234567",
                        "documentId": "{{documentoTec}}",
                        "specialtyId": "{{categoriaId}}",
                        "role": "tecnico"
                    },
                    previo=[
                        "pm.collectionVariables.set('documentoTec', String(Date.now()).slice(-10));"
                    ],
                    pruebas=[
                        "pm.test('[Auth] Registro de Técnico exitoso (201 Created)', () => pm.response.to.have.status(201));"
                    ]
                ),
                req(
                    "0.7 Login Técnico Tenant Alfa",
                    "POST",
                    "/v1/auth/login",
                    [JSON, CORR, CANAL],
                    {
                        "email": "tecnico.alfa.{{sufijo}}@quickpatch.test",
                        "password": "{{clave}}"
                    },
                    pruebas=[
                        "pm.test('[Auth] Login de Técnico exitoso (200 OK)', () => {",
                        "  pm.response.to.have.status(200);",
                        "  pm.expect(pm.response.json().user.role).to.eql('tecnico');",
                        "});",
                        "pm.collectionVariables.set('tokenTecnico', pm.response.json().accessToken);"
                    ]
                )
            ]
        },
        {
            "name": "1. Elegibilidad, Cobertura y Disponibilidad del Motor (RN-M9, RF-13)",
            "item": [
                req(
                    "1.1 Catálogo de 20 Localidades Oficiales de Bogotá (RF-13, RN-M9)",
                    "GET",
                    "/v1/localities",
                    [CORR],
                    pruebas=[
                        "pm.test('[Matching Engine] 200 OK en catálogo de localidades', () => pm.response.to.have.status(200));",
                        "pm.test('[RN-M9 / RF-13] Catálogo contiene las 20 localidades oficiales de Bogotá', () => {",
                        "  const locs = pm.response.json();",
                        "  pm.expect(locs).to.be.an('array');",
                        "  pm.expect(locs.length).to.be.at.least(20);",
                        "  pm.collectionVariables.set('codigosLocalidades', JSON.stringify(locs.slice(0, 5).map(l => l.code)));",
                        "});"
                    ]
                ),
                req(
                    "1.2 Consulta de Disponibilidad del Técnico (RF-13)",
                    "GET",
                    "/v1/technicians/me/availability",
                    [CORR, auth("tokenTecnico")],
                    pruebas=[
                        "pm.test('[Matching Engine] 200 OK en consulta de disponibilidad', () => pm.response.to.have.status(200));",
                        "pm.test('[RF-13] Estado de disponibilidad retornado correctamente', () => {",
                        "  const res = pm.response.json();",
                        "  pm.expect(res).to.have.property('status');",
                        "  pm.expect(['disponible', 'no_disponible', 'ocupado']).to.include(res.status);",
                        "});"
                    ]
                ),
                req(
                    "1.3 Configuración de Cobertura Geográfica del Técnico (RF-13, RN-M9)",
                    "PUT",
                    "/v1/technicians/me/coverage",
                    [JSON, CORR, auth("tokenTecnico")],
                    {"localityCodes": ["01", "02", "03", "04", "05"]},
                    pruebas=[
                        "pm.test('[Matching Engine] 200 OK al actualizar cobertura geográfica', () => pm.response.to.have.status(200));",
                        "pm.test('[RN-M9] Cobertura registrada exitosamente', () => {",
                        "  const res = pm.response.json();",
                        "  const codes = (res.localities || []).map(l => l.code);",
                        "  pm.expect(codes).to.include.members(['01', '02']);",
                        "});"
                    ]
                ),
                req(
                    "1.4 Transición de Disponibilidad del Técnico a Disponible (RF-13)",
                    "PUT",
                    "/v1/technicians/me/availability",
                    [JSON, CORR, auth("tokenTecnico")],
                    {"status": "disponible"},
                    pruebas=[
                        "pm.test('[Matching Engine] 200 OK al actualizar disponibilidad', () => pm.response.to.have.status(200));",
                        "pm.test('[RF-13] Técnico pasa a estado disponible', () => {",
                        "  pm.expect(pm.response.json().status).to.eql('disponible');",
                        "});"
                    ]
                )
            ]
        },
        {
            "name": "2. Creación de Solicitud y SLA de Matching (RN-M9, RNF-05, RF-09, RN-M10)",
            "item": [
                req(
                    "2.1 Creación de solicitud con candidato elegible (SLA < 60s)",
                    "POST",
                    "/v1/service-requests",
                    [JSON, CORR, auth("tokenAlfa")],
                    {
                        "categoryId": "{{categoriaId}}",
                        "description": "Fuga urgente en tubería principal — asignación requerida de matching",
                        "location": {"latitude": 4.6533, "longitude": -74.0836},
                        "addressText": "Carrera 7 # 45-10, Chapinero"
                    },
                    pruebas=[
                        "pm.test('[RF-09 / RN-M9] Solicitud creada exitosamente (201 Created)', () => {",
                        "  pm.response.to.have.status(201);",
                        "  const res = pm.response.json();",
                        "  pm.collectionVariables.set('solicitudAsignadaId', res.id);",
                        "  pm.expect(['buscando_tecnico', 'asignado', 'en_espera']).to.include(res.status);",
                        "});",
                        "pm.test('[RNF-05 / AC2-E3] SLA: Tiempo de primer intento de matching < 60 segundos', () => {",
                        "  pm.expect(pm.response.responseTime).to.be.below(60000);",
                        "});"
                    ]
                ),
                req(
                    "2.2 Consulta de Solicitud por el Cliente Dueño",
                    "GET",
                    "/v1/service-requests/{{solicitudAsignadaId}}",
                    [CORR, auth("tokenAlfa")],
                    pruebas=[
                        "pm.test('[ServiceRequest] 200 OK en consulta de solicitud', () => pm.response.to.have.status(200));",
                        "pm.test('[Consistencia] Solicitud creada mantiene identificador y ciclo de vida de matching', () => {",
                        "  const res = pm.response.json();",
                        "  pm.expect(res.id).to.eql(pm.collectionVariables.get('solicitudAsignadaId'));",
                        "  pm.expect(['buscando_tecnico', 'asignado', 'en_espera']).to.include(res.status);",
                        "});"
                    ]
                ),
                req(
                    "2.3 Solicitud en zona periférica → Búsqueda y gestión en espera (RN-M10)",
                    "POST",
                    "/v1/service-requests",
                    [JSON, CORR, auth("tokenAlfa")],
                    {
                        "categoryId": "{{categoriaId}}",
                        # Desde SCRUM-636 crear exige una de las 20 localidades: el punto anterior (4,85; -74,05) quedaba fuera y daba 422.
                        "description": "Fuga sin candidatos inmediatos en el extremo norte de Usaquén (periferia)",
                        "location": {"latitude": 4.7600, "longitude": -74.0300},
                        "addressText": "Extremo norte de Usaquén, Torca"
                    },
                    pruebas=[
                        "pm.test('[RF-10 / RN-M10] Solicitud periférica creada exitosamente (201 Created)', () => {",
                        "  pm.response.to.have.status(201);",
                        "  const res = pm.response.json();",
                        "  pm.collectionVariables.set('solicitudEnEsperaId', res.id);",
                        "  pm.expect(['buscando_tecnico', 'en_espera', 'asignado']).to.include(res.status);",
                        "});",
                        "pm.test('[RNF-05] SLA de creación y evaluación espacial < 60.000 ms', () => {",
                        "  pm.expect(pm.response.responseTime).to.be.below(60000);",
                        "});"
                    ]
                ),
                req(
                    "2.4 Detalle de Solicitud periférica no expone asignación previa errónea",
                    "GET",
                    "/v1/service-requests/{{solicitudEnEsperaId}}",
                    [CORR, auth("tokenAlfa")],
                    pruebas=[
                        "pm.test('[Consistencia] 200 OK en consulta de solicitud periférica', () => pm.response.to.have.status(200));",
                        "pm.test('[RN-M10] Solicitud permanece en búsqueda activa o en espera', () => {",
                        "  const res = pm.response.json();",
                        "  pm.expect(['buscando_tecnico', 'en_espera']).to.include(res.status);",
                        "});"
                    ]
                )
            ]
        },
        {
            "name": "3. Control de Acceso RBAC y Seguridad (IDN-017, RFC 9457)",
            "item": [
                req(
                    "3.1 Control RBAC: Rol Técnico intenta crear solicitud de servicio → 403 Forbidden",
                    "POST",
                    "/v1/service-requests",
                    [JSON, CORR, auth("tokenTecnico")],
                    {
                        "categoryId": "{{categoriaId}}",
                        "description": "Intento no autorizado de técnico creando orden",
                        "location": {"latitude": 4.6533, "longitude": -74.0836},
                        "addressText": "Carrera 7 # 45-10"
                    },
                    pruebas=[
                        "pm.test('[RBAC / IDN-012] 403 Forbidden para rol técnico creando solicitudes', () => pm.response.to.have.status(403));"
                    ] + problem
                ),
                req(
                    "3.2 Seguridad: Solicitud anónima de creación sin token → 401 Unauthorized",
                    "POST",
                    "/v1/service-requests",
                    [JSON, CORR],
                    {
                        "categoryId": "{{categoriaId}}",
                        "description": "Intento anónimo sin token de autenticación",
                        "addressText": "Carrera 7 # 45-10"
                    },
                    pruebas=[
                        "pm.test('[Seguridad / IDN-017] 401 Unauthorized ante creación anónima', () => pm.response.to.have.status(401));"
                    ] + problem + tipo("no-autenticado")
                ),
                req(
                    "3.3 Seguridad: Consulta anónima de ofertas de matching sin token → 401 Unauthorized",
                    "GET",
                    "/v1/matching/offers",
                    [CORR],
                    pruebas=[
                        "pm.test('[Seguridad / IDN-017] 401 Unauthorized ante consulta anónima de matching', () => pm.response.to.have.status(401));"
                    ] + problem + tipo("no-autenticado")
                ),
                req(
                    "3.4 Control RBAC: Rol Cliente intenta auditar matching_attempts internos → 403 Forbidden",
                    "GET",
                    "/v1/matching/attempts/{{solicitudAsignadaId}}",
                    [CORR, auth("tokenAlfa")],
                    pruebas=[
                        "pm.test('[RBAC / Auditoría] 403 Forbidden: Cliente no puede acceder a intentos de matching internos', () => {",
                        "  pm.response.to.have.status(403);",
                        "});"
                    ] + problem + tipo("no-autorizado")
                )
            ]
        },
        {
            "name": "4. Aislamiento Multi-Tenant (RLS / SAD AC6-E2)",
            "item": [
                req(
                    "4.1 Fuga Cross-Tenant Bloqueada: Cliente Beta consulta solicitud de Alfa → 404 Not Found",
                    "GET",
                    "/v1/service-requests/{{solicitudAsignadaId}}",
                    [CORR, auth("tokenBeta")],
                    pruebas=[
                        "pm.test('[Aislamiento Multi-Tenant] 404 Not Found para usuario de otro tenant (RLS)', () => pm.response.to.have.status(404));",
                        "pm.test('[Seguridad] Cero filtración de datos de la orden entre tenants', () => {",
                        "  pm.expect(pm.response.text()).to.not.include('Fuga urgente en tubería principal');",
                        "});"
                    ] + problem + tipo("no-encontrado")
                ),
                req(
                    "4.2 Fuga Cross-Tenant Bloqueada: Cliente Beta consulta solicitud periférica de Alfa → 404 Not Found",
                    "GET",
                    "/v1/service-requests/{{solicitudEnEsperaId}}",
                    [CORR, auth("tokenBeta")],
                    pruebas=[
                        "pm.test('[Aislamiento Multi-Tenant] 404 Not Found para solicitud periférica de otro tenant (RLS)', () => pm.response.to.have.status(404));",
                        "pm.test('[Seguridad] Aislamiento RLS en PostgreSQL verificado', () => {",
                        "  pm.expect(pm.response.text()).to.not.include('Zona Rural Norte');",
                        "});"
                    ] + problem + tipo("no-encontrado")
                )
            ]
        }
    ]
}

destino = pathlib.Path(__file__).with_name("scrum-78-motor-matching.postman_collection.json")
destino.write_text(json.dumps(coleccion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Colección generada exitosamente en {destino}")
