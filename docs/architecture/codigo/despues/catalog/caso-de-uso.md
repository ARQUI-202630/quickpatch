# Catalog — código del caso de uso principal (despues)

Nivel 4 del modelo C4 ([c4model.com/diagrams](https://c4model.com/diagrams)): las clases del caso de uso principal, **alta de una categoría (ADR-007, ADR-025)**, desde su clase de entrada hasta los adaptadores, con un bloque por capa (SDD 10.3.1 y 10.3.2). El resto del servicio repite el patrón y está en su diagrama de componentes (C4-04) y en [`paquetes.mmd`](paquetes.mmd).

Generado desde el código compilado de `origin/develop` (`9c574e0`) el 2026-11-23 con `tools/arquitectura/generar.py` (SCRUM-715). No se edita a mano.

```mermaid
classDiagram
    direction LR
    namespace Api {
        class CategoryEndpoints
    }
    namespace Application {
        class CreateCategoryHandler
        class ITenantUnitOfWork {
            <<interface>>
        }
        class ICategoryRepository {
            <<interface>>
        }
        class IOutbox {
            <<interface>>
        }
    }
    namespace Domain {
        class Category
    }
    namespace Infrastructure {
        class TenantUnitOfWork
        class CategoryRepository
        class EfOutbox
    }
    CategoryEndpoints --> CreateCategoryHandler : invoca
    CreateCategoryHandler --> ITenantUnitOfWork : usa
    TenantUnitOfWork ..|> ITenantUnitOfWork : implementa
    CreateCategoryHandler --> ICategoryRepository : usa
    CategoryRepository ..|> ICategoryRepository : implementa
    CreateCategoryHandler --> IOutbox : usa
    EfOutbox ..|> IOutbox : implementa
    CreateCategoryHandler ..> Category : crea o usa
```

**Cómo leerlo.** `-->` es una dependencia inyectada por el constructor; `..|>`, una clase que implementa un puerto (un adaptador de Infrastructure o un colaborador de Application); `..>`, un tipo del dominio que el caso de uso o sus colaboradores usan, según el IL (.NET) o el bytecode (Java). No se dibujan las dependencias transversales: `TimeProvider`.

| Clase | Capa | Archivo |
|---|---|---|
| `Api.Endpoints.CategoryEndpoints` | Api | `src/QuickPatch.Catalog.Api/Endpoints/CategoryEndpoints.cs` |
| `Application.Categories.CreateCategoryHandler` | Application | `src/QuickPatch.Catalog.Application/Categories/CreateCategory.cs` |
| `Application.Abstractions.ITenantUnitOfWork` | Application | `` |
| `Infrastructure.Persistence.TenantUnitOfWork` | Infrastructure | `src/QuickPatch.Catalog.Infrastructure/Persistence/TenantUnitOfWork.cs` |
| `Application.Abstractions.ICategoryRepository` | Application | `` |
| `Infrastructure.Persistence.CategoryRepository` | Infrastructure | `src/QuickPatch.Catalog.Infrastructure/Persistence/CategoryRepository.cs` |
| `Application.Abstractions.IOutbox` | Application | `` |
| `Infrastructure.Persistence.EfOutbox` | Infrastructure | `src/QuickPatch.Catalog.Infrastructure/Persistence/EfOutbox.cs` |
| `Domain.Categories.Category` | Domain | `src/QuickPatch.Catalog.Domain/Categories/Category.cs` |
