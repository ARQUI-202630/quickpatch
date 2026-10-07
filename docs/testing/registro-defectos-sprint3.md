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

Durante los ciclos de pruebas automatizadas y manuales contra el incremento de Sprint 3 se identificaron, reportaron y gestionaron los siguientes 5 defectos:

| ID | Resumen del Defecto | HU Afectada | Severidad | Prioridad | Componente | Estado Final |
|---|---|:---:|:---:|:---:|:---:|:---:|
| **BUG-001** | Fallo en captura de geolocalización GPS al cancelar diálogo de Google en Android 16 | SCRUM-27 (RF-07) | Alta | P1 | Mobile Flutter (`apps/mobile`) | **Verificado** |
| **BUG-002** | Colisión de rango CIDR de k3s (`10.43.0.0/16`) con la subred física del laboratorio | SCRUM-334 (INFRA-012) | Crítica | P1 | Infraestructura (`deploy-k3s.yml`) | **Verificado** |
| **BUG-003** | Error 404 intermitente en ServiceRequest por latencia de replicación de categorías en Kafka | SCRUM-27 (CAT-001) | Media | P2 | ServiceRequest / Kafka | **Verificado** |
| **BUG-004** | Error no controlado 500 al intentar desactivar el tenant raíz de la plataforma | SCRUM-41 (RF-21) | Media | P2 | Identity (`/v1/platform/tenants`) | **Verificado** |
| **BUG-005** | Ausencia del header `X-Correlation-Id` en respuestas de error 403 Forbidden | SCRUM-65 (RNF-04) | Alta | P2 | API Gateway / Identity | **Verificado** |

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
- **Solución y Verificación:** Se incorporó el componente de "Ubicación del dispositivo" desacoplado en Flutter. Verificado con éxito en la corrida del 7 de octubre (`tests/e2e/evidencias/movil/2-categorias-y-ubicacion.png` y `3-formulario.png`).

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
- **Solución y Verificación:** Se configuró explícitamente `--service-cidr=10.53.0.0/16` y `--cluster-cidr=10.52.0.0/16` en `deploy-k3s.yml` (documentado en INFRASTRUCTURE v1.2). Verificado con conectividad exitosa en todas las suites E2E.

---

### BUG-003: Condición de carrera por consistencia eventual de categorías en ServiceRequest
- **HU Afectada:** `SCRUM-27` / `SCRUM-319` (Flujo punta a punta de solicitud).
- **Severidad:** Media | **Prioridad:** P2.
- **Ambiente:** QA (VM2, microservicios `catalog` y `service-request`).
- **Precondiciones:** Administrador de tenant crea una categoría nueva en Catalog.
- **Pasos de Reproducción:**
  1. Enviar `POST /api/v1/catalog/admin/categories` con nombre "Cerrajería Rápida".
  2. Inmediatamente (< 100 ms), enviar `POST /api/v1/service-requests` utilizando el `categoryId` recién creado.
- **Resultado Obtenido:** La creación de solicitud fallaba con `422 Unprocessable Entity` ("Categoría no existe") debido a que el evento Kafka `catalog.category-changed` aún no se había propagado a la réplica local de lectura de ServiceRequest.
- **Resultado Esperado:** El sistema debe tolerar la consistencia eventual o el cliente debe esperar la sincronización del catálogo.
- **Causa Raíz:** Arquitectura orientada a eventos con desacoplamiento asíncrono y réplicas locales por base de datos (ADR-003).
- **Solución y Verificación:** Se implementó una política de sondeo de sincronización en la suite de pruebas E2E (espera activa hasta 10 reintentos cada 2 segundos) y se garantizó la publicación inmediata del Outbox Pattern. Verificado con 0 fallos en `quickpatch-mvp.postman_collection.json`.

---

### BUG-004: Error no controlado al intentar desactivar el tenant raíz de la plataforma
- **HU Afectada:** `SCRUM-41` (Gestión de tenants / SCRUM-113) / `SCRUM-112`.
- **Severidad:** Media | **Prioridad:** P2.
- **Ambiente:** QA (Identity en VM2).
- **Precondiciones:** Sesión iniciada como `admin_plataforma`.
- **Pasos de Reproducción:**
  1. Identificar el tenant ID correspondiente a la empresa de administración de la plataforma (`quickpatch-core`).
  2. Enviar petición `PATCH /api/v1/platform/tenants/{platform_tenant_id}/status` con `{"status": "inactivo"}`.
- **Resultado Obtenido:** Respuesta no controlada `500 Internal Server Error` al no existir una validación explícita sobre el tenant del sistema.
- **Resultado Esperado:** Respuesta controlada `409 Conflict` bajo RFC 9457 indicando que el tenant de la plataforma está protegido y no puede desactivarse.
- **Causa Raíz:** Omisión de guarda de dominio en el handler de actualización de estado de tenants de Identity.
- **Solución y Verificación:** Se incorporó la regla de negocio que rechaza la desactivación del tenant raíz con `409 Conflict` y tipo `/problems/conflicto-concurrencia`. Verificado con éxito en la carpeta 5 del MVP (SCRUM-112, PR #55).

---

### BUG-005: Ausencia del header `X-Correlation-Id` en respuestas de error 403 Forbidden
- **HU Afectada:** `SCRUM-65` (Roles y permisos / RNF-04).
- **Severidad:** Alta | **Prioridad:** P2.
- **Ambiente:** QA (Nginx Gateway VM1 y servicios Identity/Catalog).
- **Precondiciones:** Petición con token carente de roles administrativos.
- **Pasos de Reproducción:**
  1. Enviar `GET /api/v1/platform/tenants` con token de rol `cliente`.
- **Resultado Obtenido:** Código 403 Forbidden devuelto con mensaje estándar, pero sin el encabezado HTTP `X-Correlation-Id` en la respuesta.
- **Resultado Esperado:** Toda respuesta de error (4xx y 5xx) debe retornar `X-Correlation-Id` en cabeceras y en el cuerpo RFC 9457 para permitir su rastreo en Loki.
- **Causa Raíz:** El middleware de autorización denegaba el acceso antes del paso por el filtro de correlación de ASP.NET Core.
- **Solución y Verificación:** Reordenamiento en el pipeline de middlewares de los servicios, garantizando que el middleware de correlación se ejecute antes del middleware de autorización. Verificado en la suite E2E de roles (PR #31) y diagnóstico de QA (PR #58).

---

## 5. Resumen Ejecutivo y Decisión de Compuerta de Calidad

```text
┌─────────────────────────────────────────────────────────────┐
│              ESTADÍSTICAS DEL SPRINT 3                      │
├─────────────────────────────────────────┬───────────────────┤
│ Total de Defectos Registrados           │                 5 │
│ Defectos Resueltos y Verificados en QA  │                 5 │
│ Defectos Abiertos Pendientes            │                 0 │
├─────────────────────────────────────────┼───────────────────┤
│ Defectos Críticos (Blocker) Abiertos    │                 0 │
│ Defectos de Severidad Alta Abiertos     │                 0 │
└─────────────────────────────────────────┴───────────────────┘
```

**Conclusión de Calidad:**  
Al existir **0 defectos críticos y 0 defectos de severidad alta abiertos**, el incremento cumple satisfactoriamente el criterio de aceptación de la **Compuerta 2 (Pruebas de Sistema y UAT)** definido en el Documento de Pruebas `TD.md`, habilitando el corte formal de release hacia la revisión docente.
