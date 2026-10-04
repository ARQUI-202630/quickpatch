# ADR-004 — PostgreSQL + PostGIS

- **Estado:** Aceptado
- **Atributo:** AC2 — Performance Efficiency
- **Driver:** D1

## Contexto
Matching necesita filtrar y ordenar técnicos por ubicación, disponibilidad, cobertura y tenant.

## Decisión
Usar PostgreSQL como motor relacional y PostGIS para capacidades geoespaciales. Las consultas críticas utilizan índices GiST/KNN cuando corresponda.

## Evidencia
La PoC/benchmark de Matching mostró que el diseño de índices determina el rendimiento a gran volumen; los cambios de consulta o índices deben repetir el benchmark.

## Relación
ADR-003, ADR-005 y ADR-012.
