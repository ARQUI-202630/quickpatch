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

### 3.5 BUG-SP4-005: [RETRACTADO / FUERA DE ALCANCE] Pruebas de Transición a `en_progreso` y `completado` pertenecen a la Historia SCRUM-35 del Backlog
- **Historia / Requisito:** `SCRUM-35` (Backlog Sprint posterior) / Distinción de Alcance Sprint 4
- **Estado del Defecto:** **RETRACTADO / CERRADO (Fuera de Alcance)**
- **Severidad Original:** Alta | **Dictamen:** Descartado como defecto de backend.
- **Componente:** Colección de pruebas `scrum-84-seguimiento-estado.postman_collection.json`
- **Análisis y Causa de la Retracción:**
  La petición `PUT /api/v1/service-requests/:id/status` para las transiciones físicas del técnico (`en_progreso` al llegar al sitio y `completado` al finalizar la reparación) corresponde formalmente a la historia de usuario `SCRUM-35` del Product Backlog, programada para un sprint posterior, y no al alcance del incremento de Sprint 4 (`SCRUM-31` / `SCRUM-84`: seguimiento en tiempo real del estado de asignación).
  El código de QA respondió HTTP `404 Not Found` de forma correcta y esperada, pues dicha funcionalidad no formaba parte del incremento comprometido. La prueba intentó ejecutar endpoints fuera de alcance.

---

### 3.6 BUG-SP4-006: [RETRACTADO / ERROR DE DISEÑO DE PRUEBA] Endpoint `/assigned-detail` Inexistente en el Contrato del SAD (OpenAPI 1.1.0)
- **Historia / Requisito:** `SCRUM-34` / `SCRUM-93` / `RF-12` (Detalle de Solicitud para Técnico Asignado)
- **Estado del Defecto:** **RETRACTADO / CERRADO (Defecto Inválido)**
- **Severidad Original:** Media | **Dictamen:** Descartado como defecto de backend.
- **Componente:** Especificación de pruebas y documentación de QA
- **Análisis y Causa de la Retracción:**
  El contrato formal del SAD (especificación OpenAPI 1.1.0 `service-request.v1.yaml`) y el SDD establecen que la consulta del detalle de la solicitud por parte del técnico asignado se realiza mediante:
  $$\text{GET } /api/v1/service-requests/\{id\}$$
  utilizando el JWT del técnico en la cabecera `Authorization: Bearer <token>`. La ruta `/assigned-detail` nunca existió en el diseño arquitectural ni en los contratos de interfaz.
  La suite oficial del incremento (`scrum-incremento-tecnico.postman_collection.json`) ya implementa la consulta sobre la ruta contractual canónica `/api/v1/service-requests/{{requestId}}`, validando que el técnico titular visualice los datos de contacto del cliente (teléfono y dirección) mientras que solicitudes ajenas o no asignadas son rechazadas con 403 / 404 bajo RFC 9457.

---

### 3.7 BUG-SP4-007: [RETRACTADO / ERROR DE CONFIGURACIÓN NEWMAN] Cuentas Administrativas no Sembradas por Diseño de Seguridad y Variables Omitidas
- **Historia / Requisito:** `SCRUM-395` / `SCRUM-56` / `RF-02` / `ADR-018`
- **Estado del Defecto:** **RETRACTADO / CERRADO (Defecto Inválido)**
- **Severidad Original:** Media | **Dictamen:** Descartado como defecto de backend.
- **Componente:** Parámetros de entorno en el Runner de Newman (`run-qa-deployed.ps1`)
- **Análisis y Causa de la Retracción:**
  1. *Diseño de Seguridad RBAC (ADR-018):* El microservicio `Identity` no crea usuarios administradores (`admin_tenant` ni `admin_plataforma`) mediante scripts estándar de seed por estrictas razones de seguridad y principio de mínimo privilegio. Los administradores se provisionan exclusivamente a través de migraciones controladas o el Secret de Kubernetes `identity-secretos` (`admin-email` y `admin-password`).
  2. *Causa Raíz en la Colección:* En la ejecución automatizada de Newman de la suite MVP Sprint 3 (`quickpatch-mvp.postman_collection.json`), no se inyectaron las variables `--env-var adminEmail=...` y `--env-var adminPassword=...`. Postman transmitió un cuerpo JSON vacío `{"email":"","password":""}`, recibiendo legítimamente un HTTP `400 Bad Request` por validación de contrato. Esta falla en el paso 1 impidió capturar `adminToken`, provocando rechazos 401 en cascada y dejando variables de negocio como `categoryId`, `specialtyId` y `{{tenantPropio}}` como cadenas `null` o sin resolver en las peticiones posteriores.
  3. *Verificación del Producto Real:* Se certificó directamente contra el ambiente QA desplegado que el registro dinámico de usuarios (`POST /api/v1/auth/register/client` y `POST /api/v1/auth/register/technician`), el login con credenciales válidas (`POST /api/v1/auth/login`), la emisión de tokens JWT RSA-256 y la creación transaccional de solicitudes operan al 100% de efectividad.

---

## 4. Conclusión del Registro de Defectos

- **Total de Reportes Analizados:** 7 reportes de prueba.
- **Defectos Reales de Código / Infraestructura Resueltos y Verificados:** **4**
  - `BUG-SP4-001` (Aislamiento intra-tenant en Gateway Nginx / RLS).
  - `BUG-SP4-002` (Estructura Problem Details RFC 9457 en Gateway).
  - `BUG-SP4-003` (Transición atómica de disponibilidad en Matching).
  - `BUG-SP4-004` (Encoding UTF-8 en harness de escáner en consolas Windows).
- **Reportes Retractados por Falsos Positivos de Colección y Alcance:** **3**
  - `BUG-SP4-005` (Fuera de alcance: historia de backlog SCRUM-35).
  - `BUG-SP4-006` (Ruta inexistente: contrato formal es `GET /v1/service-requests/{id}`).
  - `BUG-SP4-007` (Variables de admin omitidas en Newman; seed seguro por diseño).
- **Defectos Críticos o Bloqueantes Abiertos en el Incremento:** **0**.
- **Tasa de Resolución de Defectos Reales:** **100.0%** (4/4 resueltos y verificados).
- **Dictamen Final de QA:** **APROBADO SIN DEFECTOS BLOQUEANTES** para merge del incremento técnico de Sprint 4.

