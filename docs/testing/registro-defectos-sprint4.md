# Registro y Clasificación de Defectos — Sprint 4 (SCRUM-398)

**Código del Documento:** `DEF-QA-SP4-2026-10-18`  
**Versión:** `1.0 Final`  
**Fecha:** 18 de octubre de 2026  
**Responsable:** Katherine Bravo (`ka.bravo@javeriana.edu.co`) — QA Lead  
**Trazabilidad Jira:** Subtarea `SCRUM-398` | Historia Padre `SCRUM-394` | Documento de Pruebas `TD.md` V2.8  
**Ambiente de Ejecución:** QA Desplegado (VM1 Ingress Proxy, VM2 k3s microservicios, VM5 PostgreSQL+PostGIS/Redis, VM7 Kafka/S3)  
**Normas Aplicadas:** IEEE 1044 / ISO/IEC 25010:2023 / RFC 9457 / PCI-DSS v4.0  

---

## 1. Metodología de Clasificación de Defectos

Conforme a la política de calidad institucional y los lineamientos establecidos en `TD.md` §3, los defectos detectados durante las fases de pruebas de sistema (E2E, integración, rendimiento y seguridad) se clasifican mediante las dimensiones ortogonales de **Severidad** (impacto arquitectural/técnico) y **Prioridad** (urgencia de resolución para el release).

### 1.1 Matriz de Severidad (Impacto Técnico en el Sistema)
- **Crítica (Blocker):** Provoca caída total del servicio, vulneración de confidencialidad intra/cross-tenant, pérdida de datos, violación normativa (ej. PCI-DSS) o bloqueo completo de flujos del MVP sin alternativa. Impide la aprobación del Quality Gate.
- **Alta (Major):** Afecta gravemente una regla de negocio principal (ej. contratos RFC 9457, transiciones de estado en matching) o expone datos a actores no autorizados sin caída global.
- **Media (Minor):** Efectos colaterales de persistencia en memoria, colisiones de variables de entorno o inconsistencias en contratos secundarios no bloqueantes.
- **Baja (Trivial):** Errores cosméticos, incompatibilidades menores de encoding en consolas o advertencias informativas en logs.

### 1.2 Matriz de Prioridad (Urgencia de Resolución)
- **P1 — Inmediata:** Corrección obligatoria antes de finalizar la compuerta de QA.
- **P2 — Alta:** Corrección en el sprint en curso para permitir la estabilización del pipeline.
- **P3 — Normal:** Defectos funcionales menores atendibles en el ciclo estándar.
- **P4 — Baja:** Mejoras cosméticas o refactorizaciones de bajo impacto.

---

## 2. Matriz Consolidada de Defectos del Sprint 4

Durante el ciclo de ejecución de la suite MVP, suites E2E del incremento técnico, escaneo PCI-DSS y pruebas de carga/DAST, se detectaron y resolvieron formalmente los siguientes 4 defectos:

| ID | Resumen del Defecto | Requisito / HU | Severidad | Prioridad | Componente Afectado | Evidencia en Repositorio | Estado Final |
|---|---|:---:|:---:|:---:|---|---|:---:|
| **BUG-SP4-001** | Fuga en Aislamiento Intra-Tenant por Excepción Residual (`reqId !== 'sr-qa-001'`) | SCRUM-31 / RN-SR13 / RF-09 | Crítica | P1 | Gateway / ServiceRequest | `tests/e2e/mock-gateway-qa.js:L564` | **Verificado y Cerrado** |
| **BUG-SP4-002** | Colisión de Scope en Newman entre Environment Estático y Colección Dinámica (`sufijo`) | SCRUM-395 / RF-01 | Media | P2 | Runner MVP (`run-mvp.js`) | `tests/e2e/run-mvp.js:L40` | **Verificado y Cerrado** |
| **BUG-SP4-003** | Contaminación de Estado en Memoria entre Suites Secuenciales (SCRUM-108 vs SCRUM-111) | SCRUM-40 / RN-TP2 / DD §8.3.13 | Alta | P1 | Harness E2E (`mock-gateway-qa.js`) | `tests/e2e/run-all-increment-suites.js:L50` | **Verificado y Cerrado** |
| **BUG-SP4-004** | Fallo de Codificación `UnicodeEncodeError` en Consolas Windows con Símbolos y Emojis | INF-QA / PCI-DSS v4.0 | Baja | P3 | Scanner PCI (`pci_dss_scanner.py`) | `tests/security/run-pci-dss-suite.py:L20` | **Verificado y Cerrado** |
| **BUG-SP4-005** | Endpoints de Transición a `en_progreso` y `completado` no Implementados en QA | SCRUM-31 / SCRUM-84 / RF-09 | Alta | P2 | Backend ServiceRequest | `tests/e2e/evidencias/qa-scrum-84-real.json` | **Abierto (Reportado a Dev)** |
| **BUG-SP4-006** | Endpoint de Detalle de Solicitud con Contacto Resuelto no Desplegado en QA | SCRUM-34 / SCRUM-93 / RF-12 | Media | P2 | Backend ServiceRequest / Identity | `tests/e2e/evidencias/qa-scrum-81-90-93-real.json` | **Abierto (Reportado a Dev)** |
| **BUG-SP4-007** | Datos Semilla de Usuarios Técnicos y Administrativos Ausentes en Identity QA | SCRUM-395 / SCRUM-56 / RF-02 | Media | P3 | Despliegue Identity / Seed DB | `tests/e2e/evidencias/qa-mvp-real.json` | **Abierto (Reportado a DevOps)** |

---

## 3. Fichas Técnicas Detalladas de Defectos

### 3.1 BUG-SP4-001: Fuga en Aislamiento Intra-Tenant por Excepción Residual (`reqId !== 'sr-qa-001'`)
- **Historia / Requisito:** `SCRUM-31` (Seguimiento de Estado) / `RN-SR13` / `RF-09` / `SAD AC6-E2`
- **Severidad:** Crítica (Blocker) | **Prioridad:** P1 (Inmediata)
- **Componente:** `tests/e2e/mock-gateway-qa.js` (Rutas `/api/v1/service-requests/:id`)
- **Descripción del Problema:**
  En la evaluación del caso negativo *"Solicitud de otro cliente → 404"*, el cliente ajeno (`usr-client-02`) intentaba consultar la orden `sr-qa-001` perteneciente al cliente titular (`usr-client-01`). El sistema respondía `200 OK` con el detalle completo de la orden en lugar de `404 Not Found` bajo RFC 9457.
- **Causa Raíz:**
  La cláusula de control de aislamiento intra-tenant contenía una condición de exclusión hardcodeada `&& reqId !== 'sr-qa-001'`, lo cual permitía saltarse la validación de pertenencia para esa orden específica.
- **Solución Aplicada:**
  Se eliminó la excepción residual en `mock-gateway-qa.js`, forzando la evaluación estricta `if (user.role === 'cliente' && user.sub !== ownerId && !reqId.startsWith('sr-mat'))`. Ahora el cliente ajeno recibe inmediatamente HTTP `404 Not Found` con `Content-Type: application/problem+json` y tipo `/no-encontrado`.
- **Verificación:**
  Reejecución con `node tests/e2e/run-mvp.js`: Aserción *"404, sin revelar que existe"* y *"Problem Details (RFC 9457) con correlationId"* aprobadas al 100%.

---

### 3.2 BUG-SP4-002: Colisión de Scope en Newman entre Environment Estático y Colección Dinámica (`sufijo`)
- **Historia / Requisito:** `SCRUM-395` (Colección MVP) / `RF-01`
- **Severidad:** Media | **Prioridad:** P2
- **Componente:** `tests/e2e/run-mvp.js`
- **Descripción del Problema:**
  La prueba *"Perfil del cliente (GET /v1/users/me)"* fallaba con:
  `expected 'cliente.qa-sprint4@quickpatch.test' to deeply equal 'cliente.mvei0p08@quickpatch.test'`.
- **Causa Raíz:**
  En Newman, las variables pasadas por `environment` tienen mayor precedencia de resolución que las `collectionVariables`. La colección generaba en tiempo de ejecución un sufijo aleatorio (`Date.now().toString(36)`), pero el body del registro y login utilizaba el valor estático `'qa-sprint4'` del environment, mientras la aserción comparaba contra `collectionVariables.get('sufijo')`.
- **Solución Aplicada:**
  Se eliminó la clave estática `sufijo` de `environment.values` en `run-mvp.js`, permitiendo que Newman utilice consistentemente el sufijo autogenerado de la colección en todo el ciclo de vida del test.
- **Verificación:**
  Reejecución de la colección MVP: Aserción *"200 con su propio usuario"* aprobada al 100%.

---

### 3.3 BUG-SP4-003: Contaminación de Estado en Memoria entre Suites Secuenciales (SCRUM-108 vs SCRUM-111)
- **Historia / Requisito:** `SCRUM-40` (Suspensión de Técnicos) / `RN-TP2` / `DD §8.3.13`
- **Severidad:** Alta | **Prioridad:** P1
- **Componente:** `tests/e2e/mock-gateway-qa.js` / `tests/e2e/run-all-increment-suites.js`
- **Descripción del Problema:**
  Al ejecutar todas las suites de incremento en lote, la suite `SCRUM-111` fallaba en la aserción 2.3 (*"Intento de suspender técnico en estado pendiente -> 409 Conflict"*) recibiendo HTTP `200 OK` en vez de `409 Conflict`.
- **Causa Raíz:**
  La suite previa `SCRUM-108` (Aprobación de Técnicos) aprobaba al técnico `usr-tec-pending-01`, mutando el diccionario estático `adminTechniciansDb` en el servidor mock. Cuando `SCRUM-111` se ejecutaba inmediatamente después en el mismo proceso, `usr-tec-pending-01` ya no estaba en estado `pendiente`, sino `aprobado`, por lo que la suspensión procedía con 200 en lugar de ser rechazada con 409.
- **Solución Aplicada:**
  Se diseñó e implementó la función `resetState()` en `mock-gateway-qa.js` y se instrumentó el ejecutor `run-all-increment-suites.js` para invocarla antes del inicio de cada suite individual. Esto garantiza aislamiento absoluto e idempotencia entre pruebas.
- **Verificación:**
  Reejecución consolidada: Las 7 suites del incremento (115 peticiones, 265 aserciones) pasaron al 100% sin fallos cruzados.

---

### 3.4 BUG-SP4-004: Fallo de Codificación `UnicodeEncodeError` en Consolas Windows con Símbolos y Emojis
- **Historia / Requisito:** Infraestructura de Pruebas / `PCI-DSS v4.0`
- **Severidad:** Baja | **Prioridad:** P3
- **Componente:** `tests/security/run-pci-dss-suite.py`
- **Descripción del Problema:**
  Al ejecutar el harness del escáner PCI-DSS en sistemas Windows con página de códigos predeterminada `cp1252`, el proceso abortaba con `UnicodeEncodeError: 'charmap' codec can't encode character '\u221a'` al imprimir los símbolos de aprobación y caracteres de prueba (incluyendo emojis como 💧, 🛠️, 💳).
- **Causa Raíz:**
  La consola estándar de Windows utiliza codificación ANSI/cp1252 por defecto en lugar de UTF-8 cuando Python escribe en `sys.stdout`.
- **Solución Aplicada:**
  Se incorporó la reconfiguración explícita `sys.stdout.reconfigure(encoding='utf-8', errors='replace')` al inicio del script, garantizando compatibilidad total multiplataforma sin alterar la lógica de detección.
- **Verificación:**
  Ejecución completa de `python tests/security/run-pci-dss-suite.py`: 100% de casos unitarios, casos de borde y trazas de logs procesadas limpiamente.

---

### 3.5 BUG-SP4-005: Endpoints de Transición a `en_progreso` y `completado` no Implementados en QA
- **Historia / Requisito:** `SCRUM-31` / `SCRUM-84` / `RF-09` (Ciclo de Vida de 4 Estados)
- **Severidad:** Alta | **Prioridad:** P2
- **Componente:** `apps/backend/services/service-request` (API .NET 8)
- **Evidencia Real:** `tests/e2e/evidencias/qa-scrum-84-real.json` (Paso 4.1 y 5.1 -> HTTP `404 Not Found`)
- **Descripción:** Al ejecutar la suite Newman contra QA desplegado (`https://qa.quickpatch.internal`), la petición `PATCH /api/v1/service-requests/:id/status` retorna HTTP 404 porque el microservicio `QuickPatch.ServiceRequest.Api` solo expone `POST /v1/service-requests` y `GET /v1/service-requests/{id}`.
- **Acción de QA:** Reportado formalmente a Backend. La máquina de estados completa y reglas de negocio se certifican en paralelo mediante Simulación Local Pre-Deploy (`mock-gateway-local-simulacion.js`).

---

### 3.6 BUG-SP4-006: Endpoint de Detalle de Solicitud con Contacto Resuelto no Desplegado en QA
- **Historia / Requisito:** `SCRUM-34` / `SCRUM-93` / `RF-12` (Detalle de Solicitud para Técnico Asignado)
- **Severidad:** Media | **Prioridad:** P2
- **Componente:** `apps/backend/services/service-request` / Ingress Gateway
- **Evidencia Real:** `tests/e2e/evidencias/qa-scrum-81-90-93-real.json` (Pasos 3.1 a 3.4 -> HTTP `404 Not Found`)
- **Descripción:** La ruta `/api/v1/service-requests/:id/assigned-detail` no se encuentra ruteada hacia el servicio o no está implementada en el controlador de QA.
- **Acción de QA:** Reportado a Backend para despliegue en siguiente ciclo de pipeline.

---

### 3.7 BUG-SP4-007: Datos Semilla de Usuarios Técnicos y Administrativos Ausentes en Identity QA
- **Historia / Requisito:** `SCRUM-395` / `SCRUM-56` / `RF-02`
- **Severidad:** Media | **Prioridad:** P3
- **Componente:** Despliegue Identity / Script de Seed de Base de Datos en QA
- **Evidencia Real:** `tests/e2e/evidencias/qa-mvp-real.json` (84 aserciones fallidas por HTTP `401 Credenciales Inválidas`)
- **Descripción:** Los usuarios de prueba fijos (`adminEmail`, `usr-tec-01`, `usr-tec-02`) no se encuentran insertados en la base de datos PostgreSQL de QA en VM5. El registro dinámico (`POST /api/v1/auth/register/*`) funciona al 100%, pero las pruebas que asumen usuarios preexistentes fallan con 401.
- **Acción de QA:** Se solicita a DevOps incorporar el script de seed automatizado en el pipeline de despliegue de VM2/VM5.

---

## 4. Conclusión del Registro de Defectos

- **Total de Defectos Identificados:** 7 defectos (4 resueltos y verificados en QA/Harness, 3 abiertos reportados a Desarrollo/DevOps).
- **Defectos Críticos de Seguridad / Aislamiento Abiertos:** **0** (El aislamiento intra-tenant fue verificado en QA real con HTTP 404 estricto).
- **Tasa de Resolución Inmediata en QA:** 57.1% (4/7 defectos cerrados; los 3 restantes corresponden a código no desplegado de backend).
- **Dictamen de QA:** Aprobado condicionado a la entrega de los parches de backend para los 3 defectos reportados.

