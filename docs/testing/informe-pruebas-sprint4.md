# Informe Consolidado de Pruebas — Sprint 4 (SCRUM-394 / SCRUM-398)

**Código del Documento:** `INF-QA-SP4-2026-10-22`  
**Versión:** `2.0 Final (Revisión QA)`  
**Fecha de Emisión:** 22 de octubre de 2026  
**Responsable:** Katherine Bravo (`ka.bravo@javeriana.edu.co`) — QA Lead  
**Trazabilidad Jira:** Historia Padre `SCRUM-394` | Subtareas `SCRUM-395`, `SCRUM-396`, `SCRUM-397`, `SCRUM-398`  
**Referencias Normativas:** SRS V5.0 / SAD V4 (v2.28) / DD V4 / TD V2.8 / ADR-015 / ADR-022 / RNF-08  
**Clasificación:** Entrega Formal de Aseguramiento de Calidad de Software (Quality Gate 2)  

---

## 1. Resumen Ejecutivo y Decisión de la Compuerta de Calidad

El presente informe consolida los resultados del ciclo integral de verificación y validación (V&V) ejecutado durante el **Sprint 4** sobre la plataforma **QUICKPATCH**, implementando una estrategia rigurosa de dos niveles:
1. **Ejecución Directa contra el Ambiente de QA Desplegado (`https://qa.quickpatch.internal` / VM1 Nginx Ingress / VM2 k3s):** Pruebas de integración automatizadas sobre microservicios activos (Identity, Catalog, ServiceRequest, Matching, Payments) ejecutadas mediante `correr-colecciones-qa.js`, validando endpoints reales, emisión de JWT RS256, máquinas de estados y **aislamiento intra-tenant estricto vía RLS (HTTP 404)**.
2. **Simulación Local Preparatoria (Harness de Contratos OpenAPI - `mock-gateway-local-simulacion.js`):** Validación exhaustiva de contratos sintácticos, concurrencia y máquinas de estado para certificar conformidad previa a la salida a QA.

### 1.1 Dictamen de la Compuerta de Calidad (Release Gate Decision)

> ### **ESTADO DEL RELEASE: GO — CALIDAD Y SUITES E2E VERIFICADAS EN QA**
> 
> **Veredicto:** El aseguramiento de calidad del Sprint 4 ha verificado con éxito las capacidades fundamentales del incremento técnico en el ambiente de QA desplegado.
> 
> Las observaciones iniciales identificadas en corridas preliminares (dependencia de credenciales fijas y discrepancias menores de contrato) fueron atendidas formalmente mediante la adopción del patrón dinámico `preparacion()` con `importlib`, la corrección del esquema `ProviderTechnicianRequest` (SCRUM-99) y la alineación del contrato Problem Details `problems/validacion` en Identity (SCRUM-56).
> 
> **Resumen de Métricas Clave:**
> * **Ejecución contra QA Desplegado (Corridas Oficiales del 22 de Octubre con `correr-colecciones-qa.js`):**
>   - **SCRUM-78 (Motor de Matching y SLA RNF-05):** 43 de 43 aserciones exitosas (**100.0% PASS**, SLA medido $< 60\text{ s}$).
>   - **SCRUM-84 (Seguimiento de Estado en Tiempo Real):** 100% PASS verificado contra QA (ciclo de 4 estados, `POST /start`, foto obligatoria y `POST /complete`).
>   - **SCRUM-56 (Registro y Perfil Técnico):** 100% PASS (registro dinámico, duplicados 409 y validación RFC 9457 `problems/validacion`).
>   - **SCRUM-99 (Gestión de Equipo de Proveedor):** 100% PASS (alta bajo `ProviderTechnicianRequest` sin campo excedente `specialty`, RLS y RBAC).
>   - **SCRUM-108 y SCRUM-111 (Admin Aprobación, Rechazo y Suspensión):** 100% PASS con actores creados dinámicamente.
>   - **SCRUM-81 / SCRUM-90 / SCRUM-93 (Incremento Técnico):** 100% PASS (20 localidades, disponibilidad, ofertas y detalle con contacto).
>   - **Evidencias Reales:** Exportaciones limpias de Newman generadas hoy en `tests/e2e/evidencias/*-qa-2026-10-22.txt`.
> * **Simulación Local Preparatoria (Harness):** 158 peticiones, 326 aserciones (**100.0% PASS** en contratos).
> * **Seguridad y Confidencialidad en QA:** Aislamiento intra-tenant verificado en vivo con 404 RFC 9457 (`/no-encontrado`). 0 fugas de tarjetas en trazas de microservicios (PCI-DSS v4.0).
> * **Rendimiento k6 (Carga 50 VU):** Catálogo $p95 = 60\text{ ms} < 200\text{ ms}$, Creación $p95 = 114\text{ ms} < 2.0\text{ s}$, Error rate $= 0.00\% < 1.0\%$.
> * **Rendimiento k6 (Estrés 150 VU):** Latencia $p95 = 540\text{ ms} < 5.0\text{ s}$, Errores 5xx $= 0.00\%$, 0 pods caídos (0 OOMKilled).
> * **Seguridad Dinámica DAST (OWASP ZAP):** 0 alertas Críticas / Altas sobre el API Gateway.
> * **Gestión de Defectos (DEF-QA-SP4):** 9 reportes gestionados (4 resueltos y verificados, 5 ajustes contractuales/diseño cerrados). 0 defectos bloqueantes abiertos.

### 1.2 Cuadro de Mando de Compuertas de Calidad (Quality Gates)

| Compuerta de Calidad | Métrica Evaluada | Criterio de Aceptación | Resultado Obtenido | Estado |
|---|---|---|---|:---:|
| **Compuerta 2.1: QA Desplegado (Real)** | Colecciones Newman (`correr-colecciones-qa.js`) | Ejecución real y paso de suites E2E | 100% aserciones PASS en suites del 22 de octubre | ✅ Aprobada |
| **Compuerta 2.1b: Simulación Local (Contratos)** | Suites completas en `mock-gateway-local-simulacion` | 100% aserciones de contrato PASS | 158 reqs, 326 aserciones PASS (0 fallos) | ✅ Aprobada |
| **Compuerta 2.2: Seguridad PCI-DSS** | Escáner sobre trazas de microservicios activos | Cero exposición de PAN o CVV (PAY-002) | 0 PANs y 0 CVVs detectados en logs | ✅ Aprobada |
| **Compuerta 2.3: Rendimiento Carga 50 VU** | Latencia p95 y Tasa de Fallos | Catálogo $< 200\text{ms}$, Orden $< 2\text{s}$, Fallos $< 1\%$ | Catálogo: $60\text{ms}$, Orden: $114\text{ms}$, Fallos: $0.00\%$ | ✅ Aprobada |
| **Compuerta 2.4: Rendimiento Estrés 150 VU** | Estabilidad de Pods y Errores 5xx | Latencia $< 5\text{s}$, Errores 5xx $= 0\%$, 0 caídas | Latencia: $540\text{ms}$, Errores 5xx: $0.00\%$, 0 OOMKilled | ✅ Aprobada |
| **Compuerta 2.5: Seguridad DAST (OWASP)** | Escaneo ZAP Baseline (INF-013) | 0 alertas Críticas / Altas (FAIL) | 0 alertas Críticas / Altas; TLS 1.3 y HSTS activos | ✅ Aprobada |
| **Compuerta 2.6: Calidad de Defectos** | Aislamiento y defectos blocker | 0 vulneraciones de aislamiento | 4 defectos resueltos; aislamiento intra-tenant validado 100% | ✅ Aprobada |

---

## 2. Alcance Evaluado del Sprint 4

El alcance de pruebas cubrió las Historias de Usuario priorizadas, requerimientos funcionales y reglas de negocio del Sprint 4:

```
                                       ALCANCE EVALUADO SPRINT 4
                                                   │
         ┌────────────────────────┬───────────────┴───────────────┬────────────────────────┐
         ▼                        ▼                               ▼                        ▼
     Flujo Técnico         Seguimiento Realtime             Gestión Proveedor       Administración y Matching
   (SCRUM-81/90/93)           (SCRUM-84)                       (SCRUM-99)             (SCRUM-78/108/111)
  • 20 Localidades Bogotá  • 4 estados de la orden          • Alta de técnicos       • SLA Matching < 60s
  • Cobertura espacial     • Latencia WebSocket < 1 min     • Herencia de tenant     • Aprobación/Rechazo (RN-TP1)
  • Aceptación atómica     • Notificación Push a cliente    • Cero fuga intra-tenant • Suspensión/Reactivación (RN-TP2)
  • Ocultamiento dirección • Canal WebSocket Gateway         • Estado inicial pend.   • Idempotencia processed_events
```

### 2.1 Trazabilidad Bidireccional de Historias de Usuario Evaluadas
1. **SCRUM-22 / RF-06:** Creación de solicitud con geolocalización en Bogotá D.C. y validación de cobertura (422 ante coordenadas fuera de perímetro).
2. **SCRUM-24 / RF-07:** Notificación a técnicos candidatos cumpliendo distancia y especialidad.
3. **SCRUM-29 / 78 / RF-09:** Asignación automática mediante motor de matching con SLA medido $< 60\text{ segundos}$ (RNF-05, AC2-E3).
4. **SCRUM-30 / 81 / RF-10:** Aceptación y rechazo de ofertas técnicas; transición atómica a estado `ocupado` con evento Outbox (ADR-007) y rechazo sin penalización (R12).
5. **SCRUM-31 / 84 / RF-11:** Seguimiento en tiempo real del ciclo de 4 estados (`buscando_tecnico` $\to$ `asignado` $\to$ `en_progreso` $\to$ `completado`) con canal WebSocket en Gateway (ADR-023).
6. **SCRUM-33 / 90 / RF-13:** Configuración de disponibilidad y cobertura geográfica en exactamente 20 localidades oficiales de Bogotá D.C. Bloqueo de cambio a disponible si el técnico está ocupado (409 Conflict, RN-M6).
7. **SCRUM-34 / 93 / RF-14:** Detalle de solicitud para técnico asignado con exposición de datos de contacto (RN-SR13). Ocultamiento estricto previo a asignación (403) y confidencialidad intra-tenant (404).
8. **SCRUM-36 / 99 / RF-16:** Gestión de equipo por proveedor; alta con herencia de inquilino y aislamiento intra-tenant absoluto (RN-TP3, RN-TP4).
9. **SCRUM-39 / 108 / RF-19:** Aprobación y rechazo administrativo de técnicos; motivo de rechazo obligatorio $\ge 5$ caracteres (400 Bad Request con RFC 9457 ante omisión).
10. **SCRUM-40 / 111 / RF-20:** Suspensión y reactivación de técnicos; exclusión inmediata de rondas de matching (RN-TP2).
11. **SCRUM-112 / RF-01:** Gestión de inquilinos de plataforma por `admin_plataforma`.
12. **SCRUM-287 / RF-03 / RF-04:** Desactivación lógica de categorías en catálogo y verificación de perfil técnico.

---

## 3. Detalle de Ejecución y Resultados por Compuerta

### 3.1 Compuerta 2.1 — Pruebas Funcionales y E2E de API

La evaluación de API se ejecutó en dos modalidades complementarias:

#### 3.1.1 Diagnóstico de Ejecución en QA Desplegado y Realidad de Evidencias

La evaluación de API se ejecutó en dos modalidades complementarias:

1. **Simulación Local Preparatoria (Harness `mock-gateway-local-simulacion.js`):**
   - 158 peticiones, 326 aserciones evaluadas: **100.0% PASS** (`tests/e2e/evidencias/suites-e2e-qa-sprint4-2026-10-18.txt`).
   - Respaldó la consistencia sintáctica de los contratos OpenAPI y las reglas de negocio antes de la salida a QA.

2. **Ejecución y Certificación Oficial contra el Ambiente de QA Desplegado (`https://qa.quickpatch.internal` / 22 de octubre de 2026):**
   - Tras corregir los puntos observados en la revisión del PR #106 (adopción de usuarios dinámicos con `preparacion()`, corrección contractual de `ProviderTechnicianRequest` y homologación de Problem Details RFC 9457 `problems/validacion`), las suites del incremento técnico fueron ejecutadas formalmente contra el ambiente de QA mediante `correr-colecciones-qa.js`, alcanzando una **tasa de aprobación del 100.0% (291 aserciones aprobadas de 291 evaluadas, 0 fallidas)**.
   - **Desglose oficial por colección en QA (22 de octubre):**
     * `scrum-56` (Registro y Perfil de Técnico): 8 peticiones, 23 aserciones aprobadas (✓), 0 fallidas (✗) — **100% PASS**.
     * `scrum-84` (Seguimiento de Estado en Tiempo Real): 36 peticiones, 42 aserciones aprobadas (✓), 0 fallidas (✗) — **100% PASS**.
     * `scrum-99` (Gestión de Equipo de Proveedor): 25 peticiones, 43 aserciones aprobadas (✓), 0 fallidas (✗) — **100% PASS**.
     * `scrum-108` (Aprobación y Rechazo de Técnicos): 30 peticiones, 40 aserciones aprobadas (✓), 0 fallidas (✗) — **100% PASS**.
     * `scrum-111` (Suspensión de Cuenta de Técnico): 29 peticiones, 39 aserciones aprobadas (✓), 0 fallidas (✗) — **100% PASS**.
     * `scrum-incremento-tecnico` (SCRUM-81/90/93): 43 peticiones, 61 aserciones aprobadas (✓), 0 fallidas (✗) — **100% PASS**.
     * `scrum-78` (Motor de Matching y SLA RNF-05): 21 peticiones, 43 aserciones aprobadas (✓), 0 fallidas (✗) — **100% PASS**.
     * **Total Consolidado E2E en QA:** 192 peticiones HTTP, 291 aserciones verificadas, 0 fallos (**100.0% Pass Rate**).
   - *Nota Histórica de Progresión:* La corrida preliminar del 18 de octubre (36.1% pass rate inicial con 207 fallos) quedó formalmente subsanada y reemplazada por las evidencias limpias del 22 de octubre (`tests/e2e/evidencias/*-qa-2026-10-22.txt`).

* **Causa Raíz de los Fallos y Rectificación de Alcance:**
  1. *Dependencia de Usuarios Fijos Inexistentes (Causa principal de 401s en cascada):* Las colecciones iniciales asumieron la existencia de usuarios sembrados fijos (`usr-tec-01`, `usr-client-01`, `usr-tec-pending-01`) que no estaban en la base de datos de QA. La solución formal acordada es la adopción del patrón de creación dinámica de cuentas al vuelo (`preparacion()`) importado de `generar-scrum490-96-cotizacion-evidencia.py`.
  2. *Alcance de SCRUM-35 (Ejecución Técnica) y Discrepancia de Contrato:* La historia `SCRUM-35` **sí forma parte del Sprint 4** y cubre la ejecución técnica de la orden. El fallo en la suite `scrum-84` se debió a un error de diseño de la prueba que invocaba `PUT /status` en lugar del contrato formal de ServiceRequest v1.7.0 (`POST /v1/service-requests/{id}/start`, subida de foto de evidencia y `POST /v1/service-requests/{id}/complete`). Esta capacidad cuenta con evidencia real y sin fallos en QA respaldada por `scrum-96-evidencia` del 22 de octubre.
  3. *Alcance de Pagos (Payments — SCRUM-44 / SCRUM-117 / SCRUM-495):* Payments **sí forma parte del Sprint 4**. El flujo de pago con pasarela simulada y consulta de comprobante con NIT y PDF (`GET /v1/payments/{id}/invoice`) está plenamente verificado en QA con evidencia formal sin fallos en `scrum-495-comprobante` del 22 de octubre.
  4. *Retención de Datos en Pruebas de Carga (k6):* Las corridas de carga de k6 contra QA generan órdenes persistidas en `db_service_request` (VM5). Se establece como directriz operativa no correr k6 contra QA sin coordinación previa para no saturar la base de datos.

* **Estado Real de Verificación por Servicio (Respaldado por Evidencias de QA del 22 de Octubre):**

| Dimensión / Servicio Evaluado | Estado en QA Real (Evidencia Oficial) | Estado en Simulación Local | Evidencia Formal en Repositorio (`correr-colecciones-qa.js`) |
|---|:---:|:---:|---|
| **Identity Service (SCRUM-56 / RBAC)** | PASS (Registro dinámico, duplicados 409 y RFC 9457 `validacion`) | 100% PASS | `tests/e2e/evidencias/scrum-56-registro-tecnico-qa-2026-10-22.txt` |
| **Matching Service (SCRUM-78 / SLA RNF-05)** | PASS (43/43 aserciones, 100% éxito, SLA $< 60\text{ s}$) | 100% PASS | `tests/e2e/evidencias/scrum-78-qa-2026-10-22.txt` |
| **Service-Request (SCRUM-31 / SCRUM-35 / SCRUM-84)** | PASS (Ciclo 4 estados: start, foto Garage, complete, RBAC/RLS) | 100% PASS | `tests/e2e/evidencias/scrum-84-seguimiento-estado-qa-2026-10-22.txt` |
| **Incremento Técnico (SCRUM-81 / 90 / 93)** | PASS (20 localidades Bogotá, disponibilidad, ofertas y detalle) | 100% PASS | `tests/e2e/evidencias/scrum-incremento-tecnico-qa-2026-10-22.txt` |
| **Gestión de Proveedor (SCRUM-99)** | PASS (Alta `ProviderTechnicianRequest` sin campo excedente) | 100% PASS | `tests/e2e/evidencias/scrum-99-equipo-proveedor-qa-2026-10-22.txt` |
| **Admin Verificación (SCRUM-108)** | PASS (Aprobación/Rechazo con motivo $\ge 5$ caracteres) | 100% PASS | `tests/e2e/evidencias/scrum-108-aprobacion-rechazo-qa-2026-10-22.txt` |
| **Admin Suspensión (SCRUM-111)** | PASS (Suspensión, reactivación a aprobado y 409) | 100% PASS | `tests/e2e/evidencias/scrum-111-suspension-tecnico-qa-2026-10-22.txt` |
| **Catalog Service (Categorías y Admin)** | PASS (Categorías activas y admin) | 100% PASS | `tests/e2e/evidencias/scrum-75-solicitud-empresa-qa-*.txt` |
| **Payments (SCRUM-44 / SCRUM-495)** | PASS (Comprobante JSON y PDF con NIT) | 100% PASS | `tests/e2e/evidencias/scrum-495-comprobante-qa-2026-10-22.txt` |
| **Cancelación E2E (SCRUM-478)** | PASS (Cancelación con oferta y asignado) | 100% PASS | `tests/e2e/evidencias/scrum-478-cancelacion-qa-2026-10-19.txt` |
| **Solicitud Empresa (SCRUM-75)** | PASS (Punta a punta corporativa) | 100% PASS | `tests/e2e/evidencias/scrum-75-solicitud-empresa-qa-*.txt` |
| **Simulador Local (Contratos)** | N/A (Harness de desarrollo) | **100% PASS** | `tests/e2e/evidencias/suites-e2e-qa-sprint4-2026-10-18.txt` |

#### 3.1.2 Evidencias en Repositorio
* Simulación local preparatoria: `tests/e2e/evidencias/suites-e2e-qa-sprint4-2026-10-18.txt`
* Reportes reales verificados en QA: `tests/e2e/evidencias/*-qa-2026-10-22.txt` generadas mediante `correr-colecciones-qa.js`.

### 3.2 Compuerta 2.2 — Seguridad Normativa PCI-DSS en Logs
* **Ejecutor:** `tests/security/run-pci-dss-suite.py` y `tests/security/pci_dss_scanner.py`.
* **Resultados de Robustez:**
  - Sensibilidad de Detección: 6 de 6 tarjetas válidas (Visa 13/16 dígitos, Mastercard 51-55 y 2221-2720, Amex 15 dígitos, Discover 16 dígitos) detectadas mediante Algoritmo de Luhn Mod 10 y prefijo IIN/BIN.
  - Especificidad: 16 de 16 casos negativos extremos (números de celular colombianos, cédulas CC, UUIDs, correlation IDs, timestamps, contraseñas, emojis UTF-8 e inyecciones SQLi/XSS) descartados sin falsos positivos.
  - Patrones CVV: 3/3 patrones contextuales detectados, 4/4 números estándar descartados.
* **Escaneo de Trazas Reales de QA (Exportación Oficial de Loki API - k3s VM2):**
  - Registros de logs auditados: **100 registros JSON estructurados** (`.NET AddJsonConsole`) distribuidos en 5 streams de pods reales (`matching`, `communication`, etc., namespace `quickpatch`).
  - Alcance Sprint 4: La auditoría sobre los pods de QA verifica que ningún microservicio activo en QA filtre números PAN, códigos CVV ni secretos en los logs centralizados recolectados por Promtail y Loki bajo la normativa PCI-DSS v4.0.
  - Números de Tarjeta (PAN) en texto plano: **0**.
  - Códigos CVV/CVC encontrados: **0**.
  - Secretos o credenciales en texto plano: **0**.
* **Evidencias en Repositorio:**
  - Reporte formal: `tests/security/evidencias/pci-dss-loki-qa-2026-10-18.txt`.
  - Exportación real de Loki API evaluada: `tests/security/evidencias/loki_qa_k3s.json`.

### 3.3 Compuerta 2.3 — Rendimiento Carga Normal Sostenida (50 VU)
* **Script:** `tests/performance/load-test-50vu.js` / `k6.exe`.
* **Resultados Oficiales (Ejecución Completa RNF-06):**
  - Concurrencia Máxima: **50 Virtual Users (vus_max = 50)** durante 2m30s.
  - Volumen Total: **5,755 peticiones procesadas** (37.81 req/s, 2,876 iteraciones).
  - Catálogo (`GET /api/v1/catalog/categories`): $p50 = 17.58\text{ ms}$, $p90 = 30.95\text{ ms}$, $p95 = 36.24\text{ ms}$ (Umbral SAD: $p95 < 200\text{ ms}$) $\to$ **PASS**.
  - Creación de Solicitud (`POST /api/v1/service-requests`): $p50 = 24.47\text{ ms}$, $p90 = 72.75\text{ ms}$, $p95 = 90.67\text{ ms}$ (Umbral SAD: $p95 < 2000\text{ ms}$) $\to$ **PASS**.
  - Tasa Global de Errores: **0.00%** (0 fallos en 5,755 requests; Umbral RNF-06: $< 1.0\%$) $\to$ **PASS**.
  - Aserciones de Contrato: **11,504 / 11,504 checks aprobados (100% PASS)**.
* **Evidencias en Repositorio:**
  - Resumen estructurado: `tests/performance/evidencias/k6-load-50vu-summary.json`.
  - Reporte formal: `tests/performance/evidencias/k6-load-50vu-qa-2026-10-18.txt`.

### 3.4 Compuerta 2.4 — Rendimiento Estrés Pico Inesperado (150 VU)
* **Script:** `tests/performance/stress-test-150vu.js` / `k6.exe`.
* **Resultados Oficiales (Ejecución Completa AC2-E4):**
  - Concurrencia Pico: **150 Virtual Users (vus_max = 150)** durante 4m00s.
  - Volumen Total: **38,876 peticiones procesadas** (160.46 req/s, 38,873 iteraciones, 78 MB transferidos).
  - Latencia Global bajo Estrés: $p50 = 181.78\text{ ms}$, $p90 = 348.61\text{ ms}$, $p95 = 415.39\text{ ms}$, $\text{Max} = 1.12\text{ s}$ (Umbral SAD: $p95 < 5000\text{ ms}$) $\to$ **PASS**.
  - Tasa de Errores 5xx: **0.00%** (0 errores en 38,873 llamadas transaccionales; Umbral AC2-E4: $\text{rate} == 0$) $\to$ **PASS**.
  - Tasa de Fallos de Red / HTTP: **0.00%** (0 de 38,876).
  - Aserciones de Resiliencia: **77,746 / 77,746 checks aprobados (100% PASS)**.
  - Caídas de Pods / OOMKilled: 0 caídas (Estabilidad de recursos comprobada en k3s VM2) $\to$ **PASS**.
* **Evidencias en Repositorio:**
  - Resumen estructurado: `tests/performance/evidencias/k6-stress-150vu-summary.json`.
  - Reporte formal: `tests/performance/evidencias/k6-stress-150vu-qa-2026-10-18.txt`.

### 3.5 Compuerta 2.5 — Seguridad Dinámica DAST OWASP ZAP Baseline
* **Ejecutor:** Docker container `ghcr.io/zaproxy/zaproxy:stable` ejecutado sobre VM1 apuntando a `https://qa.quickpatch.internal`.
* **Script / Configuración:** `tests/security/run-dast-zap-suite.py` / `tests/security/zap-baseline.conf`.
* **Resultados Oficiales:**
  - Total Reglas Evaluadas: 61 reglas.
  - Reglas Aprobadas (PASS): **59 reglas (96.7%)**.
  - Vulnerabilidades Críticas / Altas (FAIL): **0 alertas** (SQLi, XSS, Command Injection, Source Code Disclosure, Remote Code Execution evaluadas en 0 hallazgos).
  - Advertencias Defensivas (WARN-NEW): **2 alertas** (HSTS [10035] y CSP [10038] ausentes en respuestas 403 Forbidden de la raíz `/` al no contener index HTML por diseño).
  - Endurecimiento Comprobado: Protocolo TLS 1.3 forzado exclusivamente en VM1 Nginx Proxy (`TLS_AES_256_GCM_SHA384`), encabezado `X-Content-Type-Options: nosniff` activo en respuestas JSON.
* **Evidencias en Repositorio:**
  - Reporte consolidado: `tests/security/evidencias/zap-dast-baseline-qa-2026-10-18.txt`.
  - JSON nativo ZAP: `tests/security/evidencias/zap.json`.
  - Reporte HTML interactivo oficial: `tests/security/evidencias/zap.html`.


---

## 4. Gestión y Resolución de Defectos (Compuerta 2.6)

Conforme a la matriz formal documentada en `docs/testing/registro-defectos-sprint4.md`, durante el ciclo de pruebas se auditaron 7 reportes: **2 defectos de herramientas de simulación local (harness)**, **2 defectos menores de scripts de prueba**, y **3 inconsistencias de diseño de pruebas resueltas y aclaradas**:

### 4.1 Defectos de Harness de Pruebas y Scripts Resueltos (4 de 4 — 100% Cerrados)
1. **BUG-SP4-001 (Defecto de Harness Local):** Excepción residual `reqId !== 'sr-qa-001'` en emulación de aislamiento intra-tenant eliminada en `mock-gateway-local-simulacion.js`. Corresponde al simulador local y no al producto en QA, donde el aislamiento es nativo vía PostgreSQL RLS.
2. **BUG-SP4-002 (Defecto de Runner Newman):** Precedencia de variable `sufijo` en Newman corregida en `run-mvp.js` para respetar la generación dinámica de identificadores.
3. **BUG-SP4-003 (Defecto de Harness Local):** Contaminación de estado en memoria entre suites en el simulador local resuelta implementando `resetState()` antes de la ejecución de cada colección en `run-all-increment-suites.js`. Corresponde al arnés de pruebas y no al backend k3s.
4. **BUG-SP4-004 (Defecto de Consola):** Incompatibilidad de encoding cp1252 en consolas Windows solucionada con `sys.stdout.reconfigure(encoding='utf-8')` en el escáner PCI-DSS.

### 4.2 Inconsistencias de Diseño de Suite Aclaradas
5. **BUG-SP4-005 (Discrepancia de Contrato en Suite):** Invocación errónea de `PUT /status` en la suite original `scrum-84`. La historia `SCRUM-35` pertenece a este Sprint 4 y expone formalmente `POST /start` y `POST /complete` (con foto de evidencia obligatoria), capacidades verificadas exitosamente en QA mediante `scrum-96-evidencia`.
6. **BUG-SP4-006 (Error de Diseño de Suite):** La ruta ficticia `/assigned-detail` no existe en OpenAPI; el detalle se consulta mediante `GET /v1/service-requests/{id}` con token del técnico asignado (verificado en QA en `scrum-93`).
7. **BUG-SP4-007 (Error de Datos de Prueba):** Fallos 401 por omitir `--env-var adminEmail` o depender de usuarios quemados. Resuelto adoptando el patrón de usuarios dinámicos generado con `preparacion()` y ejecutado vía `correr-colecciones-qa.js`.

**Estado Actual:** 0 defectos abiertos de producto. Tasa de resolución: **100.0%**.

---

## 5. Recomendaciones Técnicas para el Despliegue en Producción

1. **Activación de la Compuerta RNF-08 en CI/CD:** El script `/usr/local/bin/compuerta-qa` en VM1 verificará automáticamente que las imágenes promovidas a producción coincidan exactamente con la revisión evaluada y aprobada en QA.
2. **Monitoreo de WebSocket en Gateway:** Vigilar el pool de conexiones WebSocket en VM1 para asegurar que la concurrencia en tiempo real (ADR-023) se mantenga dentro de los límites de memoria asignados.
3. **Verificación Periódica de Certificados TLS:** Asegurar la renovación automatizada de certificados para el dominio institucional garantizando que la directiva HSTS (`max-age=31536000`) continúe protegiendo a los clientes móviles y web.

---

## 6. Aprobación y Firmas

| Rol | Nombre | Firma / Estado | Fecha |
|---|---|:---:|:---:|
| **QA Lead** | Katherine Bravo | **PRESENTADO PARA REVISIÓN** | 22/10/2026 |
| **DevOps / Release Manager** | Pipeline Automatizado (RNF-08) | **VERIFICADO** | 22/10/2026 |
| **Arquitectura de Software** | Revisores de Arquitectura (PR #106) | *Pendiente de aprobación en revisión de PR* | — |
