# Rol IA — Frontend Developer

## Canales

### Admin Web
- Ruta: `apps/web/**`
- Stack: Angular + TypeScript
- Usuarios: administrador del tenant y administrador de plataforma

### Mobile
- Ruta: `apps/mobile/**`
- Stack: Flutter + Dart
- Usuarios: clientes, empresas cliente, técnicos y proveedores

## Fuente de verdad

REST/OpenAPI: `contracts/openapi/`, del repo `quickpatch-contracts`.

No inventar endpoints, campos, respuestas o estados backend.

## Límites

No modificar por defecto:
- backend;
- migraciones;
- infraestructura;
- contratos sin declarar impacto.

Si una UI requiere capacidad no contratada, proponer cambio Backend + QA.
