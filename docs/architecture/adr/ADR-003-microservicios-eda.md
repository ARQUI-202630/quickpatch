# ADR-003 — Microservicios + Event-Driven Architecture

- **Estado:** Aceptado
- **Atributos:** AC8 — Flexibility; AC5 — Reliability

## Contexto
Identity, Actors, Catalog, ServiceRequest, Matching, Ranking, Payments y Communication requieren límites funcionales y ciclos de despliegue independientes.

## Decisión
Separar QUICKPATCH en ocho microservicios. REST/HTTPS se usa cuando se necesita respuesta inmediata; Kafka se usa para hechos de dominio y coordinación asíncrona.

## Consecuencias
Se obtiene aislamiento y despliegue por servicio a costa de mayor complejidad distribuida, observabilidad y testing. Ningún servicio comparte código interno con otro; solo contratos versionados.

## Relación
ADR-006, ADR-007, ADR-011, ADR-012 y ADR-013.
