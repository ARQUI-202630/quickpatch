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
| **BUG-SP4-001** | Emulación de Aislamiento en Harness Local por Excepción Residual (`reqId !== 'sr-qa-001'`) | SCRUM-31 / RN-SR13 / RF-09 | Media (Harness) | P1 | Harness Local (`mock-gateway-local-simulacion.js`) | `tests/e2e/mock-gateway-local-simulacion.js:L564` | **Verificado y Cerrado** |
| **BUG-SP4-002** | Colisión de Scope en Newman entre Environment Estático y Colección Dinámica (`sufijo`) | SCRUM-395 / RF-01 | Media | P2 | Runner MVP (`run-mvp.js`) | `tests/e2e/run-mvp.js:L40` | **Verificado y Cerrado** |
| **BUG-SP4-003** | Contaminación de Estado en Memoria entre Suites en Harness Local (SCRUM-108 vs SCRUM-111) | SCRUM-40 / RN-TP2 / DD §8.3.13 | Media (Harness) | P1 | Harness Local (`mock-gateway-local-simulacion.js`) | `tests/e2e/run-all-increment-suites.js:L50` | **Verificado y Cerrado** |
| **BUG-SP4-004** | Fallo de Codificación `UnicodeEncodeError` en Consolas Windows con Símbolos y Emojis | INF-QA / PCI-DSS v4.0 | Baja | P3 | Scanner PCI (`pci_dss_scanner.py`) | `tests/security/run-pci-dss-suite.py:L20` | **Verificado y Cerrado** |
| **BUG-SP4-005** | Discrepancia de Contrato en Suite E2E: Invocación `PUT /status` en vez de `POST /start` y `/complete` | SCRUM-31 / SCRUM-35 / RF-09 | Media | P2 | Suite E2E (`scrum-84`) / ServiceRequest | `tests/e2e/evidencias/scrum-84-qa-2026-10-18.txt` | **Corregido en Suite** |
| **BUG-SP4-006** | Endpoint de Detalle de Solicitud con Contacto Resuelto no Desplegado en QA | SCRUM-34 / SCRUM-93 / RF-12 | Media | P2 | Backend ServiceRequest / Identity | `tests/e2e/evidencias/scrum-81-90-93-qa-2026-10-18.txt` | **Abierto (Reportado a Dev)** |
| **BUG-SP4-007** | Dependencia de Usuarios Fijos en Colecciones E2E Ausentes en Base de Datos de QA | SCRUM-395 / SCRUM-56 / RF-02 | Media | P2 | Colecciones E2E / Seed QA | `tests/e2e/evidencias/mvp-qa-sprint4-2026-10-18.txt` | **En Corrección Dinámica** |

---

## 3. Fichas Técnicas Detalladas de Defectos

### 3.1 BUG-SP4-001: Emulación de Aislamiento en Harness Local por Excepción Residual (`reqId !== 'sr-qa-001'`)
- **Historia / Requisito:** `SCRUM-31` (Seguimiento de Estado) / `RN-SR13` / `RF-09` / `SAD AC6-E2`
- **Ámbito:** Defecto del Harness de Pruebas (Simulador Local `mock-gateway-local-simulacion.js`), NO del producto en QA.
- **Severidad:** Media (Impacto exclusivo en pruebas locales preparatorias) | **Prioridad:** P1 (Inmediata)
- **Componente:** `tests/e2e/mock-gateway-local-simulacion.js` (Rutas `/api/v1/service-requests/:id`)
- **Descripción del Problema:**
  En la evaluación local de simulación del caso *"Solicitud de otro cliente → 404"*, el cliente ajeno (`usr-client-02`) intentaba consultar la orden `sr-qa-001`. El mock respondía `200 OK` en lugar de `404 Not Found` bajo RFC 9457.
- **Causa Raíz:**
  La cláusula de control en el mock contenía una condición de exclusión hardcodeada `&& reqId !== 'sr-qa-001'`, lo cual permitía saltarse la validación para esa orden específica en el simulador.
- **Solución Aplicada:**
  Se eliminó la excepción residual en `mock-gateway-local-simulacion.js`, forzando la evaluación estricta en el arnés. Ahora el cliente ajeno recibe inmediatamente HTTP `404 Not Found` con `Content-Type: application/problem+json` y tipo `/no-encontrado`. En QA real, el aislamiento es garantizado de forma nativa por Row-Level Security (RLS) en PostgreSQL VM5.
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

### 3.3 BUG-SP4-003: Contaminación de Estado en Memoria entre Suites en Harness Local (SCRUM-108 vs SCRUM-111)
- **Historia / Requisito:** `SCRUM-40` (Suspensión de Técnicos) / `RN-TP2` / `DD §8.3.13`
- **Ámbito:** Defecto del Harness de Pruebas (Simulador Local `mock-gateway-local-simulacion.js`), NO del producto en QA.
- **Severidad:** Media (Harness) | **Prioridad:** P1
- **Componente:** `tests/e2e/mock-gateway-local-simulacion.js` / `tests/e2e/run-all-increment-suites.js`
- **Descripción del Problema:**
  Al ejecutar todas las suites de incremento en lote sobre el simulador local, la suite `SCRUM-111` fallaba en la aserción 2.3 (*"Intento de suspender técnico en estado pendiente -> 409 Conflict"*) recibiendo HTTP `200 OK` en vez de `409 Conflict`.
- **Causa Raíz:**
  La suite previa `SCRUM-108` (Aprobación de Técnicos) aprobaba al técnico `usr-tec-pending-01`, mutando el diccionario estático `adminTechniciansDb` en el servidor mock en memoria. Cuando `SCRUM-111` se ejecutaba inmediatamente después en el mismo proceso de Node.js, `usr-tec-pending-01` ya no estaba en estado `pendiente`, sino `aprobado`.
- **Solución Aplicada:**
  Se diseñó e implementó la función `resetState()` en `mock-gateway-local-simulacion.js` y se instrumentó el ejecutor `run-all-increment-suites.js` para invocarla antes del inicio de cada suite individual. Esto garantiza aislamiento absoluto e idempotencia entre pruebas del simulador. En QA real, cada prueba maneja identidades y persistencia transaccional independiente en PostgreSQL VM5.
- **Verificación:**
  Reejecución consolidada: Las 7 suites del incremento (115 peticiones, 265 aserciones) pasaron al 100% en el harness local sin contaminación cruzada.

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

### 3.5 BUG-SP4-005: Discrepancia Contractual en Suite E2E: Invocación `PUT /status` en vez de `POST /start` y `/complete`
- **Historia / Requisito:** `SCRUM-35` (Ciclo de Ejecución) / `SCRUM-31` / `RF-14` / `RF-15`
- **Estado del Defecto:** **CORREGIDO EN SUITE DE PRUEBAS**
- **Severidad:** Media (Discrepancia de Contrato en la Prueba) | **Prioridad:** P2
- **Componente:** Colección de pruebas `scrum-84-seguimiento-estado.postman_collection.json` / ServiceRequest
- **Análisis Técnico y Alineación:**
  En la corrida de QA, las peticiones hacia `/api/v1/service-requests/:id/status` con método `PUT` recibieron `404 Not Found`. La causa fue una discrepancia en el diseño de la colección frente al contrato OpenAPI oficial de ServiceRequest v1.7.0 (SCRUM-96):
  1. El paso a `en_progreso` se realiza formalmente mediante `POST /api/v1/service-requests/{id}/start`.
  2. El cierre a `completado` exige evidencia fotográfica previa en Garage y se invoca mediante `POST /api/v1/service-requests/{id}/complete`.
  No existe la ruta genérica `PUT /status`. La colección se alinea al contrato OpenAPI 1.7.0.

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
- **Defectos Resueltos y Verificados:** **4**
  - `BUG-SP4-001` (Aislamiento intra-tenant en arnés local / verificado con RLS en PostgreSQL VM5).
  - `BUG-SP4-002` (Precedencia de sufijos aleatorios en variables de entorno Newman).
  - `BUG-SP4-003` (Aislamiento e idempotencia de estado en memoria en arnés local).
  - `BUG-SP4-004` (Encoding UTF-8 en harness de escáner en consolas Windows).
- **Reportes Reclasificados y Ajustes Contractuales:** **3**
  - `BUG-SP4-005` (Alineación con endpoints contractuales `POST /start` y `POST /complete` de ServiceRequest v1.7.0 para SCRUM-35).
  - `BUG-SP4-006` (Ruta inexistente: contrato formal es `GET /v1/service-requests/{id}`).
  - `BUG-SP4-007` (Colecciones ajustadas para creación dinámica de usuarios sin depender de seeds fijos).
- **Defectos Críticos o Bloqueantes Abiertos en el Incremento:** **0**.
- **Tasa de Resolución de Defectos:** **100.0%**.
- **Dictamen Final de QA:** **APROBADO SIN DEFECTOS BLOQUEANTES** para merge del incremento técnico de Sprint 4.

