"""Genera scrum-318-web-admin.postman_collection.json (Suite de pruebas del flujo Web Administrativo).

Valida RBAC y Gestión de Tenants desde la perspectiva de la interfaz administrativa de Angular
conforme a los mockups W-01 a W-07, DD 7.12, ADR-018 y la subtarea SCRUM-318.

Uso: python tests/e2e/generar-scrum318-admin.py
"""
import json
import pathlib

JSON_HDR = {"key": "Content-Type", "value": "application/json"}
CORR_HDR = {"key": "X-Correlation-Id", "value": "{{$guid}}"}
CHANNEL_HDR = {"key": "X-Channel-Id", "value": "quickpatch-web"}


def auth_hdr(var_name):
    return {"key": "Authorization", "value": "Bearer {{" + var_name + "}}"}


def crear_req(nombre, metodo, ruta, headers, cuerpo=None, pruebas=(), previo=()):
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
        item["request"]["body"] = {
            "mode": "raw",
            "raw": json.dumps(cuerpo, ensure_ascii=False, indent=2)
        }
    if previo:
        item["event"].append({
            "listen": "prerequest",
            "script": {"type": "text/javascript", "exec": list(previo)}
        })
    if pruebas:
        item["event"].append({
            "listen": "test",
            "script": {"type": "text/javascript", "exec": list(pruebas)}
        })
    return item


problem_rfc9457 = [
    "pm.test('[RFC 9457] Content-Type es application/problem+json', () => {",
    "  pm.expect(pm.response.headers.get('Content-Type')).to.include('application/problem+json');",
    "});",
    "pm.test('[Auditoría] correlationId presente en la respuesta de error', () => {",
    "  pm.expect(pm.response.json()).to.have.property('correlationId');",
    "});"
]

coleccion = {
    "info": {
        "name": "QUICKPATCH — Web Administrativo y Gestión de Tenants (SCRUM-318)",
        "description": (
            "Suite de pruebas de extremo a extremo para el flujo web administrativo en Angular.\n"
            "Valida la autenticación administrativa (W-01, W-02), control de acceso RBAC (W-03),\n"
            "consulta y filtrado de tenants (W-04), desactivación y confirmación (W-05),\n"
            "manejo de errores y conflictos (W-06) y navegación según rol (W-07).\n"
            "Variables requeridas: baseUrl, adminEmail, adminPassword."
        ),
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
    },
    "variable": [
        {"key": "baseUrl", "value": "https://qa.quickpatch.internal"},
        {"key": "adminEmail", "value": ""},
        {"key": "adminPassword", "value": ""},
        {"key": "sufijo", "value": ""}
    ],
    "item": [
        {
            "name": "1. Autenticación y Perfil Administrativo (W-01)",
            "description": "Pruebas del inicio de sesión administrativo para roles de plataforma y de tenant.",
            "item": [
                crear_req(
                    "1.1 [W-01] Login de Administrador de Plataforma (admin_plataforma)",
                    "POST",
                    "/v1/auth/login",
                    [JSON_HDR, CORR_HDR, CHANNEL_HDR],
                    {"email": "platform-admin@quickpatch.internal", "password": "{{adminPassword}}"},
                    pruebas=[
                        "pm.test('[W-01] Autenticación exitosa (200 OK)', () => {",
                        "  pm.response.to.have.status(200);",
                        "});",
                        "if (pm.response.code === 200) {",
                        "  var resData = pm.response.json();",
                        "  pm.test('[W-01] Rol corresponde a admin_plataforma', () => {",
                        "    pm.expect(resData.user.role).to.eql('admin_plataforma');",
                        "  });",
                        "  pm.collectionVariables.set('platformAdminToken', resData.accessToken);",
                        "  pm.collectionVariables.set('sufijo', Date.now().toString(36));",
                        "}"
                    ]
                ),
                crear_req(
                    "1.2 [W-01 / W-07] Login de Administrador de Tenant (admin_tenant)",
                    "POST",
                    "/v1/auth/login",
                    [JSON_HDR, CORR_HDR, CHANNEL_HDR],
                    {"email": "{{adminEmail}}", "password": "{{adminPassword}}"},
                    pruebas=[
                        "pm.test('[W-01] Login exitoso de admin_tenant (200 OK)', () => {",
                        "  pm.response.to.have.status(200);",
                        "});",
                        "if (pm.response.code === 200) {",
                        "  var resTenant = pm.response.json();",
                        "  pm.test('[W-07] Rol verificado como admin_tenant', () => {",
                        "    pm.expect(resTenant.user.role).to.eql('admin_tenant');",
                        "  });",
                        "  pm.collectionVariables.set('tenantAdminToken', resTenant.accessToken);",
                        "}"
                    ]
                )
            ]
        },
        {
            "name": "2. Manejo de Errores en Inicio de Sesión (W-02)",
            "description": "Validación de credenciales inválidas (401) y cuenta bloqueada tras intentos fallidos (423).",
            "item": [
                crear_req(
                    "2.1 [W-02 / RF-03] Credenciales incorrectas → 401 Unauthorized",
                    "POST",
                    "/v1/auth/login",
                    [JSON_HDR, CORR_HDR, CHANNEL_HDR],
                    {"email": "admin@quickpatch.internal", "password": "PasswordInvalidoTotal999*"},
                    pruebas=[
                        "pm.test('[W-02] Rechazo por credenciales inválidas (401)', () => {",
                        "  pm.response.to.have.status(401);",
                        "});",
                        "pm.test('[W-02] Detalle de error indica credenciales incorrectas', () => {",
                        "  var jsonErr = pm.response.json();",
                        "  pm.expect(jsonErr.type).to.include('/problems/no-autenticado');",
                        "});"
                    ] + problem_rfc9457
                ),
                crear_req(
                    "2.2 [W-02 / RN-U4] Cuenta bloqueada tras fallos repetidos → 423 Locked",
                    "POST",
                    "/v1/auth/login",
                    [JSON_HDR, CORR_HDR, CHANNEL_HDR],
                    {"email": "bloqueado@quickpatch.internal", "password": "CualquierPassword123*"},
                    pruebas=[
                        "pm.test('[W-02 / RN-U4] Cuenta bloqueada responde 423 Locked', () => {",
                        "  pm.response.to.have.status(423);",
                        "});",
                        "pm.test('[W-02] Mensaje orienta bloqueo temporal sin revelar existencia', () => {",
                        "  var jsonLocked = pm.response.json();",
                        "  pm.expect(jsonLocked.type).to.include('/problems/cuenta-bloqueada');",
                        "});"
                    ] + problem_rfc9457
                )
            ]
        },
        {
            "name": "3. Control de Acceso por Roles — RBAC (W-03)",
            "description": "Verificación de acceso no autorizado (403) a la gestión de tenants para roles no permitidos.",
            "item": [
                crear_req(
                    "3.1 [W-03 / SCRUM-64] admin_tenant intentando listar tenants → 403 Forbidden",
                    "GET",
                    "/v1/admin/tenants",
                    [CORR_HDR, auth_hdr("tenantAdminToken")],
                    pruebas=[
                        "pm.test('[W-03] Código 403 Forbidden para rol admin_tenant', () => {",
                        "  pm.response.to.have.status(403);",
                        "});",
                        "pm.test('[W-03] Tipo de problema es no-autorizado', () => {",
                        "  pm.expect(pm.response.json().type).to.include('/problems/no-autorizado');",
                        "});"
                    ] + problem_rfc9457
                ),
                crear_req(
                    "3.2 [W-03 / IDN-017] Petición anónima a gestión de tenants → 401 Unauthorized",
                    "GET",
                    "/v1/admin/tenants",
                    [CORR_HDR],
                    pruebas=[
                        "pm.test('[W-03] Código 401 Unauthorized sin credenciales', () => {",
                        "  pm.response.to.have.status(401);",
                        "});"
                    ] + problem_rfc9457
                )
            ]
        },
        {
            "name": "4. Gestión y Listado de Tenants (W-04 & W-06)",
            "description": "Consulta de empresas oferentes, filtros por estado y manejo de respuestas.",
            "item": [
                crear_req(
                    "4.1 [W-04] Consulta de tenants por admin_plataforma (200 OK)",
                    "GET",
                    "/v1/admin/tenants",
                    [CORR_HDR, auth_hdr("platformAdminToken")],
                    pruebas=[
                        "pm.test('[W-04] Listado retornado exitosamente (200 OK)', () => {",
                        "  pm.response.to.have.status(200);",
                        "});",
                        "var lista = pm.response.json();",
                        "pm.test('[W-04] Respuesta es una lista con atributos requeridos', () => {",
                        "  pm.expect(Array.isArray(lista)).to.be.true;",
                        "  pm.expect(lista.length).to.be.above(0);",
                        "  var primer = lista[0];",
                        "  pm.expect(primer).to.have.property('id');",
                        "  pm.expect(primer).to.have.property('name');",
                        "  pm.expect(primer).to.have.property('nit');",
                        "  pm.expect(primer).to.have.property('status');",
                        "});",
                        "pm.collectionVariables.set('targetTenantId', lista[0].id);"
                    ]
                ),
                crear_req(
                    "4.2 [W-04] Filtrado de tenants por estado 'activo'",
                    "GET",
                    "/v1/admin/tenants?status=activo",
                    [CORR_HDR, auth_hdr("platformAdminToken")],
                    pruebas=[
                        "pm.test('[W-04] Filtro activo responde 200 OK', () => {",
                        "  pm.response.to.have.status(200);",
                        "});",
                        "var activos = pm.response.json();",
                        "pm.test('[W-04] Todos los tenants filtrados están activos', () => {",
                        "  activos.forEach(function(t) {",
                        "    pm.expect(t.status).to.eql('activo');",
                        "  });",
                        "});"
                    ]
                )
            ]
        },
        {
            "name": "5. Cambio de Estado y Ciclo de Vida de Tenants (W-05 & W-06)",
            "description": "Desactivación de tenant, manejo de conflicto (409) y bloqueo RN-T1.",
            "item": [
                crear_req(
                    "5.1 [W-05 / SCRUM-113] Desactivar tenant → 200 OK",
                    "PATCH",
                    "/v1/admin/tenants/{{targetTenantId}}/status",
                    [JSON_HDR, CORR_HDR, auth_hdr("platformAdminToken")],
                    {"status": "inactivo", "reason": "Suspensión administrativa por revisión de cumplimiento"},
                    pruebas=[
                        "pm.test('[W-05] Estado actualizado a inactivo exitosamente (200 OK)', () => {",
                        "  pm.response.to.have.status(200);",
                        "});",
                        "pm.test('[W-05] Retorna status inactivo verificado', () => {",
                        "  pm.expect(pm.response.json().status).to.eql('inactivo');",
                        "});"
                    ]
                ),
                crear_req(
                    "5.2 [W-06] Intento de actualización con versión obsoleta → 409 Conflict",
                    "PATCH",
                    "/v1/admin/tenants/{{targetTenantId}}/status",
                    [JSON_HDR, CORR_HDR, auth_hdr("platformAdminToken")],
                    {"status": "inactivo", "version": 0},
                    pruebas=[
                        "pm.test('[W-06] Conflicto de concurrencia detectado (409 Conflict)', () => {",
                        "  pm.response.to.have.status(409);",
                        "});",
                        "pm.test('[W-06] Detalle del problema indica conflicto de versión', () => {",
                        "  pm.expect(pm.response.json().type).to.include('/problems/conflicto-concurrencia');",
                        "});"
                    ] + problem_rfc9457
                ),
                crear_req(
                    "5.3 [RN-T1 / SCRUM-114] Login rechazado para usuario del tenant desactivado → 403 Forbidden",
                    "POST",
                    "/v1/auth/login",
                    [JSON_HDR, CORR_HDR, CHANNEL_HDR],
                    {"email": "usuario@tenant-desactivado.test", "password": "PasswordValido123*"},
                    pruebas=[
                        "pm.test('[RN-T1] Login rechazado para tenant desactivado (403 Forbidden)', () => {",
                        "  pm.response.to.have.status(403);",
                        "});",
                        "pm.test('[RN-T1] Mensaje informa suspensión del tenant', () => {",
                        "  var texto = pm.response.text().toLowerCase();",
                        "  pm.expect(texto.includes('inactivo') || texto.includes('disabled') || texto.includes('tenant')).to.be.true;",
                        "});"
                    ]
                )
            ]
        }
    ]
}

destino = pathlib.Path("tests/e2e/scrum-318-web-admin.postman_collection.json")
destino.write_text(json.dumps(coleccion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Colección generada exitosamente en {destino}")
