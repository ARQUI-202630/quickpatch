# ADR — QUICKPATCH

Cada decisión de arquitectura tiene su propio archivo en esta carpeta, con contexto, decisión, alternativas descartadas, consecuencias, evidencia y trazabilidad. Las tablas de las secciones 5.5 y 6 del SAD resumen los trade-offs y enlazan aquí.

| ADR | Decisión | Atributo priorizado | Estado |
|---|---|---|---|
| [ADR-002](ADR-002-flutter-cliente-movil.md) | Flutter como cliente móvil único | AC7 | Aceptado |
| [ADR-003](ADR-003-microservicios-eda.md) | Microservicios + EDA | AC8, AC5 | Aceptado |
| [ADR-004](ADR-004-postgresql-postgis.md) | PostgreSQL + PostGIS | AC2 | Aceptado |
| [ADR-005](ADR-005-multitenancy-rls.md) | Multi-tenancy con `tenant_id` + RLS | AC7 | Aceptado |
| [ADR-006](ADR-006-kafka-bus-eventos.md) | Kafka como bus de eventos | AC5, AC8 | Aceptado |
| [ADR-007](ADR-007-outbox-idempotencia.md) | Outbox + idempotencia | AC5 | Aceptado |
| [ADR-009](ADR-009-tokenizacion-pagos.md) | Tokenización de pagos | AC6 | Aceptado |
| [ADR-011](ADR-011-k3s-orquestacion.md) | k3s para los microservicios | AC5 | Aceptado; ampliado por ADR-015 |
| [ADR-012](ADR-012-stack-tecnologico-polyglot.md) | Stack polyglot | AC7 | Aceptado |
| [ADR-013](ADR-013-estrategia-de-repositorios.md) | Un repositorio por componente | AC7 | Aceptado |
| [ADR-014](ADR-014-postgresql-instancia-unica.md) | Una instancia de PostgreSQL, una base por servicio | AC7 | Aceptado |
| [ADR-015](ADR-015-ambiente-qa-en-vm2.md) | QA en VM2 y acceso por VM1 | AC7 | Aceptado |
| [ADR-016](ADR-016-garage-storage-objetos.md) | Garage como almacenamiento de objetos | AC6, AC2 | Aceptado |
| [ADR-017](ADR-017-replicas-locales-por-eventos.md) | Réplicas locales alimentadas por eventos | AC5, AC2 | Aceptado |
| [ADR-018](ADR-018-jwt-rs256-identity.md) | JWT RS256 firmado solo por Identity | AC6 | Aceptado |
| [ADR-019](ADR-019-roles-base-de-datos.md) | Roles de base de datos por responsabilidad | AC6 | Propuesto |
| [ADR-020](ADR-020-codigo-transversal-compartido.md) | Código transversal compartido (.NET) | AC7 | Propuesto |

**Números sin asignar.** ADR-001 y ADR-010 nunca se usaron. ADR-008 aparecía en versiones anteriores del SAD como referencia a una decisión que no existía y se retiró en la versión 2.0. No se reutilizan, para no confundir referencias históricas.

**Cómo agregar un ADR.** Usar el siguiente número libre, copiar la estructura de un ADR existente, agregarlo a esta tabla y a la tabla correspondiente del SAD (5.5 si es de infraestructura, 6 si es de software) en el mismo Pull Request.
