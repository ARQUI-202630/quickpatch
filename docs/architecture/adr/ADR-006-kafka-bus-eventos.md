# ADR-006 — Apache Kafka como bus de eventos central

- **Estado:** Aceptado
- **Fecha:** agosto de 2026 (SAD 1.0)
- **Decisión:** Kafka (VM6) transporta todos los hechos de dominio entre microservicios
- **Atributos priorizados:** AC5 Reliability, AC8 Flexibility
- **Atributos sacrificados:** AC7 Maintainability, AC2 Performance Efficiency (consistencia eventual)
- **Drivers que la motivan:** D1, D2 y D6
- **Escenarios que la sustentan:** AC2-E3, AC5-E4

## Contexto

Con microservicios orientados a eventos (ADR-003), los servicios necesitan un medio para publicar hechos ("se creó una solicitud", "se aprobó un pago") que otros consumen a su ritmo, aunque estén caídos en ese momento. El historial de esos hechos también sirve para reconstruir el ciclo de vida de un servicio ante una reclamación (D6).

## Decisión

- **Kafka** como bus central, con un topic por tipo de evento (mismo nombre que `eventType`) y el id del agregado como clave del mensaje, para conservar el orden por entidad.
- Los contratos de eventos viven en `quickpatch-kafka/events/`, junto con la definición de los topics (`topics/topics.yaml`, ADR-021), (JSON Schema draft-07) con un sobre común: `eventId`, `eventType`, `eventVersion`, `occurredAt`, `correlationId`, `tenantId`, `producer` y `data`.
- Los eventos se publican con Outbox y se consumen de forma idempotente (ADR-007). El productor usa `acks=all` e idempotencia; el consumidor confirma el offset solo después de aplicar el efecto.
- REST queda para las interacciones en las que el usuario espera una respuesta inmediata.

## Alternativas descartadas

- **RabbitMQ:** más simple de operar y bueno para colas de trabajo, pero no conserva un registro reproducible de los eventos (útil para D6 y para reconstruir réplicas) ni ofrece orden por clave tan directo.
- **Llamadas REST entre servicios:** sin infraestructura adicional, pero acopla la disponibilidad de los servicios entre sí (ver ADR-003).
- **Servicio administrado (Amazon SNS/SQS, Confluent Cloud):** se descarta por R5 (sin presupuesto y todo dentro de las 7 VMs).

## Consecuencias

### Positivas
- Un servicio caído no pierde eventos: los procesa al volver (AC5-E3, AC5-E4).
- Agregar un consumidor nuevo no cambia al productor (AC8).
- Los eventos con `correlationId` permiten seguir un flujo entre servicios (AC7-E4).

### Costos
- Consistencia eventual: la notificación al técnico y las réplicas van unos segundos atrás (AC2-E3 fija el límite en 7 segundos).
- Un broker más que operar en VM6, de un solo nodo y sin réplica (R10).
- Cada evento exige contrato, versión y pruebas de compatibilidad.

## Evidencia

- `service-request.created` y `catalog.category-changed` publicados y consumidos contra un Kafka real (Testcontainers) en ServiceRequest y Catalog.
- POC-BE-001 (6 de octubre de 2026): ServiceRequest (.NET) publica y Matching (Spring Boot) consume `service-request.created` solo con el contrato; 723 ms de punta a punta con una solicitud.

## Trazabilidad

- SAD: secciones 4.2.4, 4.3 y 6; drivers D1, D2, D6.
- DD: catálogo de eventos y sobre común.
- Relacionados: ADR-003, ADR-007, ADR-017.
