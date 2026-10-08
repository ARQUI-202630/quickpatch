# Registro y Clasificación de Defectos — Sprint 3 (SCRUM-321)

**Fecha:** 7 de octubre de 2026  
**Responsable:** Katherine Bravo (`ka.bravo@javeriana.edu.co`) — QA Lead  
**Trazabilidad Jira:** Subtarea `SCRUM-321` | Historia `SCRUM-307` | Documento de Pruebas `TD.md` V1.4  
**Ambiente de Ejecución:** QA (VM2 k3s `10.43.98.15`, VM5 datos `10.43.98.29`, VM1 observabilidad `10.43.100.168`)

---

## 1. Criterios de Clasificación de Defectos

Conforme a la metodología definida para QUICKPATCH y los estándares IEEE 1044 / ISO/IEC 25010, los defectos detectados durante las fases de pruebas (E2E, integración, interfaz y seguridad) se evalúan mediante dos dimensiones ortogonales: **Severidad** (impacto funcional/técnico) y **Prioridad** (urgencia de resolución de cara al release).

### 1.1 Matriz de Severidad (Impacto Técnico en el Sistema)
- **Crítica (Blocker):** Provoca caída total del servicio, pérdida o corrupción irrecuperable de datos, brechas de seguridad mayores o bloqueo completo de un flujo funcional crítico sin solución alternativa (workaround). Impide el paso a producción.
- **Alta (Major):** Afecta gravemente una funcionalidad principal de una Historia de Usuario o contrato API, pero el sistema continúa operando o existe un mecanismo de mitigación temporal.
- **Media (Minor):** Comportamiento inesperado en validaciones secundarias, mensajes de error confusos, desfase en consistencia eventual o degradación visual no bloqueante en la interfaz.
- **Baja (Trivial):** Errores cosméticos, inconsistencias tipográficas en textos o etiquetas menores que no afectan la lógica del negocio.

### 1.2 Matriz de Prioridad (Urgencia de Negocio y Release)
- **P1 — Inmediata:** Debe resolverse antes de continuar las pruebas del sprint o cortar el release candidate.
- **P2 — Alta:** Debe resolverse en la iteración actual antes de la compuerta final de QA.
- **P3 — Normal:** Debe atenderse en el backlog del sprint o inicio del siguiente incremento.
- **P4 — Baja:** Atendible según disponibilidad de tiempo o en fase de refinamiento.

---

## 2. Plantilla Estandarizada de Reporte de Bug

Cada defecto identificado debe documentarse con los siguientes campos mínimos:

```text
[ID]: BUG-XXX
Título: Resumen corto, conciso e inequívoco de la anomalía
Historia de Usuario / Requisito: HU afectada (ej. SCRUM-27, RF-07)
Severidad: Crítica | Alta | Media | Baja
Prioridad: P1 | P2 | P3 | P4
Ambiente: QA (VM2/VM5) / Emulador Mobile / Web Admin
Precondiciones: Estado previo del sistema
Pasos de Reproducción:
  1. ...
  2. ...
Resultado Obtenido: Qué hizo el sistema (código HTTP, mensaje, fallo)
Resultado Esperado: Qué debió hacer según el contrato o mockup
Causa Raíz Técnica: Explicación arquitectónica/código
Evidencia / Trazas: Logs de Loki, Correlation ID, capturas o respuestas JSON
Estado: Abierto | En Corrección | Resuelto | Verificado en QA
```

---

## 3. Matriz Consolidada de Defectos Identificados en Sprint 3

Durante los ciclos de pruebas automatizadas y manuales contra el incremento de Sprint 3 se identificaron, reportaron y gestionaron los siguientes 4 defectos formales verificados con evidencias reales en el repositorio:

| ID | Resumen del Defecto | HU Afectada | Severidad | Prioridad | Componente | Evidencia en Repositorio | Estado Final |
|---|---|:---:|:---:|:---:|---|---|:---:|
| **BUG-001** | Fallo en captura de geolocalización GPS al cancelar diálogo de Google en Android 16 | SCRUM-27 (RF-07) | Alta | P1 | Mobile Flutter (`apps/mobile`) | `tests/e2e/evidencias/movil/` (capturas 2 y 3) | **Verificado** |
| **BUG-002** | Colisión de rango CIDR de k3s (`10.43.0.0/16`) con la subred física del laboratorio | SCRUM-334 (INFRA-012) | Crítica | P1 | Infraestructura (`deploy-k3s.yml`) | `infrastructure/ansible/playbooks/deploy-k3s.yml` | **Verificado** |
| **BUG-003** | Aserción permisiva y divergencia en validación de RN-T1 en suites de prueba | SCRUM-65 / 114 (RN-T1) | Media | P2 | E2E Postman Suite | `tests/e2e/scrum-65-roles-y-tenants.postman_collection.json` | **Verificado** |
| **BUG-004** | Discrepancia de tipo Problem Details RFC 9457 en rechazo por cobertura geográfica | SCRUM-325 (RN-SR9) | Media | P2 | ServiceRequest / Diagnóstico | `tests/e2e/validar-diagnostico-error-qa.js` | **Verificado** |

---

## 4. Detalle y Trazabilidad de los Defectos

### BUG-001: Fallo en captura de geolocalización GPS en Android 16
- **HU Afectada:** `SCRUM-27` (Creación de solicitud de servicio técnico por Cliente — RF-07, M-07).
- **Severidad:** Alta | **Prioridad:** P1.
- **Ambiente:** Emulador Android 16 (Google Pixel 6) contra backend QA.
- **Precondiciones:** Cliente autenticado en la app móvil en pantalla M-07 (Nueva solicitud).
- **Pasos de Reproducción:**
  1. Ingresar al formulario de creación de solicitud.
  2. En el diálogo emergente del sistema operativo "Google Location Accuracy", presionar "Cancelar" o "No ahora".
  3. Presionar el botón "Solicitar servicio".
- **Resultado Obtenido:** La aplicación móvil enviaba `location: null` o se congelaba el spinner de carga, devolviendo error 400 por campo faltante o crash del hilo UI.
- **Resultado Esperado:** La aplicación debe obtener la ubicación provista por el GPS local del dispositivo mediante el componente de ubicación nativo sin depender de servicios propietarios de Google, enviando latitud y longitud válidas en Bogotá.
- **Causa Raíz:** El plugin de geolocalización en Flutter requería de forma forzada la aceptación de Google Location Services en lugar del proveedor GPS nativo del dispositivo (referencia `quickpatch-mobile#7`).
- **Solución y Evidencia:** Se incorporó el componente de "Ubicación del dispositivo" desacoplado en Flutter. Evidencia verificada en `tests/e2e/evidencias/movil/2-categorias-y-ubicacion.png` y `3-formulario.png`.

---

### BUG-002: Colisión de rango CIDR de k3s con la red del laboratorio
- **HU Afectada:** `SCRUM-334` (Redistribución de VMs) / `INF-012`.
- **Severidad:** Crítica | **Prioridad:** P1.
- **Ambiente:** VM2 (k3s QA `10.43.98.15`) y VM3 (k3s Prod).
- **Precondiciones:** Despliegue inicial de cluster k3s con configuración por defecto.
- **Pasos de Reproducción:**
  1. Ejecutar el playbook de aprovisionamiento de k3s.
  2. Intentar comunicar los pods de VM2 con la base de datos PostgreSQL en VM5 (`10.43.98.29`) o el Gateway en VM1 (`10.43.100.168`).
- **Resultado Obtenido:** Pérdida masiva de paquetes y timeouts de conexión intermitentes entre pods y servicios externos a k3s.
- **Resultado Esperado:** Comunicación transparente bidireccional entre la red overlay de k3s y la red física del laboratorio.
- **Causa Raíz:** El `--service-cidr` por defecto de k3s asignaba el bloque `10.43.0.0/16`, el cual solapaba exactamente con el segmento de direccionamiento asignado por la Universidad (`10.43.x.x`).
- **Solución y Evidencia:** Se configuró explícitamente `--service-cidr=10.53.0.0/16` y `--cluster-cidr=10.52.0.0/16` en `infrastructure/ansible/playbooks/deploy-k3s.yml` (documentado en `docs/infrastructure/INFRASTRUCTURE.md` v2.4).

---

### BUG-003: Aserción permisiva y divergencia en validación de RN-T1 en suites de prueba
- **HU Afectada:** `SCRUM-65` / `SCRUM-114` (Roles y ciclo de vida de Tenants — RN-T1).
- **Severidad:** Media | **Prioridad:** P2.
- **Ambiente:** Suite E2E de Roles y Permisos (Newman / API Gateway).
- **Precondiciones:** Tenant `tenant-bogota-001` desactivado administrativamente mediante `PATCH /api/v1/platform/tenants/{id}/status`.
- **Pasos de Reproducción:**
  1. Ejecutar caso de prueba `IDN-019` intentando autenticación con usuario del tenant inactivo.
  2. Evaluar aserción de código HTTP en el script de prueba.
- **Resultado Obtenido:** La suite aceptaba de forma permisiva múltiples códigos de estado (`401`, `403` o `422`) e intentaba validar un bloqueo en creación de solicitudes, cuando según DD §7.12 la regla de negocio opera estrictamente rechazando el inicio de sesión.
- **Resultado Esperado:** Aserción estricta y determinística que verifique el rechazo exclusivo con `403 Forbidden` en `/api/v1/auth/login`.
- **Causa Raíz:** Ambigüedad en la definición del contrato de prueba previa a la conciliación del DD 7.12.
- **Solución y Evidencia:** Corrección en `tests/e2e/scrum-65-roles-y-tenants.postman_collection.json` (sub-folder 3.1 IDN-019 fijada en 403 estricto). Evidencia verificada en `tests/e2e/run-e2e.js` (22/22 aserciones aprobadas).

---

### BUG-004: Discrepancia de tipo Problem Details RFC 9457 en rechazo por cobertura geográfica
- **HU Afectada:** `SCRUM-325` / `SCRUM-27` (Diagnóstico de errores y Cobertura — RN-SR9).
- **Severidad:** Media | **Prioridad:** P2.
- **Ambiente:** QA (ServiceRequest en VM2).
- **Precondiciones:** Petición con coordenadas fuera del perímetro de Bogotá.
- **Pasos de Reproducción:**
  1. Enviar `POST /api/v1/service-requests` con coordenadas fuera de Bogotá (`lat: 4.1500, lng: -73.0500`).
  2. Verificar payload de respuesta de error contra el esquema Problem Details.
- **Resultado Obtenido:** La prueba esperaba un error con formato propietario `ERR_LOCATION_OUT_OF_BOUNDS` y validación por polígono PostGIS, divergiendo del contrato real de ServiceRequest.
- **Resultado Esperado:** Respuesta estandarizada RFC 9457 de tipo `https://quickpatch.internal/problems/ubicacion-fuera-de-cobertura` (`Problems.OutOfCoverage`) basada en el rectángulo de configuración `CoverageArea` (RN-SR9).
- **Causa Raíz:** Divergencia entre el contrato estipulado en `Problems.cs` de ServiceRequest y los scripts iniciales de prueba de QA.
- **Solución y Evidencia:** Alineación de contratos en `tests/e2e/validar-diagnostico-error-qa.js` y `docs/testing/diagnostico-error-qa.md`. Evidencia verificada en `tests/e2e/evidencias/scrum-325-diagnostico-error-qa-2026-10-07.txt`.

---

## 5. Resumen Ejecutivo y Decisión de Compuerta de Calidad

```text
┌─────────────────────────────────────────────────────────────┐
│              ESTADÍSTICAS DEL SPRINT 3                      │
├─────────────────────────────────────────┬───────────────────┤
│ Total de Defectos Registrados           │                 4 │
│ Defectos Resueltos y Verificados en QA  │                 4 │
│ Defectos Abiertos Pendientes            │                 0 │
├─────────────────────────────────────────┼───────────────────┤
│ Defectos Críticos (Blocker)             │       1 (BUG-002) │
│ Defectos de Severidad Alta (Major)      │       1 (BUG-001) │
│ Defectos de Severidad Media (Minor)     │ 2 (BUG-003, 004)  │
│ Defectos Abiertos Residuales            │                 0 │
└─────────────────────────────────────────┴───────────────────┘
```

**Conclusión de Calidad:**  
Al existir **0 defectos críticos y 0 defectos de severidad alta abiertos** (100% de los defectos verificados y cerrados), el incremento cumple satisfactoriamente el criterio de aceptación de la compuerta de calidad de defectos, garantizando la estabilidad y consistencia de las entregas de QA para el Sprint 3.
