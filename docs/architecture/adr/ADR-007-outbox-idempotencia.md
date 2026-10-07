# ADR-007 — Transactional Outbox e idempotencia en los consumidores

- **Estado:** Aceptado
- **Fecha:** agosto de 2026 (SAD 1.0)
- **Decisión:** El evento se guarda en `outbox_events` en la misma transacción que el cambio de negocio; un publicador lo envía a Kafka después, y cada consumidor descarta los eventos que ya aplicó
- **Atributo priorizado:** AC5 Reliability
- **Atributo sacrificado:** AC7 Maintainability (más lógica en cada escritura y en cada consumidor)
- **Drivers que la motivan:** D6 (trazabilidad) y D4 (un pago confirmado siempre genera su comprobante)
- **Escenarios que la sustentan:** AC5-E4 (Kafka no disponible), AC5-E5 (evento duplicado por reintento), AC9-E5

## Contexto

Si un servicio guarda un cambio y luego publica el evento en Kafka como dos pasos separados, cualquier falla entre los dos deja el sistema inconsistente: una solicitud creada sin que Matching se entere, o un pago aprobado sin comprobante. Por otro lado, Kafka entrega "al menos una vez": un reintento puede repetir un evento, y un efecto repetido (doble notificación, doble cobro, doble cálculo de reputación) es un error de negocio.

## Decisión

- **Outbox:** el cambio de negocio y la fila de `outbox_events` se escriben en la misma transacción local. El `id` de esa fila es el `eventId` del evento.
- **Publicador:** un proceso en segundo plano de cada servicio lee los eventos pendientes (`FOR UPDATE SKIP LOCKED`), los publica en Kafka y marca `published_at` solo después del ack del broker. Si Kafka falla, suma un intento y reintenta; ningún evento se pierde. Adopta un rol con `BYPASSRLS` para leer los eventos de todos los tenants (ADR-019).
- **Idempotencia:** cada consumidor registra el `eventId` en `processed_events` en la misma transacción en que aplica el efecto; un evento repetido se descarta. Las réplicas además descartan versiones más antiguas que la guardada (ADR-017).
- Se preservan `eventId`, `tenantId` y `correlationId` de punta a punta.

## Alternativas descartadas

- **Publicar en Kafka dentro de la transacción de la base (dos fases):** Kafka no participa en transacciones distribuidas con PostgreSQL de forma práctica, y acopla la escritura a la disponibilidad del broker.
- **Change Data Capture (Debezium):** publica desde el log de la base sin código en el servicio, pero agrega Kafka Connect, más memoria y otro componente que operar (R10, R11).
- **Confiar en la exactitud del broker (exactly-once):** no cubre el efecto en la base del consumidor; la idempotencia sigue siendo necesaria.

## Consecuencias

### Positivas
- Cero eventos perdidos si Kafka cae (AC5-E4) y cero efectos duplicados por reintentos (AC5-E5).
- El historial de `outbox_events` sirve también como evidencia de lo que se publicó (D6).

### Costos
- Cada escritura con evento y cada consumidor llevan lógica adicional.
- Latencia extra entre el cambio y el evento (el intervalo del publicador, 1 segundo por defecto).
- La tabla `outbox_events` crece y necesita una política de limpieza (pendiente).

## Evidencia

- ServiceRequest: la solicitud y su evento se guardan en la misma transacción, y una prueba de integración verifica que el evento llega a Kafka con `eventId` igual al id del Outbox.
- ServiceRequest: el consumidor de `catalog.category-changed` aplica una sola vez un evento repetido (prueba de integración) y descarta un cambio atrasado (prueba unitaria).
- Catalog: el alta y la desactivación publican el estado completo por Outbox.
- POC-BE-001: con Kafka caído la solicitud se creó y su evento llegó a Matching 8 s después de que Kafka volvió, sin pérdidas; un evento repetido se descartó en Matching. Pendiente: caída de más de 5 minutos.

## Trazabilidad

- SAD: escenarios AC5-E4, AC5-E5, AC9-E5; sección 6.
- DD: tablas `outbox_events` y `processed_events`, regla RN-EV1.
- Relacionados: ADR-006, ADR-017, ADR-019.
