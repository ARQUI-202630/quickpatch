# Inventario de funcionalidades por tipo de usuario — QUICKPATCH

**Historia:** SCRUM-559 (matriz de funcionalidades por tipo de usuario y avance real). **Esta tarea:** SCRUM-560 (inventario).
**Fecha de corte del inventario:** 27 de octubre de 2026, sobre `develop` de `quickpatch-mobile`, `quickpatch-web` y el SRS V5.6.
**Siguientes pasos:** SCRUM-561 (Katherine) llena las columnas de estado con su evidencia, y SCRUM-562 calcula el avance.

## Cómo se armó

- **Del SRS:** cada RF (RF-01 a RF-29 y RF-34 a RF-37, 33 en total) queda en al menos una fila, con la HU que el SRS le asigna (sección 3, columna HU). Los RF que no son de un usuario sino del sistema van en "Transversal".
- **De la app y del panel:** se revisaron las pantallas de `quickpatch-mobile` (`lib/features/**/paginas/`), las rutas de `quickpatch-web` (`src/app/app.routes.ts`) y las llamadas a la API de cada una. Así entran las funcionalidades básicas que el SRS no nombra como RF: cerrar sesión, editar el perfil, recuperar la contraseña, activar la cuenta y el buzón de notificaciones.
- **Columna "Qué hay hoy":** describe lo que existe en el código, sin juzgar si funciona. Que una pantalla exista no la hace "Desarrollada" ni "Probada"; eso lo decide SCRUM-561 con evidencia.
- **Columnas de estado** (las llena SCRUM-561, con los criterios de SCRUM-559):
  - **Desarrollada:** sí / parcial / no.
  - **Probada:** enlace a la evidencia de QA (`tests/e2e/evidencias/`, CI o captura). Sin enlace, no cuenta como probada.
  - **Producción:** desplegada en producción (Documento de Infraestructura, 4.3).
  - **Mock:** funciona con un simulador (por ejemplo, la pasarela de pagos, ADR-009 modificado).
  - **Pendiente:** lo que falta.

Una funcionalidad que comparten varios usuarios se repite en cada uno, porque el avance se calcula por usuario. Las filas repetidas llevan la misma evidencia.

## 1. Visitante de la landing (panel web, sin sesión)

| ID | Módulo | Funcionalidad | RF | HU | Qué hay hoy | Desarrollada | Probada (evidencia) | Producción | Mock | Pendiente |
|---|---|---|---|---|---|---|---|---|---|---|
| V-01 | Presentación | Ver la página de presentación de QUICKPATCH | — (SRS 5.3) | SCRUM-491 | Panel: ruta `''` (`presentacion`) | Sí | No | No | No | Sí (pendiente de prueba de interfaz en QA; scrum-105 prueba API del panel) |
| V-02 | Presentación | Descargar el APK de la app | — | SCRUM-628 | Panel: botón de descarga de `presentacion` hacia el último release | Sí | No | No | No | Sí (SCRUM-628 descarga existe sin prueba en QA) |

## 2. Cliente hogar (app móvil)

| ID | Módulo | Funcionalidad | RF | HU | Qué hay hoy | Desarrollada | Probada (evidencia) | Producción | Mock | Pendiente |
|---|---|---|---|---|---|---|---|---|---|---|
| C-01 | Cuenta | Registrarse con correo y contraseña | RF-01 | SCRUM-21 | `registro_page` → `POST /v1/auth/register/client` | Sí | Sí ([mvp-qa-sprint4-2026-10-18.txt](../../tests/e2e/evidencias/mvp-qa-sprint4-2026-10-18.txt)) | No | No | No |
| C-02 | Cuenta | Iniciar sesión, con bloqueo tras 5 intentos | RF-03 | SCRUM-23 | `inicio_sesion_page` → `POST /v1/auth/login` | Sí | Sí ([mvp-qa-sprint4-2026-10-18.txt](../../tests/e2e/evidencias/mvp-qa-sprint4-2026-10-18.txt)) | No | No | No |
| C-03 | Cuenta | Cerrar sesión | — | — | `cuenta_page`, botón "Cerrar sesión" | Sí | No | No | No | Sí (cerrar sesión es de la app, sin prueba de interfaz en QA) |
| C-04 | Cuenta | Editar el perfil propio | — | SCRUM-609 | Sin pantalla; `PATCH /v1/users/me` en QA desde el 27 de octubre (identity 0.6.0, SCRUM-611) | Parcial | No | No | No | Sí (pantallas SCRUM-612 y SCRUM-613, QA SCRUM-614) |
| C-05 | Cuenta | Recuperar la contraseña | — | SCRUM-623 | Sin pantalla; contrato en diseño (SCRUM-624) | No | No | No | No | Sí (SCRUM-623; contrato SCRUM-624 y pantalla UI) |
| C-06 | Solicitudes | Crear una solicitud con GPS o dirección escrita | RF-07 | SCRUM-27 | `nueva_solicitud_page` → `location-preview` y `POST /v1/service-requests` | Sí | Sí ([scrum-75-solicitud-empresa-qa-2026-10-22.txt](../../tests/e2e/evidencias/scrum-75-solicitud-empresa-qa-2026-10-22.txt)) | No | No | No |
| C-07 | Solicitudes | Ver sus solicitudes y el estado en tiempo real | RF-11 | SCRUM-31 | `mis_solicitudes_page`, `detalle_solicitud_page` y canal `/v1/realtime` | Sí | Sí ([scrum-84-seguimiento-estado-qa-2026-10-22.txt](../../tests/e2e/evidencias/scrum-84-seguimiento-estado-qa-2026-10-22.txt)) | No | No | No |
| C-08 | Solicitudes | Aceptar o rechazar la cotización | RF-35 | SCRUM-486 | `detalle_solicitud_page` → `quotes/{id}/accept` y `reject` | Sí | Sí ([scrum-490-cotizacion-qa-2026-10-22.txt](../../tests/e2e/evidencias/scrum-490-cotizacion-qa-2026-10-22.txt)) | No | No | No |
| C-09 | Solicitudes | Cancelar la solicitud con motivo | RF-36 | SCRUM-472 | `detalle_solicitud_page` → `POST /v1/service-requests/{id}/cancel` | Sí | Sí ([scrum-478-cancelacion-qa-2026-10-19.txt](../../tests/e2e/evidencias/scrum-478-cancelacion-qa-2026-10-19.txt)) | No | No | No |
| C-10 | Solicitudes | Chatear con el técnico asignado | RF-37 | SCRUM-473 | `chat_page` → `/v1/service-requests/{id}/messages` y canal en tiempo real | Sí | Sí ([scrum-483-chat-qa-2026-10-22.txt](../../tests/e2e/evidencias/scrum-483-chat-qa-2026-10-22.txt)) | No | No | No |
| C-11 | Notificaciones | Ver el buzón de notificaciones | RF-11 | — | `notificaciones_page` → `/v1/notifications` | Sí | Sí ([scrum-458-geocodificacion-buzon-qa-2026-10-22.txt](../../tests/e2e/evidencias/scrum-458-geocodificacion-buzon-qa-2026-10-22.txt)) | No | No | No |
| C-12 | Pagos | Pagar con tarjeta | RF-22 | SCRUM-42 | `pagar_page` → `POST /v1/service-requests/{id}/payment` (pasarela simulada) | Sí | Sí ([scrum-117-pago-qa-2026-10-22.txt](../../tests/e2e/evidencias/scrum-117-pago-qa-2026-10-22.txt)) | No | Sí | No |
| C-13 | Pagos | Ver el comprobante del pago | RF-24 | SCRUM-44 | `comprobante_page` → `GET /v1/payments/{id}/invoice` | Sí | Sí ([scrum-495-comprobante-qa-2026-10-22.txt](../../tests/e2e/evidencias/scrum-495-comprobante-qa-2026-10-22.txt)) | No | No | No |
| C-14 | Calificación | Calificar el servicio (1 a 5, una vez, después del pago) | RF-12 | SCRUM-32 | Ruta declarada en `api_endpoints.dart`, sin pantalla; backend planeado (ADR-027) | Parcial | No | No | No | Sí (backend fusionado SCRUM-85; faltan pantalla SCRUM-86 y QA SCRUM-87) |

## 3. Empresa cliente (usuario `empresa_contacto`, app móvil)

| ID | Módulo | Funcionalidad | RF | HU | Qué hay hoy | Desarrollada | Probada (evidencia) | Producción | Mock | Pendiente |
|---|---|---|---|---|---|---|---|---|---|---|
| E-01 | Cuenta | Registrar la cuenta corporativa (razón social, NIT y contacto) | RF-06 | SCRUM-26 | `registro_page` → `POST /v1/auth/register/company` | Sí | Sí ([scrum-68-cuenta-corporativa-qa-2026-10-22.txt](../../tests/e2e/evidencias/scrum-68-cuenta-corporativa-qa-2026-10-22.txt)) | No | No | No |
| E-02 | Cuenta | Agregar usuarios autorizados de la empresa | RF-06 | SCRUM-26 | `usuarios_empresa_page` y `agregar_usuario_empresa_page` → `/v1/companies/me/users` | Sí | Sí ([scrum-68-cuenta-corporativa-qa-2026-10-22.txt](../../tests/e2e/evidencias/scrum-68-cuenta-corporativa-qa-2026-10-22.txt)) | No | No | No |
| E-03 | Cuenta | Activar la cuenta por invitación (definir la contraseña) | RF-06 | SCRUM-26 | `activar_cuenta_page` → `POST /v1/auth/password/setup` | Sí | Sí ([scrum-68-cuenta-corporativa-qa-2026-10-22.txt](../../tests/e2e/evidencias/scrum-68-cuenta-corporativa-qa-2026-10-22.txt)) | No | No | No |
| E-04 | Cuenta | Iniciar sesión, con bloqueo tras 5 intentos | RF-03 | SCRUM-23 | `inicio_sesion_page` | Sí | Sí ([mvp-qa-sprint4-2026-10-18.txt](../../tests/e2e/evidencias/mvp-qa-sprint4-2026-10-18.txt)) | No | No | No |
| E-05 | Cuenta | Cerrar sesión | — | — | `cuenta_page` | Sí | No | No | No | Sí (cerrar sesión es de la app, sin prueba de interfaz en QA) |
| E-06 | Cuenta | Editar el perfil propio | — | SCRUM-609 | Igual que C-04 | Parcial | No | No | No | Sí (pantallas SCRUM-612 y SCRUM-613, QA SCRUM-614) |
| E-07 | Cuenta | Recuperar la contraseña | — | SCRUM-623 | Sin pantalla (SCRUM-624) | No | No | No | No | Sí (SCRUM-623; contrato SCRUM-624 y pantalla UI) |
| E-08 | Solicitudes | Crear una solicitud para una sede, a nombre de la empresa | RF-08 | SCRUM-28 | `nueva_solicitud_page` con el nombre de la sede | Sí | Sí ([scrum-75-solicitud-empresa-qa-2026-10-22.txt](../../tests/e2e/evidencias/scrum-75-solicitud-empresa-qa-2026-10-22.txt)) | No | No | No |
| E-09 | Solicitudes | Ver las solicitudes y el estado en tiempo real | RF-11 | SCRUM-31 | Las mismas pantallas de C-07 | Sí | Sí ([scrum-84-seguimiento-estado-qa-2026-10-22.txt](../../tests/e2e/evidencias/scrum-84-seguimiento-estado-qa-2026-10-22.txt)) | No | No | No |
| E-10 | Solicitudes | Aceptar o rechazar la cotización | RF-35 | SCRUM-486 | Igual que C-08 | Sí | Sí ([scrum-496-pago-empresa-qa-2026-10-27.txt](../../tests/e2e/evidencias/scrum-496-pago-empresa-qa-2026-10-27.txt)) | No | No | No |
| E-11 | Solicitudes | Cancelar la solicitud con motivo | RF-36 | SCRUM-472 | Igual que C-09 | Sí | Sí ([scrum-478-cancelacion-qa-2026-10-19.txt](../../tests/e2e/evidencias/scrum-478-cancelacion-qa-2026-10-19.txt)) | No | No | No |
| E-12 | Solicitudes | Chatear con el técnico asignado | RF-37 | SCRUM-473 | Igual que C-10 | Sí | Sí ([scrum-483-chat-qa-2026-10-22.txt](../../tests/e2e/evidencias/scrum-483-chat-qa-2026-10-22.txt)) | No | No | No |
| E-13 | Notificaciones | Ver el buzón de notificaciones | RF-11 | — | `notificaciones_page` | Sí | Sí ([scrum-458-geocodificacion-buzon-qa-2026-10-22.txt](../../tests/e2e/evidencias/scrum-458-geocodificacion-buzon-qa-2026-10-22.txt)) | No | No | No |
| E-14 | Pagos | Pagar a nombre de la cuenta corporativa | RF-23 | SCRUM-43 | `pagar_page`; paga cualquier usuario de la empresa (RN-P6) | Sí | Sí ([scrum-496-pago-empresa-qa-2026-10-27.txt](../../tests/e2e/evidencias/scrum-496-pago-empresa-qa-2026-10-27.txt)) | No | Sí | No |
| E-15 | Pagos | Ver el comprobante del pago | RF-24 | SCRUM-44 | `comprobante_page` | Sí | Sí ([scrum-496-pago-empresa-qa-2026-10-27.txt](../../tests/e2e/evidencias/scrum-496-pago-empresa-qa-2026-10-27.txt)) | No | No | No |
| E-16 | Calificación | Calificar el servicio | RF-12 | SCRUM-32 | Igual que C-14 | Parcial | No | No | No | Sí (backend fusionado SCRUM-85; faltan pantalla SCRUM-86 y QA SCRUM-87) |

## 4. Técnico (app móvil)

| ID | Módulo | Funcionalidad | RF | HU | Qué hay hoy | Desarrollada | Probada (evidencia) | Producción | Mock | Pendiente |
|---|---|---|---|---|---|---|---|---|---|---|
| T-01 | Cuenta | Registrarse con datos y documentos, en estado pendiente de verificación | RF-02 | SCRUM-22 | `registro_tecnico_page` → `POST /v1/auth/register/technician` | Sí | Sí ([scrum-56-registro-tecnico-qa-2026-10-22.txt](../../tests/e2e/evidencias/scrum-56-registro-tecnico-qa-2026-10-22.txt)) | No | No | No |
| T-02 | Cuenta | Activar la cuenta creada por su proveedor | RF-16 | SCRUM-36 | `activar_cuenta_page` | Sí | No | No | No | Sí (scrum-99 no llama a activación /v1/auth/password/setup en QA) |
| T-03 | Cuenta | Iniciar sesión, con bloqueo tras 5 intentos | RF-03 | SCRUM-23 | `inicio_sesion_page` | Sí | Sí ([mvp-qa-sprint4-2026-10-18.txt](../../tests/e2e/evidencias/mvp-qa-sprint4-2026-10-18.txt)) | No | No | No |
| T-04 | Cuenta | Cerrar sesión | — | — | `cuenta_page` | Sí | No | No | No | Sí (cerrar sesión es de la app, sin prueba de interfaz en QA) |
| T-05 | Cuenta | Editar el perfil propio | — | SCRUM-609 | Igual que C-04 | Parcial | No | No | No | Sí (pantallas SCRUM-612 y SCRUM-613, QA SCRUM-614) |
| T-06 | Cuenta | Recuperar la contraseña | — | SCRUM-623 | Sin pantalla (SCRUM-624) | No | No | No | No | Sí (SCRUM-623; contrato SCRUM-624 y pantalla UI) |
| T-07 | Disponibilidad | Cambiar la disponibilidad y la cobertura por localidades | RF-13 | SCRUM-33 | `disponibilidad_page` → `/v1/technicians/me/availability` y `coverage` | Sí | Sí ([scrum-incremento-tecnico-qa-2026-10-22.txt](../../tests/e2e/evidencias/scrum-incremento-tecnico-qa-2026-10-22.txt)) | No | No | No |
| T-08 | Ofertas | Recibir la oferta y aceptarla o rechazarla antes de 3 minutos | RF-10 | SCRUM-30 | `/v1/matching/offers`, `accept` y `reject` | Sí | Sí ([scrum-78-qa-2026-10-22.txt](../../tests/e2e/evidencias/scrum-78-qa-2026-10-22.txt)) | No | No | No |
| T-09 | Servicio | Ver el detalle de la solicitud asignada | RF-14 | SCRUM-34 | `solicitud_asignada_page` | Sí | Sí ([scrum-incremento-tecnico-qa-2026-10-22.txt](../../tests/e2e/evidencias/scrum-incremento-tecnico-qa-2026-10-22.txt)) | No | No | No |
| T-10 | Servicio | Emitir la cotización de mano de obra y materiales | RF-34 | SCRUM-486 | `solicitud_asignada_page` → `POST /v1/service-requests/{id}/quotes` | Sí | Sí ([scrum-490-cotizacion-qa-2026-10-22.txt](../../tests/e2e/evidencias/scrum-490-cotizacion-qa-2026-10-22.txt)) | No | No | No |
| T-11 | Servicio | Iniciar, subir la foto de evidencia y completar | RF-15 | SCRUM-35 | `solicitud_asignada_page` → `start`, `evidence` y `complete` | Sí | Sí ([scrum-96-evidencia-qa-2026-10-22.txt](../../tests/e2e/evidencias/scrum-96-evidencia-qa-2026-10-22.txt)) | No | No | No |
| T-12 | Servicio | Chatear con el cliente | RF-37 | SCRUM-473 | `chat_page` | Sí | Sí ([scrum-483-chat-qa-2026-10-22.txt](../../tests/e2e/evidencias/scrum-483-chat-qa-2026-10-22.txt)) | No | No | No |
| T-13 | Notificaciones | Ver el buzón de notificaciones | RF-11 | — | `notificaciones_page` | Sí | Sí ([scrum-458-geocodificacion-buzon-qa-2026-10-22.txt](../../tests/e2e/evidencias/scrum-458-geocodificacion-buzon-qa-2026-10-22.txt)) | No | No | No |
| T-14 | Historial | Ver el historial de solicitudes atendidas | RF-17 | SCRUM-37 | `servicios_tecnico_page` → `GET /v1/technicians/me/service-requests` | Sí | No | No | No | Sí (ninguna evidencia llama a GET /v1/technicians/me/service-requests; SCRUM-102) |
| T-15 | Pagos | Ver los pagos recibidos | RF-25 | SCRUM-45 | Ruta `/v1/payments/received` declarada en `api_endpoints.dart`, sin pantalla ni backend | No | No | No | No | Sí (SCRUM-45; backend Payments y pantalla UI) |

## 5. Proveedor (app móvil)

| ID | Módulo | Funcionalidad | RF | HU | Qué hay hoy | Desarrollada | Probada (evidencia) | Producción | Mock | Pendiente |
|---|---|---|---|---|---|---|---|---|---|---|
| P-01 | Cuenta | Registrarse con datos y documentos, en estado pendiente de verificación | RF-02 | SCRUM-22 | `registro_tecnico_page` | Sí | Sí ([scrum-56-registro-tecnico-qa-2026-10-22.txt](../../tests/e2e/evidencias/scrum-56-registro-tecnico-qa-2026-10-22.txt)) | No | No | No |
| P-02 | Cuenta | Iniciar sesión, con bloqueo tras 5 intentos | RF-03 | SCRUM-23 | `inicio_sesion_page` | Sí | Sí ([mvp-qa-sprint4-2026-10-18.txt](../../tests/e2e/evidencias/mvp-qa-sprint4-2026-10-18.txt)) | No | No | No |
| P-03 | Cuenta | Cerrar sesión | — | — | `cuenta_page` | Sí | No | No | No | Sí (cerrar sesión es de la app, sin prueba de interfaz en QA) |
| P-04 | Cuenta | Editar el perfil propio | — | SCRUM-609 | Igual que C-04 | Parcial | No | No | No | Sí (pantallas SCRUM-612 y SCRUM-613, QA SCRUM-614) |
| P-05 | Cuenta | Recuperar la contraseña | — | SCRUM-623 | Sin pantalla (SCRUM-624) | No | No | No | No | Sí (SCRUM-623; contrato SCRUM-624 y pantalla UI) |
| P-06 | Equipo | Registrar técnicos de su equipo | RF-16 | SCRUM-36 | `alta_tecnico_page` → `POST /v1/providers/me/technicians` e invitación | Sí | Sí ([scrum-99-equipo-proveedor-qa-2026-10-22.txt](../../tests/e2e/evidencias/scrum-99-equipo-proveedor-qa-2026-10-22.txt)) | No | No | No |
| P-07 | Equipo | Ver y administrar su equipo | RF-16 | SCRUM-36 | `equipo_page` | Sí | Sí ([scrum-99-equipo-proveedor-qa-2026-10-22.txt](../../tests/e2e/evidencias/scrum-99-equipo-proveedor-qa-2026-10-22.txt)) | No | No | No |
| P-08 | Notificaciones | Ver el buzón de notificaciones | RF-11 | — | `notificaciones_page` | Sí | Sí ([scrum-458-geocodificacion-buzon-qa-2026-10-22.txt](../../tests/e2e/evidencias/scrum-458-geocodificacion-buzon-qa-2026-10-22.txt)) | No | No | No |
| P-09 | Pagos | Ver los pagos recibidos | RF-25 | SCRUM-45 | Igual que T-15 | No | No | No | No | Sí (SCRUM-45; backend Payments y pantalla UI) |

## 6. Administrador del tenant (panel web)

| ID | Módulo | Funcionalidad | RF | HU | Qué hay hoy | Desarrollada | Probada (evidencia) | Producción | Mock | Pendiente |
|---|---|---|---|---|---|---|---|---|---|---|
| A-01 | Cuenta | Iniciar sesión en el panel (solo administradores) | RF-03, RF-05 | SCRUM-23, SCRUM-25 | Ruta `iniciar-sesion` | Sí | Sí ([scrum-108-aprobacion-rechazo-qa-2026-10-22.txt](../../tests/e2e/evidencias/scrum-108-aprobacion-rechazo-qa-2026-10-22.txt)) | No | No | No |
| A-02 | Cuenta | Activar la cuenta (definir la contraseña) | — | — | Ruta `activar` → `POST /v1/auth/password/setup` | Sí | No | No | No | Sí (activación probada solo para empresa, no para admin de tenant en QA) |
| A-03 | Cuenta | Cerrar sesión | — | — | Botón del layout del panel (`app.html`) | Sí | No | No | No | Sí (cerrar sesión es del panel web, sin prueba de interfaz en QA) |
| A-04 | Operación | Ver el tablero operativo | RF-18 | SCRUM-38 | Ruta `inicio` | Sí | Sí ([scrum-105-panel-operativo-qa-2026-10-22.txt](../../tests/e2e/evidencias/scrum-105-panel-operativo-qa-2026-10-22.txt)) | No | No | No |
| A-05 | Operación | Ver las solicitudes activas por estado | RF-18 | SCRUM-38 | Ruta `solicitudes` | Sí | Sí ([scrum-105-panel-operativo-qa-2026-10-22.txt](../../tests/e2e/evidencias/scrum-105-panel-operativo-qa-2026-10-22.txt)) | No | No | No |
| A-06 | Operación | Cancelar una solicitud con motivo | RF-36 | SCRUM-472 | Ruta `solicitudes` → `POST /v1/service-requests/{id}/cancel` | Sí | Sí ([scrum-478-cancelacion-qa-2026-10-19.txt](../../tests/e2e/evidencias/scrum-478-cancelacion-qa-2026-10-19.txt)) | No | No | No |
| A-07 | Técnicos | Aprobar o rechazar con motivo a técnicos y proveedores | RF-19 | SCRUM-39 | Ruta `tecnicos` → cambio de verificación | Sí | Sí ([scrum-108-aprobacion-rechazo-qa-2026-10-22.txt](../../tests/e2e/evidencias/scrum-108-aprobacion-rechazo-qa-2026-10-22.txt)) | No | No | No |
| A-08 | Técnicos | Suspender a un técnico | RF-20 | SCRUM-40 | Ruta `tecnicos` | Sí | Sí ([scrum-111-suspension-tecnico-qa-2026-10-22.txt](../../tests/e2e/evidencias/scrum-111-suspension-tecnico-qa-2026-10-22.txt)) | No | No | No |
| A-09 | Técnicos | Ver la reputación y la marca de reputación baja | RF-20 | SCRUM-32 | Sin pantalla; llega a Identity por evento (ADR-027, planeado) | Parcial | No | No | No | Sí (reputación llega a Identity; falta exponer en API y panel SCRUM-497, SCRUM-86) |

## 7. Administrador de plataforma (panel web)

| ID | Módulo | Funcionalidad | RF | HU | Qué hay hoy | Desarrollada | Probada (evidencia) | Producción | Mock | Pendiente |
|---|---|---|---|---|---|---|---|---|---|---|
| AP-01 | Cuenta | Iniciar sesión en el panel | RF-03, RF-05 | SCRUM-23, SCRUM-25 | Ruta `iniciar-sesion` | Sí | Sí ([scrum-105-panel-operativo-qa-2026-10-22.txt](../../tests/e2e/evidencias/scrum-105-panel-operativo-qa-2026-10-22.txt)) | No | No | No |
| AP-02 | Cuenta | Cerrar sesión | — | — | Botón del layout del panel | Sí | No | No | No | Sí (cerrar sesión es del panel web, sin prueba de interfaz en QA) |
| AP-03 | Tenants | Crear tenants | RF-21 | SCRUM-41 | Ruta `tenants` → `POST /v1/platform/tenants` | Sí | No | No | No | Sí (sin POST /v1/platform/tenants en evidencias de QA) |
| AP-04 | Tenants | Activar y desactivar tenants, con confirmación y auditoría | RF-21 | SCRUM-41 | Ruta `tenants` | Sí | No | No | No | Sí (activación/desactivación tenant en QA solo muestra 401) |
| AP-05 | Operación | Ver las solicitudes de todos los tenants, filtrables por tenant | RF-18 | SCRUM-38 | Ruta `solicitudes` → `/v1/platform/service-requests` | Sí | Sí ([scrum-105-panel-operativo-qa-2026-10-22.txt](../../tests/e2e/evidencias/scrum-105-panel-operativo-qa-2026-10-22.txt)) | No | No | No |
| AP-06 | Operación | Ver el tablero operativo | RF-18 | SCRUM-38 | Ruta `inicio` | Sí | Sí ([scrum-105-panel-operativo-qa-2026-10-22.txt](../../tests/e2e/evidencias/scrum-105-panel-operativo-qa-2026-10-22.txt)) | No | No | No |

## 8. Transversal (sistema, todos los usuarios)

| ID | Módulo | Funcionalidad | RF | HU | Qué hay hoy | Desarrollada | Probada (evidencia) | Producción | Mock | Pendiente |
|---|---|---|---|---|---|---|---|---|---|---|
| X-01 | Seguridad | Aislamiento de los datos por tenant | RF-04 | SCRUM-24 | RLS en los servicios con base (SAD 2.2, RNF-10) | Sí | Sí ([scrum-108-aprobacion-rechazo-qa-2026-10-22.txt](../../tests/e2e/evidencias/scrum-108-aprobacion-rechazo-qa-2026-10-22.txt)) | No | No | No |
| X-02 | Seguridad | Acceso según el rol y el canal | RF-05 | SCRUM-25 | Roles del JWT en cada servicio; el panel solo admite administradores | Sí | Sí ([scrum-108-aprobacion-rechazo-qa-2026-10-22.txt](../../tests/e2e/evidencias/scrum-108-aprobacion-rechazo-qa-2026-10-22.txt)) | No | No | No |
| X-03 | Matching | Asignación automática del técnico | RF-09 | SCRUM-29 | Matching Service (Kafka) | Sí | Sí ([scrum-78-qa-2026-10-22.txt](../../tests/e2e/evidencias/scrum-78-qa-2026-10-22.txt)) | No | No | No |
| X-04 | Calidad | CI/CD con build y pruebas antes de desplegar | RF-26 | SCRUM-46 | Workflows de cada repositorio y compuerta de QA | Sí | Sí ([suites-e2e-qa-sprint4-2026-10-18.txt](../../tests/e2e/evidencias/suites-e2e-qa-sprint4-2026-10-18.txt)) | No | No | No |
| X-05 | Calidad | Prueba automatizada de punta a punta del flujo crítico | RF-27 | SCRUM-47 | Colecciones de `tests/e2e/`; la calificación del final del flujo todavía no existe | Parcial | Parcial ([scrum-incremento-tecnico-qa-2026-10-22.txt](../../tests/e2e/evidencias/scrum-incremento-tecnico-qa-2026-10-22.txt)) | No | No | Sí (flujo crítico termina en calificación, pendiente en E2E) |
| X-06 | Operación | Logs centralizados con correlación y alertas de caída | RF-28 | SCRUM-48 | Loki, Prometheus y Grafana en VM1 | Sí | Sí ([loki_qa_k3s.json](../../tests/security/evidencias/loki_qa_k3s.json)) | No | No | No |
| X-07 | Seguridad | TLS en tránsito y contraseñas con hash | RF-29 | SCRUM-49 | Entrada TLS 1.2/1.3 y BCrypt (SAD 2.2, RNF-02 y RNF-03) | Sí | Sí ([tls-entrada-qa-2026-10-27.txt](../../tests/security/evidencias/tls-entrada-qa-2026-10-27.txt)) | No | No | No |

## Cobertura del SRS

| RF | Filas |
|---|---|
| RF-01 | C-01 |
| RF-02 | T-01, P-01 |
| RF-03 | C-02, E-04, T-03, P-02, A-01, AP-01 |
| RF-04 | X-01 |
| RF-05 | A-01, AP-01, X-02 |
| RF-06 | E-01, E-02, E-03 |
| RF-07 | C-06 |
| RF-08 | E-08 |
| RF-09 | X-03 |
| RF-10 | T-08 |
| RF-11 | C-07, C-11, E-09, E-13, T-13, P-08 |
| RF-12 | C-14, E-16 |
| RF-13 | T-07 |
| RF-14 | T-09 |
| RF-15 | T-11 |
| RF-16 | T-02, P-06, P-07 |
| RF-17 | T-14 |
| RF-18 | A-04, A-05, AP-05, AP-06 |
| RF-19 | A-07 |
| RF-20 | A-08, A-09 |
| RF-21 | AP-03, AP-04 |
| RF-22 | C-12 |
| RF-23 | E-14 |
| RF-24 | C-13, E-15 |
| RF-25 | T-15, P-09 |
| RF-26 | X-04 |
| RF-27 | X-05 |
| RF-28 | X-06 |
| RF-29 | X-07 |
| RF-34 | T-10 |
| RF-35 | C-08, E-10 |
| RF-36 | C-09, E-11, A-06 |
| RF-37 | C-10, E-12, T-12 |

Los 33 RF del SRS V5.6 quedan en al menos una fila.

## Totales del inventario

| Usuario | Funcionalidades |
|---|---|
| Visitante de la landing | 2 |
| Cliente hogar | 14 |
| Empresa cliente | 16 |
| Técnico | 15 |
| Proveedor | 9 |
| Administrador del tenant | 9 |
| Administrador de plataforma | 6 |
| Transversal | 7 |
| **Total** | **78** |



### Resumen de Estado de Funcionalidades (SCRUM-561 / SCRUM-562)

| Métrica de Calidad | Total | Porcentaje | Criterio de Auditoría |
|---|:---:|:---:|---|
| **Funcionalidades en Inventario** | **78** | 100.0% | 8 perfiles de usuario cubriendo los 33 RF del SRS V5.6 |
| **Implementadas y Verificadas (Avance Real)** | **51** | **65.4%** | Con evidencia real en QA que llama y comprueba la funcionalidad (`tests/`) |
| **Implementadas, Pendientes de QA** | **13** | 16.7% | Código implementado; pendiente corrida o prueba de interfaz en QA |
| **Parciales** | **8** | 10.3% | Backend sin UI completa (C-14, E-16, A-09 y la edición del perfil C-04, E-06, T-05, P-04) o flujo E2E sin paso final (X-05) |
| **No Implementadas** | **6** | 7.7% | Sin código implementado (recuperar la contraseña y pagos recibidos) |
| **Cobertura de Implementación (Verificadas + Pendientes)** | **64** | **82.1%** | Total de funcionalidades ya desarrolladas en el sistema |
| **En Producción (VM3)** | **0** | **0.0%** | Producción opera con `main` del 8 de octubre; 0 funcionalidades finales utilizables |
| **Con Mock (Pasarela simulada)** | **2** | 2.6% | Pagos de cliente hogar (C-12) y corporativo (E-14) con la pasarela simulada de Payments (ADR-009 modificado); aprobado y rechazado en `scrum-117-pago-qa-2026-10-22.txt` |

## Hallazgos del inventario

1. **Funcionalidades básicas sin HU:** cerrar sesión y el buzón de notificaciones existen en la app y en el panel, pero no tienen una HU propia. Se dejan con "—" para no inventar un número; si se crea una HU, se agrega aquí.
2. **La app declara rutas que todavía no usa:** la calificación (`/rating`) y los pagos recibidos (`/v1/payments/received`) están en `api_endpoints.dart`, pero ninguna pantalla las llama. La calificación ya está en el backend (SCRUM-85, en QA) y cuenta como parcial; los pagos recibidos no tienen backend y cuentan como no implementados.
3. **Sin pantalla:** editar el perfil (SCRUM-609) ya tiene backend en QA (SCRUM-611) y espera las pantallas; recuperar la contraseña (SCRUM-623) sigue en diseño de contrato.
4. **Categorías del tenant:** el administrador las crea por API (`/v1/catalog/admin/categories`), pero el panel no tiene pantalla y el SRS no tiene un RF para ello. No se agrega una fila; queda como pregunta para la PO.