# AC7-E5: nueva medición tras ADR-020 (v0.1.0)

Medición del 11 de noviembre de 2026 sobre `develop` de los 6 servicios .NET, después de fusionar la adopción de `quickpatch-shared-dotnet` v0.1.0 (SCRUM-657). Es el mismo método de la medición del 5 de noviembre (`ac7-mantenibilidad-e2-e3-e5-medicion-2026-11-05.md`): se buscan en `src/` (sin migraciones) los archivos de cada lógica transversal. El submódulo `shared/dotnet` no cuenta como copia: es la implementación única.

| Servicio | Commit de `develop` |
|---|---|
| identity | 359eb39 |
| catalog | 48a3308 |
| service-request | ca57833 |
| payments | 202a8f7 |
| communication | a769ddc |
| ranking | 599c26f |

## Resultado por lógica

| Lógica | Copias el 5-nov | Copias el 11-nov | Dónde está ahora |
|---|---|---|---|
| Publicador del Outbox (`OutboxPublisher.cs`) | 4 | **0** | `QuickPatch.Transversal.Messaging` en catalog, service-request, payments y ranking |
| Identificador de correlación (`CorrelationId.cs`) | 5 | **0** | `QuickPatch.Transversal.Http` en identity, catalog, service-request, payments y communication |
| Rol de sesión de PostgreSQL (`SessionRole.cs`) | no medido | **0** | `QuickPatch.Transversal.Persistence` |
| Contexto de tenant (`set_config` de RLS) | 6 | 6 | `Repositories.cs`, `TenantUnitOfWork.cs`, `ChatStore.cs` e `InboxStore.cs` de cada servicio |
| Idempotencia (`processed_events`) | al menos 4 | 4 | service-request, payments, communication y ranking |

Hallazgo que el 5-nov no contó: identity tiene su propio publicador del Outbox dentro de `Infrastructure/Messaging/Outbox.cs` (con `FOR UPDATE SKIP LOCKED`), con otro nombre de archivo. No se migró en esta versión porque identity está en refactor (SCRUM-650); queda como copia pendiente.

## Resultado

**Sigue sin cumplir, con avance parcial.** La meta es 0 copias. Bajaron a 0 la correlación y el publicador del Outbox con el nombre medido, pero quedan el contexto de tenant (6), la idempotencia (4) y el publicador propio de identity. ADR-020 explica por qué tenant e idempotencia no se compartieron: están mezclados con reglas de cada servicio.

## Despliegue y regresión en QA

Los 6 servicios se desplegaron en QA uno por uno el 11-nov: identity 0.10.1, catalog 0.4.3, service-request 0.12.2, ranking 0.1.2, payments 0.3.2 y communication 0.3.4. Después corrieron contra QA `humo-flujo-critico` (29/29 aserciones) y `scrum-483-chat` (69/69), con evidencia en `humo-flujo-critico-qa-2026-11-11.txt` y `scrum-483-chat-qa-2026-11-11.txt`.

Service-request, payments y communication necesitaron reintentar el job de despliegue. El pod nuevo quedaba listo, pero el viejo seguía en «pending termination» más de 180 s y el CI revertía. Esto ya pasaba con versiones anteriores, así que no viene del código compartido. Communication pasó al esperar 4 minutos antes de reintentar.

## Límites

- Es una búsqueda por nombre de archivo y por texto (`set_config`, `processed_events`, `FOR UPDATE SKIP LOCKED`), no una revisión de pares.
- No se comparó el contenido de las copias que quedan.
