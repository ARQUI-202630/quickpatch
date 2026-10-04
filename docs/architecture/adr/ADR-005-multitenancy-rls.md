# ADR-005 — Shared-schema con tenant_id + RLS

- **Estado:** Aceptado
- **Atributos:** AC7 — Maintainability; AC6 — Security
- **Driver:** D5

## Decisión
Usar shared-schema con `tenant_id` y PostgreSQL Row-Level Security en datos tenant-aware.

## Consecuencias
Reduce costo operativo frente a una base por tenant, pero vuelve obligatorias las pruebas de aislamiento, la propagación segura del tenant y la validación de RLS.

## Relación
ADR-004, ADR-006 y ADR-007.
