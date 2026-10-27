# Registro y Clasificación Consolidada de Defectos — Sprints 4 y 5 (SCRUM-603)

**Código del Documento:** `DEF-QA-SP4-SP5-2026-10-25`  
**Versión:** `2.0 Final`  
**Fecha:** 25 de octubre de 2026  
**Responsable:** Katherine Bravo (`ka.bravo@javeriana.edu.co`) — QA Lead  
**Trazabilidad Jira:** Tarea `SCRUM-603` | RNF-08 (Aseguramiento de Calidad) | Documento de Pruebas `TD.md` V3.0  
**Normas Aplicadas:** IEEE 1044 (Classification for Software Anomalies) / ISO/IEC 25010:2023 / RFC 9457  

---

## 1. Criterios de Clasificación y Severidad

Conforme a los acuerdos de ingeniería y la gobernanza del proyecto QuickPatch, las anomalías detectadas en las distintas fases de prueba se clasifican bajo los siguientes niveles de severidad técnica:

* **S1 — Bloqueante (Blocker):** Provoca indisponibilidad total del servicio, pérdida o corrupción irrecuperable de datos, vulneración de confidencialidad o fallo en el aislamiento multi-tenant por Row-Level Security (RLS). Impide la aprobación del Quality Gate.
* **S2 — Alta (Major):** Afecta una regla de negocio principal (ej. orquestación de matching, cálculo de cotización o procesamiento de pagos) o discrepancia contractual que bloquea flujos automatizados sin bypass inmediato.
* **S3 — Media (Minor):** Discrepancias de formato en contratos secundarios (ej. tipo en Problem Details RFC 9457), efectos colaterales de persistencia en memoria, o validaciones cosméticas.
* **S4 — Baja (Trivial):** Inconsistencias menores de encoding en consolas, cabeceras informativas de depuración o mejoras de mensajes de registro.
* **Falla de Arnés (Test Harness Issue):** Defecto originado en las herramientas, mocks o runners de prueba locales, sin impacto en el comportamiento real del software en el clúster desplegado. Exige evidencia trazable de commit o corrida.

---

## 2. Matriz Consolidada de Defectos (Sprints 4 y 5)

La siguiente tabla consolida los defectos identificados en los ciclos de prueba de los Sprints 4 y 5, organizados según el formato oficial requerido:

| ID Jira | Severidad | Servicio | Detectado en (prueba) | Estado | Sprint en que se corrigió | Evidencia / Enlace |
|:---:|:---:|---|---|:---:|:---:|---|
| **BUG-SP4-001** | Media (Falla de Arnés) | Test Harness Local | Simulación Local E2E (Orden ajena) | **Corregido** | Sprint 4 | Commit `f6db3e7` / [`mock-gateway-local-simulacion.js:564`](../../tests/e2e/mock-gateway-local-simulacion.js#L564) / Corrida: `tests/e2e/evidencias/scrum-81-90-93-local-2026-10-17.txt` |
| **BUG-SP4-002** | Media | Runner Newman | E2E MVP (`run-mvp.js` login cliente) | **Corregido** | Sprint 4 | Commit `308f245` / [`run-mvp.js:40`](../../tests/e2e/run-mvp.js#L40) / Corrida: `tests/e2e/evidencias/mvp-qa-sprint4-2026-10-18.txt` |
| **BUG-SP4-003** | Media (Falla de Arnés) | Test Harness Local | Simulación Local E2E (SCRUM-108 vs 111) | **Corregido** | Sprint 4 | Commit `743d06c` / [`run-all-increment-suites.js:50`](../../tests/e2e/run-all-increment-suites.js#L50) / Corrida: `tests/e2e/evidencias/suites-e2e-qa-sprint4-2026-10-18.txt` |
| **BUG-SP4-004** | Baja | Scanner PCI | Consola Windows cp1252 (stdout encoding) | **Corregido** | Sprint 4 | Commit `308f245` / [`run-pci-dss-suite.py:20`](../../tests/security/run-pci-dss-suite.py#L20) / Evidencia: `tests/security/evidencias/pci-dss-loki-qa-2026-10-18.txt` |
| **BUG-SP4-005** | Media | `quickpatch-service-request` | E2E QA (`scrum-84-seguimiento-estado`) | **Corregido** | Sprint 4 | `tests/e2e/evidencias/scrum-84-seguimiento-estado-qa-2026-10-22.txt` |
| **BUG-SP4-006** | Media (Inválido) | `quickpatch-service-request` | E2E QA (Ruta `/assigned-detail`) | **Descartado** | Sprint 4 | Contrato OpenAPI canónico es `GET /api/v1/service-requests/{id}` |
| **BUG-SP4-007** | Media | Runner Newman / Seed | E2E QA (Cuentas fijas omitidas) | **Corregido** | Sprint 4 | `tests/e2e/evidencias/scrum-56-registro-tecnico-qa-2026-10-22.txt` (patrón `preparacion()`) |
| **BUG-SP4-008** | Baja | `quickpatch-identity` | E2E QA (`scrum-56-registro-tecnico`) | **Corregido** | Sprint 4 | `tests/e2e/evidencias/scrum-56-registro-tecnico-qa-2026-10-22.txt` (tipo `problems/validacion`) |
| **BUG-SP4-009** | Media | `quickpatch-identity` | E2E QA (`scrum-99-equipo-proveedor`) | **Corregido** | Sprint 4 | `tests/e2e/evidencias/scrum-99-equipo-proveedor-qa-2026-10-22.txt` (remoción `specialty`) |
| **SCRUM-410** | Media | `quickpatch-service-request` | Rendimiento k6 (Prueba de estrés 150 VU) | **Corregido** | Sprint 4 | PR #121 (`cancelar()` en k6) / `tests/performance/evidencias/k6-stress-150vu-qa-2026-10-18.txt` |
| **SCRUM-606** | Media | `quickpatch-communication` | Tiempo Real WebSocket (`scrum-478`) | **Pendiente** | Sprint 5 | Reintentos automáticos y reconexión en WebSocket Gateway |
| **SCRUM-607** | Baja | `quickpatch-payments` | Facturación y Comprobante PDF (`scrum-495`) | **Pendiente** | Sprint 5 | Desglose formal de impuestos en PDF de liquidación |
| **SCRUM-608** | Media | `quickpatch-mobile` | Pruebas UAT Emulador Android (GPS Mock) | **Pendiente** | Sprint 5 | Inyección de coordenadas geográficas en emulador Android |
| **SCRUM-609** | Baja | `quickpatch-web` | Interacción UI Web Admin (Paginación) | **Pendiente** | Sprint 5 | Ajuste de paginación reactiva en listado de técnicos |

---

## 3. Resumen Cuantitativo de Defectos

| Estado del Defecto | Cantidad | Porcentaje |
|---|:---:|:---:|
| **Solucionados y Verificados (Cerrados)** | 9 | 64.3% |
| **Descartados / Inválidos (Retractados)** | 1 | 7.1% |
| **Pendientes (En desarrollo en Sprint 5)** | 4 | 28.6% |
| **Total de Defectos Registrados** | **14** | **100.0%** |

### Distribución por Severidad
* **Bloqueantes (S1):** 0 detectados (0.0%).
* **Alta (S2):** 0 abiertas en Sprint 5 (0.0%).
* **Media (S3) / Falla de Arnés:** 10 registrados (6 corregidos en producto/suite, 2 fallas de arnés comprobadas con evidencia, 1 descartado, 2 pendientes en Sprint 5).
* **Baja (S4):** 4 registrados (2 corregidos en Sprint 4, 2 pendientes en Sprint 5).

---

## 4. Fichas Técnicas de Defectos del Arnés de Pruebas (SCRUM-603)

### BUG-SP4-001: Excepción Residual en Mock Local de Simulación (`mock-gateway-local-simulacion.js`)
* **Clasificación:** Falla de Arnés de Pruebas (Test Harness Issue).
* **Severidad:** Media (Harness) | **Prioridad:** P1.
* **Componente:** `tests/e2e/mock-gateway-local-simulacion.js` (Línea 564).
* **Descripción:** En la simulación local de la prueba de aislamiento cross-tenant (*"Solicitud de otro cliente → 404"*), el arnés respondía HTTP `200 OK` en vez de `404 Not Found`.
* **Causa Raíz:** Cláusula de excepción hardcodeada `&& reqId !== 'sr-qa-001'` que puenteaba la validación de pertenencia.
* **Evidencia en Repositorio:**
  - Commit de corrección: `f6db3e7` (*"fix(qa): resolver observaciones de revision PR #106..."*).
  - Archivo modificado: [`mock-gateway-local-simulacion.js:564`](../../tests/e2e/mock-gateway-local-simulacion.js#L564).
  - Corrida de verificación: `tests/e2e/evidencias/scrum-81-90-93-local-2026-10-17.txt`.
* **Estado:** Corregido y Verificado.

### BUG-SP4-003: Contaminación de Estado en Memoria entre Suites en Runner Local
* **Clasificación:** Falla de Arnés de Pruebas (Test Harness Issue).
* **Severidad:** Media (Harness) | **Prioridad:** P1.
* **Componente:** `tests/e2e/run-all-increment-suites.js` (Línea 50).
* **Descripción:** Al correr en lote todas las suites locales, la suite `SCRUM-111` fallaba en la aserción de suspensión de técnico pendiente (`409 Conflict`), recibiendo `200 OK`.
* **Causa Raíz:** La suite anterior `SCRUM-108` aprobaba al técnico en el diccionario estático en memoria de Node.js, dejando el estado mutado para la suite siguiente.
* **Evidencia en Repositorio:**
  - Commit de corrección: `743d06c` (*"fix(qa): atender feedback pr106, reclasificar defectos..."*).
  - Archivo instrumentado: [`run-all-increment-suites.js:50`](../../tests/e2e/run-all-increment-suites.js#L50) implementando invocación a `resetState()`.
  - Corrida de verificación: `tests/e2e/evidencias/suites-e2e-qa-sprint4-2026-10-18.txt`.
* **Estado:** Corregido y Verificado.

---

## 5. Dictamen del Registro de Defectos

El sistema no presenta defectos bloqueantes (S1) ni defectos de severidad alta (S2) abiertos. Los defectos identificados en el arnés de pruebas se encuentran debidamente justificados con sus commits y archivos de corrida correspondientes. Las anomalías del Sprint 5 se encuentran priorizadas para resolución en sus respectivas historias de usuario.
