# ADR-006 — Apache Kafka como bus de eventos central

- **Estado:** Aceptado
- **Atributos:** AC5 — Reliability; AC8 — Flexibility
- **Drivers:** D1, D2 y D6

## Decisión
Usar Kafka para hechos de dominio y procesos desacoplados. REST/HTTPS permanece para interacciones síncronas. Los eventos viven en `quickpatch-contracts/events/` y cada consumidor fija una versión mediante `contracts/`.

## Consecuencias
Desacoplamiento temporal/tecnológico a cambio de consistencia eventual, contratos versionados, Outbox, idempotencia y observabilidad distribuida.

## Evidencia
POC-BE-001 valida ASP.NET Core → Kafka → Spring Boot.
