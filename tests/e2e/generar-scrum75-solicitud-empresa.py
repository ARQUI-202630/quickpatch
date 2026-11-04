"""Genera la colección de la solicitud de empresa (SCRUM-75, historia SCRUM-28) contra QA.

Uso: python tests/e2e/generar-scrum75-solicitud-empresa.py
Escribe scrum-75-solicitud-empresa.postman_collection.json. Reutiliza los pasos de
generar-scrum490-96-cotizacion-evidencia.py (preparación con técnico aprobado y clientes), que también regenera sus
dos colecciones sin cambios.

Contratos: service-request.v1.yaml 1.9.0 (siteName, clientType, companyId y la lista para cliente y empresa_contacto,
RN-SR12 y RN-SR14), identity.v1.yaml 1.8.0 (cuenta corporativa) y matching.v1.yaml. Necesita al administrador del
tenant (adminEmail y adminPassword, secretos de QA que nunca van al repositorio) para la categoría y el técnico. Correr
con --reporters cli: el reporte JSON de Newman guarda los cuerpos y los tokens, y no debe subirse.
"""
import importlib.util
import json
import pathlib

AQUI = pathlib.Path(__file__).parent
_spec = importlib.util.spec_from_file_location("base", AQUI / "generar-scrum490-96-cotizacion-evidencia.py")
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)

JSON, CORR, CANAL, auth, req, estado, error = base.JSON, base.CORR, base.CANAL, base.auth, base.req, base.estado, base.error
reintentar = base.reintentar

SOLICITUD = "/v1/service-requests/{{solicitudEmpresaId}}"

nits = [
    "if (!pm.collectionVariables.get('nitEmpresa')) {",
    "  const base = String(Date.now()).slice(-9);",
    "  pm.collectionVariables.set('nitEmpresa', base + '-1');",
    "  pm.collectionVariables.set('nitOtraEmpresa', String(Number(base) + 3).padStart(9, '2').slice(-9) + '-2');",
    "}",
]


def registrar_empresa(nombre, prefijo, nit_var, empresa_var):
    return req(f"Registro de {nombre}", "POST", "/v1/auth/register/company", [JSON, CORR, CANAL],
               {"company": {"legalName": f"{nombre} QA S.A.S.", "nit": "{{" + nit_var + "}}",
                            "contactEmail": "compras." + prefijo + ".{{sufijo}}@quickpatch.test"},
                "user": {"email": prefijo + ".{{sufijo}}@quickpatch.test", "password": "{{clave}}", "fullName": f"Contacto {nombre}"}},
               previo=nits,
               pruebas=estado(201) + [f"pm.collectionVariables.set('{empresa_var}', pm.response.json().company.id);"])


def login_empresa(nombre, correo, variable, empresa_var):
    return req(f"Login de {nombre}", "POST", "/v1/auth/login", [JSON, CORR, CANAL], {"email": correo, "password": "{{clave}}"},
               pruebas=[
                   "pm.test('200 como empresa_contacto de su empresa', () => {",
                   "  pm.response.to.have.status(200);",
                   "  pm.expect(pm.response.json().user.role).to.eql('empresa_contacto');",
                   f"  pm.expect(pm.response.json().user.companyId).to.eql(pm.collectionVariables.get('{empresa_var}'));",
                   "});",
                   f"pm.collectionVariables.set('{variable}', pm.response.json().accessToken);",
                   f"pm.collectionVariables.set('{variable}Usuario', pm.response.json().user.id);",
               ])


def crear(nombre, token, cuerpo_extra, pruebas):
    cuerpo = {"categoryId": "{{categoriaId}}", "description": "El aire acondicionado de la sala de juntas no enfría.",
              "location": {"latitude": 4.6486, "longitude": -74.063}, "addressText": "Carrera 7 # 71-21, piso 8"}
    cuerpo.update(cuerpo_extra)
    return req(nombre, "POST", "/v1/service-requests", [JSON, CORR, auth(token)], cuerpo,
               pruebas=reintentar("pm.response.code !== 422", pruebas, maximo=10))


coleccion = base.coleccion(
    "QUICKPATCH — SCRUM-75 Solicitud de empresa de punta a punta",
    "RF-08 (SCRUM-28) contra QA, con service-request.v1.yaml 1.9.0. Un empresa_contacto crea una solicitud con la sede: "
    "queda con clientType empresa y la empresa del token (RN-SR12), y sigue el mismo flujo de matching que la de hogar "
    "(oferta, aceptación y asignado). Otro usuario de la empresa la ve en el detalle y en la lista (RN-SR14), pero no la "
    "cancela; otra empresa, un cliente hogar y el cliente del tenant Beta reciben 404. El administrador del tenant la ve en "
    "su lista como de empresa, con la sede. Casos negativos: sede de un cliente hogar y sede de un carácter (400). "
    "Variables: baseUrl, adminEmail y adminPassword (secretos de QA, nunca en el repositorio). Correr con --reporters cli: "
    "el reporte JSON de Newman guarda tokens.",
    [
        base.preparacion("SCRUM-75"),
        {
            "name": "1. La empresa y sus usuarios",
            "item": [
                registrar_empresa("Empresa", "empresa75.qa", "nitEmpresa", "empresaId"),
                login_empresa("la empresa", "empresa75.qa.{{sufijo}}@quickpatch.test", "empresaToken", "empresaId"),
                req("La empresa agrega a un colega", "POST", "/v1/companies/me/users", [JSON, CORR, auth("empresaToken")],
                    {"email": "colega75.qa.{{sufijo}}@quickpatch.test", "fullName": "Colega de la empresa"},
                    pruebas=estado(201) + ["pm.collectionVariables.set('invitacionColega', pm.response.json().invitation.token);"]),
                req("El colega define su contraseña", "POST", "/v1/auth/password/setup", [JSON, CORR, CANAL],
                    {"token": "{{invitacionColega}}", "password": "{{clave}}"}, pruebas=estado(204)),
                login_empresa("el colega", "colega75.qa.{{sufijo}}@quickpatch.test", "colegaToken", "empresaId"),
                registrar_empresa("Otra Empresa", "otra75.qa", "nitOtraEmpresa", "otraEmpresaId"),
                login_empresa("la otra empresa", "otra75.qa.{{sufijo}}@quickpatch.test", "otraEmpresaToken", "otraEmpresaId"),
            ],
        },
        {
            "name": "2. Crear la solicitud de empresa",
            "item": [
                crear("Sede de un carácter → 400 en siteName", "empresaToken", {"siteName": "A"},
                      error(400, "validacion") + [
                          "pm.test('error en siteName', () => pm.expect(pm.response.json().errors).to.have.property('siteName'));",
                      ]),
                crear("Un cliente hogar no indica sede → 400", "clienteToken", {"siteName": "Sede Norte"},
                      error(400, "validacion") + [
                          "pm.test('error en siteName', () => pm.expect(pm.response.json().errors).to.have.property('siteName'));",
                      ]),
                crear("La empresa crea la solicitud con su sede", "empresaToken",
                      {"siteName": "  Sede Chapinero  "},
                      [
                          "pm.test('201 de empresa con la empresa del token', () => {",
                          "  pm.response.to.have.status(201);",
                          "  const s = pm.response.json();",
                          "  pm.expect(s.status).to.eql('buscando_tecnico');",
                          "  pm.expect(s.clientType).to.eql('empresa');",
                          "  pm.expect(s.companyId).to.eql(pm.collectionVariables.get('empresaId'));",
                          "  pm.expect(s.siteName).to.eql('Sede Chapinero');",
                          "});",
                          "pm.collectionVariables.set('solicitudEmpresaId', pm.response.json().id);",
                      ]),
            ],
        },
        {
            "name": "3. El mismo flujo de matching que las de hogar",
            "item": [
                req("El técnico recibe la oferta", "GET", "/v1/matching/offers?status=pendiente", [CORR, auth("tecnicoToken")],
                    pruebas=[
                        "const oferta = pm.response.code === 200 && pm.response.json().items.find(x => x.serviceRequestId === pm.collectionVariables.get('solicitudEmpresaId'));",
                        *reintentar("oferta", [
                            "pm.test('la oferta está pendiente para el técnico', () => pm.expect(oferta).to.be.ok);",
                            "if (oferta) { pm.collectionVariables.set('ofertaEmpresaId', oferta.attemptId); }",
                        ]),
                    ]),
                req("El técnico acepta", "POST", "/v1/matching/offers/{{ofertaEmpresaId}}/accept", [CORR, auth("tecnicoToken")],
                    pruebas=estado(200)),
                req("La solicitud de empresa queda asignada", "GET", SOLICITUD, [CORR, auth("empresaToken")],
                    pruebas=reintentar("pm.response.json().status === 'asignado'", [
                        "pm.test('asignado al técnico de la prueba', () => {",
                        "  pm.expect(pm.response.json().status).to.eql('asignado');",
                        "  pm.expect(pm.response.json().technicianId).to.eql(pm.collectionVariables.get('tecnicoId'));",
                        "});",
                    ])),
                req("El técnico asignado ve la sede en el detalle", "GET", SOLICITUD, [CORR, auth("tecnicoToken")],
                    pruebas=estado(200) + [
                        "pm.test('de empresa, con su sede', () => pm.expect(pm.response.json().siteName).to.eql('Sede Chapinero'));",
                    ]),
            ],
        },
        {
            "name": "4. Quién la ve (RN-SR14)",
            "item": [
                req("El colega la ve en el detalle", "GET", SOLICITUD, [CORR, auth("colegaToken")],
                    pruebas=estado(200) + [
                        "pm.test('la misma solicitud de empresa', () => pm.expect(pm.response.json().clientType).to.eql('empresa'));",
                    ]),
                req("El colega la ve en la lista de la empresa", "GET", "/v1/service-requests", [CORR, auth("colegaToken")],
                    pruebas=estado(200) + [
                        "pm.test('aparece con su tipo y su sede', () => {",
                        "  const s = pm.response.json().items.find(x => x.id === pm.collectionVariables.get('solicitudEmpresaId'));",
                        "  pm.expect(s).to.be.ok;",
                        "  pm.expect(s.clientType).to.eql('empresa');",
                        "  pm.expect(s.siteName).to.eql('Sede Chapinero');",
                        "  pm.expect(s.clientId).to.eql(pm.collectionVariables.get('empresaTokenUsuario'));",
                        "  pm.expect(s).to.not.have.property('addressText');",
                        "});",
                    ]),
                req("Otra empresa no la ve → 404", "GET", SOLICITUD, [CORR, auth("otraEmpresaToken")], pruebas=error(404)),
                req("Ni en su lista", "GET", "/v1/service-requests", [CORR, auth("otraEmpresaToken")],
                    pruebas=estado(200) + [
                        "pm.test('no aparece', () => pm.expect(pm.response.json().items.map(x => x.id)).to.not.include(pm.collectionVariables.get('solicitudEmpresaId')));",
                    ]),
                req("Un cliente hogar del tenant no la ve → 404", "GET", SOLICITUD, [CORR, auth("otroClienteToken")], pruebas=error(404)),
                req("El cliente de Beta no la ve → 404 (RLS)", "GET", SOLICITUD, [CORR, auth("betaToken")], pruebas=error(404)),
                req("El administrador la ve en su lista como de empresa", "GET", "/v1/service-requests?size=100",
                    [CORR, auth("adminToken")],
                    pruebas=estado(200) + [
                        "pm.test('clientType empresa con la sede', () => {",
                        "  const s = pm.response.json().items.find(x => x.id === pm.collectionVariables.get('solicitudEmpresaId'));",
                        "  pm.expect(s).to.be.ok;",
                        "  pm.expect(s.clientType).to.eql('empresa');",
                        "  pm.expect(s.companyId).to.eql(pm.collectionVariables.get('empresaId'));",
                        "});",
                    ]),
            ],
        },
        {
            "name": "5. Cerrar",
            "item": [
                req("El colega no cancela: las acciones son de quien la creó → 404", "POST", SOLICITUD + "/cancel",
                    [JSON, CORR, auth("colegaToken")], {"reason": "Fin de la prueba SCRUM-75."}, pruebas=error(404)),
                req("Quien la creó la cancela", "POST", SOLICITUD + "/cancel", [JSON, CORR, auth("empresaToken")],
                    {"reason": "Fin de la prueba SCRUM-75."}, pruebas=estado(200)),
                base.disponibilidad("disponible", "El técnico queda libre"),
            ],
        },
        base.limpieza,
    ],
)

destino = AQUI / "scrum-75-solicitud-empresa.postman_collection.json"
destino.write_text(json.dumps(coleccion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Colección escrita en {destino}")
