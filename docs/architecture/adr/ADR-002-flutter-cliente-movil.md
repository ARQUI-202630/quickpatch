# ADR-002 — Flutter como cliente móvil único

- **Estado:** Aceptado
- **Decisión:** Flutter para la aplicación móvil de clientes y técnicos
- **Atributo principal:** AC7 — Maintainability
- **Restricción:** R3

## Contexto
QUICKPATCH necesita atender clientes y técnicos en Android/iOS sin mantener dos bases de código nativas.

## Decisión
Usar Flutter como cliente móvil único. Los contratos REST se consumen desde `quickpatch-contracts` fijado mediante el submódulo `contracts/`.

## Consecuencias
Una sola base de código reduce mantenimiento y pruebas. Se acepta renunciar a optimizaciones nativas específicas cuando no sean necesarias para el MVP.

## Relación
ADR-012 y ADR-013.
