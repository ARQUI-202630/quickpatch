"""Genera la colección del comprobante del pago (SCRUM-495, historia SCRUM-44) contra QA.

Uso: python tests/e2e/generar-scrum495-comprobante.py
Escribe scrum-495-comprobante.postman_collection.json. Reutiliza los pasos de generar-scrum117-pago.py (hasta el servicio
completado), que también regenera sus colecciones sin cambios.

Contrato: payments.v1.yaml 1.1.0, GET /v1/payments/{id}/invoice en JSON o PDF según Accept. El comprobante no tiene
validez fiscal (SRS DR-03). Necesita al administrador del tenant (adminEmail y adminPassword, secretos de QA que nunca van
al repositorio). Correr con --reporters cli: el reporte JSON de Newman guarda los cuerpos y los tokens, y no debe subirse.
"""
import importlib.util
import json
import pathlib

AQUI = pathlib.Path(__file__).parent
_spec = importlib.util.spec_from_file_location("pago", AQUI / "generar-scrum117-pago.py")
pago = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pago)
base = pago.base

JSON, CORR, auth, req, estado, error = base.JSON, base.CORR, base.auth, base.req, base.estado, base.error

COMPROBANTE = "/v1/payments/{{pagoId}}/invoice"
PDF = {"key": "Accept", "value": "application/pdf"}
EMPRESA = {"name": "Inversiones Andinas QA S.A.S.", "documentType": "NIT", "documentNumber": "900123456-7",
           "email": "pagos.qa@quickpatch.test"}
CAMPOS = ["amount", "concept", "currency", "fiscalValidity", "invoiceId", "invoiceNumber", "issuedAt", "payer", "paymentId",
          "serviceRequestId"]

comprobante_json = [
    "pm.test('200 con el contrato Invoice', () => {",
    "  pm.response.to.have.status(200);",
    "  const c = pm.response.json();",
    f"  pm.expect(Object.keys(c).sort()).to.eql({json.dumps(CAMPOS)});",
    "  pm.expect(c.invoiceId).to.eql(pm.collectionVariables.get('comprobanteId'));",
    "  pm.expect(c.paymentId).to.eql(pm.collectionVariables.get('pagoId'));",
    "  pm.expect(c.serviceRequestId).to.eql(pm.collectionVariables.get('solicitud1Id'));",
    "  pm.expect(c.invoiceNumber).to.match(/^QP-[0-9]{8}-[0-9A-F]{10}$/);",
    "  pm.expect(c.amount).to.eql('185000.00');",
    "  pm.expect(c.currency).to.eql('COP');",
    "  pm.expect(c.fiscalValidity).to.eql(false);",
    f"  pm.expect(c.payer).to.eql({json.dumps(EMPRESA, ensure_ascii=False)});",
    "  pm.collectionVariables.set('numeroComprobante', c.invoiceNumber);",
    "});",
]

comprobante_pdf = [
    "pm.test('200 con el PDF como adjunto', () => {",
    "  pm.response.to.have.status(200);",
    "  pm.expect(pm.response.headers.get('Content-Type')).to.include('application/pdf');",
    "  pm.expect(pm.response.headers.get('Content-Disposition')).to.include("
    "pm.collectionVariables.get('numeroComprobante') + '.pdf');",
    "  pm.expect(pm.response.text().startsWith('%PDF-')).to.be.true;",
    "});",
]

coleccion = base.coleccion(
    "QUICKPATCH — SCRUM-495 Comprobante del pago de punta a punta",
    "RF-24 (SCRUM-44) contra QA, con payments.v1.yaml 1.1.0. Después del pago aprobado con NIT, el pagador consulta el "
    "comprobante en JSON (contrato Invoice, NIT, fiscalValidity = false) y en PDF (Accept: application/pdf, adjunto con el "
    "número), y el administrador del tenant también lo ve. Casos negativos: técnico (403), otro cliente y cliente de otro "
    "tenant (404 por RLS), un pago inexistente (404) y un Accept que no es JSON ni PDF (406). Variables: baseUrl, "
    "adminEmail y adminPassword (secretos de QA, nunca en el repositorio). Correr con --reporters cli: el reporte JSON de "
    "Newman guarda tokens.",
    [
        base.preparacion("SCRUM-495"),
        pago.hasta_completado,
        {
            "name": "2. Pago aprobado con NIT",
            "item": [
                req("El cliente ve el pago pendiente (espera service-request.completed en Payments)", "GET", pago.PAGO,
                    [CORR, auth("clienteToken")],
                    pruebas=base.reintentar("pm.response.code === 200", pago.pago("pendiente"), maximo=20)),
                req("Paga con la tarjeta aprobada y factura con NIT", "POST", pago.PAGO, [JSON, CORR, auth("clienteToken")],
                    {"paymentToken": "tok_sim_aprobada_{{sufijo}}", "billing": EMPRESA},
                    pruebas=pago.pago("aprobado", [
                        "pm.expect(p.invoiceId).to.be.a('string');",
                        "pm.collectionVariables.set('pagoId', p.paymentId);",
                        "pm.collectionVariables.set('comprobanteId', p.invoiceId);",
                    ])),
            ],
        },
        {
            "name": "3. Comprobante",
            "item": [
                req("El pagador ve el comprobante en JSON", "GET", COMPROBANTE, [CORR, auth("clienteToken")],
                    pruebas=comprobante_json),
                req("El pagador descarga el PDF", "GET", COMPROBANTE, [PDF, CORR, auth("clienteToken")],
                    pruebas=comprobante_pdf),
                req("El administrador del tenant ve el comprobante", "GET", COMPROBANTE, [CORR, auth("adminToken")],
                    pruebas=estado(200)),
                req("Un Accept que no es JSON ni PDF → 406", "GET", COMPROBANTE,
                    [{"key": "Accept", "value": "text/html"}, CORR, auth("clienteToken")], pruebas=error(406)),
            ],
        },
        {
            "name": "4. Accesos",
            "item": [
                req("El técnico no ve el comprobante → 403", "GET", COMPROBANTE, [CORR, auth("tecnicoToken")],
                    pruebas=error(403)),
                req("Otro cliente no ve el comprobante → 404", "GET", COMPROBANTE, [CORR, auth("otroClienteToken")],
                    pruebas=error(404, "no-encontrado")),
                req("El cliente de otro tenant no ve el comprobante → 404 (RLS)", "GET", COMPROBANTE,
                    [CORR, auth("betaToken")], pruebas=error(404)),
                req("Un pago que no existe → 404", "GET", "/v1/payments/{{$guid}}/invoice", [CORR, auth("clienteToken")],
                    pruebas=error(404)),
            ],
        },
        base.limpieza,
    ],
)

destino = AQUI / "scrum-495-comprobante.postman_collection.json"
destino.write_text(json.dumps(coleccion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Colección escrita en {destino}")
