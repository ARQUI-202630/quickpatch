"""Generador de la Colección E2E para SCRUM-56: Registro y Perfil de Técnico / Proveedor (Identity).

Diseñada para ejecutarse de forma segura tanto en simulación local como contra el ambiente
real de QA en VM1 (vía .github/workflows/pruebas-sistema.yml en cada release/*):
- Semilla dinámica: obtiene specialtyId desde GET /v1/catalog/categories.
- Datos únicos por corrida: documento y correo generados dinámicamente con timestamp.
- Duplicados reales: reintenta el registro con el mismo documento y el mismo correo de 1.1 (esperando 409).
- Validación de contrato: payload con clave corta o sin documento (esperando 400).
- Login y perfil: autenticación del técnico recién registrado y consulta de /v1/users/me (verificationStatus: pendiente).
- Control RBAC: técnico intentando crear solicitud de servicio (esperando 403).

Uso: python tests/e2e/generar-scrum56.py
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
        "name": "QUICKPATCH — Registro y Perfil de Técnico (SCRUM-56)",
        "description": (
            "Suite automatizada de pruebas de sistema (E2E) para SCRUM-56 (Identity Service):\n"
            "Valida el flujo completo de registro de técnicos y proveedores bajo contratos OpenAPI identity.v1.yaml.\n"
            "Compatible con ejecución en QA real y en simulador local.\n"
            "Variables: baseUrl (https://qa.quickpatch.internal o http://localhost:8080), adminEmail, adminPassword."
        ),
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
    },
    "variable": [
        {"key": "baseUrl", "value": "http://localhost:8080", "type": "string"},
        {"key": "adminEmail", "value": "", "type": "string"},
        {"key": "adminPassword", "value": "", "type": "string"},
        {"key": "tecnicoPassword", "value": "", "type": "string"},
        {"key": "specialtyId", "value": "3f1c2a4e-8d7b-4c1a-9e2f-5b6a7c8d9e01", "type": "string"},
        {"key": "documentoTecnico", "value": "", "type": "string"},
        {"key": "correoTecnico", "value": "", "type": "string"},
        {"key": "tecnicoToken", "value": "", "type": "string"}
    ],
    "item": [
        {
            "name": "0. Semillas y Datos de Referencia",
            "item": [
                req(
                    "0.1 Obtener Especialidad Real de Catálogo",
                    "GET",
                    "/v1/catalog/categories",
                    [CORR, CANAL],
                    pruebas=[
                        "pm.test('[Catalog] 200 OK en consulta de categorías activas', () => pm.response.to.have.status(200));",
                        "const categories = pm.response.json();",
                        "pm.test('[Catalog] Existe al menos una categoría en el tenant', () => pm.expect(categories.length).to.be.above(0));",
                        "if (categories && categories.length > 0) {",
                        "  pm.collectionVariables.set('specialtyId', categories[0].id);",
                        "}"
                    ]
                )
            ]
        },
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
                        "password": "{{tecnicoPassword}}",
                        "fullName": "Carlos Alberto Técnico QA",
                        "phone": "3109876543",
                        "documentId": "{{documentoTecnico}}",
                        "specialtyId": "{{specialtyId}}",
                        "role": "tecnico"
                    },
                    previo=[
                        "const ts = Date.now();",
                        "const doc = String(ts).slice(-8);",
                        "pm.collectionVariables.set('documentoTecnico', doc);",
                        "pm.collectionVariables.set('correoTecnico', 'tecnico.' + ts + '@quickpatch.test');",
                        "pm.collectionVariables.set('tecnicoPassword', 'Qp_' + ts + '_Tec9!');"
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
                        "email": "{{otroCorreo}}",
                        "password": "{{tecnicoPassword}}",
                        "fullName": "Intento Duplicado Documento",
                        "phone": "3112223344",
                        "documentId": "{{documentoTecnico}}",
                        "specialtyId": "{{specialtyId}}",
                        "role": "tecnico"
                    },
                    previo=[
                        "pm.collectionVariables.set('otroCorreo', 'otro.' + Date.now() + '@quickpatch.test');"
                    ],
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
                        "email": "{{correoTecnico}}",
                        "password": "{{tecnicoPassword}}",
                        "fullName": "Intento Duplicado Correo",
                        "phone": "3119998877",
                        "documentId": "{{otroDocumento}}",
                        "specialtyId": "{{specialtyId}}",
                        "role": "tecnico"
                    },
                    previo=[
                        "pm.collectionVariables.set('otroDocumento', String(Date.now() + 1).slice(-8));"
                    ],
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
                    ] + problem + tipo("validacion")
                ),
                req(
                    "1.5 Login de técnico registrado y obtención de JWT",
                    "POST",
                    "/v1/auth/login",
                    [JSON, CORR, CANAL],
                    {
                        "email": "{{correoTecnico}}",
                        "password": "{{tecnicoPassword}}"
                    },
                    pruebas=[
                        "pm.test('[Auth] Login de técnico registrado exitoso (200 OK)', () => pm.response.to.have.status(200));",
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
                        "categoryId": "{{specialtyId}}",
                        "description": "Fuga de agua intentada por técnico",
                        "location": {"latitude": 4.6533, "longitude": -74.0836},
                        "addressText": "Calle 45 # 13-20"
                    },
                    pruebas=[
                        "pm.test('[RBAC / IDN-012] 403 Forbidden para rol tecnico creando solicitud', () => pm.response.to.have.status(403));"
                    ] + problem + tipo("no-autorizado")
                )
            ]
        }
    ]
}

destino = pathlib.Path(__file__).with_name("scrum-56-registro-tecnico.postman_collection.json")
destino.write_text(json.dumps(coleccion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Colección generada exitosamente en {destino}")
