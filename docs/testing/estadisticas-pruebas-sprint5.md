# Cuadro de Mando de Estadísticas de Pruebas — Sprint 5 (SCRUM-604)

**Código del Documento:** `MET-QA-SP5-2026-10-25`  
**Versión:** `2.0 Dinámica Oficial`  
**Fecha de Generación:** 25 de octubre de 2026  
**Responsable:** Katherine Bravo (`ka.bravo@javeriana.edu.co`) — QA Lead  
**Trazabilidad Jira:** Tarea `SCRUM-604` | Requisito RNF-08 | Documento de Pruebas `TD.md` V3.0  
**Principio Metodológico:** Toda cifra reportada proviene directamente de archivos de resultados de CI (.trx/surefire), evidencias Newman en QA, resúmenes JSON de k6 y el registro formal de defectos. Cero cifras escritas a mano.

---

## 1. Pruebas Automatizadas de Microservicios en CI

Las pruebas reales ejecutadas por los pipelines de CI en cada microservicio se extraen directamente de los reportes generados en sus respectivos flujos de integración continua:

| Microservicio | Último Run CI | Unitarias | Integración | Total Pruebas | Pasan | Fallan | Cobertura de Código |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **quickpatch-identity** | Run #57 | 229 | 32 | **261** | 261 | 0 | *Pendiente (SCRUM-602)* |
| **quickpatch-actors** | Run #12 | 6 | 2 | **8** | 8 | 0 | *Pendiente (SCRUM-602)* |
| **quickpatch-catalog** | Run #32 | 20 | 8 | **28** | 28 | 0 | *Pendiente (SCRUM-602)* |
| **quickpatch-communication** | Run #45 | 178 | 8 | **186** | 186 | 0 | *Pendiente (SCRUM-602)* |
| **quickpatch-matching** | Run #41 | 89 | 26 | **115** | 115 | 0 | *Pendiente (SCRUM-602)* |
| **quickpatch-payments** | Run #25 | 54 | 0 | **54** | 54 | 0 | *Pendiente (SCRUM-602)* |
| **quickpatch-ranking** | Run #12 | 6 | 2 | **8** | 8 | 0 | *Pendiente (SCRUM-602)* |
| **quickpatch-servicerequest** | Run #68 | 324 | 48 | **372** | 372 | 0 | *Pendiente (SCRUM-602)* |
| **TOTAL MICROSERVICIOS** | — | **906** | **126** | **1,032** | **1,032** | **0** | *Pendiente (SCRUM-602)* |

> **Nota sobre Cobertura:** La publicación de reportes de cobertura en CI se encuentra en desarrollo bajo la tarea `SCRUM-602` (responsable: Sebastián). Mientras dicha tarea no finalice, la columna permanece en estado formal **Pendiente**, sin estimaciones porcentuales ficticias.

---

## 2. Pruebas de Sistema E2E y Seguridad (QA Desplegado)

Evaluación oficial de las colecciones de prueba automatizadas ejecutadas contra el clúster k3s de QA desplegado (`https://qa.quickpatch.internal`):

| Suite de Prueba | Componente / Servicio | Peticiones HTTP | Aserciones | Pasan | Fallan | Archivo de Evidencia (Ruta Relativa) |
|---|---|:---:|:---:|:---:|:---:|---|
| **SCRUM-56: Registro y Perfil de Técnico** | `quickpatch-identity` | 8 | 23 | 23 | 0 | `tests/e2e/evidencias/scrum-56-registro-tecnico-qa-2026-10-22.txt` |
| **SCRUM-78: Motor de Matching y Asignación** | `quickpatch-matching` | 21 | 43 | 43 | 0 | `tests/e2e/evidencias/scrum-78-qa-2026-10-22.txt` |
| **SCRUM-84: Ciclo Completo de Estados** | `quickpatch-service-request` | 36 | 42 | 42 | 0 | `tests/e2e/evidencias/scrum-84-seguimiento-estado-qa-2026-10-22.txt` |
| **SCRUM-99: Gestión de Equipo de Proveedor** | `quickpatch-actors` | 25 | 43 | 43 | 0 | `tests/e2e/evidencias/scrum-99-equipo-proveedor-qa-2026-10-22.txt` |
| **SCRUM-108: Aprobación y Rechazo de Técnicos** | `quickpatch-identity` | 30 | 40 | 40 | 0 | `tests/e2e/evidencias/scrum-108-aprobacion-rechazo-qa-2026-10-22.txt` |
| **SCRUM-111: Suspensión de Cuenta de Técnico** | `quickpatch-identity` | 29 | 39 | 39 | 0 | `tests/e2e/evidencias/scrum-111-suspension-tecnico-qa-2026-10-22.txt` |
| **SCRUM-Incremento: Cobertura, Ofertas y Detalle** | `Transversal` | 43 | 61 | 61 | 0 | `tests/e2e/evidencias/scrum-incremento-tecnico-qa-2026-10-22.txt` |
| **SCRUM-105: Panel Operativo de Solicitudes** | `quickpatch-service-request` | 29 | 35 | 35 | 0 | `tests/e2e/evidencias/scrum-105-panel-operativo-qa-2026-10-22.txt` |
| **SCRUM-117: Liquidación y Pago (Mock)** | `quickpatch-payments` | 69 | 57 | 57 | 0 | `tests/e2e/evidencias/scrum-117-pago-qa-2026-10-22.txt` |
| **SCRUM-458: Geocodificación y Validación Espacial** | `quickpatch-service-request` | 34 | 44 | 44 | 0 | `tests/e2e/evidencias/scrum-458-geocodificacion-buzon-qa-2026-10-22.txt` |
| **SCRUM-478: Cancelación Atómica de Solicitud** | `quickpatch-service-request` | 48 | 63 | 63 | 0 | `tests/e2e/evidencias/scrum-478-cancelacion-qa-2026-10-19.txt` |
| **SCRUM-483: Mensajería y Chat Bidireccional** | `quickpatch-communication` | 43 | 69 | 69 | 0 | `tests/e2e/evidencias/scrum-483-chat-qa-2026-10-22.txt` |
| **SCRUM-490: Cotización con Tarifa Base** | `quickpatch-service-request` | 61 | 76 | 76 | 0 | `tests/e2e/evidencias/scrum-490-cotizacion-qa-2026-10-22.txt` |
| **SCRUM-495: Comprobante Digital de Pago** | `quickpatch-payments` | 39 | 42 | 42 | 0 | `tests/e2e/evidencias/scrum-495-comprobante-qa-2026-10-22.txt` |
| **SCRUM-68: Cuentas Corporativas e Invitaciones** | `quickpatch-identity` | 32 | 68 | 68 | 0 | `tests/e2e/evidencias/scrum-68-cuenta-corporativa-qa-2026-10-22.txt` |
| **SCRUM-75: Solicitud Corporativa Centro de Costos** | `quickpatch-service-request` | 44 | 56 | 56 | 0 | `tests/e2e/evidencias/scrum-75-solicitud-empresa-qa-2026-10-22.txt` |
| **SCRUM-96: Carga de Evidencia Fotográfica S3** | `quickpatch-service-request` | 46 | 71 | 71 | 0 | `tests/e2e/evidencias/scrum-96-evidencia-qa-2026-10-22.txt` |
| **Auditoría PCI-DSS v4.0 (Trazas Loki)** | `quickpatch-security` | — | 12 | 12 | 0 | `tests/security/evidencias/pci-dss-loki-qa-2026-10-18.txt` |
| **Escaneo Dinámico DAST (OWASP ZAP Baseline)** | `quickpatch-api-gateway` | — | 1 | 1 | 0 | `tests/security/evidencias/zap-dast-baseline-qa-2026-10-18.txt` |
| **TOTAL SUITES DE SISTEMA** | — | **637** | **885** | **885** | **0** | — |

---

## 3. Métricas de Rendimiento k6 (Carga y Estrés)

Conforme a la directriz técnica de QA, las peticiones masivas de carga no se contabilizan como casos de prueba unitarios, sino que se reportan en su propia tabla con sus percentiles de latencia y tasa de fallo:

| Escenario de Carga | Concurrencia (VUs) | Duración | Iteraciones | Peticiones HTTP | Latencia p95 | Tasa de Error | Archivo de Evidencia |
|---|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **Prueba de Carga Concurrente (50 VU)** | 50 VUs | 2m 30s | 2,876 | 5,755 | **73.55 ms** | **0.00%** | `tests/performance/evidencias/k6-load-50vu-summary.json` |
| **Prueba de Estrés Extremo (150 VU)** | 150 VUs | 4m 00s | 38,873 | 38,876 | **415.39 ms** | **0.00%** | `tests/performance/evidencias/k6-stress-150vu-summary.json` |

---

## 4. Registro Consolidado de Defectos (SCRUM-603)

* **Total de Defectos Registrados:** **14 anomalías**.
* **Defectos Corregidos y Verificados:** **9 (64.3%)**.
* **Defectos Descartados / Retractados:** **1 (7.1%)**.
* **Defectos en Mitigación en Sprint 5:** **4 (28.6%)** (ninguno bloqueante).
* **Defectos Críticos o Bloqueantes Abiertos:** **0 (0.0%)**.

Ver detalle exhaustivo en: [`registro-defectos-sprint4-sprint5.md`](file:///c:/Users/kathe/OneDrive/Escritorio/ARQUI/Arquitectura/quickpatch/docs/testing/registro-defectos-sprint4-sprint5.md).

---

## 5. Resumen Ejecutivo y Gráficas de Calidad

* **Total de Pruebas Reales Automatizadas:** **1,917 pruebas / aserciones**.
* **Tasa de Aprobación de Pruebas:** **100.0% PASS (0 fallos)**.
* **Capacidad de Carga k6:** **44,631 peticiones procesadas** con 0.00% de errores y p95 de 415.39 ms bajo 150 VU.
* **Aislamiento Multi-Tenant (RLS) y Seguridad PCI-DSS:** 100% verificado en QA.

### Gráfica 1: Distribución de Pruebas por Tipo
![Gráfica 1: Distribución por Tipo](file:///c:/Users/kathe/OneDrive/Escritorio/ARQUI/Arquitectura/quickpatch/docs/testing/img/grafica-1-pruebas-por-tipo.png)

### Gráfica 2: Tasa de Éxito de Pruebas (100% PASS)
![Gráfica 2: Torta de Éxito](file:///c:/Users/kathe/OneDrive/Escritorio/ARQUI/Arquitectura/quickpatch/docs/testing/img/grafica-2-torta-exito-pruebas.png)

### Gráfica 3: Estado y Severidad de Defectos
![Gráfica 3: Defectos](file:///c:/Users/kathe/OneDrive/Escritorio/ARQUI/Arquitectura/quickpatch/docs/testing/img/grafica-3-barras-defectos.png)

### Gráfica 4: Pruebas Reales de CI por Microservicio
![Gráfica 4: Pruebas de CI por Microservicio](file:///c:/Users/kathe/OneDrive/Escritorio/ARQUI/Arquitectura/quickpatch/docs/testing/img/grafica-4-cobertura-por-servicio.png)
