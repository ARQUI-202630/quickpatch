# ADR-023 — Canal de estado en tiempo real: WebSocket hacia Communication Service con respaldo por REST

- **Estado:** Aceptado el 12 de octubre de 2026 por el equipo (SCRUM-412, SAD V4). Resuelve la decisión abierta del SAD (sección 4.1), del DD (8.5) y del SDD (5.1)
- **Fecha:** 12 de octubre de 2026
- **Decisión:** Las apps reciben los cambios de estado por un WebSocket (`/v1/realtime`) que termina en Communication Service, a través de VM1 y del gateway del ambiente. El mensaje solo avisa del cambio; el detalle se sigue pidiendo por REST. Si el WebSocket no está disponible, la app consulta el detalle cada 30 segundos. Las notificaciones push quedan fuera del canal de estado
- **Atributos priorizados:** AC4 Interaction Capability (la interfaz se actualiza sola, D2) y AC2 Performance Efficiency (el aviso llega en segundos y sin consultas repetidas, AC2-E3)
- **Atributos sacrificados:** AC7 Maintainability (conexiones de larga duración con estado en Communication Service, reconexión y respaldo en las apps) y AC5 Reliability del canal (si Communication cae, el aviso se degrada a consulta cada 30 segundos)
- **Restricciones:** R5 (sin dependencias externas de producción fuera de la pasarela de pagos), R9 (red privada, sin llamadas entrantes desde Internet), R10 (7 VMs fijas), R3 (tiempo del curso)

## Contexto

RF-11 pide mostrar al cliente el estado de su solicitud en tiempo real y RNF-06 fija que un cambio de estado se vea en menos de un minuto. El driver D2 del SAD exige entregar el cambio **sin que el cliente consulte por su cuenta**, y AC2-E3 mide menos de 7 segundos desde la creación de la solicitud hasta el aviso. En la validación de los RNF (SAD 2.2), RNF-06 es el único requisito **sin cobertura**: la app tiene el modelo del mensaje (`core/realtime/mensaje_tiempo_real.dart`), pero la pantalla de detalle solo se actualiza al deslizar.

Los documentos no coinciden:

- **DD 8.5** describe un WebSocket (`/v1/realtime`, mensaje `service-request.status-changed`) "pendiente de decisión".
- **SDD 5.1** descarta el WebSocket y resuelve RF-11 con notificaciones push más consulta por REST.
- **SAD 4.1** deja la decisión abierta y pide que ningún documento la dé por hecha.

Dos restricciones pesan sobre la elección:

- **R5:** la única dependencia externa de producción es la pasarela de pagos. Las notificaciones push en Android solo se entregan a través de Firebase Cloud Messaging (Google) y en iOS a través de APNs (Apple): son servicios externos que reciben datos de los usuarios (el token del dispositivo y el contenido del aviso). El SRS ya registra esa tensión entre R5 y RIE-03 (sección 7.4, punto P1; SCRUM-405 y SCRUM-413).
- **R9:** las VMs no son alcanzables desde Internet. Los teléfonos llegan al sistema por la VPN de la universidad y la única entrada es el 443 de VM1. Un canal que se abre **desde la app** hacia VM1 funciona dentro de esa restricción; uno que depende de que un tercero alcance las VMs, no.

## Decisión

1. **Transporte:** WebSocket seguro desde la app (Flutter) y el panel (Angular) hacia `wss://<ambiente>/api/v1/realtime`. TLS termina en VM1 (ADR-022, regla 3); el Nginx de VM1 ya reenvía `Upgrade` y `Connection` (`gateway-nginx.conf.j2`), y Traefik en k3s admite WebSocket sin configuración adicional. El gateway enruta `/v1/realtime` a Communication Service.
2. **Autenticación:** el token de acceso viaja en la **primera trama** del WebSocket, no en la URL, para que no quede en los logs del gateway (DD 8.5). Communication Service valida el JWT con la llave pública (ADR-018) y toma `sub`, `tenant_id` y `role` del token; si la primera trama no llega o el token no es válido, cierra la conexión. Nunca acepta un `tenant_id` enviado por el cliente.
3. **Contenido:** Communication Service ya consume los eventos de Kafka (ADR-006). Por cada evento envía un aviso corto a los usuarios conectados a los que les corresponde (al cliente, sus solicitudes; al técnico, sus ofertas y sus solicitudes asignadas; al `admin_tenant`, los conteos del panel), siempre dentro de su tenant. El aviso **no lleva el detalle**: la app vuelve a pedir `GET /v1/service-requests/{id}`, así el canal no duplica las reglas de visibilidad (RN-SR13) ni expone datos.
4. **Respaldo:** si el WebSocket no conecta o se cae, la app consulta el detalle cada 30 segundos y reintenta la conexión con espera creciente. Con ese respaldo RNF-06 se cumple aun sin el canal.
5. **Push fuera del canal de estado:** las notificaciones push (RIE-03) sirven para avisar con la app cerrada y dependen de la decisión sobre R5 (SCRUM-413). Este canal no las necesita para cumplir RF-11, RNF-06 ni D2.
6. **Escala del MVP:** una réplica de Communication Service mantiene las conexiones (R10). Si se escala a varias réplicas, cada una debe recibir los eventos de todos los usuarios (consumidores en grupos distintos) o repartirlos con Redis pub/sub; queda como evolución, no como parte de esta decisión.

## Alternativas descartadas

- **Notificaciones push más consulta por REST (SDD 5.1):** avisa incluso con la app cerrada y no mantiene conexiones abiertas. Se descarta como canal de estado porque depende de Firebase Cloud Messaging y APNs, servicios externos que contradicen R5 mientras SCRUM-413 no lo resuelva; además, el aviso llega como notificación del sistema y la pantalla abierta igual tiene que consultar.
- **Solo consulta periódica (polling cada 30 segundos):** la opción más simple y la que hoy cumple RNF-06. Se descarta como solución final porque contradice D2 ("sin que el cliente consulte por su cuenta"), multiplica las peticiones al gateway por cada pantalla abierta y no cumple los 7 segundos de AC2-E3. Se conserva como respaldo.
- **Server-Sent Events (SSE):** suficiente para un canal de una sola dirección y más simple que WebSocket. Se descarta porque el `EventSource` de los navegadores no permite enviar el token en un encabezado (el panel tendría que poner el token en la URL o usar una librería aparte) y porque el DD 8.5 y el modelo de la app ya están definidos sobre WebSocket.
- **Long polling:** mantiene la petición abierta hasta que hay un cambio. Ocupa una conexión HTTP por cliente igual que el WebSocket, pero con más reconexiones y más lógica en el servidor. No aporta frente a las otras opciones.

## Consecuencias

### Positivas

- Cierra la única brecha sin cobertura de la validación de RNF (RNF-06) y atiende D2 sin agregar dependencias externas (R5) ni llamadas entrantes desde Internet (R9).
- Es el primer ADR que prioriza AC4 Interaction Capability, que llevaba una versión del SAD sin ninguna decisión de arquitectura que lo moviera (SAD, sección 6).
- No cambia los contratos REST existentes: el detalle sigue saliendo de `GET /v1/service-requests/{id}` y las reglas de visibilidad quedan en ServiceRequest Service.
- Reutiliza piezas que ya existen: los eventos de Kafka, el consumidor de Communication Service, el reenvío de `Upgrade` en VM1 y el modelo `MensajeTiempoReal` de la app.

### Costos

- Communication Service pasa a tener estado (las conexiones abiertas): reiniciar el pod corta los WebSocket y las apps se reconectan. Mientras tanto, el respaldo de 30 segundos mantiene RNF-06.
- Las apps suman lógica de conexión, reconexión con espera creciente y respaldo por consulta.
- Hay que probar el canal a través de VM1, Traefik y la VPN, y fijar los tiempos de espera de Nginx para conexiones largas (`proxy_read_timeout`) en el gateway de VM1.
- Con la app cerrada no llega ningún aviso hasta que se resuelva RIE-03 frente a R5 (SCRUM-413).

## Trabajo que se desprende

- **Contratos (DD V4, SCRUM-418):** publicar el formato de la primera trama (autenticación), los tipos de aviso y los códigos de cierre de `/v1/realtime` en `quickpatch-api-gateway`; el DD 8.5 deja de estar "pendiente de decisión".
- **SDD:** el texto de las secciones 5.1, 6.2, 6.11 y del caso de uso de inicio y cierre del servicio ya cita este ADR. El modelo de Structurizr (`quickpatch.dsl`: componente del canal en Communication Service y relación de `core/realtime` con el gateway) y sus PNG se actualizan en SCRUM-425.
- **SAD (hecho en la versión 2.26):** la sección 4.1 deja de tener la decisión abierta y RNF-06 (sección 2.2) cita este ADR. La evidencia de RNF-06 se actualiza en el SAD V4 (SCRUM-411) cuando el canal esté implementado y medido en QA.
- **Implementación:** Communication Service (servidor del WebSocket), el gateway de VM1 (`proxy_read_timeout`) y las apps (conexión, respaldo y suscripción de la pantalla de detalle).

## Trazabilidad

- SRS: RF-11, RNF-06, RIE-03; sección 7.4 (P1).
- SAD: D2; AC2-E3, AC4-E9; secciones 2.2 (RNF-06 sin cobertura), 4.1 (decisión abierta) y 6.
- DD: 8.4 (eventos que consume Communication Service) y 8.5 (canal en tiempo real).
- SDD: 5.1 (resolución anterior por push) y sección 8.12.1 (SLA de actualización).
- Relacionados: ADR-006 (Kafka), ADR-007 (Outbox), ADR-018 (JWT), ADR-022 (entrada única por VM1).
