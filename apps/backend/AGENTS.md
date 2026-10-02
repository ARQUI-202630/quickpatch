# AGENTS — Backend

Complementa `../../AGENTS.md`.

## Stack

Siete servicios usan ASP.NET Core:

- identity
- actors
- catalog
- service-request
- ranking
- payments
- communication

Matching usa Java + Spring Boot.

## Área normal

`apps/backend/**`

## Contratos

Repo `quickpatch-contracts`, como submódulo `contracts/` dentro de cada servicio:

- REST: `contracts/openapi/`
- Kafka: `contracts/events/`

No inventes endpoints, eventos o tablas. No escribas directamente en datos de otro servicio.

## EDA

Kafka se utiliza para hechos de dominio y coordinación asíncrona.
REST se utiliza cuando se necesita respuesta inmediata.

No sustituyas uno por otro únicamente por conveniencia de implementación.

## Persistencia

Servicios .NET: EF Core + Npgsql.
Matching: Spring Data/JPA sobre PostgreSQL/PostGIS.

Toda migración debe respetar ownership, multi-tenancy y estrategia expand-contract cuando aplique.

## Áreas ajenas

No modificar por defecto:

- `apps/web/**`
- `apps/mobile/**`
- `infrastructure/**`
- `.github/workflows/**`
- `tests/e2e/**`
