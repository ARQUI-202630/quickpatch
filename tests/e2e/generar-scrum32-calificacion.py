"""Genera la colección de la calificación del servicio (SCRUM-87, historia SCRUM-32) contra QA.

Uso: python tests/e2e/generar-scrum32-calificacion.py
Escribe scrum-32-calificacion.postman_collection.json. Reutiliza los pasos de generar-scrum490-96-cotizacion-evidencia.py,
generar-scrum117-pago.py y generar-scrum75-solicitud-empresa.py, que también regeneran sus colecciones sin cambios.

Contrato: service-request.v1.yaml 1.10.0 (POST /v1/service-requests/{id}/rating, RF-12, RN-R1 a RN-R3). Casos CAL-001 a
CAL-018 y CAL-021 del TD 7.8; CAL-019 y CAL-020 (el evento service-request.rated y la reputación sin doble conteo) se
prueban en las de integración de ServiceRequest y Ranking, y CAL-022 y CAL-023 son de pantalla. Datos propios: un técnico
con tres solicitudes de hogar (una calificada con comentario, otra sin comentario, una cancelada) y una de empresa con
dos usuarios. Necesita al administrador del tenant (adminEmail y adminPassword, secretos de QA que nunca van al
repositorio). Correr con --reporters cli: el reporte JSON de Newman guarda tokens.
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
pago = cargar("pago", "generar-scrum117-pago.py")
empresa = cargar("empresa", "generar-scrum75-solicitud-empresa.py")

JSON, CORR, CANAL, BETA = base.JSON, base.CORR, base.CANAL, base.BETA
auth, req, estado, error, reintentar = base.auth, base.req, base.estado, base.error, base.reintentar

HISTORIA = "SCRUM-87"
COMENTARIO_500 = ("Muy buen trabajo, puntual y ordenado. " * 14)[:500]


def solicitud(n):
    return "/v1/service-requests/{{solicitud" + str(n) + "Id}}"


def calificar(nombre, n, token, cuerpo, pruebas):
    return req(nombre, "POST", solicitud(n) + "/rating", [JSON, CORR] + ([auth(token)] if token else []), cuerpo,
               pruebas=pruebas)


def con_errores(campo):
    return error(400) + [f"pm.test('error en {campo}', () => pm.expect(pm.response.json().errors).to.have.property('{campo}'));"]


def calificada(n, score, comentario):
    return [
        "pm.test('201 con el contrato RatingResponse', () => {",
        "  pm.response.to.have.status(201);",
        "  const r = pm.response.json();",
        f"  pm.expect(r.serviceRequestId).to.eql(pm.collectionVariables.get('solicitud{n}Id'));",
        f"  pm.expect(r.score).to.eql({score});",
        f"  pm.expect(r.comment).to.eql({json.dumps(comentario, ensure_ascii=False)});",
        "  pm.expect(new Date(r.ratedAt).getTime()).to.be.above(0);",
        "});",
    ]


def cotizar_y_ejecutar(n, cliente="clienteToken", completar=True):
    """Desde asignado: cotización de 185.000 aceptada por `cliente`, inicio, foto y (si `completar`) completado."""
    pasos = [
        base.emitir(n, f"El técnico cotiza la solicitud {n}", "150000.00", "35000.00", 1, f"cot{n}"),
        base.responder(n, f"cot{n}", "accept", f"Se acepta la cotización de la solicitud {n}", token=cliente,
                       pruebas=base.decision("aceptada", "cotizacion_aceptada", 2)),
        req(f"El técnico inicia la solicitud {n}", "POST", solicitud(n) + "/start", [CORR, auth("tecnicoToken")],
            pruebas=estado(200)),
        req(f"El técnico sube la foto de la solicitud {n}", "POST", solicitud(n) + "/evidence", [CORR, auth("tecnicoToken")],
            archivo=base.FOTO, pruebas=estado(201)),
    ]
    if completar:
        pasos.append(completar_paso(n))
    return pasos


def completar_paso(n):
    return req(f"El técnico completa la solicitud {n}", "POST", solicitud(n) + "/complete", [CORR, auth("tecnicoToken")],
               pruebas=estado(200))


def pagar(n, cliente="clienteToken"):
    """Espera el pago pendiente que crea Payments, lo paga con la tarjeta aprobada y espera a que la solicitud quede pagada."""
    ruta = solicitud(n) + "/payment"
    return [
        req(f"El pago de la solicitud {n} queda pendiente (espera service-request.completed en Payments)", "GET", ruta,
            [CORR, auth(cliente)],
            pruebas=reintentar("pm.response.code === 200",
                               estado(200) + ["pm.test('pendiente', () => pm.expect(pm.response.json().status).to.eql('pendiente'));"],
                               maximo=20)),
        req(f"Se paga la solicitud {n} con la tarjeta aprobada", "POST", ruta, [JSON, CORR, auth(cliente)],
            {"paymentToken": "tok_sim_aprobada_{{sufijo}}", "billing": pago.FACTURACION},
            pruebas=estado(200) + ["pm.test('aprobado', () => pm.expect(pm.response.json().status).to.eql('aprobado'));"]),
        req(f"La solicitud {n} queda pagada (payment.approved)", "GET", solicitud(n), [CORR, auth(cliente)],
            pruebas=reintentar("pm.response.json().status === 'pagado'",
                               ["pm.test('pagado', () => pm.expect(pm.response.json().status).to.eql('pagado'));"])),
    ]


def cancelar(n, cliente="clienteToken"):
    return req(f"El cliente cancela la solicitud {n}", "POST", solicitud(n) + "/cancel", [JSON, CORR, auth(cliente)],
               {"reason": "Ya no necesito el servicio."},
               pruebas=estado(200) + ["pm.test('cancelado', () => pm.expect(pm.response.json().status).to.eql('cancelado'));"])


def asignar_empresa(n, token):
    """Como base.asignar, pero la solicitud la crea un empresa_contacto."""
    s, o = f"solicitud{n}Id", f"oferta{n}Id"
    return [
        req(f"La empresa crea la solicitud {n} (espera la réplica de la categoría)", "POST", "/v1/service-requests",
            [JSON, CORR, auth(token)],
            {"categoryId": "{{categoriaId}}", "description": f"Prueba de calificación {HISTORIA}, solicitud {n}",
             "location": {"latitude": 4.6486, "longitude": -74.063}, "addressText": "Carrera 7 # 71-21, piso 8",
             "siteName": "Sede Chapinero"},
            pruebas=reintentar("pm.response.code !== 422", estado(201) + [
                "pm.test('de empresa', () => pm.expect(pm.response.json().clientType).to.eql('empresa'));",
                f"pm.collectionVariables.set('{s}', pm.response.json().id);",
            ], maximo=10)),
        req(f"El técnico ve la oferta de la solicitud {n}", "GET", "/v1/matching/offers?status=pendiente",
            [CORR, auth("tecnicoToken")],
            pruebas=[
                f"const oferta = pm.response.code === 200 && pm.response.json().items.find(x => x.serviceRequestId === pm.collectionVariables.get('{s}'));",
                *reintentar("oferta", [
                    "pm.test('la oferta está pendiente para el técnico', () => pm.expect(oferta).to.be.ok);",
                    f"if (oferta) {{ pm.collectionVariables.set('{o}', oferta.attemptId); }}",
                ]),
            ]),
        req(f"El técnico acepta la oferta de la solicitud {n}", "POST", "/v1/matching/offers/{{" + o + "}}/accept",
            [CORR, auth("tecnicoToken")], pruebas=estado(200)),
        req(f"La solicitud {n} queda asignada", "GET", solicitud(n), [CORR, auth(token)],
            pruebas=reintentar("pm.response.json().status === 'asignado'",
                               ["pm.test('asignado', () => pm.expect(pm.response.json().status).to.eql('asignado'));"])),
    ]


def en_historial(n, pruebas):
    """La fila de la solicitud n en el historial del técnico (RF-17), en la variable `fila`."""
    return req(f"La solicitud {n} en el historial del técnico", "GET", "/v1/technicians/me/service-requests?size=100",
               [CORR, auth("tecnicoToken")],
               pruebas=estado(200) + [
                   f"const fila = pm.response.json().items.find(i => i.id === pm.collectionVariables.get('solicitud{n}Id'));",
                   "pm.test('la solicitud está en el historial', () => pm.expect(fila).to.be.ok);",
                   *pruebas,
               ])


if __name__ == "__main__":
    estados = {
        "name": "1. Solicitud 1: no se califica antes de pagar (RN-R3)",
        "item": [
            *base.asignar(1, HISTORIA),
            calificar("CAL-011: en asignado → 409", 1, "clienteToken", {"score": 5},
                      error(409, "transicion-invalida")),
            *cotizar_y_ejecutar(1, completar=False),
            calificar("CAL-011: en en_progreso → 409", 1, "clienteToken", {"score": 5},
                      error(409, "transicion-invalida")),
            completar_paso(1),
            calificar("CAL-010: completado sin pagar → 409", 1, "clienteToken", {"score": 5},
                      error(409, "transicion-invalida")),
            *pagar(1),
        ],
    }

    validaciones = {
        "name": "2. Solicitud 1 pagada: validaciones y quién califica",
        "item": [
            calificar("CAL-004: score 0 → 400", 1, "clienteToken", {"score": 0}, con_errores("score")),
            calificar("CAL-005: score 6 → 400", 1, "clienteToken", {"score": 6}, con_errores("score")),
            calificar("CAL-006: score 4.5 → 400", 1, "clienteToken", {"score": 4.5}, error(400)),
            calificar("CAL-006: score \"5\" → 400", 1, "clienteToken", {"score": "5"}, error(400)),
            calificar("CAL-007: sin score → 400", 1, "clienteToken", {"comment": "Sin puntaje."}, con_errores("score")),
            calificar("CAL-008: comentario de 501 caracteres → 400", 1, "clienteToken",
                      {"score": 5, "comment": COMENTARIO_500 + "!"}, con_errores("comment")),
            calificar("CAL-009: technicianId en el cuerpo → 400", 1, "clienteToken",
                      {"score": 5, "technicianId": "{{tecnicoId}}"}, error(400)),
            calificar("CAL-013: otro cliente del mismo tenant → 403", 1, "otroClienteToken", {"score": 1}, error(403)),
            req("CAL-014: cliente del tenant Beta → 404 (RLS)", "POST", solicitud(1) + "/rating",
                [JSON, CORR, BETA, auth("betaToken")], {"score": 1}, pruebas=error(404)),
            calificar("CAL-015: el técnico → 403", 1, "tecnicoToken", {"score": 5}, error(403)),
            calificar("CAL-015: admin_tenant → 403", 1, "adminToken", {"score": 5}, error(403)),
            calificar("CAL-016: sin sesión → 401", 1, None, {"score": 5}, estado(401)),
            req("CAL-017: solicitud inexistente → 404", "POST",
                "/v1/service-requests/00000000-0000-4000-8000-000000000000/rating",
                [JSON, CORR, auth("clienteToken")], {"score": 5}, pruebas=error(404)),
            en_historial(1, [
                "pm.test('ningún intento rechazado dejó calificación', () => pm.expect(fila.score == null).to.eql(true));",
            ]),
            calificar("CAL-001 / CAL-003 / CAL-008: 5 estrellas con comentario de 500 caracteres → 201", 1, "clienteToken",
                      {"score": 5, "comment": COMENTARIO_500}, calificada(1, 5, COMENTARIO_500)),
            base.detalle(1, "pagado", "CAL-001: la solicitud sigue en pagado"),
            calificar("CAL-012: calificar otra vez → 409 ya-calificada", 1, "clienteToken", {"score": 1},
                      error(409, "ya-calificada")),
            en_historial(1, [
                "pm.test('CAL-012 / CAL-021: el historial del técnico conserva las 5 estrellas', () => {",
                "  pm.expect(fila.score).to.eql(5);",
                "  pm.expect(fila.ratedAt).to.be.a('string');",
                "});",
            ]),
        ],
    }

    sin_comentario = {
        "name": "3. Solicitud 2: 1 estrella sin comentario; solicitud 3 cancelada",
        "item": [
            *base.asignar(2, HISTORIA),
            *cotizar_y_ejecutar(2),
            *pagar(2),
            calificar("CAL-002 / CAL-003: 1 estrella sin comentario → 201", 2, "clienteToken", {"score": 1},
                      calificada(2, 1, None)),
            *base.asignar(3, HISTORIA),
            cancelar(3),
            calificar("CAL-011: cancelada → 409", 3, "clienteToken", {"score": 5}, error(409, "transicion-invalida")),
        ],
    }

    de_empresa = {
        "name": "4. Solicitud 4 de empresa: solo califica quien la creó (CAL-018)",
        "item": [
            empresa.registrar_empresa("Empresa", "empresa87.qa", "nitEmpresa", "empresaId"),
            empresa.login_empresa("quien crea la solicitud", "empresa87.qa.{{sufijo}}@quickpatch.test", "empresaToken",
                                  "empresaId"),
            req("La empresa agrega a un colega", "POST", "/v1/companies/me/users", [JSON, CORR, auth("empresaToken")],
                {"email": "colega87.qa.{{sufijo}}@quickpatch.test", "fullName": "Colega de la empresa"},
                pruebas=estado(201) + ["pm.collectionVariables.set('invitacionColega', pm.response.json().invitation.token);"]),
            req("El colega define su contraseña", "POST", "/v1/auth/password/setup", [JSON, CORR, CANAL],
                {"token": "{{invitacionColega}}", "password": "{{clave}}"}, pruebas=estado(204)),
            empresa.login_empresa("el colega", "colega87.qa.{{sufijo}}@quickpatch.test", "colegaToken", "empresaId"),
            *asignar_empresa(4, "empresaToken"),
            *cotizar_y_ejecutar(4, cliente="empresaToken"),
            *pagar(4, cliente="empresaToken"),
            calificar("CAL-018: el colega de la empresa → 403", 4, "colegaToken", {"score": 4}, error(403)),
            calificar("CAL-018: quien creó la solicitud → 201", 4, "empresaToken",
                      {"score": 4, "comment": "Atendieron la sede a tiempo."}, calificada(4, 4, "Atendieron la sede a tiempo.")),
        ],
    }

    coleccion = base.coleccion(
        "QUICKPATCH — SCRUM-87 Calificación del servicio",
        "RF-12 (SCRUM-32) contra QA, con service-request.v1.yaml 1.10.0 (POST /v1/service-requests/{id}/rating). Casos "
        "CAL-001 a CAL-018 y CAL-021 del TD 7.8 con datos propios: no se califica en asignado, en_progreso, completado sin "
        "pagar ni cancelado (409); validaciones del puntaje y del comentario (400); otro cliente, el técnico y el "
        "admin_tenant reciben 403, el cliente de Beta y una solicitud inexistente 404 y sin sesión 401; la calificación "
        "válida, con y sin comentario, no cambia el estado, no se repite (409 ya-calificada) y aparece en el historial del "
        "técnico; en una solicitud de empresa solo califica quien la creó. Variables: baseUrl, adminEmail y adminPassword "
        "(secretos de QA, nunca en el repositorio). Correr con --reporters cli: el reporte JSON de Newman guarda tokens.",
        [base.preparacion(HISTORIA), estados, validaciones, sin_comentario, de_empresa, base.limpieza],
    )

    destino = AQUI / "scrum-32-calificacion.postman_collection.json"
    destino.write_text(json.dumps(coleccion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Colección escrita en {destino}")
