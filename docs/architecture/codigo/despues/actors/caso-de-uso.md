# Actors — código del caso de uso principal (despues)

Nivel 4 del modelo C4 ([c4model.com/diagrams](https://c4model.com/diagrams)): las clases del caso de uso principal, **proyección de technician.registered y .verification-changed (SCRUM-640)**, desde su clase de entrada hasta los adaptadores, con un bloque por capa (SDD 10.3.1 y 10.3.2). El resto del servicio repite el patrón y está en su diagrama de componentes (C4-04) y en [`paquetes.mmd`](paquetes.mmd).

Generado desde el código compilado de `origin/develop` (`2759bd6`) el 2026-11-23 con `tools/arquitectura/generar.py` (SCRUM-715). No se edita a mano.

```mermaid
classDiagram
    direction LR
    namespace Application {
        class TechnicianEventsHandler
        class ITenantUnitOfWork {
            <<interface>>
        }
        class ITechnicianActorRepository {
            <<interface>>
        }
        class ISupplierRepository {
            <<interface>>
        }
        class IProcessedEventRepository {
            <<interface>>
        }
    }
    namespace Domain {
        class Supplier
        class TechnicianActor
    }
    namespace Infrastructure {
        class TechnicianEventsConsumer
        class TenantUnitOfWork
        class TechnicianActorRepository
        class SupplierRepository
        class ProcessedEventRepository
    }
    TechnicianEventsConsumer --> TechnicianEventsHandler : invoca
    TechnicianEventsHandler --> ITenantUnitOfWork : usa
    TenantUnitOfWork ..|> ITenantUnitOfWork : implementa
    TechnicianEventsHandler --> ITechnicianActorRepository : usa
    TechnicianActorRepository ..|> ITechnicianActorRepository : implementa
    TechnicianEventsHandler --> ISupplierRepository : usa
    SupplierRepository ..|> ISupplierRepository : implementa
    TechnicianEventsHandler --> IProcessedEventRepository : usa
    ProcessedEventRepository ..|> IProcessedEventRepository : implementa
    TechnicianEventsHandler ..> Supplier : crea o usa
    TechnicianEventsHandler ..> TechnicianActor : crea o usa
```

**Cómo leerlo.** `-->` es una dependencia inyectada por el constructor; `..|>`, una clase que implementa un puerto (un adaptador de Infrastructure o un colaborador de Application); `..>`, un tipo del dominio que el caso de uso o sus colaboradores usan, según el IL (.NET) o el bytecode (Java). No se dibujan las dependencias transversales: `ILogger`, `TimeProvider`.

| Clase | Capa | Archivo |
|---|---|---|
| `Infrastructure.Messaging.TechnicianEventsConsumer` | Infrastructure | `src/QuickPatch.Actors.Infrastructure/Messaging/TechnicianEventsConsumer.cs` |
| `Application.Technicians.TechnicianEventsHandler` | Application | `src/QuickPatch.Actors.Application/Technicians/TechnicianEventsHandler.cs` |
| `Application.Abstractions.ITenantUnitOfWork` | Application | `` |
| `Infrastructure.Persistence.TenantUnitOfWork` | Infrastructure | `src/QuickPatch.Actors.Infrastructure/Persistence/TenantUnitOfWork.cs` |
| `Application.Abstractions.ITechnicianActorRepository` | Application | `` |
| `Infrastructure.Persistence.TechnicianActorRepository` | Infrastructure | `src/QuickPatch.Actors.Infrastructure/Persistence/TechnicianActorRepository.cs` |
| `Application.Abstractions.ISupplierRepository` | Application | `` |
| `Infrastructure.Persistence.SupplierRepository` | Infrastructure | `src/QuickPatch.Actors.Infrastructure/Persistence/SupplierRepository.cs` |
| `Application.Abstractions.IProcessedEventRepository` | Application | `` |
| `Infrastructure.Persistence.ProcessedEventRepository` | Infrastructure | `src/QuickPatch.Actors.Infrastructure/Persistence/ProcessedEventRepository.cs` |
| `Domain.Suppliers.Supplier` | Domain | `src/QuickPatch.Actors.Domain/Suppliers/Supplier.cs` |
| `Domain.Technicians.TechnicianActor` | Domain | `src/QuickPatch.Actors.Domain/Technicians/TechnicianActor.cs` |
