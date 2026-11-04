"""Genera la colección de la recuperación de contraseña (SCRUM-627, historia SCRUM-623) contra QA.

Uso: python tests/e2e/generar-scrum627-recuperacion.py
Escribe scrum-627-recuperacion.postman_collection.json. Reutiliza los pasos de generar-scrum490-96-cotizacion-evidencia.py,
que también regenera su colección sin cambios.

Contrato: identity.v1.yaml 1.10.0 (POST /v1/auth/password-recovery, GET /v1/admin/password-recovery-requests,
POST /v1/admin/password-recovery-requests/{id}/link y POST /v1/auth/password-recovery/confirm).
Casos REC-001 a REC-021 y REC-026 del TD 7.2, con datos propios: tres clientes, un técnico, un proveedor con un técnico
de su equipo que nunca usó la invitación y un cliente del tenant Beta. REC-007 desactiva Beta unos segundos con el
administrador de la plataforma y lo vuelve a activar (igual que scrum-511); sin platformAdminEmail se omite.
Fuera de la colección: REC-015 (habría que esperar 1 hora a que venza el enlace), REC-022 (Loki), REC-027 (base de datos)
y REC-023 a REC-025 (pantallas). REC-009 y REC-012 se prueban desde el tenant principal: no hay administrador de Beta.

El límite es de 3 pedidos por correo por hora. Los correos son nuevos en cada corrida, salvo el del admin_tenant
(REC-006): la colección no se debe correr más de 3 veces en una hora. Necesita al administrador del tenant
(adminEmail y adminPassword, secretos de QA que nunca van al repositorio). Correr con --reporters cli: el reporte JSON
de Newman guarda tokens y los enlaces de recuperación.
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

JSON, CORR, CANAL, BETA = base.JSON, base.CORR, base.CANAL, base.BETA
auth, req, estado, error, reintentar = base.auth, base.req, base.estado, base.error, base.reintentar

HISTORIA = "SCRUM-627"
PEDIR = "/v1/auth/password-recovery"
CONFIRMAR = "/v1/auth/password-recovery/confirm"
SOLICITUDES = "/v1/admin/password-recovery-requests"
# NIT del tenant Beta de QA (evidencias/tenant-desactivado-qa-2026-11-02.txt).
NIT_BETA = "900999001-1"
CON_PLATAFORMA = ["if (!pm.variables.get('platformAdminEmail')) { pm.execution.skipRequest(); }"]
CON_BETA = CON_PLATAFORMA + ["if (!pm.collectionVariables.get('betaId')) { pm.execution.skipRequest(); }"]


def correo(prefijo):
    return prefijo + ".{{sufijo}}@quickpatch.test"


def pedir(nombre, email, pruebas, headers=(CANAL,), previo=()):
    return req(nombre, "POST", PEDIR, [JSON, CORR, *headers], {"email": email}, pruebas=pruebas, previo=previo)


def aceptado(extra=()):
    return estado(202) + list(extra)


def confirmar(nombre, token, clave, pruebas, headers=(CANAL,)):
    return req(nombre, "POST", CONFIRMAR, [JSON, CORR, *headers], {"token": token, "password": clave}, pruebas=pruebas)


def enlace_invalido():
    return error(400, "enlace-invalido")


def login(nombre, email, clave, pruebas, headers=(CANAL,)):
    return req(nombre, "POST", "/v1/auth/login", [JSON, CORR, *headers], {"email": email, "password": clave}, pruebas=pruebas)


def entra(nombre, email, variable, rol, clave="{{clave}}", headers=(CANAL,)):
    return login(f"Login del {nombre}", email, clave, [
        f"pm.test('200 con rol {rol}', () => {{",
        "  pm.response.to.have.status(200);",
        f"  pm.expect(pm.response.json().user.role).to.eql('{rol}');",
        "});",
        f"pm.collectionVariables.set('{variable}', pm.response.json().accessToken);",
    ], headers=headers)


def buscar(nombre, email, pruebas, token="adminToken"):
    """Recorre las páginas de solicitudes pendientes hasta encontrar el correo o acabar; deja `item` (o undefined)."""
    return req(nombre, "GET", SOLICITUDES + "?page={{pagina}}&size=100", [CORR, auth(token)],
               previo=["if (!pm.collectionVariables.get('pagina')) { pm.collectionVariables.set('pagina', 1); }"],
               pruebas=estado(200) + [
                   "const cuerpo = pm.response.json();",
                   "const pagina = Number(pm.collectionVariables.get('pagina'));",
                   f"const buscado = pm.variables.replaceIn('{email}').toLowerCase();",
                   "const item = cuerpo.items.find(i => i.email.toLowerCase() === buscado);",
                   "pm.test('REC-008: de la más antigua a la más reciente y sin tokens', () => {",
                   "  const fechas = cuerpo.items.map(i => Date.parse(i.requestedAt));",
                   "  fechas.forEach((f, k) => k === 0 || pm.expect(f).to.be.at.least(fechas[k - 1]));",
                   "  cuerpo.items.forEach(i => {",
                   "    pm.expect(i).to.not.have.property('token');",
                   "    pm.expect(i).to.not.have.property('link');",
                   "  });",
                   "});",
                   "if (!item && pagina * cuerpo.size < cuerpo.totalItems) {",
                   "  pm.collectionVariables.set('pagina', pagina + 1);",
                   "  pm.execution.setNextRequest(pm.info.requestId);",
                   "} else {",
                   "  pm.collectionVariables.unset('pagina');",
                   *("  " + linea for linea in pruebas),
                   "}",
               ])


def encontrada(variable, rol, extra=()):
    return [
        f"pm.test('la solicitud está pendiente con rol {rol}', () => {{",
        "  pm.expect(item, 'solicitud en la lista').to.be.ok;",
        f"  pm.expect(item.role).to.eql('{rol}');",
        "  pm.expect(item.id).to.be.a('string');",
        "});",
        f"if (item) {{ pm.collectionVariables.set('{variable}', item.id); }}",
        *extra,
    ]


def ausente(caso, descripcion):
    return [f"pm.test('{caso}: {descripcion}', () => pm.expect(item).to.be.undefined);"]


def generar(nombre, solicitud, variable, pruebas=()):
    return req(nombre, "POST", SOLICITUDES + "/{{" + solicitud + "}}/link", [CORR, auth("adminToken")],
               pruebas=estado(201) + [
                   "const e = pm.response.json();",
                   "pm.test('enlace con token y vencimiento a 1 hora', () => {",
                   "  pm.expect(e.token).to.be.a('string').and.not.empty;",
                   "  pm.expect(e.link).to.include(e.token);",
                   "  const minutos = (Date.parse(e.expiresAt) - Date.now()) / 60000;",
                   "  pm.expect(minutos).to.be.within(55, 65);",
                   "});",
                   f"pm.collectionVariables.set('{variable}', e.token);",
                   *pruebas,
               ])


def recuperar(nombre, email, rol, solicitud, enlace):
    """Pedido, solicitud en la lista del administrador y enlace: los pasos que se repiten para cada cuenta."""
    return [
        pedir(f"{nombre} pide recuperar la contraseña", email, aceptado()),
        buscar(f"El administrador ve la solicitud del {nombre}", email, encontrada(solicitud, rol)),
        generar(f"El administrador genera el enlace del {nombre}", solicitud, enlace),
    ]


nueva_clave = [
    "if (!pm.collectionVariables.get('claveNueva')) {",
    "  // Como la clave de la corrida: se genera al vuelo y no se guarda en ningún lado.",
    "  pm.collectionVariables.set('claveNueva', 'Qn_' + Math.random().toString(36).slice(2, 12) + '!Bb8');",
    "}",
]

_prep = base.preparacion(HISTORIA)["item"]
assert _prep[0]["name"] == "Login del administrador del tenant" and _prep[1]["name"].startswith("Categoría"), _prep[:2]
_prep[0]["event"][0]["script"]["exec"] += nueva_clave

preparacion = {
    "name": "0. Preparación: clientes, técnico, proveedor con equipo y cliente de Beta",
    "item": [
        _prep[0],
        _prep[1],
        req("Registro de un técnico", "POST", "/v1/auth/register/technician", [JSON, CORR, CANAL],
            {"email": correo("tecnico627.qa"), "password": "{{clave}}", "fullName": f"Técnico {HISTORIA}",
             "phone": "3007654341", "documentId": "{{docTecnico}}", "specialtyId": "{{categoriaId}}", "role": "tecnico"},
            previo=["pm.collectionVariables.set('docTecnico', String(Date.now()).slice(-10));"], pruebas=estado(201)),
        entra("técnico", correo("tecnico627.qa"), "tecnicoToken", "tecnico"),
        req("Registro del proveedor", "POST", "/v1/auth/register/technician", [JSON, CORR, CANAL],
            {"email": correo("proveedor627.qa"), "password": "{{clave}}", "fullName": f"Proveedor {HISTORIA}",
             "phone": "3007654342", "documentId": "{{docProveedor}}", "specialtyId": "{{categoriaId}}", "role": "proveedor"},
            previo=["pm.collectionVariables.set('docProveedor', String(Date.now() + 7).slice(-10));"],
            pruebas=estado(201) + ["pm.collectionVariables.set('proveedorId', pm.response.json().id);"]),
        req("El administrador aprueba al proveedor", "POST", "/v1/admin/technicians/{{proveedorId}}/approve",
            [CORR, auth("adminToken")], pruebas=estado(200)),
        entra("proveedor", correo("proveedor627.qa"), "proveedorToken", "proveedor"),
        req("El proveedor da de alta un técnico de su equipo (no usa la invitación)", "POST", "/v1/providers/me/technicians",
            [JSON, CORR, auth("proveedorToken")],
            {"email": correo("equipo627.qa"), "fullName": f"Técnico del equipo {HISTORIA}", "phone": "3007654343",
             "documentId": "{{docEquipo}}", "specialtyId": "{{categoriaId}}"},
            previo=["pm.collectionVariables.set('docEquipo', String(Date.now() + 13).slice(-10));"],
            pruebas=estado(201) + ["pm.collectionVariables.set('invitacionEquipo', pm.response.json().invitation.token);"]),
        base.registro_cliente("cliente", "rec1.qa"),
        base.registro_cliente("cliente bloqueado", "rec2.qa"),
        base.registro_cliente("cliente del límite", "rec3.qa"),
        entra("cliente", correo("rec1.qa"), "clienteToken", "cliente"),
        base.registro_cliente("cliente del tenant Beta", "rec.beta.qa", headers=(JSON, CORR, BETA)),
    ],
}

pedido = {
    "name": "1. Pedido: misma respuesta siempre, límite y validaciones",
    "item": [
        pedir("REC-001: el cliente pide recuperar la contraseña", correo("rec1.qa"), aceptado([
            "pm.collectionVariables.set('cuerpo202', pm.response.text());",
            "pm.collectionVariables.set('tipo202', pm.response.headers.get('Content-Type') || '');",
        ])),
        pedir("REC-002: un correo que no existe → la misma respuesta", correo("no.existe.qa"), aceptado([
            "pm.test('mismo cuerpo y mismo Content-Type que REC-001', () => {",
            "  pm.expect(pm.response.text()).to.eql(pm.collectionVariables.get('cuerpo202'));",
            "  pm.expect(pm.response.headers.get('Content-Type') || '').to.eql(pm.collectionVariables.get('tipo202'));",
            "});",
        ])),
        buscar("REC-001 / REC-008: el administrador ve la solicitud", correo("rec1.qa"), encontrada("solicitud1", "cliente", [
            "if (item) { pm.collectionVariables.set('fecha1', item.requestedAt); }",
            "pm.test('sin el correo de REC-002', () => pm.expect(cuerpo.items.map(i => i.email)).to.not.include(pm.variables.replaceIn('" + correo("no.existe.qa") + "')));",
        ])),
        pedir("REC-003: el cliente la pide otra vez", correo("rec1.qa"), aceptado()),
        buscar("REC-003: sigue una sola solicitud, con la fecha nueva", correo("rec1.qa"), [
            "pm.test('misma solicitud, una sola vez y con fecha posterior', () => {",
            "  pm.expect(item, 'solicitud en la lista').to.be.ok;",
            "  pm.expect(item.id).to.eql(pm.collectionVariables.get('solicitud1'));",
            "  pm.expect(cuerpo.items.filter(i => i.email.toLowerCase() === buscado)).to.have.lengthOf(1);",
            "  pm.expect(Date.parse(item.requestedAt)).to.be.above(Date.parse(pm.collectionVariables.get('fecha1')));",
            "});",
        ]),
        *(pedir(f"REC-004: pedido {n} del cliente del límite", correo("rec3.qa"), aceptado()) for n in (1, 2, 3)),
        pedir("REC-004: el cuarto pedido en la hora → 429", correo("rec3.qa"), error(429, "demasiadas-solicitudes") + [
            "pm.test('Retry-After en segundos', () => pm.expect(Number(pm.response.headers.get('Retry-After'))).to.be.above(0));",
        ]),
        *(pedir(f"REC-004: pedido {n} del correo que no existe", correo("no.existe.qa"), aceptado()) for n in (2, 3)),
        pedir("REC-004: el cuarto del correo que no existe → 429 igual", correo("no.existe.qa"),
              error(429, "demasiadas-solicitudes") + [
                  "pm.test('Retry-After', () => pm.expect(pm.response.headers.get('Retry-After')).to.be.ok);",
              ]),
        pedir("REC-005: correo inválido → 400", "no-es-un-correo", error(400) + [
            "pm.test('error en email', () => pm.expect(pm.response.json().errors).to.have.property('email'));",
        ]),
        req("REC-005: un campo de más → 400", "POST", PEDIR, [JSON, CORR, CANAL],
            {"email": correo("rec1.qa"), "tenantId": "00000000-0000-0000-0000-000000000000"}, pruebas=error(400)),
        pedir("REC-006: el admin_tenant pide recuperar su clave → 202", "{{adminEmail}}", aceptado()),
        buscar("REC-006: no queda solicitud del administrador", "{{adminEmail}}",
               ausente("REC-006", "los administradores no usan este flujo")),
        pedir("REC-009: el cliente de Beta pide recuperar la suya", correo("rec.beta.qa"), aceptado(), headers=(BETA,)),
        buscar("REC-009: el administrador del tenant principal no la ve", correo("rec.beta.qa"),
               ausente("REC-009", "sin solicitudes de otro tenant")),
    ],
}

permisos = {
    "name": "2. Lista y enlace: permisos y otro tenant",
    "item": [
        req("REC-010: el cliente lista solicitudes → 403", "GET", SOLICITUDES, [CORR, auth("clienteToken")], pruebas=error(403)),
        req("REC-010: el técnico lista solicitudes → 403", "GET", SOLICITUDES, [CORR, auth("tecnicoToken")], pruebas=error(403)),
        req("REC-010: sin sesión → 401", "GET", SOLICITUDES, [CORR], pruebas=estado(401)),
        req("REC-010: el cliente genera un enlace → 403", "POST", SOLICITUDES + "/{{solicitud1}}/link",
            [CORR, auth("clienteToken")], pruebas=error(403)),
        req("REC-012: solicitud que no es del tenant → 404", "POST", SOLICITUDES + "/{{$guid}}/link",
            [CORR, auth("adminToken")], pruebas=error(404)),
    ],
}

enlace = {
    "name": "3. Enlace de un solo uso y contraseña nueva",
    "item": [
        generar("REC-011: el administrador genera el enlace", "solicitud1", "enlace1"),
        generar("REC-016: genera otro enlace para la misma solicitud", "solicitud1", "enlace2"),
        confirmar("REC-016: el enlace anterior ya no sirve", "{{enlace1}}", "{{claveNueva}}", enlace_invalido()),
        confirmar("REC-017: token inventado → 400", "token-inventado-{{$guid}}", "{{claveNueva}}", enlace_invalido()),
        confirmar("REC-017: el enlace válido usado desde Beta → 400 igual", "{{enlace2}}", "{{claveNueva}}", enlace_invalido(),
                  headers=(BETA,)),
        confirmar("REC-018: clave de 7 caracteres → 400", "{{enlace2}}", "Qp_1a!b", error(400) + [
            "pm.test('error en password', () => pm.expect(pm.response.json().errors).to.have.property('password'));",
        ]),
        confirmar("REC-013: el cliente define la clave nueva", "{{enlace2}}", "{{claveNueva}}", estado(204)),
        login("REC-013: entra con la clave nueva", correo("rec1.qa"), "{{claveNueva}}", estado(200)),
        login("REC-013: la clave anterior ya no sirve", correo("rec1.qa"), "{{clave}}", estado(401)),
        confirmar("REC-014: el mismo enlace por segunda vez → 400", "{{enlace2}}", "{{claveNueva}}", enlace_invalido()),
        req("REC-019: otro enlace después del cambio → 409", "POST", SOLICITUDES + "/{{solicitud1}}/link",
            [CORR, auth("adminToken")], pruebas=error(409, "transicion-invalida")),
        buscar("REC-019: la solicitud ya no está en la lista", correo("rec1.qa"),
               ausente("REC-019", "solicitud cerrada")),
        req("REC-020: el token de antes del cambio sigue sirviendo", "GET", "/v1/users/me", [CORR, auth("clienteToken")],
            pruebas=estado(200)),
    ],
}

bloqueo = {
    "name": "4. Cuenta bloqueada y técnico con la invitación sin usar",
    "item": [
        login("REC-021: intentos fallidos hasta bloquear la cuenta", correo("rec2.qa"), "Clave-Equivocada-1",
              reintentar("pm.response.code === 423", [
                  "pm.test('423 cuenta bloqueada', () => pm.response.to.have.status(423));",
              ], maximo=8, espera=0)),
        login("REC-021: con la clave correcta también 423", correo("rec2.qa"), "{{clave}}", estado(423)),
        *recuperar("cliente bloqueado", correo("rec2.qa"), "cliente", "solicitud2", "enlace3"),
        confirmar("REC-021: define la clave nueva", "{{enlace3}}", "{{claveNueva}}", estado(204)),
        login("REC-021: la cuenta queda desbloqueada", correo("rec2.qa"), "{{claveNueva}}", estado(200)),
        *recuperar("técnico del equipo", correo("equipo627.qa"), "tecnico", "solicitud3", "enlace4"),
        confirmar("REC-026: el técnico del equipo define su clave con el enlace", "{{enlace4}}", "{{claveNueva}}", estado(204)),
        req("REC-026: la invitación pendiente quedó usada", "POST", "/v1/auth/password/setup", [JSON, CORR, CANAL],
            {"token": "{{invitacionEquipo}}", "password": "{{clave}}"}, pruebas=enlace_invalido()),
        login("REC-026: entra con la clave nueva", correo("equipo627.qa"), "{{claveNueva}}", estado(200)),
    ],
}


def cambiar_beta(nombre, nuevo):
    return req(nombre, "PATCH", "/v1/platform/tenants/{{betaId}}", [JSON, CORR, auth("plataformaToken")],
               {"status": nuevo}, previo=CON_BETA,
               pruebas=[
                   f"pm.test('200 y Beta queda {nuevo}', () => {{",
                   "  pm.response.to.have.status(200);",
                   f"  pm.expect(pm.response.json().status).to.eql('{nuevo}');",
                   "});",
               ])


tenant_desactivado = {
    "name": "5. Tenant desactivado (REC-007, con el administrador de la plataforma)",
    "item": [
        req("Login del administrador de la plataforma", "POST", "/v1/auth/login", [JSON, CORR, CANAL],
            {"email": "{{platformAdminEmail}}", "password": "{{platformAdminPassword}}"}, previo=CON_PLATAFORMA,
            pruebas=[
                "pm.test('200 con rol admin_plataforma', () => {",
                "  pm.response.to.have.status(200);",
                "  pm.expect(pm.response.json().user.role).to.eql('admin_plataforma');",
                "});",
                "pm.collectionVariables.set('plataformaToken', pm.response.json().accessToken);",
            ]),
        req("Ubicar el tenant Beta por su NIT", "GET", "/v1/platform/tenants", [CORR, auth("plataformaToken")],
            previo=CON_PLATAFORMA,
            pruebas=estado(200) + [
                f"const beta = pm.response.json().find(t => t.nit === '{NIT_BETA}');",
                "const partes = pm.collectionVariables.get('plataformaToken').split('.')[1].replace(/-/g, '+').replace(/_/g, '/');",
                "const yo = JSON.parse(CryptoJS.enc.Base64.parse(partes + '='.repeat((4 - partes.length % 4) % 4)).toString(CryptoJS.enc.Utf8));",
                "pm.test('Beta existe y no es el tenant de la plataforma', () => {",
                "  pm.expect(beta, 'tenant Beta de QA').to.be.ok;",
                "  pm.expect(beta.id).to.not.eql(yo.tenant_id);",
                "});",
                "// Sin Beta no se sigue: la colección nunca desactiva otro tenant.",
                "if (beta && beta.id !== yo.tenant_id) { pm.collectionVariables.set('betaId', beta.id); }",
                "else { pm.collectionVariables.unset('betaId'); }",
            ]),
        cambiar_beta("Desactivar Beta", "inactivo"),
        pedir("REC-007: pedido desde el canal de Beta desactivado → 403", correo("rec.beta2.qa"), error(403), headers=(BETA,),
              previo=CON_BETA),
        cambiar_beta("Reactivar Beta (corre aunque falle lo anterior)", "activo"),
    ],
}

limpieza = {
    "name": "Limpieza",
    "item": [
        req("Suspender al proveedor de la prueba", "POST", "/v1/admin/technicians/{{proveedorId}}/suspend",
            [JSON, CORR, auth("adminToken")], {"reason": "Cuenta de una prueba de QA."}, pruebas=estado(200)),
        req("Desactivar la categoría de la prueba", "PATCH", "/v1/catalog/admin/categories/{{categoriaId}}",
            [JSON, CORR, auth("adminToken")], {"active": False}, pruebas=estado(200)),
    ],
}

coleccion = base.coleccion(
    "QUICKPATCH — SCRUM-627 Recuperación de contraseña",
    "SCRUM-623 contra QA, con identity.v1.yaml 1.10.0. Casos REC-001 a REC-021 y REC-026 del TD 7.2 con datos propios: "
    "202 igual exista o no la cuenta; una sola solicitud por cuenta; 429 al cuarto pedido en la hora; validaciones; el "
    "admin_tenant no deja solicitud; el administrador ve las de su tenant y no las de Beta; permisos; enlace de un solo uso "
    "a 1 hora que anula al anterior; token inventado o de otro tenant 400 enlace-invalido; clave nueva, la vieja ya no "
    "entra y el token de antes sigue sirviendo; desbloqueo de la cuenta; técnico del equipo con la invitación sin usar; "
    "pedido desde Beta desactivado 403. No correr más de 3 veces en una hora (el correo del admin_tenant cuenta en el "
    "límite). Variables: baseUrl, adminEmail, adminPassword, platformAdminEmail y platformAdminPassword (secretos de QA, "
    "nunca en el repositorio). Correr con --reporters cli: el reporte JSON de Newman guarda tokens y enlaces.",
    [preparacion, pedido, permisos, enlace, bloqueo, tenant_desactivado, limpieza],
)
coleccion["variable"] += [{"key": "platformAdminEmail", "value": ""}, {"key": "platformAdminPassword", "value": ""}]

destino = AQUI / "scrum-627-recuperacion.postman_collection.json"
destino.write_text(json.dumps(coleccion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Colección escrita en {destino}")
