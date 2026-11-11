# Matching — antes

Código de `origin/develop` en `3fade78`, generado el 2026-11-10 con `tools/arquitectura/generar.py`.

| Métrica | Valor |
|---|---|
| Tipos (sin migraciones) | 45 |
| Paquetes | 13 |
| Dependencias entre tipos | 111 |
| Dependencias entre paquetes | 34 |
| Ciclos entre paquetes | 1 |
| Paquetes dentro de ciclos | 3 |
| Ciclos entre tipos | 0 |
| Tipos en el mayor ciclo | 0 |
| Violaciones de SDD 10.3.2 | 0 |
| Tipos de más de 250 líneas | 0 |
| Fan-out máximo (sin raíces de composición) | 10 |
| Fan-out promedio | 2.47 |
| Cohesión relacional promedio (H) | 0.85 |

## Dependencias entre capas

| Desde → hacia | Dependencias |
|---|---|
| Api → Application | 2 |
| Api → Domain | 4 |
| Application → Domain | 29 |
| Infrastructure → Application | 25 |
| Infrastructure → Domain | 16 |

## Clases con más dependencias de salida (fan-out)

| Tipo | Capa | Líneas | Sale | Entra |
|---|---|---|---|---|
| `infrastructure.messaging.KafkaConfig` | Infrastructure | 78 | 10 | 0 |
| `application.events.ServiceRequestCancelledHandler` | Application | 74 | 7 | 2 |
| `application.events.ServiceRequestCompletedHandler` | Application | 56 | 7 | 2 |
| `application.events.TechnicianEventsHandler` | Application | 60 | 7 | 2 |
| `application.matching.MatchingEngine` | Application | 118 | 7 | 3 |
| `application.matching.OfferService` | Application | 128 | 7 | 3 |
| `infrastructure.messaging.TechnicianEventsListener` | Infrastructure | 70 | 5 | 0 |
| `api.http.ApiExceptionHandler` | Api | 65 | 4 | 0 |
| `application.technicians.TechnicianAvailabilityService` | Application | 104 | 4 | 2 |
| `infrastructure.messaging.ServiceRequestCancelledListener` | Infrastructure | 58 | 4 | 0 |

## Clases más usadas (fan-in)

| Tipo | Capa | Entra | Sale |
|---|---|---|---|
| `application.events.Ports` | Application | 13 | 2 |
| `domain.events.InvalidEventException` | Domain | 11 | 0 |
| `domain.matching.Matching` | Domain | 11 | 0 |
| `domain.events.EventEnvelope` | Domain | 10 | 1 |
| `application.matching.MatchingPorts` | Application | 8 | 1 |
| `application.technicians.TechnicianPorts` | Application | 8 | 2 |
| `domain.technicians.Technicians` | Domain | 8 | 0 |
| `domain.events.ServiceRequestCreated` | Domain | 4 | 1 |
| `application.matching.MatchingEngine` | Application | 3 | 7 |
| `application.matching.OfferService` | Application | 3 | 7 |

## Clases más grandes

| Tipo | Capa | Líneas | Archivo |
|---|---|---|---|
| `infrastructure.persistence.JdbcMatchingStores` | Infrastructure | 220 | `src/main/java/co/quickpatch/matching/infrastructure/persistence/JdbcMatchingStores.java` |
| `application.matching.OfferService` | Application | 128 | `src/main/java/co/quickpatch/matching/application/matching/OfferService.java` |
| `application.matching.MatchingEngine` | Application | 118 | `src/main/java/co/quickpatch/matching/application/matching/MatchingEngine.java` |
| `application.technicians.TechnicianAvailabilityService` | Application | 104 | `src/main/java/co/quickpatch/matching/application/technicians/TechnicianAvailabilityService.java` |
| `domain.matching.Matching` | Domain | 98 | `src/main/java/co/quickpatch/matching/domain/matching/Matching.java` |
| `api.security.SecurityConfig` | Api | 92 | `src/main/java/co/quickpatch/matching/api/security/SecurityConfig.java` |
| `infrastructure.messaging.OutboxPublisher` | Infrastructure | 91 | `src/main/java/co/quickpatch/matching/infrastructure/messaging/OutboxPublisher.java` |
| `application.matching.MatchingPorts` | Application | 88 | `src/main/java/co/quickpatch/matching/application/matching/MatchingPorts.java` |
| `infrastructure.messaging.KafkaConfig` | Infrastructure | 78 | `src/main/java/co/quickpatch/matching/infrastructure/messaging/KafkaConfig.java` |
| `application.events.ServiceRequestCancelledHandler` | Application | 74 | `src/main/java/co/quickpatch/matching/application/events/ServiceRequestCancelledHandler.java` |

## Ciclos entre paquetes

- `application.events`, `application.matching`, `application.technicians`

## Violaciones de las reglas de dependencia (SDD 10.3.2)

Ninguna.

## Paquetes

| Paquete | Tipos | Fan-in | Fan-out | Inestabilidad | Cohesión H |
|---|---|---|---|---|---|
| `co.quickpatch.matching` | 1 | 0 | 0 | 0.0 | 1.0 |
| `api.controllers` | 2 | 1 | 4 | 0.8 | 1.0 |
| `api.http` | 3 | 1 | 3 | 0.75 | 1.0 |
| `api.security` | 1 | 0 | 1 | 1.0 | 1.0 |
| `application.events` | 5 | 5 | 5 | 0.5 | 1.0 |
| `application.matching` | 3 | 5 | 5 | 0.5 | 1.33 |
| `application.technicians` | 2 | 5 | 3 | 0.38 | 1.0 |
| `domain.events` | 9 | 3 | 0 | 0.0 | 1.11 |
| `domain.matching` | 1 | 6 | 0 | 0.0 | 1.0 |
| `domain.technicians` | 1 | 6 | 0 | 0.0 | 1.0 |
| `infrastructure.messaging` | 8 | 0 | 5 | 1.0 | 0.12 |
| `infrastructure.persistence` | 6 | 2 | 5 | 0.71 | 0.17 |
| `infrastructure.scheduling` | 3 | 0 | 3 | 1.0 | 0.33 |

## Diagrama de paquetes

Fuente: [`paquetes.puml`](paquetes.puml) (PlantUML) y [`paquetes.mmd`](paquetes.mmd). Clases más conectadas: [`clases-centrales.puml`](clases-centrales.puml).

```mermaid
flowchart LR
  subgraph Api
    co_quickpatch_matching["co.quickpatch.matching (1)"]
    co_quickpatch_matching_api_controllers["api.controllers (2)"]
    co_quickpatch_matching_api_http["api.http (3)"]
    co_quickpatch_matching_api_security["api.security (1)"]
  end
  subgraph Application
    co_quickpatch_matching_application_events["application.events (5)"]
    co_quickpatch_matching_application_matching["application.matching (3)"]
    co_quickpatch_matching_application_technicians["application.technicians (2)"]
  end
  subgraph Domain
    co_quickpatch_matching_domain_events["domain.events (9)"]
    co_quickpatch_matching_domain_matching["domain.matching (1)"]
    co_quickpatch_matching_domain_technicians["domain.technicians (1)"]
  end
  subgraph Infrastructure
    co_quickpatch_matching_infrastructure_messaging["infrastructure.messaging (8)"]
    co_quickpatch_matching_infrastructure_persistence["infrastructure.persistence (6)"]
    co_quickpatch_matching_infrastructure_scheduling["infrastructure.scheduling (3)"]
  end
  co_quickpatch_matching_api_controllers -->|1| co_quickpatch_matching_application_matching
  co_quickpatch_matching_api_controllers -->|1| co_quickpatch_matching_application_technicians
  co_quickpatch_matching_api_controllers -->|1| co_quickpatch_matching_domain_matching
  co_quickpatch_matching_api_controllers -->|1| co_quickpatch_matching_domain_technicians
  co_quickpatch_matching_api_http -->|1| co_quickpatch_matching_api_controllers
  co_quickpatch_matching_api_http -->|1| co_quickpatch_matching_domain_matching
  co_quickpatch_matching_api_http -->|1| co_quickpatch_matching_domain_technicians
  co_quickpatch_matching_api_security -->|1| co_quickpatch_matching_api_http
  co_quickpatch_matching_application_events -->|2| co_quickpatch_matching_application_matching
  co_quickpatch_matching_application_events -->|3| co_quickpatch_matching_application_technicians
  co_quickpatch_matching_application_events -->|12| co_quickpatch_matching_domain_events
  co_quickpatch_matching_application_events -->|3| co_quickpatch_matching_domain_matching
  co_quickpatch_matching_application_events -->|2| co_quickpatch_matching_domain_technicians
  co_quickpatch_matching_application_matching -->|2| co_quickpatch_matching_application_events
  co_quickpatch_matching_application_matching -->|2| co_quickpatch_matching_application_technicians
  co_quickpatch_matching_application_matching -->|4| co_quickpatch_matching_domain_events
  co_quickpatch_matching_application_matching -->|3| co_quickpatch_matching_domain_matching
  co_quickpatch_matching_application_matching -->|1| co_quickpatch_matching_domain_technicians
  co_quickpatch_matching_application_technicians -->|1| co_quickpatch_matching_application_events
  co_quickpatch_matching_application_technicians -->|2| co_quickpatch_matching_domain_matching
  co_quickpatch_matching_application_technicians -->|2| co_quickpatch_matching_domain_technicians
  co_quickpatch_matching_infrastructure_messaging -->|9| co_quickpatch_matching_application_events
  co_quickpatch_matching_infrastructure_messaging -->|5| co_quickpatch_matching_application_matching
  co_quickpatch_matching_infrastructure_messaging -->|2| co_quickpatch_matching_application_technicians
  co_quickpatch_matching_infrastructure_messaging -->|14| co_quickpatch_matching_domain_events
  co_quickpatch_matching_infrastructure_messaging -->|1| co_quickpatch_matching_infrastructure_persistence
  co_quickpatch_matching_infrastructure_persistence -->|3| co_quickpatch_matching_application_events
  co_quickpatch_matching_infrastructure_persistence -->|1| co_quickpatch_matching_application_matching
  co_quickpatch_matching_infrastructure_persistence -->|1| co_quickpatch_matching_application_technicians
  co_quickpatch_matching_infrastructure_persistence -->|1| co_quickpatch_matching_domain_matching
  co_quickpatch_matching_infrastructure_persistence -->|1| co_quickpatch_matching_domain_technicians
  co_quickpatch_matching_infrastructure_scheduling -->|2| co_quickpatch_matching_application_events
  co_quickpatch_matching_infrastructure_scheduling -->|2| co_quickpatch_matching_application_matching
  co_quickpatch_matching_infrastructure_scheduling -->|2| co_quickpatch_matching_infrastructure_persistence
  style co_quickpatch_matching_application_events fill:#FFCDD2
  style co_quickpatch_matching_application_matching fill:#FFCDD2
  style co_quickpatch_matching_application_technicians fill:#FFCDD2
  linkStyle 8 stroke:#EF6C00,stroke-width:2px
  linkStyle 9 stroke:#EF6C00,stroke-width:2px
  linkStyle 13 stroke:#EF6C00,stroke-width:2px
  linkStyle 14 stroke:#EF6C00,stroke-width:2px
  linkStyle 18 stroke:#EF6C00,stroke-width:2px
```
