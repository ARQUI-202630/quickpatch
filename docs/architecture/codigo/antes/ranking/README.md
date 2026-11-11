# Ranking — antes

Código de `origin/develop` en `867716d`, generado el 2026-11-10 con `tools/arquitectura/generar.py`.

| Métrica | Valor |
|---|---|
| Tipos (sin migraciones) | 32 |
| Paquetes | 11 |
| Dependencias entre tipos | 61 |
| Dependencias entre paquetes | 19 |
| Ciclos entre paquetes | 0 |
| Paquetes dentro de ciclos | 0 |
| Ciclos entre tipos | 0 |
| Tipos en el mayor ciclo | 0 |
| Violaciones de SDD 10.3.2 | 0 |
| Tipos de más de 250 líneas | 0 |
| Fan-out máximo (sin raíces de composición) | 10 |
| Fan-out promedio | 1.91 |
| Cohesión relacional promedio (H) | 0.79 |

## Dependencias entre capas

| Desde → hacia | Dependencias |
|---|---|
| Api → Application | 1 |
| Api → Infrastructure | 1 |
| Application → Domain | 5 |
| Infrastructure → Application | 14 |
| Infrastructure → Domain | 4 |

## Clases con más dependencias de salida (fan-out)

| Tipo | Capa | Líneas | Sale | Entra |
|---|---|---|---|---|
| `Application.Reputation.ServiceRequestRatedHandler` | Application | 49 | 10 | 2 |
| `Application.Events.RankingEvents` | Application | 14 | 5 | 1 |
| `Infrastructure.Messaging.ServiceRequestRatedConsumer` | Infrastructure | 88 | 5 | 1 |
| `Infrastructure.Messaging.OutboxPublisher` | Infrastructure | 73 | 4 | 1 |
| `Infrastructure.Persistence.EfOutbox` | Infrastructure | 16 | 4 | 1 |
| `Infrastructure.Persistence.RankingDbContext` | Infrastructure | 71 | 4 | 7 |
| `Infrastructure.Persistence.ReputationRepository` | Infrastructure | 13 | 4 | 1 |
| `Infrastructure.Persistence.ProcessedEventRepository` | Infrastructure | 7 | 3 | 1 |
| `Application.Abstractions.IReputationRepository` | Application | 0 | 2 | 3 |
| `Infrastructure.Persistence.TenantUnitOfWork` | Infrastructure | 21 | 2 | 1 |

## Clases más usadas (fan-in)

| Tipo | Capa | Entra | Sale |
|---|---|---|---|
| `Infrastructure.Persistence.RankingDbContext` | Infrastructure | 7 | 4 |
| `Domain.Reputation.TechnicianReputation` | Domain | 5 | 0 |
| `Domain.Reputation.AppliedRating` | Domain | 4 | 0 |
| `Application.Abstractions.IOutbox` | Application | 3 | 1 |
| `Application.Abstractions.IProcessedEventRepository` | Application | 3 | 0 |
| `Application.Abstractions.IReputationRepository` | Application | 3 | 2 |
| `Application.Abstractions.ITenantUnitOfWork` | Application | 3 | 0 |
| `Application.Abstractions.OutboxMessage` | Application | 3 | 0 |
| `Application.Events.EventEnvelope` | Application | 3 | 0 |
| `Infrastructure.Persistence.OutboxEventRecord` | Infrastructure | 3 | 0 |

## Clases más grandes

| Tipo | Capa | Líneas | Archivo |
|---|---|---|---|
| `Infrastructure.Messaging.ServiceRequestRatedConsumer` | Infrastructure | 88 | `src/QuickPatch.Ranking.Infrastructure/Messaging/ServiceRequestRatedConsumer.cs` |
| `Infrastructure.Messaging.OutboxPublisher` | Infrastructure | 73 | `src/QuickPatch.Ranking.Infrastructure/Messaging/OutboxPublisher.cs` |
| `Infrastructure.Persistence.RankingDbContext` | Infrastructure | 71 | `src/QuickPatch.Ranking.Infrastructure/Persistence/RankingDbContext.cs` |
| `Domain.Reputation.TechnicianReputation` | Domain | 55 | `src/QuickPatch.Ranking.Domain/Reputation/TechnicianReputation.cs` |
| `Application.Reputation.ServiceRequestRatedHandler` | Application | 49 | `src/QuickPatch.Ranking.Application/Reputation/ServiceRequestRatedHandler.cs` |
| `Domain.Reputation.AppliedRating` | Domain | 24 | `src/QuickPatch.Ranking.Domain/Reputation/TechnicianReputation.cs` |
| `Infrastructure.Persistence.TenantUnitOfWork` | Infrastructure | 21 | `src/QuickPatch.Ranking.Infrastructure/Persistence/Repositories.cs` |
| `Infrastructure.Persistence.EfOutbox` | Infrastructure | 16 | `src/QuickPatch.Ranking.Infrastructure/Persistence/Repositories.cs` |
| `Infrastructure.Persistence.OutboxEventRecord` | Infrastructure | 15 | `src/QuickPatch.Ranking.Infrastructure/Persistence/RankingDbContext.cs` |
| `Application.Events.RankingEvents` | Application | 14 | `src/QuickPatch.Ranking.Application/Events/EventContracts.cs` |

## Ciclos entre paquetes

Ninguno.

## Violaciones de las reglas de dependencia (SDD 10.3.2)

Ninguna.

## Paquetes

| Paquete | Tipos | Fan-in | Fan-out | Inestabilidad | Cohesión H |
|---|---|---|---|---|---|
| `(global)` | 1 | 0 | 2 | 1.0 | 1.0 |
| `Application` | 1 | 1 | 1 | 0.5 | 1.0 |
| `Application.Abstractions` | 5 | 4 | 1 | 0.2 | 0.4 |
| `Application.Events` | 6 | 2 | 2 | 0.5 | 0.67 |
| `Application.Reputation` | 2 | 2 | 3 | 0.6 | 1.0 |
| `Domain` | 1 | 0 | 0 | 0.0 | 1.0 |
| `Domain.Reputation` | 2 | 4 | 0 | 0.0 | 0.5 |
| `Infrastructure` | 1 | 1 | 4 | 0.8 | 1.0 |
| `Infrastructure.Messaging` | 2 | 1 | 4 | 0.8 | 0.5 |
| `Infrastructure.Options` | 2 | 2 | 0 | 0.0 | 0.5 |
| `Infrastructure.Persistence` | 9 | 2 | 2 | 0.5 | 1.11 |

## Diagrama de paquetes

Fuente: [`paquetes.puml`](paquetes.puml) (PlantUML) y [`paquetes.mmd`](paquetes.mmd). Clases más conectadas: [`clases-centrales.puml`](clases-centrales.puml).

```mermaid
flowchart LR
  subgraph Api
    _global_["(global) (1)"]
  end
  subgraph Application
    QuickPatch_Ranking_Application["Application (1)"]
    QuickPatch_Ranking_Application_Abstractions["Application.Abstractions (5)"]
    QuickPatch_Ranking_Application_Events["Application.Events (6)"]
    QuickPatch_Ranking_Application_Reputation["Application.Reputation (2)"]
  end
  subgraph Domain
    QuickPatch_Ranking_Domain["Domain (1)"]
    QuickPatch_Ranking_Domain_Reputation["Domain.Reputation (2)"]
  end
  subgraph Infrastructure
    QuickPatch_Ranking_Infrastructure["Infrastructure (1)"]
    QuickPatch_Ranking_Infrastructure_Messaging["Infrastructure.Messaging (2)"]
    QuickPatch_Ranking_Infrastructure_Options["Infrastructure.Options (2)"]
    QuickPatch_Ranking_Infrastructure_Persistence["Infrastructure.Persistence (9)"]
  end
  _global_ -->|1| QuickPatch_Ranking_Application
  _global_ -->|1| QuickPatch_Ranking_Infrastructure
  QuickPatch_Ranking_Application -->|1| QuickPatch_Ranking_Application_Reputation
  QuickPatch_Ranking_Application_Abstractions -->|2| QuickPatch_Ranking_Domain_Reputation
  QuickPatch_Ranking_Application_Events -->|1| QuickPatch_Ranking_Application_Abstractions
  QuickPatch_Ranking_Application_Events -->|1| QuickPatch_Ranking_Domain_Reputation
  QuickPatch_Ranking_Application_Reputation -->|4| QuickPatch_Ranking_Application_Abstractions
  QuickPatch_Ranking_Application_Reputation -->|3| QuickPatch_Ranking_Application_Events
  QuickPatch_Ranking_Application_Reputation -->|2| QuickPatch_Ranking_Domain_Reputation
  QuickPatch_Ranking_Infrastructure -->|4| QuickPatch_Ranking_Application_Abstractions
  QuickPatch_Ranking_Infrastructure -->|2| QuickPatch_Ranking_Infrastructure_Messaging
  QuickPatch_Ranking_Infrastructure -->|2| QuickPatch_Ranking_Infrastructure_Options
  QuickPatch_Ranking_Infrastructure -->|5| QuickPatch_Ranking_Infrastructure_Persistence
  QuickPatch_Ranking_Infrastructure_Messaging -->|3| QuickPatch_Ranking_Application_Events
  QuickPatch_Ranking_Infrastructure_Messaging -->|2| QuickPatch_Ranking_Application_Reputation
  QuickPatch_Ranking_Infrastructure_Messaging -->|1| QuickPatch_Ranking_Infrastructure_Options
  QuickPatch_Ranking_Infrastructure_Messaging -->|3| QuickPatch_Ranking_Infrastructure_Persistence
  QuickPatch_Ranking_Infrastructure_Persistence -->|5| QuickPatch_Ranking_Application_Abstractions
  QuickPatch_Ranking_Infrastructure_Persistence -->|4| QuickPatch_Ranking_Domain_Reputation
```
