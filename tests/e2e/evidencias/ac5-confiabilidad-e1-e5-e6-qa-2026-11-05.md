# Confiabilidad en QA: AC5-E1, AC5-E5 y AC5-E6

Pruebas del 4 de noviembre de 2026 por la noche en Colombia, que es el 5 de noviembre en UTC. Las horas están en UTC.

## AC5-E1: caída de un componente no crítico (recuperación manual en 12 a 24 h)

Se usó la prueba de RF-28 (`rf-28-alerta-de-caida-y-logs-qa-2026-11-05.md`). El componente no crítico es el `node_exporter` de VM7 (QA): si cae, se pierden las métricas de esa VM, pero Kafka y Garage siguen sirviendo.

| Hora (UTC) | Hecho |
|---|---|
| 02:55:17 | Se detiene el componente (`docker stop agentes-node-exporter-1`) |
| 02:58:20 | Grafana detecta la caída y dispara la alerta |
| 03:00:32 | Recuperación manual (`docker start`) |
| 03:01:20 | Grafana confirma la recuperación |

Recuperación manual: **5 min 15 s** desde que se detuvo y 2 min 12 s desde la alerta. La meta es de 12 a 24 h; se cumple con mucho margen.

Límite: lo recuperó un ingeniero que estaba presente. El escenario ya acepta tiempos de horas porque no hay operación 24/7 (R7); esta medición no prueba la recuperación de madrugada.

## AC5-E5: evento duplicado, 0 efectos duplicados

Se publicó en el Kafka de QA (VM7) el mismo `eventId` de `catalog.category-changed`, con una categoría nueva **inactiva** (para no aparecer en ninguna lista), y se miró `processed_events` y la réplica `service_request_categories` de `db_service_request`.

| Hora (UTC) | Publicación | Resultado |
|---|---|---|
| 03:20:45 | Evento E1 («AC5-E5 version A») | Se procesa |
| 03:20:49 | **El mismo E1** otra vez | Sin efecto nuevo |
| 03:20:57 | Evento E2, más nuevo («AC5-E5 version B») | Se procesa |
| 03:21:05 | **El mismo E1** una tercera vez, ya con E2 aplicado | Sin efecto: no revierte la versión B |

Verificación en la base:
- `processed_events`: **1 fila** para E1, publicado 3 veces, y 1 fila para E2.
- `service_request_categories`: **1 fila** para la categoría, con nombre «AC5-E5 version B» y `active = false`.

Se borraron después la categoría y los dos eventos de la prueba (1 y 2 filas). Resultado: **0 efectos duplicados** con 3 publicaciones del mismo `eventId`.

Límite: se probó un solo consumidor (ServiceRequest, categorías). Las pruebas de integración de Communication, Payments y Ranking cubren los demás.

## AC5-E6: operación sin fallos del flujo crítico

**Menos del 1 % de 5xx, medido con los logs del gateway en Loki.** Se contaron las respuestas del Nginx de VM1 (`{job="docker",vm="vm1"}`, formato estándar con el código de estado), que recibe todo el tráfico de QA y de producción:

| Periodo | Peticiones | 5xx | % |
|---|---|---|---|
| 30 oct a 5 nov (8 días) | 55.296 | 27 | **0,049 %** |
| Sin el día de la k6 (5 nov) | 10.955 | 25 | 0,228 % |

De los 27 5xx, los 23 que salen en los 12 grupos de ruta más frecuentes son: 12 en `/api/v1/service-requests/categories` (11 `503` y un `502`, por las pruebas de Beta antes de que llegara la réplica de la categoría y por el relevo de un pod); 8 `502` en rutas de pago (la pasarela simulada responde 502 a propósito en las pruebas de «pasarela sin respuesta»); y `502` aislados en calificación y en el detalle de una solicitud (3), cuyo origen no se revisó y pueden ser relevos de pod durante los despliegues. Los otros 4 no están en esas 12 rutas y no se detallaron. Los días 29 de octubre y 1 y 3 de noviembre salen con 0 peticiones: no se distingue entre «sin tráfico» y «sin logs».

**0 fallos en las ejecuciones de `pruebas-sistema.yml`:** las 9 corridas del 30 de octubre al 5 de noviembre (humo del flujo crítico, ZAP y PCI-DSS, E2E y, en la última, k6) terminaron en verde.

Lo que falta: **no existe una corrida programada** (el escenario habla de «ejecuciones programadas»). `pruebas-sistema.yml` solo corre con `push` a `release/**` o a mano. Programarla de noche dejaría datos de prueba en QA cada día; hay que decidir si se acepta y con qué limpieza.
