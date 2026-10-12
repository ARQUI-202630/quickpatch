# ADR-020 — Código transversal compartido entre servicios .NET

- **Estado:** Propuesto
- **Fecha:** 6 de octubre de 2026
- **Decisión propuesta:** Publicar la lógica transversal de los servicios .NET (correlación, Problem Details, validación de JWT, contexto de tenant, Outbox e idempotencia) como paquetes NuGet internos versionados, sin lógica de dominio
- **Atributo priorizado:** AC7 Maintainability (Modifiability, Reusability)
- **Atributo sacrificado:** independencia total entre servicios (ADR-013: ningún servicio importa código de otro)
- **Escenario relacionado:** AC7-E5

## Contexto

Identity, Catalog y ServiceRequest copian hoy el mismo código transversal:

- middleware de `X-Correlation-Id`;
- manejo de errores con Problem Details (RFC 9457) y los tipos `https://quickpatch.internal/problems/<slug>`;
- validación del JWT RS256 (ADR-018) y lectura de los claims;
- transacción con `set_config('app.current_tenant', ...)` (ADR-005);
- Outbox y publicador a Kafka, y registro de `processed_events` (ADR-007).

Con 7 servicios .NET, una corrección (por ejemplo, de seguridad en la validación del token) habría que repetirla 7 veces, y las copias pueden divergir. ADR-013 prohíbe que un servicio importe código de **otro servicio**, pero no se pronuncia sobre una librería transversal sin dominio.

## Opciones

1. **Mantener copias** (situación actual): sin dependencias, pero cada corrección se repite y las copias divergen.
2. **Paquetes NuGet internos** en un repositorio `quickpatch-shared-dotnet`, publicados en GitHub Packages con versión semántica. Cada servicio fija la versión y actualiza cuando quiere.
3. **Plantilla de servicio** (`dotnet new`) con el código transversal: arranque homogéneo, pero las correcciones posteriores siguen siendo manuales.

## Recomendación

Opción 2, con estas reglas:

- Los paquetes no contienen entidades, eventos ni reglas de negocio; solo infraestructura transversal.
- Cada servicio fija una versión; actualizar es un PR propio del servicio.
- Matching (Java) implementa las mismas convenciones en su stack; la equivalencia se verifica con los contratos y las pruebas, no con código compartido.

## Consecuencias si se acepta

### Positivas
- Una corrección se publica una vez y cada servicio la adopta con un cambio de versión.
- Las convenciones (errores, correlación, tenant) quedan garantizadas por el mismo código.

### Costos
- Un repositorio y un pipeline más (R11), y un paquete que versionar con cuidado: un cambio incompatible obliga a coordinar a los servicios.
- Hace falta excepción explícita a ADR-013.

## Pendientes

Decisión del equipo antes de implementar los 4 servicios .NET restantes (Actors, Ranking, Payments, Communication), para no multiplicar las copias.

## Trazabilidad

- SAD: escenario AC7-E5; ADR-013.
- Relacionados: ADR-005, ADR-007, ADR-012, ADR-013, ADR-018.
