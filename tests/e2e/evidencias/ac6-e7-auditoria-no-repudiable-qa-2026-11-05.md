# AC6-E7: acción crítica no repudiable

Prueba en QA del 4 de noviembre de 2026 por la noche en Colombia (5 de noviembre, 03:15 a 03:20 UTC). Meta del escenario: (1) 100 % de las acciones críticas con un usuario autenticado y una marca de tiempo del servidor; (2) 100 % de los intentos de modificar o borrar `audit_logs` con la credencial de la aplicación, rechazados.

## Parte 1: usuario y hora en `audit_logs`

La tabla (`db_service_request` y `db_identity`) tiene `id`, `tenant_id`, `actor_user_id`, `action`, `target_id`, `metadata` y `created_at`.

| Base | Filas | Sin usuario | Sin hora | Periodo |
|---|---|---|---|---|
| `db_identity` | 876 | **0** | **0** | 14 oct a 5 nov |
| `db_service_request` | 1 (QA recién limpiado) | **0** | **0** | 5 nov |

Acciones en `db_identity`: `aprobar_tecnico`, `suspender_tecnico`, `rechazar_tecnico`, `generar_enlace_recuperacion`, `crear_tenant`, `activar_tenant` y `desactivar_tenant`.

Prueba en vivo de una acción crítica de ServiceRequest, a las 03:19:23 UTC: el `admin_tenant` de QA cancela una solicitud. Fila resultante: `cancelar_solicitud_admin`, `actor_user_id` = el administrador, `created_at` = 03:19:23.034 UTC (la hora del servidor, no la que manda el cliente) y `metadata` con el `correlationId` de la petición y el estado anterior (`buscando_tecnico`).

## Parte 2: la credencial de la aplicación no puede modificar la auditoría

Permisos sobre `audit_logs` (`information_schema.role_table_grants`):
- `service_request_app` (la credencial de la aplicación): **solo `INSERT` y `SELECT`**.
- `service_request_migrator` (migraciones): todos los permisos; no lo usa la aplicación en operación.

Intentos con `SET LOCAL ROLE service_request_app` dentro de una transacción que se revierte:

| Sentencia | Resultado |
|---|---|
| `UPDATE audit_logs SET created_at = now()` | `ERROR: permission denied for table audit_logs` |
| `DELETE FROM audit_logs` | `ERROR: permission denied for table audit_logs` |
| `TRUNCATE audit_logs` | `ERROR: permission denied for table audit_logs` |

Control: el mismo rol sí puede insertar y leer (`has_table_privilege`: insert, select = verdadero; update, delete = falso). Después de los intentos la tabla quedó intacta.

**Resultado: 3 de 3 intentos rechazados y 0 filas sin usuario ni hora.**

## Límites

- La parte 2 se probó con `SET ROLE` de un superusuario al rol de la aplicación, no con una conexión que use la contraseña real del Secret. Los privilegios son los mismos (el rol es el que tiene la concesión), pero no se ejercitó la cadena de conexión de la aplicación.
- Solo `identity` y `service-request` tienen `audit_logs`. Payments, Matching y Communication no tienen esa tabla.
- `created_at` no tiene valor por defecto en la base: lo pone el servicio. Es una hora del servidor, pero no la fuerza la base de datos.
- Las pruebas de integración del 22 de octubre que cita la matriz (`LaAplicacion_NoPuedeCambia...`) ya cubrían esto en CI; esta prueba lo repite en QA.
