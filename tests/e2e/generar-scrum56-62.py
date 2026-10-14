"""Generador de la Colección E2E para SCRUM-56 y SCRUM-62.
- SCRUM-56: Pruebas de Registro de Técnico / Proveedor (Identity).
- SCRUM-62: Pruebas de Aislamiento Lógico de Datos por Tenant (Multi-tenant RLS).

Uso: python tests/e2e/generar-scrum56-62.py
"""
import json
import pathlib

JSON = {"key": "Content-Type", "value": "application/json"}
CORR = {"key": "X-Correlation-Id", "value": "{{$guid}}"}
CANAL = {"key": "X-Channel-Id", "value": "quickpatch-mobile"}


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
        "name": "QUICKPATCH — Registro de Técnico (SCRUM-56) y Aislamiento por Tenant (SCRUM-62)",
        "description": (
            "Suite automatizada de pruebas del Sprint 4 para verificar:\n"
            "1. SCRUM-56: Registro legítimo de técnico, validación de unicidad de documento (409) y correo (409), "
            "validación de esquema (400), consulta de perfil propio (/v1/users/me con verificationStatus: pendiente) "
            "y restricción RBAC para creación de solicitudes (403).\n"
            "2. SCRUM-62: Aislamiento estricto multi-tenant (RLS) en lectura de solicitudes cruzadas (404 Not Found), "
            "aislamiento de catálogo entre Tenant Alfa y Tenant Beta, y acceso positivo para el tenant propietario.\n"
            "Variables: baseUrl (https://qa.quickpatch.internal o http://localhost:8080 en local)."
        ),
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
    },
    "variable": [
        {"key": "baseUrl", "value": "http://localhost:8080", "type": "string"},
        {"key": "documento", "value": "CC-1020304050", "type": "string"},
        {"key": "correoTecnico", "value": "tecnico.qa@quickpatch.test", "type": "string"},
        {"key": "tecnicoToken", "value": "", "type": "string"},
        {"key": "tokenAlfa", "value": "", "type": "string"},
        {"key": "tokenBeta", "value": "", "type": "string"},
        {"key": "solicitudAlfaId", "value": "sr-qa-001", "type": "string"}
    ],
    "item": [
        {
            "name": "1. SCRUM-56 — Registro y Perfil de Técnico (Identity)",
            "item": [
                req(
                    "1.1 Registro exitoso de técnico (verificationStatus: pendiente)",
                    "POST",
                    "/v1/auth/register/technician",
                    [JSON, CORR, CANAL],
                    {
                        "email": "{{correoTecnico}}",
                        "password": "PasswordTecnico123*",
                        "fullName": "Carlos Alberto Técnico",
                        "phone": "3109876543",
                        "documentId": "{{documento}}",
                        "specialtyId": "3f1c2a4e-8d7b-4c1a-9e2f-5b6a7c8d9e01",
                        "role": "tecnico"
                    },
                    previo=[
                        "const ts = Date.now();",
                        "pm.collectionVariables.set('documento', 'CC-' + String(ts).slice(-8));",
                        "pm.collectionVariables.set('correoTecnico', 'tecnico.qa.' + ts + '@quickpatch.test');"
                    ],
                    pruebas=[
                        "pm.test('[SCRUM-56] 201 Created para registro legítimo', () => pm.response.to.have.status(201));",
                        "pm.test('[SCRUM-56] Rol verificado como tecnico', () => pm.expect(pm.response.json().role).to.eql('tecnico'));",
                        "pm.test('[SCRUM-56 / RN-U1] verificationStatus inicial es pendiente', () => pm.expect(pm.response.json().verificationStatus).to.eql('pendiente'));",
                        "pm.test('[Auditoría] Correlation ID presente en cabecera', () => pm.expect(pm.response.headers.get('X-Correlation-Id')).to.not.be.empty);"
                    ]
                ),
                req(
                    "1.2 Rechazo por documento de identidad repetido → 409 Conflict",
                    "POST",
                    "/v1/auth/register/technician",
                    [JSON, CORR, CANAL],
                    {
                        "email": "otro.correo.repetido@quickpatch.test",
                        "password": "PasswordTecnico123*",
                        "fullName": "Intento Duplicado Documento",
                        "phone": "3112223344",
                        "documentId": "{{documento}}_repetido",
                        "role": "tecnico"
                    },
                    pruebas=[
                        "pm.test('[SCRUM-56] 409 Conflict ante documento repetido', () => pm.response.to.have.status(409));"
                    ] + problem + tipo("documento-registrado")
                ),
                req(
                    "1.3 Rechazo por correo electrónico repetido → 409 Conflict",
                    "POST",
                    "/v1/auth/register/technician",
                    [JSON, CORR, CANAL],
                    {
                        "email": "{{correoTecnico}}_repetido",
                        "password": "PasswordTecnico123*",
                        "fullName": "Intento Duplicado Correo",
                        "phone": "3119998877",
                        "documentId": "CC-99887766",
                        "role": "tecnico"
                    },
                    pruebas=[
                        "pm.test('[SCRUM-56] 409 Conflict ante correo repetido', () => pm.response.to.have.status(409));"
                    ] + problem + tipo("correo-registrado")
                ),
                req(
                    "1.4 Rechazo por documento ausente / clave corta → 400 Bad Request",
                    "POST",
                    "/v1/auth/register/technician",
                    [JSON, CORR, CANAL],
                    {
                        "email": "invalido@quickpatch.test",
                        "password": "123",
                        "fullName": "Técnico Inválido",
                        "role": "tecnico"
                    },
                    pruebas=[
                        "pm.test('[SCRUM-56] 400 Bad Request por fallo de validación de contrato', () => pm.response.to.have.status(400));"
                    ] + problem + tipo("validacion-solicitud")
                ),
                req(
                    "1.5 Login de técnico registrado y obtención de JWT",
                    "POST",
                    "/v1/auth/login",
                    [JSON, CORR, CANAL],
                    {
                        "email": "tecnico@quickpatch.test",
                        "password": "PasswordTecnico123*"
                    },
                    pruebas=[
                        "pm.test('[Auth] Login de técnico exitoso (200 OK)', () => pm.response.to.have.status(200));",
                        "pm.test('[RBAC] Rol del usuario es tecnico', () => pm.expect(pm.response.json().user.role).to.eql('tecnico'));",
                        "pm.collectionVariables.set('tecnicoToken', pm.response.json().accessToken);"
                    ]
                ),
                req(
                    "1.6 Consulta de perfil propio (/v1/users/me) con verificationStatus",
                    "GET",
                    "/v1/users/me",
                    [CORR, auth("tecnicoToken")],
                    pruebas=[
                        "pm.test('[SCRUM-56] 200 OK en consulta de perfil', () => pm.response.to.have.status(200));",
                        "pm.test('[SCRUM-56] verificationStatus visible como pendiente', () => pm.expect(pm.response.json().verificationStatus).to.eql('pendiente'));",
                        "pm.test('[SCRUM-56] Rol verificado como tecnico', () => pm.expect(pm.response.json().role).to.eql('tecnico'));"
                    ]
                ),
                req(
                    "1.7 Control RBAC: Técnico no puede crear solicitudes de cliente → 403 Forbidden",
                    "POST",
                    "/v1/service-requests",
                    [JSON, CORR, auth("tecnicoToken")],
                    {
                        "categoryId": "3f1c2a4e-8d7b-4c1a-9e2f-5b6a7c8d9e01",
                        "description": "Fuga de agua intentada por técnico",
                        "location": {"latitude": 4.6533, "longitude": -74.0836},
                        "addressText": "Calle 45 # 13-20"
                    },
                    pruebas=[
                        "pm.test('[RBAC / IDN-012] 403 Forbidden para rol tecnico creando solicitud', () => pm.response.to.have.status(403));"
                    ] + problem + tipo("no-autorizado")
                )
            ]
        },
        {
            "name": "2. SCRUM-62 — Aislamiento Lógico de Datos por Tenant (Multi-tenant RLS)",
            "item": [
                req(
                    "2.1 Login de Cliente en Tenant Alfa",
                    "POST",
                    "/v1/auth/login",
                    [JSON, CORR, CANAL],
                    {
                        "email": "cliente.alfa@quickpatch.test",
                        "password": "PasswordCliente123*"
                    },
                    pruebas=[
                        "pm.test('[Tenant Alfa] Login exitoso', () => pm.response.to.have.status(200));",
                        "pm.collectionVariables.set('tokenAlfa', pm.response.json().accessToken);"
                    ]
                ),
                req(
                    "2.2 Creación de Solicitud de Servicio en Tenant Alfa",
                    "POST",
                    "/v1/service-requests",
                    [JSON, CORR, auth("tokenAlfa")],
                    {
                        "categoryId": "3f1c2a4e-8d7b-4c1a-9e2f-5b6a7c8d9e01",
                        "description": "Fuga de tubería principal exclusiva Tenant Alfa",
                        "location": {"latitude": 4.6533, "longitude": -74.0836},
                        "addressText": "Carrera 7 # 72-10"
                    },
                    pruebas=[
                        "pm.test('[Tenant Alfa] Solicitud creada con éxito (201 Created)', () => pm.response.to.have.status(201));",
                        "pm.collectionVariables.set('solicitudAlfaId', pm.response.json().id);"
                    ]
                ),
                req(
                    "2.3 Login de Cliente en Tenant Beta",
                    "POST",
                    "/v1/auth/login",
                    [JSON, CORR, CANAL],
                    {
                        "email": "cliente.beta@quickpatch.test",
                        "password": "PasswordCliente123*"
                    },
                    pruebas=[
                        "pm.test('[Tenant Beta] Login exitoso con credenciales de Tenant Beta', () => pm.response.to.have.status(200));",
                        "pm.collectionVariables.set('tokenBeta', pm.response.json().accessToken);"
                    ]
                ),
                req(
                    "2.4 Verificación de Fuga Cross-Tenant (Tenant Beta consulta solicitud de Tenant Alfa) → 404 Not Found",
                    "GET",
                    "/v1/service-requests/{{solicitudAlfaId}}",
                    [CORR, auth("tokenBeta")],
                    pruebas=[
                        "pm.test('[SCRUM-62 / RLS] Código 404 Not Found (cero fuga de datos cross-tenant)', () => pm.response.to.have.status(404));",
                        "pm.test('[Seguridad] Cuerpo no expone datos de la orden de Tenant Alfa', () => {",
                        "  pm.expect(pm.response.text()).to.not.include('exclusiva Tenant Alfa');",
                        "});"
                    ] + problem + tipo("no-encontrado")
                ),
                req(
                    "2.5 Aislamiento en Catálogo: Tenant Beta no ve categorías de Tenant Alfa",
                    "GET",
                    "/v1/catalog/categories",
                    [CORR, auth("tokenBeta")],
                    pruebas=[
                        "pm.test('[SCRUM-62] Catálogo responde 200 OK para Tenant Beta', () => pm.response.to.have.status(200));",
                        "pm.test('[Aislamiento Catálogo] Categoría exclusiva de Alfa no es visible en Beta', () => {",
                        "  const nombres = pm.response.json().map(c => c.name);",
                        "  pm.expect(nombres).to.not.include('Plomería Exclusiva Alfa');",
                        "});"
                    ]
                ),
                req(
                    "2.6 Control Positivo: Propietario en Tenant Alfa sí consulta su solicitud",
                    "GET",
                    "/v1/service-requests/{{solicitudAlfaId}}",
                    [CORR, auth("tokenAlfa")],
                    pruebas=[
                        "pm.test('[Tenant Alfa] 200 OK para el cliente propietario en su mismo tenant', () => pm.response.to.have.status(200));",
                        "pm.test('[Consistencia] Retorna la misma solicitud creada en el paso 2.2', () => {",
                        "  pm.expect(pm.response.json().id).to.eql(pm.collectionVariables.get('solicitudAlfaId'));",
                        "});"
                    ]
                )
            ]
        }
    ]
}

destino = pathlib.Path(__file__).with_name("scrum-56-62-registro-y-aislamiento.postman_collection.json")
destino.write_text(json.dumps(coleccion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Colección generada exitosamente en {destino}")
