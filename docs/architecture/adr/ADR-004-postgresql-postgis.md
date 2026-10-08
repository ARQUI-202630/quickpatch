# ADR-004 — PostgreSQL con PostGIS como base de datos

- **Estado:** Aceptado
- **Fecha:** agosto de 2026 (SAD 1.0)
- **Decisión:** PostgreSQL como motor relacional de todos los servicios y PostGIS para las consultas geoespaciales
- **Atributo priorizado:** AC2 Performance Efficiency
- **Atributo sacrificado:** AC7 Maintainability (la flexibilidad de esquema de un motor NoSQL)
- **Driver que la motiva:** D1 (asignar al técnico más cercano y disponible)
- **Escenario que la sustenta:** AC2-E1 (búsqueda de técnicos cercanos en menos de 3 segundos para el 95% de las solicitudes)

## Contexto

El matching debe encontrar, en segundos, a los técnicos aprobados, disponibles, con la especialidad pedida y cuya zona cubra la ubicación de la solicitud, ordenados por distancia (D1, RNF-05). Eso exige índices espaciales y consultas por distancia en la base de datos, no en memoria de la aplicación.

Además, todos los dominios necesitan transacciones (por ejemplo, guardar una solicitud y su evento en la misma transacción, ADR-007) y aislamiento por tenant (ADR-005).

## Decisión

- **PostgreSQL 16** para todos los servicios, cada uno con su propia base (ADR-014).
- **PostGIS** donde hay datos geográficos: ubicación de las solicitudes (`geometry(Point, 4326)`), cobertura y disponibilidad de técnicos en Matching. Las consultas críticas usan índices GiST y `ST_DWithin` / KNN.
- Acceso desde .NET con EF Core + Npgsql (con NetTopologySuite para la geometría) y desde Matching con Spring Data/JPA (ADR-012).

## Alternativas descartadas

- **MongoDB (índices geoespaciales 2dsphere):** consultas geográficas competentes y esquema flexible, pero sin RLS para el aislamiento por tenant (ADR-005) y con transacciones multi-documento más limitadas para el patrón Outbox.
- **MySQL con extensiones espaciales:** soporte geoespacial más pobre que PostGIS y sin RLS.
- **Un motor de búsqueda (Elasticsearch) para la cercanía:** rápido para geo-búsquedas, pero sería un segundo almacén que mantener sincronizado y no cabe en el presupuesto de recursos de las 7 VMs (R10).

## Consecuencias

### Positivas
- Consultas geoespaciales nativas e indexadas para el matching.
- RLS (ADR-005), transacciones y JSONB (cargas de eventos en `outbox_events`) en el mismo motor.
- Un solo motor que operar, respaldar y monitorear (R11).

### Costos
- Cambios de esquema por migraciones (EF Core, Flyway o equivalentes) en lugar de esquema libre.
- El rendimiento depende del diseño de índices: un cambio en las consultas de matching debe repetir la medición de AC2-E1.

## Evidencia

- PoC de Matching con PostGIS ejecutada por el rol de backend (matriz `docs/architecture/poc/POC-ADR-MATRIX.md`).
- ServiceRequest guarda la ubicación como `geometry(Point, 4326)` con índice GiST; sus pruebas de integración corren contra la imagen `postgis/postgis:16`.

## Trazabilidad

- SAD: driver D1, escenarios AC2-E1 y AC2-E4, sección 6.
- DD: tablas `service_requests`, `technician_availability`, `coverage_zones`.
- Relacionados: ADR-003, ADR-005, ADR-012, ADR-014.
