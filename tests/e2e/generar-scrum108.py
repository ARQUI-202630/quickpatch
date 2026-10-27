"""Generador de la Colección E2E para SCRUM-108: Aprobación/Rechazo de Técnicos y Proveedores (Admin).
HU Padre: SCRUM-39 (Aprobación/rechazo de técnicos y proveedores - Admin).
Microservicios validados: Identity Service, API Gateway.
Autora: Katherine Bravo — QA Lead (ka.bravo@javeriana.edu.co)

Alineado con:
- RF-19: El Administrador del Tenant aprueba o rechaza solicitudes de registro de técnicos y proveedores.
- RN-TP1: Solo técnicos aprobados pueden participar en matching.
- Transiciones de Estado (DD §8.3.13):
   - pendiente -> aprobado
   - pendiente -> rechazado (con motivo obligatorio >= 5 caracteres)
   - rechazo de transiciones inválidas (409 Conflict): no se permite aprobar o rechazar técnico ya aprobado.
- Validación de Motivo (DD §8.3.13 / RFC 9457): Motivo ausente o < 5 caracteres responde 400 Bad Request.
- Control de Acceso (RBAC): Clientes y técnicos bloqueados de endpoints administrativos (403 Forbidden).
- Autenticación (IDN-017): Peticiones anónimas bloqueadas (401 Unauthorized).
- Aislamiento Multi-Tenant (SAD AC6-E2 / RLS): Actor de otro tenant no accede a recursos de Alfa (404 Not Found).

Uso:
    python tests/e2e/generar-scrum108.py
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
    "QUICKPATCH — SCRUM-108 Aprobación y Rechazo de Técnicos (Admin)",
    "Suite E2E para RF-19, RN-TP1 y DD §8.3.13 contra QA real. "
    "Verificación, aprobación, rechazo con motivo, máquina de estados, control RBAC y aislamiento multi-tenant con RLS. "
    "Utiliza la preparación dinámica de base (importlib) sin depender de credenciales ni usuarios fijos en el repositorio. "
    "Variables: baseUrl, adminEmail y adminPassword.",
    [
        base.preparacion("SCRUM-108"),
        {
            "name": "1. Consulta y Filtros de Verificación (RF-19 / DD §8.2.1)",
            "item": [
                req(
                    "1.1 Admin lista técnicos pendientes de verificación",
                    "GET",
                    "/v1/admin/technicians?verificationStatus=pendiente&size=100",
                    [CORR, auth("adminToken")],
                    pruebas=[
                        "pm.test('[RF-19] 200 OK al listar técnicos pendientes', () => {",
                        "  pm.response.to.have.status(200);",
                        "  const json = pm.response.json();",
                        "  pm.expect(json).to.have.property('items');",
                        "  pm.expect(json.items).to.be.an('array').that.is.not.empty;",
                        "  pm.expect(json.items.every(t => t.verificationStatus === 'pendiente')).to.be.true;",
                        "  const pending = json.items.find(t => (t.userId || t.id) === pm.collectionVariables.get('tecnico2Id'));",
                        "  if (pending) { pm.expect(pending.verificationStatus).to.eql('pendiente'); }",
                        "});",
                    ],
                ),
                req(
                    "1.2 Admin lista técnicos aprobados",
                    "GET",
                    "/v1/admin/technicians?verificationStatus=aprobado",
                    [CORR, auth("adminToken")],
                    pruebas=[
                        "pm.test('[Filtro status=aprobado] 200 OK y técnico aprobado listado', () => {",
                        "  pm.response.to.have.status(200);",
                        "  const json = pm.response.json();",
                        "  pm.expect(json.items).to.be.an('array');",
                        "  const app = json.items.find(t => (t.userId || t.id) === pm.collectionVariables.get('tecnicoId'));",
                        "  pm.expect(app).to.exist;",
                        "  pm.expect(app.verificationStatus).to.eql('aprobado');",
                        "});",
                    ],
                ),
            ],
        },
        {
            "name": "2. Aprobación de Técnico (RF-19 / RN-TP1 / DD §8.3.13)",
            "item": [
                req(
                    "2.1 Admin aprueba técnico pendiente (tecnico2Id)",
                    "POST",
                    "/v1/admin/technicians/{{tecnico2Id}}/approve",
                    [CORR, auth("adminToken")],
                    pruebas=[
                        "pm.test('[RF-19 / RN-TP1] 200 OK al aprobar perfil técnico', () => {",
                        "  pm.response.to.have.status(200);",
                        "  const json = pm.response.json();",
                        "  const id = json.userId || json.id;",
                        "  pm.expect(id).to.eql(pm.collectionVariables.get('tecnico2Id'));",
                        "  pm.expect(json.verificationStatus).to.eql('aprobado');",
                        "});",
                    ],
                ),
                req(
                    "2.2 Admin verifica que técnico aprobado ya no está en pendientes",
                    "GET",
                    "/v1/admin/technicians?verificationStatus=pendiente",
                    [CORR, auth("adminToken")],
                    pruebas=[
                        "pm.test('[Consistencia] El técnico aprobado ya no aparece en pendientes', () => {",
                        "  pm.response.to.have.status(200);",
                        "  const json = pm.response.json();",
                        "  const found = json.items.find(t => (t.userId || t.id) === pm.collectionVariables.get('tecnico2Id'));",
                        "  pm.expect(found).to.be.undefined;",
                        "});",
                    ],
                ),
                req(
                    "2.3 Transición Inválida: Intento de aprobar técnico ya aprobado -> 409 Conflict",
                    "POST",
                    "/v1/admin/technicians/{{tecnicoId}}/approve",
                    [CORR, auth("adminToken")],
                    pruebas=error(409, "transicion-invalida"),
                ),
            ],
        },
        {
            "name": "3. Rechazo de Técnico con Motivo (RF-19 / DD §8.3.13)",
            "item": [
                req(
                    "3.0 Registro dinámico de técnico para prueba de rechazo",
                    "POST",
                    "/v1/auth/register/technician",
                    [JSON, CORR, CANAL],
                    {
                        "email": "tecnico3.qa.{{sufijo}}@quickpatch.test",
                        "password": "{{clave}}",
                        "fullName": "Técnico Rechazo QA",
                        "phone": "3007654399",
                        "documentId": "{{documento3}}",
                        "specialtyId": "{{categoriaId}}",
                        "role": "tecnico",
                    },
                    previo=["pm.collectionVariables.set('documento3', String(Date.now() + 15).slice(-10));"],
                    pruebas=estado(201) + ["pm.collectionVariables.set('tecnico3Id', pm.response.json().id);"],
                ),
                req(
                    "3.1 Validación: Intento de rechazar sin motivo válido (< 5 caracteres) -> 400 Bad Request",
                    "POST",
                    "/v1/admin/technicians/{{tecnico3Id}}/reject",
                    [JSON, CORR, auth("adminToken")],
                    {"reason": "no"},
                    pruebas=error(400, "validacion"),
                ),
                req(
                    "3.2 Admin rechaza técnico con motivo válido",
                    "POST",
                    "/v1/admin/technicians/{{tecnico3Id}}/reject",
                    [JSON, CORR, auth("adminToken")],
                    {"reason": "Documento de identidad ilegible y certificado técnico vencido."},
                    pruebas=[
                        "pm.test('[RF-19] 200 OK al rechazar técnico con motivo fundamentado', () => {",
                        "  pm.response.to.have.status(200);",
                        "  const json = pm.response.json();",
                        "  const id = json.userId || json.id;",
                        "  pm.expect(id).to.eql(pm.collectionVariables.get('tecnico3Id'));",
                        "  pm.expect(json.verificationStatus).to.eql('rechazado');",
                        "  pm.expect(json.reason).to.include('ilegible');",
                        "});",
                    ],
                ),
                req(
                    "3.3 Transición Inválida: Intento de rechazar técnico aprobado -> 409 Conflict",
                    "POST",
                    "/v1/admin/technicians/{{tecnicoId}}/reject",
                    [JSON, CORR, auth("adminToken")],
                    {"reason": "Rechazo posterior no permitido según máquina de estados"},
                    pruebas=error(409, "transicion-invalida"),
                ),
            ],
        },
        {
            "name": "4. Control de Acceso RBAC y Aislamiento Multi-Tenant (RLS)",
            "item": [
                req(
                    "4.1 Control RBAC: Cliente intenta aprobar técnico -> 403 Forbidden",
                    "POST",
                    "/v1/admin/technicians/{{tecnicoId}}/approve",
                    [CORR, auth("clienteToken")],
                    pruebas=error(403),
                ),
                req(
                    "4.2 Control RBAC: Técnico intenta auto-aprobarse -> 403 Forbidden",
                    "POST",
                    "/v1/admin/technicians/{{tecnicoId}}/approve",
                    [CORR, auth("tecnicoToken")],
                    pruebas=error(403),
                ),
                req(
                    "4.3 Seguridad: Consulta anónima sin token -> 401 Unauthorized",
                    "GET",
                    "/v1/admin/technicians",
                    [CORR],
                    pruebas=error(401),
                ),
                req(
                    "4.4 Aislamiento Multi-Tenant (RLS): Actor de Tenant Beta no ve técnicos de Alfa -> 404",
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

destino = pathlib.Path(__file__).with_name("scrum-108-aprobacion-rechazo.postman_collection.json")
destino.write_text(base.json.dumps(coleccion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Colección generada con éxito en: {destino}")
