# ADR-026 — Chat de la solicitud en Communication, sobre el canal en tiempo real

- **Estado:** Propuesto el 21 de octubre de 2026 con SCRUM-473 (subtarea de diseño SCRUM-479). Acota FA3 del SAD (sección 1.3) y agrega una excepción a ADR-025
- **Fecha:** 21 de octubre de 2026
- **Decisión:** el cliente dueño de la solicitud y el técnico asignado se escriben mensajes de texto dentro de la solicitud. **Communication Service** guarda la conversación en `db_communication` y entrega cada mensaje nuevo por el canal en tiempo real de ADR-023. El historial y el envío son REST hacia Communication (`/v1/service-requests/{id}/messages`), como **excepción explícita** de ADR-025. Communication sabe quién participa y en qué estado está la solicitud por una réplica alimentada con `service-request.status-changed` (ADR-017), sin llamar a ServiceRequest
- **Atributos priorizados:** AC4 (el mensaje llega al otro participante en el momento, por el canal que ya existe) y AC6 Security (solo los dos participantes, con RLS por tenant y sin el texto en los logs)
- **Atributos sacrificados:** AC7 Maintainability (Communication suma un dominio con datos propios y una ruta más fuera de los tres servicios REST) y AC5 en la entrega en tiempo real (las conexiones siguen en memoria en una sola réplica, ADR-023)
- **Restricciones:** ADR-003, ADR-005 (RLS), ADR-017 (réplicas por eventos), ADR-023 (canal), ADR-025 (REST principal), R3 (alcance del MVP) y K12 (datos personales)

## Contexto

El SAD dejaba el chat fuera del MVP (FA3, roadmap 1.x): las dudas del servicio (acceso, horario, materiales) se resolvían por fuera de la aplicación, por teléfono o WhatsApp. En la revisión del Sprint 4 el equipo lo pidió dentro de la app (SCRUM-473), porque el teléfono del técnico no se muestra al cliente antes de la asignación (RN-SR13) y porque una conversación guardada en la solicitud sirve como trazabilidad (D6).

Hay tres preguntas: qué servicio guarda los mensajes, cómo llega el mensaje al otro participante y cómo sabe ese servicio quién puede escribir.

## Decisión

1. **Dueño: Communication Service.** El diagrama de alto nivel le asigna la comunicación con el usuario, y ya tiene base propia (`db_communication`, ADR-024) y el canal en tiempo real (ADR-023). Tablas nuevas `chat_participants` (réplica) y `chat_messages` (DD 5.23 y 5.24), con RLS por tenant.
2. **Participantes y estado por eventos.** Communication consume `service-request.status-changed`, que ya trae `clientId`, `technicianId` y `status`, y guarda por solicitud el cliente, el técnico asignado y el estado, descartando eventos más viejos que el último aplicado (`changedAt`, ADR-017). No hace falta un evento nuevo ni llamar a ServiceRequest.
   - Pueden escribir el cliente dueño y el técnico asignado **actual**. Si la solicitud se reasigna (RF-10), el técnico anterior deja de verla.
   - El chat se abre cuando la solicitud tiene técnico (`asignado`, `cotizado`, `cotizacion_aceptada`, `en_progreso`) y queda de solo lectura en `completado`, `pagado` y `cancelado`.
   - Los usuarios de una empresa (`empresa_contacto`) participan como el cliente dueño: hoy, el que creó la solicitud. Cuando el token traiga la empresa (SCRUM-26), se suman los demás usuarios autorizados de la misma empresa, igual que RN-P6 en el pago.
3. **REST para el historial y el envío, como excepción de ADR-025.** `GET` y `POST /v1/service-requests/{id}/messages` (`communication.v1.yaml` 1.3.0). El usuario necesita la respuesta en el momento (ver el historial y confirmar que su mensaje quedó guardado), y mover los mensajes a ServiceRequest mezclaría su dominio con la comunicación. La ruta empieza por `/v1/service-requests/{id}` porque nombra la solicitud, igual que el pago: un `IngressRoute` de Traefik la toma por el sufijo `/messages` con más prioridad que el prefijo de ServiceRequest.
4. **Entrega en tiempo real por el canal existente.** Al guardar un mensaje, Communication envía la trama `chat.message` (`asyncapi/realtime.v1.yaml` 1.1.0) a las conexiones del otro participante y a las demás del autor, en el mismo tenant. A diferencia de los avisos de estado, la trama lleva el mensaje completo: así la app lo pinta sin pedir el historial. Si el otro participante no está conectado, lo ve al abrir el chat; el MVP no crea una notificación en el buzón por cada mensaje.
5. **Contenido.** Texto plano de 1 a 1.000 caracteres, sin adjuntos. El texto no se escribe en los logs ni en los eventos de Kafka; los mensajes no salen de Communication.

## Alternativas descartadas

- **Mensajes en ServiceRequest:** ServiceRequest ya conoce a los participantes y el estado, y no haría falta la réplica. Pero mezcla la conversación con la máquina de estados de la solicitud, y la entrega en tiempo real igual tendría que pasar por Communication con un evento por mensaje (el texto viajaría por Kafka).
- **Enviar y leer solo por el WebSocket:** evita la excepción de ADR-025, pero el canal está diseñado para avisos de un solo sentido (ADR-023). Un envío por el socket no tiene respuesta HTTP que confirme que el mensaje quedó guardado, y el respaldo por REST de ADR-023 no tendría con qué leer el historial.
- **Un servicio de chat externo** (Firebase, Stream, Sendbird): viola R5 (única dependencia externa: la pasarela) y saca datos personales de las 7 VMs (K12).

## Consecuencias

### Positivas

- El cliente y el técnico acuerdan detalles sin compartir teléfonos antes de tiempo (RN-SR13), y la conversación queda guardada con la solicitud.
- No hay eventos nuevos ni llamadas síncronas entre servicios: la réplica sale de un evento que ya existe.
- El aislamiento se prueba igual que en el buzón: RLS por tenant y el usuario solo desde el JWT.

### Costos

- Communication guarda una réplica más y depende de recibir `status-changed` en orden por solicitud (la clave del mensaje es la solicitud).
- La entrega en tiempo real hereda el límite de ADR-023: una sola réplica de Communication con las conexiones en memoria.
- Una ruta más de la lista de excepciones de ADR-025.
