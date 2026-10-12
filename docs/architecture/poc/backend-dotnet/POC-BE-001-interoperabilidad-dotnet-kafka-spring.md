# POC-BE-001 — Interoperabilidad ASP.NET Core → Kafka → Spring Boot

- **Rol:** Backend Developer / Arquitectura
- **Estado:** Ejecutada el 6 de octubre de 2026; hipótesis confirmada, con un hallazgo corregido
- **Respalda:** ADR-006, ADR-007 y ADR-012 (también ADR-005, ADR-017)
- **Repositorios:** `quickpatch-service-request` (develop + PR #6), `quickpatch-matching` (PR #4), `quickpatch-contracts`

## Pregunta

¿Puede ServiceRequest en ASP.NET Core producir un evento versionado que Matching en Spring Boot consuma sin compartir clases internas, preservando `eventId`, `tenantId` y `correlationId`, y manteniendo Outbox e idempotencia?

## Hipótesis

1. El único acoplamiento entre los dos runtimes es el contrato `events/service-request.created.v1.json`: ninguno importa código del otro.
2. El `eventId` que llega a Matching es el id de la fila de `outbox_events` de ServiceRequest, y el `tenantId` y el `correlationId` son los del token y el encabezado de la petición original.
3. Un evento repetido no produce un segundo efecto en Matching.
4. Un mensaje que no cumple el contrato no bloquea al consumidor.
5. Si Kafka está caído, la solicitud se crea igual y el evento llega a Matching cuando Kafka vuelve, sin pérdidas.

## Corte funcional

```text
cliente (JWT RS256, X-Correlation-Id)
  -> ServiceRequest (.NET 10): POST /v1/service-requests
       service_requests + outbox_events en la misma transacción (RLS por tenant)
  -> publicador del Outbox -> Kafka: service-request.created (clave: serviceRequestId)
  -> Matching (Java 25 / Spring Boot 4.1.1): ServiceRequestCreatedListener
       processed_events + inicio del matching en la misma transacción (RLS por tenant)
```

## Procedimiento

Ambiente local, mismas versiones que el CI:

- Una instancia `postgis/postgis:16-3.5` con dos bases, `db_service_request` y `db_matching` (ADR-014). Las migraciones corren como administrador y los roles salen de `db/roles.sql` de cada servicio. Cada servicio se conecta con su rol `_app`, sin `BYPASSRLS`.
- `confluentinc/cp-kafka:7.7.1` en modo KRaft, sin topics creados de antemano.
- ServiceRequest con `dotnet run` y Matching con `java -jar`. El token RS256 se firma con un par de llaves generado solo para la prueba.
- La categoría se crea publicando `catalog.category-changed`, como lo haría Catalog (ADR-017).

El script reproducible está en `evidencias/POC-BE-001/poc.sh` y la salida en `evidencias/POC-BE-001/resultado.txt`.

## Resultados

|Caso|Qué se hizo|Resultado|
|---|---|---|
|C1 Interoperabilidad|`POST /v1/service-requests` con token y `X-Correlation-Id`|201. Matching registró el evento con `eventId` igual al id de `outbox_events`; 723 ms desde el POST hasta el registro en Matching|
|C2 Tenant y correlación|Comparar `tenantId` y `correlationId` de punta a punta|El `tenant_id` de `processed_events` en Matching es el del token; el `correlationId` del encabezado aparece en el `payload` del Outbox y en los logs JSON de Matching|
|C3 Duplicado|Republicar el mismo mensaje del Outbox en Kafka|Matching registró `DUPLICATE`; sigue habiendo una sola fila en `processed_events`|
|C4 Kafka caído|Detener Kafka y crear una solicitud|201: la solicitud y su evento quedan en la base con `published_at` nulo|
|C5 Recuperación|Arrancar Kafka de nuevo|El evento se publicó y Matching lo aplicó 8 s después de que Kafka volvió; 0 eventos pendientes en el Outbox|
|C6 Contrato inválido|Publicar un texto que no es JSON y un evento sin campos obligatorios|Los dos se registraron como descartados y el consumidor siguió procesando los eventos válidos|
|C7 Independencia de runtimes|Revisar dependencias|Ningún repositorio importa código del otro; solo comparten el submódulo `contracts/`|

Las 5 hipótesis se confirman.

## Hallazgos

1. **Defecto corregido: el consumidor de ServiceRequest detenía el servicio si el topic no existía.** Al arrancar ServiceRequest antes de que Catalog publicara su primer evento, `catalog.category-changed` todavía no existía. El consumidor lanzaba `ConsumeException` (*Unknown topic or partition*) y, con `BackgroundServiceExceptionBehavior=StopHost`, se caía todo el servicio, incluida la API REST.
   - Las pruebas de integración no lo detectaban porque crean los topics antes de arrancar.
   - Corrección en `quickpatch-service-request` PR #6: un error de lectura no fatal se reintenta cada 5 s. Incluye una prueba con un Kafka sin topics que falla sin la corrección.
   - Matching (Spring Kafka) no tiene el problema: el contenedor del listener sigue reintentando.
2. **Con Kafka caído, el Outbox no aumentó `attempts`.** El productor de Confluent guarda el mensaje en su búfer interno y lo reintenta mientras no venza `message.timeout.ms` (5 minutos por defecto); por eso el publicador no registró un fallo. Si la caída supera ese tiempo, la entrega falla, el publicador suma un intento y el evento vuelve a quedar pendiente en la base, de modo que tampoco se pierde.
   - **No se probó** una caída de más de 5 minutos; queda como caso pendiente (AC5-E4).
   - Mientras espera la entrega, el publicador mantiene abierta su transacción con las filas bloqueadas (`FOR UPDATE SKIP LOCKED`) y ocupa una conexión del pool hasta 5 minutos.
   - **Recomendación:** fijar `MessageTimeoutMs` del productor (por ejemplo, 30 segundos) para que el fallo se registre pronto y la transacción se libere.
   - La misma revisión aplica a Catalog, que usa el mismo publicador.
3. **Infraestructura:** los topics deben crearse explícitamente en VM6 (Ansible) en lugar de depender de la creación automática, y con los mismos nombres que `eventType`.

## Pendientes

- C4 con una caída de Kafka de más de 5 minutos.
- Repetir la PoC en el ambiente de QA (VM2) cuando estén desplegados los dos servicios (ADR-015).
- Medir la latencia bajo carga con k6 para AC2-E3 (menos de 7 s hasta la notificación); la medida de 723 ms es de una sola solicitud.
