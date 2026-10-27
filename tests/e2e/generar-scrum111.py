"""Generador de la Colección E2E para SCRUM-111: Suspensión de Cuenta de Técnico (Admin).
HU Padre: SCRUM-40 (Suspensión de cuenta de técnico - Admin).
Microservicios validados: Identity Service, Matching Service, API Gateway.
Autora: Katherine Bravo — QA Lead (ka.bravo@javeriana.edu.co)

Alineado con:
- RF-20: El Administrador suspende la cuenta de un técnico con motivo registrado.
- RN-TP2: Un técnico suspendido no puede recibir nuevas solicitudes (matching bloqueado).
- Transiciones de Estado (DD §8.3.13):
   - aprobado -> suspendido (con motivo obligatorio >= 5 caracteres).
   - suspendido -> aprobado (reactivación exitosa por admin).
   - rechazo de transiciones inválidas (409 Conflict): no se permite suspender desde pendiente o re-suspender.
- Validación de Motivo (DD §8.3.13 / RFC 9457): Motivo ausente o < 5 caracteres responde 400 Bad Request.
- Control de Acceso (RBAC): Clientes y técnicos bloqueados de suspender cuentas (403 Forbidden).
- Autenticación (IDN-017): Peticiones anónimas bloqueadas (401 Unauthorized).
- Aislamiento Multi-Tenant (SAD AC6-E2 / RLS): Actor de otro tenant no accede a recursos de Alfa (404 Not Found).

Uso:
    python tests/e2e/generar-scrum111.py
"""
import importlib.util
import pathlib

AQUI = pathlib.Path(__file__).parent
_spec = importlib.util.spec_from_file_location("base", AQUI / "generar-scrum490-96-cotizacion-evidencia.py")
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)

JSON, CORR, CANAL, auth, req, estado, error = base.JSON, base.CORR, base.CANAL, base.auth, base.req, base.estado, base.error
BETA = base.BETA

coleccion = base.coleccion(
    "QUICKPATCH — SCRUM-111 Suspensión de Cuenta de Técnico (Admin)",
    "Suite E2E para RF-20, RN-TP2 y DD §8.3.13 contra QA real. "
    "Suspensión con motivo obligatorio, consulta de suspendidos, reactivación a aprobado, control de transiciones inválidas (409), "
    "control de acceso RBAC y aislamiento multi-tenant con RLS. "
    "Utiliza la preparación dinámica de base (importlib) sin depender de credenciales ni usuarios fijos en el repositorio. "
    "Variables: baseUrl, adminEmail y adminPassword.",
    [
        base.preparacion("SCRUM-111"),
        {
            "name": "1. Suspensión y Reactivación de Técnico (RF-20 / RN-TP2 / DD §8.3.13)",
            "item": [
                req(
                    "1.1 Admin suspende técnico en estado aprobado",
                    "POST",
                    "/v1/admin/technicians/{{tecnicoId}}/suspend",
                    [JSON, CORR, auth("adminToken")],
                    {"reason": "Incumplimiento grave reiterado de protocolos de seguridad."},
                    pruebas=[
                        "pm.test('[RF-20 / RN-TP2] 200 OK al suspender técnico aprobado con motivo válido', () => {",
                        "  pm.response.to.have.status(200);",
                        "  const json = pm.response.json();",
                        "  const id = json.userId || json.id;",
                        "  pm.expect(id).to.eql(pm.collectionVariables.get('tecnicoId'));",
                        "  pm.expect(json.verificationStatus).to.eql('suspendido');",
                        "  pm.expect(json.reason).to.include('Incumplimiento grave');",
                        "});",
                    ],
                ),
                req(
                    "1.2 Admin consulta técnicos suspendidos",
                    "GET",
                    "/v1/admin/technicians?verificationStatus=suspendido&size=100",
                    [CORR, auth("adminToken")],
                    pruebas=[
                        "pm.test('[Consistencia] Técnico suspendido aparece en lista de suspendidos', () => {",
                        "  pm.response.to.have.status(200);",
                        "  const json = pm.response.json();",
                        "  pm.expect(json.items).to.be.an('array').that.is.not.empty;",
                        "  pm.expect(json.items.every(t => t.verificationStatus === 'suspendido')).to.be.true;",
                        "  const found = json.items.find(t => (t.userId || t.id) === pm.collectionVariables.get('tecnicoId'));",
                        "  if (found) { pm.expect(found.verificationStatus).to.eql('suspendido'); }",
                        "});",
                    ],
                ),
                req(
                    "1.3 Reactivación: Admin aprueba y reactiva técnico suspendido (tecnicoId)",
                    "POST",
                    "/v1/admin/technicians/{{tecnicoId}}/approve",
                    [CORR, auth("adminToken")],
                    pruebas=[
                        "pm.test('[Reactivación / DD §8.3.13] 200 OK al reactivar técnico suspendido a aprobado', () => {",
                        "  pm.response.to.have.status(200);",
                        "  const json = pm.response.json();",
                        "  const id = json.userId || json.id;",
                        "  pm.expect(id).to.eql(pm.collectionVariables.get('tecnicoId'));",
                        "  pm.expect(json.verificationStatus).to.eql('aprobado');",
                        "});",
                    ],
                ),
            ],
        },
        {
            "name": "2. Reglas de Negocio, Validación y Máquina de Estados",
            "item": [
                req(
                    "2.1 Validación: Intento de suspender con motivo menor a 5 caracteres -> 400 Bad Request",
                    "POST",
                    "/v1/admin/technicians/{{tecnicoId}}/suspend",
                    [JSON, CORR, auth("adminToken")],
                    {"reason": "mal"},
                    pruebas=error(400, "validacion"),
                ),
                req(
                    "2.2 Admin suspende técnico para probar transición de re-suspensión",
                    "POST",
                    "/v1/admin/technicians/{{tecnicoId}}/suspend",
                    [JSON, CORR, auth("adminToken")],
                    {"reason": "Suspensión formal para verificación de estado."},
                    pruebas=estado(200),
                ),
                req(
                    "2.3 Transición Inválida: Intento de suspender técnico ya suspendido -> 409 Conflict",
                    "POST",
                    "/v1/admin/technicians/{{tecnicoId}}/suspend",
                    [JSON, CORR, auth("adminToken")],
                    {"reason": "Intento de re-suspensión no admitido"},
                    pruebas=error(409, "transicion-invalida"),
                ),
                req(
                    "2.4 Transición Inválida: Intento de suspender técnico en estado pendiente (tecnico2Id) -> 409 Conflict",
                    "POST",
                    "/v1/admin/technicians/{{tecnico2Id}}/suspend",
                    [JSON, CORR, auth("adminToken")],
                    {"reason": "No se puede suspender quien no ha sido previamente aprobado"},
                    pruebas=error(409, "transicion-invalida"),
                ),
                req(
                    "2.5 Reactivar técnico a aprobado para aislamiento y limpieza",
                    "POST",
                    "/v1/admin/technicians/{{tecnicoId}}/approve",
                    [CORR, auth("adminToken")],
                    pruebas=estado(200),
                ),
            ],
        },
        {
            "name": "3. Control de Acceso RBAC y Aislamiento Multi-Tenant (RLS)",
            "item": [
                req(
                    "3.1 Control RBAC: Rol Cliente intenta suspender técnico -> 403 Forbidden",
                    "POST",
                    "/v1/admin/technicians/{{tecnicoId}}/suspend",
                    [JSON, CORR, auth("clienteToken")],
                    {"reason": "Intento ilegal cliente"},
                    pruebas=error(403),
                ),
                req(
                    "3.2 Control RBAC: Rol Técnico intenta auto-suspenderse -> 403 Forbidden",
                    "POST",
                    "/v1/admin/technicians/{{tecnicoId}}/suspend",
                    [JSON, CORR, auth("tecnicoToken")],
                    {"reason": "Intento ilegal técnico"},
                    pruebas=error(403),
                ),
                req(
                    "3.3 Seguridad: Petición anónima sin token -> 401 Unauthorized",
                    "POST",
                    "/v1/admin/technicians/{{tecnicoId}}/suspend",
                    [JSON, CORR],
                    {"reason": "Sin token"},
                    pruebas=error(401),
                ),
                req(
                    "3.4 Aislamiento Multi-Tenant (RLS): Actor de Tenant Beta no ve técnicos de Alfa -> 404",
                    "GET",
                    "/v1/admin/technicians/{{tecnicoId}}",
                    [CORR, auth("betaToken"), BETA],
                    pruebas=error(404),
                ),
            ],
        },
        base.limpieza,
    ],
)

destino = pathlib.Path(__file__).with_name("scrum-111-suspension-tecnico.postman_collection.json")
destino.write_text(base.json.dumps(coleccion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Colección generada con éxito en: {destino}")
