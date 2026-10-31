"""Genera la prueba de humo del flujo crítico contra QA (SCRUM-504, historia SCRUM-47).

Uso: python tests/e2e/generar-humo-flujo-critico.py
Escribe humo-flujo-critico.postman_collection.json. Reutiliza los pasos de generar-scrum117-pago.py y de
generar-scrum490-96-cotizacion-evidencia.py, que también regenera sus colecciones sin cambios.

Recorre una sola vez, sin casos negativos, solicitud, asignación, cotización, ejecución con foto, pago, comprobante y
calificación (RF-27, RNF-08). Crea su propia categoría, su técnico y su cliente, con una clave aleatoria que no se guarda, y
al final suspende al técnico y desactiva la categoría. Falla si tarda más de 5 minutos. Necesita al administrador del
tenant (adminEmail y adminPassword, secretos de QA que nunca van al repositorio). Correr con --reporters cli: el reporte
JSON de Newman guarda los cuerpos y los tokens, y no debe subirse.
"""
import copy
import importlib.util
import json
import pathlib

AQUI = pathlib.Path(__file__).parent
_spec = importlib.util.spec_from_file_location("pago", AQUI / "generar-scrum117-pago.py")
pago = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pago)
base = pago.base

JSON, CORR, auth, req, estado, error = base.JSON, base.CORR, base.auth, base.req, base.estado, base.error

HISTORIA = "SCRUM-504"
CALIFICACION = "/v1/service-requests/{{solicitud1Id}}/rating"
COMPROBANTE = "/v1/payments/{{pagoId}}/invoice"
LIMITE_MS = 5 * 60 * 1000

# Solo lo necesario de la preparación común: administrador, categoría, técnico aprobado, con cobertura y disponible, y un
# cliente. Se descartan el segundo técnico, el segundo cliente y el del tenant Beta, que son de los casos negativos.
_prep = base.preparacion(HISTORIA)
_nombres = [i["name"] for i in _prep["item"]]
assert _nombres[0].startswith("Login del administrador") and _nombres[6] == "El técnico queda disponible", _nombres
preparacion = {
    "name": "0. Preparación: categoría propia, técnico aprobado y cliente",
    "item": _prep["item"][0:7] + _prep["item"][9:11],
}
assert _prep["item"][10]["name"].lower().startswith("login") and "cliente" in _prep["item"][10]["name"], _nombres
# El reloj arranca con el primer paso.
preparacion["item"][0]["event"][0]["script"]["exec"].append(
    "pm.collectionVariables.set('inicioHumo', Date.now());")

# La limpieza de siempre, con la comprobación del tiempo total en su último paso.
limpieza = copy.deepcopy(base.limpieza)
limpieza["item"][-1]["event"][-1]["script"]["exec"] += [
    f"pm.test('el recorrido completo tardó menos de {LIMITE_MS // 60000} minutos', () => {{",
    "  const ms = Date.now() - Number(pm.collectionVariables.get('inicioHumo'));",
    f"  pm.expect(ms).to.be.below({LIMITE_MS});",
    "});",
]

coleccion = base.coleccion(
    "QUICKPATCH — SCRUM-504 Prueba de humo del flujo crítico",
    "RF-27 y RNF-08 (SCRUM-47) contra QA. Un solo recorrido sin casos negativos: el cliente crea la solicitud, el técnico "
    "acepta la oferta, cotiza, el cliente acepta, el técnico inicia, sube la foto y completa, el cliente paga con la "
    "tarjeta simulada aprobada, consulta el comprobante y califica el servicio. Crea sus propios datos y los desactiva al "
    "final. Falla si tarda más de 5 minutos. Variables: baseUrl, adminEmail y adminPassword (secretos de QA, nunca en el "
    "repositorio). Correr con --reporters cli: el reporte JSON de Newman guarda tokens.",
    [
        preparacion,
        {
            "name": "1. Solicitud y asignación",
            "item": base.asignar(1, HISTORIA),
        },
        {
            "name": "2. Cotización",
            "item": [
                base.emitir(1, "El técnico cotiza 185.000", "150000.00", "35000.00", 1, "cot1"),
                base.responder(1, "cot1", "accept", "El cliente acepta la cotización",
                               pruebas=base.decision("aceptada", "cotizacion_aceptada", 2)),
            ],
        },
        {
            "name": "3. Ejecución con foto",
            "item": [
                req("El técnico inicia", "POST", "/v1/service-requests/{{solicitud1Id}}/start",
                    [CORR, auth("tecnicoToken")], pruebas=estado(200)),
                req("El técnico sube la foto", "POST", "/v1/service-requests/{{solicitud1Id}}/evidence",
                    [CORR, auth("tecnicoToken")], archivo=base.FOTO, pruebas=estado(201)),
                req("El técnico completa", "POST", "/v1/service-requests/{{solicitud1Id}}/complete",
                    [CORR, auth("tecnicoToken")], pruebas=estado(200)),
            ],
        },
        {
            "name": "4. Pago y comprobante",
            "item": [
                req("El cliente ve el pago pendiente (espera service-request.completed en Payments)", "GET", pago.PAGO,
                    [CORR, auth("clienteToken")],
                    pruebas=base.reintentar("pm.response.code === 200", pago.pago("pendiente"), maximo=20)),
                pago.pagar("El cliente paga con la tarjeta aprobada", "tok_sim_aprobada_",
                           pago.pago("aprobado", [
                               "pm.expect(p.invoiceId).to.be.a('string');",
                               "pm.collectionVariables.set('pagoId', p.paymentId);",
                               "pm.collectionVariables.set('comprobanteId', p.invoiceId);",
                           ])),
                base.detalle(1, "pagado", "ServiceRequest pasa la solicitud a pagado (payment.approved)"),
                req("El cliente ve el comprobante", "GET", COMPROBANTE, [CORR, auth("clienteToken")],
                    pruebas=[
                        "pm.test('200 con el comprobante del pago', () => {",
                        "  pm.response.to.have.status(200);",
                        "  const c = pm.response.json();",
                        "  pm.expect(c.invoiceId).to.eql(pm.collectionVariables.get('comprobanteId'));",
                        "  pm.expect(c.paymentId).to.eql(pm.collectionVariables.get('pagoId'));",
                        "  pm.expect(c.amount).to.eql('185000.00');",
                        "  pm.expect(c.invoiceNumber).to.match(/^QP-[0-9]{8}-[0-9A-F]{10}$/);",
                        "});",
                    ]),
            ],
        },
        {
            "name": "5. Calificación",
            "item": [
                req("El cliente califica el servicio pagado", "POST", CALIFICACION, [JSON, CORR, auth("clienteToken")],
                    {"score": 5, "comment": "Servicio de la prueba de humo."},
                    pruebas=[
                        "pm.test('201 con el contrato Rating', () => {",
                        "  pm.response.to.have.status(201);",
                        "  const r = pm.response.json();",
                        "  pm.expect(r.serviceRequestId).to.eql(pm.collectionVariables.get('solicitud1Id'));",
                        "  pm.expect(r.score).to.eql(5);",
                        "  pm.expect(r.ratedAt).to.be.a('string');",
                        "});",
                    ]),
                req("Calificar otra vez → 409 ya-calificada (RN-R2)", "POST", CALIFICACION,
                    [JSON, CORR, auth("clienteToken")], {"score": 4}, pruebas=error(409, "ya-calificada")),
            ],
        },
        limpieza,
    ],
)

destino = AQUI / "humo-flujo-critico.postman_collection.json"
destino.write_text(json.dumps(coleccion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Colección escrita en {destino}")
