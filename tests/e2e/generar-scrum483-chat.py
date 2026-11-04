"""Genera la colección del chat de la solicitud (SCRUM-483, historia SCRUM-473) contra QA.

Uso: python tests/e2e/generar-scrum483-chat.py
Escribe scrum-483-chat.postman_collection.json. Reutiliza los pasos de generar-scrum490-96-cotizacion-evidencia.py
(preparación, oferta y asignación), que también regenera sus dos colecciones sin cambios.

Contrato: communication.v1.yaml 1.3.0 (GET y POST /v1/service-requests/{id}/messages, ADR-026). Communication arma los
participantes con service-request.status-changed: las primeras peticiones reintentan hasta que llega la réplica. La
entrega en tiempo real (trama chat.message) la cubre scrum-483-chat-tiempo-real.mjs, porque Newman no habla WebSocket.
Necesita al administrador del tenant (adminEmail y adminPassword, secretos de QA que nunca van al repositorio). Correr
con --reporters cli: el reporte JSON de Newman guarda los cuerpos y los tokens, y no debe subirse.
"""
import importlib.util
import json
import pathlib

AQUI = pathlib.Path(__file__).parent
_spec = importlib.util.spec_from_file_location("base", AQUI / "generar-scrum490-96-cotizacion-evidencia.py")
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)

JSON, CORR, auth, req, estado, error = base.JSON, base.CORR, base.auth, base.req, base.estado, base.error
reintentar = base.reintentar

CHAT = "/v1/service-requests/{{solicitud1Id}}/messages"
CAMPOS_MENSAJE = ["authorId", "authorRole", "id", "sentAt", "text"]
CAMPOS_PAGINA = ["items", "page", "size", "totalItems", "writable"]


def mensaje(rol, texto, autor, variable):
    return [
        "pm.test('201 con el contrato ChatMessage', () => {",
        "  pm.response.to.have.status(201);",
        "  const m = pm.response.json();",
        f"  pm.expect(Object.keys(m).sort()).to.eql({json.dumps(CAMPOS_MENSAJE)});",
        f"  pm.expect(m.authorRole).to.eql('{rol}');",
        f"  pm.expect(m.authorId).to.eql(pm.collectionVariables.get('{autor}'));",
        f"  pm.expect(m.text).to.eql({json.dumps(texto, ensure_ascii=False)});",
        "});",
        f"pm.collectionVariables.set('{variable}', pm.response.json().id);",
    ]


def enviar(nombre, token, texto, pruebas):
    return req(nombre, "POST", CHAT, [JSON, CORR, auth(token)], {"text": texto}, pruebas=pruebas)


def historial(nombre, token, escribible, pruebas=(), consulta=""):
    """Reintenta hasta que la réplica muestre `writable` = escribible: llega por Kafka y no es inmediata."""
    return req(nombre, "GET", CHAT + consulta, [CORR, auth(token)],
               pruebas=reintentar(
                   f"pm.response.code === 200 && pm.response.json().writable === {str(escribible).lower()}", [
                       "pm.test('200 con el contrato ChatMessagePage', () => {",
                       "  pm.response.to.have.status(200);",
                       f"  pm.expect(Object.keys(pm.response.json()).sort()).to.eql({json.dumps(CAMPOS_PAGINA)});",
                       "});",
                       f"pm.test('writable {str(escribible).lower()}', () => "
                       f"pm.expect(pm.response.json().writable).to.eql({str(escribible).lower()}));",
                       *pruebas,
                   ]))



coleccion = base.coleccion(
    "QUICKPATCH — SCRUM-483 Chat de la solicitud de punta a punta",
    "RF-37 (SCRUM-473, ADR-026) contra QA, con communication.v1.yaml 1.3.0. Con la solicitud asignada, el cliente y el "
    "técnico intercambian mensajes y los dos ven el mismo historial, del más reciente al más antiguo y paginado. Casos "
    "negativos: texto vacío o de 1.001 caracteres y campos de más (400), tamaño de página fuera de rango (400), sin "
    "token (401), administrador del tenant (403), otro cliente y otro técnico del mismo tenant (404) y cliente de otro "
    "tenant (404 por RLS). Al cancelar, el chat queda de solo lectura: el historial se lee y escribir da 409 "
    "chat-cerrado (RN-CH2). La trama chat.message en tiempo real la prueba scrum-483-chat-tiempo-real.mjs. Variables: "
    "baseUrl, adminEmail y adminPassword (secretos de QA, nunca en el repositorio). Correr con --reporters cli: el "
    "reporte JSON de Newman guarda tokens.",
    [
        base.preparacion("SCRUM-483"),
        {
            "name": "1. Solicitud asignada: el chat se abre",
            "item": [
                *base.asignar(1, "SCRUM-483"),
                req("Id del cliente (para comprobar el autor)", "GET", "/v1/users/me", [CORR, auth("clienteToken")],
                    pruebas=estado(200) + ["pm.collectionVariables.set('clienteId', pm.response.json().id);"]),
                historial("El cliente abre el chat vacío (espera la réplica de participantes)", "clienteToken", True, [
                    "pm.test('sin mensajes', () => {",
                    "  pm.expect(pm.response.json().items).to.eql([]);",
                    "  pm.expect(pm.response.json().totalItems).to.eql(0);",
                    "});",
                ]),
            ],
        },
        {
            "name": "2. Cliente y técnico conversan",
            "item": [
                enviar("El cliente escribe (con espacios en los extremos)", "clienteToken", "  Hola, ¿a qué hora llega?  ",
                       mensaje("cliente", "Hola, ¿a qué hora llega?", "clienteId", "mensaje1Id")),
                enviar("El técnico responde", "tecnicoToken", "Llego en 20 minutos.",
                       mensaje("tecnico", "Llego en 20 minutos.", "tecnicoId", "mensaje2Id")),
                historial("El técnico ve los dos mensajes, el más reciente primero", "tecnicoToken", True, [
                    "pm.test('dos mensajes en orden', () => {",
                    "  const p = pm.response.json();",
                    "  pm.expect(p.totalItems).to.eql(2);",
                    "  pm.expect(p.items.map(m => m.id)).to.eql([",
                    "    pm.collectionVariables.get('mensaje2Id'), pm.collectionVariables.get('mensaje1Id')]);",
                    "});",
                ]),
                historial("Página 2 de tamaño 1: el primer mensaje", "clienteToken", True, [
                    "pm.test('page 2, size 1, el mensaje del cliente', () => {",
                    "  const p = pm.response.json();",
                    "  pm.expect([p.page, p.size, p.totalItems]).to.eql([2, 1, 2]);",
                    "  pm.expect(p.items).to.have.lengthOf(1);",
                    "  pm.expect(p.items[0].id).to.eql(pm.collectionVariables.get('mensaje1Id'));",
                    "});",
                ], consulta="?page=2&size=1"),
            ],
        },
        {
            "name": "3. Validación y acceso",
            "item": [
                enviar("Texto con solo espacios → 400 en text", "clienteToken", "   ", error(400, "validacion") + [
                    "pm.test('error en text', () => pm.expect(pm.response.json().errors).to.have.property('text'));",
                ]),
                enviar("Texto de 1.001 caracteres → 400 en text", "clienteToken", "a" * 1001, error(400, "validacion") + [
                    "pm.test('error en text', () => pm.expect(pm.response.json().errors).to.have.property('text'));",
                ]),
                req("Campos de más (authorId) → 400", "POST", CHAT, [JSON, CORR, auth("clienteToken")],
                    {"text": "hola", "authorId": "{{tecnicoId}}"}, pruebas=error(400, "validacion")),
                req("Tamaño de página 500 → 400", "GET", CHAT + "?size=500", [CORR, auth("clienteToken")],
                    pruebas=error(400, "validacion")),
                req("Sin token → 401", "GET", CHAT, [CORR], pruebas=estado(401)),
                req("El administrador del tenant no usa el chat → 403", "GET", CHAT, [CORR, auth("adminToken")],
                    pruebas=error(403)),
                req("Otro cliente del mismo tenant no lo ve → 404", "GET", CHAT, [CORR, auth("otroClienteToken")],
                    pruebas=error(404, "no-encontrado")),
                enviar("Otro técnico no escribe → 404", "otroTecnicoToken", "Hola", error(404, "no-encontrado")),
                req("El cliente de otro tenant no lo ve → 404 (RLS)", "GET", CHAT, [CORR, auth("betaToken")],
                    pruebas=error(404, "no-encontrado")),
            ],
        },
        {
            "name": "4. Al cancelar queda de solo lectura (RN-CH2)",
            "item": [
                req("El cliente cancela la solicitud", "POST", "/v1/service-requests/{{solicitud1Id}}/cancel",
                    [JSON, CORR, auth("clienteToken")], {"reason": "Fin de la prueba SCRUM-483."}, pruebas=estado(200)),
                historial("El historial sigue disponible, sin escritura (espera la réplica)", "clienteToken", False, [
                    "pm.test('los dos mensajes', () => pm.expect(pm.response.json().totalItems).to.eql(2));",
                ]),
                enviar("Escribir con la solicitud cancelada → 409 chat-cerrado", "clienteToken", "¿Sigue en pie?",
                       error(409, "chat-cerrado")),
                enviar("El técnico tampoco escribe → 409 chat-cerrado", "tecnicoToken", "Entendido.",
                       error(409, "chat-cerrado")),
            ],
        },
        base.limpieza,
    ],
)

destino = AQUI / "scrum-483-chat.postman_collection.json"
destino.write_text(json.dumps(coleccion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Colección escrita en {destino}")
