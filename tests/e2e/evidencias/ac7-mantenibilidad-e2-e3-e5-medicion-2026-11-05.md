# Mantenibilidad: AC7-E2, AC7-E3 y AC7-E5, medidos sobre el repositorio

Medición del 5 de noviembre de 2026 (UTC) sobre `develop` de los repositorios de servicios de la organización. Es una medición de lectura: ningún resultado se ajustó para que pase. Las decisiones de **qué cuenta como cambio** son de Juan Diego, y aquí se muestran varias definiciones.

## AC7-E2: acoplamiento entre módulos (80 % o más de los cambios afectan un solo servicio)

Fuente: los 191 PR mezclados en `develop` de todos los repositorios desde el 24 de octubre. Un «cambio» es un número de SCRUM; se cuenta en cuántos de los 7 repositorios de servicios (identity, catalog, service-request, matching, payments, communication y ranking) tiene PR mezclados. Se excluyeron las promociones `release/*`, los back-merge y los PR sin número de SCRUM (7).

De 92 cambios con PR, 75 solo tocan app, panel, contratos, documentos o infraestructura. Los **17 que tocan servicios**:

| Definición de «cambio» | Un servicio | Dos | Tres o más |
|---|---|---|---|
| Todos los cambios (17) | 11 (**64,7 %**) | 4 | 2 |
| Sin la subida mecánica de submódulos de contratos, SCRUM-547 (16) | 11 (68,8 %) | 4 | 1 |
| Solo funcionalidades y correcciones, sin `chore` ni `refactor` (14) | 11 (**78,6 %**) | 3 | 0 |

Los cambios que tocan más de un servicio:
- **SCRUM-547** (6 servicios): `chore(contracts)`, subir el puntero del submódulo de contratos a `api-gateway` v0.21.0 y `kafka` v0.10.0. Es mecánico.
- **SCRUM-586/588** (3 servicios: communication, matching y payments): refactor de la convención de paquetes por capa.
- **SCRUM-515** (2): `timeoutSeconds` de las sondas de identity y communication.
- **SCRUM-348** (identity y service-request): `tenant.status-changed` y su réplica.
- **SCRUM-32** (ranking y service-request): calificación y reputación.
- **SCRUM-118** (payments y service-request): la empresa paga la solicitud de su empresa.

**Resultado: no llega al 80 % con ninguna definición** (64,7 % a 78,6 %). Los dos cambios de tres o más servicios son mecánicos o estructurales, no de lógica. Conviene que Juan Diego fije la definición y que Kathe la use; el 78,6 % queda a un cambio del 80 %. Limitación: son 17 cambios, una muestra pequeña, y el número de SCRUM sale del título, la rama o el cuerpo del PR.

## AC7-E3: incorporación de un nuevo microservicio (0 cambios de código en los servicios existentes, fuera de los contratos)

Caso real: Ranking. PR de la organización relacionados con Ranking o su reputación:

| Repositorio | PR | Qué cambió |
|---|---|---|
| ranking | #7, #8 | El servicio nuevo y su manifiesto |
| kafka | #10 | Los topics `service-request.rated` y `ranking.technician-reputation-changed` (contrato) |
| api-gateway | #31 | El endpoint de calificación (contrato) |
| **identity** | #26 | **Código en un servicio existente:** proyecta la reputación del técnico desde Ranking |
| **service-request** | #29 | **Código en un servicio existente:** calificación del servicio pagado y publicación de `service-request.rated` |

**Cambios de código en servicios existentes: 2 (identity y service-request), no 0.** Lo que sí es cierto es que ningún servicio existente tuvo que cambiar para que Ranking arrancara: los dos cambios son funcionalidades de producto nuevas (el evento de calificación y la reputación visible en Identity). Si esos cambios «cuentan como necesarios para incorporar Ranking» es una decisión de Juan Diego; con la métrica literal, **no cumple**.

## AC7-E5: reutilización de la lógica transversal (0 copias entre servicios del mismo stack)

Se compararon los archivos de cada servicio .NET (identity, catalog, service-request, payments, communication y ranking) con `difflib`, después de normalizar los nombres propios de cada servicio.

| Lógica | Servicios con su propia copia | Parecido |
|---|---|---|
| Publicador del Outbox (`OutboxPublisher.cs`) | 4 (catalog, service-request, payments y ranking) | 94 % de promedio; payments y ranking, **100 %** |
| Identificador de correlación (`CorrelationId.cs`) | 5 | **100 %** entre los 5 |
| Contexto de tenant (`set_config` de RLS, dentro de `Repositories.cs` o `ChatStore.cs`) | 6 | 35 % de promedio: es la misma idea integrada en archivos con otro contenido |
| Idempotencia (`processed_events`) | al menos 4 (service-request, payments, communication y ranking) | no se comparó el contenido |

Matching (Java y Spring Boot) es el único del suyo, así que para ese stack hay una sola implementación.

**Resultado: no cumple.** Hay copias de la lógica transversal en el stack .NET, algunas idénticas. Cumplir la meta exige un paquete compartido que consuman los servicios, lo que toca servicios ya promovidos a producción y obliga a repetir regresión y despliegue.

## Límites

- AC7-E2 y AC7-E5 se miden con el código y los PR, no con una revisión de pares.
- No se mide el esfuerzo de arreglarlo, solo el estado actual.
