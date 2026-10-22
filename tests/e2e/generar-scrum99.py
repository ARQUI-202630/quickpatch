"""Generador de la Colección E2E para SCRUM-99: Gestión de Equipo de Técnicos (Proveedor).
HU Padre: SCRUM-36 (Gestión de equipo de técnicos).
Microservicios validados: Identity Service, Communication Service, API Gateway.
Autora: Katherine Bravo — QA Lead

Criterios y Reglas de Negocio cubiertos:
1. RF-16: El Proveedor registra y administra su equipo de técnicos.
2. RN-TP3: El técnico dado de alta hereda el tenant del proveedor, rol "tecnico", y queda en "pendiente" hasta aprobación de admin_tenant.
3. RN-TP4: Un proveedor solo puede consultar y administrar los técnicos asociados a su propio usuario (provider_id = user.id).
4. Unicidad (RN-U1): Rechazo por cédula o correo duplicado (409 Conflict).
5. Validación: Rechazo por campos obligatorios faltantes (400 Bad Request).
6. Control de Acceso (RBAC): Bloqueo a clientes y técnicos intentando invocar endpoints de proveedor (403 Forbidden).
7. Autenticación (IDN-017): Bloqueo a peticiones anónimas (401 Unauthorized).
8. Aislamiento Intra-Tenant: Proveedor 2 no visualiza los técnicos de Proveedor 1 (mismo tenant).
9. Aislamiento Multi-Tenant (RLS): Proveedor de Tenant Beta no visualiza técnicos de Tenant Alfa.

Uso: python tests/e2e/generar-scrum99.py
Escribe scrum-99-equipo-proveedor.postman_collection.json.
No exige credenciales fijas: todas las cuentas (proveedor 1, proveedor 2, proveedor Beta, cliente y técnico)
se registran dinámicamente con sufijo y clave temporal por corrida.
Las acciones administrativas (aprobación) usan CON_ADMIN y se omiten automáticamente si adminEmail no está definido,
permitiendo que la suite corra completa tanto en simulación local como en QA sin credenciales admin obligatorias.
"""
import importlib.util
import json
import pathlib

AQUI = pathlib.Path(__file__).parent
_spec = importlib.util.spec_from_file_location("base", AQUI / "generar-scrum490-96-cotizacion-evidencia.py")
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)

JSON = base.JSON
CORR = base.CORR
CANAL = base.CANAL
BETA = base.BETA
CANAL_WEB = {"key": "X-Channel-Id", "value": "quickpatch-web-admin"}
CON_ADMIN = base.CON_ADMIN
auth = base.auth
preparar = base.preparar


def req(nombre, metodo, ruta, headers, cuerpo=None, pruebas=(), previo=(), con_admin=False):
    """Genera item de Postman. Si no requiere admin, omite la guardia CON_ADMIN."""
    item = base.req(nombre, metodo, ruta, headers, cuerpo, pruebas, previo)
    if not con_admin:
        for evento in item["event"]:
            if evento["listen"] == "prerequest":
                evento["script"]["exec"] = [linea for linea in evento["script"]["exec"] if linea not in CON_ADMIN]
    return item


problem = [
    "pm.test('[RFC 9457] Problem Details con correlationId', () => {",
    "  pm.expect(pm.response.headers.get('Content-Type')).to.include('application/problem+json');",
    "  pm.expect(pm.response.json()).to.have.property('correlationId');",
    "});",
]


def tipo(nombre):
    return [f"pm.test('[Contrato] Tipo de error {nombre}', () => pm.expect(pm.response.json().type).to.include('{nombre}'));"]


def generar():
    carpetas = []

    # -------------------------------------------------------------------------
    # 0. Autenticación Dinámica de Actores y Catálogo
    # -------------------------------------------------------------------------
    login_prov1 = [
        "pm.test('[Auth] Login de Proveedor 1 exitoso (200 OK)', () => {",
        "  pm.response.to.have.status(200);",
        "  const json = pm.response.json();",
        "  pm.expect(json).to.have.property('accessToken');",
        "  pm.expect(json.user.role).to.eql('proveedor');",
        "  pm.collectionVariables.set('tokenProv1', json.accessToken);",
        "  pm.collectionVariables.set('prov1Id', json.user.id);",
        "});",
    ]
    login_prov2 = [
        "pm.test('[Auth] Login de Proveedor 2 exitoso (200 OK)', () => {",
        "  pm.response.to.have.status(200);",
        "  const json = pm.response.json();",
        "  pm.expect(json).to.have.property('accessToken');",
        "  pm.expect(json.user.role).to.eql('proveedor');",
        "  pm.collectionVariables.set('tokenProv2', json.accessToken);",
        "  pm.collectionVariables.set('prov2Id', json.user.id);",
        "});",
    ]
    login_prov_beta = [
        "pm.test('[Auth] Login de Proveedor Beta exitoso (200 OK)', () => {",
        "  pm.response.to.have.status(200);",
        "  const json = pm.response.json();",
        "  pm.expect(json).to.have.property('accessToken');",
        "  pm.expect(json.user.role).to.eql('proveedor');",
        "  pm.collectionVariables.set('tokenProvBeta', json.accessToken);",
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
        "name": "0. Autenticación Dinámica de Actores y Catálogo",
        "item": [
            req(
                "0.1 Consulta de Categoría Activa de Catálogo",
                "GET",
                "/v1/catalog/categories",
                [CORR, CANAL],
                pruebas=[
                    "pm.test('[Catalog] 200 OK en consulta de categorías activas', () => pm.response.to.have.status(200));",
                    "const cats = pm.response.json();",
                    "pm.test('[Catalog] Categoría disponible para especialidad', () => pm.expect(cats).to.be.an('array').that.is.not.empty);",
                    "if (cats && cats.length > 0) { pm.collectionVariables.set('specialtyId', cats[0].id); }",
                ],
                previo=preparar,
            ),
            req(
                "0.2 Registro Dinámico Proveedor Principal",
                "POST",
                "/v1/auth/register/technician",
                [JSON, CORR, CANAL],
                {
                    "email": "prov1.qa.{{sufijo}}@quickpatch.test",
                    "password": "{{clave}}",
                    "fullName": "Proveedor Principal QA",
                    "phone": "3101234567",
                    "documentId": "{{docProv1}}",
                    "specialtyId": "{{specialtyId}}",
                    "role": "proveedor",
                },
                previo=["pm.collectionVariables.set('docProv1', String(Date.now()).slice(-8));"],
                pruebas=[
                    "pm.test('[Auth] 201 Created registro proveedor 1', () => pm.response.to.have.status(201));",
                    "pm.collectionVariables.set('prov1Id', pm.response.json().id || pm.response.json().userId);",
                ],
            ),
            req("0.3 Login Proveedor Principal", "POST", "/v1/auth/login", [JSON, CORR, CANAL],
                {"email": "prov1.qa.{{sufijo}}@quickpatch.test", "password": "{{clave}}"}, login_prov1),
            req(
                "0.4 Registro Dinámico Proveedor 2 (Mismo Tenant)",
                "POST",
                "/v1/auth/register/technician",
                [JSON, CORR, CANAL],
                {
                    "email": "prov2.qa.{{sufijo}}@quickpatch.test",
                    "password": "{{clave}}",
                    "fullName": "Proveedor 2 QA",
                    "phone": "3101234568",
                    "documentId": "{{docProv2}}",
                    "specialtyId": "{{specialtyId}}",
                    "role": "proveedor",
                },
                previo=["pm.collectionVariables.set('docProv2', String(Date.now() + 1).slice(-8));"],
                pruebas=[
                    "pm.test('[Auth] 201 Created registro proveedor 2', () => pm.response.to.have.status(201));",
                    "pm.collectionVariables.set('prov2Id', pm.response.json().id || pm.response.json().userId);",
                ],
            ),
            req("0.5 Login Proveedor 2 en Mismo Tenant", "POST", "/v1/auth/login", [JSON, CORR, CANAL],
                {"email": "prov2.qa.{{sufijo}}@quickpatch.test", "password": "{{clave}}"}, login_prov2),
            req(
                "0.6 Registro Dinámico Proveedor Tenant Beta",
                "POST",
                "/v1/auth/register/technician",
                [JSON, CORR, BETA],
                {
                    "email": "provbeta.qa.{{sufijo}}@quickpatch.test",
                    "password": "{{clave}}",
                    "fullName": "Proveedor Beta QA",
                    "phone": "3101234569",
                    "documentId": "{{docProvBeta}}",
                    "specialtyId": "{{specialtyId}}",
                    "role": "proveedor",
                },
                previo=["pm.collectionVariables.set('docProvBeta', String(Date.now() + 2).slice(-8));"],
                pruebas=["pm.test('[Auth] 201 Created registro proveedor Beta', () => pm.response.to.have.status(201));"],
            ),
            req("0.7 Login Proveedor Tenant Beta", "POST", "/v1/auth/login", [JSON, CORR, BETA],
                {"email": "provbeta.qa.{{sufijo}}@quickpatch.test", "password": "{{clave}}"}, login_prov_beta),
            req(
                "0.8 Registro Dinámico Cliente para Control RBAC",
                "POST",
                "/v1/auth/register/client",
                [JSON, CORR, CANAL],
                {
                    "email": "cliente.qa.{{sufijo}}@quickpatch.test",
                    "password": "{{clave}}",
                    "fullName": "Cliente RBAC QA",
                },
                pruebas=["pm.test('[Auth] 201 Created registro cliente', () => pm.response.to.have.status(201));"],
            ),
            req("0.9 Login Cliente para Control RBAC", "POST", "/v1/auth/login", [JSON, CORR, CANAL],
                {"email": "cliente.qa.{{sufijo}}@quickpatch.test", "password": "{{clave}}"}, login_cliente),
            req(
                "0.10 Registro Dinámico Técnico para Control RBAC",
                "POST",
                "/v1/auth/register/technician",
                [JSON, CORR, CANAL],
                {
                    "email": "tecnico.qa.{{sufijo}}@quickpatch.test",
                    "password": "{{clave}}",
                    "fullName": "Técnico RBAC QA",
                    "phone": "3101234570",
                    "documentId": "{{docTecnico}}",
                    "specialtyId": "{{specialtyId}}",
                    "role": "tecnico",
                },
                previo=["pm.collectionVariables.set('docTecnico', String(Date.now() + 3).slice(-8));"],
                pruebas=["pm.test('[Auth] 201 Created registro técnico', () => pm.response.to.have.status(201));"],
            ),
            req("0.11 Login Técnico para Control RBAC", "POST", "/v1/auth/login", [JSON, CORR, CANAL],
                {"email": "tecnico.qa.{{sufijo}}@quickpatch.test", "password": "{{clave}}"}, login_tecnico),
            req(
                "0.12 Login Administrador de Tenant (Opcional)",
                "POST",
                "/v1/auth/login",
                [JSON, CORR, CANAL],
                {"email": "{{adminEmail}}", "password": "{{adminPassword}}"},
                pruebas=[
                    "pm.test('[Auth] Login de administrador exitoso (200 OK)', () => pm.response.to.have.status(200));",
                    "pm.collectionVariables.set('adminToken', pm.response.json().accessToken);",
                ],
                con_admin=True,
            ),
            req(
                "0.13 Aprobación de Proveedor 1 por Administrador (Opcional)",
                "POST",
                "/v1/admin/technicians/{{prov1Id}}/approve",
                [CORR, auth("adminToken")],
                pruebas=["pm.test('[Admin] Proveedor 1 aprobado exitosamente', () => pm.response.to.have.status(200));"],
                con_admin=True,
            ),
        ],
    })

    # -------------------------------------------------------------------------
    # 1. Registro de Técnico en Equipo (RN-TP3 / SCRUM-36)
    # -------------------------------------------------------------------------
    t_registro_ok = [
        "pm.test('[RN-TP3 / RF-16] 201 Created al dar de alta técnico en equipo', () => {",
        "  pm.response.to.have.status(201);",
        "  const json = pm.response.json();",
        "  pm.expect(json).to.have.property('userId');",
        "  pm.expect(json.role).to.eql('tecnico');",
        "  pm.expect(json.verificationStatus).to.eql('pendiente');",
        "  pm.expect(json.noticeEmitted).to.eql('technician.registered');",
        "  pm.collectionVariables.set('teamTechId', json.userId);",
        "});",
        "pm.test('[RN-TP3] El técnico hereda estado pendiente y rol técnico', () => {",
        "  const json = pm.response.json();",
        "  pm.expect(json.verificationStatus).to.eql('pendiente');",
        "  pm.expect(json.role).to.eql('tecnico');",
        "});",
    ]

    carpetas.append({
        "name": "1. Registro de Técnico en Equipo del Proveedor",
        "item": [
            req(
                "1.1 Proveedor 1 registra un técnico en su equipo",
                "POST",
                "/v1/providers/me/technicians",
                [JSON, CORR, auth("tokenProv1")],
                {
                    "fullName": "Pedro Ramirez (Equipo)",
                    "email": "pedro.ramirez.{{sufijo}}@quickpatch.test",
                    "documentId": "{{docTeamTech}}",
                    "phone": "+573105556677",
                    "specialtyId": "{{specialtyId}}",
                },
                pruebas=t_registro_ok,
                previo=["pm.collectionVariables.set('docTeamTech', 'CC-' + String(Date.now()).slice(-8));"],
            ),
        ],
    })

    # -------------------------------------------------------------------------
    # 2. Consulta y Filtros de Equipo (RN-TP4 / DD §8.3.14)
    # -------------------------------------------------------------------------
    t_list_all = [
        "pm.test('[RN-TP4] 200 OK al consultar equipo de técnicos', () => {",
        "  pm.response.to.have.status(200);",
        "  const json = pm.response.json();",
        "  pm.expect(json).to.have.property('items');",
        "  pm.expect(json.items).to.be.an('array');",
        "  pm.expect(json.total).to.be.at.least(1);",
        "});",
        "pm.test('[RF-16] Técnico registrado aparece en la lista con datos completos', () => {",
        "  const json = pm.response.json();",
        "  const correoBuscado = 'pedro.ramirez.' + pm.collectionVariables.get('sufijo') + '@quickpatch.test';",
        "  const tech = json.items.find(t => t.email === correoBuscado);",
        "  pm.expect(tech).to.exist;",
        "  pm.expect(tech.fullName).to.eql('Pedro Ramirez (Equipo)');",
        "  pm.expect(tech.verificationStatus).to.eql('pendiente');",
        "});",
    ]

    t_list_inactivos = [
        "pm.test('[Filtro status=inactivo] 200 OK y técnico pendiente listado', () => {",
        "  pm.response.to.have.status(200);",
        "  const json = pm.response.json();",
        "  const correoBuscado = 'pedro.ramirez.' + pm.collectionVariables.get('sufijo') + '@quickpatch.test';",
        "  const tech = json.items.find(t => t.email === correoBuscado);",
        "  pm.expect(tech).to.exist;",
        "  pm.expect(tech.verificationStatus).to.eql('pendiente');",
        "});",
    ]

    t_list_activos = [
        "pm.test('[Filtro status=activo] 200 OK y técnico pendiente NO listado como activo', () => {",
        "  pm.response.to.have.status(200);",
        "  const json = pm.response.json();",
        "  const correoBuscado = 'pedro.ramirez.' + pm.collectionVariables.get('sufijo') + '@quickpatch.test';",
        "  const tech = json.items.find(t => t.email === correoBuscado);",
        "  pm.expect(tech).to.be.undefined;",
        "  pm.expect(json.total).to.eql(0);",
        "});",
        "pm.test('[RN-TP1] Solo técnicos aprobados por admin_tenant pueden estar activos', () => {",
        "  pm.expect(pm.response.json().total).to.eql(0);",
        "});",
    ]

    carpetas.append({
        "name": "2. Consulta y Filtros de Equipo",
        "item": [
            req("2.1 Proveedor 1 consulta la lista completa de su equipo", "GET", "/v1/providers/me/technicians",
                [JSON, CORR, auth("tokenProv1")], None, t_list_all),
            req("2.2 Proveedor 1 filtra equipo por status=inactivo", "GET", "/v1/providers/me/technicians?status=inactivo",
                [JSON, CORR, auth("tokenProv1")], None, t_list_inactivos),
            req("2.3 Proveedor 1 filtra equipo por status=activo", "GET", "/v1/providers/me/technicians?status=activo",
                [JSON, CORR, auth("tokenProv1")], None, t_list_activos),
        ],
    })

    # -------------------------------------------------------------------------
    # 3. Filtros Negativos y Validaciones de Negocio
    # -------------------------------------------------------------------------
    t_val_incompleto = [
        "pm.test('[Validación] 400 Bad Request ante datos faltantes', () => {",
        "  pm.response.to.have.status(400);",
        "});",
        *problem,
        *tipo("validacion-solicitud"),
    ]

    t_doc_dup = [
        "pm.test('[RN-U1] 409 Conflict ante documento de identidad duplicado', () => {",
        "  pm.response.to.have.status(409);",
        "});",
        *problem,
        *tipo("documento-registrado"),
    ]

    t_mail_dup = [
        "pm.test('[RN-U1] 409 Conflict ante correo electrónico duplicado', () => {",
        "  pm.response.to.have.status(409);",
        "});",
        *problem,
        *tipo("correo-registrado"),
    ]

    carpetas.append({
        "name": "3. Validaciones de Negocio y Errores",
        "item": [
            req(
                "3.1 Validación: Proveedor envía solicitud incompleta -> 400 Bad Request",
                "POST",
                "/v1/providers/me/technicians",
                [JSON, CORR, auth("tokenProv1")],
                {"fullName": "Incompleto"},
                t_val_incompleto,
            ),
            req(
                "3.2 Unicidad: Proveedor intenta registrar documento duplicado -> 409 Conflict",
                "POST",
                "/v1/providers/me/technicians",
                [JSON, CORR, auth("tokenProv1")],
                {
                    "fullName": "Otro Tecnico",
                    "email": "otro.correo.{{sufijo}}@quickpatch.test",
                    "documentId": "{{docTeamTech}}",
                    "phone": "+573101112233",
                    "specialtyId": "{{specialtyId}}",
                },
                t_doc_dup,
            ),
            req(
                "3.3 Unicidad: Proveedor intenta registrar correo duplicado -> 409 Conflict",
                "POST",
                "/v1/providers/me/technicians",
                [JSON, CORR, auth("tokenProv1")],
                {
                    "fullName": "Otro Nombre",
                    "email": "pedro.ramirez.{{sufijo}}@quickpatch.test",
                    "documentId": "CC-999999999",
                    "phone": "+573101112233",
                    "specialtyId": "{{specialtyId}}",
                },
                t_mail_dup,
            ),
        ],
    })

    # -------------------------------------------------------------------------
    # 4. Seguridad RBAC y Aislamiento Multi-Tenant
    # -------------------------------------------------------------------------
    t_rbac_cliente = [
        "pm.test('[RBAC] 403 Forbidden para cliente intentando gestionar equipo', () => {",
        "  pm.response.to.have.status(403);",
        "});",
        *problem,
        *tipo("no-autorizado"),
    ]

    t_rbac_tecnico = [
        "pm.test('[RBAC] 403 Forbidden para técnico intentando registrar equipo', () => {",
        "  pm.response.to.have.status(403);",
        "});",
        *problem,
        *tipo("no-autorizado"),
    ]

    t_anonimo = [
        "pm.test('[Seguridad] 401 Unauthorized ante solicitud anónima (IDN-017)', () => {",
        "  pm.response.to.have.status(401);",
        "});",
        *problem,
        *tipo("no-autenticado"),
    ]

    t_intra_tenant = [
        "pm.test('[RN-TP4 / Confidencialidad] 200 OK para Proveedor 2 sin ver técnicos de Proveedor 1', () => {",
        "  pm.response.to.have.status(200);",
        "  const json = pm.response.json();",
        "  pm.expect(json.total).to.eql(0);",
        "  pm.expect(json.items).to.be.an('array').that.is.empty;",
        "});",
        "pm.test('[Aislamiento Intra-Tenant] Cero fuga de técnicos entre proveedores del mismo tenant', () => {",
        "  pm.expect(pm.response.json().total).to.eql(0);",
        "});",
    ]

    t_multi_tenant = [
        "pm.test('[SAD AC6-E2 / RLS] 200 OK para Proveedor Beta con cero técnicos de Tenant Alfa', () => {",
        "  pm.response.to.have.status(200);",
        "  const json = pm.response.json();",
        "  pm.expect(json.total).to.eql(0);",
        "  pm.expect(json.items).to.be.an('array').that.is.empty;",
        "});",
        "pm.test('[Multi-Tenancy] Row-Level Security garantiza aislamiento estricto cross-tenant', () => {",
        "  pm.expect(pm.response.json().total).to.eql(0);",
        "});",
    ]

    carpetas.append({
        "name": "4. Control de Acceso RBAC y Aislamiento Multi-Tenant",
        "item": [
            req(
                "4.1 Control RBAC: Cliente intenta dar de alta técnico en equipo -> 403 Forbidden",
                "POST",
                "/v1/providers/me/technicians",
                [JSON, CORR, auth("tokenCliente")],
                {
                    "fullName": "Intento Ilegal",
                    "email": "ilegal.{{sufijo}}@quickpatch.test",
                    "documentId": "CC-777777777",
                    "phone": "+573100000000",
                    "specialtyId": "{{specialtyId}}",
                },
                t_rbac_cliente,
            ),
            req(
                "4.2 Control RBAC: Técnico intenta dar de alta técnico en equipo -> 403 Forbidden",
                "POST",
                "/v1/providers/me/technicians",
                [JSON, CORR, auth("tokenTecnico")],
                {
                    "fullName": "Intento Tecnico",
                    "email": "ilegal2.{{sufijo}}@quickpatch.test",
                    "documentId": "CC-888888888",
                    "phone": "+573100000000",
                    "specialtyId": "{{specialtyId}}",
                },
                t_rbac_tecnico,
            ),
            req("4.3 Seguridad: Consulta anónima sin token -> 401 Unauthorized", "GET",
                "/v1/providers/me/technicians", [JSON, CORR], None, t_anonimo),
            req("4.4 Aislamiento Intra-Tenant (RN-TP4): Proveedor 2 no ve técnicos de Proveedor 1", "GET",
                "/v1/providers/me/technicians", [JSON, CORR, auth("tokenProv2")], None, t_intra_tenant),
            req("4.5 Aislamiento Multi-Tenant (RLS): Proveedor Beta no ve técnicos de Tenant Alfa", "GET",
                "/v1/providers/me/technicians", [JSON, CORR, auth("tokenProvBeta")], None, t_multi_tenant),
        ],
    })

    coleccion = {
        "info": {
            "_postman_id": "scrum-99-equipo-proveedor-qa",
            "name": "QUICKPATCH — Gestión de Equipo de Técnicos (SCRUM-99 / HU SCRUM-36)",
            "description": (
                "Suite E2E para RF-16, RN-TP3 y RN-TP4: Registro de técnicos en equipo por parte de proveedores, "
                "filtros activo/inactivo, unicidad, control RBAC y aislamiento multi-tenant con RLS. "
                "Genera cuentas de proveedor, cliente y técnico de forma dinámica en cada corrida. "
                "QA Lead: Katherine Bravo."
            ),
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "item": carpetas,
        "variable": [
            {"key": "baseUrl", "value": "http://localhost:8080"},
            {"key": "adminEmail", "value": ""},
            {"key": "adminPassword", "value": ""},
            {"key": "adminToken", "value": ""},
            {"key": "specialtyId", "value": "3f1c2a4e-8d7b-4c1a-9e2f-5b6a7c8d9e01"},
            {"key": "sufijo", "value": ""},
            {"key": "clave", "value": ""},
            {"key": "docProv1", "value": ""},
            {"key": "prov1Id", "value": ""},
            {"key": "docProv2", "value": ""},
            {"key": "prov2Id", "value": ""},
            {"key": "docProvBeta", "value": ""},
            {"key": "docTecnico", "value": ""},
            {"key": "docTeamTech", "value": ""},
            {"key": "tokenProv1", "value": ""},
            {"key": "tokenProv2", "value": ""},
            {"key": "tokenProvBeta", "value": ""},
            {"key": "tokenCliente", "value": ""},
            {"key": "tokenTecnico", "value": ""},
            {"key": "teamTechId", "value": ""},
        ],
    }

    destino = pathlib.Path(__file__).parent / "scrum-99-equipo-proveedor.postman_collection.json"
    destino.write_text(json.dumps(coleccion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Colección generada con éxito en: {destino}")


if __name__ == "__main__":
    generar()
