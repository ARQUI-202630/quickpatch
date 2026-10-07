# Claude Code — Backend

Aplica `../../CLAUDE.md`, `../../AGENTS.md` y `../../.ai/roles/backend.md`.

Mapa tecnológico:

- Identity: ASP.NET Core
- Actors: ASP.NET Core
- Catalog: ASP.NET Core
- ServiceRequest: ASP.NET Core
- Matching: Java + Spring Boot
- Ranking: ASP.NET Core
- Payments: ASP.NET Core
- Communication: ASP.NET Core

No cambies el stack asignado a un servicio sin una nueva decisión arquitectónica.

Contratos:
- `contracts/api-gateway/openapi/`
- `contracts/kafka/events/`

(Submódulos de `quickpatch-api-gateway` y `quickpatch-kafka` dentro de cada servicio.)
