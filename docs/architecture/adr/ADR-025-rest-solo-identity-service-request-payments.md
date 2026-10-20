# ADR-025 — REST desde el API Gateway solo hacia Identity, ServiceRequest y Payments

- **Estado:** Aceptado el 20 de octubre de 2026 por el equipo (diagrama de arquitectura de alto nivel, «EDA con microservicios»). Modifica la sección 4.3 del SAD y precisa ADR-003 y ADR-023
- **Fecha:** 20 de octubre de 2026
- **Decisión:** el API Gateway tiene REST principal solo hacia **Identity, ServiceRequest y Payments**. **Actors, Catalog, Matching, Ranking y Communication** se integran por Kafka. Las lecturas de referencia que necesitan las apps (categorías y localidades) las sirve ServiceRequest desde sus réplicas. Unas pocas acciones directas del usuario quedan en su servicio dueño como **excepciones explícitas**, cada una con su motivo
- **Atributos priorizados:** AC7 Maintainability (menos superficie síncrona y menos rutas en el gateway) y AC5 Reliability (si Catalog o Matching caen, crear y consultar solicitudes sigue funcionando con las réplicas)
- **Atributos sacrificados:** AC1 Functional Suitability en la frescura de los datos (un cambio de categoría tarda segundos en verse) y AC7 Maintainability en ServiceRequest (sirve datos que no son de su dominio)
- **Restricciones:** ADR-003 (microservicios y EDA), ADR-017 (réplicas locales por eventos), ADR-022 (el gateway es la única entrada), R5 y R9

## Contexto

El diagrama de alto nivel del equipo dibuja tres conexiones REST desde el gateway: Identity, ServiceRequest y Payments. Los otros cinco servicios aparecen conectados solo a Kafka. La regla que acompaña al diagrama es:

- **REST** cuando el usuario inicia una acción y necesita la respuesta en ese momento.
- **Kafka** cuando algo ya ocurrió y otros servicios deben enterarse.

Al 20 de octubre, el gateway publicaba 12 rutas de servicios que el diagrama deja sin REST:

|Servicio|Rutas|Quién las usa|
|---|---|---|
|Catalog|`GET /v1/catalog/categories`; `POST` y `PATCH /v1/catalog/admin/categories`|App (nueva solicitud, registro de técnicos, equipo) y panel (filtros); la administración, ningún cliente todavía|
|Matching|`GET /v1/localities`; `GET` y `PUT /v1/technicians/me/availability` y `/coverage`; `GET /v1/matching/offers` y `POST .../accept` y `.../reject`|App del técnico|
|Communication|`GET /v1/notifications` y `POST .../{id}/read` (ADR-024); WebSocket `/v1/realtime` (ADR-023)|App|

## Decisión

1. **Las lecturas de referencia pasan a ServiceRequest** (contrato service-request 1.8.0):
   - `GET /v1/service-requests/categories`: categorías activas desde la réplica `service_request_categories`. Con token, las del tenant del token; sin token, las del tenant del canal (registro de técnicos). `catalog.category-changed` lleva la descripción desde quickpatch-kafka v0.8.0.
   - `GET /v1/service-requests/localities`: las 20 localidades desde la copia de P-09.
   - `GET /v1/catalog/categories` (catalog 1.3.0) y `GET /v1/localities` (matching 1.1.0) quedan obsoletas. Su ruta se retira del gateway cuando la app y el panel ya usen las nuevas.
2. **Excepciones explícitas.** Siguen en su servicio dueño, por REST a través del gateway, porque el usuario necesita la respuesta al instante y moverlas significaría mudar datos de dominio de un servicio a otro:
   - **Matching, acciones del técnico:** disponibilidad, cobertura, y listar, aceptar y rechazar ofertas. Aceptar una oferta debe confirmar en el momento que la asignación es suya (RN-M7). Por Kafka sería un `202` y una espera, con la cuenta regresiva de la oferta corriendo (RN-M8).
   - **Catalog, administración del catálogo** (`/v1/catalog/admin/categories`): el `admin_tenant` crea o desactiva una categoría y necesita la respuesta.
   - **Communication, buzón y canal en tiempo real:** el buzón (ADR-024) y el WebSocket (ADR-023). Son la entrega de los avisos al usuario, que el diagrama asigna a Communication. Dentro de la red del laboratorio cumplen el papel del proveedor de notificaciones, que R5 no admite.
3. **Lo que no cambia:**
   - Ningún servicio llama por REST a otro para cumplir su función. La única llamada interna (ServiceRequest → Identity, nombres por lote, `identity-internal.v1.yaml`) es de solo lectura, tolera fallos y no pasa por el gateway.
   - Kafka sigue con un topic por tipo de evento (ADR-006). Las familias del diagrama (`service-request.events`, `matching.events`, …) son el prefijo del nombre de cada topic: `service-request.*`, `matching.*`, `catalog.*`. Los eventos del técnico (`technician.*`) los publica Identity.
   - Redis y Garage se asignan por servicio según su uso (Documento de Infraestructura, sección 3.4), no en todos.
4. **Regla para lo que venga:** una ruta nueva va a Identity, ServiceRequest o Payments. Si tiene que ir a otro servicio, se agrega a la lista de excepciones de este ADR con su motivo.

## Alternativas descartadas

- **Cumplimiento estricto:** aceptar y rechazar ofertas como mensajes asíncronos vía ServiceRequest; disponibilidad y cobertura en Identity; buzón y WebSocket reubicados. Eran semanas de trabajo y mudar datos de Matching y Communication a otros servicios. Además, contradecía ADR-023 y ADR-024 y rompía lo que ya estaba probado en QA antes de la entrega.
- **Solo documentar las 12 rutas como excepciones:** era más barato, pero dejaba en otros servicios dos lecturas que ServiceRequest ya tiene en sus réplicas (ADR-017) y que la app usa en el flujo principal.
- **Un servicio de agregación (BFF) delante de Catalog y Matching:** agregaba un noveno componente y una llamada síncrona entre servicios, justo lo que ADR-003 evita.

## Consecuencias

### Positivas

- Crear una solicitud ya no depende de que Catalog responda: la app lee las categorías de ServiceRequest, que también las valida (RN-SR10).
- El gateway enruta tres servicios principales, más las excepciones listadas aquí y en la sección 4.3 del SAD.
- La regla es verificable: cada ruta del Ingress de un servicio que no es REST principal debe estar en este ADR.

### Costos

- ServiceRequest sirve datos de Catalog y de Matching: un cambio de categoría tarda unos segundos en verse en las apps (consistencia eventual).
- Catalog tuvo que volver a publicar todas sus categorías una vez, para que la réplica recibiera la descripción (migración `PublicarDescripcion`).
- Las excepciones mantienen REST hacia Matching, Catalog y Communication, y hay que revisarlas cuando cambien esos dominios.
