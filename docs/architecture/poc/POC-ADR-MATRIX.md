# Matriz PoC / Benchmark / ADR

| Evidencia | Decisión | ADR | Estado |
|---|---|---|---|
| POC-BE-001 | .NET → Kafka → Spring, Outbox/idempotencia | ADR-006, ADR-007, ADR-012 | Ejecutada (6 oct 2026): 7 casos correctos; un defecto encontrado y corregido. Ver `backend-dotnet/POC-BE-001-interoperabilidad-dotnet-kafka-spring.md` |
| BENCH-BE-001 | ASP.NET Core principal | ADR-012 | Cualitativa |
| PoC Matching/PostGIS | geoespacial | ADR-004 | Ejecutada según evidencia del rol |
| PoC DevOps | operación/orquestación | ADR-011, ADR-015 | Según evidencia DevOps |
| PoC Frontend | Angular | ADR-012 | Según evidencia Frontend |
| PoC Garage vs SeaweedFS | almacenamiento de objetos | ADR-016 | Ejecutada (VM7, 3 oct 2026; resultados en el ADR) |
| IT-SR-001 | Outbox → Kafka con `eventId` del Outbox; RLS por tenant | ADR-005, ADR-006, ADR-007 | Ejecutada: pruebas de integración de ServiceRequest (Testcontainers) |
| IT-SR-002 | Réplica de categorías por evento, idempotente | ADR-007, ADR-017 | Ejecutada: pruebas de integración de ServiceRequest |
| IT-CAT-001 | Estado completo de la categoría publicado por Outbox | ADR-007, ADR-017 | Ejecutada: pruebas de integración de Catalog |
| IT-ID-001 | Token RS256 con los claims del contrato; RLS en `users` | ADR-005, ADR-018 | Ejecutada: pruebas de integración de Identity |
