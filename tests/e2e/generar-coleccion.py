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

def tipo(nombre):
    """Comprueba el tipo de Problem Details del contrato (https://quickpatch.internal/problems/<nombre>)."""
    return [f"pm.test('tipo {nombre}', () => pm.expect(pm.response.json().type).to.match(/\\/{nombre}$/));"]


coleccion = {
    "info": {
        "name": "QUICKPATCH — MVP Sprint 3 (flujo de punta a punta)",
        "description": (
            "Administrador crea una categoría (Catalog publica catalog.category-changed) → cliente se registra e inicia "
            "sesión (Identity) → crea una solicitud (ServiceRequest valida la categoría en su réplica y publica "
            "service-request.created, que consume Matching) → consulta el detalle. Incluye casos negativos de "
            "autenticación, rol y cobertura, la gestión de tenants del administrador de la plataforma (SCRUM-112) y los casos "
            "de SCRUM-287: perfil, correo y documento repetidos, login fallido y bloqueo, solicitud de otro cliente, "
            "desactivación de categoría y registro de técnico. "
            "Variables: baseUrl (https://qa.quickpatch.internal), adminEmail, adminPassword, platformAdminEmail y "
            "platformAdminPassword (secretos de QA, nunca en el repositorio). Contratos: quickpatch-api-gateway/openapi."
        ),
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
    },
    "variable": [
        {"key": "baseUrl", "value": "https://qa.quickpatch.internal"},
        {"key": "adminEmail", "value": ""},
        {"key": "adminPassword", "value": ""},
        {"key": "platformAdminEmail", "value": ""},
        {"key": "platformAdminPassword", "value": ""},
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
                req("Perfil del cliente (GET /v1/users/me)", "GET", "/v1/users/me", [CORR, auth("clienteToken")],
                    pruebas=[
                        "pm.test('200 con su propio usuario', () => {",
                        "  pm.response.to.have.status(200);",
                        "  const u = pm.response.json();",
                        "  pm.expect(u.email).to.eql('cliente.' + pm.collectionVariables.get('sufijo') + '@quickpatch.test');",
                        "  pm.expect(u.role).to.eql('cliente');",
                        "  pm.expect(u.verificationStatus).to.eql(null);",
                        "});",
                    ]),
                req("Correo repetido → 409", "POST", "/v1/auth/register/client", [JSON, CORR, CANAL],
                    {"email": "cliente.{{sufijo}}@quickpatch.test", "password": "Segura123", "fullName": "Cliente repetido"},
                    pruebas=["pm.test('409', () => pm.response.to.have.status(409));"] + problem + tipo("correo-registrado")),
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
                req("Contraseña incorrecta → 401", "POST", "/v1/auth/login", [JSON, CORR, CANAL],
                    {"email": "cliente.{{sufijo}}@quickpatch.test", "password": "Incorrecta123"},
                    pruebas=["pm.test('401', () => pm.response.to.have.status(401));"] + problem + tipo("credenciales-invalidas")),
                req("Registro de un cliente para el bloqueo", "POST", "/v1/auth/register/client", [JSON, CORR, CANAL],
                    {"email": "bloqueo.{{sufijo}}@quickpatch.test", "password": "Segura123", "fullName": "Cliente bloqueo"},
                    pruebas=["pm.test('201 registrado', () => pm.response.to.have.status(201));"]),
                req("Intentos fallidos hasta el bloqueo → 423", "POST", "/v1/auth/login", [JSON, CORR, CANAL],
                    {"email": "bloqueo.{{sufijo}}@quickpatch.test", "password": "Incorrecta123"},
                    pruebas=[
                        "// RN-U4: al 5.º intento fallido la cuenta queda bloqueada 15 minutos (LockoutPolicy.Default).",
                        "const n = Number(pm.collectionVariables.get('fallidos') || 0) + 1;",
                        "if (pm.response.code === 401 && n < 10) {",
                        "  pm.collectionVariables.set('fallidos', n);",
                        "  postman.setNextRequest(pm.info.requestName);",
                        "} else {",
                        "  pm.collectionVariables.unset('fallidos');",
                        "  pm.test('423 al llegar al máximo de intentos', () => pm.response.to.have.status(423));",
                        "  pm.test('bloqueo al 5.º intento', () => pm.expect(n).to.eql(5));",
                        "}",
                    ]),
                req("Contraseña correcta durante el bloqueo → 423", "POST", "/v1/auth/login", [JSON, CORR, CANAL],
                    {"email": "bloqueo.{{sufijo}}@quickpatch.test", "password": "Segura123"},
                    pruebas=["pm.test('423', () => pm.response.to.have.status(423));"] + problem + tipo("cuenta-bloqueada")),
                req("Registro de un segundo cliente", "POST", "/v1/auth/register/client", [JSON, CORR, CANAL],
                    {"email": "otro.{{sufijo}}@quickpatch.test", "password": "Segura123", "fullName": "Otro cliente"},
                    pruebas=["pm.test('201 registrado', () => pm.response.to.have.status(201));"]),
                req("Login del segundo cliente", "POST", "/v1/auth/login", [JSON, CORR, CANAL],
                    {"email": "otro.{{sufijo}}@quickpatch.test", "password": "Segura123"},
                    pruebas=[
                        "pm.test('200', () => pm.response.to.have.status(200));",
                        "pm.collectionVariables.set('otroToken', pm.response.json().accessToken);",
                    ]),
                req("Solicitud de otro cliente → 404", "GET", "/v1/service-requests/{{solicitudId}}", [CORR, auth("otroToken")],
                    pruebas=["pm.test('404, sin revelar que existe', () => pm.response.to.have.status(404));"] + problem),
            ],
        },
        {
            "name": "5. Administrador de la plataforma (SCRUM-112)",
            "item": [
                req("Login del administrador de la plataforma", "POST", "/v1/auth/login", [JSON, CORR, CANAL],
                    {"email": "{{platformAdminEmail}}", "password": "{{platformAdminPassword}}"},
                    pruebas=[
                        "pm.test('200 con rol admin_plataforma', () => {",
                        "  pm.response.to.have.status(200);",
                        "  pm.expect(pm.response.json().user.role).to.eql('admin_plataforma');",
                        "});",
                        "pm.collectionVariables.set('plataformaToken', pm.response.json().accessToken);",
                    ]),
                req("Listar tenants", "GET", "/v1/platform/tenants", [CORR, auth("plataformaToken")],
                    pruebas=[
                        "pm.test('200 con al menos el tenant del canal', () => {",
                        "  pm.response.to.have.status(200);",
                        "  const t = pm.response.json();",
                        "  pm.expect(t).to.be.an('array').that.is.not.empty;",
                        "  t.forEach(x => pm.expect(x.status).to.be.oneOf(['activo', 'inactivo']));",
                        "});",
                        "// El tenant del canal es el del administrador de la plataforma en el MVP (DD 10.3).",
                        "const yo = JSON.parse(require('atob')(pm.collectionVariables.get('plataformaToken').split('.')[1].replace(/-/g, '+').replace(/_/g, '/')));",
                        "pm.collectionVariables.set('tenantPropio', yo.tenant_id);",
                        "pm.test('el tenant propio está en la lista', () => pm.expect(pm.response.json().map(x => x.id)).to.include(pm.collectionVariables.get('tenantPropio')));",
                    ]),
                req("Administrador del tenant no lista tenants → 403", "GET", "/v1/platform/tenants", [CORR, auth("adminToken")],
                    pruebas=["pm.test('403', () => pm.response.to.have.status(403));"]),
                req("Cliente no cambia el estado de un tenant → 403", "PATCH", "/v1/platform/tenants/{{tenantPropio}}", [JSON, CORR, auth("clienteToken")],
                    {"status": "inactivo"},
                    pruebas=["pm.test('403', () => pm.response.to.have.status(403));"]),
                req("Desactivar el tenant de la plataforma → 409", "PATCH", "/v1/platform/tenants/{{tenantPropio}}", [JSON, CORR, auth("plataformaToken")],
                    {"status": "inactivo"},
                    pruebas=["pm.test('409 tenant de la plataforma', () => pm.response.to.have.status(409));"] + problem),
                req("Activar el tenant propio es idempotente → 200", "PATCH", "/v1/platform/tenants/{{tenantPropio}}", [JSON, CORR, auth("plataformaToken")],
                    {"status": "activo"},
                    pruebas=[
                        "pm.test('200 y sigue activo', () => {",
                        "  pm.response.to.have.status(200);",
                        "  pm.expect(pm.response.json().status).to.eql('activo');",
                        "});",
                    ]),
                req("Estado fuera del contrato → 400 por campo", "PATCH", "/v1/platform/tenants/{{tenantPropio}}", [JSON, CORR, auth("plataformaToken")],
                    {"status": "suspendido"},
                    pruebas=[
                        "pm.test('400 con error en status', () => {",
                        "  pm.response.to.have.status(400);",
                        "  pm.expect(pm.response.json().errors).to.have.property('status');",
                        "});",
                    ] + problem),
                req("Tenant inexistente → 404", "PATCH", "/v1/platform/tenants/{{$guid}}", [JSON, CORR, auth("plataformaToken")],
                    {"status": "activo"},
                    pruebas=["pm.test('404', () => pm.response.to.have.status(404));"] + problem),
            ],
        },
        {
            "name": "6. Catálogo: desactivar una categoría (SCRUM-287)",
            "item": [
                req("Crear una categoría para desactivar", "POST", "/v1/catalog/admin/categories", [JSON, CORR, auth("adminToken")],
                    {"name": "Cerrajería {{sufijo}}"},
                    pruebas=[
                        "pm.test('201', () => pm.response.to.have.status(201));",
                        "pm.collectionVariables.set('categoriaInactivaId', pm.response.json().id);",
                    ]),
                req("Desactivar la categoría", "PATCH", "/v1/catalog/admin/categories/{{categoriaInactivaId}}", [JSON, CORR, auth("adminToken")],
                    {"active": False},
                    pruebas=[
                        "pm.test('200 inactiva y con updatedAt', () => {",
                        "  pm.response.to.have.status(200);",
                        "  pm.expect(pm.response.json().active).to.eql(false);",
                        "  pm.expect(pm.response.json().updatedAt).to.be.a('string');",
                        "});",
                    ]),
                req("El cliente ya no la ve", "GET", "/v1/catalog/categories", [CORR, auth("clienteToken")],
                    pruebas=[
                        "pm.test('200 sin la categoría inactiva', () => {",
                        "  pm.response.to.have.status(200);",
                        "  pm.expect(pm.response.json().map(c => c.id)).to.not.include(pm.collectionVariables.get('categoriaInactivaId'));",
                        "});",
                    ]),
                req("Categoría inexistente → 404", "PATCH", "/v1/catalog/admin/categories/{{$guid}}", [JSON, CORR, auth("adminToken")],
                    {"active": False},
                    pruebas=["pm.test('404', () => pm.response.to.have.status(404));"] + problem + tipo("no-encontrado")),
            ],
        },
        {
            "name": "7. Técnico (SCRUM-287)",
            "item": [
                req("Registro de técnico", "POST", "/v1/auth/register/technician", [JSON, CORR, CANAL],
                    {"email": "tecnico.{{sufijo}}@quickpatch.test", "password": "Segura123", "fullName": "Técnico de prueba",
                     "phone": "3007654321", "documentId": "{{documento}}", "specialtyId": "{{categoriaId}}", "role": "tecnico"},
                    previo=["pm.collectionVariables.set('documento', String(Date.now()).slice(-10));"],
                    pruebas=[
                        "pm.test('201 pendiente de verificación', () => {",
                        "  pm.response.to.have.status(201);",
                        "  pm.expect(pm.response.json().role).to.eql('tecnico');",
                        "  pm.expect(pm.response.json().verificationStatus).to.eql('pendiente');",
                        "});",
                    ]),
                req("Documento repetido → 409", "POST", "/v1/auth/register/technician", [JSON, CORR, CANAL],
                    {"email": "tecnico2.{{sufijo}}@quickpatch.test", "password": "Segura123", "fullName": "Técnico repetido",
                     "phone": "3007654321", "documentId": "{{documento}}", "specialtyId": "{{categoriaId}}", "role": "tecnico"},
                    pruebas=["pm.test('409', () => pm.response.to.have.status(409));"] + problem + tipo("documento-registrado")),
                req("Login del técnico", "POST", "/v1/auth/login", [JSON, CORR, CANAL],
                    {"email": "tecnico.{{sufijo}}@quickpatch.test", "password": "Segura123"},
                    pruebas=[
                        "pm.test('200 con rol tecnico', () => {",
                        "  pm.response.to.have.status(200);",
                        "  pm.expect(pm.response.json().user.role).to.eql('tecnico');",
                        "});",
                        "pm.collectionVariables.set('tecnicoToken', pm.response.json().accessToken);",
                    ]),
                req("Perfil del técnico muestra la verificación", "GET", "/v1/users/me", [CORR, auth("tecnicoToken")],
                    pruebas=[
                        "pm.test('200 con verificationStatus pendiente', () => {",
                        "  pm.response.to.have.status(200);",
                        "  pm.expect(pm.response.json().verificationStatus).to.eql('pendiente');",
                        "});",
                    ]),
                req("El técnico no crea solicitudes → 403", "POST", "/v1/service-requests", [JSON, CORR, auth("tecnicoToken")],
                    {"categoryId": "{{categoriaId}}", "description": "Fuga de agua debajo del lavaplatos",
                     "location": {"latitude": 4.6533, "longitude": -74.0836}, "addressText": "Calle 45 # 13-20"},
                    pruebas=["pm.test('403', () => pm.response.to.have.status(403));"] + problem),
            ],
        },
    ],
}

destino = pathlib.Path(__file__).with_name("quickpatch-mvp.postman_collection.json")
destino.write_text(json.dumps(coleccion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Colección escrita en {destino}")
