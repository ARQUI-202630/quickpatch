# BENCH-BE-001 — ASP.NET Core frente a NestJS

- **Rol:** Backend Developer
- **Estado:** Benchmark arquitectónico/cualitativo
- **Respalda:** ADR-012

## Resultado
Se mantiene ASP.NET Core para Identity, Actors, Catalog, ServiceRequest, Ranking, Payments y Communication; Matching permanece Java/Spring Boot.

La razón es de adecuación a QUICKPATCH: cumple estructuralmente la restricción .NET, evita tres stacks backend (.NET + Node + Java), se integra con Kafka/PostgreSQL y mantiene coherencia con ADR-012. No se afirma superioridad universal de rendimiento.

Si se exige benchmark cuantitativo, ambos stacks deben implementar el mismo servicio y medirse con hardware, payload y carga idénticos.
