# RF-28: alerta de caída y logs centralizados con identificador de correlación

Prueba contra QA el 4 de noviembre de 2026 a las 21:55 hora de Colombia, que es el 5 de noviembre a las 02:55 UTC. Las horas de abajo están en UTC. RF-28: logs centralizados y estructurados de errores, con un identificador de correlación entre servicios, y alertas básicas de caída de servicio.

## Parte 1. Alerta `qp-vm-caida` («VM sin métricas»)

La regla (`infrastructure/ansible/files/grafana/alerting/rules.yml`) se dispara si Prometheus no puede leer `node_exporter` de una VM durante 2 minutos (`up{job="node"}`; sin datos cuenta como alerta). Se apagó solo el contenedor `agentes-node-exporter-1` de **VM7** (QA, Kafka y Garage); Kafka y Garage siguieron arriba.

| Hora (UTC) | Hecho | Fuente |
|---|---|---|
| 02:55:17 | Se apaga el `node_exporter` de VM7 | registro de Ansible |
| **02:58:20** | **La alerta pasa a «Firing»** («vm7 no responde», severidad crítica) | correo de Grafana: «Observed 37s before this notification was delivered, at 02:58:20 UTC» |
| **02:58:57** | **Llega el correo «[FIRING:1] VM sin métricas (posible caída) vm7»** | fecha del mensaje |
| 03:00:32 | Se enciende de nuevo el `node_exporter` | registro de Ansible |
| 03:01:20 | La alerta se resuelve | correo de Grafana |
| 03:03:57 | Llega el correo «[RESOLVED] VM sin métricas (posible caída) vm7» | fecha del mensaje |

| Medida | Valor |
|---|---|
| De apagar el exportador a la alerta en «Firing» | 3 min 03 s (regla: 2 min + 1 min de evaluación) |
| De apagar el exportador al correo | 3 min 40 s |

Es la VM de QA, no una de producción, y la regla es la misma para todas (`vm` es una etiqueta).

## Parte 2. Un error en QA, hallado en Loki por su `correlationId`

Se envió cada petición con una cabecera `X-Correlation-Id` propia; el servicio la devuelve igual en el cuerpo del error (`correlationId`) y en la cabecera de la respuesta. Se buscó en Loki con LogQL: `{entorno="qa",namespace="quickpatch"} |= "<correlationId>"`.

| Error provocado | HTTP | ¿Aparece en Loki por su `correlationId`? |
|---|---|---|
| Crear una solicitud con una categoría que no es un UUID | 400 | **No** (0 líneas) |
| Pedir una solicitud que no existe | 404 | **No** (0 líneas) |
| Un cliente pide `GET /api/v1/payments/received` (solo de técnicos) | 403 | **Sí**: 1 línea a las 03:08:22 UTC, servicio `payments`, nivel `Warning`, `ForbiddenAuditHandler`: «Acceso denegado (403): GET /v1/payments/received por el usuario … con rol cliente.» |

## Lo que se aprendió (importa para AC7-E4, diagnóstico de un fallo)

- Los servicios .NET escriben el `correlationId` dentro del bloque `Scopes` de las líneas que emiten **mientras atienden una petición**. Un 400 o un 404 normales no emiten ninguna línea, así que no se pueden hallar por su identificador. Los accesos denegados (403) y los fallos de login sí dejan una línea `Warning` con el identificador. Servicios con líneas que lo traen en las últimas 4 horas de QA: `service-request` (361), `matching` (630, en formato ECS) y `payments` (9).
- Los errores de tareas de fondo no traen identificador de correlación porque no son una petición (por ejemplo el `Error` de `QuoteExpirer`: «Falló la vuelta del vencimiento de cotizaciones»).
- En producción, en las últimas 4 horas, solo hay 3 líneas `Error` con identificador (2 de `payments` y 1 de `service-request`). De las que se revisó el detalle, son del chequeo de salud (`Microsoft.Extensions.Diagnostics.HealthChecks`), que coincide con los despliegues de ese día; no se leyó la tercera.
- Loki (`:3100` de VM1) no es alcanzable desde la VPN, solo desde VM1: la consulta del equipo se hace en Grafana, en Explore, con la fuente Loki.

## Límites

- La alerta se probó en VM7 de QA. No se probó en producción.
- Para RF-28 se probó un error de acceso denegado, que es un error real de la aplicación con identificador, pero no una excepción no controlada (5xx). Esos no se provocaron en QA.
