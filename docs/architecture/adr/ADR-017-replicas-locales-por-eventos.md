# ADR-017 — Réplicas locales de lectura alimentadas por eventos (event-carried state transfer)

- **Estado:** Aceptado
- **Fecha:** 5 de octubre de 2026 (SCRUM-27)
- **Decisión:** Cuando un servicio necesita datos de otro para validar una operación, mantiene una réplica local de solo lectura alimentada por eventos que llevan el estado completo de la entidad, en lugar de consultar al otro servicio por REST
- **Atributos priorizados:** AC5 Reliability (el servicio sigue funcionando aunque el dueño de los datos esté caído) y AC2 Performance Efficiency (la validación es una consulta local)
- **Atributo sacrificado:** consistencia inmediata (la réplica puede ir unos segundos atrás) y AC7 Maintainability (una tabla y un consumidor más por réplica)
- **Implementación:** Catalog (productor) y ServiceRequest (consumidor)

## Contexto

Al crear una solicitud, ServiceRequest debe comprobar que la categoría exista y esté activa en el tenant del cliente (RN-SR10). Las categorías son de Catalog. Consultar a Catalog por REST en cada solicitud acoplaría la disponibilidad de la creación de solicitudes (D1) a la de Catalog, en contra de ADR-003, y sumaría una llamada de red al camino crítico. Leer la base de Catalog está prohibido por ADR-014.

## Decisión

- El dueño de los datos publica un evento con el **estado completo** de la entidad cada vez que la crea o la modifica (no solo el cambio). Para las categorías es `catalog.category-changed` v1, con `categoryId`, `name`, `active` y `updatedAt` (que funciona como versión).
- El consumidor guarda la réplica en una tabla propia (`service_request_categories`) con los campos que necesita y la usa solo para leer.
- El consumidor es idempotente (ADR-007) y además **descarta los cambios con `updatedAt` más antiguo** que el que ya tiene, así que el orden de llegada o un reenvío no deja la réplica atrás.
- La réplica nunca se escribe desde la API del consumidor; solo desde el evento.
- Una categoría desconocida o inactiva se rechaza con `422 categoria-no-disponible`. Si la réplica aún no recibió una categoría recién creada, el cliente puede reintentar segundos después.

## Alternativas descartadas

- **Consulta REST a Catalog en cada solicitud:** dato siempre fresco, pero acopla la disponibilidad de ServiceRequest a la de Catalog y suma latencia (ADR-003).
- **Caché en Redis con la respuesta de Catalog:** reduce las llamadas, pero sigue fallando cuando la caché está vacía y Catalog está caído, y la invalidación queda en manos del consumidor.
- **Eventos con solo el cambio (event notification):** obligarían al consumidor a llamar a Catalog para conocer el estado, con el mismo acoplamiento.
- **No validar la categoría:** permitiría solicitudes con categorías inexistentes, que Matching no podría asignar.

## Consecuencias

### Positivas
- La creación de solicitudes no depende de que Catalog esté arriba.
- La validación es una consulta local indexada.
- Otros consumidores (Matching) pueden mantener su propia réplica del mismo evento sin cambiar a Catalog.

### Costos
- Consistencia eventual: una categoría recién creada o desactivada tarda unos segundos en reflejarse.
- Una tabla, un consumidor y sus pruebas por cada réplica.
- Si se agrega una réplica nueva sobre datos existentes, hay que poblarla inicialmente (republicando el estado actual).

## Evidencia

- Catalog publica `catalog.category-changed` por Outbox al crear y al modificar una categoría (PR #4 de `quickpatch-catalog`).
- ServiceRequest: pruebas unitarias del consumidor (crea la réplica, actualiza con un cambio más reciente, descarta uno atrasado) y una prueba de integración contra Kafka y PostgreSQL reales que aplica una sola vez un evento repetido (PR #4 de `quickpatch-service-request`).

## Trazabilidad

- DD: tabla `service_request_categories` (5.17), RN-SR10, catálogo de eventos.
- Contratos: `events/catalog.category-changed.v1.json`.
- Relacionados: ADR-003, ADR-006, ADR-007, ADR-014.
