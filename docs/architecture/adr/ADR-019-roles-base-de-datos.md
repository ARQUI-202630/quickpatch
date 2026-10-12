# ADR-019 — Roles de base de datos separados por responsabilidad

- **Estado:** Propuesto (el DD 10.2 ya lo define; falta alinear la infraestructura)
- **Fecha:** 6 de octubre de 2026
- **Decisión:** Cada base de servicio usa roles distintos para la operación de negocio (sin `BYPASSRLS`), el publicador del Outbox, las migraciones y, solo en Identity, las operaciones de plataforma
- **Atributo priorizado:** AC6 Security (mínimo privilegio; RLS efectivo)
- **Atributo sacrificado:** AC7 Maintainability (más roles, permisos y credenciales que administrar)
- **Killers y drivers:** D5, K12
- **Escenario que la sustenta:** AC6-E2

## Contexto

RLS (ADR-005) no aplica al dueño de una tabla cuando la tabla no tiene `FORCE ROW LEVEL SECURITY`, ni a ningún rol con `BYPASSRLS`. Si el servicio se conecta con el mismo rol que es dueño de las tablas y corre las migraciones, el aislamiento entre tenants depende de que ese rol no tenga privilegios de más.

Hoy hay una contradicción entre documentos:

- El **DD 10.2** define cuatro roles por servicio (`<servicio>_app`, `<servicio>_outbox`, `<servicio>_migrator` e `identity_platform`).
- **Ansible** (`postgres-init.sql.j2`) crea un solo rol `app_<servicio>`, que además es dueño de la base.

## Decisión (propuesta)

Seguir el DD 10.2:

|Rol|`BYPASSRLS`|Uso|
|---|---|---|
|`<servicio>_app`|No|Peticiones REST y consumidores de eventos. Solo `INSERT` sobre `outbox_events`.|
|`<servicio>_outbox`|Sí|Publicador del Outbox. Solo `SELECT` y `UPDATE` sobre `outbox_events`. Se adopta con `SET LOCAL ROLE` dentro de la transacción; `_app` es miembro con `NOINHERIT`.|
|`<servicio>_migrator`|Sí|Solo el paso de migraciones del pipeline; es el dueño de las tablas.|
|`identity_platform`|Sí|Solo Identity, para las operaciones de plataforma (administración de tenants).|

- Los servicios se conectan con `_app`; el pipeline de despliegue ejecuta las migraciones con `_migrator`.
- Los servicios ya incluyen `db/roles.sql` con la definición de sus roles, como referencia para DevOps.

## Alternativas descartadas

- **Un solo rol dueño por servicio (lo que hace hoy Ansible):** más simple, pero el rol de la aplicación puede alterar el esquema y queda a una configuración de distancia de omitir RLS.
- **Dos roles (aplicación y migraciones), con el publicador usando el rol de migraciones:** el publicador tendría permisos de dueño sobre todas las tablas.

## Consecuencias

### Positivas
- Un error en el código de la aplicación no puede omitir RLS ni cambiar el esquema.
- El publicador del Outbox solo puede tocar `outbox_events`.

### Costos
- Más credenciales que gestionar en Ansible Vault y en los secretos de Kubernetes (la credencial del migrador solo en el pipeline).
- Cambio en la infraestructura existente: Ansible, `pg_hba.conf` y el paso de migraciones.

## Pendientes

- Decisión del rol de DevOps para alinear Ansible y el pipeline; al hacerlo, este ADR pasa a Aceptado.
- Mientras tanto, las pruebas de integración de los servicios ya usan el esquema de roles del DD.

## Trazabilidad

- DD: sección 10.2 (roles) y 10.4 (operaciones de plataforma).
- Infraestructura: `ansible/templates/postgres-init.sql.j2`, `qa-postgres-init.sql.j2`.
- Relacionados: ADR-005, ADR-007, ADR-014.
