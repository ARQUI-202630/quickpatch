"""Genera la colección del pago a nombre de la empresa (SCRUM-496, historia SCRUM-43) contra QA.

Uso: python tests/e2e/generar-scrum496-pago-empresa.py
Escribe scrum-496-pago-empresa.postman_collection.json. Reutiliza los pasos de
generar-scrum490-96-cotizacion-evidencia.py (preparación, cotización y cierre) y la cuenta corporativa de
generar-scrum75-solicitud-empresa.py; los dos regeneran sus colecciones sin cambios.

Contratos: payments.v1.yaml 1.1.0 (RN-P6: cualquier empresa_contacto de la empresa paga la solicitud de la empresa; el
comprobante lo lee el pagador), service-request.v1.yaml 1.9.0 e identity.v1.yaml 1.8.0. Necesita payments 0.2.0
(quickpatch-payments#11) en QA y al administrador del tenant (adminEmail y adminPassword, secretos de QA que nunca van al
repositorio). Correr con --reporters cli: el reporte JSON de Newman guarda los cuerpos y los tokens, y no debe subirse.
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

JSON, CORR, auth, req, estado, error = base.JSON, base.CORR, base.auth, base.req, base.estado, base.error
reintentar = base.reintentar

SOLICITUD = "/v1/service-requests/{{solicitud1Id}}"
PAGO = SOLICITUD + "/payment"
FACTURACION = {"name": "Empresa QA S.A.S.", "documentType": "NIT", "documentNumber": "900123456",
               "email": "pagos.qa@quickpatch.test"}


def pago(estado_pago, campos=()):
    return [
        f"pm.test('200 con el pago en {estado_pago}', () => {{",
        "  pm.response.to.have.status(200);",
        "  const p = pm.response.json();",
        f"  pm.expect(p.status).to.eql('{estado_pago}');",
        "  pm.expect(p.amount).to.eql('185000.00');",
        "  pm.expect(p.serviceRequestId).to.eql(pm.collectionVariables.get('solicitud1Id'));",
        *("  " + c for c in campos),
        "});",
    ]


def pagar(nombre, token, pruebas):
    return req(nombre, "POST", PAGO, [JSON, CORR, auth(token)],
               {"paymentToken": "tok_sim_aprobada_{{sufijo}}", "billing": FACTURACION}, pruebas=pruebas)


def detalle(estado_esperado, nombre):
    return req(nombre, "GET", SOLICITUD, [CORR, auth("empresaToken")],
               pruebas=reintentar(f"pm.response.json().status === '{estado_esperado}'", [
                   f"pm.test('{estado_esperado}', () => pm.expect(pm.response.json().status).to.eql('{estado_esperado}'));",
               ]))


coleccion = base.coleccion(
    "QUICKPATCH — SCRUM-496 Pago de la empresa de punta a punta",
    "RF-23 (SCRUM-43, RN-P6) contra QA, con payments 0.2.0. Un empresa_contacto crea la solicitud de la empresa y acepta "
    "la cotización; con el servicio completado, otro usuario de la misma empresa ve el pago pendiente y lo paga con la "
    "pasarela simulada. ServiceRequest pasa la solicitud a pagado y el comprobante lo lee quien pagó. Casos negativos: "
    "otra empresa y un cliente hogar del tenant no ven ni pagan el pago (404), el técnico no lo consulta (403), quien creó "
    "la solicitud no lee el comprobante del colega (404) y pagar otra vez responde 409 ya-pagado. Variables: baseUrl, "
    "adminEmail y adminPassword (secretos de QA, nunca en el repositorio). Correr con --reporters cli: el reporte JSON de "
    "Newman guarda tokens.",
    [
        base.preparacion("SCRUM-496"),
        {
            "name": "1. La empresa y sus usuarios",
            "item": [
                empresa.registrar_empresa("Empresa", "empresa496.qa", "nitEmpresa", "empresaId"),
                empresa.login_empresa("quien crea la solicitud", "empresa496.qa.{{sufijo}}@quickpatch.test",
                                      "empresaToken", "empresaId"),
                req("La empresa agrega a un colega", "POST", "/v1/companies/me/users", [JSON, CORR, auth("empresaToken")],
                    {"email": "colega496.qa.{{sufijo}}@quickpatch.test", "fullName": "Colega que paga"},
                    pruebas=estado(201) + ["pm.collectionVariables.set('invitacionColega', pm.response.json().invitation.token);"]),
                req("El colega define su contraseña", "POST", "/v1/auth/password/setup", [JSON, CORR, base.CANAL],
                    {"token": "{{invitacionColega}}", "password": "{{clave}}"}, pruebas=estado(204)),
                empresa.login_empresa("el colega", "colega496.qa.{{sufijo}}@quickpatch.test", "colegaToken", "empresaId"),
                empresa.registrar_empresa("Otra Empresa", "otra496.qa", "nitOtraEmpresa", "otraEmpresaId"),
                empresa.login_empresa("la otra empresa", "otra496.qa.{{sufijo}}@quickpatch.test", "otraEmpresaToken",
                                      "otraEmpresaId"),
            ],
        },
        {
            "name": "2. Hasta el servicio completado",
            "item": [
                req("La empresa crea la solicitud (espera la réplica de la categoría)", "POST", "/v1/service-requests",
                    [JSON, CORR, auth("empresaToken")],
                    {"categoryId": "{{categoriaId}}", "description": "Prueba de punta a punta SCRUM-496, pago de la empresa",
                     "location": {"latitude": 4.6486, "longitude": -74.063}, "addressText": "Carrera 7 # 71-21, piso 8",
                     "siteName": "Sede Chapinero"},
                    pruebas=reintentar("pm.response.code !== 422", estado(201) + [
                        "pm.test('de empresa', () => pm.expect(pm.response.json().clientType).to.eql('empresa'));",
                        "pm.collectionVariables.set('solicitud1Id', pm.response.json().id);",
                    ], maximo=10)),
                req("El técnico ve la oferta", "GET", "/v1/matching/offers?status=pendiente", [CORR, auth("tecnicoToken")],
                    pruebas=[
                        "const oferta = pm.response.code === 200 && pm.response.json().items.find(x => x.serviceRequestId === pm.collectionVariables.get('solicitud1Id'));",
                        *reintentar("oferta", [
                            "pm.test('la oferta está pendiente para el técnico', () => pm.expect(oferta).to.be.ok);",
                            "if (oferta) { pm.collectionVariables.set('oferta1Id', oferta.attemptId); }",
                        ]),
                    ]),
                req("El técnico acepta", "POST", "/v1/matching/offers/{{oferta1Id}}/accept", [CORR, auth("tecnicoToken")],
                    pruebas=estado(200)),
                detalle("asignado", "La solicitud queda asignada"),
                base.emitir(1, "El técnico cotiza 185.000", "150000.00", "35000.00", 1, "cot1"),
                base.responder(1, "cot1", "accept", "Quien creó la solicitud acepta la cotización", token="empresaToken",
                               pruebas=base.decision("aceptada", "cotizacion_aceptada", 2)),
                req("El técnico inicia", "POST", SOLICITUD + "/start", [CORR, auth("tecnicoToken")], pruebas=estado(200)),
                req("El técnico sube la foto", "POST", SOLICITUD + "/evidence", [CORR, auth("tecnicoToken")],
                    archivo=base.FOTO, pruebas=estado(201)),
                req("El técnico completa", "POST", SOLICITUD + "/complete", [CORR, auth("tecnicoToken")],
                    pruebas=estado(200)),
            ],
        },
        {
            "name": "3. Quién ve y quién paga (RN-P6)",
            "item": [
                req("El colega ve el pago pendiente (espera service-request.completed en Payments)", "GET", PAGO,
                    [CORR, auth("colegaToken")],
                    pruebas=reintentar("pm.response.code === 200", pago("pendiente", ["pm.expect(p.invoiceId).to.eql(null);"]),
                                       maximo=20)),
                req("Quien creó la solicitud también lo ve", "GET", PAGO, [CORR, auth("empresaToken")],
                    pruebas=pago("pendiente")),
                req("Otra empresa no ve el pago → 404", "GET", PAGO, [CORR, auth("otraEmpresaToken")], pruebas=error(404)),
                req("Un cliente hogar del tenant no ve el pago → 404", "GET", PAGO, [CORR, auth("otroClienteToken")],
                    pruebas=error(404)),
                req("El cliente de Beta no ve el pago → 404 (RLS)", "GET", PAGO, [CORR, auth("betaToken")],
                    pruebas=error(404)),
                req("El técnico no consulta el pago → 403", "GET", PAGO, [CORR, auth("tecnicoToken")], pruebas=error(403)),
                pagar("Otra empresa no paga → 404", "otraEmpresaToken", error(404)),
                pagar("Un cliente hogar no paga → 404", "otroClienteToken", error(404)),
                pagar("El colega paga a nombre de la empresa → 200 aprobado", "colegaToken",
                      pago("aprobado", [
                          "pm.expect(p.invoiceId).to.be.a('string');",
                          "pm.collectionVariables.set('pago1Id', p.paymentId);",
                      ])),
                detalle("pagado", "ServiceRequest pasa la solicitud a pagado (payment.approved)"),
                pagar("Quien creó la solicitud paga otra vez → 409 ya-pagado", "empresaToken", error(409, "ya-pagado")),
            ],
        },
        {
            "name": "4. Comprobante del pagador",
            "item": [
                req("El colega lee su comprobante", "GET", "/v1/payments/{{pago1Id}}/invoice",
                    [CORR, auth("colegaToken"), {"key": "Accept", "value": "application/json"}],
                    pruebas=estado(200) + [
                        "pm.test('con los datos de facturación de quien pagó', () => pm.expect(JSON.stringify(pm.response.json())).to.include('Empresa QA S.A.S.'));",
                    ]),
                req("Quien creó la solicitud no lee el comprobante del colega → 404", "GET",
                    "/v1/payments/{{pago1Id}}/invoice",
                    [CORR, auth("empresaToken"), {"key": "Accept", "value": "application/json"}], pruebas=error(404)),
                req("El administrador del tenant lo lee", "GET", "/v1/payments/{{pago1Id}}/invoice",
                    [CORR, auth("adminToken"), {"key": "Accept", "value": "application/json"}], pruebas=estado(200)),
                base.disponibilidad("disponible", "El técnico queda libre"),
            ],
        },
        base.limpieza,
    ],
)

destino = AQUI / "scrum-496-pago-empresa.postman_collection.json"
destino.write_text(json.dumps(coleccion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Colección escrita en {destino}")
