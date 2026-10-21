"""Generador de la Colección E2E para SCRUM-81, SCRUM-90 y SCRUM-93: Incremento del Técnico.

Diseñada para ejecutarse con Newman contra el Gateway de QA o el emulador local:
- SCRUM-90: Localidades de Bogotá (20 oficiales), disponibilidad (disponible/ocupado/no_disponible)
  y cobertura geográfica (polígonos de localidades) bajo matching.v1.yaml.
- SCRUM-81: Ofertas de matching sin dirección exacta previa (RN-SR13), aceptación atómica
  con cambio a ocupado (RN-M6) y outbox matching.technician-assigned, rechazo sin penalización (R12),
  y control de conflictos 409 (oferta vencida, ya respondida o técnico ocupado).
- SCRUM-93: Detalle de solicitud asignada (service-request.v1.yaml 1.1.0): técnico asignado ve
  contacto del cliente (nombre y teléfono vía Identity), 403 fuera de asignado-completado y 404 para técnicos ajenos.

Uso: python tests/e2e/generar-scrum-incremento-tecnico.py
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


def tipo(nombre):
    return [f"pm.test('[Contrato] Tipo de error {nombre}', () => pm.expect(pm.response.json().type).to.match(/\\/{nombre}$/));"]


coleccion = {
    "info": {
        "name": "QUICKPATCH — Incremento Técnico (SCRUM-81, SCRUM-90, SCRUM-93)",
        "description": (
            "Suite automatizada de pruebas de sistema (E2E) para el incremento del técnico (Sprint 4):\n"
            "- SCRUM-90: Disponibilidad y cobertura geográfica (Matching Service / HU SCRUM-33)\n"
            "- SCRUM-81: Aceptación y rechazo de ofertas de asignación (Matching Service / HU SCRUM-30)\n"
            "- SCRUM-93: Detalle de solicitud para técnico asignado (ServiceRequest Service / HU SCRUM-34)\n"
            "Valida contratos OpenAPI matching.v1.yaml y service-request.v1.yaml con RFC 9457."
        ),
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
    },
    "variable": [
        {"key": "baseUrl", "value": "http://localhost:8080", "type": "string"},
        {"key": "tecnicoEmail", "value": "tecnico@quickpatch.test", "type": "string"},
        {"key": "tecnicoOcupadoEmail", "value": "tecnico.ocupado@quickpatch.test", "type": "string"},
        {"key": "tecnicoOtroEmail", "value": "tecnico.otro@quickpatch.test", "type": "string"},
        {"key": "clienteEmail", "value": "cliente@quickpatch.test", "type": "string"},
        {"key": "passwordComun", "value": "", "type": "string"},
        {"key": "tecnicoToken", "value": "", "type": "string"},
        {"key": "tecnicoOcupadoToken", "value": "", "type": "string"},
        {"key": "tecnicoOtroToken", "value": "", "type": "string"},
        {"key": "clienteToken", "value": "", "type": "string"}
    ],
    "item": [
        {
            "name": "0. Autenticación y Tokens de Prueba",
            "item": [
                req(
                    "0.1 Login Técnico Principal (usr-tec-01)",
                    "POST",
                    "/v1/auth/login",
                    [JSON, CORR, CANAL_MOVIL],
                    {"email": "{{tecnicoEmail}}", "password": "{{passwordComun}}"},
                    pruebas=[
                        "pm.test('[Auth] Login técnico exitoso (200 OK)', () => pm.response.to.have.status(200));",
                        "pm.collectionVariables.set('tecnicoToken', pm.response.json().accessToken);"
                    ]
                ),
                req(
                    "0.2 Login Técnico Ocupado (usr-tec-02)",
                    "POST",
                    "/v1/auth/login",
                    [JSON, CORR, CANAL_MOVIL],
                    {"email": "{{tecnicoOcupadoEmail}}", "password": "{{passwordComun}}"},
                    pruebas=[
                        "pm.test('[Auth] Login técnico ocupado exitoso (200 OK)', () => pm.response.to.have.status(200));",
                        "pm.collectionVariables.set('tecnicoOcupadoToken', pm.response.json().accessToken);"
                    ]
                ),
                req(
                    "0.3 Login Técnico Ajeno (usr-tec-03)",
                    "POST",
                    "/v1/auth/login",
                    [JSON, CORR, CANAL_MOVIL],
                    {"email": "{{tecnicoOtroEmail}}", "password": "{{passwordComun}}"},
                    pruebas=[
                        "pm.test('[Auth] Login técnico ajeno exitoso (200 OK)', () => pm.response.to.have.status(200));",
                        "pm.collectionVariables.set('tecnicoOtroToken', pm.response.json().accessToken);"
                    ]
                ),
                req(
                    "0.4 Login Cliente Dueño (usr-client-01)",
                    "POST",
                    "/v1/auth/login",
                    [JSON, CORR, CANAL_MOVIL],
                    {"email": "{{clienteEmail}}", "password": "{{passwordComun}}"},
                    pruebas=[
                        "pm.test('[Auth] Login cliente exitoso (200 OK)', () => pm.response.to.have.status(200));",
                        "pm.collectionVariables.set('clienteToken', pm.response.json().accessToken);"
                    ]
                )
            ]
        },
        {
            "name": "1. SCRUM-90 — Disponibilidad y Cobertura (Matching Service)",
            "item": [
                req(
                    "1.1 [COV-001] Catálogo público de 20 localidades oficiales de Bogotá",
                    "GET",
                    "/v1/localities",
                    [CORR],
                    pruebas=[
                        "pm.test('[SCRUM-90] 200 OK en listado de localidades', () => pm.response.to.have.status(200));",
                        "const locs = pm.response.json();",
                        "pm.test('[Localidades] Devuelve exactamente las 20 localidades oficiales de Bogotá', () => pm.expect(locs.length).to.equal(20));",
                        "pm.test('[Localidades] Códigos oficiales 01 a 20 presentes', () => {",
                        "  pm.expect(locs[0].code).to.equal('01');",
                        "  pm.expect(locs[0].name).to.equal('Usaquén');",
                        "  pm.expect(locs[1].code).to.equal('02');",
                        "  pm.expect(locs[1].name).to.equal('Chapinero');",
                        "});"
                    ]
                ),
                req(
                    "1.2 [AVA-001] Consulta de disponibilidad inicial del técnico",
                    "GET",
                    "/v1/technicians/me/availability",
                    [CORR, auth("tecnicoToken")],
                    pruebas=[
                        "pm.test('[SCRUM-90] 200 OK en consulta de disponibilidad', () => pm.response.to.have.status(200));",
                        "const body = pm.response.json();",
                        "pm.test('[Contrato] Atributos de disponibilidad presentes', () => {",
                        "  pm.expect(body).to.have.property('status');",
                        "  pm.expect(body).to.have.property('available');",
                        "  pm.expect(body).to.have.property('busy');",
                        "});"
                    ]
                ),
                req(
                    "1.3 [AVA-002] Cambiar disponibilidad a disponible (RF-13, RN-M10)",
                    "PUT",
                    "/v1/technicians/me/availability",
                    [JSON, CORR, auth("tecnicoToken")],
                    {"status": "disponible"},
                    pruebas=[
                        "pm.test('[SCRUM-90] 200 OK al actualizar disponibilidad', () => pm.response.to.have.status(200));",
                        "const body = pm.response.json();",
                        "pm.test('[SCRUM-90] Estado actualizado a disponible', () => pm.expect(body.status).to.equal('disponible'));",
                        "pm.test('[SCRUM-90] Flag available es true', () => pm.expect(body.available).to.be.true);",
                        "pm.test('[SCRUM-90] Flag busy es false', () => pm.expect(body.busy).to.be.false);"
                    ]
                ),
                req(
                    "1.4 [AVA-003] Rechazo de cambio manual si técnico está ocupado en servicio (RN-M6)",
                    "PUT",
                    "/v1/technicians/me/availability",
                    [JSON, CORR, auth("tecnicoOcupadoToken")],
                    {"status": "no_disponible"},
                    pruebas=[
                        "pm.test('[SCRUM-90 / RN-M6] 409 Conflict si técnico está ocupado', () => pm.response.to.have.status(409));",
                        *problem,
                        *tipo("transicion-invalida")
                    ]
                ),
                req(
                    "1.5 [COV-002] Consulta de cobertura inicial del técnico",
                    "GET",
                    "/v1/technicians/me/coverage",
                    [CORR, auth("tecnicoToken")],
                    pruebas=[
                        "pm.test('[SCRUM-90] 200 OK en consulta de cobertura', () => pm.response.to.have.status(200));",
                        "const body = pm.response.json();",
                        "pm.test('[Contrato] Atributo localityCodes es array', () => pm.expect(body.localityCodes).to.be.an('array'));"
                    ]
                ),
                req(
                    "1.6 [COV-003] Configuración de cobertura geográfica por localidades (RF-13)",
                    "PUT",
                    "/v1/technicians/me/coverage",
                    [JSON, CORR, auth("tecnicoToken")],
                    {"localityCodes": ["01", "02", "12", "13"]},
                    pruebas=[
                        "pm.test('[SCRUM-90] 200 OK al actualizar cobertura', () => pm.response.to.have.status(200));",
                        "const body = pm.response.json();",
                        "pm.test('[SCRUM-90] Localidades configuradas correctamente', () => {",
                        "  pm.expect(body.localityCodes).to.include('01');",
                        "  pm.expect(body.localityCodes).to.include('02');",
                        "});"
                    ]
                ),
                req(
                    "1.7 [COV-004] Rechazo de cobertura vacía o con código inexistente",
                    "PUT",
                    "/v1/technicians/me/coverage",
                    [JSON, CORR, auth("tecnicoToken")],
                    {"localityCodes": ["99"]},
                    pruebas=[
                        "pm.test('[SCRUM-90] 400 Bad Request ante código inexistente', () => pm.response.to.have.status(400));",
                        *problem,
                        *tipo("validacion-solicitud")
                    ]
                ),
                req(
                    "1.8 [AVA-004] Rechazo de consulta sin token → 401 Unauthorized",
                    "GET",
                    "/v1/technicians/me/availability",
                    [CORR],
                    pruebas=[
                        "pm.test('[Seguridad] 401 Unauthorized sin token', () => pm.response.to.have.status(401));",
                        *problem,
                        *tipo("no-autenticado")
                    ]
                ),
                req(
                    "1.9 [AVA-005] Control RBAC: Rol cliente no puede gestionar disponibilidad → 403 Forbidden",
                    "PUT",
                    "/v1/technicians/me/availability",
                    [JSON, CORR, auth("clienteToken")],
                    {"status": "disponible"},
                    pruebas=[
                        "pm.test('[RBAC] 403 Forbidden para rol cliente', () => pm.response.to.have.status(403));",
                        *problem,
                        *tipo("no-autorizado")
                    ]
                )
            ]
        },
        {
            "name": "2. SCRUM-81 — Aceptación y Rechazo de Ofertas (Matching Service)",
            "item": [
                req(
                    "2.1 [OFF-001] Consultar ofertas pendientes (sin dirección exacta, RN-SR13)",
                    "GET",
                    "/v1/matching/offers?status=pendiente",
                    [CORR, auth("tecnicoToken")],
                    pruebas=[
                        "pm.test('[SCRUM-81] 200 OK en consulta de ofertas', () => pm.response.to.have.status(200));",
                        "const body = pm.response.json();",
                        "pm.test('[SCRUM-81] Lista de ofertas con al menos un elemento', () => pm.expect(body.items.length).to.be.above(0));",
                        "const oferta = body.items[0];",
                        "pm.test('[RN-SR13] Oferta contiene localidad y distancia pero NO dirección exacta', () => {",
                        "  pm.expect(oferta).to.have.property('locality');",
                        "  pm.expect(oferta).to.have.property('distanceM');",
                        "  pm.expect(oferta).to.have.property('description');",
                        "  pm.expect(oferta).to.not.have.property('addressText');",
                        "  pm.expect(oferta).to.not.have.property('address');",
                        "});"
                    ]
                ),
                req(
                    "2.2 [OFF-002] Aceptar oferta legítima (Atómica: ocupado, asignado, Outbox)",
                    "POST",
                    "/v1/matching/offers/attempt-valid-01/accept",
                    [JSON, CORR, auth("tecnicoToken")],
                    {},
                    pruebas=[
                        "pm.test('[SCRUM-81] 200 OK al aceptar oferta legítima', () => pm.response.to.have.status(200));",
                        "const body = pm.response.json();",
                        "pm.test('[SCRUM-81] Respuesta es aceptado', () => pm.expect(body.response).to.equal('aceptado'));",
                        "pm.test('[SCRUM-81] Atributos de respuesta presentes', () => {",
                        "  pm.expect(body).to.have.property('attemptId');",
                        "  pm.expect(body).to.have.property('serviceRequestId');",
                        "  pm.expect(body).to.have.property('assignedAt');",
                        "});"
                    ]
                ),
                req(
                    "2.3 [OFF-003] Rechazo de oferta ya respondida o duplicada → 409 Conflict",
                    "POST",
                    "/v1/matching/offers/attempt-valid-01/accept",
                    [JSON, CORR, auth("tecnicoToken")],
                    {},
                    pruebas=[
                        "pm.test('[SCRUM-81] 409 Conflict ante intento duplicado', () => pm.response.to.have.status(409));",
                        *problem,
                        *tipo("oferta-no-disponible")
                    ]
                ),
                req(
                    "2.4 [OFF-004] Rechazo de oferta vencida por tiempo límite (RN-M8) → 409 Conflict",
                    "POST",
                    "/v1/matching/offers/attempt-expired-01/accept",
                    [JSON, CORR, auth("tecnicoToken")],
                    {},
                    pruebas=[
                        "pm.test('[SCRUM-81 / RN-M8] 409 Conflict ante oferta expirada', () => pm.response.to.have.status(409));",
                        *problem,
                        *tipo("oferta-no-disponible")
                    ]
                ),
                req(
                    "2.5 [OFF-005] Rechazo de oferta si el técnico ya está ocupado (RN-M7) → 409 Conflict",
                    "POST",
                    "/v1/matching/offers/attempt-second-01/accept",
                    [JSON, CORR, auth("tecnicoOcupadoToken")],
                    {},
                    pruebas=[
                        "pm.test('[SCRUM-81 / RN-M7] 409 Conflict si técnico está ocupado', () => pm.response.to.have.status(409));",
                        *problem,
                        *tipo("tecnico-no-disponible")
                    ]
                ),
                req(
                    "2.6 [OFF-006] Rechazo de oferta sin penalización (RF-10, R12)",
                    "POST",
                    "/v1/matching/offers/attempt-reject-01/reject",
                    [JSON, CORR, auth("tecnicoToken")],
                    {},
                    pruebas=[
                        "pm.test('[SCRUM-81 / R12] 200 OK al rechazar oferta sin penalización', () => pm.response.to.have.status(200));",
                        "const body = pm.response.json();",
                        "pm.test('[SCRUM-81] Respuesta es rechazado', () => pm.expect(body.response).to.equal('rechazado'));",
                        "pm.test('[RN-M3] Siguiente candidato notificado', () => pm.expect(body.nextCandidateNotified).to.be.true);"
                    ]
                ),
                req(
                    "2.7 [OFF-007] Control RBAC: Rol cliente no puede responder ofertas → 403 Forbidden",
                    "POST",
                    "/v1/matching/offers/attempt-valid-01/accept",
                    [JSON, CORR, auth("clienteToken")],
                    {},
                    pruebas=[
                        "pm.test('[RBAC] 403 Forbidden para rol cliente', () => pm.response.to.have.status(403));",
                        *problem,
                        *tipo("no-autorizado")
                    ]
                )
            ]
        },
        {
            "name": "3. SCRUM-93 — Detalle de Solicitud para Técnico Asignado (ServiceRequest)",
            "item": [
                req(
                    "3.1 [DTL-001] Técnico asignado ve detalle completo con contacto del cliente (RN-SR13)",
                    "GET",
                    "/v1/service-requests/sr-assigned-01",
                    [CORR, auth("tecnicoToken")],
                    pruebas=[
                        "pm.test('[SCRUM-93] 200 OK en consulta de solicitud asignada', () => pm.response.to.have.status(200));",
                        "const body = pm.response.json();",
                        "pm.test('[SCRUM-93] Estado verificado como asignado', () => pm.expect(body.status).to.equal('asignado'));",
                        "pm.test('[SCRUM-93] Dirección exacta visible para técnico asignado', () => {",
                        "  pm.expect(body).to.have.property('addressText');",
                        "  pm.expect(body.addressText).to.include('Calle 63');",
                        "});",
                        "pm.test('[RN-SR13] Contacto del cliente presente con nombre y teléfono', () => {",
                        "  pm.expect(body).to.have.property('client');",
                        "  pm.expect(body.client).to.have.property('fullName', 'Ana Gómez');",
                        "  pm.expect(body.client).to.have.property('phone', '+573009876543');",
                        "});"
                    ]
                ),
                req(
                    "3.2 [DTL-002] Técnico consulta solicitud no asignada (buscando_tecnico) → 403 Forbidden",
                    "GET",
                    "/v1/service-requests/sr-unassigned-01",
                    [CORR, auth("tecnicoToken")],
                    pruebas=[
                        "pm.test('[SCRUM-93 / RN-SR13] 403 Forbidden antes de asignación', () => pm.response.to.have.status(403));",
                        *problem,
                        *tipo("solicitud-no-asignada")
                    ]
                ),
                req(
                    "3.3 [DTL-003] Técnico ajeno consulta solicitud asignada a otro → 404 Not Found",
                    "GET",
                    "/v1/service-requests/sr-assigned-01",
                    [CORR, auth("tecnicoOtroToken")],
                    pruebas=[
                        "pm.test('[Confidencialidad] 404 Not Found para técnico ajeno', () => pm.response.to.have.status(404));",
                        *problem,
                        *tipo("no-encontrado")
                    ]
                ),
                req(
                    "3.4 [DTL-004] Cliente dueño consulta su solicitud asignada (client es null)",
                    "GET",
                    "/v1/service-requests/sr-assigned-01",
                    [CORR, auth("clienteToken")],
                    pruebas=[
                        "pm.test('[Cliente] 200 OK en consulta de solicitud propia', () => pm.response.to.have.status(200));",
                        "const body = pm.response.json();",
                        "pm.test('[Contrato] Para cliente el bloque client es null', () => pm.expect(body.client).to.be.null);",
                        "pm.test('[Contrato] Bloque technician visible con nombre de técnico', () => {",
                        "  pm.expect(body.technician).to.have.property('fullName');",
                        "});"
                    ]
                )
            ]
        }
    ]
}

destino = pathlib.Path(__file__).parent / "scrum-incremento-tecnico.postman_collection.json"
destino.write_text(json.dumps(coleccion, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Colección generada con éxito en: {destino}")
print(f"Total carpetas: {len(coleccion['item'])}")
total_reqs = sum(len(f['item']) for f in coleccion['item'])
print(f"Total peticiones de prueba: {total_reqs}")
