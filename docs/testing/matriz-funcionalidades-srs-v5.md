# Matriz de Funcionalidades y Cobertura SRS V5 (SCRUM-561)

**Código del Documento:** `MTX-FUNC-SRS-V5-2026-10-25`  
**Versión:** `2.0 Final`  
**Fecha:** 25 de octubre de 2026  
**Responsable:** Katherine Bravo (`ka.bravo@javeriana.edu.co`) — QA Lead  
**Trazabilidad Jira:** Tarea `SCRUM-561` | SRS V5 | Documento de Pruebas `TD.md` V3.0  
**Ambiente:** QA Desplegado (`https://qa.quickpatch.internal` en VM2 k3s)  

---

## 1. Convenciones de Estado de Desarrollo y Prueba

* **Probada (E2E QA):** Funcionalidad completamente implementada en backend/frontend y certificada mediante suites E2E ejecutadas contra el clúster de QA desplegado.
* **Probada (Mock):** Funcionalidad validada en flujos de prueba contra servicios simulados o pasarelas en modo sandbox/mock (ej. pasarela de pagos Wompi/Stripe simulada).
* **No desarrollada:** Requisito o funcionalidad especificada en el SRS pero cuya lógica de negocio no ha sido implementada en los microservicios actuales.

---

## 2. Matriz de Cobertura de Requisitos Funcionales (SRS V5)

| RF / HU | Funcionalidad | Servicio Responsable | Estado de Desarrollo / Prueba | Archivo de Evidencia (Ruta Relativa del Repositorio) | Observaciones |
|---|---|---|:---:|---|---|
| **RF-01** (SCRUM-21) | Registro de Clientes Individuales | `Identity` | **Probada (E2E QA)** | `tests/e2e/evidencias/mvp-qa-sprint4-2026-10-18.txt` | Creación de cuenta, validación de contraseña segura y unicidad de email. |
| **RF-02** (SCRUM-21) | Autenticación y Cierre de Sesión (JWT) | `Identity` | **Probada (E2E QA)** | `tests/e2e/evidencias/mvp-qa-sprint4-2026-10-18.txt` | Emisión de tokens JWT RSA-256 con claims de tenant y rol. |
| **RF-03** (SCRUM-21) | Consulta de Perfil de Usuario (`/me`) | `Identity` | **Probada (E2E QA)** | `tests/e2e/evidencias/mvp-qa-sprint4-2026-10-18.txt` | Consulta de datos básicos y roles del usuario autenticado. |
| **RF-04** (SCRUM-23) | Consulta de Categorías y Especialidades | `Catalog` | **Probada (E2E QA)** | `tests/e2e/evidencias/mvp-qa-sprint4-2026-10-18.txt` | Catálogo de servicios con caché Redis y respuesta $< 100\text{ ms}$. |
| **RF-05** (SCRUM-28) | Creación de Solicitud de Servicio | `ServiceRequest` | **Probada (E2E QA)** | `tests/e2e/evidencias/scrum-84-seguimiento-estado-qa-2026-10-22.txt` | Alta de solicitud en estado `buscando_tecnico` con evento Outbox. |
| **RF-06** (SCRUM-43) | Liquidación y Pago de Solicitud | `Payments` | **Probada (Mock)** | `tests/e2e/evidencias/scrum-117-pago-qa-2026-10-22.txt` | Integración con pasarela de pagos simulada en modo sandbox/mock. |
| **RF-07** (SCRUM-45) | Generación de Comprobante de Pago | `Payments` | **Probada (Mock)** | `tests/e2e/evidencias/scrum-495-comprobante-qa-2026-10-22.txt` | Emisión de recibo digital simulado con correlationId y desglose. |
| **RF-08** (SCRUM-30) | Cancelación de Solicitud de Servicio | `ServiceRequest` | **Probada (E2E QA)** | `tests/e2e/evidencias/scrum-478-cancelacion-qa-2026-10-19.txt` | Cancelación atómica y liberación de técnico en Matching. |
| **RF-09** (SCRUM-29) | Motor de Asignación Automática (Matching) | `Matching` | **Probada (E2E QA)** | `tests/e2e/evidencias/scrum-78-qa-2026-10-22.txt` | Evaluación de proximidad geoespacial con PostGIS y estado operativo. |
| **RF-10** (SCRUM-29) | Notificación y Aceptación/Rechazo de Oferta | `Matching` | **Probada (E2E QA)** | `tests/e2e/evidencias/scrum-incremento-tecnico-qa-2026-10-22.txt` | Aceptación y rechazo atómico de ofertas con reintento automático. |
| **RF-11** (SCRUM-31) | Seguimiento de Estados en Tiempo Real | `ServiceRequest` | **Probada (E2E QA)** | `tests/e2e/evidencias/scrum-84-seguimiento-estado-qa-2026-10-22.txt` | Transiciones `buscando_tecnico` $\to$ `asignado` $\to$ `en_progreso` $\to$ `completado`. |
| **RF-12** (SCRUM-32) | Calificación del Servicio Realizado | `ServiceRequest` | **No desarrollada** | *(Sin archivo de evidencia)* | Funcionalidad de calificación por el cliente aún no implementada. |
| **RF-13** (SCRUM-22) | Registro de Técnico Independiente | `Identity` | **Probada (E2E QA)** | `tests/e2e/evidencias/scrum-56-registro-tecnico-qa-2026-10-22.txt` | Alta con especialidad y estado inicial `pendiente_verificacion`. |
| **RF-14** (SCRUM-22) | Registro de Empresa Proveedora | `Identity` | **Probada (E2E QA)** | `tests/e2e/evidencias/scrum-56-registro-tecnico-qa-2026-10-22.txt` | Alta de entidad proveedora con herencia de tenant. |
| **RF-15** (SCRUM-81) | Cobertura Geográfica de Técnico | `Matching` | **Probada (E2E QA)** | `tests/e2e/evidencias/scrum-incremento-tecnico-qa-2026-10-22.txt` | Definición de polígonos y radios de atención con PostGIS. |
| **RF-16** (SCRUM-36) | Gestión de Equipo de Técnicos por Proveedor | `Actors` / `Identity` | **Probada (E2E QA)** | `tests/e2e/evidencias/scrum-99-equipo-proveedor-qa-2026-10-22.txt` | Alta, activación y listado de técnicos del equipo del proveedor. |
| **RF-17** (SCRUM-90) | Control de Disponibilidad Operativa | `Matching` | **Probada (E2E QA)** | `tests/e2e/evidencias/scrum-incremento-tecnico-qa-2026-10-22.txt` | Conmutación de estado disponible / no disponible para asignaciones. |
| **RF-18** (SCRUM-34) | Panel Operativo de Solicitudes para Técnico | `ServiceRequest` | **Probada (E2E QA)** | `tests/e2e/evidencias/scrum-105-panel-operativo-qa-2026-10-22.txt` | Detalle de orden con datos de contacto resueltos para técnico asignado. |
| **RF-19** (SCRUM-39) | Aprobación y Rechazo de Técnicos | `Identity` | **Probada (E2E QA)** | `tests/e2e/evidencias/scrum-108-aprobacion-rechazo-qa-2026-10-22.txt` | Dictamen administrativo con emisión de evento Kafka outbox. |
| **RF-20** (SCRUM-40) | Suspensión de Cuenta de Técnico | `Identity` | **Probada (E2E QA)** | `tests/e2e/evidencias/scrum-111-suspension-tecnico-qa-2026-10-22.txt` | Suspensión con motivo justificado y bloqueo automático en matching. |
| **RF-21** (SCRUM-32) | Reputación y Ranking de Técnico | `Ranking` | **No desarrollada** | *(Sin archivo de evidencia)* | Microservicio Ranking opera en esqueleto (6 pruebas unitarias básicas). |
| **RF-22** (SCRUM-66) | Cuenta Corporativa y Gestión de Miembros | `Identity` | **Probada (E2E QA)** | `tests/e2e/evidencias/scrum-68-cuenta-corporativa-qa-2026-10-22.txt` | Aprovisionamiento de tenant empresarial y roles corporativos. |
| **RF-23** (SCRUM-73) | Solicitud de Servicio Corporativa | `ServiceRequest` | **Probada (E2E QA)** | `tests/e2e/evidencias/scrum-75-solicitud-empresa-qa-2026-10-22.txt` | Creación de solicitud con cargo a centro de costos empresarial. |
| **RF-24** (SCRUM-96) | Carga de Evidencia Fotográfica en S3 | `ServiceRequest` | **Probada (E2E QA)** | `tests/e2e/evidencias/scrum-96-evidencia-qa-2026-10-22.txt` | Subida de imágenes a Garage S3 (VM7) requerida para cierre de orden. |
| **RF-25** (SCRUM-458) | Geocodificación y Validación Espacial | `ServiceRequest` | **Probada (E2E QA)** | `tests/e2e/evidencias/scrum-458-geocodificacion-buzon-qa-2026-10-22.txt` | Resolución de coordenadas en perímetro urbano de Bogotá. |
| **RF-26** (SCRUM-483) | Chat Bidireccional Cliente-Técnico | `Communication` | **Probada (E2E QA)** | `tests/e2e/evidencias/scrum-483-chat-qa-2026-10-22.txt` | Mensajería de texto transaccional asociada al ciclo de la orden. |
| **RF-27** (SCRUM-490) | Cotización de Servicio con Tarifa Base | `ServiceRequest` | **Probada (E2E QA)** | `tests/e2e/evidencias/scrum-490-cotizacion-qa-2026-10-22.txt` | Estimación de precio previa a la confirmación de la solicitud. |
| **RF-28** (SCRUM-614) | Edición de Perfil de Usuario | `Identity` | **No desarrollada** | *(Sin archivo de evidencia)* | Endpoint y formularios de actualización de perfil no implementados. |
| **RF-29** (SCRUM-627) | Recuperación de Contraseña por Correo | `Identity` | **No desarrollada** | *(Sin archivo de evidencia)* | Flujo de reset de credenciales por email no implementado. |
| **RF-30** (SCRUM-24) | Aislamiento Lógico por Tenant (RLS) | Persistencia / `All` | **Probada (E2E QA)** | `tests/e2e/evidencias/scrum-108-aprobacion-rechazo-qa-2026-10-22.txt` | Políticas Row-Level Security en PostgreSQL VM5; respuesta HTTP 404. |
| **RF-31** (SCRUM-24) | Control de Acceso Basado en Roles (RBAC) | `Gateway` / `All` | **Probada (E2E QA)** | `tests/e2e/evidencias/scrum-56-registro-tecnico-qa-2026-10-22.txt` | Bloqueo con HTTP 403 Forbidden ante invocaciones no autorizadas. |
| **RF-32** (SCRUM-478) | Avisos en Tiempo Real (WebSocket) | `Communication` | **Probada (E2E QA)** | `tests/e2e/evidencias/scrum-478-aviso-tiempo-real-qa-2026-10-22.txt` | Difusión de eventos de asignación y cambio de estado vía WS. |

---

## 3. Resumen Cuantitativo de Funcionalidades

* **Total de Funcionalidades Evaluadas:** **32 Requisitos Funcionales**.
* **Probadas y Certificadas en QA Real (E2E):** **26 funcionalidades (81.3%)**.
* **Probadas con Mocks / Sandbox (Pagos):** **2 funcionalidades (6.2%)** (RF-06 y RF-07).
* **No Desarrolladas / Pendientes:** **4 funcionalidades (12.5%)** (Calificación RF-12, Reputación/Ranking RF-21, Editar Perfil RF-28, Recuperar Contraseña RF-29).
