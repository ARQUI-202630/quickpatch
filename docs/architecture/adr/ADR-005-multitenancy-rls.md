# ADR-005 — Multi-tenancy con esquema compartido, `tenant_id` y Row-Level Security

- **Estado:** Aceptado
- **Fecha:** agosto de 2026 (SAD 1.0)
- **Decisión:** Todos los tenants comparten las mismas tablas; cada fila lleva `tenant_id` y PostgreSQL aplica Row-Level Security (RLS) forzado
- **Atributo priorizado:** AC7 Maintainability (costo y velocidad de implementación)
- **Atributo sacrificado:** AC6 Security (aislamiento físico total entre tenants)
- **Driver y restricción:** D5 (multi-tenancy), R3 (tiempo)
- **Escenario que la sustenta:** AC6-E2 (cero fugas de datos entre tenants)

## Contexto

QUICKPATCH atiende a varias empresas oferentes (tenants). Los datos de una nunca pueden ser visibles para otra (D5, RF-04, RNF-10). Hay tres formas clásicas de aislar: una base por tenant, un esquema por tenant o un esquema compartido con una columna de tenant.

El aislamiento no puede depender solo de que cada consulta de la aplicación recuerde filtrar por tenant: un solo olvido expondría datos de otra empresa.

## Decisión

- **Esquema compartido** con `tenant_id` en cada tabla de negocio.
- **RLS forzado** (`ENABLE` + `FORCE ROW LEVEL SECURITY`) con la política `tenant_id = current_setting('app.current_tenant')` en lectura y escritura (DD, sección de multi-tenancy).
- Cada operación corre en una transacción que primero fija el tenant con `set_config('app.current_tenant', ..., true)` (equivale a `SET LOCAL`). Sin tenant fijado, `current_setting` devuelve nulo y no se ve ni se escribe nada: el sistema **falla cerrado**.
- El tenant sale **solo** del token (`tenant_id`, ADR-018) o, en el registro y el login, del canal; nunca del cuerpo de la petición (RN-U3, RN-U5).
- El servicio usa un rol sin `BYPASSRLS`; solo los roles técnicos (publicador del Outbox, migraciones, operaciones de plataforma) lo omiten (ADR-019).

## Alternativas descartadas

- **Una base de datos por tenant:** aislamiento físico total, pero multiplica bases, conexiones y migraciones por cada empresa; no cabe en las 100 conexiones de VM4 ni en R3.
- **Un esquema por tenant:** aislamiento fuerte, pero cada alta de tenant exige crear esquemas y migrarlos en todos los servicios (contradice RNF-09: incorporar tenants sin afectar a los demás).
- **Filtro solo en la aplicación (sin RLS):** más simple, pero un error de código expone datos de otra empresa; RLS deja la base como segunda barrera.

## Consecuencias

### Positivas
- Incorporar un tenant es insertar una fila (RNF-09, AC8-E1).
- La base de datos garantiza el aislamiento aunque la aplicación tenga un error.

### Costos
- Todas las operaciones deben pasar por la transacción que fija el tenant; una consulta fuera de ella no ve nada.
- Las operaciones que recorren varios tenants (publicador del Outbox, tareas programadas) necesitan roles técnicos con `BYPASSRLS`, muy acotados.
- Las pruebas de aislamiento son obligatorias en cada servicio.

## Evidencia

Pruebas de integración contra PostgreSQL real en Identity, Catalog y ServiceRequest: sin tenant no se ve ninguna fila, otro tenant no ve nada, y un `INSERT` con un tenant distinto al de la sesión falla con `42501`.

## Trazabilidad

- SAD: driver D5, escenarios AC6-E2 y AC8-E1, sección 6.
- DD: tablas con `tenant_id`, roles de base de datos y origen del tenant.
- Relacionados: ADR-004, ADR-014, ADR-018, ADR-019.
