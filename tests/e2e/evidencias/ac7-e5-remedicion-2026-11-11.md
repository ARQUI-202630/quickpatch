# AC7-E5: mediciones tras ADR-020 (11 de noviembre de 2026)

AC7-E5 pide 0 copias de la lógica transversal entre servicios del mismo stack. El escenario nombra contexto de tenant, idempotencia, Outbox y logging (`docs/testing/matriz-escenarios-calidad-52.md`, sección 5).

Se usó el mismo método de la medición del 5 de noviembre (`ac7-mantenibilidad-e2-e3-e5-medicion-2026-11-05.md`): buscar en el `src/` de cada servicio .NET, sin contar las migraciones, el código propio de cada mecanismo. El submódulo `shared/dotnet` no cuenta como copia, porque es la implementación única. Hubo dos mediciones el mismo día.

## Segunda medición: v0.2.1 (resultado final)

Se midieron las ramas de los PR de adopción (catalog #21, service-request #46, ranking #15, payments #21, identity #40 y communication #26), que se fusionan a `develop` sin cambios.

| Servicio | Commit | `shared/dotnet` |
|---|---|---|
| identity | 86b3f15 | v0.2.1 |
| catalog | e4a8a71 | v0.2.1 |
| service-request | d19dda5 | v0.2.1 |
| payments | 107e2ec | v0.2.1 |
| communication | 673e611 | v0.2.1 |
| ranking | e84bd39 | v0.2.1 |

Cuántas veces aparece el código propio de cada mecanismo en el `src/` de los 6 servicios. El buscador se indica entre paréntesis.

| Lógica | 5-nov | v0.1.0 | v0.2.1 | Implementación única |
|---|---|---|---|---|
| Contexto de tenant (`set_config(` fuera de comentarios) | 6 servicios | 6 | **0** | `TenantTransaction` |
| Idempotencia (`ProcessedEvents.AnyAsync`, `class ProcessedEventRecord`, `Entity<ProcessedEventRecord>`) | al menos 4 | 3 | **0** | `ProcessedEventStore<TContext>`, `ProcessedEventRecord`, `MapProcessedEvents` |
| Publicador del Outbox (`SKIP LOCKED`) | 4 | 1 (identity) | **0** | `OutboxPublisher<TContext, TRecord>` |
| Registro y mapeo del Outbox (`class OutboxEventRecord`, `Entity<OutboxEventRecord>`) | no medido | 5 | **0** | `OutboxEventRecord`, `MapOutboxEvents` |
| Bucle consumidor de Kafka (`consumer.Consume(`) | no medido | 10 | **0** | `KafkaConsumerService` |
| Logging (`AddJsonConsole`) | no medido | 5 | **0** | `AddQuickPatchJsonConsole` |
| Correlación (middleware propio de `X-Correlation-Id`) | 5 | 0 | **0** | `CorrelationId` |
| Rol de sesión (`SET LOCAL ROLE`) | no medido | 4 (identity 2, service-request 2) | **0** | `SessionRole` |
| Validación del JWT RS256 (`RSA.Create()` o `new TokenValidationParameters` en Api) | no medido | 6 | **0** | `JwtValidation`, `JwtClaims`, `JwtSettings` |

**Resultado: cumple.** No quedan copias de la lógica transversal en el stack .NET. Matching (Java y Spring Boot) es el único servicio de su stack, así que ahí ya había una sola implementación.

### Las capas no cambian

Ningún archivo de las capas Domain o Application de los 6 servicios referencia `QuickPatch.Transversal` (`git grep` sobre `src/*Domain*` y `src/*Application*`: 0 archivos). Los puertos `ITenantUnitOfWork`, `IOutbox` e `IProcessedEventRepository` siguen en Application. Infrastructure los implementa con adaptadores delgados que delegan en el código compartido, y cada servicio conserva la traducción de sus índices únicos a sus excepciones de dominio.

Tampoco cambian el esquema ni los contratos:
- `dotnet ef migrations has-pending-model-changes` no encontró cambios en los 5 servicios con Outbox o idempotencia.
- Los contratos REST y de eventos son los mismos.

### Lo que no se cuenta como copia

| Caso | Por qué no es una copia |
|---|---|
| Problem Details de cada servicio | Los tipos de error son del contrato de cada servicio (ADR-020) |
| Idempotencia de Communication | Es la restricción única `source_event_id` del buzón (DD 5.22), una regla de su modelo de datos; no usa `processed_events` |
| `PlatformUnitOfWork` de Identity (DD 10.4) | Solo existe en Identity; ya usa `SessionRole` |
| Nombre de la cabecera `X-Correlation-Id` en la llamada saliente de ServiceRequest a Identity (`IdentityUserDirectory`) | Es un literal de una línea en Infrastructure, no lógica |
| Propiedades `DbSet<OutboxEventRecord>` y `DbSet<ProcessedEventRecord>` | Exponen el tipo común en el DbContext de cada servicio |

### Pruebas

| Proyecto | Unitarias | Integración | Cobertura de líneas |
|---|---|---|---|
| quickpatch-shared-dotnet v0.2.1 | 37 (incluye PostgreSQL con RLS y JWT con TestServer) | | 91,26 % |
| identity | 292 | 49 | 91,25 % |
| catalog | 25 | 9 | 83,09 % |
| service-request | 395 | 62 | 93,37 % |
| payments | 91 | 12 | 90,97 % |
| communication | 180 | 8 | 80,77 % |
| ranking | 37 | 5 | 87,27 % |

La cobertura de catalog y communication bajó respecto al 5-nov porque se borraron líneas propias que estaban cubiertas. Las dos siguen sobre el 80 % que exige el CI.

## Primera medición: v0.1.0 (historial)

Se midió con el `develop` de cada servicio después de fusionar la v0.1.0:

| Servicio | Commit |
|---|---|
| identity | 359eb39 |
| catalog | 48a3308 |
| service-request | ca57833 |
| payments | 202a8f7 |
| communication | a769ddc |
| ranking | 599c26f |

Bajaron a 0 la correlación y el publicador del Outbox con el nombre medido el 5-nov. Quedaban:
- el contexto de tenant, en 6 servicios;
- la idempotencia, en 4;
- el publicador propio de identity dentro de `Outbox.cs`.

Resultado de esa medición: **no cumple**, con avance parcial.

Con esa versión, los 6 servicios se desplegaron en QA:

| Servicio | Versión |
|---|---|
| identity | 0.10.1 |
| catalog | 0.4.3 |
| service-request | 0.12.2 |
| ranking | 0.1.2 |
| payments | 0.3.2 |
| communication | 0.3.4 |

Después pasó la regresión contra QA:
- `humo-flujo-critico`: 29/29 aserciones;
- `scrum-483-chat`: 69/69 aserciones.

En service-request, payments y communication hubo que reintentar el despliegue. El pod viejo seguía en «pending termination» más de 180 s y el CI revertía la versión, que estaba bien. Esto ya pasaba antes del código compartido.

## Límites

- Es una búsqueda por texto y por nombre, no una revisión de pares. Los buscadores están en la tabla para que cualquiera pueda repetir la medición.
- La regresión en QA de la v0.2.1 está en `ac7-e5-regresion-qa-2026-11-11.txt`: identity 0.10.2, catalog 0.4.4, service-request 0.12.3, ranking 0.1.3, payments 0.3.3 y communication 0.3.5 desplegados al primer intento; `humo-flujo-critico` 29/29 y `scrum-483-chat` 69/69 aserciones.
