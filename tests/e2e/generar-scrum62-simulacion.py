"""Generador de la Suite de Simulación para SCRUM-62: Aislamiento Lógico de Datos por Tenant.

Se guarda como *.simulacion.json (siguiendo el estándar de scrum-318-web-admin.simulacion.json)
para no ejecutarse contra el ambiente monotenant de QA en CI, manteniéndose como prueba
de arquitectura y verificación de políticas RLS locales:
- Validación de cero fuga de información cross-tenant en lectura de órdenes (404 Not Found).
- Aislamiento en catálogo entre Tenant Alfa y Tenant Beta.
- Control positivo dentro del mismo tenant (200 OK).

Uso: python tests/e2e/generar-scrum62-simulacion.py
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
        "name": "QUICKPATCH — Aislamiento por Tenant (SCRUM-62 / Simulación RLS)",
        "description": (
            "Suite de simulación arquitectónica para SCRUM-62 (Aislamiento Lógico de Datos por Tenant):\n"
            "Valida que las reglas de negocio y políticas de Row-Level Security (RLS) eviten cualquier fuga\n"
            "de información entre empresas oferentes (Tenant Alfa vs Tenant Beta).\n"
            "Nota: En el release de QA real, el aislamiento se valida mediante las pruebas de integración\n"
            "con PostgreSQL real (IDN-009, IDN-010, CAT-004, SRQ-007) mientras se habilita el multi-tenant público (SCRUM-41).\n"
            "Variables: baseUrl (http://localhost:8080 en simulador local)."
        ),
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
    },
    "variable": [
        {"key": "baseUrl", "value": "http://localhost:8080", "type": "string"},
        {"key": "clienteAlfaEmail", "value": "cliente.alfa@quickpatch.test", "type": "string"},
        {"key": "clienteAlfaPassword", "value": "", "type": "string"},
        {"key": "clienteBetaEmail", "value": "cliente.beta@quickpatch.test", "type": "string"},
        {"key": "clienteBetaPassword", "value": "", "type": "string"},
        {"key": "tokenAlfa", "value": "", "type": "string"},
        {"key": "tokenBeta", "value": "", "type": "string"},
        {"key": "solicitudAlfaId", "value": "sr-qa-001", "type": "string"}
    ],
    "item": [
        {
            "name": "SCRUM-62 — Aislamiento Lógico de Datos por Tenant (Simulación RLS)",
            "item": [
                req(
                    "1. Login de Cliente en Tenant Alfa",
                    "POST",
                    "/v1/auth/login",
                    [JSON, CORR, CANAL],
                    {
                        "email": "{{clienteAlfaEmail}}",
                        "password": "{{clienteAlfaPassword}}"
                    },
                    pruebas=[
                        "pm.test('[Tenant Alfa] Login exitoso', () => pm.response.to.have.status(200));",
                        "pm.collectionVariables.set('tokenAlfa', pm.response.json().accessToken);"
                    ]
                ),
                req(
                    "2. Creación de Solicitud de Servicio en Tenant Alfa",
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
                    "3. Login de Cliente en Tenant Beta",
                    "POST",
                    "/v1/auth/login",
                    [JSON, CORR, CANAL],
                    {
                        "email": "{{clienteBetaEmail}}",
                        "password": "{{clienteBetaPassword}}"
                    },
                    pruebas=[
                        "pm.test('[Tenant Beta] Login exitoso con credenciales de Tenant Beta', () => pm.response.to.have.status(200));",
                        "pm.collectionVariables.set('tokenBeta', pm.response.json().accessToken);"
                    ]
                ),
                req(
                    "4. Verificación de Fuga Cross-Tenant (Tenant Beta consulta solicitud de Tenant Alfa) → 404 Not Found",
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
                    "5. Aislamiento en Catálogo: Tenant Beta no ve categorías de Tenant Alfa",
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
                    "6. Control Positivo: Propietario en Tenant Alfa sí consulta su solicitud",
                    "GET",
                    "/v1/service-requests/{{solicitudAlfaId}}",
                    [CORR, auth("tokenAlfa")],
                    pruebas=[
                        "pm.test('[Tenant Alfa] 200 OK para el cliente propietario en su mismo tenant', () => pm.response.to.have.status(200));",
                        "pm.test('[Consistencia] Retorna la misma solicitud creada en el paso 2', () => {",
                        "  pm.expect(pm.response.json().id).to.eql(pm.collectionVariables.get('solicitudAlfaId'));",
                        "});"
                    ]
                )
            ]
        }
    ]
}

destino = pathlib.Path(__file__).with_name("scrum-62-aislamiento-tenant.simulacion.json")
destino.write_text(json.dumps(coleccion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Colección de simulación generada exitosamente en {destino}")
