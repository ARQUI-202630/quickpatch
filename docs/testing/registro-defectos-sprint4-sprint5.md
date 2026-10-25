# Registro Consolidado de Defectos — Sprints 4 y 5 (SCRUM-603)

**Código del Documento:** `DEF-QA-SP4-SP5-2026-10-24`  
**Responsable:** Katherine Bravo (`ka.bravo@javeriana.edu.co`) — QA Lead  
**Trazabilidad Jira:** Tarea Padre `SCRUM-603` | Requisito RNF-08 | TD V2.9 (§9)  
**Estándares Aplicados:** IEEE 1044 (Classification for Software Anomalies), ISO/IEC 25010:2023  
**Fecha de Actualización:** 24 de octubre de 2026  

---

## 1. Criterios de Clasificación y Severidad

Conforme a la metodología arquitectónica de QuickPatch, cada defecto detectado durante las pruebas automatizadas (E2E, integración, rendimiento, seguridad y UAT) se clasifica según su severidad técnica:

* **S1 — Blocker (Crítica):** Provoca caída total del servicio, pérdida o corrupción irrecuperable de datos, brechas de seguridad mayores o violación del aislamiento multi-tenant por Row-Level Security (RLS).
* **S2 — Alta (Major):** Falla en una función principal de negocio (ej. flujo de matching, cotización o pago) o discrepancia contractual que bloquea la ejecución de suites automatizadas sin alternativa operativa inmediata.
* **S3 — Media (Minor):** Desfase de validaciones de contrato secundarias (ej. nombres de Problem Details RFC 9457), mensajes de error confusos o inconsistencias menores en esquemas de solicitud.
* **S4 — Baja (Trivial):** Ajustes cosméticos, cabeceras de depuración o formatos opcionales que no impiden el funcionamiento de la lógica del negocio.

---

## 2. Matriz Consolidada de Registro de Defectos (SCRUM-603)

A continuación se presenta el registro oficial de anomalías identificadas, trazadas y gestionadas en los Sprints 4 y 5, con su correspondiente estado de resolución:

| ID Jira | Severidad | Servicio | Detectado en (prueba) | Estado | Sprint en que se corrigió |
|:---:|:---:|---|---|:---:|:---:|
| **SCRUM-405** | Alta | `quickpatch-identity` | E2E Newman (`scrum-incremento-tecnico` en QA) | **Corregido** | Sprint 4 |
| **SCRUM-406** | Media | `quickpatch-actors` | E2E Newman (`scrum-99-equipo-proveedor` en QA) | **Corregido** | Sprint 4 |
| **SCRUM-407** | Media | `quickpatch-identity` | E2E Newman (`scrum-56-registro-tecnico` en QA) | **Corregido** | Sprint 4 |
| **SCRUM-408** | Alta | `quickpatch-service-request` | E2E Newman (`scrum-84-seguimiento-estado` en QA) | **Corregido** | Sprint 4 |
| **SCRUM-409** | Baja | `quickpatch-api-gateway` | Seguridad DAST (OWASP ZAP Baseline en VM1) | **Corregido** | Sprint 4 |
| **SCRUM-410** | Media | `quickpatch-service-request` | Rendimiento k6 (Prueba de Estrés 150 VU) | **Corregido** | Sprint 4 |
| **SCRUM-411** | Baja | QA Test Harness / CLI | Newman CLI en PowerShell (Codificación terminal) | **Corregido** | Sprint 4 |
| **SCRUM-606** | Media | `quickpatch-communication` | Tiempo Real WebSocket (`scrum-478-aviso-tiempo-real`) | **Pendiente** | Sprint 5 |
| **SCRUM-607** | Baja | `quickpatch-payments` | Facturación y Comprobante PDF (`scrum-495`) | **Pendiente** | Sprint 5 |
| **SCRUM-608** | Media | `quickpatch-mobile` | Pruebas UAT Emulador Android 16 (Google Location) | **Pendiente** | Sprint 5 |
| **SCRUM-609** | Baja | `quickpatch-web` | Interacción UI Web Admin (Paginación de técnicos) | **Pendiente** | Sprint 5 |

---

## 3. Resumen Cuantitativo de Defectos

| Estado del Defecto | Cantidad | Porcentaje |
|---|:---:|:---:|
| **Solucionados / Verificados (Cerrados)** | 7 | 63.6% |
| **Pendientes (En desarrollo en Sprint 5)** | 4 | 36.4% |
| **Total de Defectos Registrados** | **11** | **100.0%** |

### Distribución por Severidad
* **Bloqueantes (S1):** 0 abiertos (0%)
* **Alta (S2):** 2 detectados en Sprint 4, ambos 100% corregidos.
* **Media (S3):** 6 detectados (3 corregidos en Sprint 4, 3 en mitigación en Sprint 5).
* **Baja (S4):** 3 detectados (2 corregidos en Sprint 4, 1 en refinamiento en Sprint 5).

---

## 4. Fichas Técnicas de Defectos Relevantes

### SCRUM-405: Fallo en cascada de autenticación en QA por dependencia de credenciales estáticas
* **Severidad:** Alta | **Estado:** Corregido (Sprint 4).
* **Causa Raíz:** La suite de Newman asumía la existencia previa de fixtures fijos (`usr-tec-01`) que no estaban sembrados en la base de datos de QA en VM5, originando respuestas HTTP 401 Unauthorized en cadena.
* **Solución Aplicada:** Implementación del patrón dinámico `preparacion()` con generación al vuelo de usuarios únicos (`Date.now().toString(36)`) y contraseña conforme a políticas de seguridad.

### SCRUM-406: Discrepancia de esquema en alta de técnicos por proveedor
* **Severidad:** Media | **Estado:** Corregido (Sprint 4).
* **Causa Raíz:** La prueba enviaba un campo excedente `specialty` en `ProviderTechnicianRequest`, generando HTTP 400 Bad Request por fallo de validación del contrato OpenAPI.
* **Solución Aplicada:** Alineación estricta de la prueba con la especificación OpenAPI v1.0.0, enviando únicamente `email`, `fullName`, `phone` y `documentId`.

### SCRUM-408: Invocación de endpoint deprecado en seguimiento de estados
* **Severidad:** Alta | **Estado:** Corregido (Sprint 4).
* **Causa Raíz:** La suite `scrum-84` intentaba modificar el estado de la orden mediante `PUT /status`, endpoint retirado en ServiceRequest v1.7.0.
* **Solución Aplicada:** Corrección del flujo para utilizar `POST /start`, carga obligatoria de evidencia fotográfica en Garage S3 (VM7) y `POST /complete`.

### SCRUM-410: Saturación de persistencia en PostgreSQL por falta de auto-cancelación en k6
* **Severidad:** Media | **Estado:** Corregido (Sprint 4).
* **Causa Raíz:** Las 38.876 iteraciones de la prueba de estrés de 150 VU dejaban solicitudes abiertas en estado `buscando_tecnico`, acumulando miles de registros no atendidos en VM5.
* **Solución Aplicada:** Inclusión de la rutina `cancelar(res, headers)` invocando `POST /api/v1/service-requests/{id}/cancel` al término de cada ciclo de usuario virtual (PR #121 / SCRUM-472).
