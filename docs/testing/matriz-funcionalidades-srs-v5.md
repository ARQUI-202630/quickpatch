# Matriz de Funcionalidades y Cobertura SRS V5.5 (SCRUM-561)

**Código del Documento:** `MTX-FUNC-SRS-V5.5-2026-10-26`  
**Versión:** `3.0 Final Sincronizada`  
**Fecha:** 26 de octubre de 2026  
**Responsable:** Katherine Bravo (`ka.bravo@javeriana.edu.co`) — QA Lead  
**Trazabilidad Jira:** Tarea `SCRUM-561` | SRS v5.5 (33 RFs canónicos: RF-01 a RF-29 y RF-34 a RF-37) | `TD.md` V3.0  
**Ambiente:** QA Desplegado (`https://qa.quickpatch.internal` en VM2 k3s)  

---

## 1. Convenciones y Estándar de Clasificación

Conforme a la directriz de arquitectura y el estándar del SRS v5.5:
* **Implementado / Aprobado (E2E QA):** Funcionalidad desplegada en el clúster de QA y certificada mediante suites automáticas con archivo de corrida en el repositorio.
* **Implementado (mock) / Aprobado:** Funcionalidad validada en flujos de prueba contra pasarela simulada o sandbox (ej. Pagos conforme a RN-P6 y ADR-009).
* **Parcial / Aprobado con observaciones:** Flujo verificado en componentes principales con alguna sub-acción o integración pendiente de completar.
* **No implementado / Sin probar:** Requisito del SRS cuya lógica no ha sido desarrollada aún (ej. Ranking/Calificación RF-12 y registro de pagos recibidos RF-25).
* **Alcance:** Los números RF-30 a RF-33 fueron retirados formalmente en el SRS v3.0 y sus identificadores no se reutilizan.

---

## 2. Matriz Oficial de Cobertura de Requisitos Funcionales (SRS v5.5)

| ID | Módulo | Descripción del Requisito Funcional (SRS v5.5 §5) | Estado Desarrollo | Resultado QA | Archivo de Evidencia (Ruta Relativa del Repositorio) | Observaciones Técnicas |
|:---:|---|---|:---:|:---:|---|---|
| **RF-01** | Usuarios y Cuentas | Registro de Cliente (correo, contraseña $\ge 8$, correo único en el tenant) | Implementado | Aprobado | `tests/e2e/evidencias/tenant-beta-qa-2026-10-15.txt`; `tests/e2e/evidencias/mvp-qa-sprint4-2026-10-18.txt` | Creación de cuenta, hashing BCrypt y unicidad validada. |
| **RF-02** | Usuarios y Cuentas | Registro de Técnico/Proveedor con documentos $\to$ 'Pendiente de verificación' | Implementado | Aprobado | `tests/e2e/evidencias/scrum-56-registro-tecnico-qa-2026-10-22.txt` (23 aserciones) | Registro validado contra QA desplegado con RFC 9457 Problem Details. |
| **RF-03** | Usuarios y Cuentas | Inicio de sesión de todos los roles + bloqueo tras 5 intentos fallidos | Implementado | Aprobado | `tests/e2e/evidencias/mvp-qa-sprint4-2026-10-18.txt` (bloque fuerza bruta) | Respuesta HTTP 423 Locked tras 5 intentos fallidos (RN-U4). |
| **RF-04** | Multi-tenancy | Aislamiento de datos por tenant (`tenant_id` del usuario autenticado) | Implementado | Aprobado | `tests/e2e/evidencias/scrum-108-aprobacion-rechazo-qa-2026-10-22.txt`; `tests/e2e/evidencias/tenant-beta-qa-2026-10-15.txt` | RLS en PostgreSQL VM5; intentos cross-tenant retornan HTTP 404. |
| **RF-05** | Seguridad | Acceso por rol y por canal (panel solo admins; app el resto) | Implementado | Aprobado | `tests/e2e/evidencias/scrum-56-registro-tecnico-qa-2026-10-22.txt`; `tests/e2e/evidencias/scrum-105-panel-operativo-qa-2026-10-22.txt` | Bloqueo HTTP 403 Forbidden ante accesos no autorizados por RBAC. |
| **RF-06** | Usuarios y Cuentas | Cuenta corporativa de Empresa con varios usuarios autorizados | Implementado | Aprobado | `tests/e2e/evidencias/scrum-68-cuenta-corporativa-qa-2026-10-22.txt` (68 aserciones) | Alta de tenant corporativo y gestión de miembros multi-usuario. |
| **RF-07** | Solicitudes y Matching | Crear solicitud (categoría, ubicación GPS o dirección geocodificada en Bogotá, descripción) | Implementado | Aprobado | `tests/e2e/evidencias/scrum-458-geocodificacion-buzon-qa-2026-10-22.txt` | Geocodificación urbana y asignación con radio geoespacial PostGIS. |
| **RF-08** | Solicitudes y Matching | Solicitud de servicio a nombre de la Empresa (sedes) | Implementado | Aprobado | `tests/e2e/evidencias/scrum-75-solicitud-empresa-qa-2026-10-22.txt` (56 aserciones) | Creación de solicitud con asignación a sede empresarial. |
| **RF-09** | Solicitudes y Matching | Asignación automática de técnico (matching por especialidad, zona y cercanía) | Implementado | Aprobado | `tests/e2e/evidencias/scrum-78-qa-2026-10-22.txt` | Algoritmo PostGIS; latencia percentil 95 p95 = 73.55 ms en carga 50 VU. |
| **RF-10** | Solicitudes y Matching | Técnico acepta o rechaza la oferta antes de 3 min; si no, pasa al siguiente | Implementado | Aprobado con obs. | `tests/e2e/evidencias/scrum-incremento-tecnico-qa-2026-10-22.txt` (bloques 2.3 y 2.6) | Aceptación atómica (OFF-004) y rechazo explícito (OFF-002) verificados; vencimiento a los 3 min pendiente de prueba de reloj. |
| **RF-11** | Seguimiento y Calificación | Estado de la solicitud en tiempo real (mín. 4 estados) | Implementado | Aprobado | `tests/e2e/evidencias/scrum-84-seguimiento-estado-qa-2026-10-22.txt`; `tests/e2e/evidencias/scrum-478-aviso-tiempo-real-qa-2026-10-22.txt` | Transiciones de estado auditadas y eventos WebSocket en tiempo real. |
| **RF-12** | Seguimiento y Calificación | Calificar el servicio (1–5 + comentario) una vez, tras el pago | No implementado | Sin probar | *(Sin archivo de evidencia)* | Ranking es un esqueleto con 8 pruebas; sin endpoint de calificación. |
| **RF-13** | Ejecución de Servicios | Técnico cambia disponibilidad y zona de cobertura (localidades) | Implementado | Aprobado | `tests/e2e/evidencias/scrum-incremento-tecnico-qa-2026-10-22.txt` | Conmutación operativa y actualización de polígonos de cobertura. |
| **RF-14** | Ejecución de Servicios | Detalle completo de la solicitud asignada al técnico | Implementado | Aprobado | `tests/e2e/evidencias/scrum-incremento-tecnico-qa-2026-10-22.txt` (bloque 3.1 DTL-001) | Técnico asignado ve teléfono y dirección (RN-SR13). Terceros reciben 403. |
| **RF-15** | Ejecución de Servicios | Completar la solicitud solo con evidencia fotográfica | Implementado | Aprobado | `tests/e2e/evidencias/scrum-96-evidencia-qa-2026-10-22.txt` (71 aserciones) | Subida obligatoria de fotografía a Garage S3 (VM7) para cierre de orden. |
| **RF-16** | Gestión de Equipos | Proveedor registra y administra su equipo de técnicos | Implementado | Aprobado | `tests/e2e/evidencias/scrum-99-equipo-proveedor-qa-2026-10-22.txt` (43 aserciones) | Alta, activación y listado de técnicos del proveedor certificados. |
| **RF-17** | Ejecución de Servicios | Historial de solicitudes atendidas por el técnico | Implementado | Sin probar | *(Sin archivo de evidencia)* | Endpoint `GET /v1/technicians/me/service-requests` pendiente de prueba E2E dedicada (scrum-105 es panel admin). |
| **RF-18** | Administración | Panel de solicitudes activas por estado (tenant / todos los tenants) | Implementado | Aprobado | `tests/e2e/evidencias/scrum-105-panel-operativo-qa-2026-10-22.txt` (35 aserciones) | Monitoreo operacional de solicitudes en curso por tenant. |
| **RF-19** | Administración | Aprobar o rechazar con motivo técnicos/proveedores (auditado) | Implementado | Aprobado | `tests/e2e/evidencias/scrum-108-aprobacion-rechazo-qa-2026-10-22.txt` | Aprobación con motivo auditado y publicación de evento Kafka outbox. |
| **RF-20** | Administración | Suspender la cuenta de un técnico (fecha y responsable) | Implementado | Aprobado | `tests/e2e/evidencias/scrum-111-suspension-tecnico-qa-2026-10-22.txt` (39 aserciones) | Suspensión motivada con fecha, actor responsable y bloqueo en matching. |
| **RF-21** | Administración | Activar/desactivar tenants con confirmación y auditoría | Implementado | Sin probar | *(Sin archivo de evidencia)* | Aislamiento verificado en tenant-beta; activación/desactivación administrativa pendiente de prueba contra QA. |
| **RF-22** | Pagos | Pago con tarjeta de la cotización aceptada (pasarela PCI-DSS) | Implementado (mock) | Aprobado | `tests/e2e/evidencias/scrum-117-pago-qa-2026-10-22.txt` (57 aserciones) | Pasarela simulada sandbox sin tocar datos de tarjeta reales (ADR-009). |
| **RF-23** | Pagos | Pago a nombre de la cuenta corporativa | Implementado | Aprobado | `tests/e2e/evidencias/scrum-496-pago-empresa-qa-2026-10-27.txt` (59 aserciones, 27-oct) | Pago corporativo con usuario empresa_contacto verificado conforme a RN-P6 (SCRUM-118 y SCRUM-496). |
| **RF-24** | Pagos | Comprobante automático al confirmarse el pago | Implementado | Aprobado | `tests/e2e/evidencias/scrum-495-comprobante-qa-2026-10-22.txt` (42 aserciones) | Emisión digital con desglose de servicios y correlation-id (DR-03). |
| **RF-25** | Pagos | Registro de pagos recibidos para Técnico/Proveedor | No implementado | Sin probar | *(Sin archivo de evidencia)* | Payments no implementa aún el endpoint `/payments/received` (Sp5/futuro). |
| **RF-26** | CI/CD | Pipeline CI/CD con build y pruebas antes de desplegar | Implementado | Aprobado | GitHub Actions (8 repos backend, runs oficiales #57, #68, etc.) | Pipelines automatizados en GitHub Actions con 1.032 pruebas backend PASS. |
| **RF-27** | CI/CD | Prueba E2E automática del flujo crítico (solicitud $\to$ … $\to$ pago $\to$ calificación) | Parcial | Aprobado con obs. | `tests/e2e/evidencias/scrum-incremento-tecnico-qa-2026-10-22.txt`; `tests/e2e/evidencias/scrum-117-pago-qa-2026-10-22.txt` | Flujo verificado hasta pago y comprobante; pendiente únicamente calificación. |
| **RF-28** | Logging y Monitoreo | Logs centralizados con correlation-id + alertas de caída | Implementado | Aprobado con obs. | `tests/security/evidencias/pci-dss-loki-qa-2026-10-18.txt` | Trazas estructuradas en Loki con correlation-id; alertas en configuración. |
| **RF-29** | Seguridad | Cifrado en tránsito (TLS) y contraseñas con hash | Implementado | Aprobado | `openssl s_client -connect qa.quickpatch.internal:443` (TLSv1.3); Identity CI run #57 | Nginx Ingress fuerza TLS 1.2/1.3; Identity aplica BCrypt para hash de credenciales (18 tests CI). |
| **RF-34** | Ejecución de Servicios | Técnico emite cotización (mano de obra + materiales) | Implementado | Aprobado | `tests/e2e/evidencias/scrum-490-cotizacion-qa-2026-10-22.txt` (76 aserciones) | Desglose formal de cotización previa al inicio de labores. |
| **RF-35** | Solicitudes y Matching | Cliente acepta/rechaza la cotización (máx. 3; vence) | Implementado | Aprobado | `tests/e2e/evidencias/scrum-490-cotizacion-qa-2026-10-22.txt` | Aceptación con avance de estado o rechazo controlado por el cliente. |
| **RF-36** | Solicitudes y Matching | Cancelar la solicitud antes de iniciar, con motivo | Implementado | Aprobado | `tests/e2e/evidencias/scrum-478-cancelacion-qa-2026-10-19.txt` (63 aserciones) | Cancelación justificada y liberación de recursos en matching. |
| **RF-37** | Seguimiento y Calificación | Chat Cliente–Técnico dentro de la solicitud, en tiempo real | Implementado | Aprobado | `tests/e2e/evidencias/scrum-483-chat-qa-2026-10-22.txt` (69 aserciones) | Canal bidireccional transaccional por WebSocket asociado a la orden. |
| **EXT-01** | Usuarios y Cuentas | Editar perfil (comentario del profesor) | No implementado | Sin probar | *(Sin archivo de evidencia)* | No especificado formalmente en SRS; pendiente definición de PO. |
| **EXT-02** | Interacción (AC4) | Navegación consistente: botón de volver en todas las pantallas | Parcial | Sin probar | `tests/e2e/evidencias/humo-qa-2026-10-19/` | Botón de retorno implementado en pantallas principales del flujo. |
| **EXT-03** | Landing / Release | Descargar el APK desde la landing (pedido del profesor) | Implementado | Aprobado | `quickpatch-mobile releases/tag/v0.5.1-qa` (55.25 MB, HTTP 200 OK) | Descarga directa de `quickpatch.apk` verificada vía HTTP 302 $\to$ 200 OK. |

---

## 3. Resumen Cuantitativo Consolidado

* **Total de Requisitos Funcionales Oficiales (SRS v5.5):** **33 Requisitos Funcionales**.
* **Requisitos Aprobados en QA:** **26 RFs (78.8%)** (incluye pagos corporativos SCRUM-496 y pasarela simulada ADR-009).
* **Requisitos Aprobados con Observaciones:** **3 RFs (9.1%)** (RF-10 vencimiento 3 min, RF-27 flujo E2E sin calificación, RF-28 alertas).
* **Requisitos Sin Probar / No Implementados:** **4 RFs (12.1%)** (RF-12 Calificación, RF-17 Historial técnico, RF-21 Activar/Desactivar tenant, RF-25 Registro de Pagos).
* **Extensiones Adicionales Auditadas:** **3 ítems** (EXT-03 Aprobada en landing; EXT-01 y EXT-02 pendientes).
