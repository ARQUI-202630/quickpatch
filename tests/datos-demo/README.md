# Datos de demostración de QA y producción

Script idempotente que carga en QA o en producción un juego de datos de demostración (SCRUM-632, SCRUM-634). Usa solo la API pública, el mismo camino de la app y del panel, así que respeta RLS y los roles de cada servicio.

| Archivo | Qué es |
|---|---|
| `cargar-datos-demo.py` | El script (Python 3, sin dependencias) |
| `juego-datos.json` | El juego de datos: categorías base, clientes, empresa, técnicos, cobertura y solicitudes de ejemplo. Sin contraseñas |

## Qué carga

- Las 6 categorías base del catálogo, las mismas de QA: Aire acondicionado, Cerrajería, Eléctrico, Electrodomésticos, Pintura y Plomería. Se crean solo las que falten (`POST /v1/catalog/admin/categories`). Una categoría que existe inactiva no se reactiva: eso lo decide el administrador del tenant. Producción no tenía ninguna el 28 de octubre de 2026.
- 2 clientes, 1 empresa cliente con su usuario y 2 técnicos, aprobados y con cobertura en las 20 localidades de Bogotá. En QA los técnicos quedan además `disponible`. **En producción no se marcan disponibles** (siguen en `no_disponible`): marcarlos haría que Matching les ofreciera trabajo de clientes reales y reintentara solicitudes en espera (RN-M10). Para una demostración en producción se ponen disponibles a mano justo antes y se vuelven a bajar después.
- 2 solicitudes de ejemplo con direcciones de Bogotá, con la descripción `[DEMO] …`.
- Los correos usan el dominio `demo.quickpatch.test`. Las categorías se buscan por nombre en el catálogo del ambiente después de sembrarlas; si falta alguna, el script se detiene y lista las que existen.

El juego es un punto de partida: la definición final de los datos es la tarea SCRUM-633 y se ajusta en `juego-datos.json`.

## Cómo se usa

Las credenciales van en el entorno, nunca en el repositorio ni en este archivo:

| Variable | Qué es |
|---|---|
| `QP_ADMIN_EMAIL`, `QP_ADMIN_PASSWORD` | Administrador **del tenant** del ambiente, rol `admin_tenant` (`vault_identity_admins` del vault de Ansible). Aprobar técnicos es solo de `admin_tenant`; el administrador de la plataforma recibiría 403 |
| `QP_DEMO_PASSWORD` | Contraseña de las cuentas de demostración, entre 8 y 128 caracteres (política de Identity) |

```bash
python3 tests/datos-demo/cargar-datos-demo.py --ambiente qa --simular       # muestra el plan, no escribe nada
python3 tests/datos-demo/cargar-datos-demo.py --ambiente qa                 # carga en QA
python3 tests/datos-demo/cargar-datos-demo.py --ambiente produccion --confirmar-produccion
python3 tests/datos-demo/cargar-datos-demo.py --ambiente produccion --confirmar-produccion --solo-categorias
```

Con `--solo-categorias` solo crea las categorías base. No crea cuentas ni solicitudes de demostración y no necesita `QP_DEMO_PASSWORD`. Así se siembra el catálogo de producción después de la promoción (SCRUM-518). Contra QA, el 28 de octubre de 2026 respondió «6 ya existían, 0 con error».

Hace falta la VPN: el script entra por la IP de VM1 con el `Host` del ambiente, como la app móvil.

Al terminar imprime el conteo de creados, ya existentes, aplicados y con error. Termina con código 1 si hubo algún error. Si un registro ya existe (HTTP 409) lo deja como está, así que se puede repetir sin duplicar nada.

## Limpieza

- **Datos de las pruebas de carga (k6):** `infrastructure/ansible/playbooks/limpiar-carga-qa.yml`. Filtra las solicitudes por «Solicitud de carga k6 %» y «Estrés pico 150 VU%», así que **no toca** las de demostración (`[DEMO] …`). Primero solo cuenta; con `-e borrar=si` respalda las bases y borra.
- **Datos de demostración:** la API no ofrece borrar usuarios ni solicitudes. Si hace falta retirarlos, se hace en la base con un respaldo previo, filtrando por el dominio `demo.quickpatch.test` y por `[DEMO]`.

## Qué no cubre

- No crea tenants de proveedores ni administradores de tenant.
- Las solicitudes quedan en estado inicial; no simula cotizaciones, pagos ni chat.
- Se probó contra un servidor simulado en local (flujo, paginación, producción y fallos de aprobación) y contra QA real el 26 de octubre de 2026: la primera corrida creó 2 clientes, 1 empresa, 2 técnicos (aprobados, con cobertura y disponibles) y 2 solicitudes, sin errores; la segunda dejó todo como «ya existía». **En producción todavía no se ha corrido**: primero `--simular`, y los técnicos quedan sin marcar disponibles.
