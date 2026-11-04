# ADR-009 — Tokenización de pagos en la pasarela

- **Estado:** Aceptado; modificado el 20 de octubre de 2026 (SAD 2.32, SCRUM-42): en el MVP la pasarela es simulada
- **Fecha:** agosto de 2026 (SAD 1.0)
- **Decisión:** Los datos de la tarjeta se capturan directamente en la pasarela de pagos certificada; QUICKPATCH solo recibe y guarda un token
- **Atributo priorizado:** AC6 Security
- **Atributo sacrificado:** AC7 Maintainability (dependencia de la pasarela externa y menor control del flujo de pago)
- **Killer que la motiva:** K2 (PCI-DSS)
- **Escenario que la sustenta:** AC6-E1 (cero números de tarjeta o CVV en bases de datos o logs)

## Contexto

QUICKPATCH cobra los servicios como merchant of record (D4). La norma PCI-DSS prohíbe guardar el código de seguridad (CVV) después de la autorización, y cualquier sistema que reciba, procese o guarde el número de tarjeta (PAN) queda dentro del alcance de la certificación, con controles que un proyecto académico no puede cumplir (K2, RNF-01, RIE-01).

## Decisión

- La app captura los datos de la tarjeta con el componente o SDK de la **pasarela certificada**, que devuelve un **token**. El PAN y el CVV nunca pasan por el backend de QUICKPATCH.
- Payments Service guarda solo el token y los datos que la norma permite (por ejemplo, últimos 4 dígitos y marca) y registra el resultado de cada intento.
- Ningún log, evento ni base de datos contiene PAN o CVV; las pruebas de seguridad buscan esos patrones en los logs de Loki (TD).
- El estado del pago se confirma por webhook de la pasarela o, si la red privada lo impide (R9), por consulta periódica.
- Payments Service habla con la pasarela a través de un puerto (`IPaymentProvider`: cobrar con un token y consultar el estado de un cobro). Cambiar de pasarela es cambiar el adaptador y el tokenizador de la app, sin tocar los contratos REST ni los eventos.

## Modificación del 20 de octubre de 2026: pasarela simulada en el MVP

**Contexto.** El SAD no había fijado el proveedor de la pasarela (sección 4.1). Integrar una real exige una cuenta del comercio, manejar sus llaves y salida a Internet desde las VMs, que R9 no garantiza. El equipo decidió que eso complica de más el MVP.

**Decisión.** En el MVP, la pasarela es una **pasarela simulada** que imita las dos piezas de una pasarela real y respeta todas las reglas de arriba:

1. **Tokenizador en la app**, que hace las veces del widget de la pasarela. Valida la tarjeta en el dispositivo y la cambia por un token. Solo acepta las tarjetas de prueba de la tabla; cualquier otra se rechaza en el dispositivo. El número, la fecha y el CVV nunca salen del dispositivo: al backend solo llega el token (RN-P1).
2. **Adaptador `PasarelaSimulada` de Payments Service**, que implementa `IPaymentProvider`. Decide el resultado según el token y devuelve una referencia de cobro (`provider_token_ref`), como haría la API de cobro de una pasarela. Corre dentro de Payments, sin red: no agrega una dependencia externa (R5) ni necesita salir de la red del laboratorio (R9).

|Tarjeta de prueba|Token|Resultado en Payments|
|---|---|---|
|4242 4242 4242 4242|`tok_sim_aprobada_…`|`aprobado`: `payment.approved` y comprobante|
|4000 0000 0000 0002|`tok_sim_rechazada_…`|`rechazado` con `reasonCode` `fondos_insuficientes`: `payment.rejected` y se puede reintentar (RN-SR5)|
|4000 0000 0000 0119|`tok_sim_error_…`|La pasarela «no responde»: `502 PAYMENT_PROVIDER_ERROR` y el pago queda `procesando`; la conciliación periódica lo cierra como `rechazado` con `reasonCode` `pasarela_sin_respuesta` (AC9-E5)|

**No es una pasarela propia** (alternativa descartada abajo): no recibe, procesa ni guarda tarjetas reales, y el backend sigue sin ver nunca el PAN ni el CVV. Es un sustituto de pruebas detrás del mismo puerto. Para producción con dinero real se reemplaza por el adaptador y el tokenizador de una pasarela certificada, y esta modificación se revisa.

**Consecuencias.** No hay cobros reales en el MVP. La interoperabilidad con una pasarela real (AC3-E1, RIE-01) queda sin evidencia; lo que se demuestra es la separación del puerto, la idempotencia (RN-P5) y la conciliación de pagos sin respuesta (AC9-E5). Las pruebas de ausencia de PAN y CVV en logs siguen aplicando.

## Alternativas descartadas

- **Recibir los datos de tarjeta en el backend y enviarlos a la pasarela:** todo el backend entraría al alcance de PCI-DSS.
- **Guardar el PAN cifrado para pagos recurrentes:** el modelo de negocio no necesita pagos recurrentes y el riesgo no se justifica.
- **Pasarela propia:** fuera del alcance y prohibido por K2.

## Consecuencias

### Positivas
- El alcance de PCI-DSS se reduce a la integración con la pasarela (AC6-E1).
- Un incidente en QUICKPATCH no expone datos de tarjetas.

### Costos
- Dependencia de la disponibilidad y del contrato de la pasarela (AC9-E5 cubre su caída).
- Los webhooks de la pasarela necesitan llegar a la red privada del laboratorio (R9, decisión pendiente del equipo).
- La pasarela es la única dependencia externa de producción permitida por R5.

## Evidencia

Pago con la pasarela simulada (SCRUM-42): pruebas de Payments Service con las tres tarjetas de prueba y colección Newman contra QA. Pendiente: prueba automática de ausencia de PAN/CVV en logs.

## Trazabilidad

- SAD: killer K2, driver D4, escenario AC6-E1, sección 6.
- DD: tabla `payments` (solo token y datos permitidos).
- Relacionados: ADR-007 (el comprobante se emite por evento).
