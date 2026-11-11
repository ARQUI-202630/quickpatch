"""Genera la colección de AC9-E2 (SCRUM-642): un técnico con calificaciones bajas queda señalado en el panel, sin suspensión.

Uso: python tests/e2e/generar-scrum642-reputacion-baja.py
Escribe scrum-642-reputacion-baja.postman_collection.json. Reutiliza los pasos de generar-scrum32-calificacion.py (y, a
través de él, los de cotización, evidencia y pago), que también regeneran sus colecciones sin cambios.

Contratos: identity.v1.yaml 1.12.0 (GET /v1/admin/technicians con averageRating, ratingCount, lowReputation y el filtro
lowReputation) y service-request.v1.yaml (POST /v1/service-requests/{id}/rating). Condición del SAD 3.9: promedio menor a
3,0 con al menos 5 servicios calificados. El técnico de la corrida recibe cinco calificaciones de 2 estrellas; la
reputación viaja por service-request.rated → Ranking → ranking.technician-reputation-changed → Identity (ADR-027).

A diferencia de las otras colecciones, la limpieza NO suspende al técnico: lo que se verifica es justamente que nadie lo
suspende. Solo se desactiva la categoría de la corrida, así ninguna solicitud nueva le llega.
Necesita adminEmail y adminPassword (secretos de QA que nunca van al repositorio). Correr con --reporters cli.
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


cal = cargar("cal", "generar-scrum32-calificacion.py")
base = cal.base
CORR = base.CORR
auth, req, estado, reintentar = base.auth, base.req, base.estado, base.reintentar

HISTORIA = "SCRUM-642"
SERVICIOS = 5
PUNTAJE = 2


def servicio(n):
    return {
        "name": f"{n}. Servicio {n}: se paga y se califica con {PUNTAJE} estrellas",
        "item": [
            *base.asignar(n, HISTORIA),
            *cal.cotizar_y_ejecutar(n),
            *cal.pagar(n),
            cal.calificar(f"El cliente califica la solicitud {n} con {PUNTAJE} estrellas", n, "clienteToken",
                          {"score": PUNTAJE, "comment": "Prueba de reputación baja (AC9-E2)."},
                          cal.calificada(n, PUNTAJE, "Prueba de reputación baja (AC9-E2).")),
        ],
    }


def fila_del_tecnico(nombre, ruta, condicion, pruebas, maximo=30):
    return req(nombre, "GET", ruta, [CORR, auth("adminToken")],
               pruebas=estado(200) + [
                   "const fila = pm.response.json().items.find(t => t.userId === pm.collectionVariables.get('tecnicoId'));",
                   *reintentar(condicion, pruebas, maximo=maximo),
               ])


verificacion = {
    "name": f"{SERVICIOS + 1}. AC9-E2: el panel señala al técnico y nadie lo suspende",
    "item": [
        fila_del_tecnico(
            "Con la quinta calificación queda señalado (espera la reputación de Ranking)",
            "/v1/admin/technicians?size=100&verificationStatus=aprobado",
            f"fila && fila.ratingCount === {SERVICIOS}",
            [
                "pm.test('la reputación llegó a Identity: 5 calificaciones con promedio 2,0', () => {",
                "  pm.expect(fila).to.be.ok;",
                f"  pm.expect(fila.ratingCount).to.eql({SERVICIOS});",
                f"  pm.expect(Number(fila.averageRating)).to.eql({PUNTAJE});",
                "});",
                "pm.test('queda marcado con reputación baja', () => pm.expect(fila.lowReputation).to.eql(true));",
                "pm.test('sigue aprobado: no hay suspensión automática', () => pm.expect(fila.verificationStatus).to.eql('aprobado'));",
            ]),
        fila_del_tecnico(
            "El filtro del panel (lowReputation=true) lo incluye",
            "/v1/admin/technicians?size=100&lowReputation=true",
            "fila",
            [
                "pm.test('está entre los señalados', () => pm.expect(fila).to.be.ok);",
                "pm.test('todos los señalados cumplen la condición (promedio < 3 con al menos 5)', () => {",
                "  for (const t of pm.response.json().items) {",
                "    pm.expect(t.lowReputation).to.eql(true);",
                "    pm.expect(t.ratingCount).to.be.at.least(5);",
                "    pm.expect(Number(t.averageRating)).to.be.below(3);",
                "  }",
                "});",
            ], maximo=5),
    ],
}

limpieza = {
    "name": f"{SERVICIOS + 2}. Limpieza: se desactiva la categoría (el técnico no se suspende)",
    "item": [i for i in base.limpieza["item"] if "categor" in i["name"].lower()],
}
assert limpieza["item"], "la limpieza base ya no tiene el paso de la categoría"

if __name__ == "__main__":
    coleccion = base.coleccion(
        "QUICKPATCH — SCRUM-642 Técnico con calificaciones bajas (AC9-E2)",
        "AC9-E2 (SAD 3.9) contra QA: un técnico con cinco servicios pagados y calificados con 2 estrellas aparece en el "
        "listado del admin_tenant con averageRating 2, ratingCount 5 y lowReputation true, el filtro lowReputation=true lo "
        "incluye y sigue aprobado (sin suspensión automática). Contrato identity.v1.yaml 1.12.0. Variables: baseUrl, "
        "adminEmail y adminPassword (secretos de QA, nunca en el repositorio). Correr con --reporters cli.",
        [base.preparacion(HISTORIA), *[servicio(n) for n in range(1, SERVICIOS + 1)], verificacion, limpieza],
    )
    destino = AQUI / "scrum-642-reputacion-baja.postman_collection.json"
    destino.write_text(json.dumps(coleccion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Colección escrita en {destino}")
