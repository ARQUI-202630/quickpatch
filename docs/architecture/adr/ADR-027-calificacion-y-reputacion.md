# ADR-027 — Calificación en ServiceRequest y reputación del técnico en Ranking

- **Estado:** Propuesto el 25 de octubre de 2026 con SCRUM-542 (SAD V5, SCRUM-541) para SCRUM-32. Concreta ADR-003 para el driver D3 y cierra DEP-04 del DD
- **Fecha:** 25 de octubre de 2026
- **Decisión:** la calificación es un hecho de la solicitud y la guarda **ServiceRequest** (`ratings`, DD 5.9), que la recibe por REST (`POST /v1/service-requests/{id}/rating`, DD 8.3.11) y publica `service-request.rated` con Outbox. **Ranking Service** consume ese evento, mantiene la reputación de cada técnico de forma idempotente y publica `ranking.technician-reputation-changed`, del que Identity actualiza la proyección `technician_profiles.average_rating` y la marca de reputación baja (AC9-E2). Ningún servicio llama a otro de forma síncrona por la calificación
- **Atributos priorizados:** AC5 Reliability (si Ranking falla, la calificación igual queda guardada y la reputación se pone al día al volver) y AC1 Functional Suitability (una sola calificación por solicitud pagada y un promedio correcto)
- **Atributos sacrificados:** AC7 Maintainability (Ranking pasa de esqueleto a servicio con base propia y un evento más) y la consistencia inmediata: la reputación va unos segundos detrás de la calificación
- **Restricciones:** ADR-003 (microservicios + EDA), ADR-005 (RLS), ADR-006 (Kafka), ADR-007 (Outbox e idempotencia), ADR-017 (réplicas por eventos), ADR-025 (REST solo hacia Identity, ServiceRequest y Payments) y R3 (alcance del MVP)

## Contexto

RF-12 pide que el cliente califique el servicio (1 a 5 y comentario opcional) una sola vez, cuando la solicitud está `pagado` (RN-R1 a RN-R3, DEP-11 resuelta en el SRS V4). Es el último paso del flujo crítico que falta (SCRUM-32).

El driver D3 ya fijó que la reputación no debe acoplarse al flujo del servicio: «Ranking Service separado que consume los eventos de evaluación» (ADR-003). Quedaban tres preguntas abiertas:

1. qué servicio guarda la calificación;
2. cómo se calcula la reputación y qué pasa si Ranking no está;
3. cómo vuelve el promedio a quien lo muestra (DEP-04 del DD: «Falta definir cómo Ranking devuelve el promedio a Identity»).

Hay además una diferencia de nombres: el SAD (4.2) llama al evento `SERVICE_EVALUATED`, las subtareas de Jira `service-request.evaluated` y el DD (8.4) `service-request.rated`. El contrato es el del DD.

## Decisión

1. **La calificación vive en ServiceRequest.** Es un dato de la solicitud, con la misma vida y los mismos permisos, y ServiceRequest ya conoce su estado, su dueño y su técnico.
   - `POST /v1/service-requests/{id}/rating` con `{ score, comment? }`, como dice el DD (8.3.11). ServiceRequest ya es uno de los tres servicios con REST desde el gateway (ADR-025), así que no hace falta una excepción.
   - Califica solo el **dueño** de la solicitud, tomado del JWT (para una empresa, el usuario que la creó, igual que las demás acciones sobre la solicitud), y solo si está en `pagado`. Si no está en `pagado`, la respuesta es `409 INVALID_STATE_TRANSITION`; si ya tiene calificación, `409 ALREADY_RATED` (`UNIQUE (service_request_id)`); si es de otro usuario del mismo tenant, `403`, y si es de otro tenant, `404` porque RLS no la deja ver (ADR-005); igual que la consulta de la solicitud.
   - `score` entre 1 y 5 (RN-R1, `CHECK`). El comentario es opcional y su longitud máxima la fija el contrato (SCRUM-497); este ADR propone **500 caracteres**. El comentario no va en los logs.
   - Calificar **no cambia el estado** de la solicitud (DD 7.4, `EVALUATED`). El detalle de la solicitud y el historial del técnico (SCRUM-37) leen la calificación de la propia tabla `ratings`, sin consultar a Ranking.
2. **Evento `service-request.rated` por Outbox.** La fila de `ratings` y el evento se guardan en la misma transacción (ADR-007). Campos del DD (8.4): `serviceRequestId`, `technicianId`, `score`, `ratedAt`, en el sobre común con `eventId`, `tenantId` y `correlationId`. El comentario no viaja: Ranking no lo necesita y así no sale de ServiceRequest. Los nombres `SERVICE_EVALUATED` y `service-request.evaluated` se reemplazan por `service-request.rated` en el SAD y en Jira.
3. **Ranking calcula la reputación, de forma idempotente.** Ranking consume `service-request.rated` y guarda por técnico y tenant la cantidad de calificaciones, la suma y el promedio, con RLS. Registra el `eventId` y el `serviceRequestId` de cada calificación aplicada:
   - un evento repetido (la entrega de Kafka es al menos una vez) no vuelve a sumar;
   - el promedio es `suma / cantidad`, redondeado a un decimal (`NUMERIC(2,1)`, como `average_rating`). No depende del orden de llegada, porque cada solicitud aporta una sola calificación que no se edita.
   - Si el técnico tiene **5 o más calificaciones y un promedio menor a 3.0**, queda marcado como reputación baja (AC9-E2). La marca no suspende al técnico: el Admin decide (RF-20).
4. **El promedio vuelve por evento, no por consulta.** Ranking publica `ranking.technician-reputation-changed` (`technicianId`, `averageRating`, `ratingCount`, `lowReputation`, `changedAt`) con Outbox cada vez que cambia la reputación. Identity lo consume y actualiza `technician_profiles.average_rating` y la marca. Descarta eventos más viejos que el último aplicado, por `changedAt` (ADR-017). Así el panel del Admin y el perfil del técnico muestran la reputación desde Identity, que es quien ya los sirve, sin una ruta REST nueva hacia Ranking (ADR-025). Este evento es nuevo: su contrato lo publica SCRUM-497 en `quickpatch-kafka`.
5. **Si Ranking está caído.** La calificación se acepta igual (`201`), porque solo depende de ServiceRequest. El evento queda en el Outbox o en Kafka, y Ranking procesa el atraso al volver (AC5-E3). Mientras tanto, el panel muestra la última reputación conocida. Es consistencia eventual, aceptada a cambio de que una falla de Ranking no bloquee el cierre del servicio, que es justamente el riesgo que nombra D3.

## Alternativas descartadas

- **Guardar la calificación en Ranking por REST:** tendría que ser una excepción de ADR-025, y Ranking necesitaría una réplica del estado, el dueño y el técnico de cada solicitud solo para validar quién puede calificar. Además, el detalle y el historial de la solicitud tendrían que consultarle a Ranking.
- **Calcular el promedio en ServiceRequest:** evita un servicio, pero mezcla la reputación con la máquina de estados de la solicitud, contra lo que fija D3, y deja a ServiceRequest como fuente de un dato que es del técnico.
- **Que Identity o el panel consulten el promedio a Ranking en línea:** es una llamada síncrona entre servicios (ADR-003). Si Ranking falla, se cae la pantalla del Admin.
- **Recalcular la reputación de forma periódica sobre todas las calificaciones:** obliga a Ranking a leer la base de ServiceRequest o a pedir un volcado, y la marca de AC9-E2 llegaría con el retraso del periodo.

## Consecuencias

### Positivas

- La calificación se guarda y se responde aunque Ranking no esté; la reputación se pone al día sola.
- Una entrega repetida del evento no infla el promedio.
- El historial del técnico (SCRUM-37) muestra la calificación de cada servicio sin depender de otro servicio.
- DEP-04 queda resuelta: el promedio llega a `technician_profiles` por un evento con dueño claro.

### Negativas

- Ranking deja de ser un esqueleto: base `db_ranking`, roles (ADR-019), consumidor, Outbox y despliegue en QA y producción (SCRUM-512, SCRUM-518).
- Hay un evento más (`ranking.technician-reputation-changed`) y una réplica más en Identity.
- El panel puede mostrar durante unos segundos un promedio anterior a la última calificación.

## Verificación

- ServiceRequest: pruebas de integración de RN-R1 a RN-R3, de dueño (403), de tenant (404) y de estado o repetición (409), y de que la fila y el evento se guardan juntos.
- Ranking: el mismo `service-request.rated` entregado dos veces suma una sola vez; el promedio de un conjunto conocido de puntajes coincide; la marca aparece con 5 calificaciones y promedio menor a 3.0, y no antes.
- QA: colección `scrum-32-calificacion` contra QA con la evidencia en `tests/e2e/evidencias/`.

## Trazabilidad

RF-12, RF-20; RN-R1 a RN-R3; D3; AC1, AC5-E3, AC9-E2; DD 5.3 (`technician_profiles.average_rating`), 5.9 (`ratings`), 8.3.11, 8.4 y DEP-04; SCRUM-32 (85, 86, 87, 497, 498), SCRUM-37, SCRUM-541 (542).
