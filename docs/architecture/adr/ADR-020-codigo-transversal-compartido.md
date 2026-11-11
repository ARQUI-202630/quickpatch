# ADR-020 — Código transversal compartido entre servicios .NET

- **Estado:** Aceptado (11 de noviembre de 2026, SCRUM-657). Propuesto el 6 de octubre de 2026.
- **Fecha:** 6 de octubre de 2026; aceptado y modificado el 11 de noviembre de 2026
- **Decisión:** La lógica transversal sin dominio de los servicios .NET vive en un repositorio propio, `quickpatch-shared-dotnet`, con un proyecto por mecanismo. Cada servicio lo consume como submódulo en `shared/dotnet`, fijado a una etiqueta `vX.Y.Z`, con `ProjectReference`. No se publica en GitHub Packages.
- **Atributo priorizado:** AC7 Maintainability (Modifiability, Reusability)
- **Atributo sacrificado:** independencia total entre servicios (ADR-013: ningún servicio importa código de otro). Se acepta para código sin dominio.
- **Escenario relacionado:** AC7-E5

## Contexto

Los servicios .NET copiaban el mismo código transversal. La medición del 5 de noviembre (`tests/e2e/evidencias/ac7-mantenibilidad-e2-e3-e5-medicion-2026-11-05.md`) encontró el publicador del Outbox en 4 servicios, `CorrelationId` en 5 (idénticos al 100 %), el contexto de tenant en 6 e idempotencia en al menos 4. AC7-E5 quedó en No cumple.

Las copias ya divergían: ServiceRequest había corregido el apagado de su publicador del Outbox (un tiempo de espera con forma de cancelación ya no apaga el host) y Catalog, Ranking y Payments seguían con la versión anterior. Es exactamente el costo que este ADR anticipaba.

ADR-013 prohíbe que un servicio importe código de **otro servicio**, pero no se pronuncia sobre una librería transversal sin dominio.

## Opciones

1. **Mantener copias** (situación anterior): sin dependencias, pero cada corrección se repite y las copias divergen.
2. **Paquetes NuGet internos** en `quickpatch-shared-dotnet`, publicados en GitHub Packages con versión semántica.
3. **Repositorio propio consumido como submódulo** fijado a una etiqueta, con `ProjectReference`: el mismo mecanismo con el que los servicios ya consumen los contratos (`contracts/api-gateway` y `contracts/kafka`, ADR-021).
4. **Plantilla de servicio** (`dotnet new`) con el código transversal: arranque homogéneo, pero las correcciones posteriores siguen siendo manuales.

## Decisión

Opción 3. Frente a la 2, GitHub Packages exige un token con permiso de lectura en cada `dotnet restore`, también dentro del `docker build` de la imagen, y un pipeline de publicación; con una sola persona en infraestructura (R11) y sin presupuesto (R5), el submódulo da lo mismo (versión fijada por el servicio, actualización con un PR propio) sin credenciales nuevas ni cambios en el CI: el `checkout` ya trae los submódulos y el `Dockerfile` solo suma `COPY shared/ shared/`.

Reglas:

- **Sin dominio.** No hay entidades, eventos, contratos ni reglas de negocio. Cada servicio conserva su tabla `outbox_events`, la clase que la mapea, su DbContext, sus migraciones y sus contratos de `quickpatch-kafka`.
- **Un proyecto por mecanismo, pequeño.** `QuickPatch.Transversal.Http` (correlación), `QuickPatch.Transversal.Persistence` (rol de sesión) y `QuickPatch.Transversal.Messaging` (publicador del Outbox). Nada de una librería «común» que crezca sin límite; lo que usa un solo servicio se queda en ese servicio.
- **Versión fijada.** Cada servicio fija una etiqueta; actualizar es un PR propio del servicio, con su CI y su despliegue en QA. Un cambio incompatible sube la versión mayor.
- **Matching (Java)** aplica las mismas convenciones en su stack; la equivalencia se verifica con los contratos y las pruebas, no con código compartido.
- **Excepción a ADR-013:** un servicio puede depender de `quickpatch-shared-dotnet`, nunca de otro servicio.

## Alcance de la v0.1.0 (11 de noviembre de 2026)

| Mecanismo | Antes | Con la v0.1.0 |
|---|---|---|
| Publicador del Outbox, `OutboxOptions` | Copiado en Catalog, ServiceRequest, Ranking y Payments | Compartido (`OutboxPublisher<TContext, TRecord>`); Identity tiene su propio diseño de Outbox y lo revisa SCRUM-650 |
| `CorrelationId` | Copiado en Identity, Catalog, ServiceRequest, Payments y Communication | Compartido en los 5 |
| `SessionRole` (`SET LOCAL ROLE` validado) | Copiado en Ranking y Payments, e integrado en los publicadores | Compartido |
| Contexto de tenant (`set_config` de RLS) | En 6 servicios, mezclado con reglas propias (por ejemplo, el conflicto de pago abierto de Payments) | **Sin compartir todavía**: el parecido es del 35 % y cada unidad de trabajo traduce errores de su dominio |
| Problem Details | Un archivo por servicio con los tipos de error de ese servicio | **Sin compartir**: los tipos de error son del contrato de cada servicio |
| Idempotencia (`processed_events`) | Repositorios de dos líneas sobre el DbContext de cada servicio | **Sin compartir todavía** |

Los servicios conservan el modelo de EF y las migraciones: su `OutboxEventRecord` implementa `IOutboxRecord`.

## Consecuencias

### Positivas
- Una corrección se hace una vez y cada servicio la adopta subiendo la etiqueta del submódulo.
- La corrección del apagado del publicador llegó a los cuatro servicios con la v0.1.0.
- Las convenciones de correlación y de rol de sesión las garantiza el mismo código, con sus pruebas (incluida una contra PostgreSQL con Testcontainers) en el CI del repositorio compartido.

### Costos
- Un repositorio y un pipeline más: 13 repositorios de componentes más el principal (ADR-021).
- Un cambio incompatible obliga a coordinar a los servicios que lo usan.
- AC7-E5 no llega a 0 copias con la v0.1.0: quedan el contexto de tenant y la idempotencia. Se re-mide con el mismo método del 5 de noviembre.

## Trazabilidad

- SAD: escenario AC7-E5; riesgo de la lógica transversal copiada (6.2); ADR-013.
- Relacionados: ADR-005, ADR-007, ADR-012, ADR-013, ADR-018, ADR-021.
- Jira: SCRUM-657 (historia SCRUM-647).
