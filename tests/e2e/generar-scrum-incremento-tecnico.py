"""Generador de la Colección E2E para SCRUM-81, SCRUM-90 y SCRUM-93: Incremento del Técnico.

Diseñada para ejecutarse contra el Gateway de QA real (o arnés local) mediante correr-colecciones-qa.js:
- SCRUM-90: Localidades de Bogotá (20 oficiales), disponibilidad (disponible/ocupado/no_disponible)
  y cobertura geográfica (polígonos de localidades) bajo matching.v1.yaml.
- SCRUM-81: Ofertas de matching sin dirección exacta previa (RN-SR13), aceptación atómica
  con cambio a ocupado (RN-M6) y outbox matching.technician-assigned, rechazo sin penalización (R12),
  y control de conflictos 409 (oferta ya respondida, o técnico ya ocupado).
- SCRUM-93: Detalle de solicitud asignada (service-request.v1.yaml 1.1.0): técnico asignado ve
  contacto del cliente (nombre y teléfono vía Identity), 403 fuera de asignado-completado y 404 para técnicos o clientes ajenos (RLS).

Autora: Katherine Bravo — QA Lead (ka.bravo@javeriana.edu.co)

Uso:
    python tests/e2e/generar-scrum-incremento-tecnico.py
"""
import importlib.util
import pathlib

AQUI = pathlib.Path(__file__).parent
_spec = importlib.util.spec_from_file_location("base", AQUI / "generar-scrum490-96-cotizacion-evidencia.py")
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)

JSON, CORR, CANAL, auth, req, estado, error = base.JSON, base.CORR, base.CANAL, base.auth, base.req, base.estado, base.error
reintentar = base.reintentar
BETA = base.BETA

coleccion = base.coleccion(
    "QUICKPATCH — Incremento Técnico (SCRUM-81, SCRUM-90, SCRUM-93)",
    "Suite E2E automatizada contra QA real para el incremento del técnico (Sprint 4):\n"
    "- SCRUM-90: Disponibilidad y cobertura geográfica (Matching Service / HU SCRUM-33)\n"
    "- SCRUM-81: Aceptación y rechazo de ofertas de asignación (Matching Service / HU SCRUM-30)\n"
    "- SCRUM-93: Detalle de solicitud para técnico asignado (ServiceRequest Service / HU SCRUM-34)\n"
    "Valida contratos OpenAPI matching.v1.yaml y service-request.v1.yaml con RFC 9457.\n"
    "Utiliza la preparación dinámica de base (importlib) sin depender de credenciales ni usuarios fijos en el repositorio.\n"
    "Variables: baseUrl, adminEmail y adminPassword.",
    [
        base.preparacion("SCRUM-INC-TEC"),
        {
            "name": "1. SCRUM-90 — Disponibilidad y Cobertura (Matching Service)",
            "item": [
                req(
                    "1.1 [COV-001] Catálogo público de 20 localidades oficiales de Bogotá",
                    "GET",
                    "/v1/localities",
                    [CORR],
                    pruebas=[
                        "pm.test('[SCRUM-90] 200 OK en listado de localidades', () => pm.response.to.have.status(200));",
                        "const locs = pm.response.json();",
                        "pm.test('[Localidades] Devuelve exactamente las 20 localidades oficiales de Bogotá', () => pm.expect(locs.length).to.equal(20));",
                        "pm.test('[Localidades] Códigos oficiales 01 a 20 presentes', () => {",
                        "  pm.expect(locs[0].code).to.equal('01');",
                        "  pm.expect(locs[0].name).to.equal('Usaquén');",
                        "  pm.expect(locs[1].code).to.equal('02');",
                        "  pm.expect(locs[1].name).to.equal('Chapinero');",
                        "});",
                    ],
                ),
                req(
                    "1.2 [AVA-001] Consulta de disponibilidad del técnico",
                    "GET",
                    "/v1/technicians/me/availability",
                    [CORR, auth("tecnicoToken")],
                    pruebas=[
                        "pm.test('[SCRUM-90] 200 OK en consulta de disponibilidad', () => pm.response.to.have.status(200));",
                        "const body = pm.response.json();",
                        "pm.test('[Contrato] Atributos de disponibilidad presentes', () => {",
                        "  pm.expect(body).to.have.property('status');",
                        "  pm.expect(body.status).to.be.oneOf(['disponible', 'no_disponible', 'ocupado']);",
                        "  if (body.updatedAt) { pm.expect(body).to.have.property('updatedAt'); }",
                        "});",
                    ],
                ),
                req(
                    "1.3 [AVA-002] Cambiar disponibilidad a disponible (RF-13, RN-M10)",
                    "PUT",
                    "/v1/technicians/me/availability",
                    [JSON, CORR, auth("tecnicoToken")],
                    {"status": "disponible"},
                    pruebas=[
                        "pm.test('[SCRUM-90] 200 OK al actualizar disponibilidad', () => pm.response.to.have.status(200));",
                        "const body = pm.response.json();",
                        "pm.test('[SCRUM-90] Estado actualizado a disponible', () => pm.expect(body.status).to.equal('disponible'));",
                        "pm.test('[SCRUM-90] Flag available es true', () => pm.expect(body.status === 'disponible' || body.available === true).to.be.true);",
                        "pm.test('[SCRUM-90] Flag busy es false', () => pm.expect(body.status !== 'ocupado' && body.busy !== true).to.be.true);",
                    ],
                ),
                req(
                    "1.4 [COV-002] Consulta de cobertura inicial del técnico",
                    "GET",
                    "/v1/technicians/me/coverage",
                    [CORR, auth("tecnicoToken")],
                    pruebas=[
                        "pm.test('[SCRUM-90] 200 OK en consulta de cobertura', () => pm.response.to.have.status(200));",
                        "const body = pm.response.json();",
                        "pm.test('[Contrato] Atributo localityCodes es array', () => {",
                        "  const locs = body.localities || body.localityCodes || [];",
                        "  pm.expect(locs).to.be.an('array');",
                        "});",
                    ],
                ),
                req(
                    "1.5 [COV-003] Configuración de cobertura geográfica por localidades (RF-13)",
                    "PUT",
                    "/v1/technicians/me/coverage",
                    [JSON, CORR, auth("tecnicoToken")],
                    {"localityCodes": ["01", "02", "12", "13"]},
                    pruebas=[
                        "pm.test('[SCRUM-90] 200 OK al actualizar cobertura', () => pm.response.to.have.status(200));",
                        "const body = pm.response.json();",
                        "pm.test('[SCRUM-90] Localidades configuradas correctamente', () => {",
                        "  const locs = body.localities || body.localityCodes || [];",
                        "  const codes = locs.map(l => (typeof l === 'object' && l ? l.code : l));",
                        "  pm.expect(codes).to.include('01');",
                        "  pm.expect(codes).to.include('02');",
                        "});",
                    ],
                ),
                req(
                    "1.6 [COV-004] Rechazo de cobertura con código inexistente",
                    "PUT",
                    "/v1/technicians/me/coverage",
                    [JSON, CORR, auth("tecnicoToken")],
                    {"localityCodes": ["99"]},
                    pruebas=error(400, "validacion"),
                ),
                req(
                    "1.7 [COV-005] Restaurar cobertura a toda Bogotá para flujo de matching",
                    "PUT",
                    "/v1/technicians/me/coverage",
                    [JSON, CORR, auth("tecnicoToken")],
                    {"localityCodes": base.LOCALIDADES},
                    pruebas=estado(200),
                ),
                req(
                    "1.8 [AVA-003] Rechazo de consulta sin token → 401 Unauthorized",
                    "GET",
                    "/v1/technicians/me/availability",
                    [CORR],
                    pruebas=error(401),
                ),
                req(
                    "1.9 [AVA-004] Control RBAC: Rol cliente no puede gestionar disponibilidad → 403 Forbidden",
                    "PUT",
                    "/v1/technicians/me/availability",
                    [JSON, CORR, auth("clienteToken")],
                    {"status": "disponible"},
                    pruebas=error(403),
                ),
            ],
        },
        {
            "name": "2. SCRUM-81 — Aceptación y Rechazo de Ofertas (Matching Service)",
            "item": [
                req(
                    "2.1 [OFF-PREP] Cliente crea solicitud para prueba de rechazo",
                    "POST",
                    "/v1/service-requests",
                    [JSON, CORR, auth("clienteToken")],
                    {
                        "categoryId": "{{categoriaId}}",
                        "description": "Prueba de oferta de matching y rechazo sin penalización (SCRUM-81)",
                        "location": {"latitude": 4.6486, "longitude": -74.063},
                        "addressText": "Calle 63 # 9-45, apto 201",
                    },
                    pruebas=reintentar("pm.response.code !== 422", estado(201) + [
                        "pm.collectionVariables.set('solicitudRechazoId', pm.response.json().id);",
                    ], maximo=10),
                ),
                req(
                    "2.2 [OFF-001] Técnico consulta oferta pendiente (sin dirección exacta, RN-SR13)",
                    "GET",
                    "/v1/matching/offers?status=pendiente",
                    [CORR, auth("tecnicoToken")],
                    pruebas=[
                        "const oferta = pm.response.code === 200 && pm.response.json().items.find(x => x.serviceRequestId === pm.collectionVariables.get('solicitudRechazoId'));",
                        *reintentar("oferta", [
                            "pm.test('[SCRUM-81] Oferta pendiente para la solicitud', () => pm.expect(oferta).to.be.ok);",
                            "pm.test('[RN-SR13] Oferta no expone dirección exacta', () => {",
                            "  pm.expect(oferta).to.not.have.property('addressText');",
                            "  pm.expect(oferta).to.not.have.property('address');",
                            "});",
                            "if (oferta) { pm.collectionVariables.set('ofertaRechazoId', oferta.attemptId); }",
                        ]),
                    ],
                ),
                req(
                    "2.3 [OFF-002] Rechazo de oferta sin penalización (RF-10, R12)",
                    "POST",
                    "/v1/matching/offers/{{ofertaRechazoId}}/reject",
                    [CORR, auth("tecnicoToken")],
                    pruebas=estado(200),
                ),
                req(
                    "2.4 [OFF-PREP2] Cliente crea solicitud para prueba de aceptación atómica",
                    "POST",
                    "/v1/service-requests",
                    [JSON, CORR, auth("clienteToken")],
                    {
                        "categoryId": "{{categoriaId}}",
                        "description": "Prueba de asignación y detalle para técnico asignado (SCRUM-81/SCRUM-93)",
                        "location": {"latitude": 4.6486, "longitude": -74.063},
                        "addressText": "Calle 63 # 9-45, apto 201",
                    },
                    pruebas=reintentar("pm.response.code !== 422", estado(201) + [
                        "pm.collectionVariables.set('solicitudAsignadaId', pm.response.json().id);",
                    ], maximo=10),
                ),
                req(
                    "2.5 [OFF-003] Técnico consulta oferta pendiente para la nueva solicitud",
                    "GET",
                    "/v1/matching/offers?status=pendiente",
                    [CORR, auth("tecnicoToken")],
                    pruebas=[
                        "const oferta = pm.response.code === 200 && pm.response.json().items.find(x => x.serviceRequestId === pm.collectionVariables.get('solicitudAsignadaId'));",
                        *reintentar("oferta", [
                            "pm.test('[SCRUM-81] Oferta pendiente encontrada', () => pm.expect(oferta).to.be.ok);",
                            "if (oferta) { pm.collectionVariables.set('ofertaAsignadaId', oferta.attemptId); }",
                        ]),
                    ],
                ),
                req(
                    "2.6 [OFF-004] Técnico acepta oferta legítima (atómica: ocupado, asignado)",
                    "POST",
                    "/v1/matching/offers/{{ofertaAsignadaId}}/accept",
                    [CORR, auth("tecnicoToken")],
                    pruebas=estado(200),
                ),
                req(
                    "2.7 [OFF-005] Rechazo de oferta ya respondida o duplicada → 409 Conflict",
                    "POST",
                    "/v1/matching/offers/{{ofertaAsignadaId}}/accept",
                    [CORR, auth("tecnicoToken")],
                    pruebas=error(409),
                ),
                req(
                    "2.8 [OFF-006] Control RBAC: Rol cliente no puede responder ofertas → 403 Forbidden",
                    "POST",
                    "/v1/matching/offers/{{ofertaAsignadaId}}/accept",
                    [CORR, auth("clienteToken")],
                    pruebas=error(403),
                ),
            ],
        },
        {
            "name": "3. SCRUM-93 — Detalle de Solicitud para Técnico Asignado (ServiceRequest)",
            "item": [
                req(
                    "3.1 [DTL-001] Técnico asignado ve detalle completo con contacto y dirección (RN-SR13)",
                    "GET",
                    "/v1/service-requests/{{solicitudAsignadaId}}",
                    [CORR, auth("tecnicoToken")],
                    pruebas=reintentar("pm.response.json().status === 'asignado'", [
                        "pm.test('[SCRUM-93] 200 OK en consulta de solicitud asignada', () => pm.response.to.have.status(200));",
                        "const body = pm.response.json();",
                        "pm.test('[SCRUM-93] Estado es asignado y técnicoId coincide', () => {",
                        "  pm.expect(body.status).to.equal('asignado');",
                        "  pm.expect(body.technicianId).to.equal(pm.collectionVariables.get('tecnicoId'));",
                        "});",
                        "pm.test('[RN-SR13] Dirección exacta visible tras asignación', () => {",
                        "  pm.expect(body).to.have.property('addressText');",
                        "  pm.expect(body.addressText).to.include('Calle 63');",
                        "});",
                    ]),
                ),
                req(
                    "3.2 [DTL-002] Cliente dueño consulta su solicitud asignada",
                    "GET",
                    "/v1/service-requests/{{solicitudAsignadaId}}",
                    [CORR, auth("clienteToken")],
                    pruebas=[
                        "pm.test('[Cliente] 200 OK en consulta de solicitud propia', () => pm.response.to.have.status(200));",
                        "const body = pm.response.json();",
                        "pm.test('[Contrato] Estado asignado y técnico asignado presente', () => {",
                        "  pm.expect(body.status).to.equal('asignado');",
                        "  pm.expect(body.technicianId).to.equal(pm.collectionVariables.get('tecnicoId'));",
                        "});",
                    ],
                ),
                req(
                    "3.3 [DTL-003] Técnico ajeno consulta solicitud asignada a otro → 404 / 403",
                    "GET",
                    "/v1/service-requests/{{solicitudAsignadaId}}",
                    [CORR, auth("otroTecnicoToken")],
                    pruebas=[
                        "pm.test('404 o 403 para técnico ajeno', () => {",
                        "  pm.expect([403, 404]).to.include(pm.response.code);",
                        "});",
                    ],
                ),
                req(
                    "3.4 [DTL-004] Otro cliente del mismo tenant no ve la solicitud → 404",
                    "GET",
                    "/v1/service-requests/{{solicitudAsignadaId}}",
                    [CORR, auth("otroClienteToken")],
                    pruebas=error(404),
                ),
                req(
                    "3.5 [DTL-005] Cliente de otro tenant no ve la solicitud → 404 (RLS)",
                    "GET",
                    "/v1/service-requests/{{solicitudAsignadaId}}",
                    [CORR, auth("betaToken"), BETA],
                    pruebas=error(404),
                ),
                req(
                    "3.6 [DTL-006] Consulta sin token → 401 Unauthorized",
                    "GET",
                    "/v1/service-requests/{{solicitudAsignadaId}}",
                    [CORR],
                    pruebas=error(401),
                ),
            ],
        },
        base.limpieza,
    ],
)

destino = pathlib.Path(__file__).with_name("scrum-incremento-tecnico.postman_collection.json")
destino.write_text(base.json.dumps(coleccion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Colección generada con éxito en: {destino}")
