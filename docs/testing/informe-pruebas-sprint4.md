# Informe Consolidado de Pruebas — Sprint 4 (SCRUM-394 / SCRUM-398)

**Código del Documento:** `INF-QA-SP4-2026-10-18`  
**Versión:** `1.0 Final`  
**Fecha de Emisión:** 18 de octubre de 2026  
**Responsable:** Katherine Bravo (`ka.bravo@javeriana.edu.co`) — QA Lead  
**Trazabilidad Jira:** Historia Padre `SCRUM-394` | Subtareas `SCRUM-395`, `SCRUM-396`, `SCRUM-397`, `SCRUM-398`  
**Referencias Normativas:** SRS V5.0 / SAD V4 (v2.28) / DD V4 / TD V2.8 / ADR-015 / ADR-022 / RNF-08  
**Clasificación:** Entrega Formal de Aseguramiento de Calidad de Software (Quality Gate 2)  

---

## 1. Resumen Ejecutivo y Decisión de la Compuerta de Calidad

El presente informe consolida los resultados del ciclo integral de verificación y validación (V&V) ejecutado durante el **Sprint 4** sobre la plataforma **QUICKPATCH**. Se evaluaron en profundidad las capacidades funcionales del incremento técnico desplegado en el ambiente de QA (topología de 7 máquinas virtuales definida en ADR-022), abarcando el flujo operativo completo del técnico (disponibilidad en 20 localidades, aceptación atómica de ofertas y detalle de órdenes), seguimiento de estados en tiempo real vía WebSocket, gestión de equipos de proveedores, aprobación, rechazo y suspensión administrativa de técnicos, y las pruebas no funcionales de rendimiento (k6 50 y 150 VU), seguridad normativa (PCI-DSS v4.0 en logs centralizados) y escaneo dinámico de vulnerabilidades (DAST OWASP ZAP Baseline).

Todas las pruebas se ejecutaron conforme a la estrategia de compuertas establecida en `TD.md` §3 y las especificaciones verificables de SRS V5 §5.5, alcanzando una tasa de éxito consolidada del **100.0%** en todas las compuertas aplicables, con **0 defectos críticos ni bloqueantes abiertos**.

### 1.1 Dictamen de la Compuerta de Calidad (Release Gate Decision)

> ### **ESTADO DEL RELEASE: GO (APROBADO PARA PRODUCCIÓN)**
> 
> **Veredicto:** El incremento de software de Sprint 4 **CUMPLE SATISFACTORIAMENTE AL 100%** con todos los criterios de aceptación y compuertas de calidad de QA (Compuertas 2.1 a 2.6). Se autoriza formalmente el paso a Producción bajo el mecanismo de compuerta automatizada `compuerta-qa.sh` (RNF-08).
> 
> **Resumen de Métricas Clave:**
> * **Pruebas Funcionales E2E (API):** 158 peticiones ejecutadas, 326 aserciones evaluadas, **0 fallos** (100% PASS).
> * **Seguridad PCI-DSS en Logs:** 0 números de tarjeta (PAN) en claro, 0 códigos CVV/CVC detectados.
> * **Rendimiento k6 (Carga 50 VU):** Catálogo $p95 = 60\text{ ms} < 200\text{ ms}$, Creación $p95 = 114\text{ ms} < 2.0\text{ s}$, Error rate $= 0.00\% < 1.0\%$.
> * **Rendimiento k6 (Estrés 150 VU):** Latencia $p95 = 540\text{ ms} < 5.0\text{ s}$, Errores 5xx $= 0.00\%$, 0 pods caídos (0 OOMKilled).
> * **Seguridad Dinámica DAST (OWASP ZAP):** 0 alertas Críticas / Altas (SQLi, XSS, RCE, Traversal).
> * **Gestión de Defectos:** 4 de 4 defectos identificados durante el sprint fueron **resueltos y verificados**.

### 1.2 Cuadro de Mando de Compuertas de Calidad (Quality Gates)

| Compuerta de Calidad | Métrica Evaluada | Criterio de Aceptación | Resultado Obtenido en QA | Estado |
|---|---|---|---|:---:|
| **Compuerta 2.1: Funcional y E2E API** | Colección MVP y 7 Suites del Incremento | 100% aserciones aprobadas (0 fallos) | 158 peticiones, 326 aserciones aprobadas (0 fallos) | ✅ Aprobada |
| **Compuerta 2.2: Seguridad PCI-DSS** | Escáner de logs en Loki / trazas | Cero exposición de PAN o CVV (PAY-002) | 0 PANs y 0 CVVs detectados (Tokenización Wompi conforme) | ✅ Aprobada |
| **Compuerta 2.3: Rendimiento Carga 50 VU** | Latencia p95 y Tasa de Fallos | Catálogo $< 200\text{ms}$, Orden $< 2\text{s}$, Fallos $< 1\%$ | Catálogo: $60\text{ms}$, Orden: $114\text{ms}$, Fallos: $0.00\%$ | ✅ Aprobada |
| **Compuerta 2.4: Rendimiento Estrés 150 VU** | Estabilidad de Pods y Errores 5xx | Latencia $< 5\text{s}$, Errores 5xx $= 0\%$, 0 caídas | Latencia: $540\text{ms}$, Errores 5xx: $0.00\%$, 0 OOMKilled | ✅ Aprobada |
| **Compuerta 2.5: Seguridad DAST (OWASP)** | Escaneo ZAP Baseline (INF-013) | 0 alertas Críticas / Altas (FAIL) | 0 alertas Críticas / Altas; TLS 1.3 y HSTS activos | ✅ Aprobada |
| **Compuerta 2.6: Calidad de Defectos** | Defectos bloqueantes o críticos | 0 defectos blocker/critical abiertos | 0 defectos abiertos (4 de 4 resueltos y verificados) | ✅ Aprobada |

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
* **Ejecutores:** `tests/e2e/run-mvp.js` y `tests/e2e/run-all-increment-suites.js`.
* **Ambiente:** QA Desplegado a través de `https://qa.quickpatch.internal`.
* **Resumen Consolidado de Suites:**
  - **Colección MVP:** 43 peticiones, 61 aserciones, 0 fallos (**100% PASS**).
  - **SCRUM-81/90/93 (Flujo Operativo Técnico):** 24 peticiones, 63 aserciones (**100% PASS**).
  - **SCRUM-56 (Registro y Perfil Técnico):** 9 peticiones, 24 aserciones (**100% PASS**).
  - **SCRUM-84 (Seguimiento Realtime):** 18 peticiones, 47 aserciones (**100% PASS**).
  - **SCRUM-99 (Gestión Equipo Proveedor):** 17 peticiones, 34 aserciones (**100% PASS**).
  - **SCRUM-108 (Aprobación/Rechazo de Técnicos):** 17 peticiones, 32 aserciones (**100% PASS**).
  - **SCRUM-111 (Suspensión de Técnicos):** 15 peticiones, 30 aserciones (**100% PASS**).
  - **SCRUM-78 (Motor de Matching y Asignación):** 15 peticiones, 35 aserciones (**100% PASS**).
* **Total Global:** 158 peticiones HTTP, 326 aserciones evaluadas, **0 fallos**. Pass Rate: **100.0%**.
* **Evidencias en Repositorio:**
  - `tests/e2e/evidencias/mvp-qa-sprint4-2026-10-18.txt`
  - `tests/e2e/evidencias/suites-e2e-qa-sprint4-2026-10-18.txt`

### 3.2 Compuerta 2.2 — Seguridad Normativa PCI-DSS en Logs
* **Ejecutor:** `tests/security/run-pci-dss-suite.py` y `tests/security/pci_dss_scanner.py`.
* **Resultados de Robustez:**
  - Sensibilidad de Detección: 6 de 6 tarjetas válidas (Visa 13/16 dígitos, Mastercard 51-55 y 2221-2720, Amex 15 dígitos, Discover 16 dígitos) detectadas mediante Algoritmo de Luhn Mod 10 y prefijo IIN/BIN.
  - Especificidad: 16 de 16 casos negativos extremos (números de celular colombianos, cédulas CC, UUIDs, correlation IDs, timestamps, contraseñas, emojis UTF-8 e inyecciones SQLi/XSS) descartados sin falsos positivos.
  - Patrones CVV: 3/3 patrones contextuales detectados, 4/4 números estándar descartados.
* **Escaneo de Trazas de QA (Loki / VM2):**
  - Registros de logs auditados: 20 bloques completos de transacciones de microservicios.
  - Números de Tarjeta (PAN) en texto plano: **0**.
  - Códigos CVV/CVC encontrados: **0**.
  - Conformidad con Wompi (ADR-014): Exclusivamente tokens seguros `tok_test_...` efímeros y no reversibles.
* **Evidencia en Repositorio:** `tests/security/evidencias/pci-dss-loki-qa-2026-10-18.txt`.

### 3.3 Compuerta 2.3 — Rendimiento Carga Normal Sostenida (50 VU)
* **Script:** `tests/performance/load-test-50vu.js` / `run-performance-suite.js`.
* **Resultados:**
  - Catálogo (`GET /api/v1/catalog/categories`): $p50 = 27\text{ ms}$, $p90 = 38\text{ ms}$, $p95 = 60\text{ ms}$, $p99 = 80\text{ ms}$ (Umbral SAD: $p95 < 200\text{ ms}$) $\to$ **PASS**.
  - Creación de Solicitud (`POST /api/v1/service-requests`): $p50 = 87\text{ ms}$, $p90 = 110\text{ ms}$, $p95 = 114\text{ ms}$, $p99 = 220\text{ ms}$ (Umbral SAD: $p95 < 2000\text{ ms}$) $\to$ **PASS**.
  - Tasa Global de Errores: $0.00\%$ (Umbral RNF-06: $< 1.0\%$) $\to$ **PASS**.
* **Evidencia en Repositorio:** `tests/performance/evidencias/k6-load-50vu-qa-2026-10-18.txt`.

### 3.4 Compuerta 2.4 — Rendimiento Estrés Pico Inesperado (150 VU)
* **Script:** `tests/performance/stress-test-150vu.js` / `run-performance-suite.js`.
* **Resultados:**
  - Latencia Global bajo Estrés: $p50 = 176\text{ ms}$, $p90 = 460\text{ ms}$, $p95 = 540\text{ ms}$, $p99 = 1123\text{ ms}$ (Umbral SAD: $p95 < 5000\text{ ms}$) $\to$ **PASS**.
  - Tasa de Errores 5xx: $0.00\%$ (0 errores) (Umbral AC2-E4: $\text{rate} == 0$) $\to$ **PASS**.
  - Caídas de Pods / OOMKilled: 0 caídas (Estabilidad de recursos comprobada en k3s VM2) $\to$ **PASS**.
  - PostgreSQL en VM5: 58 conexiones pico sin desbordamiento ni deadlocks.
* **Evidencia en Repositorio:** `tests/performance/evidencias/k6-stress-150vu-qa-2026-10-18.txt`.

### 3.5 Compuerta 2.5 — Seguridad Dinámica DAST OWASP ZAP Baseline
* **Configuración:** `tests/security/zap-baseline.conf` / `run-dast-zap-suite.py`.
* **Resultados:**
  - Vulnerabilidades de Severidad Alta / Crítica (FAIL): 0 alertas detectadas.
    * SQL Injection (40018): 0 alertas.
    * Cross Site Scripting XSS (40026): 0 alertas.
    * Remote OS Command Injection (90020): 0 alertas.
    * Server Side Code Injection (90019): 0 alertas.
    * Source Code Disclosure (10045): 0 alertas.
  - Endurecimiento Comprobado: Protocolo TLS 1.3 forzado exclusivamente en VM1 Nginx Proxy, HSTS configurado con `max-age=31536000`, encabezado `X-Content-Type-Options: nosniff` activo en todas las respuestas.
* **Evidencia en Repositorio:** `tests/security/evidencias/zap-dast-baseline-qa-2026-10-18.txt`.

---

## 4. Gestión y Resolución de Defectos (Compuerta 2.6)

Conforme a la matriz documentada en `docs/testing/registro-defectos-sprint4.md`, durante el ciclo de pruebas se identificaron, corrigieron y verificaron satisfactoriamente 4 defectos:

1. **BUG-SP4-001 (Crítica - P1):** Excepción residual `reqId !== 'sr-qa-001'` en aislamiento intra-tenant eliminada en `mock-gateway-qa.js`, restituyendo el código `404 Not Found` estricto bajo RFC 9457.
2. **BUG-SP4-002 (Media - P2):** Precedencia de variable `sufijo` en Newman corregida en `run-mvp.js` para respetar la generación dinámica de identificadores.
3. **BUG-SP4-003 (Alta - P1):** Contaminación de estado en memoria entre suites resuelta implementando `resetState()` antes de la ejecución de cada colección en `run-all-increment-suites.js`.
4. **BUG-SP4-004 (Baja - P3):** Incompatibilidad de encoding cp1252 en consolas Windows solucionada con `sys.stdout.reconfigure(encoding='utf-8')` en el escáner PCI-DSS.

**Estado Actual:** 0 defectos abiertos. Tasa de resolución: **100.0%**.

---

## 5. Recomendaciones Técnicas para el Despliegue en Producción

1. **Activación de la Compuerta RNF-08 en CI/CD:** El script `/usr/local/bin/compuerta-qa` en VM1 verificará automáticamente que las imágenes promovidas a producción coincidan exactamente con la revisión evaluada y aprobada en QA.
2. **Monitoreo de WebSocket en Gateway:** Vigilar el pool de conexiones WebSocket en VM1 para asegurar que la concurrencia en tiempo real (ADR-023) se mantenga dentro de los límites de memoria asignados.
3. **Verificación Periódica de Certificados TLS:** Asegurar la renovación automatizada de certificados para el dominio institucional garantizando que la directiva HSTS (`max-age=31536000`) continúe protegiendo a los clientes móviles y web.

---

## 6. Aprobación y Firmas

| Rol | Nombre | Firma / Estado | Fecha |
|---|---|:---:|:---:|
| **QA Lead** | Katherine Bravo | **APROBADO** | 18/10/2026 |
| **Arquitectura de Software** | Equipo de Arquitectura QUICKPATCH | **APROBADO** | 18/10/2026 |
| **DevOps / Release Manager** | Pipeline Automatizado (RNF-08) | **VERIFICADO** | 18/10/2026 |
