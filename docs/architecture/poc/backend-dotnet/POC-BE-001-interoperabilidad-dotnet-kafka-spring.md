# POC-BE-001 — Interoperabilidad ASP.NET Core → Kafka → Spring Boot

- **Rol:** Backend Developer
- **Estado:** Planeada; ejecución pendiente
- **Respalda:** ADR-006, ADR-007 y ADR-012
- **Repositorios:** `quickpatch-service-request`, `quickpatch-matching`, `quickpatch-contracts`

## Pregunta
¿Puede ServiceRequest en ASP.NET Core producir un evento versionado que Matching en Spring Boot consuma sin compartir clases internas, preservando `eventId`, `tenantId` y `correlationId`, y manteniendo Outbox e idempotencia?

## Corte funcional

```text
quickpatch-service-request (.NET 10)
  -> PostgreSQL + outbox_events
  -> Kafka: service-request.created
  -> quickpatch-matching (Java 25 / Spring Boot 4.1.1)
  -> processed_events
```

El contrato vive en `contracts/`, fijado a una versión SemVer de `quickpatch-contracts`.

## Casos
Interoperabilidad, tenant/correlation, duplicado por `eventId`, Kafka caído, recuperación, contrato inválido e independencia de runtimes.

## Estado
No se declaran métricas todavía. La evidencia se agregará después del scaffolding real de ServiceRequest y Matching.
