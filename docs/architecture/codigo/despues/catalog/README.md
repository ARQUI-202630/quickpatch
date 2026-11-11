# Catalog — despues

Código de `origin/develop` en `44373e3`, generado el 2026-11-11 con `tools/arquitectura/generar.py`.

| Métrica | Valor |
|---|---|
| Tipos (sin migraciones) | 43 |
| Paquetes | 14 |
| Dependencias entre tipos | 84 |
| Dependencias entre paquetes | 26 |
| Ciclos entre paquetes | 0 |
| Paquetes dentro de ciclos | 0 |
| Ciclos entre tipos | 0 |
| Tipos en el mayor ciclo | 0 |
| Violaciones de SDD 10.3.2 | 0 |
| Tipos de más de 250 líneas | 0 |
| Fan-out máximo (sin raíces de composición) | 15 |
| Fan-out promedio | 1.95 |
| Cohesión relacional promedio (H) | 0.86 |

## Dependencias entre capas

| Desde → hacia | Dependencias |
|---|---|
| Api → Application | 7 |
| Api → Domain | 4 |
| Api → Infrastructure | 1 |
| Application → Domain | 6 |
| Infrastructure → Application | 8 |
| Infrastructure → Domain | 2 |

## Clases con más dependencias de salida (fan-out)

| Tipo | Capa | Líneas | Sale | Entra |
|---|---|---|---|---|
| `Api.Endpoints.CategoryEndpoints` | Api | 88 | 15 | 1 |
| `Application.Categories.CreateCategoryHandler` | Application | 34 | 7 | 2 |
| `Application.Categories.UpdateCategoryHandler` | Application | 28 | 6 | 2 |
| `Application.Events.CategoryChangedEvent` | Application | 17 | 4 | 2 |
| `Infrastructure.Persistence.EfOutbox` | Infrastructure | 16 | 4 | 1 |
| `Application.Categories.ListCategoriesHandler` | Application | 4 | 3 | 2 |
| `Infrastructure.Messaging.OutboxPublisher` | Infrastructure | 84 | 3 | 1 |
| `Infrastructure.Persistence.CategoryRepository` | Infrastructure | 14 | 3 | 1 |
| `Infrastructure.Persistence.TenantUnitOfWork` | Infrastructure | 30 | 3 | 1 |
| `Api.Security.AuthenticationSetup` | Api | 39 | 2 | 1 |

## Clases más usadas (fan-in)

| Tipo | Capa | Entra | Sale |
|---|---|---|---|
| `Domain.Categories.Category` | Domain | 11 | 1 |
| `Infrastructure.Persistence.CatalogDbContext` | Infrastructure | 6 | 2 |
| `Application.Abstractions.ICategoryRepository` | Application | 5 | 1 |
| `Application.Abstractions.ITenantUnitOfWork` | Application | 5 | 0 |
| `Application.Abstractions.IOutbox` | Application | 4 | 1 |
| `Api.Http.CorrelationId` | Api | 3 | 0 |
| `Application.Abstractions.OutboxMessage` | Application | 3 | 0 |
| `Infrastructure.Persistence.OutboxEventRecord` | Infrastructure | 3 | 0 |
| `Api.Security.AuthenticatedUser` | Api | 2 | 0 |
| `Api.Security.ChannelOptions` | Api | 2 | 0 |

## Clases más grandes

| Tipo | Capa | Líneas | Archivo |
|---|---|---|---|
| `Domain.Categories.Category` | Domain | 97 | `src/QuickPatch.Catalog.Domain/Categories/Category.cs` |
| `Api.Endpoints.CategoryEndpoints` | Api | 88 | `src/QuickPatch.Catalog.Api/Endpoints/CategoryEndpoints.cs` |
| `Infrastructure.Messaging.OutboxPublisher` | Infrastructure | 84 | `src/QuickPatch.Catalog.Infrastructure/Messaging/OutboxPublisher.cs` |
| `Api.Security.AuthenticationSetup` | Api | 39 | `src/QuickPatch.Catalog.Api/Security/AuthenticatedUser.cs` |
| `Infrastructure.Persistence.CatalogDbContext` | Infrastructure | 37 | `src/QuickPatch.Catalog.Infrastructure/Persistence/CatalogDbContext.cs` |
| `Application.Categories.CreateCategoryHandler` | Application | 34 | `src/QuickPatch.Catalog.Application/Categories/CreateCategory.cs` |
| `Infrastructure.Persistence.TenantUnitOfWork` | Infrastructure | 30 | `src/QuickPatch.Catalog.Infrastructure/Persistence/TenantUnitOfWork.cs` |
| `Application.Categories.UpdateCategoryHandler` | Application | 28 | `src/QuickPatch.Catalog.Application/Categories/UpdateCategory.cs` |
| `Api.Http.BadRequestExceptionHandler` | Api | 24 | `src/QuickPatch.Catalog.Api/Http/BadRequestExceptionHandler.cs` |
| `Api.Security.RequestTenant` | Api | 24 | `src/QuickPatch.Catalog.Api/Security/RequestTenant.cs` |

## Ciclos entre paquetes

Ninguno.

## Violaciones de las reglas de dependencia (SDD 10.3.2)

Ninguna.

## Paquetes

| Paquete | Tipos | Fan-in | Fan-out | Inestabilidad | Cohesión H |
|---|---|---|---|---|---|
| `(global)` | 1 | 0 | 5 | 1.0 | 1.0 |
| `Api.Endpoints` | 5 | 1 | 5 | 0.83 | 1.0 |
| `Api.Http` | 3 | 2 | 0 | 0.0 | 0.67 |
| `Api.Security` | 6 | 2 | 0 | 0.0 | 0.83 |
| `Application` | 1 | 1 | 1 | 0.5 | 1.0 |
| `Application.Abstractions` | 5 | 4 | 1 | 0.2 | 0.4 |
| `Application.Categories` | 6 | 2 | 3 | 0.6 | 0.67 |
| `Application.Events` | 3 | 1 | 2 | 0.67 | 1.0 |
| `Domain.Categories` | 1 | 5 | 1 | 0.17 | 1.0 |
| `Domain.Common` | 1 | 2 | 0 | 0.0 | 1.0 |
| `Infrastructure` | 1 | 1 | 4 | 0.8 | 1.0 |
| `Infrastructure.Messaging` | 1 | 1 | 2 | 0.67 | 1.0 |
| `Infrastructure.Options` | 2 | 2 | 0 | 0.0 | 0.5 |
| `Infrastructure.Persistence` | 7 | 2 | 2 | 0.5 | 1.0 |

## Diagrama de paquetes

Fuente: [`paquetes.puml`](paquetes.puml) (PlantUML) y [`paquetes.mmd`](paquetes.mmd). Clases más conectadas: [`clases-centrales.puml`](clases-centrales.puml).

```mermaid
flowchart LR
  subgraph Api
    _global_["(global) (1)"]
    QuickPatch_Catalog_Api_Endpoints["Api.Endpoints (5)"]
    QuickPatch_Catalog_Api_Http["Api.Http (3)"]
    QuickPatch_Catalog_Api_Security["Api.Security (6)"]
  end
  subgraph Application
    QuickPatch_Catalog_Application["Application (1)"]
    QuickPatch_Catalog_Application_Abstractions["Application.Abstractions (5)"]
    QuickPatch_Catalog_Application_Categories["Application.Categories (6)"]
    QuickPatch_Catalog_Application_Events["Application.Events (3)"]
  end
  subgraph Domain
    QuickPatch_Catalog_Domain_Categories["Domain.Categories (1)"]
    QuickPatch_Catalog_Domain_Common["Domain.Common (1)"]
  end
  subgraph Infrastructure
    QuickPatch_Catalog_Infrastructure["Infrastructure (1)"]
    QuickPatch_Catalog_Infrastructure_Messaging["Infrastructure.Messaging (1)"]
    QuickPatch_Catalog_Infrastructure_Options["Infrastructure.Options (2)"]
    QuickPatch_Catalog_Infrastructure_Persistence["Infrastructure.Persistence (7)"]
  end
  _global_ -->|1| QuickPatch_Catalog_Api_Endpoints
  _global_ -->|3| QuickPatch_Catalog_Api_Http
  _global_ -->|3| QuickPatch_Catalog_Api_Security
  _global_ -->|1| QuickPatch_Catalog_Application
  _global_ -->|1| QuickPatch_Catalog_Infrastructure
  QuickPatch_Catalog_Api_Endpoints -->|1| QuickPatch_Catalog_Api_Http
  QuickPatch_Catalog_Api_Endpoints -->|2| QuickPatch_Catalog_Api_Security
  QuickPatch_Catalog_Api_Endpoints -->|6| QuickPatch_Catalog_Application_Categories
  QuickPatch_Catalog_Api_Endpoints -->|3| QuickPatch_Catalog_Domain_Categories
  QuickPatch_Catalog_Api_Endpoints -->|1| QuickPatch_Catalog_Domain_Common
  QuickPatch_Catalog_Application -->|3| QuickPatch_Catalog_Application_Categories
  QuickPatch_Catalog_Application_Abstractions -->|1| QuickPatch_Catalog_Domain_Categories
  QuickPatch_Catalog_Application_Categories -->|8| QuickPatch_Catalog_Application_Abstractions
  QuickPatch_Catalog_Application_Categories -->|2| QuickPatch_Catalog_Application_Events
  QuickPatch_Catalog_Application_Categories -->|4| QuickPatch_Catalog_Domain_Categories
  QuickPatch_Catalog_Application_Events -->|1| QuickPatch_Catalog_Application_Abstractions
  QuickPatch_Catalog_Application_Events -->|1| QuickPatch_Catalog_Domain_Categories
  QuickPatch_Catalog_Domain_Categories -->|1| QuickPatch_Catalog_Domain_Common
  QuickPatch_Catalog_Infrastructure -->|3| QuickPatch_Catalog_Application_Abstractions
  QuickPatch_Catalog_Infrastructure -->|1| QuickPatch_Catalog_Infrastructure_Messaging
  QuickPatch_Catalog_Infrastructure -->|2| QuickPatch_Catalog_Infrastructure_Options
  QuickPatch_Catalog_Infrastructure -->|4| QuickPatch_Catalog_Infrastructure_Persistence
  QuickPatch_Catalog_Infrastructure_Messaging -->|1| QuickPatch_Catalog_Infrastructure_Options
  QuickPatch_Catalog_Infrastructure_Messaging -->|2| QuickPatch_Catalog_Infrastructure_Persistence
  QuickPatch_Catalog_Infrastructure_Persistence -->|5| QuickPatch_Catalog_Application_Abstractions
  QuickPatch_Catalog_Infrastructure_Persistence -->|2| QuickPatch_Catalog_Domain_Categories
```
