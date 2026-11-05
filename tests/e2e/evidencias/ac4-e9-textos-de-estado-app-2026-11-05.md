# AC4-E9: seguimiento del servicio que se explica solo (parte 1, revisión de los textos)

Revisión del 5 de noviembre de 2026 de `lib/features/solicitudes/presentation/estado_vista.dart` en `quickpatch-mobile` (`develop`, versión `release/0.5.5`). Meta del escenario: (1) el 100 % de los estados (mínimo 4, RF-11) muestra un texto que explica **qué ocurre y cuál es el siguiente paso**; (2) al menos 4 de 5 usuarios de prueba describen bien el estado sin ayuda. **Esta revisión cubre solo la parte 1.** La parte 2 es la sesión con 5 personas (UAT).

## Qué dice hoy cada estado

| Estado | Texto que ve el cliente | ¿Qué ocurre? | ¿Dice el siguiente paso? |
|---|---|---|---|
| `buscando_tecnico` | «Estamos buscando un técnico disponible cerca de ti.» | Sí | No |
| `en_espera` | «Por ahora no hay técnicos disponibles; seguimos intentando.» | Sí | Parcial («seguimos intentando») |
| `asignado` | «Un técnico aceptó tu solicitud.» | Sí | No |
| `cotizado` | «El técnico envió una cotización para que la revises.» | Sí | **Sí** (revisarla) |
| `cotizacion_aceptada` | «Aceptaste la cotización.» | Sí | No |
| `en_progreso` | «El técnico está trabajando en tu servicio.» | Sí | No |
| `completado` | «El técnico marcó el servicio como terminado.» | Sí | No |
| `pagado` | «El servicio está pagado.» | Sí | No |
| `cancelado` | «La solicitud se canceló.» | Sí | No aplica |

**Resultado de la parte 1: 9 de 9 estados explican qué ocurre; solo 1 de 9 dice explícitamente el siguiente paso**, y otro lo insinúa. Con la meta literal («qué ocurre y cuál es el siguiente paso»), **no se cumple al 100 %**. Cuenta a favor que otras partes de la pantalla (el botón de pagar en `completado`, el formulario de calificación en `pagado`, el de aceptar la cotización en `cotizado`) sí indican la acción, pero el texto del estado no lo dice.

## Propuesta de textos (no aplicada, para que Miguel y Juan Diego la validen)

| Estado | Texto propuesto |
|---|---|
| `buscando_tecnico` | Estamos buscando un técnico disponible cerca de ti. Te avisamos apenas uno acepte. |
| `en_espera` | Por ahora no hay técnicos disponibles. Seguimos intentando y te avisamos cuando uno acepte. |
| `asignado` | Un técnico aceptó tu solicitud. Te enviará una cotización para que la apruebes. |
| `cotizado` | El técnico envió una cotización. Revísala y acéptala o recházala. |
| `cotizacion_aceptada` | Aceptaste la cotización. El técnico va a iniciar el servicio. |
| `en_progreso` | El técnico está trabajando en tu servicio. Te avisamos cuando termine. |
| `completado` | El técnico terminó el servicio. Paga para cerrarlo. |
| `pagado` | El servicio está pagado. Cuéntanos cómo te fue con una calificación. |
| `cancelado` | La solicitud se canceló. Puedes crear una nueva cuando quieras. |

Cambiar estos textos toca `estado_vista.dart` y las pruebas de widget que los citan.

## Límites

- Se revisó la vista del **cliente**. Las pantallas del técnico («Servicio asignado») tienen sus propios textos, que no se revisaron.
- Es una revisión de texto, no de comprensión: que 4 de 5 personas lo describan bien se mide en la sesión de UAT.
