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
| Evidencias | Garage |
| Gateway | Nginx |
| Orquestación backend | k3s |
| Aprovisionamiento | Ansible |

La decisión está formalizada en `docs/architecture/adr/ADR-012-stack-tecnologico-polyglot.md`.

## Repositorios

QUICKPATCH tiene **12 repositorios**, uno por componente de la solución (retroalimentación del profesor, SCRUM-333): Flutter, Angular, API Gateway, los 8 microservicios y Apache Kafka. Este repositorio principal los une mediante submódulos de Git (ADR-013) y contiene la documentación, las pruebas del sistema completo y los punteros a los demás repos de la organización `ARQUI-202630`.

```text
quickpatch/                          (este repo)
├── apps/
│   ├── mobile/                      → quickpatch-mobile (Flutter)
│   ├── web/                         → quickpatch-web (Angular)
│   ├── api-gateway/                 → quickpatch-api-gateway (gateway y contratos REST/OpenAPI)
│   ├── backend/services/
│   │   ├── identity/                → quickpatch-identity
│   │   ├── actors/                  → quickpatch-actors
│   │   ├── catalog/                 → quickpatch-catalog
│   │   ├── service-request/         → quickpatch-service-request
│   │   ├── matching/                → quickpatch-matching (Java + Spring Boot)
│   │   ├── ranking/                 → quickpatch-ranking
│   │   ├── payments/                → quickpatch-payments
│   │   └── communication/           → quickpatch-communication
│   └── kafka/                       → quickpatch-kafka (bus de eventos, esquemas y topics)
├── infrastructure/                  Ansible e inventario de las VMs (antes quickpatch-infrastructure, SCRUM-338)
├── tests/                           pruebas del sistema completo
└── docs/                            SRS, SAD, SDD, DD, Infraestructura, Políticas
```

Las rutas marcadas con `→` son submódulos. Cada servicio incluye además los contratos como submódulos fijados en una versión: `contracts/api-gateway/` (REST) y `contracts/kafka/` (eventos); web y mobile solo `contracts/api-gateway/`. `tools/validate-composition.sh` lo comprueba en el CI.

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

- REST: `openapi/` del repo `quickpatch-api-gateway` (en los consumidores, `contracts/api-gateway/openapi/`).
- Kafka: `events/` y `topics/` del repo `quickpatch-kafka` (en los servicios, `contracts/kafka/events/`).

Ambos versionados con tags SemVer. Hasta octubre de 2026 vivían juntos en `quickpatch-contracts`, ahora archivado.

## GitFlow

Trabajo normal:

`feature/* -> develop -> release/* -> main`

Los PR de feature deben apuntar a `develop`.
