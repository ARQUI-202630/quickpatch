# ADR-014 — Una instancia de PostgreSQL con una base de datos por servicio

- **Estado:** Aceptado
- **Fecha:** septiembre de 2026 (registrado como archivo el 6 de octubre de 2026; ya lo citaban el SDD y el Documento de Infraestructura)
- **Decisión:** Una sola instancia de PostgreSQL + PostGIS en VM4, con una base de datos propia por microservicio (`db_<servicio>`) y credenciales separadas
- **Atributo priorizado:** AC7 Maintainability (Modularity: cada servicio es dueño de sus datos) dentro del presupuesto de recursos
- **Atributo sacrificado:** AC5 Reliability (la instancia es un punto único de falla)
- **Restricciones:** R5, R10, R11

> **Actualización (ADR-022, 6 de octubre de 2026):** la instancia de QA pasa de VM2 a VM6; producción sigue en VM4.

## Contexto

Con microservicios (ADR-003), cada servicio debe ser dueño de sus datos: ningún otro puede leer sus tablas ni depender de su esquema. La forma habitual es un servidor de base de datos por servicio, pero solo hay 7 VMs (R10) y una sola persona que las administra (R11). VM4 es la VM de base de datos.

## Decisión

- Una sola **instancia** de PostgreSQL 16 con PostGIS en VM4 (y otra propia en VM2 para QA, ADR-015).
- Una **base de datos por servicio** (`db_identity`, `db_actors`, `db_catalog`, `db_service_request`, `db_matching`, `db_ranking`, `db_payments`, `db_communication`). PostgreSQL no permite llaves foráneas ni JOINs entre bases, así que la separación la impone el motor y no la disciplina del equipo.
- **Credenciales por servicio**: cada servicio solo puede conectarse a su propia base, y `pg_hba.conf` solo admite conexiones desde los nodos de k3s. Los roles dentro de cada base se definen en ADR-019.
- Cuando un servicio necesita datos de otro, los obtiene por eventos (ADR-017) o por su API, nunca de la base del otro.

## Alternativas descartadas

- **Una instancia (o VM) por servicio:** el aislamiento más fuerte, pero 8 servidores no caben en 7 VMs (R10) y multiplican el mantenimiento (R11).
- **Una sola base compartida con un esquema por servicio:** el motor sí permite consultas entre esquemas, así que un servicio podría acoplarse al esquema de otro.
- **Una sola base y un solo esquema:** contradice la independencia de los servicios (ADR-003).

## Consecuencias

### Positivas
- Cada servicio evoluciona su esquema y sus migraciones de forma independiente.
- Un solo servidor que respaldar (`pg_dump` diario de cada base a Garage, ADR-016), monitorear y actualizar.

### Costos
- Punto único de falla: si VM4 cae, caen todas las bases (limitación aceptada en el Documento de Infraestructura).
- Recursos compartidos: un servicio con consultas pesadas afecta a los demás; el límite de 100 conexiones de la instancia se reparte entre los pools de los 8 servicios.

## Evidencia

- Ansible crea `db_<servicio>` y su rol de conexión en VM4 y en VM2.
- Cada servicio implementado (Identity, Catalog, ServiceRequest) tiene su propia cadena de conexión y migraciones, y sus pruebas de integración usan una base aislada.

## Trazabilidad

- SDD: vista de contenedores (C4 nivel 2) y sección de datos por servicio.
- Documento de Infraestructura: VM4, `pg_hba.conf` y respaldos.
- DD: propietario de cada tabla.
- Relacionados: ADR-003, ADR-004, ADR-005, ADR-016, ADR-017, ADR-019.
