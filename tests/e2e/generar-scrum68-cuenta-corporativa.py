"""Genera la colección de la cuenta corporativa (SCRUM-68, historia SCRUM-26) contra QA.

Uso: python tests/e2e/generar-scrum68-cuenta-corporativa.py
Escribe scrum-68-cuenta-corporativa.postman_collection.json. Reutiliza los ayudantes de
generar-scrum490-96-cotizacion-evidencia.py, que también regenera sus dos colecciones sin cambios.

Contrato: identity.v1.yaml 1.8.0 (POST /v1/auth/register/company, /v1/companies/me y /v1/companies/me/users con su
invitación; RF-06, DD 8.3.18). No necesita al administrador del tenant: todas las cuentas se registran por el canal con
correo, NIT y contraseña generados al vuelo, así que la colección corre aunque adminEmail esté vacío. Correr con
--reporters cli: el reporte JSON de Newman guarda los cuerpos y los tokens, y no debe subirse.
"""
import importlib.util
import json
import pathlib

AQUI = pathlib.Path(__file__).parent
_spec = importlib.util.spec_from_file_location("base", AQUI / "generar-scrum490-96-cotizacion-evidencia.py")
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)

JSON, CORR, CANAL, BETA, auth, estado, error = base.JSON, base.CORR, base.CANAL, base.BETA, base.auth, base.estado, base.error

CAMPOS_EMPRESA = ["contactEmail", "contactPhone", "createdAt", "id", "legalName", "nit"]
CAMPOS_USUARIO = ["createdAt", "email", "fullName", "passwordDefined", "phone", "userId"]


def req(nombre, metodo, ruta, headers, cuerpo=None, pruebas=(), previo=()):
    """Como base.req, pero sin omitir la petición cuando falta el administrador: aquí no se usa."""
    item = base.req(nombre, metodo, ruta, headers, cuerpo, pruebas, previo)
    for evento in item["event"]:
        if evento["listen"] == "prerequest":
            evento["script"]["exec"] = [linea for linea in evento["script"]["exec"] if linea not in base.CON_ADMIN]
    return item


preparar = [
    "if (!pm.collectionVariables.get('sufijo')) {",
    "  pm.collectionVariables.set('sufijo', Date.now().toString(36));",
    "  // Clave de las cuentas de esta corrida: se genera al vuelo y no se guarda en ningún lado.",
    "  pm.collectionVariables.set('clave', 'Qp_' + Math.random().toString(36).slice(2, 12) + '!Aa7');",
    "  // NIT de 9 dígitos con dígito de verificación, distinto en cada corrida.",
    "  const base = String(Date.now()).slice(-9);",
    "  pm.collectionVariables.set('nit', base + '-7');",
    "  pm.collectionVariables.set('nitOtra', String(Number(base) + 1).padStart(9, '1').slice(-9) + '-3');",
    "}",
]

# Lee el claim company_id del JWT sin verificar la firma (la verifica cada servicio con la llave pública).
claims = [
    "const parte = pm.response.json().accessToken.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');",
    "const claims = JSON.parse(atob(parte + '='.repeat((4 - parte.length % 4) % 4)));",
]


def empresa(prefijo, nit_var, headers=(JSON, CORR, CANAL), nombre_empresa="Inversiones Andinas QA S.A.S."):
    return {
        "company": {"legalName": nombre_empresa, "nit": "{{" + nit_var + "}}", "contactEmail": "compras." + prefijo + ".{{sufijo}}@quickpatch.test"},
        "user": {"email": prefijo + ".{{sufijo}}@quickpatch.test", "password": "{{clave}}", "fullName": "Contacto " + prefijo},
    }


def login(nombre, correo, variable, headers=(JSON, CORR, CANAL), empresa_var="empresaId", clave="{{clave}}"):
    return req(f"Login de {nombre}", "POST", "/v1/auth/login", list(headers), {"email": correo, "password": clave},
               pruebas=[
                   "pm.test('200 como empresa_contacto de la empresa', () => {",
                   "  pm.response.to.have.status(200);",
                   "  pm.expect(pm.response.json().user.role).to.eql('empresa_contacto');",
                   f"  pm.expect(pm.response.json().user.companyId).to.eql(pm.collectionVariables.get('{empresa_var}'));",
                   "});",
                   *claims,
                   f"pm.test('el token trae company_id', () => pm.expect(claims.company_id).to.eql(pm.collectionVariables.get('{empresa_var}')));",
                   f"pm.collectionVariables.set('{variable}', pm.response.json().accessToken);",
               ])


registro_ok = [
    "pm.test('201 con el contrato CompanyRegistered', () => {",
    "  pm.response.to.have.status(201);",
    "  const r = pm.response.json();",
    f"  pm.expect(Object.keys(r.company).sort()).to.eql({json.dumps(CAMPOS_EMPRESA)});",
    "  pm.expect(r.user.role).to.eql('empresa_contacto');",
    "  pm.expect(r.user.companyId).to.eql(r.company.id);",
    "  pm.expect(r.user).to.not.have.property('password');",
    "});",
]

coleccion = base.coleccion(
    "QUICKPATCH — SCRUM-68 Cuenta corporativa de punta a punta",
    "RF-06 (SCRUM-26) contra QA, con identity.v1.yaml 1.8.0. La empresa se registra con su primer usuario dentro del tenant "
    "del canal; el token trae company_id. El primer usuario agrega a otro con una invitación de un solo uso: sin usarla "
    "no puede entrar, la usa, entra con la misma empresa y los dos aparecen con la contraseña definida. Casos negativos: "
    "NIT y correo repetidos (409), datos inválidos (400 por campo), invitación para quien ya definió su contraseña (409), "
    "usuario de otra empresa (404), cliente hogar (403) y sin token (401). Aislamiento: otra empresa del mismo tenant "
    "solo ve sus usuarios, y el mismo NIT se registra en el tenant Beta como otra cuenta. Variables: baseUrl. Correr con "
    "--reporters cli: el reporte JSON de Newman guarda tokens.",
    [
        {
            "name": "1. Registro de la empresa",
            "item": [
                req("Registro de la empresa con su primer usuario", "POST", "/v1/auth/register/company", [JSON, CORR, CANAL],
                    empresa("empresa.qa", "nit"), previo=preparar,
                    pruebas=registro_ok + [
                        "pm.collectionVariables.set('empresaId', pm.response.json().company.id);",
                        "pm.collectionVariables.set('fundadorId', pm.response.json().user.id);",
                    ]),
                req("El mismo NIT en el tenant → 409 nit-registrado", "POST", "/v1/auth/register/company", [JSON, CORR, CANAL],
                    {"company": {"legalName": "Copia", "nit": "{{nit}}", "contactEmail": "copia.{{sufijo}}@quickpatch.test"},
                     "user": {"email": "copia.{{sufijo}}@quickpatch.test", "password": "{{clave}}", "fullName": "Copia"}},
                    pruebas=error(409, "nit-registrado")),
                req("El mismo correo → 409 correo-registrado", "POST", "/v1/auth/register/company", [JSON, CORR, CANAL],
                    {"company": {"legalName": "Otra", "nit": "{{nitOtra}}", "contactEmail": "otra.{{sufijo}}@quickpatch.test"},
                     "user": {"email": "empresa.qa.{{sufijo}}@quickpatch.test", "password": "{{clave}}", "fullName": "Otra"}},
                    pruebas=error(409, "correo-registrado")),
                req("Datos inválidos → 400 por campo con prefijo", "POST", "/v1/auth/register/company", [JSON, CORR, CANAL],
                    {"company": {"legalName": "A", "nit": "900.123", "contactEmail": "no-es-correo"},
                     "user": {"email": "malo", "password": "corta", "fullName": "B"}},
                    pruebas=error(400, "validacion") + [
                        "pm.test('errores de la empresa y del usuario', () => {",
                        "  const e = pm.response.json().errors;",
                        "  ['company.legalName', 'company.nit', 'company.contactEmail', 'user.email', 'user.password']",
                        "    .forEach(c => pm.expect(e).to.have.property(c));",
                        "});",
                    ]),
                login("la empresa", "empresa.qa.{{sufijo}}@quickpatch.test", "fundadorToken"),
                req("El perfil trae companyId", "GET", "/v1/users/me", [CORR, auth("fundadorToken")],
                    pruebas=estado(200) + [
                        "pm.test('companyId de la empresa', () => pm.expect(pm.response.json().companyId).to.eql(pm.collectionVariables.get('empresaId')));",
                    ]),
                req("La empresa del token", "GET", "/v1/companies/me", [CORR, auth("fundadorToken")],
                    pruebas=estado(200) + [
                        "pm.test('contrato Company con el NIT registrado', () => {",
                        "  const c = pm.response.json();",
                        f"  pm.expect(Object.keys(c).sort()).to.eql({json.dumps(CAMPOS_EMPRESA)});",
                        "  pm.expect(c.id).to.eql(pm.collectionVariables.get('empresaId'));",
                        "  pm.expect(c.nit).to.eql(pm.collectionVariables.get('nit'));",
                        "});",
                    ]),
            ],
        },
        {
            "name": "2. Otro usuario de la empresa con su invitación",
            "item": [
                req("Agregar un usuario a la empresa", "POST", "/v1/companies/me/users", [JSON, CORR, auth("fundadorToken")],
                    {"email": "usuario2.qa.{{sufijo}}@quickpatch.test", "fullName": "Segundo usuario QA"},
                    pruebas=[
                        "pm.test('201 con la invitación y la misma empresa', () => {",
                        "  pm.response.to.have.status(201);",
                        "  const u = pm.response.json();",
                        "  pm.expect(u.role).to.eql('empresa_contacto');",
                        "  pm.expect(u.companyId).to.eql(pm.collectionVariables.get('empresaId'));",
                        "  pm.expect(u.invitation.link).to.include('#token=');",
                        "  pm.expect(u.invitation.token).to.have.lengthOf(43);",
                        "});",
                        "pm.collectionVariables.set('usuario2Id', pm.response.json().id);",
                        "pm.collectionVariables.set('invitacion2', pm.response.json().invitation.token);",
                    ]),
                req("Correo repetido → 409", "POST", "/v1/companies/me/users", [JSON, CORR, auth("fundadorToken")],
                    {"email": "usuario2.qa.{{sufijo}}@quickpatch.test", "fullName": "Repetido"},
                    pruebas=error(409, "correo-registrado")),
                req("Datos inválidos → 400", "POST", "/v1/companies/me/users", [JSON, CORR, auth("fundadorToken")],
                    {"email": "malo", "fullName": "A"}, pruebas=error(400, "validacion")),
                req("Sin usar la invitación no puede entrar → 401", "POST", "/v1/auth/login", [JSON, CORR, CANAL],
                    {"email": "usuario2.qa.{{sufijo}}@quickpatch.test", "password": "{{clave}}"},
                    pruebas=error(401, "credenciales-invalidas")),
                req("Lista: el nuevo aparece sin contraseña definida", "GET", "/v1/companies/me/users", [CORR, auth("fundadorToken")],
                    pruebas=estado(200) + [
                        "pm.test('dos usuarios; el nuevo pendiente', () => {",
                        "  const p = pm.response.json();",
                        "  pm.expect(p.totalItems).to.eql(2);",
                        f"  pm.expect(Object.keys(p.items[0]).sort()).to.eql({json.dumps(CAMPOS_USUARIO)});",
                        "  const nuevo = p.items.find(u => u.userId === pm.collectionVariables.get('usuario2Id'));",
                        "  pm.expect(nuevo.passwordDefined).to.eql(false);",
                        "});",
                    ]),
                req("El usuario define su contraseña con la invitación", "POST", "/v1/auth/password/setup", [JSON, CORR, CANAL],
                    {"token": "{{invitacion2}}", "password": "{{clave}}"}, pruebas=estado(204)),
                req("La invitación no sirve dos veces → 400 enlace-invalido", "POST", "/v1/auth/password/setup", [JSON, CORR, CANAL],
                    {"token": "{{invitacion2}}", "password": "{{clave}}"}, pruebas=error(400, "enlace-invalido")),
                login("el segundo usuario", "usuario2.qa.{{sufijo}}@quickpatch.test", "usuario2Token"),
                req("El segundo usuario ve a los dos, ya activos", "GET", "/v1/companies/me/users", [CORR, auth("usuario2Token")],
                    pruebas=estado(200) + [
                        "pm.test('dos usuarios con la contraseña definida', () => {",
                        "  const p = pm.response.json();",
                        "  pm.expect(p.totalItems).to.eql(2);",
                        "  pm.expect(p.items.every(u => u.passwordDefined)).to.eql(true);",
                        "});",
                    ]),
                req("Nadie recibe invitación para el primer usuario → 409 (nadie toma su cuenta)", "POST",
                    "/v1/companies/me/users/{{fundadorId}}/invitation", [CORR, auth("usuario2Token")],
                    pruebas=error(409, "contrasena-definida")),
                req("Ni para quien ya usó la suya → 409", "POST", "/v1/companies/me/users/{{usuario2Id}}/invitation",
                    [CORR, auth("fundadorToken")], pruebas=error(409, "contrasena-definida")),
                req("Agregar un tercero", "POST", "/v1/companies/me/users", [JSON, CORR, auth("usuario2Token")],
                    {"email": "usuario3.qa.{{sufijo}}@quickpatch.test", "fullName": "Tercer usuario QA"},
                    pruebas=estado(201) + ["pm.collectionVariables.set('usuario3Id', pm.response.json().id);"]),
                req("Enlace nuevo para el tercero, que aún no lo usa", "POST", "/v1/companies/me/users/{{usuario3Id}}/invitation",
                    [CORR, auth("fundadorToken")],
                    pruebas=estado(201) + [
                        "pm.test('contrato Invitation', () => pm.expect(Object.keys(pm.response.json()).sort()).to.eql(['expiresAt', 'link', 'token']));",
                    ]),
            ],
        },
        {
            "name": "3. Aislamiento y roles",
            "item": [
                req("Otra empresa del mismo tenant", "POST", "/v1/auth/register/company", [JSON, CORR, CANAL],
                    empresa("otra.qa", "nitOtra", nombre_empresa="Otra Empresa QA S.A.S."),
                    pruebas=registro_ok + ["pm.collectionVariables.set('otraEmpresaId', pm.response.json().company.id);"]),
                login("la otra empresa", "otra.qa.{{sufijo}}@quickpatch.test", "otraToken", empresa_var="otraEmpresaId"),
                req("La otra empresa solo ve a su usuario", "GET", "/v1/companies/me/users", [CORR, auth("otraToken")],
                    pruebas=estado(200) + ["pm.test('un usuario', () => pm.expect(pm.response.json().totalItems).to.eql(1));"]),
                req("No renueva la invitación de un usuario ajeno → 404", "POST", "/v1/companies/me/users/{{usuario3Id}}/invitation",
                    [CORR, auth("otraToken")], pruebas=error(404, "no-encontrado")),
                req("Registro de un cliente hogar", "POST", "/v1/auth/register/client", [JSON, CORR, CANAL],
                    {"email": "hogar.qa.{{sufijo}}@quickpatch.test", "password": "{{clave}}", "fullName": "Cliente hogar QA"},
                    pruebas=estado(201)),
                req("Login del cliente hogar", "POST", "/v1/auth/login", [JSON, CORR, CANAL],
                    {"email": "hogar.qa.{{sufijo}}@quickpatch.test", "password": "{{clave}}"},
                    pruebas=estado(200) + [
                        "pm.test('sin companyId', () => pm.expect(pm.response.json().user.companyId).to.eql(null));",
                        *claims,
                        "pm.test('el token no trae company_id', () => pm.expect(claims).to.not.have.property('company_id'));",
                        "pm.collectionVariables.set('hogarToken', pm.response.json().accessToken);",
                    ]),
                req("El cliente hogar no tiene empresa → 403", "GET", "/v1/companies/me", [CORR, auth("hogarToken")],
                    pruebas=estado(403)),
                req("Sin token → 401", "GET", "/v1/companies/me/users", [CORR], pruebas=estado(401)),
                req("El mismo NIT en el tenant Beta es otra cuenta (DEP-13)", "POST", "/v1/auth/register/company", [JSON, CORR, BETA],
                    empresa("beta.qa", "nit"),
                    pruebas=registro_ok + [
                        "pm.test('otra empresa', () => pm.expect(pm.response.json().company.id).to.not.eql(pm.collectionVariables.get('empresaId')));",
                        "pm.collectionVariables.set('betaEmpresaId', pm.response.json().company.id);",
                    ]),
                login("la empresa de Beta", "beta.qa.{{sufijo}}@quickpatch.test", "betaToken", headers=(JSON, CORR, BETA),
                      empresa_var="betaEmpresaId"),
                req("La empresa de Beta no ve los usuarios de Alfa", "GET", "/v1/companies/me/users", [CORR, auth("betaToken")],
                    pruebas=estado(200) + ["pm.test('solo su usuario', () => pm.expect(pm.response.json().totalItems).to.eql(1));"]),
                req("Ni renueva la invitación de un usuario de Alfa → 404 (RLS)", "POST",
                    "/v1/companies/me/users/{{usuario3Id}}/invitation", [CORR, auth("betaToken")], pruebas=error(404)),
            ],
        },
    ],
)

destino = AQUI / "scrum-68-cuenta-corporativa.postman_collection.json"
destino.write_text(json.dumps(coleccion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Colección escrita en {destino}")
