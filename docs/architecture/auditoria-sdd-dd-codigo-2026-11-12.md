# Auditoría de SDD y DD contra el código (SCRUM-693, 12 de noviembre de 2026)

Esta auditoría forma parte de SCRUM-690. Compara el SDD y el DD con las fuentes de verdad de cada dato:

| Dato | Fuente de verdad |
|---|---|
| Tablas y columnas | Snapshots de EF Core (`*ModelSnapshot.cs`) de los 6 servicios .NET y migraciones Flyway de Matching, en `develop` |
| Eventos, productores y consumidores | `topics/topics.yaml` y `events/` de `quickpatch-kafka` v0.10.0, y las suscripciones en el código de cada consumidor |
| Rutas REST | `openapi/` y `asyncapi/` de `quickpatch-api-gateway` v0.24.0 |

Los scripts de la comparación son de un solo uso y no se versionan. El método se puede repetir:
1. Sacar las columnas por tabla con `HasColumnName` y `ToTable` de cada snapshot, y con `create table` y `alter table` de las migraciones SQL.
2. Sacar las columnas de cada sección «Tabla» del DD (sección 5).
3. Comparar las rutas `/v1/...` y los nombres de eventos de los documentos contra los contratos.

## Discrepancias y corrección

| # | Documento | Valor anterior | Valor correcto | Fuente de verdad | Corrección |
|---|---|---|---|---|---|
| 1 | DD 3, Figura 1, Cuadro 8 | Ranking «sin tablas en esta versión» | `technician_reputations` y `applied_ratings` en `db_ranking` | Snapshot de Ranking (migración `Inicial`) | DD 5.29 y 5.30 nuevas; secciones 3, 6 y 10.1 y figuras 1 y 2 |
| 2 | DD 5.3 | `technician_profiles` sin `rating_count`, `low_reputation` ni `reputation_changed_at` | Las tres columnas existen | Snapshot de Identity (migración `ReputacionTecnico`) | Filas nuevas en 5.3 |
| 3 | DD figuras 1 y 2 | Faltaban 10 tablas: tokens y recuperación de contraseña, `tenant_status_replica`, `payment_technicians`, buzón y chat, y las 2 de Ranking. El texto decía que las figuras tenían «exactamente las mismas entidades» que el diccionario | Las 28 tablas del diccionario más las 2 de Ranking | Diccionario (sección 5) y snapshots | Entidades, relaciones físicas y referencias lógicas agregadas |
| 4 | DD Cuadro 8 | Estado al 14 de octubre: Communication y Payments sin tablas, y varias pendientes en Identity y ServiceRequest | Todas implementadas; solo Actors sin tablas | Snapshots y migraciones | Cuadro al 12 de noviembre |
| 5 | DD 3 | Identity sin `client_companies`; ServiceRequest sin la copia de `localities` (P-09); Communication solo con `notifications`; «transversal en cada servicio» | Las tablas reales de cada servicio; las transversales solo donde existen | Snapshots | Filas corregidas |
| 6 | DD Cuadro 11 | Communication como consumidor de `service-request.completed`, `service-request.rated`, `payment.approved` y `payment.rejected` | Communication no los consume: avisa con `service-request.status-changed` | `topics.yaml` v0.10.0; `EventEnvelope.Consumed` e `Inbox` de Communication | Consumidores corregidos |
| 7 | DD Cuadro 11 | `technician.registered` sin Payments; sin `ranking.technician-reputation-changed` | Payments consume `technician.registered`; Ranking publica la reputación e Identity la consume | `topics.yaml` v0.10.0; `TechnicianRegisteredConsumer` y `ReputationChangedConsumer` | Fila corregida y fila nueva |
| 8 | DD Cuadro 11 | Matching como consumidor de `catalog.category-changed` | Previsto: `topics.yaml` lo lista, pero el código de Matching no lo consume | Listeners de Matching | Marcado como previsto, igual que en el SDD 8.6 |
| 9 | DD DEP-04 | «Parcial: falta definir cómo Ranking devuelve el promedio a Identity» | Resuelta por ADR-027 | ADR-027 y código de Identity | Estado actualizado |
| 10 | Superproyecto | `apps/api-gateway` apuntaba a v0.21.0 | v0.24.0, la que usan Identity y la web | Etiquetas de `quickpatch-api-gateway` | Puntero subido; `validate-composition.sh` en verde |

## Lo que se verificó y coincide

- **Columnas:** las 28 tablas del diccionario coinciden columna por columna con el código. Las únicas diferencias eran las de las filas 1 y 2.
- **Rutas REST:** todas las rutas del SDD y del DD existen en los contratos. Las que no aparecen en OpenAPI son de tres tipos:
  - prefijos de enrutamiento (`/v1/auth`, `/v1/catalog`, `/v1/platform`);
  - el canal `/v1/realtime`, que está en `asyncapi/realtime.v1.yaml`;
  - nombres anteriores que el DD conserva a propósito en sus tablas de cambios (`/v1/service-categories`, `/v1/matching/{id}/accept`, `/v1/platform/tenants/{id}/activate`). `POST /v1/auth/refresh` figura como pendiente y sin contrato.
- **Nombres de eventos:** todos los del SDD, el DD y el SAD existen en `quickpatch-kafka` v0.10.0. Hay algunas excepciones que no son errores:
  - `chat.message`, `offer.created` y `service-request.counts-changed` son mensajes del canal en tiempo real, no topics.
  - `service-request.evaluated` y `SERVICE_EVALUATED` aparecen solo como historia: lo reemplazó `service-request.rated`.
- **SDD 8.6:** la matriz de productores y consumidores coincide con `topics.yaml` y con el código.
- **Bases del modelo C4:** la descripción de cada `db_*` en `quickpatch.dsl` coincide con las tablas reales.

## Lo que queda abierto

- **Actors:** sigue sin tablas ni código. Es la clasificación que dio SCRUM-696, no una discrepancia.
- **DEP-05, DEP-06 y DEP-07 del DD:** son decisiones de diseño, no diferencias con el código. No se resuelven aquí y quedan para la revisión del equipo.
