"""Genera la colección del seguimiento de estado en tiempo real (SCRUM-84, historia SCRUM-31) contra QA.

Uso: python tests/e2e/generar-scrum84.py
Escribe scrum-84-seguimiento-estado.postman_collection.json. Reutiliza los pasos de
generar-scrum490-96-cotizacion-evidencia.py (preparación con técnico aprobado y clientes, asignación, cotización,
y limpieza al final).

Contratos: service-request.v1.yaml 1.7.0, identity.v1.yaml y matching.v1.yaml:
- Ciclo de 4 estados: buscando_tecnico -> asignado -> en_progreso -> completado (RF-11, SCRUM-31).
- Transición a 'en_progreso' mediante POST /v1/service-requests/{id}/start (SCRUM-35).
- Requisito de evidencia fotográfica previa a completar: POST /v1/service-requests/{id}/evidence con foto de fixtures/.
- Transición a 'completado' mediante POST /v1/service-requests/{id}/complete (SCRUM-35).
- Controles de seguridad RBAC (técnico y cliente), transiciones inválidas (409) y aislamiento multi-tenant RLS (404).

Necesita al administrador del tenant (adminEmail y adminPassword, secretos de QA que nunca van al repositorio)
para la categoría y el técnico. Correr con --reporters cli: el reporte JSON de Newman guarda tokens.
"""
import importlib.util
import pathlib

AQUI = pathlib.Path(__file__).parent
_spec = importlib.util.spec_from_file_location("base", AQUI / "generar-scrum490-96-cotizacion-evidencia.py")
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)

JSON, CORR, auth, req, estado, error = base.JSON, base.CORR, base.auth, base.req, base.estado, base.error
reintentar, detalle = base.reintentar, base.detalle

coleccion = base.coleccion(
    "QUICKPATCH — SCRUM-84 Seguimiento de estado en tiempo real de punta a punta",
    "RF-11 (SCRUM-31) y SCRUM-35 contra QA, con service-request.v1.yaml 1.7.0. La solicitud recorre los cuatro estados: "
    "buscando_tecnico al crearse, asignado tras la aceptación de la oferta (matching.technician-assigned), "
    "en_progreso al iniciar el técnico con la cotización aceptada (POST /start), y completado al terminar el servicio "
    "(POST /complete) habiendo subido previamente la foto de evidencia obligatoria desde fixtures/evidencia-1x1.png. "
    "El cliente visualiza la actualización y los datos del técnico en cada estado. Casos negativos: cliente que intenta "
    "iniciar o completar (403), otro cliente del mismo tenant (404), cliente de otro tenant (404 por RLS), sin token (401), "
    "y transiciones inválidas al completar dos veces (409). "
    "Variables: baseUrl, adminEmail y adminPassword (secretos de QA, nunca en el repositorio). "
    "Correr con --reporters cli: el reporte JSON de Newman guarda tokens.",
    [
        base.preparacion("SCRUM-84"),
        {
            "name": "1. Ciclo de estados: buscando_tecnico -> asignado -> en_progreso -> completado",
            "item": [
                *base.asignar(1, "SCRUM-84"),
                req("El cliente ve la solicitud asignada y datos del técnico (RF-11, RF-14)", "GET",
                    "/v1/service-requests/{{solicitud1Id}}", [CORR, auth("clienteToken")],
                    pruebas=[
                        "pm.test('200 asignado con datos del técnico', () => {",
                        "  pm.response.to.have.status(200);",
                        "  const r = pm.response.json();",
                        "  pm.expect(r.status).to.eql('asignado');",
                        "  pm.expect(r.technicianId).to.eql(pm.collectionVariables.get('tecnicoId'));",
                        "});",
                    ]),
                base.emitir(1, "El técnico cotiza la reparación previa a iniciar", "120000.00", "45000.00", 1, "cot1"),
                base.responder(1, "cot1", "accept", "El cliente acepta la cotización",
                               pruebas=base.decision("aceptada", "cotizacion_aceptada", 2)),
                req("El técnico inicia el trabajo (pasa a en_progreso / SCRUM-35)", "POST",
                    "/v1/service-requests/{{solicitud1Id}}/start", [CORR, auth("tecnicoToken")],
                    pruebas=estado(200)),
                detalle(1, "en_progreso", "El cliente ve la solicitud en_progreso (RF-11)"),
                req("El técnico sube foto de evidencia obligatoria antes de completar", "POST",
                    "/v1/service-requests/{{solicitud1Id}}/evidence", [CORR, auth("tecnicoToken")],
                    archivo=base.FOTO, pruebas=estado(201)),
                req("El técnico completa el trabajo (pasa a completado / SCRUM-35)", "POST",
                    "/v1/service-requests/{{solicitud1Id}}/complete", [CORR, auth("tecnicoToken")],
                    pruebas=estado(200)),
                detalle(1, "completado", "El cliente ve la solicitud completada (RF-11)"),
            ],
        },
        {
            "name": "2. Controles de acceso RBAC, transiciones inválidas y aislamiento RLS",
            "item": [
                req("El cliente no puede iniciar el servicio → 403", "POST",
                    "/v1/service-requests/{{solicitud1Id}}/start", [CORR, auth("clienteToken")],
                    pruebas=error(403)),
                req("El cliente no puede completar el servicio → 403", "POST",
                    "/v1/service-requests/{{solicitud1Id}}/complete", [CORR, auth("clienteToken")],
                    pruebas=error(403)),
                req("Completar un servicio ya completado → 409 transicion-invalida", "POST",
                    "/v1/service-requests/{{solicitud1Id}}/complete", [CORR, auth("tecnicoToken")],
                    pruebas=error(409, "transicion-invalida")),
                req("Sin token → 401", "GET", "/v1/service-requests/{{solicitud1Id}}", [CORR],
                    pruebas=error(401)),
                req("Otro cliente del mismo tenant no ve la solicitud → 404", "GET",
                    "/v1/service-requests/{{solicitud1Id}}", [CORR, auth("otroClienteToken")],
                    pruebas=error(404)),
                req("Cliente de otro tenant no ve la solicitud → 404 (RLS)", "GET",
                    "/v1/service-requests/{{solicitud1Id}}", [CORR, auth("betaToken")],
                    pruebas=error(404)),
            ],
        },
        base.limpieza,
    ],
)

destino = pathlib.Path(__file__).with_name("scrum-84-seguimiento-estado.postman_collection.json")
destino.write_text(base.json.dumps(coleccion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Colección generada exitosamente en {destino}")
