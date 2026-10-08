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

Durante los ciclos de revisión de arquitectura, pruebas locales y simulación preparatoria del Sprint 3 se identificaron, gestionaron y corrigieron los siguientes 4 defectos formales:

| ID | Resumen del Defecto | HU Afectada | Severidad | Prioridad | Componente | Evidencia en Repositorio | Estado Final |
|---|---|:---:|:---:|:---:|---|---|:---:|
| **BUG-001** | Fallo en geolocalización por dependencia forzada de Google Location Services | SCRUM-27 (RF-07) | Alta | P1 | Mobile Flutter (`quickpatch-mobile#7`) | `tests/e2e/evidencias/movil/` (capturas 2 y 3) | **Verificado (Local)** |
| **BUG-002** | Colisión de rango CIDR de k3s (`10.43.0.0/16`) con la subred física del laboratorio | SCRUM-334 (INF-010) | Crítica | P1 | Infraestructura (`deploy-k3s.yml`, INFRA §5.2) | `docs/infrastructure/INFRASTRUCTURE.md` v1.2 | **Verificado (Inspección)** |
| **BUG-003** | Aserción permisiva y divergencia en validación de RN-T1 en suites de prueba | SCRUM-65 / 114 (RN-T1) | Media | P2 | E2E Postman Suite | `tests/e2e/scrum-65-roles-y-tenants.postman_collection.json` | **Corregido (Simulación)** |
| **BUG-004** | Discrepancia de tipo Problem Details RFC 9457 en rechazo por cobertura geográfica | SCRUM-325 (RN-SR9) | Media | P2 | ServiceRequest / Diagnóstico | `tests/e2e/validar-diagnostico-error-qa.js` | **Corregido (Simulación)** |

---

## 4. Detalle y Trazabilidad de los Defectos

### BUG-001: Fallo en captura de geolocalización por dependencia forzada de Google Play Services
- **HU Afectada:** `SCRUM-27` (Creación de solicitud de servicio técnico por Cliente — RF-07, M-07).
- **Severidad:** Alta | **Prioridad:** P1.
- **Ambiente:** Emulador Android 16 (Google Pixel 6) contra backend local (`http://10.0.2.2:8080`).
- **Precondiciones:** Cliente autenticado en la aplicación móvil en pantalla M-07 (Nueva solicitud).
- **Pasos de Reproducción:**
  1. Ingresar al formulario de creación de solicitud (`nueva_solicitud_page.dart`).
  2. En el diálogo emergente del sistema operativo "Google Location Accuracy", presionar "Cancelar" o rechazar el servicio propietario de Google.
  3. Presionar el botón "Solicitar servicio".
- **Resultado Obtenido:** La aplicación móvil no podía obtener la posición y quedaba bloqueada indefinidamente con el spinner de carga en pantalla, o arrojaba excepción no controlada (`LocationServiceDisabledException`) al carecer de los servicios propietarios de Google.
- **Resultado Esperado:** La aplicación debe solicitar la posición y, si los servicios de Google son rechazados o no se encuentran disponibles, activar un flujo de respaldo (`leerConRespaldo`) con un tiempo límite de 15 segundos (`limiteLectura`), usando la última posición conocida reciente ($\le 10$ minutos) o el GPS nativo del sistema (`LocationManager` con `forceLocationManager: true`), emitiendo un mensaje claro al usuario solo si todos los mecanismos fallan.
- **Causa Raíz:** `ProveedorUbicacionGps` utilizaba `Geolocator.getCurrentPosition()` directamente sin límites de tiempo ni estrategia de contingencia para dispositivos sin Google Play Services o que rechacen "Location Accuracy" (Pull Request `quickpatch-mobile#7`).
- **Solución y Evidencia:** Se implementó `LecturasGps`, `leerConRespaldo`, límite de lectura de 15 s y fallback forzado al GPS nativo del sistema (`soloGpsDelSistema: true`). Verificado en pruebas unitarias (`proveedor_ubicacion_test.dart`) y manuales en emulador Android contra backend local (`tests/e2e/evidencias/movil/2-categorias-y-ubicacion.png` y `3-formulario.png`).
- **Estado:** Corregido y verificado en entorno local.

---

### BUG-002: Riesgo de colisión de rango CIDR de k3s con la red del laboratorio
- **HU Afectada:** `SCRUM-334` (Redistribución de VMs) / `INF-010` (TD.md) / `INF-012`.
- **Severidad:** Crítica | **Prioridad:** P1.
- **Ambiente:** Especificación de despliegue k3s (VM2 QA `10.43.98.15` y VM3 Prod `10.43.98.205`).
- **Precondiciones:** Revisión crítica del diseño de infraestructura y playbooks de Ansible previo a la instalación del clúster k3s en las 7 VMs.
- **Pasos de Detección:**
  1. Inspeccionar la configuración por defecto de red en la instalación de k3s (`deploy-k3s.yml`).
  2. Contrastar el rango que k3s reserva por defecto para servicios (`10.43.0.0/16`) frente a la subred asignada por la Universidad a las 7 VMs del laboratorio (`10.43.98.x`, `10.43.99.x`, `10.43.100.x`).
- **Resultado Obtenido (Hallazgo de Revisión):** Si se utilizaba el `--service-cidr` por defecto de k3s (`10.43.0.0/16`), un ClusterIP asignado a un servicio interno podía coincidir con la IP real de otra VM del laboratorio (como VM4 en `10.43.98.209` o VM5 en `10.43.98.29`), provocando que el tráfico saliente desde un pod hacia PostgreSQL se enrutara internamente al servicio en vez de salir a la VM externa.
- **Resultado Esperado:** k3s debe instalarse configurando explícitamente sus bloques CIDR de pods y servicios por fuera del rango `10.43.0.0/16` del laboratorio.
- **Causa Raíz:** Hallazgo bloqueante detectado durante la revisión técnica independiente de la arquitectura e infraestructura (documentado en el historial de cambios de `INFRASTRUCTURE.md` v1.2 y caso `INF-010` de `TD.md`). No constituyó una pérdida de paquetes en vivo, sino un hallazgo de diseño preventivo antes del aprovisionamiento.
- **Solución y Evidencia:** Se configuró explícitamente en `deploy-k3s.yml` el flag `--cluster-cidr=10.42.0.0/16` para la subred de pods y `--service-cidr=10.44.0.0/16` para la subred de servicios, desacoplándolos por completo de la subred del laboratorio (`10.43.0.0/16`) según se documenta en `INFRASTRUCTURE.md` §5.2 y §10.3.
- **Estado:** Corregido y verificado mediante inspección técnica de configuración.

---

### BUG-003: Aserción permisiva y divergencia en validación de RN-T1 en suites de prueba
- **HU Afectada:** `SCRUM-65` / `SCRUM-114` (Roles y ciclo de vida de Tenants — RN-T1).
- **Severidad:** Media | **Prioridad:** P2.
- **Ambiente:** Suite de Pruebas de Roles y Permisos (Newman / API Gateway).
- **Precondiciones:** Tenant desactivado administrativamente mediante `PATCH /api/v1/platform/tenants/{id}/status`.
- **Pasos de Reproducción:**
  1. Ejecutar caso de prueba `IDN-019` intentando autenticación con usuario del tenant inactivo.
  2. Evaluar aserción de código HTTP en el script de prueba.
- **Resultado Obtenido:** La suite aceptaba de forma permisiva múltiples códigos de estado (`401`, `403` o `422`) e intentaba validar un bloqueo en creación de solicitudes, cuando según DD §7.12 la regla de negocio opera estrictamente rechazando el inicio de sesión.
- **Resultado Esperado:** Aserción estricta y determinística que verifique el rechazo exclusivo con `403 Forbidden` en `/api/v1/auth/login`.
- **Causa Raíz:** Ambigüedad en la definición del contrato de prueba previa a la conciliación del DD 7.12.
- **Solución y Evidencia:** Corrección en `tests/e2e/scrum-65-roles-y-tenants.postman_collection.json` (sub-folder 3.1 IDN-019 fijada en 403 estricto). Probado preliminarmente en simulación local con `tests/e2e/run-e2e.js` (22/22 aserciones aprobadas).
- **Estado:** Corregido en colección; verificado en simulación local (pendiente de ejecución sobre el ambiente de QA desplegado).

---

### BUG-004: Discrepancia de tipo Problem Details RFC 9457 en rechazo por cobertura geográfica
- **HU Afectada:** `SCRUM-325` / `SCRUM-27` (Diagnóstico de errores y Cobertura — RN-SR9).
- **Severidad:** Media | **Prioridad:** P2.
- **Ambiente:** Diagnóstico y Cobertura (ServiceRequest).
- **Precondiciones:** Petición con coordenadas fuera del perímetro de Bogotá.
- **Pasos de Reproducción:**
  1. Enviar `POST /api/v1/service-requests` con coordenadas fuera de Bogotá (`lat: 4.1500, lng: -73.0500`).
  2. Verificar payload de respuesta de error contra el esquema Problem Details.
- **Resultado Obtenido:** La prueba esperaba un error con formato propietario `ERR_LOCATION_OUT_OF_BOUNDS` y validación por polígono PostGIS, divergiendo del contrato real de ServiceRequest.
- **Resultado Esperado:** Respuesta estandarizada RFC 9457 de tipo `https://quickpatch.internal/problems/ubicacion-fuera-de-cobertura` (`Problems.OutOfCoverage`) basada en el rectángulo de configuración `CoverageArea` (RN-SR9).
- **Causa Raíz:** Divergencia entre el contrato estipulado en `Problems.cs` de ServiceRequest y los scripts iniciales de prueba de QA.
- **Solución y Evidencia:** Alineación de contratos en `tests/e2e/validar-diagnostico-error-qa.js` y `docs/testing/diagnostico-error-qa.md`. Probado preliminarmente en la simulación preparatoria reportada en `tests/e2e/evidencias/scrum-325-diagnostico-error-qa-2026-10-07.txt`.
- **Estado:** Corregido en contrato y script; verificado en simulación local (pendiente de ejecución sobre el ambiente de QA desplegado).

---

## 5. Resumen Ejecutivo y Estado de Defectos

```text
┌─────────────────────────────────────────────────────────────┐
│              ESTADÍSTICAS DEL SPRINT 3                      │
├─────────────────────────────────────────┬───────────────────┤
│ Total de Defectos Registrados           │                 4 │
│ Defectos Verificados en Local / Diseño  │     2 (BUG-001, 002)│
│ Defectos Corregidos en Simulación       │     2 (BUG-003, 004)│
│ Defectos Abiertos Residuales            │                 0 │
├─────────────────────────────────────────┼───────────────────┤
│ Defectos Críticos (Blocker)             │       1 (BUG-002) │
│ Defectos de Severidad Alta (Major)      │       1 (BUG-001) │
│ Defectos de Severidad Media (Minor)     │ 2 (BUG-003, 004)  │
│ Defectos Pendientes de QA Desplegado    │ 2 (BUG-003, 004)  │
└─────────────────────────────────────────┴───────────────────┘
```

**Conclusión de Calidad:**  
Los 4 defectos documentados se encuentran plenamente atendidos y resueltos: BUG-001 corregido en el repositorio móvil y validado en emulador local; BUG-002 prevenido en la configuración de Ansible de k3s por inspección técnica; y BUG-003 y BUG-004 alineados a nivel de contrato y colecciones, habiendo pasado la simulación preparatoria local y quedando agendados para su verificación final una vez esté disponible el clúster desplegado de QA.

