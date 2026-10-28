"""Genera la colección de la restricción geográfica a Bogotá (SCRUM-600, historia SCRUM-598) contra QA.

Uso: python tests/e2e/generar-scrum600-fuera-de-bogota.py
Escribe scrum-600-fuera-de-bogota.postman_collection.json. Reutiliza los ayudantes de
generar-scrum490-96-cotizacion-evidencia.py, que también regenera sus dos colecciones sin cambios.

Contratos: service-request.v1.yaml 1.8.0 (location-preview y creación con solo la dirección) y RN-SR9 del DD. No necesita
al administrador: el cliente se registra solo y usa una categoría que ya existe en QA. Cada corrida usa un cliente nuevo
con clave aleatoria, y las solicitudes que llegan a crearse (carpeta 4) se cancelan al final de cada caso.

Qué prueba: una dirección o un punto de GPS fuera de Bogotá. Las carpetas 1 a 3 son lo que la regla cumple hoy (422 sin
crear nada). La 4 deja por escrito tres límites que la prueba encontró en QA y que la regla no cubre; se afirman tal como
responde QA hoy, para que el CI de los release no falle por un defecto ya conocido y, el día que se corrija, la corrida
avise y la colección se actualice junto con la corrección. Cada solicitud que llega a crearse se cancela en el paso siguiente.
"""
import importlib.util
import json
import pathlib

AQUI = pathlib.Path(__file__).parent
_spec = importlib.util.spec_from_file_location("base", AQUI / "generar-scrum490-96-cotizacion-evidencia.py")
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)

JSON, CORR, CANAL, auth, estado, error = base.JSON, base.CORR, base.CANAL, base.auth, base.estado, base.error

PREVIEW = "/v1/service-requests/location-preview"
SOLICITUDES = "/v1/service-requests"


def req(nombre, metodo, ruta, headers, cuerpo=None, pruebas=(), previo=()):
    """Como base.req, pero sin la omisión por falta del administrador: esta colección no lo usa."""
    item = {"name": nombre, "request": {"method": metodo, "header": list(headers), "url": base.url(ruta)}, "event": []}
    if cuerpo is not None:
        item["request"]["body"] = {"mode": "raw", "raw": json.dumps(cuerpo, ensure_ascii=False, indent=2)}
    if previo:
        item["event"].append({"listen": "prerequest", "script": {"type": "text/javascript", "exec": list(previo)}})
    if pruebas:
        item["event"].append({"listen": "test", "script": {"type": "text/javascript", "exec": list(pruebas)}})
    return item


def registro_cliente():
    return req("Registro del cliente", "POST", "/v1/auth/register/client", [JSON, CORR, CANAL],
               {"email": "cliente.qa.{{sufijo}}@quickpatch.test", "password": "{{clave}}", "fullName": "Prueba QA cliente"},
               previo=base.preparar, pruebas=estado(201))


def login_cliente():
    return req("Login del cliente", "POST", "/v1/auth/login", [JSON, CORR, CANAL],
               {"email": "cliente.qa.{{sufijo}}@quickpatch.test", "password": "{{clave}}"},
               pruebas=[
                   "pm.test('200 con rol cliente', () => {",
                   "  pm.response.to.have.status(200);",
                   "  pm.expect(pm.response.json().user.role).to.eql('cliente');",
                   "});",
                   "pm.collectionVariables.set('clienteToken', pm.response.json().accessToken);",
               ])


def fuera_de_cobertura(detalle):
    return error(422, "ubicacion-fuera-de-cobertura") + [
        f"pm.test('detalle: {detalle}', () => pm.expect(pm.response.json().detail).to.include('{detalle}'));",
    ]


def ubicacion_en_bogota(localidad=None):
    pruebas = [
        "pm.test('200 con punto dentro del área de cobertura de Bogotá', () => {",
        "  pm.response.to.have.status(200);",
        "  const r = pm.response.json();",
        "  pm.expect(r.location.latitude).to.be.within(4.45, 4.85);",
        "  pm.expect(r.location.longitude).to.be.within(-74.25, -73.98);",
        "  pm.expect(r.matchedAddress).to.include('Bogotá');",
    ]
    if localidad:
        pruebas.append(f"  pm.expect(r.locality.name).to.eql('{localidad}');")
    return pruebas + ["});"]


def vista_previa(nombre, direccion, pruebas):
    return req(nombre, "POST", PREVIEW, [JSON, CORR, auth("clienteToken")], {"addressText": direccion}, pruebas=pruebas)


def crear(nombre, cuerpo, pruebas):
    cuerpo = {"categoryId": "{{categoriaId}}", "description": "Prueba de cobertura SCRUM-600", **cuerpo}
    return req(nombre, "POST", SOLICITUDES, [JSON, CORR, auth("clienteToken")], cuerpo, pruebas=pruebas)


def con_gps(nombre, direccion, latitud, longitud):
    return crear(f"GPS en {nombre} → 422", {"addressText": direccion, "location": {"latitude": latitud, "longitude": longitud}},
                 fuera_de_cobertura("solo en Bogotá"))


# Direcciones escritas como las escribiría un cliente. Las rechaza el geocodificador (solo tiene el mapa de Bogotá).
CALI = "Calle 5 # 38-70, Cali, Valle del Cauca"
SOACHA = "Carrera 7 # 12-30, Soacha, Cundinamarca"
CHIA = "Calle 12 # 8-30, Chía, Cundinamarca"
VILLAVICENCIO = "Carrera 3 # 14-20, Villavicencio, Meta"
MEDELLIN_POBLADO = "Calle 10 Sur # 43A-30, El Poblado, Medellín, Antioquia"
CALI_SIN_COINCIDENCIA = "Avenida 6N # 25-60, Cali"

# Límite 1: la calle existe en Bogotá y el geocodificador ignora la ciudad y la numeración que le siguen.
LIMITE_CIUDAD = [
    ("Medellín", "Carrera 70 # 44-50, Laureles, Medellín", "Suba"),
    ("Bucaramanga", "Carrera 15 # 85-20, Bucaramanga", "Usaquén"),
    ("Tunja", "Plaza de Bolívar, Tunja", "La Candelaria"),
]

preparacion = {
    "name": "0. Preparación: un cliente nuevo y una categoría de QA",
    "item": [
        registro_cliente(),
        login_cliente(),
        req("El cliente toma la primera categoría del catálogo", "GET", "/v1/catalog/categories", [CORR, auth("clienteToken")],
            pruebas=estado(200) + [
                "pm.test('hay categorías', () => pm.expect(pm.response.json()).to.be.an('array').that.is.not.empty);",
                "pm.collectionVariables.set('categoriaId', pm.response.json()[0].id);",
            ]),
    ],
}

direccion_escrita = {
    "name": "1. Dirección escrita fuera de Bogotá: la vista previa la rechaza",
    "item": [
        vista_previa("Control: una dirección de Bogotá sí se ubica", "Calle 72 # 10-07, Bogotá", ubicacion_en_bogota("Chapinero")),
        vista_previa("Cali → 422 fuera de cobertura", CALI, fuera_de_cobertura("fuera de Bogotá")),
        vista_previa("Soacha, vecina de Bogotá → 422 fuera de cobertura", SOACHA, fuera_de_cobertura("fuera de Bogotá")),
        vista_previa("Chía, vecina de Bogotá → 422 fuera de cobertura", CHIA, fuera_de_cobertura("fuera de Bogotá")),
        vista_previa("Villavicencio → 422 fuera de cobertura", VILLAVICENCIO, fuera_de_cobertura("fuera de Bogotá")),
        vista_previa("El Poblado, Medellín → 422 fuera de cobertura", MEDELLIN_POBLADO, fuera_de_cobertura("fuera de Bogotá")),
        vista_previa("Cali sin ninguna coincidencia → 422 dirección no encontrada", CALI_SIN_COINCIDENCIA,
                     error(422, "direccion-no-encontrada")),
    ],
}

crear_con_direccion = {
    "name": "2. Crear la solicitud solo con la dirección: sin coincidencia no se crea",
    "item": [
        crear("Cali sin coincidencia, solo con la dirección → 422 dirección no encontrada",
              {"addressText": CALI_SIN_COINCIDENCIA}, error(422, "direccion-no-encontrada")),
    ],
}

gps = {
    "name": "3. GPS fuera de Bogotá: RN-SR9 rechaza el punto",
    "item": [
        con_gps("Medellín", "Centro, Medellín", 6.2442, -75.5812),
        con_gps("Cali", "Centro, Cali", 3.4516, -76.5320),
        con_gps("Tunja", "Centro, Tunja", 5.5353, -73.3678),
        con_gps("Chía, al norte del área de cobertura", "Centro, Chía", 4.8587, -74.0586),
    ],
}

def creada_en_rectangulo(origen):
    return estado(201) + [
        f"pm.test('creada en buscando_tecnico con un punto dentro del rectángulo de cobertura ({origen})', () => {{",
        "  const s = pm.response.json();",
        "  pm.expect(s.status).to.eql('buscando_tecnico');",
        "  pm.expect(s.location.latitude).to.be.within(4.45, 4.85);",
        "  pm.expect(s.location.longitude).to.be.within(-74.25, -73.98);",
        "});",
    ]


def crear_y_cancelar(nombre, variable, cuerpo, origen):
    return [
        crear(nombre, cuerpo, creada_en_rectangulo(origen) + [
            f"pm.collectionVariables.set('{variable}', pm.response.json().id);",
        ]),
        req("Limpieza: el cliente cancela la solicitud de la prueba", "POST", SOLICITUDES + "/{{" + variable + "}}/cancel",
            [JSON, CORR, auth("clienteToken")], {"reason": "Limpieza de la prueba SCRUM-600."}, pruebas=estado(200)),
    ]


hallazgos = {
    "name": "4. Límites conocidos de la regla (hallazgos de SCRUM-600)",
    "item": [
        *[vista_previa(
            f"HALLAZGO 1: una calle de Bogotá con {ciudad} escrita se ubica en Bogotá ({localidad})", direccion,
            ubicacion_en_bogota(localidad)) for ciudad, direccion, localidad in LIMITE_CIUDAD],
        # La vista previa de estas dos direcciones da 422 (carpeta 1), pero al crear solo con la dirección la solicitud se crea
        # con un punto que cae dentro del rectángulo de RN-SR9 (Soacha y el norte de Bogotá).
        *crear_y_cancelar("HALLAZGO 2: Cali, que la vista previa rechaza, se crea con un punto en Soacha", "solicitudCaliId",
                          {"addressText": CALI}, "vista previa: 422"),
        *crear_y_cancelar("HALLAZGO 2: Villavicencio, que la vista previa rechaza, se crea con un punto al norte de Bogotá",
                          "solicitudVillavicencioId", {"addressText": VILLAVICENCIO}, "vista previa: 422"),
        *crear_y_cancelar("HALLAZGO 3: un punto de GPS en Soacha, dentro del rectángulo, crea la solicitud",
                          "solicitudSoachaId",
                          {"addressText": "Centro, Soacha", "location": {"latitude": 4.5794, "longitude": -74.2168}},
                          "GPS en Soacha"),
    ],
}

coleccion = {
    "info": {
        "name": "QUICKPATCH — SCRUM-600 Dirección fuera de Bogotá contra QA",
        "description": (
            "Restricción geográfica a Bogotá (R6 del SAD, RN-SR9 del DD, SRS 2.3.1) contra QA. Una dirección escrita fuera de "
            "Bogotá la rechaza la vista previa con 422 ubicacion-fuera-de-cobertura (o direccion-no-encontrada si el "
            "geocodificador no la reconoce); un punto de GPS fuera del "
            "área de cobertura también da 422. La carpeta 4 deja por escrito tres límites encontrados en QA: el geocodificador "
            "ignora la ciudad escrita cuando la calle existe en Bogotá (1); crear solo con la dirección acepta Cali y "
            "Villavicencio, que la vista previa rechaza, con un punto dentro del rectángulo de cobertura (2); y ese rectángulo "
            "incluye parte de Soacha (3). No necesita el administrador: el cliente se registra solo y cada solicitud que se "
            "crea se cancela. Variable: baseUrl. Correr con --reporters cli: el reporte JSON de Newman guarda tokens."
        ),
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
    },
    "variable": [{"key": "baseUrl", "value": "https://qa.quickpatch.internal"}],
    "item": [preparacion, direccion_escrita, crear_con_direccion, gps, hallazgos],
}

(AQUI / "scrum-600-fuera-de-bogota.postman_collection.json").write_text(
    json.dumps(coleccion, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
