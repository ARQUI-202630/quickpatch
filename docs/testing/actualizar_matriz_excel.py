import openpyxl
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import os

local_excel = os.path.join(os.path.dirname(__file__), 'Matriz_UAT_Avance_QuickPatch.xlsx')
downloads_excel = r'C:\Users\kathe\Downloads\Matriz_UAT_Avance_QuickPatch.xlsx'
FILE_PATH = local_excel if os.path.exists(local_excel) else downloads_excel

print(f"Cargando workbook: {FILE_PATH}...")
wb = openpyxl.load_workbook(FILE_PATH, data_only=False)

# ===========================================================================
# 1. ACTUALIZAR HOJA FUNCIONALIDADES
# ===========================================================================
ws_func = wb['Funcionalidades']
print("Actualizando hoja Funcionalidades...")

func_updates = {
    # RF: (estado_dev, res_qa, evidencia, observaciones, lista_prod, cuenta)
    'RF-02': ('Implementado', 'Aprobado', 'scrum-56-registro-tecnico-qa-2026-10-22.txt (23 aserciones)', 'Registro de técnicos y proveedores validado contra QA desplegado (RFC 9457).', 'Sí', 'Sí'),
    'RF-10': ('Implementado', 'Aprobado con observaciones', 'scrum-incremento-tecnico-qa-2026-10-22.txt (bloques 2.3 y 2.6)', 'Aceptación atómica (OFF-004) y rechazo explícito (OFF-002) verificados; vencimiento a los 3 min pendiente de prueba de reloj.', 'Sí', 'Sí'),
    'RF-12': ('No implementado', 'Sin probar', '', 'Ranking es un esqueleto con 8 pruebas; sin endpoint de calificación.', 'No', 'Sí'),
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
print("\nActualizando hoja Escenarios...")

esc_updates = {
    # ID: (valor_medido, evidencia, estado, observaciones)
    'AC1-E1': ('0 asignaciones a técnicos de otra especialidad', 'scrum-78-qa-2026-10-22.txt; scrum-incremento-tecnico-qa-2026-10-22.txt', 'Cumple', 'Filtro por especialidad validado en motor de matching (0 asignaciones erróneas).'),
    'AC1-E3': ('Detalle completo (categoría, dirección, teléfono) entregado al técnico', 'scrum-incremento-tecnico-qa-2026-10-22.txt (bloque 3.1 DTL-001)', 'Cumple', 'Detalle completo visible para técnico asignado (RN-SR13). Terceros reciben 403.'),
    'AC2-E1': ('p95 = 73.55 ms en carga 50 VU (< 3 s)', 'tests/performance/evidencias/k6-load-50vu-summary.json', 'Cumple', 'Búsqueda espacial con PostGIS y latencia percentil 95 muy por debajo de 3s.'),
    'AC2-E3': ('≈ 2 s en pruebas E2E contra QA (< 7 s)', 'scrum-490-cotizacion-qa-2026-10-22.txt; scrum-478-aviso-tiempo-real-qa-2026-10-22.txt', 'Cumple', 'Tiempo desde creación de solicitud hasta entrega de evento WebSocket en QA.'),
    'AC2-E4': ('150 VU sostenido, 0% fallos (38,876 reqs), p95 = 415.39 ms', 'tests/performance/evidencias/k6-stress-150vu-summary.json', 'Cumple', 'Carga masiva sostenida durante 4 minutos sin degradación ni pérdida de peticiones.'),
    'AC2-E5': ('0 caídas observadas en k6', 'tests/performance/evidencias/k6-stress-150vu-qa-2026-10-18.txt', 'Parcial', 'Requiere captura gráfica de Grafana / kubectl get pods con limits (Infraestructura §5.6).'),
    'AC3-E2': ('8 microservicios coexistiendo en VM2 k3s; p95 = 73.55 ms y 0 pods desalojados', 'k6-stress-150vu-qa-2026-10-18.txt; tests/ci-results/', 'Cumple', 'Convivencia y estabilidad demostrada bajo carga masiva sin fallos.'),
    'AC5-E3': ('Eventos retenidos en outbox_events y procesados al reconectar', 'scrum-incremento-tecnico-qa-2026-10-22.txt (outbox pattern)', 'Parcial', 'Garantía Outbox atómica verificada en persistencia PostgreSQL.'),
    'AC5-E4': ('Persistencia transaccional en outbox_events; reintento activo', 'docs/architecture/SDD.md §4.2; outbox_events en PostgreSQL', 'Parcial', 'Patrón Outbox implementado en microservicios productores.'),
    'AC5-E5': ('Sin prueba de deduplicación en QA', '', 'No medido', 'Prueba de reintento de eventos duplicados en QA pendiente de ejecución; verificada en suite local.'),
    'AC5-E6': ('Flujo E2E probado sin fallos (61 aserciones PASS)', 'tests/e2e/evidencias/scrum-incremento-tecnico-qa-2026-10-22.txt', 'Parcial', 'Flujo verificado hasta pago y comprobante; calificación pendiente por RF-12 no desarrollado.'),
    'AC6-E1': ('0 números PAN/CVV en 2,649 trazas auditadas en Loki', 'tests/security/evidencias/pci-dss-loki-qa-2026-10-18.txt', 'Cumple', 'Escaneo exhaustivo de logs estructurados con regex de tarjetas de crédito.'),
    'AC6-E2': ('Accesos cross-tenant aislados responden 404 (0 fugas)', 'tests/e2e/evidencias/scrum-108-aprobacion-rechazo-qa-2026-10-22.txt; tenant-beta-qa-2026-10-15.txt', 'Cumple', 'Aislamiento lógico garantizado con Row-Level Security (RLS) en PostgreSQL VM5.'),
    'AC6-E3': ('Accesos no autorizados bloqueados con HTTP 403 Forbidden', 'tests/e2e/evidencias/scrum-56-registro-tecnico-qa-2026-10-22.txt; scrum-105-panel-operativo-qa-2026-10-22.txt', 'Cumple', 'Control de acceso basado en roles (RBAC) validado en API Gateway y microservicios.'),
    'AC6-E4': ('401 en REST y 4001 en WS ante tokens sin firma/expirados', 'tests/e2e/evidencias/mvp-qa-sprint4-2026-10-18.txt; scrum-478-aviso-tiempo-real-qa-2026-10-22.txt', 'Cumple', 'Rechazo inmediato de JWT RSA-256 expirados o manipulados.'),
    'AC6-E5': ('Transiciones registradas con actor, timestamp y S3', 'tests/e2e/evidencias/scrum-84-seguimiento-estado-qa-2026-10-22.txt; scrum-96-evidencia-qa-2026-10-22.txt', 'Cumple', 'Trazabilidad de la orden y evidencia fotográfica en Garage S3.'),
    'AC6-E8': ('423 Locked tras 5 intentos fallidos (RN-U4)', 'mvp-qa-sprint4-2026-10-18.txt (bloque fuerza bruta)', 'Cumple', 'Mitigación de fuerza bruta en autenticación verificada en QA.'),
    'AC7-E1': ('1,032 pruebas CI backend aprobadas en runs de 1m a 4m (< 10 min)', 'GitHub Actions (8 repositorios backend, runs oficiales)', 'Cumple', 'Pipelines automatizados de CI ejecutan unitarias e integración en repos backend; cobertura no publicada aún.'),
    'AC7-E2': ('Sin conteo formal de PRs por repositorio', '', 'No medido', 'Métrica histórica de PRs por repositorio pendiente de consolidar en Sprint 5.'),
    'AC7-E6': ('Compuertas 2.1 a 2.6 aprobadas; pruebas k6 en QA (ADR-015)', 'docs/testing/informe-pruebas-sprint4.md §5', 'Cumple', 'Aislamiento total de producción; validación en QA previa a promoción.'),
    'AC8-E3': ('Soporte de cuenta Empresa integrado limpiamente (RF-06, RF-08)', 'scrum-68-cuenta-corporativa-qa-2026-10-22.txt; scrum-75-solicitud-empresa-qa-2026-10-22.txt', 'Cumple', 'Nuevo tipo de cliente corporativo integrado sin regresiones en el dominio.'),
    'AC9-E1': ('Saltos de estado inválidos responden 409 Conflict', 'tests/e2e/evidencias/scrum-84-seguimiento-estado-qa-2026-10-22.txt', 'Cumple', 'Máquina de estados estricta en ServiceRequest bloquea transiciones ilegales.'),
    'AC9-E4': ('Transición atómica a en_espera sin candidatos elegibles', 'tests/e2e/evidencias/scrum-78-qa-2026-10-22.txt', 'Cumple', 'Lógica de reintentos y paso a en_espera probada en Matching Service.'),
    'AC9-E5': ('Conciliación y manejo de timeout en pasarela simulada', 'tests/e2e/evidencias/scrum-117-pago-qa-2026-10-22.txt; scrum-495-comprobante-qa-2026-10-22.txt', 'Cumple', 'Manejo de estados pendientes y pago simulado sin duplicación de cobros.'),
    'AC9-E7': ('Suites E2E de incremento técnico aprobadas antes de merge', 'scrum-incremento-tecnico-qa-2026-10-22.txt', 'Cumple', 'Integración de componentes del incremento técnico validada en QA.')
}

for r in range(5, ws_esc.max_row + 1):
    esc_id = ws_esc.cell(r, 1).value
    if esc_id in esc_updates:
        v_med, evid, estado, obs = esc_updates[esc_id]
        ws_esc.cell(r, 6).value = v_med   # Col F: Valor medido
        ws_esc.cell(r, 7).value = evid    # Col G: Evidencia
        ws_esc.cell(r, 8).value = estado  # Col H: Estado (Cumple, Parcial, No cumple, No medido)
        if obs:
            ws_esc.cell(r, 10).value = obs # Col J: Observaciones

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
print(f"\nGuardando cambios en {FILE_PATH}...")
try:
    wb.save(FILE_PATH)
    print("¡Archivo Excel modificado y guardado con éxito en la ruta principal!")
except PermissionError:
    FILE_PATH_V2 = r'C:\Users\kathe\Downloads\Matriz_UAT_Avance_QuickPatch_v2.xlsx'
    print(f"El archivo principal está abierto en Excel (bloqueado). Guardando copia refinada en {FILE_PATH_V2}...")
    wb.save(FILE_PATH_V2)
    print("¡Archivo guardado con éxito en Matriz_UAT_Avance_QuickPatch_v2.xlsx!")
