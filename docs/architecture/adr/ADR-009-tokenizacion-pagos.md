# ADR-009 — Tokenización de pagos en la pasarela

- **Estado:** Aceptado
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

Pendiente: integración con la pasarela en modo de pruebas (HU de pagos) y prueba automática de ausencia de PAN/CVV en logs.

## Trazabilidad

- SAD: killer K2, driver D4, escenario AC6-E1, sección 6.
- DD: tabla `payments` (solo token y datos permitidos).
- Relacionados: ADR-007 (el comprobante se emite por evento).
