"""Genera quickpatch-mvp.postman_collection.json (flujo de punta a punta del MVP de Sprint 3).

Uso: python tests/e2e/generar-coleccion.py
La colección se edita aquí y se regenera, para que el JSON siempre sea válido y revisable en los PR.
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
            "url": {"raw": "{{baseUrl}}/api" + ruta, "host": ["{{baseUrl}}"], "path": ["api"] + ruta.strip("/").split("/")},
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
    "pm.test('Problem Details (RFC 9457) con correlationId', () => {",
    "  pm.expect(pm.response.headers.get('Content-Type')).to.include('application/problem+json');",
    "  pm.expect(pm.response.json()).to.have.property('correlationId');",
    "});",
]

coleccion = {
    "info": {
        "name": "QUICKPATCH — MVP Sprint 3 (flujo de punta a punta)",
        "description": (
            "Administrador crea una categoría (Catalog publica catalog.category-changed) → cliente se registra e inicia "
            "sesión (Identity) → crea una solicitud (ServiceRequest valida la categoría en su réplica y publica "
            "service-request.created, que consume Matching) → consulta el detalle. Incluye casos negativos de "
            "autenticación, rol y cobertura. Variables: baseUrl (https://qa.quickpatch.internal), adminEmail y "
            "adminPassword (secretos de QA, nunca en el repositorio). Contratos: quickpatch-api-gateway/openapi."
        ),
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
    },
    "variable": [
        {"key": "baseUrl", "value": "https://qa.quickpatch.internal"},
        {"key": "adminEmail", "value": ""},
        {"key": "adminPassword", "value": ""},
    ],
    "item": [
        {
            "name": "1. Administrador del tenant",
            "item": [
                req("Login del administrador", "POST", "/v1/auth/login", [JSON, CORR, CANAL],
                    {"email": "{{adminEmail}}", "password": "{{adminPassword}}"},
                    pruebas=[
                        "pm.test('200 con token', () => pm.response.to.have.status(200));",
                        "const r = pm.response.json();",
                        "pm.test('rol admin_tenant', () => pm.expect(r.user.role).to.eql('admin_tenant'));",
                        "pm.collectionVariables.set('adminToken', r.accessToken);",
                    ]),
                req("Crear categoría", "POST", "/v1/catalog/admin/categories", [JSON, CORR, auth("adminToken")],
                    {"name": "Plomería {{sufijo}}", "description": "Fugas, grifería y tuberías"},
                    previo=["pm.collectionVariables.set('sufijo', Date.now().toString(36));"],
                    pruebas=[
                        "pm.test('201 creada y activa', () => {",
                        "  pm.response.to.have.status(201);",
                        "  pm.expect(pm.response.json().active).to.eql(true);",
                        "});",
                        "pm.collectionVariables.set('categoriaId', pm.response.json().id);",
                    ]),
                req("Categoría con nombre repetido → 409", "POST", "/v1/catalog/admin/categories", [JSON, CORR, auth("adminToken")],
                    {"name": "Plomería {{sufijo}}"},
                    pruebas=["pm.test('409 categoría registrada', () => pm.response.to.have.status(409));"] + problem),
            ],
        },
        {
            "name": "2. Cliente",
            "item": [
                req("Registro de cliente", "POST", "/v1/auth/register/client", [JSON, CORR, CANAL],
                    {"email": "cliente.{{sufijo}}@quickpatch.test", "password": "Segura123", "fullName": "Cliente de prueba", "phone": "3001234567"},
                    pruebas=["pm.test('201 registrado', () => pm.response.to.have.status(201));"]),
                req("Login del cliente", "POST", "/v1/auth/login", [JSON, CORR, CANAL],
                    {"email": "cliente.{{sufijo}}@quickpatch.test", "password": "Segura123"},
                    pruebas=[
                        "pm.test('200 con rol cliente', () => {",
                        "  pm.response.to.have.status(200);",
                        "  pm.expect(pm.response.json().user.role).to.eql('cliente');",
                        "});",
                        "pm.collectionVariables.set('clienteToken', pm.response.json().accessToken);",
                    ]),
                req("Categorías del tenant incluyen la nueva", "GET", "/v1/catalog/categories", [CORR, auth("clienteToken")],
                    pruebas=[
                        "pm.test('200 y la categoría está activa', () => {",
                        "  pm.response.to.have.status(200);",
                        "  pm.expect(pm.response.json().map(c => c.id)).to.include(pm.collectionVariables.get('categoriaId'));",
                        "});",
                    ]),
            ],
        },
        {
            "name": "3. Solicitud de servicio",
            "item": [
                req("Crear solicitud (espera la réplica de la categoría)", "POST", "/v1/service-requests", [JSON, CORR, auth("clienteToken")],
                    {"categoryId": "{{categoriaId}}", "description": "Fuga de agua debajo del lavaplatos",
                     "location": {"latitude": 4.6533, "longitude": -74.0836}, "addressText": "Calle 45 # 13-20, apto 301"},
                    pruebas=[
                        "// La réplica de categorías de ServiceRequest se actualiza por evento (ADR-017): se reintenta",
                        "// hasta 10 veces, cada 2 s, mientras la categoría todavía no llega (422 categoria-no-disponible).",
                        "const intento = Number(pm.collectionVariables.get('intentos') || 0);",
                        "if (pm.response.code === 422 && intento < 10) {",
                        "  pm.collectionVariables.set('intentos', intento + 1);",
                        "  setTimeout(() => {}, 2000);",
                        "  postman.setNextRequest(pm.info.requestName);",
                        "} else {",
                        "  pm.collectionVariables.unset('intentos');",
                        "  pm.test('201 en buscando_tecnico', () => {",
                        "    pm.response.to.have.status(201);",
                        "    const s = pm.response.json();",
                        "    pm.expect(s.status).to.eql('buscando_tecnico');",
                        "    pm.expect(s.technicianId).to.eql(null);",
                        "    pm.expect(s.categoryId).to.eql(pm.collectionVariables.get('categoriaId'));",
                        "  });",
                        "  pm.test('responde con X-Correlation-Id', () => pm.expect(pm.response.headers.get('X-Correlation-Id')).to.be.ok);",
                        "  pm.collectionVariables.set('solicitudId', pm.response.json().id);",
                        "}",
                    ]),
                req("Consultar la solicitud", "GET", "/v1/service-requests/{{solicitudId}}", [CORR, auth("clienteToken")],
                    pruebas=[
                        "pm.test('200 con la misma solicitud', () => {",
                        "  pm.response.to.have.status(200);",
                        "  pm.expect(pm.response.json().id).to.eql(pm.collectionVariables.get('solicitudId'));",
                        "});",
                    ]),
            ],
        },
        {
            "name": "4. Casos negativos",
            "item": [
                req("Sin token → 401", "POST", "/v1/service-requests", [JSON, CORR],
                    {"categoryId": "{{categoriaId}}", "description": "Fuga de agua debajo del lavaplatos",
                     "location": {"latitude": 4.6533, "longitude": -74.0836}, "addressText": "Calle 45 # 13-20"},
                    pruebas=["pm.test('401', () => pm.response.to.have.status(401));"]),
                req("Administrador no crea solicitudes → 403", "POST", "/v1/service-requests", [JSON, CORR, auth("adminToken")],
                    {"categoryId": "{{categoriaId}}", "description": "Fuga de agua debajo del lavaplatos",
                     "location": {"latitude": 4.6533, "longitude": -74.0836}, "addressText": "Calle 45 # 13-20"},
                    pruebas=["pm.test('403', () => pm.response.to.have.status(403));"]),
                req("Cliente no administra categorías → 403", "POST", "/v1/catalog/admin/categories", [JSON, CORR, auth("clienteToken")],
                    {"name": "No permitida {{sufijo}}"},
                    pruebas=["pm.test('403', () => pm.response.to.have.status(403));"]),
                req("Fuera de Bogotá → 422", "POST", "/v1/service-requests", [JSON, CORR, auth("clienteToken")],
                    {"categoryId": "{{categoriaId}}", "description": "Fuga de agua debajo del lavaplatos",
                     "location": {"latitude": 6.2442, "longitude": -75.5812}, "addressText": "Medellín, calle 10"},
                    pruebas=["pm.test('422 fuera de cobertura', () => pm.response.to.have.status(422));"] + problem),
                req("Descripción corta → 400 por campo", "POST", "/v1/service-requests", [JSON, CORR, auth("clienteToken")],
                    {"categoryId": "{{categoriaId}}", "description": "corta",
                     "location": {"latitude": 4.6533, "longitude": -74.0836}, "addressText": "Calle 45 # 13-20"},
                    pruebas=[
                        "pm.test('400 con error en description', () => {",
                        "  pm.response.to.have.status(400);",
                        "  pm.expect(pm.response.json().errors).to.have.property('description');",
                        "});",
                    ] + problem),
            ],
        },
    ],
}

destino = pathlib.Path(__file__).with_name("quickpatch-mvp.postman_collection.json")
destino.write_text(json.dumps(coleccion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Colección escrita en {destino}")
