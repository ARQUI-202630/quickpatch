# Ventana de mantenimiento en QA: despliegue de service-request 0.12.0 (AC5-E2)

Registro de una ventana real, con inicio, fin, servicios afectados y caída medida. Meta del escenario AC5-E2: downtime planeado menor a 2 horas.

| Dato | Valor |
|---|---|
| Qué se hizo | Despliegue de `service-request` `release/0.12.0` en QA: la calificación viaja en el detalle de la solicitud (SCRUM-639, contrato 1.12.0) |
| Ambiente | QA (VM2, k3s), por el pipeline de `quickpatch-service-request` (run 41947748162, en verde) |
| Inicio | 2026-11-05 01:19:38 UTC (se corta la rama `release/0.12.0` desde `develop`) |
| Fin | 2026-11-05 01:26:51 UTC (el despliegue termina en verde) |
| Duración de la ventana | 7 minutos 13 segundos (meta: menos de 2 horas) |
| Servicios afectados | Solo `service-request`: imagen `t-0206bfb2e2cb`, pod nuevo iniciado a las 01:26:04 UTC; el pod anterior se detuvo hacia las 01:26:36. Los otros 6 servicios no cambiaron |
| Caída medida | 1 segundo: una sola respuesta 502 de `service-request` a las 01:26:36 UTC, cuando se detuvo el pod anterior |
| Reinicios en el pod nuevo | 0 |

## Cómo se midió

Un medidor de disponibilidad (`HTTP` cada segundo, desde un equipo con VPN a la universidad) consultó por el gateway de VM1 dos rutas de QA: `/gateway-salud` y `/api/v1/service-requests/categories`, y anotó la hora (UTC) y el código de cada respuesta. Corrió de 01:19:23 a 01:27:24 UTC. Muestras crudas: `ventana-qa-release-0.12.0-2026-11-05.csv`.

| Ruta | Resultado en 482 muestras |
|---|---|
| `/gateway-salud` | 482 respuestas 200 |
| `/api/v1/service-requests/categories` | 481 respuestas 200 y 1 respuesta 502 (01:26:36 UTC) |

Latencia de `service-request` durante la ventana: mediana 53 ms, p95 73 ms, máximo 1.071 ms.

## Límites de esta medición

- Es un despliegue por actualización gradual (`maxUnavailable: 0`), que no garantiza cero caída: aquí hubo 1 segundo de 502 al relevar el pod.
- La resolución del medidor es de 1 segundo, y mide una ruta pública de `service-request` y el gateway, no todas las operaciones.
- Es QA, no producción. En producción no se ha medido una ventana: los despliegues del 4 de noviembre usaron el mismo mecanismo pero sin medidor.
