"""Genera la colección del historial de servicios del técnico (SCRUM-102, historia SCRUM-37) contra QA.

Uso: python tests/e2e/generar-scrum37-historial.py
Escribe scrum-37-historial.postman_collection.json. Reutiliza los pasos de generar-scrum32-calificacion.py y, a través
de él, los de generar-scrum490-96-cotizacion-evidencia.py, generar-scrum117-pago.py y generar-scrum75-solicitud-empresa.py,
que también regeneran sus colecciones sin cambios.

Contrato: service-request.v1.yaml 1.10.0 (GET /v1/technicians/me/service-requests con score y ratedAt, RF-17, RN-SR13,
RN-SR15). Casos HIS-001 a HIS-015 del TD 7.5; HIS-016 es de pantalla. Datos propios: un técnico con cinco solicitudes en
el orden en que se le asignan (pagada y calificada, pagada sin calificar, completada, cancelada y asignada). HIS-013
necesita una categoría activa en el tenant Beta para registrar a su técnico; sin ella se omite. Necesita al
administrador del tenant (adminEmail y adminPassword, secretos de QA que nunca van al repositorio). Correr con
--reporters cli: el reporte JSON de Newman guarda tokens.
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


cal = cargar("calificacion", "generar-scrum32-calificacion.py")
base = cal.base

JSON, CORR, CANAL, BETA = base.JSON, base.CORR, base.CANAL, base.BETA
auth, req, estado, error = base.auth, base.req, base.estado, base.error

HISTORIA = "SCRUM-102"
HISTORIAL = "/v1/technicians/me/service-requests"
CAMPOS = ["assignedAt", "categoryId", "createdAt", "description", "id", "ratedAt", "score", "status"]
CON_BETA = ["if (!pm.collectionVariables.get('categoriaBetaId')) { pm.execution.skipRequest(); }"]


def historial(nombre, token, query="", pruebas=(), headers=(), previo=()):
    ruta = HISTORIAL + (("?" + query) if query else "")
    return req(nombre, "GET", ruta, [CORR, *headers] + ([auth(token)] if token else []), pruebas=pruebas, previo=previo)


def ids(*n):
    return "[" + ", ".join(f"pm.collectionVariables.get('solicitud{i}Id')" for i in n) + "]"


def solo(estado_filtro, *n):
    return estado(200) + [
        f"pm.test('solo las solicitudes en {estado_filtro}', () => {{",
        "  const p = pm.response.json();",
        f"  pm.expect(p.items.map(i => i.id)).to.eql({ids(*n)});",
        f"  pm.expect(p.totalItems).to.eql({len(n)});",
        f"  p.items.forEach(i => pm.expect(i.status).to.eql('{estado_filtro}'));",
        "});",
    ]


def pagina(numero, cantidad):
    return estado(200) + [
        f"pm.test('página {numero}: {cantidad} de 5', () => {{",
        "  const p = pm.response.json();",
        f"  pm.expect(p.page).to.eql({numero});",
        "  pm.expect(p.size).to.eql(2);",
        f"  pm.expect(p.items.length).to.eql({cantidad});",
        "  pm.expect(p.totalItems).to.eql(5);",
        "  const vistos = JSON.parse(pm.collectionVariables.get('vistos') || '[]');",
        "  p.items.forEach(i => pm.expect(vistos).to.not.include(i.id));",
        "  pm.collectionVariables.set('vistos', JSON.stringify(vistos.concat(p.items.map(i => i.id))));",
        "});",
    ]


def vacio(descripcion):
    return estado(200) + [
        f"pm.test('{descripcion}: 200 sin solicitudes', () => {{",
        "  const p = pm.response.json();",
        "  pm.expect(p.items).to.eql([]);",
        "  pm.expect(p.totalItems).to.eql(0);",
        "});",
    ]


preparacion = base.preparacion(HISTORIA)
preparacion["name"] = "0. Preparación: categoría propia, técnicos, clientes y técnico de Beta"
preparacion["item"] += [
    req("Categorías del tenant Beta", "GET", "/v1/catalog/categories", [CORR, BETA],
        pruebas=estado(200) + [
            "// Sin categorías en Beta no se puede registrar un técnico allá: HIS-013 se omite (ver README).",
            "const beta = pm.response.json();",
            "if (beta.length > 0) { pm.collectionVariables.set('categoriaBetaId', beta[0].id); }",
            "else { pm.collectionVariables.unset('categoriaBetaId'); console.log('Beta sin categorías: se omite HIS-013'); }",
        ]),
    req("Registro del técnico de Beta", "POST", "/v1/auth/register/technician", [JSON, CORR, BETA],
        {"email": "tecnico102.beta.{{sufijo}}@quickpatch.test", "password": "{{clave}}", "fullName": f"Técnico de Beta {HISTORIA}",
         "phone": "3007654331", "documentId": "{{docTecnicoBeta}}", "specialtyId": "{{categoriaBetaId}}", "role": "tecnico"},
        previo=[*CON_BETA, "pm.collectionVariables.set('docTecnicoBeta', String(Date.now() + 17).slice(-10));"],
        pruebas=estado(201)),
    req("Login del técnico de Beta", "POST", "/v1/auth/login", [JSON, CORR, BETA],
        {"email": "tecnico102.beta.{{sufijo}}@quickpatch.test", "password": "{{clave}}"}, previo=CON_BETA,
        pruebas=estado(200) + ["pm.collectionVariables.set('tecnicoBetaToken', pm.response.json().accessToken);"]),
]

datos = {
    "name": "1. Cinco solicitudes del técnico: pagada y calificada, pagada, completada, cancelada y asignada",
    "item": [
        historial("HIS-011: técnico sin historial", "tecnicoToken", pruebas=vacio("técnico nuevo")),
        *base.asignar(1, HISTORIA),
        *cal.cotizar_y_ejecutar(1),
        *cal.pagar(1),
        cal.calificar("El cliente califica la solicitud 1 con 4 estrellas", 1, "clienteToken", {"score": 4},
                      cal.calificada(1, 4, None)),
        *base.asignar(2, HISTORIA),
        *cal.cotizar_y_ejecutar(2),
        *cal.pagar(2),
        *base.asignar(3, HISTORIA),
        *cal.cotizar_y_ejecutar(3),
        *base.asignar(4, HISTORIA),
        cal.cancelar(4),
        *base.asignar(5, HISTORIA),
    ],
}

consultas = {
    "name": "2. Historial, filtros y paginación",
    "item": [
        historial("HIS-001 / HIS-009: historial completo, de la asignación más reciente a la más antigua", "tecnicoToken",
                  pruebas=estado(200) + [
                      "const p = pm.response.json();",
                      "pm.test('HIS-001: las cinco del técnico en orden, página 1 de tamaño 20', () => {",
                      f"  pm.expect(p.items.map(i => i.id)).to.eql({ids(5, 4, 3, 2, 1)});",
                      "  pm.expect(p.items.map(i => i.status)).to.eql(['asignado', 'cancelado', 'completado', 'pagado', 'pagado']);",
                      "  pm.expect(p.page).to.eql(1);",
                      "  pm.expect(p.size).to.eql(20);",
                      "  pm.expect(p.totalItems).to.eql(5);",
                      "  for (let k = 1; k < p.items.length; k++) {",
                      "    pm.expect(new Date(p.items[k - 1].assignedAt) >= new Date(p.items[k].assignedAt)).to.eql(true);",
                      "  }",
                      "});",
                      "pm.test('HIS-009: solo los campos del contrato, sin dirección, ubicación ni cliente', () => {",
                      "  p.items.forEach(i => {",
                      f"    Object.keys(i).forEach(k => pm.expect({json.dumps(CAMPOS)}).to.include(k));",
                      "    pm.expect(i.categoryId).to.eql(pm.collectionVariables.get('categoriaId'));",
                      "  });",
                      "  pm.expect(pm.response.text()).to.not.match(/addressText|latitude|longitude|clientId|Calle 63/);",
                      "});",
                      "pm.test('HIS-010: la calificada trae score y ratedAt; las demás, nulos o ausentes', () => {",
                      "  const s1 = p.items.find(i => i.id === pm.collectionVariables.get('solicitud1Id'));",
                      "  pm.expect(s1.score).to.eql(4);",
                      "  pm.expect(s1.ratedAt).to.be.a('string');",
                      "  p.items.filter(i => i.id !== s1.id).forEach(i => {",
                      "    pm.expect(i.score == null).to.eql(true);",
                      "    pm.expect(i.ratedAt == null).to.eql(true);",
                      "  });",
                      "});",
                  ]),
        historial("HIS-002: filtro completado", "tecnicoToken", "status=completado", pruebas=solo("completado", 3)),
        historial("HIS-003: filtro cancelado", "tecnicoToken", "status=cancelado", pruebas=solo("cancelado", 4)),
        historial("HIS-004: filtro pagado / SRQ-026", "tecnicoToken", "status=pagado", pruebas=solo("pagado", 2, 1)),
        historial("HIS-005: estado inexistente → 400", "tecnicoToken", "status=terminado", pruebas=error(400)),
        historial("HIS-006: página 1 de tamaño 2", "tecnicoToken", "page=1&size=2", pruebas=pagina(1, 2),
                  previo=["pm.collectionVariables.unset('vistos');"]),
        historial("HIS-006: página 2 de tamaño 2", "tecnicoToken", "page=2&size=2", pruebas=pagina(2, 2)),
        historial("HIS-006: página 3 de tamaño 2", "tecnicoToken", "page=3&size=2", pruebas=pagina(3, 1)),
        historial("HIS-007: página fuera de rango", "tecnicoToken", "page=4&size=2",
                  pruebas=estado(200) + [
                      "pm.test('sin elementos y con el total real', () => {",
                      "  pm.expect(pm.response.json().items).to.eql([]);",
                      "  pm.expect(pm.response.json().totalItems).to.eql(5);",
                      "});",
                  ]),
        historial("HIS-008: page=0 → 400", "tecnicoToken", "page=0", pruebas=error(400)),
        historial("HIS-008: size=0 → 400", "tecnicoToken", "size=0", pruebas=error(400)),
        historial("HIS-008: size=101 → 400", "tecnicoToken", "size=101", pruebas=error(400)),
    ],
}

fugas = {
    "name": "3. Otro técnico, otro tenant, roles sin acceso y sin sesión",
    "item": [
        historial("HIS-012: otro técnico del mismo tenant", "otroTecnicoToken", pruebas=vacio("otro técnico")),
        historial("HIS-013: técnico del tenant Beta", "tecnicoBetaToken", headers=[BETA], previo=CON_BETA,
                  pruebas=vacio("técnico de Beta")),
        historial("HIS-014: cliente → 403", "clienteToken", pruebas=error(403)),
        historial("HIS-014: admin_tenant → 403", "adminToken", pruebas=error(403)),
        historial("HIS-015: sin sesión → 401", None, pruebas=estado(401)),
    ],
}

coleccion = base.coleccion(
    "QUICKPATCH — SCRUM-102 Historial de servicios del técnico",
    "RF-17 (SCRUM-37) contra QA, con service-request.v1.yaml 1.10.0 (GET /v1/technicians/me/service-requests). Casos "
    "HIS-001 a HIS-015 del TD 7.5 con datos propios: el técnico ve sus cinco solicitudes de la asignación más reciente a "
    "la más antigua, sin datos del cliente y con la calificación recibida; filtros por completado, cancelado y pagado; "
    "páginas de tamaño 2 sin repetidos, página fuera de rango y límites (400); otro técnico y el técnico de Beta no ven "
    "nada; cliente y admin_tenant reciben 403 y sin sesión 401. Variables: baseUrl, adminEmail y adminPassword (secretos "
    "de QA, nunca en el repositorio). Correr con --reporters cli: el reporte JSON de Newman guarda tokens.",
    [preparacion, datos, consultas, fugas, base.limpieza],
)

destino = AQUI / "scrum-37-historial.postman_collection.json"
destino.write_text(json.dumps(coleccion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Colección escrita en {destino}")
