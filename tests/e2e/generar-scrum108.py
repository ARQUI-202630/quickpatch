"""Generador de la Colección E2E para SCRUM-108: Aprobación/Rechazo de Técnicos y Proveedores (Admin).
HU Padre: SCRUM-39 (Aprobación/rechazo de técnicos y proveedores - Admin).
Microservicios validados: Identity Service, Communication Service, API Gateway.
Autora: Katherine Bravo — QA Lead

Criterios y Reglas de Negocio cubiertos:
1. RF-19: El Administrador del Tenant aprueba o rechaza solicitudes de registro de técnicos y proveedores.
2. RN-TP1: Solo técnicos aprobados pueden participar en matching.
3. Transiciones de Estado (DD §8.3.13):
   - pendiente -> aprobado
   - pendiente -> rechazado (con motivo obligatorio >= 5 caracteres)
   - rechazo de transiciones inválidas (409 Conflict): no se permite aprobar o rechazar técnico ya aprobado.
4. Validación de Motivo (DD §8.3.13 / RFC 9457): Motivo ausente o < 5 caracteres responde 400 Bad Request.
5. Notificación y Outbox (ADR-007): Emisión del evento technician.verification-changed.
6. Control de Acceso (RBAC): Clientes y técnicos bloqueados de endpoints administrativos (403 Forbidden).
7. Autenticación (IDN-017): Peticiones anónimas bloqueadas (401 Unauthorized).
8. Aislamiento Multi-Tenant (SAD AC6-E2 / RLS): Admin de Tenant Beta no puede ver ni aprobar técnicos de Tenant Alfa (404 Not Found).

Uso: python tests/e2e/generar-scrum108.py
"""
import json
import pathlib

JSON = {"key": "Content-Type", "value": "application/json"}
CORR = {"key": "X-Correlation-Id", "value": "{{$guid}}"}
CANAL_WEB = {"key": "X-Channel-Id", "value": "quickpatch-web-admin"}


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


def generar():
    carpetas = []

    # -------------------------------------------------------------------------
    # 0. Autenticación de Actores
    # -------------------------------------------------------------------------
    login_admin = [
        "pm.test('[Auth] Login de Admin Tenant Alfa exitoso (200 OK)', () => {",
        "  pm.response.to.have.status(200);",
        "  const json = pm.response.json();",
        "  pm.expect(json).to.have.property('accessToken');",
        "  pm.expect(json.user.role).to.eql('admin_tenant');",
        "  pm.collectionVariables.set('tokenAdmin', json.accessToken);",
        "});",
    ]
    login_admin_beta = [
        "pm.test('[Auth] Login de Admin Tenant Beta exitoso (200 OK)', () => {",
        "  pm.response.to.have.status(200);",
        "  const json = pm.response.json();",
        "  pm.expect(json).to.have.property('accessToken');",
        "  pm.expect(json.user.role).to.eql('admin_tenant');",
        "  pm.collectionVariables.set('tokenAdminBeta', json.accessToken);",
        "});",
    ]
    login_cliente = [
        "pm.test('[Auth] Login de Cliente para RBAC exitoso (200 OK)', () => {",
        "  pm.response.to.have.status(200);",
        "  const json = pm.response.json();",
        "  pm.expect(json).to.have.property('accessToken');",
        "  pm.expect(json.user.role).to.eql('cliente');",
        "  pm.collectionVariables.set('tokenCliente', json.accessToken);",
        "});",
    ]
    login_tecnico = [
        "pm.test('[Auth] Login de Técnico para RBAC exitoso (200 OK)', () => {",
        "  pm.response.to.have.status(200);",
        "  const json = pm.response.json();",
        "  pm.expect(json).to.have.property('accessToken');",
        "  pm.expect(json.user.role).to.eql('tecnico');",
        "  pm.collectionVariables.set('tokenTecnico', json.accessToken);",
        "});",
    ]

    carpetas.append({
        "name": "0. Autenticación de Actores",
        "item": [
            req("0.1 Login Administrador Tenant Alfa", "POST", "/v1/auth/login", [JSON, CORR, CANAL_WEB],
                {"email": "{{adminEmail}}", "password": "{{adminPassword}}"}, login_admin),
            req("0.2 Login Administrador Tenant Beta", "POST", "/v1/auth/login", [JSON, CORR, CANAL_WEB],
                {"email": "{{adminBetaEmail}}", "password": "{{adminBetaPassword}}"}, login_admin_beta),
            req("0.3 Login Cliente para Control RBAC", "POST", "/v1/auth/login", [JSON, CORR, CANAL_WEB],
                {"email": "{{clienteEmail}}", "password": "{{clientePassword}}"}, login_cliente),
            req("0.4 Login Técnico para Control RBAC", "POST", "/v1/auth/login", [JSON, CORR, CANAL_WEB],
                {"email": "{{tecnicoEmail}}", "password": "{{tecnicoPassword}}"}, login_tecnico),
        ],
    })

    # -------------------------------------------------------------------------
    # 1. Consulta y Filtros de Verificación (RF-19 / DD §8.2.1)
    # -------------------------------------------------------------------------
    t_list_pending = [
        "pm.test('[RF-19] 200 OK al listar técnicos pendientes de verificación', () => {",
        "  pm.response.to.have.status(200);",
        "  const json = pm.response.json();",
        "  pm.expect(json).to.have.property('items');",
        "  pm.expect(json.items).to.be.an('array');",
        "  pm.expect(json.total).to.be.at.least(2);",
        "});",
        "pm.test('[RF-19] Técnicos en lista tienen estado pendiente y datos requeridos', () => {",
        "  const json = pm.response.json();",
        "  const pending1 = json.items.find(t => t.userId === 'usr-tec-pending-01');",
        "  pm.expect(pending1).to.exist;",
        "  pm.expect(pending1.verificationStatus).to.eql('pendiente');",
        "  pm.expect(pending1).to.have.property('documentId');",
        "  pm.expect(pending1).to.have.property('specialty');",
        "});",
    ]

    t_list_approved = [
        "pm.test('[Filtro status=aprobado] 200 OK y técnicos aprobados listados', () => {",
        "  pm.response.to.have.status(200);",
        "  const json = pm.response.json();",
        "  pm.expect(json.items).to.be.an('array');",
        "  const app1 = json.items.find(t => t.userId === 'usr-tec-approved-01');",
        "  pm.expect(app1).to.exist;",
        "  pm.expect(app1.verificationStatus).to.eql('aprobado');",
        "});",
    ]

    carpetas.append({
        "name": "1. Consulta y Filtros de Verificación",
        "item": [
            req("1.1 Admin lista técnicos pendientes de verificación", "GET",
                "/v1/admin/technicians?verificationStatus=pendiente", [JSON, CORR, auth("tokenAdmin")], None, t_list_pending),
            req("1.2 Admin lista técnicos aprobados", "GET",
                "/v1/admin/technicians?verificationStatus=aprobado", [JSON, CORR, auth("tokenAdmin")], None, t_list_approved),
        ],
    })

    # -------------------------------------------------------------------------
    # 2. Aprobación de Técnico (RF-19 / RN-TP1 / DD §8.3.13)
    # -------------------------------------------------------------------------
    t_approve_ok = [
        "pm.test('[RF-19 / RN-TP1] 200 OK al aprobar perfil técnico', () => {",
        "  pm.response.to.have.status(200);",
        "  const json = pm.response.json();",
        "  pm.expect(json.userId).to.eql('usr-tec-pending-01');",
        "  pm.expect(json.verificationStatus).to.eql('aprobado');",
        "  pm.expect(json).to.have.property('verifiedAt');",
        "  pm.expect(json.verifiedBy).to.eql('usr-admin-01');",
        "  pm.expect(json.noticeEmitted).to.eql('technician.verification-changed');",
        "});",
    ]

    t_verify_no_longer_pending = [
        "pm.test('[Consistencia] El técnico aprobado ya no aparece en lista de pendientes', () => {",
        "  pm.response.to.have.status(200);",
        "  const json = pm.response.json();",
        "  const found = json.items.find(t => t.userId === 'usr-tec-pending-01');",
        "  pm.expect(found).to.be.undefined;",
        "});",
    ]

    t_approve_invalid = [
        "pm.test('[RN-TP1 / Transición] 409 Conflict al intentar aprobar técnico ya aprobado', () => {",
        "  pm.response.to.have.status(409);",
        "});",
        *problem,
        "pm.test('[Contrato RFC 9457] Tipo de error /transicion-invalida', () => {",
        "  pm.expect(pm.response.json().type).to.include('transicion-invalida');",
        "});",
    ]

    carpetas.append({
        "name": "2. Aprobación de Técnico",
        "item": [
            req("2.1 Admin aprueba técnico pendiente (usr-tec-pending-01)", "POST",
                "/v1/admin/technicians/usr-tec-pending-01/approve", [JSON, CORR, auth("tokenAdmin")], None, t_approve_ok),
            req("2.2 Admin verifica que técnico aprobado ya no está en pendientes", "GET",
                "/v1/admin/technicians?verificationStatus=pendiente", [JSON, CORR, auth("tokenAdmin")], None, t_verify_no_longer_pending),
            req("2.3 Transición Inválida: Intento de aprobar técnico ya aprobado -> 409 Conflict", "POST",
                "/v1/admin/technicians/usr-tec-approved-01/approve", [JSON, CORR, auth("tokenAdmin")], None, t_approve_invalid),
        ],
    })

    # -------------------------------------------------------------------------
    # 3. Rechazo de Técnico con Motivo (RF-19 / DD §8.3.13)
    # -------------------------------------------------------------------------
    t_reject_ok = [
        "pm.test('[RF-19] 200 OK al rechazar técnico con motivo fundamentado', () => {",
        "  pm.response.to.have.status(200);",
        "  const json = pm.response.json();",
        "  pm.expect(json.userId).to.eql('usr-tec-pending-02');",
        "  pm.expect(json.verificationStatus).to.eql('rechazado');",
        "  pm.expect(json.reason).to.include('ilegible');",
        "  pm.expect(json).to.have.property('rejectedAt');",
        "  pm.expect(json.rejectedBy).to.eql('usr-admin-01');",
        "  pm.expect(json.noticeEmitted).to.eql('technician.verification-changed');",
        "});",
    ]

    t_reject_missing_reason = [
        "pm.test('[Validación] 400 Bad Request cuando el motivo es menor a 5 caracteres', () => {",
        "  pm.response.to.have.status(400);",
        "});",
        *problem,
        "pm.test('[Contrato RFC 9457] Tipo de error /validacion-solicitud', () => {",
        "  pm.expect(pm.response.json().type).to.include('validacion-solicitud');",
        "});",
    ]

    t_reject_invalid_state = [
        "pm.test('[Transición Inválida] 409 Conflict al intentar rechazar un técnico en estado aprobado', () => {",
        "  pm.response.to.have.status(409);",
        "});",
        *problem,
        "pm.test('[Contrato RFC 9457] Tipo de error /transicion-invalida', () => {",
        "  pm.expect(pm.response.json().type).to.include('transicion-invalida');",
        "});",
    ]

    carpetas.append({
        "name": "3. Rechazo de Técnico con Motivo",
        "item": [
            req("3.1 Admin rechaza técnico con motivo válido", "POST",
                "/v1/admin/technicians/usr-tec-pending-02/reject", [JSON, CORR, auth("tokenAdmin")],
                {"reason": "Documento de identidad ilegible y certificado técnico vencido."}, t_reject_ok),
            req("3.2 Validación: Intento de rechazar sin motivo válido -> 400 Bad Request", "POST",
                "/v1/admin/technicians/usr-tec-pending-02/reject", [JSON, CORR, auth("tokenAdmin")],
                {"reason": "no"}, t_reject_missing_reason),
            req("3.3 Transición Inválida: Intento de rechazar técnico aprobado -> 409 Conflict", "POST",
                "/v1/admin/technicians/usr-tec-approved-01/reject", [JSON, CORR, auth("tokenAdmin")],
                {"reason": "Rechazo posterior no permitido según máquina de estados"}, t_reject_invalid_state),
        ],
    })

    # -------------------------------------------------------------------------
    # 4. Seguridad RBAC y Aislamiento Multi-Tenant (RLS)
    # -------------------------------------------------------------------------
    t_rbac_cliente = [
        "pm.test('[RBAC] 403 Forbidden para cliente intentando aprobar técnicos', () => {",
        "  pm.response.to.have.status(403);",
        "});",
        *problem,
        "pm.test('[Contrato RFC 9457] Tipo de error /no-autorizado', () => {",
        "  pm.expect(pm.response.json().type).to.include('no-autorizado');",
        "});",
    ]

    t_rbac_tecnico = [
        "pm.test('[RBAC] 403 Forbidden para técnico intentando auto-aprobarse', () => {",
        "  pm.response.to.have.status(403);",
        "});",
        *problem,
        "pm.test('[Contrato RFC 9457] Tipo de error /no-autorizado', () => {",
        "  pm.expect(pm.response.json().type).to.include('no-autorizado');",
        "});",
    ]

    t_anonimo = [
        "pm.test('[Seguridad] 401 Unauthorized ante solicitud anónima (IDN-017)', () => {",
        "  pm.response.to.have.status(401);",
        "});",
        *problem,
        "pm.test('[Contrato RFC 9457] Tipo de error /no-autenticado', () => {",
        "  pm.expect(pm.response.json().type).to.include('no-autenticado');",
        "});",
    ]

    t_rls_cross_approve = [
        "pm.test('[SAD AC6-E2 / RLS] 404 Not Found para Admin Beta intentando aprobar técnico de Alfa', () => {",
        "  pm.response.to.have.status(404);",
        "});",
        *problem,
        "pm.test('[Contrato RFC 9457] Tipo de error /no-encontrado', () => {",
        "  pm.expect(pm.response.json().type).to.include('no-encontrado');",
        "});",
    ]

    t_rls_list_beta = [
        "pm.test('[SAD AC6-E2 / RLS] 200 OK para Admin Beta con aislamiento estricto de técnicos', () => {",
        "  pm.response.to.have.status(200);",
        "  const json = pm.response.json();",
        "  pm.expect(json.total).to.eql(1);",
        "  pm.expect(json.items[0].userId).to.eql('usr-tec-beta-01');",
        "  const hasAlfa = json.items.some(t => t.tenantId === '11111111-1111-1111-1111-111111111111');",
        "  pm.expect(hasAlfa).to.be.false;",
        "});",
    ]

    carpetas.append({
        "name": "4. Control de Acceso RBAC y Aislamiento Multi-Tenant",
        "item": [
            req("4.1 Control RBAC: Cliente intenta aprobar técnico -> 403 Forbidden", "POST",
                "/v1/admin/technicians/usr-tec-pending-01/approve", [JSON, CORR, auth("tokenCliente")], None, t_rbac_cliente),
            req("4.2 Control RBAC: Técnico intenta auto-aprobarse -> 403 Forbidden", "POST",
                "/v1/admin/technicians/usr-tec-pending-01/approve", [JSON, CORR, auth("tokenTecnico")], None, t_rbac_tecnico),
            req("4.3 Seguridad: Consulta anónima sin token -> 401 Unauthorized", "GET",
                "/v1/admin/technicians", [JSON, CORR], None, t_anonimo),
            req("4.4 Aislamiento Multi-Tenant (RLS): Admin Beta intenta aprobar técnico de Tenant Alfa -> 404 Not Found", "POST",
                "/v1/admin/technicians/usr-tec-pending-01/approve", [JSON, CORR, auth("tokenAdminBeta")], None, t_rls_cross_approve),
            req("4.5 Aislamiento Multi-Tenant (RLS): Admin Beta lista técnicos pendientes con cero fuga de Alfa", "GET",
                "/v1/admin/technicians?verificationStatus=pendiente", [JSON, CORR, auth("tokenAdminBeta")], None, t_rls_list_beta),
        ],
    })

    coleccion = {
        "info": {
            "_postman_id": "scrum-108-aprobacion-rechazo-qa",
            "name": "QUICKPATCH — Aprobación y Rechazo de Técnicos (SCRUM-108 / HU SCRUM-39)",
            "description": "Suite E2E para RF-19, RN-TP1 y DD §8.3.13: Verificación, aprobación, rechazo con motivo, máquina de estados, control RBAC y aislamiento multi-tenant con RLS. QA Lead: Katherine Bravo.",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "item": carpetas,
        "variable": [
            {"key": "baseUrl", "value": "http://localhost:8080"},
            {"key": "adminEmail", "value": ""},
            {"key": "adminPassword", "value": ""},
            {"key": "adminBetaEmail", "value": ""},
            {"key": "adminBetaPassword", "value": ""},
            {"key": "clienteEmail", "value": ""},
            {"key": "clientePassword", "value": ""},
            {"key": "tecnicoEmail", "value": ""},
            {"key": "tecnicoPassword", "value": ""},
            {"key": "tokenAdmin", "value": ""},
            {"key": "tokenAdminBeta", "value": ""},
            {"key": "tokenCliente", "value": ""},
            {"key": "tokenTecnico", "value": ""},
        ],
    }

    destino = pathlib.Path(__file__).parent / "scrum-108-aprobacion-rechazo.postman_collection.json"
    destino.write_text(json.dumps(coleccion, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Colección generada con éxito en: {destino}")


if __name__ == "__main__":
    generar()
