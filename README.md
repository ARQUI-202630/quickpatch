# QUICKPATCH

Plataforma multi-tenant de servicios técnicos para hogares y empresas.

## Stack vigente

| Área | Tecnología |
|---|---|
| Admin web | Angular + TypeScript |
| Mobile cliente/técnico | Flutter + Dart |
| Backend principal | ASP.NET Core / .NET |
| Matching | Java + Spring Boot |
| Eventos | Apache Kafka |
| Persistencia | PostgreSQL + PostGIS |
| Cache | Redis |
| Evidencias | MinIO |
| Gateway | Nginx |
| Orquestación backend | k3s |
| Aprovisionamiento | Ansible |

La decisión está formalizada en `docs/architecture/adr/ADR-012-stack-tecnologico-polyglot.md`.

## Repositorios

QUICKPATCH usa un repositorio por componente, unidos por este repositorio principal mediante submódulos de Git (ADR-013). Este repo contiene la documentación, las pruebas del sistema completo y los punteros a los demás repos de la organización `ARQUI-202630`.

```text
quickpatch/                          (este repo)
├── apps/
│   ├── web/                         → quickpatch-web (Angular)
│   ├── mobile/                      → quickpatch-mobile (Flutter)
│   └── backend/services/
│       ├── identity/                → quickpatch-identity
│       ├── actors/                  → quickpatch-actors
│       ├── catalog/                 → quickpatch-catalog
│       ├── service-request/         → quickpatch-service-request
│       ├── matching/                → quickpatch-matching (Java + Spring Boot)
│       ├── ranking/                 → quickpatch-ranking
│       ├── payments/                → quickpatch-payments
│       └── communication/           → quickpatch-communication
├── contracts/                       → quickpatch-contracts (OpenAPI y eventos)
├── infrastructure/                  → quickpatch-infrastructure (Ansible y k3s)
├── tests/                           pruebas del sistema completo
└── docs/                            SRS, SAD, SDD, DD, Infraestructura, Políticas
```

Las rutas marcadas con `→` son submódulos. Cada servicio incluye además `contracts/` como submódulo, fijado en una versión.

### Clonar

```bash
git clone --recurse-submodules https://github.com/ARQUI-202630/quickpatch.git
# si ya estaba clonado sin submódulos:
git submodule update --init --recursive
```

### Trabajar en un componente

Dentro de la carpeta del submódulo, cambiarse primero a una rama (`git switch develop`): Git deja los submódulos sin rama por defecto. Los cambios se hacen, revisan y fusionan en el repo del componente; después se actualiza el puntero en este repo. Detalle en el ADR-013.

## Documentación

- `docs/requirements/SRS.md`
- `docs/architecture/SAD.md`
- `docs/architecture/SDD.md`
- `docs/design/DD.md`
- `docs/infrastructure/INFRASTRUCTURE.md`
- `docs/governance/WORKING_AGREEMENTS.md`

## IA

- Codex/agentes: `AGENTS.md`
- Claude Code: `CLAUDE.md`
- Contexto: `.ai/`

## Contratos

- REST: `contracts/openapi/`
- Kafka: `contracts/events/`

Ambos en el repo `quickpatch-contracts`, versionado con tags SemVer.

## GitFlow

Trabajo normal:

`feature/* -> develop -> release/* -> main`

Los PR de feature deben apuntar a `develop`.
