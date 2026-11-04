"""Genera la colección de los pagos recibidos del técnico y del proveedor (SCRUM-503, historia SCRUM-45) contra QA.

Uso: python tests/e2e/generar-scrum45-pagos-tecnico.py
Escribe scrum-45-pagos-tecnico.postman_collection.json. Reutiliza los pasos de generar-scrum490-96-cotizacion-evidencia.py,
generar-scrum117-pago.py y generar-scrum75-solicitud-empresa.py, que también regeneran sus colecciones sin cambios.

Contrato: payments.v1.yaml 1.2.0 (GET /v1/payments/received, RF-25). Casos PAY-024 a PAY-038 del TD 3.1; PAY-039 y
PAY-040 son de pantalla y se verifican a mano con el APK. Datos propios: un técnico independiente con dos servicios (uno
pagado después de un rechazo y otro sin pagar), un proveedor con un técnico de su equipo y un servicio sin pagar, y
cuentas del tenant Beta para la fuga entre tenants. PAY-026 y PAY-036 necesitan una categoría activa en Beta
(la crea su administrador); sin ella se omiten. Necesita al administrador del tenant (adminEmail y adminPassword,
secretos de QA que nunca van al repositorio). Correr con --reporters cli: el reporte JSON de Newman guarda tokens.
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
pago = cargar("pago", "generar-scrum117-pago.py")
empresa = cargar("empresa", "generar-scrum75-solicitud-empresa.py")

JSON, CORR, CANAL, BETA = base.JSON, base.CORR, base.CANAL, base.BETA
auth, req, estado, error, reintentar = base.auth, base.req, base.estado, base.error, base.reintentar

HISTORIA = "SCRUM-503"
RECIBIDOS = "/v1/payments/received"
CAMPOS = ["amount", "approvedAt", "createdAt", "currency", "id", "serviceRequestId", "status", "technicianId"]


CON_BETA = ["if (!pm.collectionVariables.get('categoriaBetaId')) { pm.execution.skipRequest(); }"]


def recibidos(nombre, token, query="", pruebas=(), headers=(), previo=()):
    ruta = RECIBIDOS + (("?" + query) if query else "")
    return req(nombre, "GET", ruta, [CORR, *headers] + ([auth(token)] if token else []), pruebas=pruebas, previo=previo)


def pagina_vacia(descripcion):
    return estado(200) + [
        f"pm.test('{descripcion}: 200 sin pagos', () => {{",
        "  const p = pm.response.json();",
        "  pm.expect(p.items).to.eql([]);",
        "  pm.expect(p.totalItems).to.eql(0);",
        "});",
    ]


def contrato_items():
    """PAY-027 y PAY-033: solo los campos del contrato, sin datos de tarjeta, con el formato de monto y fecha."""
    return [
        "pm.test('PAY-027: cada pago trae solo los campos del contrato, sin datos de tarjeta', () => {",
        "  pm.response.json().items.forEach(i => {",
        f"    pm.expect(Object.keys(i).sort()).to.eql({json.dumps(CAMPOS)});",
        "  });",
        "  pm.expect(pm.response.text()).to.not.match(/cardNumber|cvv|paymentToken|tok_sim_/i);",
        "});",
        "pm.test('PAY-033: monto XXXXXX.CC en COP y approvedAt solo en aprobado', () => {",
        "  pm.response.json().items.forEach(i => {",
        "    pm.expect(i.amount).to.match(/^[0-9]+\\.[0-9]{2}$/);",
        "    pm.expect(i.currency).to.eql('COP');",
        "    if (i.status === 'aprobado') { pm.expect(i.approvedAt).to.be.a('string'); }",
        "    else { pm.expect(i.approvedAt).to.eql(null); }",
        "  });",
        "});",
    ]


def hasta_completado(n, token, tecnico_var, monto_mano, monto_materiales):
    """Solicitud n asignada al técnico de `token`, cotizada, aceptada, ejecutada con foto y completada."""
    s, o = f"solicitud{n}Id", f"oferta{n}Id"
    sr = "/v1/service-requests/{{" + s + "}}"
    return [
        req(f"Crear la solicitud {n} (espera la réplica de la categoría)", "POST", "/v1/service-requests",
            [JSON, CORR, auth("clienteToken")],
            {"categoryId": "{{categoriaId}}", "description": f"Prueba de pagos recibidos {HISTORIA}, solicitud {n}",
             "location": {"latitude": 4.6486, "longitude": -74.063}, "addressText": "Calle 63 # 9-45, apto 201"},
            pruebas=reintentar("pm.response.code !== 422", estado(201) + [
                f"pm.collectionVariables.set('{s}', pm.response.json().id);",
            ], maximo=10)),
        req(f"El técnico ve la oferta de la solicitud {n}", "GET", "/v1/matching/offers?status=pendiente",
            [CORR, auth(token)],
            pruebas=[
                f"const oferta = pm.response.code === 200 && pm.response.json().items.find(x => x.serviceRequestId === pm.collectionVariables.get('{s}'));",
                *reintentar("oferta", [
                    "pm.test('la oferta está pendiente para el técnico', () => pm.expect(oferta).to.be.ok);",
                    f"if (oferta) {{ pm.collectionVariables.set('{o}', oferta.attemptId); }}",
                ]),
            ]),
        req(f"El técnico acepta la oferta de la solicitud {n}", "POST", "/v1/matching/offers/{{" + o + "}}/accept",
            [CORR, auth(token)], pruebas=estado(200)),
        req(f"La solicitud {n} queda asignada a ese técnico", "GET", sr, [CORR, auth("clienteToken")],
            pruebas=reintentar("pm.response.json().status === 'asignado'", [
                "pm.test('asignado al técnico esperado', () => {",
                "  pm.expect(pm.response.json().status).to.eql('asignado');",
                f"  pm.expect(pm.response.json().technicianId).to.eql(pm.collectionVariables.get('{tecnico_var}'));",
                "});",
            ])),
        req(f"El técnico cotiza la solicitud {n}", "POST", sr + "/quotes", [JSON, CORR, auth(token)],
            {"laborAmount": monto_mano, "materialsAmount": monto_materiales, "detail": "Cambio de sifón y empaques."},
            pruebas=estado(201) + [f"pm.collectionVariables.set('cot{n}', pm.response.json().id);"]),
        req(f"El cliente acepta la cotización de la solicitud {n}", "POST", sr + "/quotes/{{cot" + str(n) + "}}/accept",
            [CORR, auth("clienteToken")], pruebas=estado(200)),
        req(f"El técnico inicia la solicitud {n}", "POST", sr + "/start", [CORR, auth(token)], pruebas=estado(200)),
        req(f"El técnico sube la foto de la solicitud {n}", "POST", sr + "/evidence", [CORR, auth(token)],
            archivo=base.FOTO, pruebas=estado(201)),
        req(f"El técnico completa la solicitud {n}", "POST", sr + "/complete", [CORR, auth(token)], pruebas=estado(200)),
    ]


def disponible(token, nombre):
    return [
        req(f"{nombre} cubre toda Bogotá (espera a que Matching lo conozca)", "PUT", "/v1/technicians/me/coverage",
            [JSON, CORR, auth(token)], {"localityCodes": base.LOCALIDADES},
            pruebas=reintentar("pm.response.code === 200", estado(200))),
        req(f"{nombre} queda disponible", "PUT", "/v1/technicians/me/availability", [JSON, CORR, auth(token)],
            {"status": "disponible"}, pruebas=reintentar("pm.response.code === 200", estado(200))),
    ]


def login(nombre, correo, variable, rol, headers=(JSON, CORR, CANAL), id_var=None, previo=()):
    return req(f"Login del {nombre}", "POST", "/v1/auth/login", list(headers), {"email": correo, "password": "{{clave}}"},
               previo=previo,
               pruebas=[
                   f"pm.test('200 con rol {rol}', () => {{",
                   "  pm.response.to.have.status(200);",
                   f"  pm.expect(pm.response.json().user.role).to.eql('{rol}');",
                   "});",
                   f"pm.collectionVariables.set('{variable}', pm.response.json().accessToken);",
                   *([f"pm.collectionVariables.set('{id_var}', pm.response.json().user.id);"] if id_var else []),
               ])


def registro_tecnico(nombre, correo, rol, doc_var, id_var, headers=(JSON, CORR, CANAL), especialidad="categoriaId", delta=0,
                     previo=()):
    return req(f"Registro del {nombre}", "POST", "/v1/auth/register/technician", list(headers),
               {"email": correo, "password": "{{clave}}", "fullName": f"{nombre.capitalize()} {HISTORIA}",
                "phone": "3007654329", "documentId": "{{" + doc_var + "}}", "specialtyId": "{{" + especialidad + "}}",
                "role": rol},
               previo=[*previo, f"pm.collectionVariables.set('{doc_var}', String(Date.now() + {delta}).slice(-10));"],
               pruebas=estado(201) + [f"pm.collectionVariables.set('{id_var}', pm.response.json().id);"])


_prep = base.preparacion(HISTORIA)
_nombres = [i["name"] for i in _prep["item"]]
assert _nombres[6] == "El técnico queda disponible" and "otro técnico" in _nombres[7] and "cliente" in _nombres[10], _nombres

preparacion = {
    "name": "0. Preparación: técnico independiente, proveedor con su técnico, clientes y cuentas de Beta",
    "item": _prep["item"][0:11] + [
        # Proveedor aprobado con un técnico de su equipo, aprobado y con la contraseña definida por la invitación.
        registro_tecnico("proveedor", "proveedor.qa.{{sufijo}}@quickpatch.test", "proveedor", "docProveedor",
                         "proveedorId", delta=11),
        req("El administrador aprueba al proveedor", "POST", "/v1/admin/technicians/{{proveedorId}}/approve",
            [CORR, auth("adminToken")], pruebas=estado(200)),
        login("proveedor", "proveedor.qa.{{sufijo}}@quickpatch.test", "proveedorToken", "proveedor"),
        req("El proveedor da de alta un técnico de su equipo", "POST", "/v1/providers/me/technicians",
            [JSON, CORR, auth("proveedorToken")],
            {"email": "equipo.qa.{{sufijo}}@quickpatch.test", "fullName": f"Técnico del equipo {HISTORIA}",
             "phone": "3007654330", "documentId": "{{docEquipo}}", "specialtyId": "{{categoriaId}}"},
            previo=["pm.collectionVariables.set('docEquipo', String(Date.now() + 13).slice(-10));"],
            pruebas=estado(201) + [
                "pm.collectionVariables.set('equipoId', pm.response.json().id);",
                "pm.collectionVariables.set('invitacionEquipo', pm.response.json().invitation.token);",
            ]),
        req("El técnico del equipo define su contraseña", "POST", "/v1/auth/password/setup", [JSON, CORR, CANAL],
            {"token": "{{invitacionEquipo}}", "password": "{{clave}}"}, pruebas=estado(204)),
        req("El administrador aprueba al técnico del equipo", "POST", "/v1/admin/technicians/{{equipoId}}/approve",
            [CORR, auth("adminToken")], pruebas=estado(200)),
        login("técnico del equipo", "equipo.qa.{{sufijo}}@quickpatch.test", "equipoToken", "tecnico"),
        # Roles sin acceso (PAY-037).
        empresa.registrar_empresa("Empresa", "empresa503.qa", "nitEmpresa", "empresaId"),
        empresa.login_empresa("la empresa", "empresa503.qa.{{sufijo}}@quickpatch.test", "empresaToken", "empresaId"),
        # Tenant Beta: una especialidad de su catálogo, un técnico y un proveedor (PAY-026 y PAY-036).
        req("Categorías del tenant Beta", "GET", "/v1/catalog/categories", [CORR, BETA],
            pruebas=estado(200) + [
                "// Sin categorías en Beta no se puede registrar un técnico allá: PAY-026 y PAY-036 se omiten (ver README).",
                "const beta = pm.response.json();",
                "if (beta.length > 0) { pm.collectionVariables.set('categoriaBetaId', beta[0].id); }",
                "else { pm.collectionVariables.unset('categoriaBetaId'); console.log('Beta sin categorías: se omiten PAY-026 y PAY-036'); }",
            ]),
        registro_tecnico("técnico de Beta", "tecnico503.beta.{{sufijo}}@quickpatch.test", "tecnico", "docTecnicoBeta",
                         "tecnicoBetaId", headers=(JSON, CORR, BETA), especialidad="categoriaBetaId", delta=17,
                         previo=CON_BETA),
        login("técnico de Beta", "tecnico503.beta.{{sufijo}}@quickpatch.test", "tecnicoBetaToken", "tecnico",
              headers=(JSON, CORR, BETA), previo=CON_BETA),
        registro_tecnico("proveedor de Beta", "proveedor503.beta.{{sufijo}}@quickpatch.test", "proveedor",
                         "docProveedorBeta", "proveedorBetaId", headers=(JSON, CORR, BETA), especialidad="categoriaBetaId",
                         delta=19, previo=CON_BETA),
        login("proveedor de Beta", "proveedor503.beta.{{sufijo}}@quickpatch.test", "proveedorBetaToken", "proveedor",
              headers=(JSON, CORR, BETA), previo=CON_BETA),
    ],
}

pago_pendiente = req("El pago de la solicitud 1 queda pendiente (espera service-request.completed en Payments)", "GET",
                     pago.PAGO, [CORR, auth("clienteToken")],
                     pruebas=reintentar("pm.response.code === 200", pago.pago("pendiente"), maximo=20))

tecnico = {
    "name": "1. Técnico independiente: un servicio pagado tras un rechazo y otro sin pagar",
    "item": [
        *hasta_completado(1, "tecnicoToken", "tecnicoId", "150000.00", "35000.00"),
        pago_pendiente,
        pago.pagar("Tarjeta rechazada por fondos → 200 rechazado", "tok_sim_rechazada_", pago.pago("rechazado")),
        pago.pagar("Tarjeta aprobada → 200 aprobado", "tok_sim_aprobada_", pago.pago("aprobado")),
        *hasta_completado(2, "tecnicoToken", "tecnicoId", "80000.00", "20000.00"),
        recibidos("PAY-024 / PAY-031: el técnico ve sus dos pagos (espera los eventos de Payments)", "tecnicoToken",
                  pruebas=reintentar(
                      "pm.response.code === 200 && pm.response.json().totalItems === 2",
                      estado(200) + [
                          "const p = pm.response.json();",
                          "const s1 = pm.collectionVariables.get('solicitud1Id');",
                          "const s2 = pm.collectionVariables.get('solicitud2Id');",
                          "pm.test('PAY-024: solo pagos suyos, del más reciente al más antiguo', () => {",
                          "  pm.expect(p.totalItems).to.eql(2);",
                          "  p.items.forEach(i => pm.expect(i.technicianId).to.eql(pm.collectionVariables.get('tecnicoId')));",
                          "  pm.expect(p.items.map(i => i.serviceRequestId)).to.eql([s2, s1]);",
                          "  pm.expect(new Date(p.items[0].createdAt) >= new Date(p.items[1].createdAt)).to.eql(true);",
                          "});",
                          "pm.test('PAY-031: el rechazado no aparece; el aprobado, una sola vez', () => {",
                          "  const de1 = p.items.filter(i => i.serviceRequestId === s1);",
                          "  pm.expect(de1.length).to.eql(1);",
                          "  pm.expect(de1[0].status).to.eql('aprobado');",
                          "  pm.expect(de1[0].amount).to.eql('185000.00');",
                          "  p.items.forEach(i => pm.expect(i.status).to.not.eql('rechazado'));",
                          "});",
                          "pm.test('la solicitud sin pagar está pendiente', () => {",
                          "  const de2 = p.items.find(i => i.serviceRequestId === s2);",
                          "  pm.expect(de2.status).to.eql('pendiente');",
                          "  pm.expect(de2.amount).to.eql('100000.00');",
                          "});",
                          "pm.collectionVariables.set('pagoAprobadoId', p.items.find(i => i.serviceRequestId === s1).id);",
                          *contrato_items(),
                      ], maximo=20)),
        recibidos("PAY-032: filtro pendiente", "tecnicoToken", "status=pendiente",
                  pruebas=estado(200) + [
                      "pm.test('solo la solicitud sin pagar, en pendiente', () => {",
                      "  const p = pm.response.json();",
                      "  pm.expect(p.items.map(i => i.serviceRequestId)).to.eql([pm.collectionVariables.get('solicitud2Id')]);",
                      "  p.items.forEach(i => pm.expect(i.status).to.eql('pendiente'));",
                      "});",
                  ]),
        recibidos("PAY-032: filtro aprobado", "tecnicoToken", "status=aprobado",
                  pruebas=estado(200) + [
                      "pm.test('solo el pago aprobado', () => {",
                      "  const p = pm.response.json();",
                      "  pm.expect(p.items.map(i => i.id)).to.eql([pm.collectionVariables.get('pagoAprobadoId')]);",
                      "});",
                  ]),
        recibidos("PAY-032: filtro procesando", "tecnicoToken", "status=procesando",
                  pruebas=estado(200) + [
                      "pm.test('ninguno fuera de procesando', () => pm.response.json().items.forEach(i => pm.expect(i.status).to.eql('procesando')));",
                  ]),
        recibidos("PAY-032: filtro rechazado → 400", "tecnicoToken", "status=rechazado", pruebas=error(400)),
        recibidos("PAY-034: página 1 de tamaño 1", "tecnicoToken", "page=1&size=1",
                  pruebas=estado(200) + [
                      "pm.test('un pago y el total de dos', () => {",
                      "  const p = pm.response.json();",
                      "  pm.expect(p.items.length).to.eql(1);",
                      "  pm.expect(p.totalItems).to.eql(2);",
                      "  pm.collectionVariables.set('primeraPagina', p.items[0].id);",
                      "});",
                  ]),
        recibidos("PAY-034: página 2 de tamaño 1", "tecnicoToken", "page=2&size=1",
                  pruebas=estado(200) + [
                      "pm.test('otro pago con el mismo total', () => {",
                      "  const p = pm.response.json();",
                      "  pm.expect(p.items.length).to.eql(1);",
                      "  pm.expect(p.totalItems).to.eql(2);",
                      "  pm.expect(p.items[0].id).to.not.eql(pm.collectionVariables.get('primeraPagina'));",
                      "});",
                  ]),
        recibidos("PAY-034: page=0 → 400", "tecnicoToken", "page=0", pruebas=error(400)),
        recibidos("PAY-034: size=0 → 400", "tecnicoToken", "size=0", pruebas=error(400)),
        recibidos("PAY-034: size=101 → 400", "tecnicoToken", "size=101", pruebas=error(400)),
        recibidos("PAY-030: el técnico envía technicianId → 400", "tecnicoToken", "technicianId={{tecnicoId}}",
                  pruebas=error(400)),
        recibidos("PAY-035: otro técnico del mismo tenant no ve esos pagos", "otroTecnicoToken",
                  pruebas=pagina_vacia("otro técnico")),
    ],
}

proveedor = {
    "name": "2. Proveedor: los pagos de su equipo",
    "item": [
        req("El técnico independiente queda no disponible, para que la oferta sea del técnico del equipo", "PUT",
            "/v1/technicians/me/availability", [JSON, CORR, auth("tecnicoToken")], {"status": "no_disponible"},
            pruebas=reintentar("pm.response.code === 200", estado(200))),
        *disponible("equipoToken", "El técnico del equipo"),
        *hasta_completado(3, "equipoToken", "equipoId", "120000.00", "30000.00"),
        recibidos("PAY-025: el proveedor ve el pago de su equipo (espera technician.registered y el pago)", "proveedorToken",
                  pruebas=reintentar(
                      "pm.response.code === 200 && pm.response.json().items.some(i => i.serviceRequestId === pm.collectionVariables.get('solicitud3Id'))",
                      estado(200) + [
                          "const p = pm.response.json();",
                          "pm.test('PAY-025: solo pagos de técnicos de su equipo', () => {",
                          "  pm.expect(p.totalItems).to.eql(1);",
                          "  p.items.forEach(i => pm.expect(i.technicianId).to.eql(pm.collectionVariables.get('equipoId')));",
                          "  const ajenas = [pm.collectionVariables.get('solicitud1Id'), pm.collectionVariables.get('solicitud2Id')];",
                          "  p.items.forEach(i => pm.expect(ajenas).to.not.include(i.serviceRequestId));",
                          "});",
                          "pm.test('el servicio del equipo está pendiente por 150.000', () => {",
                          "  pm.expect(p.items[0].status).to.eql('pendiente');",
                          "  pm.expect(p.items[0].amount).to.eql('150000.00');",
                          "});",
                          *contrato_items(),
                      ], maximo=20)),
        recibidos("PAY-028: el proveedor filtra por el técnico de su equipo", "proveedorToken", "technicianId={{equipoId}}",
                  pruebas=estado(200) + [
                      "pm.test('solo los pagos de ese técnico', () => {",
                      "  const p = pm.response.json();",
                      "  pm.expect(p.items.map(i => i.serviceRequestId)).to.eql([pm.collectionVariables.get('solicitud3Id')]);",
                      "});",
                  ]),
        recibidos("PAY-029: el proveedor filtra por un técnico ajeno a su equipo", "proveedorToken",
                  "technicianId={{tecnicoId}}", pruebas=pagina_vacia("técnico ajeno")),
        recibidos("El técnico del equipo ve su propio pago", "equipoToken",
                  pruebas=estado(200) + [
                      "pm.test('el pago de la solicitud 3', () => {",
                      "  pm.expect(pm.response.json().items.map(i => i.serviceRequestId)).to.eql([pm.collectionVariables.get('solicitud3Id')]);",
                      "});",
                  ]),
    ],
}

fugas = {
    "name": "3. Otro tenant, roles sin acceso y sin sesión",
    "item": [
        recibidos("PAY-026: técnico del tenant Beta", "tecnicoBetaToken", headers=[BETA],
                  previo=CON_BETA, pruebas=pagina_vacia("técnico de Beta")),
        recibidos("PAY-036: proveedor de Beta filtra por el técnico del equipo", "proveedorBetaToken",
                  "technicianId={{equipoId}}", headers=[BETA], previo=CON_BETA,
                  pruebas=pagina_vacia("proveedor de Beta")),
        recibidos("PAY-037: cliente → 403", "clienteToken", pruebas=error(403)),
        recibidos("PAY-037: empresa_contacto → 403", "empresaToken", pruebas=error(403)),
        recibidos("PAY-037: admin_tenant → 403", "adminToken", pruebas=error(403)),
        recibidos("PAY-038: sin sesión → 401", None, pruebas=estado(401)),
    ],
}

limpieza = {
    "name": "Limpieza",
    "item": [
        req("Suspender al técnico independiente", "POST", "/v1/admin/technicians/{{tecnicoId}}/suspend",
            [JSON, CORR, auth("adminToken")], {"reason": "Cuenta de una prueba de QA."}, pruebas=estado(200)),
        req("Suspender al técnico del equipo", "POST", "/v1/admin/technicians/{{equipoId}}/suspend",
            [JSON, CORR, auth("adminToken")], {"reason": "Cuenta de una prueba de QA."}, pruebas=estado(200)),
        req("Desactivar la categoría de la prueba", "PATCH", "/v1/catalog/admin/categories/{{categoriaId}}",
            [JSON, CORR, auth("adminToken")], {"active": False}, pruebas=estado(200)),
    ],
}

coleccion = base.coleccion(
    "QUICKPATCH — SCRUM-503 Pagos recibidos del técnico y del proveedor",
    "RF-25 (SCRUM-45) contra QA, con payments.v1.yaml 1.2.0 (GET /v1/payments/received). Casos PAY-024 a PAY-038 del "
    "TD 3.1 con datos propios: el técnico ve solo sus pagos, sin el rechazado y sin datos de tarjeta; filtros por estado, "
    "paginación y límites; el proveedor ve los de su equipo y filtra por técnico; otro técnico, otro tenant (Beta) y "
    "técnicos ajenos no ven nada; cliente, empresa y admin_tenant reciben 403 y sin sesión 401. Variables: baseUrl, "
    "adminEmail y adminPassword (secretos de QA, nunca en el repositorio). Correr con --reporters cli: el reporte JSON "
    "de Newman guarda tokens.",
    [preparacion, tecnico, proveedor, fugas, limpieza],
)

destino = AQUI / "scrum-45-pagos-tecnico.postman_collection.json"
destino.write_text(json.dumps(coleccion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Colección escrita en {destino}")
