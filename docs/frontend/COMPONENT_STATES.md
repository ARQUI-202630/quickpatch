# Guía de estados de pantalla — QUICKPATCH

|Campo|Valor|
|---|---|
|**Historia**|SCRUM-620 (subtarea de SCRUM-619, consistencia visual y de estados)|
|**Versión**|1.0|
|**Fecha**|28 de octubre de 2026|
|**Para**|App móvil (Flutter) y panel web (Angular)|
|**Fuente**|DD 5.15: máquina de estados (sección 5.5, figura 3), reglas RN-SR, RN-Q, RN-P y RN-R (sección 7), canal en tiempo real (sección 8.5); contratos de `quickpatch-api-gateway`|

Esta guía no define reglas nuevas: resume para los frontends lo que ya dicen el DD y los contratos. Si algo de aquí no coincide con ellos, mandan el DD y el contrato, y esta guía se corrige.

## Reglas comunes

- **El estado lo decide el backend.** La pantalla muestra el estado que devuelve la API; no lo adelanta al pulsar un botón ni lo deduce de otro dato. Después de una acción, se vuelve a pedir el recurso.
- **Tiempo real primero, consulta después.** El canal de Communication (WebSocket `/v1/realtime`, `asyncapi/realtime.v1.yaml`, DD 8.5, ADR-023) avisa `service-request.status-changed`, `offer.created` y `service-request.counts-changed`. Los avisos no traen el detalle: al recibir uno, la app pide el recurso por REST. Si el canal está caído, la pantalla consulta al abrirse y con el gesto de recargar.
- **Sin caché de estados de negocio.** Cada vez que se abre una pantalla de solicitud, pago o cotización, se consulta el servidor.
- **Cuatro estados de pantalla en todas las vistas:** cargando, vacío (con un texto que diga qué falta y qué puede hacer el usuario), error (con reintentar) y con datos.
- **Los errores llegan en `application/problem+json`** (RFC 9457). La pantalla decide por `type`, no por el texto; en `400 validacion` muestra `errors.<campo>` junto al campo.
- **Las acciones que no aplican no se muestran.** Si una acción falla con `409 transicion-invalida`, se recarga el recurso y se muestra el estado actual.

## 1. Solicitud de servicio

Estados del DD (sección 5.5): `buscando_tecnico`, `en_espera`, `asignado`, `cotizado`, `cotizacion_aceptada`, `en_progreso`, `completado`, `pagado` y `cancelado`.

|Estado|Qué ve el cliente o la empresa|Acciones del cliente|Qué ve el técnico asignado|Acciones del técnico|
|---|---|---|---|---|
|`buscando_tecnico`|Buscando técnico|Cancelar|—|Aceptar o rechazar la oferta (`offer.created`)|
|`en_espera`|Sin técnicos disponibles por ahora; la búsqueda se reanuda sola|Cancelar|—|—|
|`asignado`|Técnico asignado, esperando cotización|Cancelar|Detalle con dirección y teléfono (RN-SR13)|Emitir cotización (RN-Q1)|
|`cotizado`|Cotización por responder, con su vencimiento|Aceptar, rechazar o cancelar|Cotización enviada|—|
|`cotizacion_aceptada`|Cotización aceptada, esperando el inicio|Cancelar|Detalle con dirección y teléfono|Iniciar el servicio (RN-SR6)|
|`en_progreso`|Servicio en curso|—|Detalle con dirección y teléfono|Subir evidencia y completar (RN-SR3: sin evidencia responde `422 evidencia-requerida`)|
|`completado`|Servicio terminado, pago pendiente|Pagar (y reintentar si el pago fue rechazado, RN-SR5)|Detalle con dirección y teléfono|—|
|`pagado`|Servicio pagado|Calificar una vez (RN-R2, RN-R3); comprobante del pago|En el historial, sin datos de contacto (RN-SR13), con `score` y `ratedAt` si ya lo calificaron|—|
|`cancelado`|Cancelada, con el motivo|—|En el historial|—|

- **Cancelar** solo existe antes de `en_progreso` (RN-SR7) y solo lo pueden hacer el cliente que creó la solicitud y el `admin_tenant` (RN-SR8). Si la solicitud tenía una cotización pendiente, esa cotización queda `anulada` (RN-Q5).
- **Empresa cliente:** los demás `empresa_contacto` de la misma empresa ven la solicitud, pero las acciones (cancelar, responder la cotización, calificar) son solo de quien la creó (RN-SR14).
- **`admin_tenant`:** ve todas las solicitudes de su tenant en el panel operativo, filtradas por estado (RF-18), y puede cancelar las que estén antes de `en_progreso`.

## 2. Cotización

Estados del DD (sección 5.11): `pendiente`, `aceptada`, `rechazada`, `anulada` y `expirada`.

|Estado|Pantalla del cliente|Qué pasa con la solicitud|
|---|---|---|
|`pendiente`|Total de mano de obra y materiales, vencimiento, aceptar o rechazar|Queda en `cotizado`|
|`aceptada`|Cotización aceptada (no se modifica, RN-Q4)|Pasa a `cotizacion_aceptada`|
|`rechazada`|Cotización rechazada|Vuelve a `asignado`; el técnico puede enviar otra, hasta 3 por solicitud. Al rechazar la tercera, la solicitud se cancela (RN-Q7)|
|`expirada`|Venció sin respuesta|La solicitud se cancela con el motivo «cotización sin respuesta» (RN-Q6)|
|`anulada`|La solicitud se canceló con la cotización pendiente|`cancelado` (RN-Q5)|

## 3. Pago

El pago nace cuando la solicitud llega a `completado` (RN-P4), no al aceptar la cotización. Su monto es el total de la cotización aceptada (RN-P3). La pantalla de pago consulta `GET /v1/service-requests/{id}/payment`.

|Estado|Pantalla del cliente|Acción|
|---|---|---|
|`pendiente`|Monto a pagar|Pagar. El botón se desactiva al enviar; un segundo envío responde `409 pago-en-curso` y no crea otro pago (RN-P5). Si el pago todavía no existe, responde `409 pago-no-disponible` (RN-P4): se espera y se vuelve a consultar|
|`procesando`|Pago en proceso|Ninguna. La app vuelve a consultar el pago hasta que la conciliación lo cierre (contrato payments)|
|`aprobado`|Pago aprobado; la solicitud pasa a `pagado` (RN-SR4)|Ver el comprobante, sin validez fiscal (`GET /v1/payments/{id}/invoice`, SRS P3)|
|`rechazado`|Pago rechazado; la solicitud sigue en `completado` (RN-SR5)|Reintentar: el mismo endpoint crea un pago nuevo|

Los datos de la tarjeta nunca llegan al backend ni se guardan en la app (RN-P1).

## 4. Calificación

Solo el dueño de la solicitud califica, solo en `pagado` y una sola vez (RN-R1 a RN-R3). Puntaje de 1 a 5 y comentario opcional de hasta 500 caracteres.

|Estado|Cliente|Técnico|
|---|---|---|
|Sin calificar (`pagado`)|Formulario de calificación|Nada|
|Calificada|Su calificación, de solo lectura|`score` y `ratedAt` en su historial (`GET /v1/technicians/me/service-requests`, service-request 1.10.0)|

`409 ya-calificada` significa que ya existe: se muestra la calificación en modo lectura. La reputación del técnico la calcula Ranking por eventos (ADR-027) y puede tardar unos segundos en verse.

## 5. Errores que la pantalla debe distinguir

|`type` (sufijo)|Código|Qué muestra la pantalla|
|---|---|---|
|`validacion`|400|El mensaje de `errors.<campo>` junto al campo|
|`no-autenticado`|401|Vuelve al inicio de sesión|
|`no-autorizado`|403|«No tienes permiso para esta acción»; no reintenta|
|`no-encontrado`|404|«No encontramos este elemento»; una solicitud de otro tenant también responde 404|
|`transicion-invalida`|409|Recarga el recurso y muestra el estado actual|
|`ya-calificada`|409|Muestra la calificación existente|
|`limite-de-cotizaciones`|409|Al técnico: la solicitud ya tiene 3 cotizaciones o una pendiente (RN-Q2, RN-Q7)|
|`pago-en-curso`|409|El pago se está procesando; consulta el pago en vez de reenviar|
|`evidencia-requerida`|422|Pide subir al menos una evidencia antes de completar|
|`ubicacion-fuera-de-cobertura`|422|«Por ahora solo atendemos en Bogotá» (RN-SR9)|
|`direccion-no-encontrada`|422|Pide corregir la dirección o marcar el punto en el mapa|
|`cuenta-bloqueada`|423|Inicio de sesión bloqueado 15 minutos tras 5 intentos (RN-U4); usa la cabecera `Retry-After`|

## Historial

|Versión|Fecha|Cambio|
|---|---|---|
|1.0|28 oct 2026|Primera versión (SCRUM-620): reglas comunes, estados de la solicitud, la cotización, el pago y la calificación según el DD 5.15, y errores que la pantalla distingue.|
