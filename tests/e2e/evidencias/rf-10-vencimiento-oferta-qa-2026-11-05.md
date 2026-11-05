# RF-10: una oferta sin responder vence a los 3 minutos y pasa al siguiente técnico

Prueba contra QA el 4 de noviembre de 2026 a las 22:03 hora de Colombia, que es el 5 de noviembre a las 03:03 UTC. Las horas de abajo están en UTC. Registro crudo en `rf-10-vencimiento-oferta-qa-2026-11-05.txt`.

## Cómo se hizo

Con peticiones HTTP a la API de QA, sin tocar la base: 1) una categoría propia; 2) dos técnicos (A y B) con esa especialidad, aprobados por el administrador, con cobertura de toda Bogotá y disponibles; 3) un cliente que crea una solicitud; 4) el técnico que recibe la oferta **no la responde**; 5) se consulta cada 5 segundos `GET /api/v1/matching/offers?status=pendiente` de los dos técnicos; 6) el técnico que dejó vencer la oferta intenta aceptarla; 7) los técnicos se suspenden y la categoría se desactiva.

El tiempo de la oferta es `MATCHING_OFFER_TTL: 3m` y el barrido de vencimiento corre cada 15 s (`MATCHING_EXPIRY_INTERVAL: PT15S`), según `deploy/k8s/matching.yaml` de `quickpatch-matching` (RN-M8).

## Resultado

| Hora (UTC) | Hecho |
|---|---|
| 03:03:02 | El cliente crea la solicitud (estado `buscando_tecnico`) |
| 03:03:05 | El técnico A recibe la oferta (a los 3 s). La oferta vence a las 03:06:02 (`expiresAt`) |
| 03:06:04 | La oferta de A deja de estar pendiente: **179 s después de recibirla** (esperado: unos 180) |
| 03:06:09 | **El técnico B recibe la oferta** de la misma solicitud, 184 s después de que la recibió A |
| 03:06:14 | A intenta aceptar la oferta vencida: **409 `oferta-no-disponible`** |
| 03:06:14 | Ofertas pendientes de A para esa solicitud: 0 |

**CUMPLE.** La oferta venció a los 179 s, pasó al siguiente técnico 5 s después (el barrido de 15 s) y la vencida ya no se puede aceptar.

## Límites y un primer intento descartado

- El primer intento de las 02:56 UTC **no vale**: el script leyó mal los campos de la oferta (el identificador es `attemptId` y el filtro de estado es el parámetro `status=pendiente`) y marcó la oferta como no pendiente a los 0 s. Se corrigió el script y se repitió completo; la evidencia es la de la segunda corrida.
- Se probó con dos técnicos que cubren toda Bogotá; no se probó el caso de que no quede ningún técnico, que cubre `matching.no-technician-available`.
- La solicitud de la prueba queda en QA sin cerrar. Los usuarios `@quickpatch.test` y la solicitud los borra `limpiar-qa-uat.yml`.
