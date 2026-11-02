import openpyxl
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_PATH = os.path.join(BASE_DIR, 'Matriz_UAT_Avance_QuickPatch.xlsx')
MATRIZ_MD = os.path.join(BASE_DIR, 'matriz-escenarios-calidad-52.md')

print(f"Cargando workbook: {os.path.basename(FILE_PATH)}...")
wb = openpyxl.load_workbook(FILE_PATH, data_only=False)

wb['Funcionalidades']['A2'].value = (
    'Columnas M a O llenadas por QA el 25-oct-2026 al revisar develop de los 15 repos de ARQUI-202630. '
    'Kathe (QA) valida M a O; la PO llena P (UAT). Una X en la columna del rol = el rol usa esa funcionalidad.'
)
wb['Escenarios']['A2'].value = (
    'Fuente: docs/testing/matriz-escenarios-calidad-52.md (sección 2), que sigue la sección 3 del SAD. '
    'Esta hoja se llena con docs/testing/actualizar_matriz_excel.py. '
    "'No medido' = no hay evidencia todavía."
)

# ===========================================================================
# 1. ACTUALIZAR HOJA FUNCIONALIDADES
# ===========================================================================
ws_func = wb['Funcionalidades']
print("Actualizando hoja Funcionalidades...")

func_updates = {
    # RF: (estado_dev, res_qa, evidencia, observaciones, lista_prod, cuenta)
    'RF-02': ('Implementado', 'Aprobado', 'scrum-56-registro-tecnico-qa-2026-10-22.txt (23 aserciones)', 'Registro de técnicos y proveedores validado contra QA desplegado (RFC 9457).', 'Sí', 'Sí'),
    'RF-10': ('Implementado', 'Aprobado con observaciones', 'scrum-incremento-tecnico-qa-2026-10-22.txt (bloques 2.3 y 2.6)', 'Aceptación atómica (OFF-004) y rechazo explícito (OFF-002) verificados; vencimiento a los 3 min pendiente de prueba de reloj.', 'Sí', 'Sí'),
    'RF-12': ('Parcial', 'Sin probar', 'humo-flujo-critico-qa-2026-10-30.txt (calificación 201 y segunda calificación 409)', 'Backend de calificación fusionado (SCRUM-85) y respondiendo en QA por API; falta la pantalla del cliente (SCRUM-86) y su prueba.', 'No', 'Sí'),
    'RF-14': ('Implementado', 'Aprobado', 'scrum-incremento-tecnico-qa-2026-10-22.txt (bloque 3.1 DTL-001)', 'Técnico asignado ve detalle completo con teléfono y dirección (RN-SR13). Terceros reciben 403/404.', 'Sí', 'Sí'),
    'RF-16': ('Implementado', 'Aprobado', 'scrum-99-equipo-proveedor-qa-2026-10-22.txt (43 aserciones)', 'Alta, activación y listado de técnicos del equipo del proveedor certificados en QA.', 'Sí', 'Sí'),
    'RF-17': ('Implementado', 'Sin probar', '', 'Endpoint GET /v1/technicians/me/service-requests pendiente de prueba E2E dedicada (scrum-105 es panel admin).', 'No', 'Sí'),
    'RF-21': ('Implementado', 'Sin probar', '', 'Aislamiento verificado en tenant-beta; activación/desactivación administrativa pendiente de prueba contra QA.', 'No', 'Sí'),
    'RF-23': ('Implementado', 'Aprobado', 'scrum-496-pago-empresa-qa-2026-10-27.txt (59 aserciones, 27-oct)', 'Pago corporativo con usuario empresa_contacto verificado conforme a RN-P6 (SCRUM-118 y SCRUM-496).', 'Sí', 'Sí'),
    'RF-25': ('No implementado', 'Sin probar', '', 'Payments no tiene el endpoint /payments/received (pendiente para sprint futuro).', 'No', 'Sí'),
    'RF-27': ('Parcial', 'Aprobado con observaciones', 'scrum-incremento-tecnico-qa-2026-10-22.txt; scrum-117-pago', 'Flujo completo verificado hasta pago y comprobante; pendiente únicamente calificación (RF-12).', 'No', 'Sí'),
    'RF-29': ('Implementado', 'Aprobado', 'tests/security/evidencias/tls-ingress-qa-2026-10-27.txt; tests/ci-results/identity/ (Run #57)', 'Nginx Ingress fuerza TLSv1.3 (certificado RSA 4096-bit); Identity aplica BCrypt para hash e invitaciones (18 pruebas CI run #57).', 'Sí', 'Sí'),
    'EXT-03': ('Implementado', 'Aprobado', 'quickpatch-mobile releases/tag/v0.5.1-qa (55.25 MB, HTTP 200 OK)', 'Botón en landing descarga directamente quickpatch.apk verificado vía HTTP 302 -> 200 OK.', 'Sí', 'Sí')
}

for r in range(5, ws_func.max_row + 1):
    rf_code = ws_func.cell(r, 1).value
    if rf_code in func_updates:
        dev, qa, evid, obs, prod, cuenta = func_updates[rf_code]
        ws_func.cell(r, 13).value = dev      # Col M: Estado desarrollo
        ws_func.cell(r, 14).value = qa       # Col N: Resultado QA
        if evid:
            ws_func.cell(r, 15).value = evid # Col O: Evidencia QA
        if obs:
            ws_func.cell(r, 17).value = obs  # Col Q: Observaciones
        ws_func.cell(r, 18).value = prod     # Col R: Lista para producción
        ws_func.cell(r, 19).value = cuenta   # Col S: Cuenta en el %

# ===========================================================================
# 2. ACTUALIZAR HOJA ESCENARIOS (52 Escenarios del SAD)
# ===========================================================================
ws_esc = wb['Escenarios']
print("\nActualizando hoja Escenarios desde matriz-escenarios-calidad-52.md...")

# La matriz en markdown es la fuente única: valor medido, evidencia, estado y
# observaciones de cada escenario salen de su sección 2.
LATEX = [
    (r'\approx', '≈'), (r'\ge', '≥'), (r'\le', '≤'), (r'\times', '×'), (r'\%', '%'),
]


def texto_plano(celda):
    celda = celda.replace('**', '').replace('`', '').replace('*', '')
    for latex, simbolo in LATEX:
        celda = celda.replace(latex, simbolo)
    celda = re.sub(r'\\text\{\s*([^}]*)\}', r' \1', celda)
    celda = celda.replace('$', '')
    return re.sub(r'\s+', ' ', celda).strip()


with open(MATRIZ_MD, encoding='utf-8') as f:
    seccion_2 = f.read().split('## 3.')[0]

esc_updates = {}
for linea in seccion_2.splitlines():
    m = re.match(r'\| \*\*(AC\d-E\d)\*\* \|', linea)
    if not m:
        continue
    columnas = [c.strip() for c in linea.strip().strip('|').split('|')]
    if len(columnas) != 8:
        continue
    valor, evidencia, estado, obs = columnas[4], columnas[5], columnas[6], columnas[7]
    evidencia = '' if 'Sin archivo de evidencia' in evidencia else texto_plano(evidencia)
    esc_updates[m.group(1)] = (texto_plano(valor), evidencia, texto_plano(estado), texto_plano(obs))

if len(esc_updates) != 52:
    sys.exit(f"La matriz trae {len(esc_updates)} escenarios en la sección 2; se esperaban 52.")

for r in range(5, ws_esc.max_row + 1):
    esc_id = ws_esc.cell(r, 1).value
    if esc_id in esc_updates:
        v_med, evid, estado, obs = esc_updates.pop(esc_id)
        ws_esc.cell(r, 6).value = v_med            # Col F: Valor medido
        ws_esc.cell(r, 7).value = evid or None     # Col G: Evidencia
        ws_esc.cell(r, 8).value = estado           # Col H: Estado (Cumple, Parcial, No cumple, No medido)
        ws_esc.cell(r, 10).value = obs             # Col J: Observaciones

if esc_updates:
    sys.exit(f"Escenarios de la matriz que no están en la hoja: {', '.join(sorted(esc_updates))}")

# ===========================================================================
# 3. ACTUALIZAR HOJA PRUEBAS
# ===========================================================================
ws_pruebas = wb['Pruebas']
print("\nActualizando hoja Pruebas...")

# Ajustar filas de k6 conforme a observaciones de Juan Diego y Angie:
# Fila 20: k6 carga 50 VU
ws_pruebas.cell(20, 5).value = 5755 # Total requests
ws_pruebas.cell(20, 6).value = 5755
ws_pruebas.cell(20, 8).value = 0
ws_pruebas.cell(20, 9).value = 'k6-load-50vu-summary.json (50 VU sostenidos, p95 = 73.55 ms, tasa fallos = 0.00%)'

# Fila 21: k6 estrés 150 VU
ws_pruebas.cell(21, 5).value = 38876 # Total requests
ws_pruebas.cell(21, 6).value = 38876
ws_pruebas.cell(21, 8).value = 0
ws_pruebas.cell(21, 9).value = 'k6-stress-150vu-summary.json (150 VU sostenidos, p95 = 415.39 ms, tasa fallos = 0.00%)'

# Fila 24: Pruebas unitarias e integración de CI y App Móvil
ws_pruebas.cell(24, 1).value = 'Pruebas unitarias e integración (CI Backend + App Móvil)'
ws_pruebas.cell(24, 2).value = 'Unitarias / integración'
ws_pruebas.cell(24, 3).value = '2026-10-25'
ws_pruebas.cell(24, 4).value = 'CI / App'
ws_pruebas.cell(24, 5).value = 1525  # 1,032 CI backend + 493 pruebas app móvil
ws_pruebas.cell(24, 6).value = 1525  # Aserciones / tests ejecutados
ws_pruebas.cell(24, 8).value = 0     # Aserciones fallidas en runs oficiales
ws_pruebas.cell(24, 9).value = 'CI Backend: 1,032 pruebas (Identity #57: 261, SR #68: 372, Comm #45: 186, Matching #41: 115, Payments #25: 54, Catalog #32: 28, Ranking #12: 8, Actors #12: 8) + App Móvil: 493 pruebas'
ws_pruebas.cell(24, 10).value = 'AC7-E1, RNF-08 (8 repos backend + App Flutter; Ranking/Actors son esqueletos; pruebas panel web van aparte en Sp5; cobertura pendiente en SCRUM-602)'

# Añadir filas de suites del 22-oct
suites_sp4 = [
    ('scrum-56 registro técnico', 'E2E / API', '2026-10-22', 'QA', 8, 23, 0, 'scrum-56-registro-tecnico-qa-2026-10-22.txt', 'RF-02'),
    ('scrum-78 motor matching', 'E2E / API', '2026-10-22', 'QA', 21, 43, 0, 'scrum-78-qa-2026-10-22.txt', 'RF-09'),
    ('scrum-84 seguimiento estado', 'E2E / API', '2026-10-22', 'QA', 36, 42, 0, 'scrum-84-seguimiento-estado-qa-2026-10-22.txt', 'RF-11'),
    ('scrum-99 equipo proveedor', 'E2E / API', '2026-10-22', 'QA', 25, 43, 0, 'scrum-99-equipo-proveedor-qa-2026-10-22.txt', 'RF-16'),
    ('scrum-108 aprobación/rechazo', 'E2E / API', '2026-10-22', 'QA', 30, 40, 0, 'scrum-108-aprobacion-rechazo-qa-2026-10-22.txt', 'RF-19'),
    ('scrum-111 suspensión técnico', 'E2E / API', '2026-10-22', 'QA', 29, 39, 0, 'scrum-111-suspension-tecnico-qa-2026-10-22.txt', 'RF-20'),
    ('scrum-incremento técnico', 'E2E / API', '2026-10-22', 'QA', 43, 61, 0, 'scrum-incremento-tecnico-qa-2026-10-22.txt', 'RF-10, RF-13, RF-14')
]

for idx, s in enumerate(suites_sp4):
    target_row = 25 + idx
    ws_pruebas.cell(target_row, 1).value = s[0]
    ws_pruebas.cell(target_row, 2).value = s[1]
    ws_pruebas.cell(target_row, 3).value = s[2]
    ws_pruebas.cell(target_row, 4).value = s[3]
    ws_pruebas.cell(target_row, 5).value = s[4]
    ws_pruebas.cell(target_row, 6).value = s[5]
    ws_pruebas.cell(target_row, 7).value = f'=IF(F{target_row}="","",F{target_row}-H{target_row})'
    ws_pruebas.cell(target_row, 8).value = s[6]
    ws_pruebas.cell(target_row, 9).value = s[7]
    ws_pruebas.cell(target_row, 10).value = s[8]

# ===========================================================================
# 4. ACTUALIZAR HOJA DEFECTOS
# ===========================================================================
ws_def = wb['Defectos']
print("\nActualizando hoja Defectos...")

defectos_data = [
    ('BUG-001', 'Geolocalización dependía de Google Location', '3', 'Alta', 'Mobile', 'RF-07', '2026-10-07', 'Verificado', '2026-10-08', 'quickpatch-mobile#7'),
    ('BUG-002', 'Colisión del CIDR de k3s con la red del laboratorio', '3', 'Crítica', 'Infraestructura', 'INF-010', '2026-10-07', 'Verificado', '2026-10-08', 'INFRASTRUCTURE.md v1.2'),
    ('BUG-003', 'Aserción permisiva en RN-T1 en las suites E2E', '3', 'Media', 'E2E Postman', 'RN-T1', '2026-10-07', 'Resuelto', '2026-10-08', 'scrum-65 colección'),
    ('BUG-004', 'Problem Details incorrecto en el rechazo RFC 9457', '3', 'Media', 'ServiceRequest', 'RN-SR9', '2026-10-07', 'Resuelto', '2026-10-08', 'validar-diagnostico-error-qa.js'),
    ('BUG-SP4-001', 'Emulación de aislamiento en harness local (reqId !== sr-qa-001)', '4', 'Media', 'Harness Local', 'RF-09', '2026-10-17', 'Verificado', '2026-10-18', 'Commit f6db3e7 (mock-gateway-local-simulacion.js:564)'),
    ('BUG-SP4-002', 'Colisión de scope en Newman entre environment y colección', '4', 'Media', 'Runner MVP', 'RF-01', '2026-10-18', 'Verificado', '2026-10-18', 'Commit 308f245 (run-mvp.js:40)'),
    ('BUG-SP4-003', 'Contaminación de estado en memoria entre suites en harness local', '4', 'Media', 'Harness Local', 'RF-20', '2026-10-18', 'Verificado', '2026-10-18', 'Commit 743d06c (run-all-increment-suites.js:50 resetState)'),
    ('BUG-SP4-004', 'Fallo de codificación UnicodeEncodeError en consolas Windows cp1252', '4', 'Baja', 'Scanner PCI', 'PCI-DSS', '2026-10-18', 'Verificado', '2026-10-18', 'Commit 308f245 (run-pci-dss-suite.py:20)'),
    ('BUG-SP4-005', 'Invocación PUT /status en vez de POST /start y /complete', '4', 'Media', 'Suite E2E', 'RF-11', '2026-10-18', 'Resuelto', '2026-10-22', 'scrum-84-seguimiento-estado-qa-2026-10-22.txt'),
    ('BUG-SP4-006', 'Endpoint /assigned-detail inexistente en OpenAPI 1.1.0 canónico', '4', 'Media', 'Suite E2E', 'RF-14', '2026-10-18', 'Resuelto', '2026-10-22', 'scrum-incremento-tecnico-qa-2026-10-22.txt (GET /service-requests/{id})'),
    ('BUG-SP4-007', 'Dependencia de fixtures fijos ausentes en base de datos de QA', '4', 'Media', 'Colecciones E2E', 'RF-02', '2026-10-18', 'Resuelto', '2026-10-22', 'scrum-56-registro-tecnico-qa-2026-10-22.txt (preparacion())'),
    ('BUG-SP4-008', 'Discrepancia en aserción de tipo RFC 9457 problems/validacion', '4', 'Baja', 'Suite E2E', 'RF-02', '2026-10-22', 'Resuelto', '2026-10-22', 'scrum-56-registro-tecnico-qa-2026-10-22.txt'),
    ('BUG-SP4-009', 'Rechazo 400 por campo adicional specialty en alta de técnico', '4', 'Media', 'Suite E2E', 'RF-16', '2026-10-22', 'Resuelto', '2026-10-22', 'scrum-99-equipo-proveedor-qa-2026-10-22.txt (specialtyId)'),
    ('DEF-S4-02', 'Falta de auto-cancelación en k6 acumuló solicitudes abiertas', '4', 'Alta', 'Pruebas / QA', 'RF-05', '2026-10-19', 'Resuelto', '2026-10-20', 'PR quickpatch#121 rutina cancelar() en k6'),
    ('DEF-S4-03', 'Advertencias informativas HSTS y CSP en escaneo DAST ZAP', '4', 'Media', 'API Gateway', 'AC6', '2026-10-19', 'Resuelto', '', 'Corregido en Nginx Gateway; pendiente verificar repitiendo ZAP por VPN'),
    ('SCRUM-606', 'Manejo de reconexión y heartbeat en canal WebSocket', '5', 'Media', 'Communication', 'RF-11', '2026-10-24', 'En corrección', '', 'scrum-478-aviso-tiempo-real-qa-2026-10-22.txt'),
    ('SCRUM-607', 'Desglose de IVA e impuestos en comprobante digital PDF', '5', 'Baja', 'Payments', 'RF-24', '2026-10-24', 'En corrección', '', 'scrum-495-comprobante-qa-2026-10-22.txt'),
    ('SCRUM-608', 'Inyección de coordenadas GPS mock en emulador Android para UAT', '5', 'Media', 'Mobile', 'RF-07', '2026-10-24', 'En corrección', '', 'quickpatch-mobile UAT test cases'),
    ('SCRUM-609', 'Ajuste de paginación reactiva en lista de técnicos del Web Admin', '5', 'Baja', 'Web Admin', 'RF-19', '2026-10-24', 'En corrección', '', 'quickpatch-web admin portal')
]

for idx, d in enumerate(defectos_data):
    target_row = 5 + idx
    for col_idx, val in enumerate(d, start=1):
        ws_def.cell(target_row, col_idx).value = val

# Guardar workbook
print(f"\nGuardando cambios en {os.path.basename(FILE_PATH)}...")
try:
    wb.save(FILE_PATH)
    print("¡Archivo Excel modificado y guardado con éxito en la ruta principal!")
except PermissionError:
    FILE_PATH_V2 = os.path.join(BASE_DIR, 'Matriz_UAT_Avance_QuickPatch_v2.xlsx')
    print(f"El archivo principal está abierto en Excel (bloqueado). Guardando copia en {os.path.basename(FILE_PATH_V2)}...")
    wb.save(FILE_PATH_V2)
    print("¡Archivo guardado con éxito en Matriz_UAT_Avance_QuickPatch_v2.xlsx!")
