# ADR-020 — Código transversal compartido entre servicios .NET

- **Estado:** Aceptado (11 de noviembre de 2026, SCRUM-657). Propuesto el 6 de octubre de 2026.
- **Fecha:** 6 de octubre de 2026; aceptado y modificado el 11 de noviembre de 2026
- **Decisión:** La lógica transversal sin dominio de los servicios .NET vive en un repositorio propio, `quickpatch-shared-dotnet`, con un proyecto por mecanismo. Cada servicio lo consume como submódulo en `shared/dotnet`, fijado a una etiqueta `vX.Y.Z`, con `ProjectReference`, solo desde sus capas Infrastructure y Api. No se publica en GitHub Packages.
- **Atributo priorizado:** AC7 Maintainability (Modifiability, Reusability)
- **Atributo sacrificado:** independencia total entre servicios (ADR-013: ningún servicio importa código de otro). Se acepta para código sin dominio.
- **Escenario relacionado:** AC7-E5

## Contexto

Los servicios .NET copiaban el mismo código transversal. La medición del 5 de noviembre (`tests/e2e/evidencias/ac7-mantenibilidad-e2-e3-e5-medicion-2026-11-05.md`) encontró el publicador del Outbox en 4 servicios, `CorrelationId` en 5 (idénticos al 100 %), el contexto de tenant en 6 e idempotencia en al menos 4. AC7-E5 quedó en No cumple.

Las copias ya divergían: ServiceRequest había corregido el apagado de su publicador del Outbox (un tiempo de espera con forma de cancelación ya no apaga el host) y Catalog, Ranking y Payments seguían con la versión anterior. Es exactamente el costo que este ADR anticipaba.

ADR-013 prohíbe que un servicio importe código de **otro servicio**, pero no se pronuncia sobre una librería transversal sin dominio.

## Opciones

1. **Mantener copias** (situación anterior): sin dependencias, pero cada corrección se repite y las copias divergen.
2. **Paquetes NuGet internos** en `quickpatch-shared-dotnet`, publicados en GitHub Packages con versión semántica.
3. **Repositorio propio consumido como submódulo** fijado a una etiqueta, con `ProjectReference`: el mismo mecanismo con el que los servicios ya consumen los contratos (`contracts/api-gateway` y `contracts/kafka`, ADR-021).
4. **Plantilla de servicio** (`dotnet new`) con el código transversal: arranque homogéneo, pero las correcciones posteriores siguen siendo manuales.

## Decisión

Opción 3. Frente a la 2, GitHub Packages exige un token con permiso de lectura en cada `dotnet restore`, también dentro del `docker build` de la imagen, y un pipeline de publicación; con una sola persona en infraestructura (R11) y sin presupuesto (R5), el submódulo da lo mismo (versión fijada por el servicio, actualización con un PR propio) sin credenciales nuevas ni cambios en el CI: el `checkout` ya trae los submódulos y el `Dockerfile` solo suma `COPY shared/ shared/`.

Reglas:

- **Sin dominio.** No hay entidades, eventos, contratos ni reglas de negocio. Cada servicio conserva su base, su DbContext, sus migraciones, sus contratos de `quickpatch-kafka`, sus roles y políticas, y la traducción de errores de base a sus excepciones de dominio.
- **Las capas del servicio no cambian.** Domain y Application no referencian el código compartido. Los puertos (`ITenantUnitOfWork`, `IOutbox`, `IProcessedEventRepository`) siguen en Application. Infrastructure los implementa con adaptadores delgados que delegan en el código compartido, y Api usa la correlación, el registro y la validación del JWT. Así cada servicio sigue siendo un microservicio en capas (ADR-013) y la comunicación entre servicios sigue siendo por eventos (ADR-006, ADR-007): lo compartido es cómo publica y consume cada uno, no qué publica.
- **Un proyecto por mecanismo, pequeño.** `QuickPatch.Transversal.Http` (correlación y registro), `QuickPatch.Transversal.Security` (validación del JWT), `QuickPatch.Transversal.Persistence` (transacción por tenant y rol de sesión) y `QuickPatch.Transversal.Messaging` (Outbox, idempotencia y consumidor de Kafka). Nada de una librería «común» que crezca sin límite; lo que usa un solo servicio se queda en ese servicio.
- **Versión fijada.** Cada servicio fija una etiqueta; actualizar es un PR propio del servicio, con su CI y su despliegue en QA. Un cambio incompatible sube la versión mayor.
- **Matching (Java)** aplica las mismas convenciones en su stack; la equivalencia se verifica con los contratos y las pruebas, no con código compartido.
- **Excepción a ADR-013:** un servicio puede depender de `quickpatch-shared-dotnet`, nunca de otro servicio.

## Alcance (11 de noviembre de 2026)

| Mecanismo | Antes (medición del 5-nov) | Versión | En el código compartido |
|---|---|---|---|
| Publicador del Outbox | Copiado en Catalog, ServiceRequest, Ranking y Payments; Identity con su propia copia en `Outbox.cs` | v0.1.0 (Identity en v0.2.0) | `OutboxPublisher<TContext, TRecord>`, `OutboxOptions` |
| Registro y mapeo de `outbox_events` | Clase y mapeo idénticos en 5 servicios | v0.2.0 | `OutboxEventRecord`, `TransversalModel.MapOutboxEvents` |
| `CorrelationId` | Copiado en 5 servicios | v0.1.0 | `CorrelationId` |
| Registro estructurado | `AddJsonConsole` con scopes en 5 servicios; Communication sin JSON | v0.2.0 | `StructuredLogging.AddQuickPatchJsonConsole` |
| Rol de sesión (`SET LOCAL ROLE` validado) | Copiado en Ranking, Payments, ServiceRequest (2 lugares) e Identity | v0.1.0 (resto en v0.2.0) | `SessionRole` |
| Contexto de tenant (`set_config` de RLS) | En 6 servicios (7 archivos) | v0.2.0 | `TenantTransaction`; cada servicio traduce sus índices únicos a sus excepciones |
| Idempotencia (`processed_events`) | Repositorio, registro y mapeo en ServiceRequest, Payments y Ranking | v0.2.0 | `ProcessedEventStore<TContext>`, `ProcessedEventRecord`, `MapProcessedEvents` |
| Bucle consumidor de Kafka | 10 consumidores con el mismo bucle (consumir, confirmar o volver al mensaje, reintentar) | v0.2.0 | `KafkaConsumerService`; el servicio solo decide qué hacer con cada mensaje |
| Validación del JWT RS256 (ADR-018) | Copiada en Catalog, ServiceRequest, Payments, Communication (2) e Identity | v0.2.1 | `JwtSettings`, `JwtValidation`, `JwtClaims` |
| Problem Details | Un archivo por servicio con sus tipos de error | — | **No se comparte:** los tipos de error son del contrato de cada servicio |

Communication no usa `processed_events`: su idempotencia es la restricción única `source_event_id` del buzón, una regla de su modelo de datos (DD 5.22). La transacción de plataforma de Identity (`PlatformUnitOfWork`, DD 10.4) es de un solo servicio y se queda ahí, aunque ya usa `SessionRole`.

## Consecuencias

### Positivas
- Una corrección se hace una vez y cada servicio la adopta subiendo la etiqueta del submódulo. La corrección del apagado del publicador llegó a los cuatro servicios con la v0.1.0.
- AC7-E5 llega a 0 copias en el stack .NET (`tests/e2e/evidencias/ac7-e5-remedicion-2026-11-11.md`), con el mismo método del 5 de noviembre.
- Las convenciones (tenant, idempotencia, Outbox, consumo, correlación, registro y JWT) las garantiza el mismo código, con sus pruebas en el CI del repositorio compartido: 37 pruebas, incluidas las de PostgreSQL con RLS (Testcontainers) y las del JWT con TestServer.
- Un servicio nuevo (por ejemplo, Actors) arranca con estos mecanismos sin copiar código.

### Costos
- Un repositorio y un pipeline más: 13 repositorios de componentes más el principal (ADR-021).
- Un cambio incompatible obliga a coordinar a los servicios que lo usan.
- Desplegar una corrección del código compartido exige desplegar cada servicio que la adopta, de a uno.

## Trazabilidad

- SAD: escenario AC7-E5; riesgo de la lógica transversal copiada (6.2); ADR-013.
- Relacionados: ADR-005, ADR-007, ADR-012, ADR-013, ADR-018, ADR-021.
- Jira: SCRUM-657 (historia SCRUM-647).
- Versiones: v0.1.0, v0.2.0 y v0.2.1 de `quickpatch-shared-dotnet`, todas del 11 de noviembre de 2026.
