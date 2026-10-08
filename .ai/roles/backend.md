# Rol IA — Backend Developer

## Área

`apps/backend/**`

## Stack obligatorio por servicio

.NET / ASP.NET Core:
- Identity
- Actors
- Catalog
- ServiceRequest
- Ranking
- Payments
- Communication

Java + Spring Boot:
- Matching

No cambiar el stack asignado sin nueva ADR.

## Contratos

Cada servicio los incluye como submódulos fijados en una versión (tag SemVer): `contracts/api-gateway/` (repo `quickpatch-api-gateway`) y `contracts/kafka/` (repo `quickpatch-kafka`).

- REST: `contracts/api-gateway/openapi/`
- Eventos: `contracts/kafka/events/` (topics en `quickpatch-kafka/topics/topics.yaml`)

Cambiar de versión de contratos es un commit explícito en el servicio, no una actualización automática.

## Persistencia

- .NET: EF Core + Npgsql.
- Matching: Spring Data/JPA.
- PostgreSQL/PostGIS como persistencia.
- Cada servicio es propietario de sus datos.

## EDA

REST para respuesta inmediata.
Kafka para eventos/hechos de dominio y flujos desacoplados.

Respetar idempotencia, correlation IDs, Outbox y compatibilidad cuando aplique.

## Seguridad

- tenant derivado del contexto autenticado cuando corresponda;
- no eliminar aislamiento;
- no almacenar PAN/CVV;
- no registrar secretos/datos prohibidos.

## No modificar por defecto

- `apps/web/**`
- `apps/mobile/**`
- `infrastructure/**`
- `.github/workflows/**`
- E2E de QA
