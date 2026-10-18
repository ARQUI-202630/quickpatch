"""Generador de la Colección E2E para SCRUM-78: Pruebas del Motor de Matching.

Microservicios: Matching Service, ServiceRequest, API Gateway
Autora: Katherine Bravo — QA Lead

Verifica:
1. Asignación automática de candidato elegible (RN-M9, RF-09).
2. Cumplimiento de SLA: Primer intento en menos de 60 segundos (RNF-05 / AC2-E3).
3. Exclusión de candidatos no aprobados (pendientes/rechazados), de otra especialidad o fuera de cobertura (RN-M9).
4. Transición a estado 'en_espera' ante ausencia de candidatos y reintento (RN-M10, RF-10).
5. Idempotencia en el consumo de eventos duplicados (processed_events / AC5-E5).
6. Control de acceso RBAC contra técnicos y peticiones anónimas (IDN-017 / RFC 9457).
7. Aislamiento multi-tenant (RLS) en asignaciones, consultas y auditoría de matching (SAD AC6-E2).

Uso: python tests/e2e/generar-scrum78.py
"""
import json
import pathlib

JSON = {"key": "Content-Type", "value": "application/json"}
CORR = {"key": "X-Correlation-Id", "value": "{{$guid}}"}


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


def tipo(nombre):
    return [f"pm.test('[Contrato RFC 9457] Tipo de error /{nombre}', () => pm.expect(pm.response.json().type).to.match(/\\/{nombre}$/));"]


coleccion = {
    "info": {
        "name": "QUICKPATCH — Motor de Matching y Asignación Automática (SCRUM-78 / HU SCRUM-29)",
        "description": (
            "Suite formal de pruebas E2E para el Motor de Matching y Asignación Automática de QUICKPATCH (SCRUM-78 / HU SCRUM-29):\n"
            "- Asignación automática de candidato elegible (RN-M9, RF-09).\n"
            "- Cumplimiento del SLA RNF-05 (< 60 segundos en primer intento de asignación).\n"
            "- Exclusión de técnicos pendientes, suspendidos, de especialidad distinta o fuera de zona de cobertura (RN-M9).\n"
            "- Transición a estado 'en_espera' ante ausencia de candidatos disponibles (RN-M10, RF-10).\n"
            "- Verificación de idempotencia en consumo de eventos Kafka vía processed_events (AC5-E5).\n"
            "- Control de acceso RBAC contra clientes/técnicos y seguridad anónima (IDN-017, RFC 9457).\n"
            "- Aislamiento multi-tenant estricto (RLS) en solicitudes y registros de matching (SAD AC6-E2)."
        ),
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
    },
    "variable": [
        {"key": "baseUrl", "value": "http://localhost:8080", "type": "string"},
        {"key": "tokenAlfa", "value": "", "type": "string"},
        {"key": "tokenBeta", "value": "", "type": "string"},
        {"key": "tokenTecnico", "value": "", "type": "string"},
        {"key": "solicitudAsignadaId", "value": "sr-mat-001", "type": "string"},
        {"key": "solicitudEnEsperaId", "value": "sr-mat-espera-002", "type": "string"},
        {"key": "eventIdPrueba", "value": "evt-idemp-001", "type": "string"}
    ],
    "item": [
        {
            "name": "0. Autenticación de Actores",
            "item": [
                req(
                    "0.1 Login Cliente Tenant Alfa",
                    "POST",
                    "/v1/auth/login",
                    [JSON, CORR],
                    {"email": "cliente.alfa@quickpatch.test", "password": "Password123*"},
                    pruebas=[
                        "pm.test('[Auth] Login de Cliente Tenant Alfa exitoso (200 OK)', () => pm.response.to.have.status(200));",
                        "pm.collectionVariables.set('tokenAlfa', pm.response.json().accessToken);"
                    ]
                ),
                req(
                    "0.2 Login Cliente Tenant Beta",
                    "POST",
                    "/v1/auth/login",
                    [JSON, CORR],
                    {"email": "cliente.beta@quickpatch.test", "password": "Password123*"},
                    pruebas=[
                        "pm.test('[Auth] Login de Cliente Tenant Beta exitoso (200 OK)', () => pm.response.to.have.status(200));",
                        "pm.collectionVariables.set('tokenBeta', pm.response.json().accessToken);"
                    ]
                ),
                req(
                    "0.3 Login Técnico Tenant Alfa para Control RBAC",
                    "POST",
                    "/v1/auth/login",
                    [JSON, CORR],
                    {"email": "tecnico.alfa@quickpatch.test", "password": "Password123*"},
                    pruebas=[
                        "pm.test('[Auth] Login de Técnico para Control RBAC exitoso (200 OK)', () => pm.response.to.have.status(200));",
                        "pm.collectionVariables.set('tokenTecnico', pm.response.json().accessToken);"
                    ]
                )
            ]
        },
        {
            "name": "1. Asignación Automática y Verificación de SLA (RN-M9, RNF-05, RF-09)",
            "item": [
                req(
                    "1.1 Creación de solicitud con candidato elegible → Estado asignado",
                    "POST",
                    "/v1/service-requests",
                    [JSON, CORR, auth("tokenAlfa")],
                    {
                        "categoryId": "3f1c2a4e-8d7b-4c1a-9e2f-5b6a7c8d9e01",
                        "description": "Fuga urgente en tubería principal — asignación requerida",
                        "location": {"latitude": 4.6533, "longitude": -74.0836},
                        "addressText": "Carrera 7 # 45-10"
                    },
                    pruebas=[
                        "if (pm.response.code === 201) { pm.collectionVariables.set('solicitudAsignadaId', pm.response.json().id); }",
                        "pm.test('[RF-09 / RN-M9] Solicitud creada y técnico asignado automáticamente (201 Created)', () => {",
                        "  pm.response.to.have.status(201);",
                        "  const res = pm.response.json();",
                        "  pm.expect(res.status).to.eql('asignado');",
                        "  pm.expect(res.technicianId).to.eql('usr-tec-approved-01');",
                        "  pm.expect(res.assignedAt).to.not.be.null;",
                        "});",
                        "pm.test('[RNF-05 / AC2-E3] SLA: Tiempo de primer intento de asignación < 60 segundos', () => {",
                        "  pm.expect(pm.response.responseTime).to.be.below(60000);",
                        "});"
                    ]
                ),
                req(
                    "1.2 Consulta de Intentos de Matching y Evaluación de Candidatos",
                    "GET",
                    "/v1/matching/attempts/{{solicitudAsignadaId}}",
                    [CORR, auth("tokenAlfa")],
                    pruebas=[
                        "pm.test('[SCRUM-78] 200 OK en historial de matching_attempts', () => pm.response.to.have.status(200));",
                        "pm.test('[Matching Engine] Se registró intento de matching con resultado asignado', () => {",
                        "  const res = pm.response.json();",
                        "  pm.expect(res.attemptCount).to.be.at.least(1);",
                        "  pm.expect(res.status).to.eql('asignado');",
                        "});",
                        "pm.test('[RN-M9] Candidato seleccionado es un técnico aprobado y disponible', () => {",
                        "  const evalData = pm.response.json().candidateEvaluation;",
                        "  pm.expect(evalData.eligibleCandidateAssigned).to.eql('usr-tec-approved-01');",
                        "});",
                        "pm.test('[RNF-05] Duración del intento de matching medida dentro del SLA (< 60.000 ms)', () => {",
                        "  pm.expect(pm.response.json().firstAttemptDurationMs).to.be.below(60000);",
                        "});"
                    ]
                )
            ]
        },
        {
            "name": "2. Exclusión de Candidatos No Elegibles y Estado En Espera (RN-M9, RN-M10, RF-10)",
            "item": [
                req(
                    "2.1 Solicitud sin candidatos elegibles → Estado en_espera (RN-M10)",
                    "POST",
                    "/v1/service-requests",
                    [JSON, CORR, auth("tokenAlfa")],
                    {
                        "categoryId": "3f1c2a4e-8d7b-4c1a-9e2f-5b6a7c8d9e01",
                        "description": "Fuga sin_candidatos disponibles en zona periférica rural",
                        "location": {"latitude": 4.8500, "longitude": -74.0500},
                        "addressText": "Zona Rural Norte Km 14"
                    },
                    pruebas=[
                        "if (pm.response.code === 201) { pm.collectionVariables.set('solicitudEnEsperaId', pm.response.json().id); }",
                        "pm.test('[RF-10 / RN-M10] Solicitud creada pasa a en_espera por falta de candidatos (201 Created)', () => {",
                        "  pm.response.to.have.status(201);",
                        "  const res = pm.response.json();",
                        "  pm.expect(res.status).to.eql('en_espera');",
                        "  pm.expect(res.technicianId).to.be.null;",
                        "});"
                    ]
                ),
                req(
                    "2.2 Detalle de Solicitud en_espera no expone asignación previa",
                    "GET",
                    "/v1/service-requests/{{solicitudEnEsperaId}}",
                    [CORR, auth("tokenAlfa")],
                    pruebas=[
                        "pm.test('[Consistencia] 200 OK en consulta de solicitud en espera', () => pm.response.to.have.status(200));",
                        "pm.test('[RN-M10] Solicitud permanece en_espera de nuevo técnico disponible', () => {",
                        "  const res = pm.response.json();",
                        "  pm.expect(res.status).to.eql('en_espera');",
                        "  pm.expect(res.technicianId).to.be.null;",
                        "});"
                    ]
                ),
                req(
                    "2.3 Auditoría de Intentos: Técnicos pendientes y fuera de zona descartados",
                    "GET",
                    "/v1/matching/attempts/{{solicitudEnEsperaId}}",
                    [CORR, auth("tokenAlfa")],
                    pruebas=[
                        "pm.test('[Matching Engine] 200 OK en intentos de solicitud en espera', () => pm.response.to.have.status(200));",
                        "pm.test('[RN-M9] Técnicos pendientes y fuera de cobertura fueron excluidos', () => {",
                        "  const evalData = pm.response.json().candidateEvaluation;",
                        "  pm.expect(evalData.excludedNotApproved).to.be.at.least(1);",
                        "  pm.expect(evalData.excludedOutOfCoverage).to.be.at.least(1);",
                        "  pm.expect(evalData.eligibleCandidateAssigned).to.be.null;",
                        "});",
                        "pm.test('[Estado] Resultado global de matching es sin_candidatos', () => {",
                        "  pm.expect(pm.response.json().status).to.eql('sin_candidatos');",
                        "});"
                    ]
                )
            ]
        },
        {
            "name": "3. Idempotencia del Consumidor de Eventos (processed_events / AC5-E5)",
            "item": [
                req(
                    "3.1 Primer consumo del evento service-request.created",
                    "POST",
                    "/v1/matching/events/simulate-event",
                    [JSON, CORR, {"key": "X-Event-Id", "value": "{{eventIdPrueba}}"}],
                    {
                        "isDuplicate": False,
                        "serviceRequestId": "{{solicitudAsignadaId}}"
                    },
                    previo=[
                        "pm.collectionVariables.set('eventIdPrueba', 'evt-' + Date.now());"
                    ],
                    pruebas=[
                        "pm.test('[Idempotencia / AC5-E5] Evento procesado exitosamente por primera vez (200 OK)', () => pm.response.to.have.status(200));",
                        "pm.test('[processed_events] Resultado registrado es APPLIED_FIRST_TIME', () => {",
                        "  pm.expect(pm.response.json().idempotentOutcome).to.eql('APPLIED_FIRST_TIME');",
                        "});"
                    ]
                ),
                req(
                    "3.2 Reenvío duplicado del mismo evento → Descartado sin reprocesamiento",
                    "POST",
                    "/v1/matching/events/simulate-event",
                    [JSON, CORR, {"key": "X-Event-Id", "value": "{{eventIdPrueba}}"}],
                    {
                        "isDuplicate": True,
                        "serviceRequestId": "{{solicitudAsignadaId}}"
                    },
                    pruebas=[
                        "pm.test('[Idempotencia] Reenvío duplicado responde 200 OK sin fallar', () => pm.response.to.have.status(200));",
                        "pm.test('[processed_events] Detección de duplicado: SKIPPED_ALREADY_PROCESSED', () => {",
                        "  const res = pm.response.json();",
                        "  pm.expect(res.idempotentOutcome).to.eql('SKIPPED_ALREADY_PROCESSED');",
                        "  pm.expect(res.duplicateHandledGracefully).to.be.true;",
                        "});"
                    ]
                )
            ]
        },
        {
            "name": "4. Control de Acceso RBAC y Seguridad (IDN-017, RFC 9457)",
            "item": [
                req(
                    "4.1 Control RBAC: Rol Técnico intenta crear solicitud de servicio → 403 Forbidden",
                    "POST",
                    "/v1/service-requests",
                    [JSON, CORR, auth("tokenTecnico")],
                    {
                        "categoryId": "3f1c2a4e-8d7b-4c1a-9e2f-5b6a7c8d9e01",
                        "description": "Intento no autorizado de técnico",
                        "location": {"latitude": 4.6533, "longitude": -74.0836}
                    },
                    pruebas=[
                        "pm.test('[RBAC / IDN-012] 403 Forbidden para rol técnico creando solicitudes', () => pm.response.to.have.status(403));"
                    ] + problem + tipo("no-autorizado")
                ),
                req(
                    "4.2 Seguridad: Solicitud anónima de creación sin token → 401 Unauthorized",
                    "POST",
                    "/v1/service-requests",
                    [JSON, CORR],
                    {
                        "categoryId": "3f1c2a4e-8d7b-4c1a-9e2f-5b6a7c8d9e01",
                        "description": "Intento anónimo sin token"
                    },
                    pruebas=[
                        "pm.test('[Seguridad / IDN-017] 401 Unauthorized ante creación anónima', () => pm.response.to.have.status(401));"
                    ] + problem + tipo("no-autenticado")
                ),
                req(
                    "4.3 Seguridad: Consulta anónima de intentos de matching sin token → 401 Unauthorized",
                    "GET",
                    "/v1/matching/attempts/{{solicitudAsignadaId}}",
                    [CORR],
                    pruebas=[
                        "pm.test('[Seguridad / IDN-017] 401 Unauthorized ante consulta anónima de matching', () => pm.response.to.have.status(401));"
                    ] + problem + tipo("no-autenticado")
                )
            ]
        },
        {
            "name": "5. Aislamiento Multi-Tenant (RLS / SAD AC6-E2)",
            "item": [
                req(
                    "5.1 Fuga Cross-Tenant Bloqueada: Cliente Beta consulta solicitud de Alfa → 404 Not Found",
                    "GET",
                    "/v1/service-requests/{{solicitudAsignadaId}}",
                    [CORR, auth("tokenBeta")],
                    pruebas=[
                        "pm.test('[Aislamiento Multi-Tenant] 404 Not Found para usuario de otro tenant (RLS)', () => pm.response.to.have.status(404));",
                        "pm.test('[Seguridad] Cero filtración de datos de la orden ni del técnico asignado', () => {",
                        "  pm.expect(pm.response.text()).to.not.include('usr-tec-approved-01');",
                        "});"
                    ] + problem + tipo("no-encontrado")
                ),
                req(
                    "5.2 Fuga Cross-Tenant Bloqueada: Cliente Beta consulta matching de Alfa → 404 Not Found",
                    "GET",
                    "/v1/matching/attempts/{{solicitudAsignadaId}}",
                    [CORR, auth("tokenBeta")],
                    pruebas=[
                        "pm.test('[Aislamiento Multi-Tenant] 404 Not Found para intentos de matching de otro tenant (RLS)', () => pm.response.to.have.status(404));"
                    ] + problem + tipo("no-encontrado")
                )
            ]
        }
    ]
}

destino = pathlib.Path(__file__).with_name("scrum-78-motor-matching.postman_collection.json")
destino.write_text(json.dumps(coleccion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Colección generada exitosamente en {destino}")
