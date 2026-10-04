# ADR-007 — Transactional Outbox + idempotencia

- **Estado:** Aceptado
- **Atributo:** AC5 — Reliability

## Decisión
Persistir el cambio de negocio y `outbox_events` en la misma transacción local. Un publicador posterior envía a Kafka. Los consumidores deduplican por `eventId` mediante `processed_events` o mecanismo equivalente.

## Reglas
No marcar Outbox como publicado antes del ack del broker. Preservar `eventId`, `tenantId` y `correlationId`. Un reintento no puede duplicar el efecto de negocio.

## Evidencia
POC-BE-001 prueba caída/recuperación de Kafka y reentrega duplicada.
