# ADR-009 — Tokenización de pagos

- **Estado:** Aceptado
- **Atributo:** AC6 — Security
- **Restricción:** K2 — PCI-DSS

## Decisión
Delegar captura/tokenización de PAN y CVV a la pasarela. QUICKPATCH persiste únicamente referencias/tokens y datos de auditoría permitidos.

## Consecuencias
Reduce exposición de datos sensibles a cambio de dependencia del proveedor. Bases y logs se verifican automáticamente para detectar PAN/CVV.
