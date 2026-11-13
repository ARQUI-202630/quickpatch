# Matriz de Funcionalidades y Cobertura SRS V5.6 (SCRUM-561)

**Código del Documento:** `MTX-FUNC-SRS-V5.6-2026-10-26`  
**Versión:** `4.0` (estado al 12 de noviembre de 2026, SCRUM-701)  
**Fecha:** 26 de octubre de 2026 (versión 4.0: 12 de noviembre de 2026)  
**Responsable:** Katherine Bravo (`ka.bravo@javeriana.edu.co`) — QA Lead  
**Trazabilidad Jira:** Tarea `SCRUM-561` | SRS v5.6 (33 RFs canónicos: RF-01 a RF-29 y RF-34 a RF-37) | `TD.md` V3.3 | Indicadores: [`indicadores-funcionales.md`](indicadores-funcionales.md) (SCRUM-700)  
**Ambiente:** QA Desplegado (`https://qa.quickpatch.internal` en VM2 k3s)  

---

## 1. Convenciones y Estándar de Clasificación

Conforme a la directriz de arquitectura y el estándar del SRS v5.6:
* **Implementado / Aprobado (E2E QA):** Funcionalidad desplegada en el clúster de QA y certificada mediante suites automáticas con archivo de corrida en el repositorio.
* **Implementado (mock) / Aprobado:** Funcionalidad validada en flujos de prueba contra pasarela simulada o sandbox (ej. Pagos conforme a RN-P6 y ADR-009).
* **Parcial / Aprobado con observaciones:** Flujo verificado en componentes principales con alguna sub-acción o integración pendiente de completar.
* **No implementado / Sin probar:** Requisito del SRS cuya lógica no ha sido desarrollada o que no tiene evidencia en QA. Al 12 de noviembre no queda ningún RF en este estado.
* **Alcance:** Los números RF-30 a RF-33 fueron retirados formalmente en el SRS v3.0 y sus identificadores no se reutilizan.

---

## 2. Matriz Oficial de Cobertura de Requisitos Funcionales (SRS v5.6)

| ID | Módulo | Descripción del Requisito Funcional (SRS v5.6 §5) | Estado Desarrollo | Resultado QA | Archivo de Evidencia (Ruta Relativa del Repositorio) | Observaciones Técnicas |
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
| **RF-10** | Solicitudes y Matching | Técnico acepta o rechaza la oferta antes de 3 min; si no, pasa al siguiente | Implementado | Aprobado con obs. | `tests/e2e/evidencias/rf-10-vencimiento-oferta-qa-2026-11-05.md` (PR #269); `tests/e2e/evidencias/scrum-incremento-tecnico-qa-2026-11-04.txt` | La oferta vence a los 179 s y pasa al siguiente técnico; aceptar la vencida da 409. Aceptado por la PO con observaciones: no se probó el caso sin más técnicos. |
| **RF-11** | Seguimiento y Calificación | Estado de la solicitud en tiempo real (mín. 4 estados) | Implementado | Aprobado | `tests/e2e/evidencias/scrum-84-seguimiento-estado-qa-2026-10-22.txt`; `tests/e2e/evidencias/scrum-478-aviso-tiempo-real-qa-2026-10-22.txt` | Transiciones de estado auditadas y eventos WebSocket en tiempo real. |
| **RF-12** | Seguimiento y Calificación | Calificar el servicio (1–5 + comentario) una vez, tras el pago | Implementado | Aprobado | `tests/e2e/evidencias/scrum-639-calificacion-detalle-qa-2026-11-05.txt` (142 aserciones); `tests/e2e/evidencias/scrum-32-calificacion-qa-2026-11-04.txt` | Calificación 1–5 tras el pago (ServiceRequest 0.12.0) y estrellas en la app (APK `v0.5.5-qa`). |
| **RF-13** | Ejecución de Servicios | Técnico cambia disponibilidad y zona de cobertura (localidades) | Implementado | Aprobado | `tests/e2e/evidencias/scrum-incremento-tecnico-qa-2026-10-22.txt` | Conmutación operativa y actualización de polígonos de cobertura. |
| **RF-14** | Ejecución de Servicios | Detalle completo de la solicitud asignada al técnico | Implementado | Aprobado | `tests/e2e/evidencias/scrum-incremento-tecnico-qa-2026-10-22.txt` (bloque 3.1 DTL-001) | Técnico asignado ve teléfono y dirección (RN-SR13). Terceros reciben 403. |
| **RF-15** | Ejecución de Servicios | Completar la solicitud solo con evidencia fotográfica | Implementado | Aprobado | `tests/e2e/evidencias/scrum-96-evidencia-qa-2026-10-22.txt` (71 aserciones) | Subida obligatoria de fotografía a Garage S3 (VM7) para cierre de orden. |
| **RF-16** | Gestión de Equipos | Proveedor registra y administra su equipo de técnicos | Implementado | Aprobado | `tests/e2e/evidencias/scrum-99-equipo-proveedor-qa-2026-10-22.txt` (43 aserciones) | Alta, activación y listado de técnicos del proveedor certificados. |
| **RF-17** | Ejecución de Servicios | Historial de solicitudes atendidas por el técnico | Implementado | Aprobado | `tests/e2e/evidencias/scrum-37-historial-qa-2026-11-04.txt` (105 aserciones) | `GET /v1/technicians/me/service-requests` probado contra QA, con fuga desde Beta (404). |
| **RF-18** | Administración | Panel de solicitudes activas por estado (tenant / todos los tenants) | Implementado | Aprobado | `tests/e2e/evidencias/scrum-105-panel-operativo-qa-2026-10-22.txt` (35 aserciones) | Monitoreo operacional de solicitudes en curso por tenant. |
| **RF-19** | Administración | Aprobar o rechazar con motivo técnicos/proveedores (auditado) | Implementado | Aprobado | `tests/e2e/evidencias/scrum-108-aprobacion-rechazo-qa-2026-10-22.txt` | Aprobación con motivo auditado y publicación de evento Kafka outbox. |
| **RF-20** | Administración | Suspender la cuenta de un técnico (fecha y responsable) | Implementado | Aprobado | `tests/e2e/evidencias/scrum-111-suspension-tecnico-qa-2026-10-22.txt` (39 aserciones) | Suspensión motivada con fecha, actor responsable y bloqueo en matching. |
| **RF-21** | Administración | Activar/desactivar tenants con confirmación y auditoría | Implementado | Aprobado | `tests/e2e/evidencias/scrum-511-tenant-desactivado-qa-2026-11-04.txt` (24 aserciones) | Activar y desactivar probado contra QA, con el rechazo del tenant desactivado (RN-T1) y auditoría en Identity. |
| **RF-22** | Pagos | Pago con tarjeta de la cotización aceptada (pasarela PCI-DSS) | Implementado (mock) | Aprobado | `tests/e2e/evidencias/scrum-117-pago-qa-2026-10-22.txt` (57 aserciones) | Pasarela simulada sandbox sin tocar datos de tarjeta reales (ADR-009). |
| **RF-23** | Pagos | Pago a nombre de la cuenta corporativa | Implementado (mock) | Aprobado | `tests/e2e/evidencias/scrum-496-pago-empresa-qa-2026-11-04.txt` (59 aserciones) | Pago corporativo con otro usuario de la empresa (RN-P6), con la pasarela simulada (ADR-009). |
| **RF-24** | Pagos | Comprobante automático al confirmarse el pago | Implementado | Aprobado | `tests/e2e/evidencias/scrum-495-comprobante-qa-2026-10-22.txt` (42 aserciones) | Emisión digital con desglose de servicios y correlation-id (DR-03). |
| **RF-25** | Pagos | Registro de pagos recibidos para Técnico/Proveedor | Implementado | Aprobado | `tests/e2e/evidencias/scrum-45-pagos-tecnico-qa-2026-11-04.txt` (111 aserciones) | `GET /v1/payments/received` para técnico y proveedor (Payments `release/0.3.0`) y «Mis pagos» en la app. |
| **RF-26** | CI/CD | Pipeline CI/CD con build y pruebas antes de desplegar | Implementado | Aprobado | GitHub Actions (8 repos backend, runs oficiales #57, #68, etc.) | Pipelines automatizados en GitHub Actions: 1,525 pruebas unitarias y de integración con 0 fallos (SCRUM-602) y el workflow `pruebas-sistema.yml` en verde (run 41935076005). |
| **RF-27** | CI/CD | Prueba E2E automática del flujo crítico (solicitud $\to$ … $\to$ pago $\to$ calificación) | Implementado | Aprobado | `tests/e2e/evidencias/humo-flujo-critico-qa-2026-11-11.txt` (29 aserciones) | Flujo crítico de punta a punta en QA, incluida la calificación. |
| **RF-28** | Logging y Monitoreo | Logs centralizados con correlation-id + alertas de caída | Implementado | Aprobado | `tests/e2e/evidencias/rf-28-alerta-de-caida-y-logs-qa-2026-11-05.md` (PR #269); `tests/security/evidencias/pci-dss-loki-qa-sprint5-2026-11-04.md` | Alerta `qp-vm-caida` disparada en QA (correo a los 3 min 40 s) y un 403 encontrado en Loki por su correlationId. |
| **RF-29** | Seguridad | Cifrado en tránsito (TLS) y contraseñas con hash | Implementado | Aprobado | `tests/security/evidencias/tls-ingress-qa-2026-10-27.txt`; `tests/ci-results/identity/` (Run #57) | Nginx Ingress fuerza TLSv1.3 (certificado RSA 4096-bit); Identity aplica BCrypt para hash de credenciales e invitaciones (18 pruebas en CI run #57). |
| **RF-34** | Ejecución de Servicios | Técnico emite cotización (mano de obra + materiales) | Implementado | Aprobado | `tests/e2e/evidencias/scrum-490-cotizacion-qa-2026-10-22.txt` (76 aserciones) | Desglose formal de cotización previa al inicio de labores. |
| **RF-35** | Solicitudes y Matching | Cliente acepta/rechaza la cotización (máx. 3; vence) | Implementado | Aprobado | `tests/e2e/evidencias/scrum-490-cotizacion-qa-2026-10-22.txt` | Aceptación con avance de estado o rechazo controlado por el cliente. |
| **RF-36** | Solicitudes y Matching | Cancelar la solicitud antes de iniciar, con motivo | Implementado | Aprobado | `tests/e2e/evidencias/scrum-478-cancelacion-qa-2026-10-19.txt` (63 aserciones) | Cancelación justificada y liberación de recursos en matching. |
| **RF-37** | Seguimiento y Calificación | Chat Cliente–Técnico dentro de la solicitud, en tiempo real | Implementado | Aprobado | `tests/e2e/evidencias/scrum-483-chat-qa-2026-10-22.txt` (69 aserciones) | Canal bidireccional transaccional por WebSocket asociado a la orden. |
| **EXT-01** | Usuarios y Cuentas | Editar perfil (comentario del profesor) | Implementado | Aprobado | `tests/e2e/evidencias/scrum-614-perfil-qa-2026-11-04.txt` (102 aserciones) | RF-39 propuesto en el SRS 5.11, sección 7.6. Aceptado por la PO; se reporta aparte de los 33 RF. |
| **EXT-02** | Interacción (AC4) | Navegación consistente: botón de volver en todas las pantallas | Implementado | Aprobado | `tests/e2e/evidencias/scrum-618-navegacion-capturas-qa-2026-11-04/` (23 capturas, PR #267) | Botón atrás verificado en QA con el APK `v0.5.5-qa`. Aceptado por la PO. |
| **EXT-03** | Landing / Release | Descargar el APK desde la landing (pedido del profesor) | Implementado | Aprobado | `quickpatch-mobile releases/tag/v0.5.4-qa` | La descarga 302 → 200 desde la landing se verificó con `v0.5.1-qa` y no se repitió. Aceptado por la PO. |
| **EXT-04** | Usuarios y Cuentas | Recuperar la contraseña con enlace generado por el administrador (SCRUM-623) | Implementado | Aprobado | `tests/e2e/evidencias/scrum-627-recuperacion-qa-2026-11-04.txt` (118 aserciones); `tests/e2e/evidencias/scrum-627-enlace-vencido-qa-2026-11-04.txt` | RF-38 propuesto en el SRS 5.11, sección 7.6. Aceptado por la PO; se reporta aparte de los 33 RF. |

---

## 3. Resumen Cuantitativo Consolidado

Corte del 12 de noviembre de 2026. Los cuatro indicadores se definen y se calculan en [`indicadores-funcionales.md`](indicadores-funcionales.md), con `python scripts/calcular_indicadores_qa.py`.

* **Requisitos Funcionales Oficiales (SRS v5.6):** **33**.
* **Implementados en develop y desplegados en QA:** **33 (100%)**. RF-22 y RF-23 usan la pasarela simulada (ADR-009).
* **Verificados en QA con evidencia:** **33 (100%)**. 32 aprobados y 1 aprobado con observaciones (RF-10, el caso sin más técnicos).
* **Aceptados por la Product Owner en UAT:** **33 (100%)**, según el Informe UAT del 5 de noviembre y el acta (PR #272).
* **Extensiones fuera del SRS:** **4** (EXT-01 a EXT-04), implementadas, verificadas y aceptadas. Se reportan aparte. EXT-01 y EXT-04 corresponden a RF-39 y RF-38, que están propuestos.

**Cambios frente a la versión 3.0 (26 de octubre):** RF-12, RF-17, RF-21 y RF-25 pasan de Sin probar a Aprobado. RF-27 y RF-28 pasan de Aprobado con observaciones a Aprobado. EXT-01 y EXT-02 pasan a Aprobado, y se agrega EXT-04. En la versión 3.0 el resumen daba 26 RF aprobados, 3 con observaciones y 4 sin probar.
