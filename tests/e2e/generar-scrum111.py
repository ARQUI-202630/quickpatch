"""Generador de la Colección E2E para SCRUM-111: Suspensión de Cuenta de Técnico (Admin).
HU Padre: SCRUM-40 (Suspensión de cuenta de técnico - Admin).
Microservicios validados: Identity Service, Matching Service, Communication Service, API Gateway.
Autora: Katherine Bravo — QA Lead

Criterios y Reglas de Negocio cubiertos:
1. RF-20: El Administrador suspende la cuenta de un técnico con motivo registrado.
2. RN-TP2: Un técnico suspendido no puede recibir nuevas solicitudes (participación en matching bloqueada).
3. Transiciones de Estado (DD §8.3.13):
   - aprobado -> suspendido (con motivo obligatorio >= 5 caracteres).
   - suspendido -> aprobado (reactivación exitosa por admin).
   - rechazo de transiciones inválidas (409 Conflict): no se permite suspender desde pendiente o re-suspender.
4. Validación de Motivo (DD §8.3.13 / RFC 9457): Motivo ausente o < 5 caracteres responde 400 Bad Request.
5. Notificación y Outbox (ADR-007): Emisión del evento technician.verification-changed.
6. Control de Acceso (RBAC): Clientes y técnicos bloqueados de suspender cuentas (403 Forbidden).
7. Autenticación (IDN-017): Peticiones anónimas bloqueadas (401 Unauthorized).
8. Aislamiento Multi-Tenant (SAD AC6-E2 / RLS): Admin de Tenant Beta no puede suspender técnicos de Tenant Alfa (404 Not Found).

Uso: python tests/e2e/generar-scrum111.py
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
                {"email": "admin@quickpatch.test", "password": "PasswordAdmin123*"}, login_admin),
            req("0.2 Login Administrador Tenant Beta", "POST", "/v1/auth/login", [JSON, CORR, CANAL_WEB],
                {"email": "admin.beta@quickpatch.test", "password": "PasswordAdminBeta123*"}, login_admin_beta),
            req("0.3 Login Cliente para Control RBAC", "POST", "/v1/auth/login", [JSON, CORR, CANAL_WEB],
                {"email": "cliente@quickpatch.test", "password": "PasswordCliente123*"}, login_cliente),
            req("0.4 Login Técnico para Control RBAC", "POST", "/v1/auth/login", [JSON, CORR, CANAL_WEB],
                {"email": "tecnico@quickpatch.test", "password": "PasswordTecnico123*"}, login_tecnico),
        ],
    })

    # -------------------------------------------------------------------------
    # 1. Suspensión de Cuenta de Técnico (RF-20 / RN-TP2 / DD §8.3.13)
    # -------------------------------------------------------------------------
    t_suspend_ok = [
        "pm.test('[RF-20 / RN-TP2] 200 OK al suspender técnico aprobado con motivo válido', () => {",
        "  pm.response.to.have.status(200);",
        "  const json = pm.response.json();",
        "  pm.expect(json.userId).to.eql('usr-tec-approved-01');",
        "  pm.expect(json.verificationStatus).to.eql('suspendido');",
        "  pm.expect(json.reason).to.include('Incumplimiento grave');",
        "  pm.expect(json.matchingBlocked).to.be.true;",
        "  pm.expect(json).to.have.property('suspendedAt');",
        "  pm.expect(json.suspendedBy).to.eql('usr-admin-01');",
        "  pm.expect(json.noticeEmitted).to.eql('technician.verification-changed');",
        "});",
    ]

    t_list_suspended = [
        "pm.test('[Consistencia] Técnico suspendido aparece en lista de suspendidos', () => {",
        "  pm.response.to.have.status(200);",
        "  const json = pm.response.json();",
        "  const found = json.items.find(t => t.userId === 'usr-tec-approved-01');",
        "  pm.expect(found).to.exist;",
        "  pm.expect(found.verificationStatus).to.eql('suspendido');",
        "});",
    ]

    t_reactivate_ok = [
        "pm.test('[Reactivación / DD §8.3.13] 200 OK al reactivar técnico suspendido a aprobado', () => {",
        "  pm.response.to.have.status(200);",
        "  const json = pm.response.json();",
        "  pm.expect(json.userId).to.eql('usr-tec-suspended-01');",
        "  pm.expect(json.verificationStatus).to.eql('aprobado');",
        "  pm.expect(json.noticeEmitted).to.eql('technician.verification-changed');",
        "});",
    ]

    carpetas.append({
        "name": "1. Suspensión y Reactivación de Técnico",
        "item": [
            req("1.1 Admin suspende técnico en estado aprobado", "POST",
                "/v1/admin/technicians/usr-tec-approved-01/suspend", [JSON, CORR, auth("tokenAdmin")],
                {"reason": "Incumplimiento grave reiterado de protocolos de seguridad."}, t_suspend_ok),
            req("1.2 Admin consulta técnicos suspendidos", "GET",
                "/v1/admin/technicians?verificationStatus=suspendido", [JSON, CORR, auth("tokenAdmin")], None, t_list_suspended),
            req("1.3 Reactivación: Admin aprueba y reactiva técnico suspendido (usr-tec-suspended-01)", "POST",
                "/v1/admin/technicians/usr-tec-suspended-01/approve", [JSON, CORR, auth("tokenAdmin")], None, t_reactivate_ok),
        ],
    })

    # -------------------------------------------------------------------------
    # 2. Reglas de Negocio, Validación y Máquina de Estados
    # -------------------------------------------------------------------------
    t_suspend_missing_reason = [
        "pm.test('[Validación] 400 Bad Request cuando el motivo de suspensión es < 5 caracteres', () => {",
        "  pm.response.to.have.status(400);",
        "});",
        *problem,
        "pm.test('[Contrato RFC 9457] Tipo de error /validacion-solicitud', () => {",
        "  pm.expect(pm.response.json().type).to.include('validacion-solicitud');",
        "});",
    ]

    t_suspend_already_suspended = [
        "pm.test('[Transición Inválida] 409 Conflict al intentar suspender un técnico ya suspendido', () => {",
        "  pm.response.to.have.status(409);",
        "});",
        *problem,
        "pm.test('[Contrato RFC 9457] Tipo de error /transicion-invalida', () => {",
        "  pm.expect(pm.response.json().type).to.include('transicion-invalida');",
        "});",
    ]

    t_suspend_pending = [
        "pm.test('[Transición Inválida] 409 Conflict al intentar suspender un técnico en estado pendiente', () => {",
        "  pm.response.to.have.status(409);",
        "});",
        *problem,
        "pm.test('[Contrato RFC 9457] Tipo de error /transicion-invalida', () => {",
        "  pm.expect(pm.response.json().type).to.include('transicion-invalida');",
        "});",
    ]

    carpetas.append({
        "name": "2. Reglas de Negocio y Validaciones",
        "item": [
            req("2.1 Validación: Intento de suspender con motivo menor a 5 caracteres -> 400 Bad Request", "POST",
                "/v1/admin/technicians/usr-tec-approved-01/suspend", [JSON, CORR, auth("tokenAdmin")],
                {"reason": "mal"}, t_suspend_missing_reason),
            req("2.2 Transición Inválida: Intento de suspender técnico ya suspendido -> 409 Conflict", "POST",
                "/v1/admin/technicians/usr-tec-approved-01/suspend", [JSON, CORR, auth("tokenAdmin")],
                {"reason": "Intento de re-suspensión no admitido"}, t_suspend_already_suspended),
            req("2.3 Transición Inválida: Intento de suspender técnico en estado pendiente -> 409 Conflict", "POST",
                "/v1/admin/technicians/usr-tec-pending-01/suspend", [JSON, CORR, auth("tokenAdmin")],
                {"reason": "No se puede suspender quien no ha sido previamente aprobado"}, t_suspend_pending),
        ],
    })

    # -------------------------------------------------------------------------
    # 3. Control de Acceso RBAC y Aislamiento Multi-Tenant (RLS)
    # -------------------------------------------------------------------------
    t_rbac_cliente = [
        "pm.test('[RBAC] 403 Forbidden para cliente intentando suspender técnico', () => {",
        "  pm.response.to.have.status(403);",
        "});",
        *problem,
        "pm.test('[Contrato RFC 9457] Tipo de error /no-autorizado', () => {",
        "  pm.expect(pm.response.json().type).to.include('no-autorizado');",
        "});",
    ]

    t_rbac_tecnico = [
        "pm.test('[RBAC] 403 Forbidden para técnico intentando suspender a otro técnico', () => {",
        "  pm.response.to.have.status(403);",
        "});",
        *problem,
        "pm.test('[Contrato RFC 9457] Tipo de error /no-autorizado', () => {",
        "  pm.expect(pm.response.json().type).to.include('no-autorizado');",
        "});",
    ]

    t_anonimo = [
        "pm.test('[Seguridad] 401 Unauthorized ante solicitud anónima de suspensión (IDN-017)', () => {",
        "  pm.response.to.have.status(401);",
        "});",
        *problem,
        "pm.test('[Contrato RFC 9457] Tipo de error /no-autenticado', () => {",
        "  pm.expect(pm.response.json().type).to.include('no-autenticado');",
        "});",
    ]

    t_rls_cross_suspend = [
        "pm.test('[SAD AC6-E2 / RLS] 404 Not Found para Admin Beta intentando suspender técnico de Alfa', () => {",
        "  pm.response.to.have.status(404);",
        "});",
        *problem,
        "pm.test('[Contrato RFC 9457] Tipo de error /no-encontrado', () => {",
        "  pm.expect(pm.response.json().type).to.include('no-encontrado');",
        "});",
    ]

    t_rls_list_beta_suspended = [
        "pm.test('[SAD AC6-E2 / RLS] 200 OK para Admin Beta con total = 0 suspendidos en su tenant', () => {",
        "  pm.response.to.have.status(200);",
        "  const json = pm.response.json();",
        "  pm.expect(json.total).to.eql(0);",
        "  pm.expect(json.items).to.be.an('array').that.is.empty;",
        "});",
        "pm.test('[Multi-Tenancy] Cero fuga de técnicos suspendidos de Tenant Alfa a Tenant Beta', () => {",
        "  pm.expect(pm.response.json().total).to.eql(0);",
        "});",
    ]

    carpetas.append({
        "name": "3. Control de Acceso RBAC y Aislamiento Multi-Tenant",
        "item": [
            req("3.1 Control RBAC: Cliente intenta suspender técnico -> 403 Forbidden", "POST",
                "/v1/admin/technicians/usr-tec-approved-01/suspend", [JSON, CORR, auth("tokenCliente")],
                {"reason": "Cliente inconforme con servicio"}, t_rbac_cliente),
            req("3.2 Control RBAC: Técnico intenta suspender a colega -> 403 Forbidden", "POST",
                "/v1/admin/technicians/usr-tec-approved-01/suspend", [JSON, CORR, auth("tokenTecnico")],
                {"reason": "Conflicto operativo entre técnicos"}, t_rbac_tecnico),
            req("3.3 Seguridad: Solicitud anónima sin token -> 401 Unauthorized", "POST",
                "/v1/admin/technicians/usr-tec-approved-01/suspend", [JSON, CORR],
                {"reason": "Petición anónima ilegal"}, t_anonimo),
            req("3.4 Aislamiento Multi-Tenant (RLS): Admin Beta intenta suspender técnico de Alfa -> 404 Not Found", "POST",
                "/v1/admin/technicians/usr-tec-approved-01/suspend", [JSON, CORR, auth("tokenAdminBeta")],
                {"reason": "Suspensión cross-tenant no permitida"}, t_rls_cross_suspend),
            req("3.5 Aislamiento Multi-Tenant (RLS): Admin Beta lista suspendidos con cero fuga de Alfa", "GET",
                "/v1/admin/technicians?verificationStatus=suspendido", [JSON, CORR, auth("tokenAdminBeta")], None, t_rls_list_beta_suspended),
        ],
    })

    coleccion = {
        "info": {
            "_postman_id": "scrum-111-suspension-tecnico-qa",
            "name": "QUICKPATCH — Suspensión de Cuenta de Técnico (SCRUM-111 / HU SCRUM-40)",
            "description": "Suite E2E para RF-20, RN-TP2 y DD §8.3.13: Suspensión de cuenta con motivo, bloqueo de matching, reactivación a aprobado, máquina de estados, control RBAC y aislamiento multi-tenant con RLS. QA Lead: Katherine Bravo.",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "item": carpetas,
        "variable": [
            {"key": "baseUrl", "value": "http://localhost:8080"},
            {"key": "tokenAdmin", "value": ""},
            {"key": "tokenAdminBeta", "value": ""},
            {"key": "tokenCliente", "value": ""},
            {"key": "tokenTecnico", "value": ""},
        ],
    }

    destino = pathlib.Path(__file__).parent / "scrum-111-suspension-tecnico.postman_collection.json"
    destino.write_text(json.dumps(coleccion, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Colección generada con éxito en: {destino}")


if __name__ == "__main__":
    generar()
