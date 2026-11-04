"""Genera la colección de la edición del perfil propio (SCRUM-614, historia SCRUM-609) contra QA.

Uso: python tests/e2e/generar-scrum614-perfil.py
Escribe scrum-614-perfil.postman_collection.json. Reutiliza los pasos de generar-scrum490-96-cotizacion-evidencia.py y
generar-scrum75-solicitud-empresa.py, que también regeneran sus colecciones sin cambios.

Contrato: identity.v1.yaml 1.9.0 (PATCH /v1/users/me: fullName de 2 a 150 y phone de 7 a 30 o null, sin campos de más).
Casos PER-001 a PER-018 del TD 7.2; PER-019 a PER-022 son de pantalla. Datos propios: cliente, otro cliente, técnico
aprobado, técnico pendiente, empresa_contacto y cliente del tenant Beta. Al admin_tenant de QA solo se le reenvía su
mismo nombre, para no cambiar sus datos. Necesita al administrador del tenant (adminEmail y adminPassword, secretos de
QA que nunca van al repositorio). Correr con --reporters cli: el reporte JSON de Newman guarda tokens.
"""
import importlib.util
import json
import pathlib

AQUI = pathlib.Path(__file__).parent


def cargar(nombre, archivo):
    spec = importlib.util.spec_from_file_location(nombre, AQUI / archivo)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


base = cargar("base", "generar-scrum490-96-cotizacion-evidencia.py")
empresa = cargar("empresa", "generar-scrum75-solicitud-empresa.py")

JSON, CORR, BETA = base.JSON, base.CORR, base.BETA
auth, req, estado, error = base.auth, base.req, base.estado, base.error

HISTORIA = "SCRUM-614"
PERFIL = "/v1/users/me"


def editar(nombre, token, cuerpo, pruebas, headers=()):
    return req(nombre, "PATCH", PERFIL, [JSON, CORR, *headers] + ([auth(token)] if token else []), cuerpo, pruebas=pruebas)


def perfil(nombre, token, pruebas):
    return req(nombre, "GET", PERFIL, [CORR, auth(token)], pruebas=estado(200) + ["const u = pm.response.json();", *pruebas])


def editado(**esperado):
    return estado(200) + [
        "pm.test('el perfil devuelto trae los datos nuevos', () => {",
        "  const u = pm.response.json();",
        *(f"  pm.expect(u.{k}).to.eql({v});" for k, v in esperado.items()),
        "});",
    ]


def con_errores(campo):
    return error(400) + [
        "pm.test('PER-017: errores por campo', () => pm.expect(pm.response.json()).to.have.property('errors'));",
        f"pm.test('error en {campo}', () => pm.expect(pm.response.json().errors).to.have.property('{campo}'));",
    ]


def js(texto):
    return json.dumps(texto, ensure_ascii=False)


# Sin espacios en los extremos: Identity los recorta (PER-009) y el largo cambiaría.
NOMBRE_150 = ("Ana María de los Ángeles " * 7)[:149] + "z"
NOMBRE_151 = NOMBRE_150 + "s"
TEL_30 = "+57 300 123 4567 ext 123456789"
assert len(NOMBRE_150) == 150 and NOMBRE_150 == NOMBRE_150.strip() and len(TEL_30) == 30, (len(NOMBRE_150), len(TEL_30))

preparacion = base.preparacion(HISTORIA)
preparacion["name"] = "0. Preparación: clientes, técnicos, empresa y cliente de Beta"
preparacion["item"] += [
    empresa.registrar_empresa("Empresa", "empresa614.qa", "nitEmpresa", "empresaId"),
    empresa.login_empresa("la empresa", "empresa614.qa.{{sufijo}}@quickpatch.test", "empresaToken", "empresaId"),
    perfil("Perfil del otro cliente antes de la prueba", "otroClienteToken", [
        "pm.collectionVariables.set('otroClienteId', u.id);",
        "pm.collectionVariables.set('otroClienteNombre', u.fullName);",
    ]),
    perfil("Perfil del cliente antes de la prueba", "clienteToken", [
        "pm.collectionVariables.set('clienteCorreo', u.email);",
        "pm.test('rol cliente', () => pm.expect(u.role).to.eql('cliente'));",
    ]),
    req("Tenant del cliente de Beta (claim tenant_id de su token)", "GET", PERFIL, [CORR, BETA, auth("betaToken")],
        pruebas=estado(200) + [
            "const claims = JSON.parse(atob(pm.collectionVariables.get('betaToken').split('.')[1].replace(/-/g, '+').replace(/_/g, '/')));",
            "pm.test('el token trae tenant_id', () => pm.expect(claims.tenant_id).to.be.a('string'));",
            "pm.collectionVariables.set('tenantBeta', claims.tenant_id);",
        ]),
]

positivos = {
    "name": "1. Cada rol edita su propio perfil",
    "item": [
        editar("PER-001: el cliente cambia su nombre", "clienteToken", {"fullName": "Cliente Editado QA"},
               editado(fullName=js("Cliente Editado QA"))),
        perfil("PER-001: GET /v1/users/me devuelve el nombre nuevo", "clienteToken", [
            "pm.test('nombre nuevo', () => pm.expect(u.fullName).to.eql('Cliente Editado QA'));",
        ]),
        editar("PER-002: cambia su teléfono", "clienteToken", {"phone": "3101234567"}, editado(phone=js("3101234567"))),
        editar("PER-003: borra su teléfono", "clienteToken", {"phone": None}, editado(phone="null")),
        editar("PER-004: nombre y teléfono a la vez", "clienteToken", {"fullName": "Cliente Doble QA", "phone": "3109876543"},
               editado(fullName=js("Cliente Doble QA"), phone=js("3109876543"))),
        editar("PER-005: el técnico edita su perfil", "tecnicoToken", {"phone": "3201112233"},
               editado(phone=js("3201112233"), role=js("tecnico"))),
        editar("PER-005: el empresa_contacto edita su perfil", "empresaToken", {"fullName": "Contacto Editado QA"},
               editado(fullName=js("Contacto Editado QA"), role=js("empresa_contacto"))),
        perfil("Nombre actual del admin_tenant", "adminToken", [
            "pm.collectionVariables.set('adminNombre', u.fullName);",
        ]),
        editar("PER-005: el admin_tenant reenvía su mismo nombre", "adminToken", {"fullName": "{{adminNombre}}"},
               estado(200) + [
                   "pm.test('mismo nombre y rol admin_tenant', () => {",
                   "  pm.expect(pm.response.json().fullName).to.eql(pm.collectionVariables.get('adminNombre'));",
                   "  pm.expect(pm.response.json().role).to.eql('admin_tenant');",
                   "});",
               ]),
    ],
}

limites = {
    "name": "2. Validaciones y límites",
    "item": [
        editar("PER-006: cuerpo vacío → 400", "clienteToken", {}, error(400)),
        editar("PER-007: nombre de 1 carácter → 400", "clienteToken", {"fullName": "A"}, con_errores("fullName")),
        editar("PER-007: nombre de 151 caracteres → 400", "clienteToken", {"fullName": NOMBRE_151}, con_errores("fullName")),
        editar("PER-007: nombre de 2 caracteres → 200", "clienteToken", {"fullName": "Al"}, editado(fullName=js("Al"))),
        editar("PER-007: nombre de 150 caracteres → 200", "clienteToken", {"fullName": NOMBRE_150},
               editado(fullName=js(NOMBRE_150))),
        editar("PER-008: teléfono de 6 caracteres → 400", "clienteToken", {"phone": "123456"}, con_errores("phone")),
        editar("PER-008: teléfono de 31 caracteres → 400", "clienteToken", {"phone": TEL_30 + "0"}, con_errores("phone")),
        editar("PER-008: teléfono de 7 caracteres → 200", "clienteToken", {"phone": "6012345"}, editado(phone=js("6012345"))),
        editar("PER-008: teléfono de 30 caracteres → 200", "clienteToken", {"phone": TEL_30}, editado(phone=js(TEL_30))),
        editar("PER-009: nombre vacío → 400", "clienteToken", {"fullName": ""}, con_errores("fullName")),
        editar("PER-009: nombre con solo espacios → 400", "clienteToken", {"fullName": "   "}, con_errores("fullName")),
    ],
}

inmodificables = {
    "name": "3. Campos que no se editan y fugas",
    "item": [
        editar("PER-010: cambiar el correo → 400", "clienteToken",
               {"fullName": "Cliente Correo QA", "email": "otro.correo.{{sufijo}}@quickpatch.test"}, error(400)),
        editar("PER-011: cambiar el rol → 400", "clienteToken", {"role": "admin_tenant"}, error(400)),
        editar("PER-012: cambiar el tenant → 400", "clienteToken", {"tenant_id": "{{tenantBeta}}"}, error(400)),
        perfil("PER-010 a PER-012: correo, rol y nombre no cambiaron", "clienteToken", [
            "pm.test('mismo correo, rol cliente y el último nombre válido', () => {",
            "  pm.expect(u.email).to.eql(pm.collectionVariables.get('clienteCorreo'));",
            "  pm.expect(u.role).to.eql('cliente');",
            f"  pm.expect(u.fullName).to.eql({js(NOMBRE_150)});",
            "});",
        ]),
        req("PER-012: el cliente sigue entrando en su tenant", "POST", "/v1/auth/login", [JSON, CORR, base.CANAL],
            {"email": "cliente.qa.{{sufijo}}@quickpatch.test", "password": "{{clave}}"},
            pruebas=estado(200) + ["pm.test('rol cliente', () => pm.expect(pm.response.json().user.role).to.eql('cliente'));"]),
        editar("PER-013: el técnico pendiente se aprueba solo → 400", "otroTecnicoToken",
               {"verificationStatus": "aprobado"}, error(400)),
        perfil("PER-013: el técnico sigue pendiente", "otroTecnicoToken", [
            "pm.test('pendiente', () => pm.expect(u.verificationStatus).to.eql('pendiente'));",
        ]),
        editar("PER-014: el cliente envía el id del otro cliente → 400", "clienteToken",
               {"id": "{{otroClienteId}}", "fullName": "Nombre Ajeno QA"}, error(400)),
        perfil("PER-014: el otro cliente no cambió", "otroClienteToken", [
            "pm.test('mismo nombre', () => pm.expect(u.fullName).to.eql(pm.collectionVariables.get('otroClienteNombre')));",
        ]),
        editar("PER-015: X-Tenant-Id de Beta se ignora", "clienteToken", {"fullName": "Cliente Con Cabecera QA"},
               editado(fullName=js("Cliente Con Cabecera QA")),
               headers=[{"key": "X-Tenant-Id", "value": "{{tenantBeta}}"}]),
        perfil("PER-015: el cambio quedó en el cliente de su propio tenant", "clienteToken", [
            "pm.test('nombre nuevo en el tenant principal', () => pm.expect(u.fullName).to.eql('Cliente Con Cabecera QA'));",
        ]),
        req("PER-015: el cliente de Beta no cambió", "GET", PERFIL, [CORR, BETA, auth("betaToken")],
            pruebas=estado(200) + [
                "pm.test('nombre de registro', () => pm.expect(pm.response.json().fullName).to.eql('Prueba QA cliente del tenant Beta'));",
            ]),
        editar("PER-016: sin sesión → 401", None, {"fullName": "Sin Sesion QA"}, estado(401)),
        perfil("PER-018: el mismo token sigue sirviendo tras editar", "clienteToken", [
            "pm.test('sin volver a iniciar sesión', () => pm.expect(u.role).to.eql('cliente'));",
        ]),
    ],
}

coleccion = base.coleccion(
    "QUICKPATCH — SCRUM-614 Edición del perfil propio",
    "SCRUM-609 (RF-01, RF-04) contra QA, con identity.v1.yaml 1.9.0 (PATCH /v1/users/me). Casos PER-001 a PER-018 del "
    "TD 7.2 con datos propios: cliente, técnico, empresa_contacto y admin_tenant editan su nombre y teléfono; límites de "
    "2 a 150 y de 7 a 30 caracteres; cuerpo vacío y nombre en blanco (400); correo, rol, tenant, verificación e id ajeno "
    "responden 400 sin cambiar nada; X-Tenant-Id falsificado se ignora; sin sesión 401; el token sigue sirviendo. "
    "Variables: baseUrl, adminEmail y adminPassword (secretos de QA, nunca en el repositorio). Correr con --reporters "
    "cli: el reporte JSON de Newman guarda tokens.",
    [preparacion, positivos, limites, inmodificables, base.limpieza],
)

destino = AQUI / "scrum-614-perfil.postman_collection.json"
destino.write_text(json.dumps(coleccion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Colección escrita en {destino}")
