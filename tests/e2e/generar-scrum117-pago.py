"""Genera la colección del pago con la pasarela simulada (SCRUM-117) contra QA.

Uso: python tests/e2e/generar-scrum117-pago.py
Escribe scrum-117-pago.postman_collection.json. Reutiliza los pasos de generar-scrum490-96-cotizacion-evidencia.py
(preparación, oferta, cotización, inicio, evidencia y cierre), que también regenera sus dos colecciones sin cambios.

Contratos: payments.v1.yaml 1.0.0 y service-request.v1.yaml 1.7.0, con la pasarela simulada del ADR-009 modificado: los
tokens tok_sim_aprobada_…, tok_sim_rechazada_… y tok_sim_error_… son los que genera el tokenizador de la app con las tres
tarjetas de prueba. Necesita al administrador del tenant (adminEmail y adminPassword, secretos de QA que nunca van al
repositorio). Correr con --reporters cli: el reporte JSON de Newman guarda los cuerpos y los tokens, y no debe subirse.
"""
import importlib.util
import json
import pathlib

AQUI = pathlib.Path(__file__).parent
_spec = importlib.util.spec_from_file_location("base", AQUI / "generar-scrum490-96-cotizacion-evidencia.py")
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)

JSON, CORR, auth, req, estado, error = base.JSON, base.CORR, base.auth, base.req, base.estado, base.error
reintentar, detalle = base.reintentar, base.detalle

PAGO = "/v1/service-requests/{{solicitud1Id}}/payment"
FACTURACION = {"name": "Prueba QA SCRUM-117", "documentType": "CC", "documentNumber": "52123456",
               "email": "pago.qa@quickpatch.test"}
CAMPOS_PAGO = ["amount", "createdAt", "invoiceId", "paymentId", "processedAt", "reasonCode", "serviceRequestId", "status"]


def pagar(nombre, token, pruebas, cliente="clienteToken"):
    return req(nombre, "POST", PAGO, [JSON, CORR, auth(cliente)],
               {"paymentToken": token + "{{sufijo}}", "billing": FACTURACION}, pruebas=pruebas)


def pago(estado_pago, campos=()):
    return [
        f"pm.test('200 con el contrato Payment en {estado_pago}', () => {{",
        "  pm.response.to.have.status(200);",
        "  const p = pm.response.json();",
        f"  pm.expect(Object.keys(p).sort()).to.eql({json.dumps(CAMPOS_PAGO)});",
        f"  pm.expect(p.status).to.eql('{estado_pago}');",
        "  pm.expect(p.amount).to.eql('185000.00');",
        "  pm.expect(p.serviceRequestId).to.eql(pm.collectionVariables.get('solicitud1Id'));",
        *("  " + c for c in campos),
        "});",
    ]


hasta_completado = {
    "name": "1. Hasta el servicio completado",
    "item": [
        *base.asignar(1, "SCRUM-117"),
        base.emitir(1, "El técnico cotiza 185.000", "150000.00", "35000.00", 1, "cot1"),
        base.responder(1, "cot1", "accept", "El cliente acepta", pruebas=base.decision("aceptada", "cotizacion_aceptada", 2)),
        req("El técnico inicia", "POST", "/v1/service-requests/{{solicitud1Id}}/start", [CORR, auth("tecnicoToken")],
            pruebas=estado(200)),
        req("El técnico sube la foto", "POST", "/v1/service-requests/{{solicitud1Id}}/evidence", [CORR, auth("tecnicoToken")],
            archivo=base.FOTO, pruebas=estado(201)),
        req("El técnico completa", "POST", "/v1/service-requests/{{solicitud1Id}}/complete", [CORR, auth("tecnicoToken")],
            pruebas=estado(200)),
    ],
}

coleccion = base.coleccion(
    "QUICKPATCH — SCRUM-117 Pago con la pasarela simulada de punta a punta",
    "RF-22 (SCRUM-42) contra QA, con payments.v1.yaml 1.0.0 y la pasarela simulada del ADR-009 modificado. Payments crea "
    "el pago pendiente al consumir service-request.completed con el total de la cotización aceptada; el cliente paga con "
    "el token del dispositivo. Rechazo por fondos (200 rechazado, la solicitud sigue en completado), pasarela sin "
    "respuesta (502 y 409 pago-en-curso) que la conciliación cierra como rechazado, y aprobado con comprobante, después "
    "del cual ServiceRequest pasa la solicitud a pagado y un segundo pago responde 409 ya-pagado. Casos negativos: "
    "técnico (403), otro cliente y cliente de otro tenant (404 por RLS), tarjeta en vez de token y campo desconocido "
    "(400). Variables: baseUrl, adminEmail y adminPassword (secretos de QA, nunca en el repositorio). Correr con "
    "--reporters cli: el reporte JSON de Newman guarda tokens.",
    [
        base.preparacion("SCRUM-117"),
        hasta_completado,
        {
            "name": "2. Pago pendiente y accesos",
            "item": [
                req("El cliente ve el pago pendiente (espera service-request.completed en Payments)", "GET", PAGO,
                    [CORR, auth("clienteToken")],
                    pruebas=reintentar("pm.response.code === 200", pago("pendiente", [
                        "pm.expect(p.invoiceId).to.eql(null);",
                        "pm.expect(p.reasonCode).to.eql(null);",
                    ]), maximo=20)),
                req("El técnico no consulta el pago → 403", "GET", PAGO, [CORR, auth("tecnicoToken")], pruebas=error(403)),
                req("Otro cliente no ve el pago → 404", "GET", PAGO, [CORR, auth("otroClienteToken")], pruebas=error(404)),
                req("El cliente de otro tenant no ve el pago → 404 (RLS)", "GET", PAGO, [CORR, auth("betaToken")],
                    pruebas=error(404)),
                req("Otro cliente no paga → 404", "POST", PAGO, [JSON, CORR, auth("otroClienteToken")],
                    {"paymentToken": "tok_sim_aprobada_x{{sufijo}}", "billing": FACTURACION}, pruebas=error(404)),
                req("El número de la tarjeta en vez del token → 400 en paymentToken", "POST", PAGO,
                    [JSON, CORR, auth("clienteToken")], {"paymentToken": "4242424242424242", "billing": FACTURACION},
                    pruebas=error(400, "validacion") + [
                        "pm.test('error en paymentToken', () => pm.expect(pm.response.json().errors).to.have.property('paymentToken'));",
                    ]),
                req("Un campo que el contrato no define → 400", "POST", PAGO, [JSON, CORR, auth("clienteToken")],
                    {"paymentToken": "tok_sim_aprobada_x", "billing": FACTURACION, "cardNumber": "4242424242424242"},
                    pruebas=error(400, "validacion")),
            ],
        },
        {
            "name": "3. Rechazo y pasarela sin respuesta",
            "item": [
                pagar("Tarjeta rechazada por fondos → 200 rechazado", "tok_sim_rechazada_",
                      pago("rechazado", ["pm.expect(p.reasonCode).to.eql('fondos_insuficientes');",
                                         "pm.expect(p.invoiceId).to.eql(null);",
                                         "pm.expect(p.processedAt).to.be.a('string');"])),
                detalle(1, "completado", "La solicitud sigue en completado (RN-SR5)"),
                pagar("La pasarela no responde → 502 pasarela-sin-respuesta", "tok_sim_error_",
                      error(502, "pasarela-sin-respuesta")),
                pagar("Pagar otra vez mientras se concilia → 409 pago-en-curso", "tok_sim_aprobada_",
                      error(409, "pago-en-curso")),
                req("La conciliación cierra el pago como rechazado (AC9-E5)", "GET", PAGO, [CORR, auth("clienteToken")],
                    pruebas=reintentar("pm.response.json().status === 'rechazado'", pago("rechazado", [
                        "pm.expect(p.reasonCode).to.eql('pasarela_sin_respuesta');",
                    ]), maximo=45)),
            ],
        },
        {
            "name": "4. Pago aprobado",
            "item": [
                pagar("Tarjeta aprobada → 200 aprobado con comprobante", "tok_sim_aprobada_",
                      pago("aprobado", ["pm.expect(p.invoiceId).to.be.a('string');",
                                        "pm.expect(p.reasonCode).to.eql(null);"])),
                detalle(1, "pagado", "ServiceRequest pasa la solicitud a pagado (payment.approved, RN-SR4)"),
                pagar("Pagar otra vez → 409 ya-pagado", "tok_sim_aprobada_", error(409, "ya-pagado")),
                req("El pago queda aprobado", "GET", PAGO, [CORR, auth("clienteToken")],
                    pruebas=pago("aprobado", ["pm.expect(p.invoiceId).to.be.a('string');"])),
            ],
        },
        base.limpieza,
    ],
)

destino = AQUI / "scrum-117-pago.postman_collection.json"
destino.write_text(json.dumps(coleccion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Colección escrita en {destino}")
