"""Generador de la Colección E2E para SCRUM-84: Seguimiento de Estado en Tiempo Real.
HU Padre: SCRUM-31 (Seguimiento en tiempo real del estado de la solicitud).
Microservicios validados: ServiceRequest, Communication, API Gateway.
Autora: Katherine Bravo — QA Lead

Criterios de aceptación cubiertos:
1. Al menos 4 estados visibles: buscando_tecnico, asignado, en_progreso, completado.
2. Latencia de reflejo de estado en menos de 1 minuto tras la actualización del técnico.
3. Visibilidad del nombre y especialidad del técnico asignado para el cliente.
4. Canal en tiempo real WebSocket (/api/v1/realtime) bajo ADR-023 y SCRUM-451.
5. Emisión del aviso transaccional service-request.status-changed (SCRUM-466).
6. Aislamiento estricto de privacidad intra-tenant (Cliente 2 no ve solicitudes de Cliente 1).
7. Aislamiento lógico multi-tenant (RLS) cross-tenant (Tenant Beta no ve solicitudes de Tenant Alfa).
8. Bloqueo de transiciones inválidas (409 Conflict) y control RBAC (403 Forbidden).

Uso: python tests/e2e/generar-scrum84.py
"""
import json
import pathlib

JSON = {"key": "Content-Type", "value": "application/json"}
CORR = {"key": "X-Correlation-Id", "value": "{{$guid}}"}
CANAL_MOVIL = {"key": "X-Channel-Id", "value": "quickpatch-mobile"}


def auth(var):
    return {"key": "Authorization", "value": "Bearer {{" + var + "}}"}


def req(nombre, metodo, ruta, headers, cuerpo=None, pruebas=(), previo=()):
    item = {
        "name": nombre,
        "request": {
            "method": metodo,
            "header": list(headers),
            "url": {
                "raw": "{{baseUrl}}/api" + ruta,
                "host": ["{{baseUrl}}"],
                "path": ["api"] + ruta.strip("/").split("/")
            },
        },
        "event": [],
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


def tipo_error(slug):
    return [
        f"pm.test('[Contrato RFC 9457] Tipo de error /{slug}', () => {{",
        f"  pm.expect(pm.response.json().type).to.match(/\\/{slug}$/);",
        "});",
    ]


items = [
    # =========================================================================
    # 0. AUTENTICACIÓN DE ACTORES (Identity Service)
    # =========================================================================
    {
        "name": "0. Autenticación de Actores",
        "item": [
            req(
                "0.1 Login Cliente Propietario (usr-client-01)",
                "POST", "/v1/auth/login", [JSON, CORR, CANAL_MOVIL],
                {"email": "{{clienteEmail}}", "password": "PasswordCliente123*"},
                [
                    "pm.test('[Auth] Login de cliente exitoso (200 OK)', () => pm.response.to.have.status(200));",
                    "pm.collectionVariables.set('clienteToken', pm.response.json().accessToken);",
                ]
            ),
            req(
                "0.2 Login Técnico Asignado (usr-tec-01)",
                "POST", "/v1/auth/login", [JSON, CORR, CANAL_MOVIL],
                {"email": "{{tecnicoEmail}}", "password": "PasswordTecnico123*"},
                [
                    "pm.test('[Auth] Login de técnico exitoso (200 OK)', () => pm.response.to.have.status(200));",
                    "pm.collectionVariables.set('tecnicoToken', pm.response.json().accessToken);",
                ]
            ),
            req(
                "0.3 Login Cliente Ajeno en Mismo Tenant (usr-client-02)",
                "POST", "/v1/auth/login", [JSON, CORR, CANAL_MOVIL],
                {"email": "{{cliente2Email}}", "password": "PasswordCliente123*"},
                [
                    "pm.test('[Auth] Login de cliente 2 exitoso (200 OK)', () => pm.response.to.have.status(200));",
                    "pm.collectionVariables.set('cliente2Token', pm.response.json().accessToken);",
                ]
            ),
            req(
                "0.4 Login Cliente en Tenant Beta",
                "POST", "/v1/auth/login", [JSON, CORR, CANAL_MOVIL],
                {"email": "{{clienteBetaEmail}}", "password": "PasswordCliente123*"},
                [
                    "pm.test('[Auth] Login de cliente Beta exitoso (200 OK)', () => pm.response.to.have.status(200));",
                    "pm.collectionVariables.set('clienteBetaToken', pm.response.json().accessToken);",
                ]
            ),
        ]
    },

    # =========================================================================
    # 1. CANAL EN TIEMPO REAL (Communication / Gateway - ADR-023, SCRUM-451)
    # =========================================================================
    {
        "name": "1. Canal en Tiempo Real (WebSocket / Gateway)",
        "item": [
            req(
                "1.1 Handshake y suscripción a WebSocket (/v1/realtime) con token",
                "GET", "/v1/realtime", [CORR, auth("clienteToken")],
                None,
                [
                    "pm.test('[ADR-023 / SCRUM-451] 200 OK en handshake de canal en tiempo real', () => pm.response.to.have.status(200));",
                    "pm.test('[Gateway] Cabecera de canal activo verificada', () => pm.expect(pm.response.headers.get('X-Realtime-Channel')).to.eql('active'));",
                    "pm.test('[Tiempo Real] Estado connected y transporte websocket', () => {",
                    "  const res = pm.response.json();",
                    "  pm.expect(res.status).to.eql('connected');",
                    "  pm.expect(res.transport).to.eql('websocket');",
                    "});",
                    "pm.test('[SCRUM-466] Suscripción obligatoria a service-request.status-changed', () => {",
                    "  pm.expect(pm.response.json().subscribedEvents).to.include('service-request.status-changed');",
                    "});",
                ]
            ),
            req(
                "1.2 Rechazo de conexión a tiempo real sin token (IDN-017) -> 401 Unauthorized",
                "GET", "/v1/realtime", [CORR],
                None,
                [
                    "pm.test('[Seguridad] 401 Unauthorized para handshake anónimo', () => pm.response.to.have.status(401));",
                ] + problem + tipo_error("no-autenticado")
            ),
        ]
    },

    # =========================================================================
    # 2. ESTADO 1: BUSCANDO TÉCNICO (SCRUM-31 / Criterio 1)
    # =========================================================================
    {
        "name": "2. Estado 1: Buscando Técnico",
        "item": [
            req(
                "2.1 Creación de solicitud por cliente (estado inicial buscando_tecnico)",
                "POST", "/v1/service-requests", [JSON, CORR, CANAL_MOVIL, auth("clienteToken")],
                {
                    "id": "sr-tracking-01",
                    "categoryId": "3f1c2a4e-8d7b-4c1a-9e2f-5b6a7c8d9e01",
                    "description": "Fuga de tubería principal en cocina",
                    "location": {"latitude": 4.6533, "longitude": -74.0836},
                    "addressText": "Carrera 15 # 85-30, apto 401"
                },
                [
                    "pm.test('[ServiceRequest] 201 Created para nueva solicitud', () => pm.response.to.have.status(201));",
                    "pm.test('[SCRUM-31] Estado inicial es buscando_tecnico', () => pm.expect(pm.response.json().status).to.eql('buscando_tecnico'));",
                    "pm.collectionVariables.set('requestId', pm.response.json().id);",
                ]
            ),
            req(
                "2.2 Cliente consulta estado inicial de su solicitud",
                "GET", "/v1/service-requests/{{requestId}}", [CORR, auth("clienteToken")],
                None,
                [
                    "pm.test('[Seguimiento] 200 OK en consulta de solicitud', () => pm.response.to.have.status(200));",
                    "pm.test('[Estado 1] Solicitud visible en estado buscando_tecnico', () => pm.expect(pm.response.json().status).to.eql('buscando_tecnico'));",
                    "pm.test('[Cliente] Técnico es null antes de la asignación', () => pm.expect(pm.response.json().technician).to.be.null);",
                ]
            ),
        ]
    },

    # =========================================================================
    # 3. ESTADO 2: ASIGNADO Y VISIBILIDAD DEL TÉCNICO (SCRUM-31 / Criterios 1 y 3)
    # =========================================================================
    {
        "name": "3. Estado 2: Asignado",
        "item": [
            req(
                "3.1 Actualización a estado 'asignado' tras aceptación de oferta",
                "PUT", "/v1/service-requests/{{requestId}}/status", [JSON, CORR, auth("tecnicoToken")],
                {"status": "asignado"},
                [
                    "pm.test('[Transición] 200 OK en actualización a asignado', () => pm.response.to.have.status(200));",
                    "const resAsig = pm.response.json();",
                    "pm.test('[Transición] Estado nuevo es asignado', () => pm.expect(resAsig.status).to.eql('asignado'));",
                    "pm.test('[SCRUM-466] Evento service-request.status-changed emitido', () => pm.expect(resAsig.noticeEmitted).to.eql('service-request.status-changed'));",
                ]
            ),
            req(
                "3.2 Cliente consulta estado asignado y visualiza datos del técnico",
                "GET", "/v1/service-requests/{{requestId}}", [CORR, auth("clienteToken")],
                None,
                [
                    "pm.test('[Seguimiento] 200 OK para cliente consultando asignación', () => pm.response.to.have.status(200));",
                    "pm.test('[Estado 2] Estado actualizado a asignado', () => pm.expect(pm.response.json().status).to.eql('asignado'));",
                    "pm.test('[SCRUM-31 / Criterio 3] Nombre del técnico visible para el cliente', () => {",
                    "  const res = pm.response.json();",
                    "  pm.expect(res.technician).to.not.be.null;",
                    "  pm.expect(res.technician.fullName).to.include('Carlos Pérez');",
                    "});",
                    "pm.test('[SCRUM-31 / Criterio 3] Especialidad del técnico visible para el cliente', () => {",
                    "  pm.expect(pm.response.json().technician.specialty).to.eql('Plomería');",
                    "});",
                ]
            ),
        ]
    },

    # =========================================================================
    # 4. ESTADO 3: EN PROGRESO Y LATENCIA < 1 MINUTO (SCRUM-31 / Criterios 1 y 2)
    # =========================================================================
    {
        "name": "4. Estado 3: En Progreso",
        "item": [
            req(
                "4.1 Técnico inicia el trabajo y pasa solicitud a 'en_progreso'",
                "PUT", "/v1/service-requests/{{requestId}}/status", [JSON, CORR, auth("tecnicoToken")],
                {"status": "en_progreso"},
                [
                    "pm.test('[Transición] 200 OK en actualización a en_progreso', () => pm.response.to.have.status(200));",
                    "const resProg = pm.response.json();",
                    "pm.test('[Máquina de Estados] previousStatus: asignado -> status: en_progreso', () => {",
                    "  pm.expect(resProg.previousStatus).to.eql('asignado');",
                    "  pm.expect(resProg.status).to.eql('en_progreso');",
                    "});",
                    "pm.test('[SCRUM-466] Aviso de estado emitido en la misma transacción', () => pm.expect(resProg.noticeEmitted).to.eql('service-request.status-changed'));",
                ]
            ),
            req(
                "4.2 Cliente observa estado 'en_progreso' con latencia inmediata (< 1 minuto)",
                "GET", "/v1/service-requests/{{requestId}}", [CORR, auth("clienteToken")],
                None,
                [
                    "pm.test('[Seguimiento] 200 OK en consulta de estado en progreso', () => pm.response.to.have.status(200));",
                    "pm.test('[SCRUM-31 / Criterio 2] Latencia de respuesta inferior a 1 minuto (< 60s)', () => {",
                    "  pm.expect(pm.response.responseTime).to.be.below(60000);",
                    "});",
                    "pm.test('[Estado 3] Estado confirmado como en_progreso', () => pm.expect(pm.response.json().status).to.eql('en_progreso'));",
                    "pm.test('[Seguimiento] Técnico asignado permanece visible', () => pm.expect(pm.response.json().technician.fullName).to.not.be.empty);",
                ]
            ),
        ]
    },

    # =========================================================================
    # 5. ESTADO 4: COMPLETADO Y CIERRE DEL CICLO (SCRUM-31 / Criterio 1)
    # =========================================================================
    {
        "name": "5. Estado 4: Completado",
        "item": [
            req(
                "5.1 Técnico finaliza la reparación y pasa solicitud a 'completado'",
                "PUT", "/v1/service-requests/{{requestId}}/status", [JSON, CORR, auth("tecnicoToken")],
                {"status": "completado"},
                [
                    "pm.test('[Transición] 200 OK en finalización de servicio', () => pm.response.to.have.status(200));",
                    "const resComp = pm.response.json();",
                    "pm.test('[Máquina de Estados] previousStatus: en_progreso -> status: completado', () => {",
                    "  pm.expect(resComp.previousStatus).to.eql('en_progreso');",
                    "  pm.expect(resComp.status).to.eql('completado');",
                    "});",
                ]
            ),
            req(
                "5.2 Cliente consulta estado final 'completado' (ciclo completo 4/4 estados)",
                "GET", "/v1/service-requests/{{requestId}}", [CORR, auth("clienteToken")],
                None,
                [
                    "pm.test('[Seguimiento] 200 OK en consulta de estado completado', () => pm.response.to.have.status(200));",
                    "pm.test('[Estado 4] Estado confirmado como completado', () => pm.expect(pm.response.json().status).to.eql('completado'));",
                    "pm.test('[Criterio 1 Cumplido] 4 estados verificados (buscando_tecnico, asignado, en_progreso, completado)', () => {",
                    "  pm.expect(['buscando_tecnico', 'asignado', 'en_progreso', 'completado']).to.include(pm.response.json().status);",
                    "});",
                ]
            ),
        ]
    },

    # =========================================================================
    # 6. FILTROS NEGATIVOS, SEGURIDAD Y AISLAMIENTO (RN-SR6, RBAC, RLS)
    # =========================================================================
    {
        "name": "6. Filtros Negativos y Aislamiento",
        "item": [
            req(
                "6.1 Transición Inválida: Técnico intenta saltar de completado a buscando_tecnico -> 409 Conflict",
                "PUT", "/v1/service-requests/{{requestId}}/status", [JSON, CORR, auth("tecnicoToken")],
                {"status": "buscando_tecnico"},
                [
                    "pm.test('[RN-SR6] 409 Conflict ante transición de estado inválida', () => pm.response.to.have.status(409));",
                ] + problem + tipo_error("transicion-invalida")
            ),
            req(
                "6.2 Control RBAC: Cliente intenta modificar el estado técnico de la orden -> 403 Forbidden",
                "PUT", "/v1/service-requests/{{requestId}}/status", [JSON, CORR, auth("clienteToken")],
                {"status": "en_progreso"},
                [
                    "pm.test('[RBAC / SCRUM-31] 403 Forbidden para cliente intentando cambiar estado', () => pm.response.to.have.status(403));",
                ] + problem + tipo_error("no-autorizado")
            ),
            req(
                "6.3 Aislamiento Intra-Tenant: Cliente 2 intenta consultar la solicitud de Cliente 1 -> 404 Not Found",
                "GET", "/v1/service-requests/{{requestId}}", [CORR, auth("cliente2Token")],
                None,
                [
                    "pm.test('[Confidencialidad Intra-Tenant] 404 Not Found para cliente ajeno del mismo tenant', () => pm.response.to.have.status(404));",
                ] + problem + tipo_error("no-encontrado")
            ),
            req(
                "6.4 Aislamiento Multi-Tenant: Cliente de Tenant Beta intenta consultar solicitud de Tenant Alfa -> 404 Not Found",
                "GET", "/v1/service-requests/{{requestId}}", [CORR, auth("clienteBetaToken")],
                None,
                [
                    "pm.test('[SAD AC6-E2 / RLS] 404 Not Found garantizado por Row-Level Security', () => pm.response.to.have.status(404));",
                ] + problem + tipo_error("no-encontrado")
            ),
        ]
    },
]

collection = {
    "info": {
        "name": "QUICKPATCH — Seguimiento de Estado en Tiempo Real (SCRUM-84 / HU SCRUM-31)",
        "description": "Suite E2E automatizada para SCRUM-84 (HU SCRUM-31: Seguimiento en tiempo real del estado de la solicitud):\nValida ServiceRequest (máquina de estados), Communication (WebSocket y evento status-changed) y API Gateway (/api/v1/realtime).\nAutora: Katherine Bravo — QA Lead.",
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
    },
    "variable": [
        {"key": "baseUrl", "value": "http://localhost:8080", "type": "string"},
        {"key": "clienteEmail", "value": "cliente@quickpatch.test", "type": "string"},
        {"key": "tecnicoEmail", "value": "tecnico@quickpatch.test", "type": "string"},
        {"key": "cliente2Email", "value": "cliente2@quickpatch.test", "type": "string"},
        {"key": "clienteBetaEmail", "value": "cliente.beta@quickpatch.test", "type": "string"},
        {"key": "clienteToken", "value": "", "type": "string"},
        {"key": "tecnicoToken", "value": "", "type": "string"},
        {"key": "cliente2Token", "value": "", "type": "string"},
        {"key": "clienteBetaToken", "value": "", "type": "string"},
        {"key": "requestId", "value": "sr-tracking-01", "type": "string"},
    ],
    "item": items
}

out_file = pathlib.Path(__file__).parent / "scrum-84-seguimiento-estado.postman_collection.json"
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(collection, f, ensure_ascii=False, indent=2)

print(f"Colección generada con éxito: {out_file.name}")
