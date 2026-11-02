# Datos de demostración de QA y producción

Script idempotente que carga en QA o en producción un juego de datos de demostración (SCRUM-632; la definición de los datos es SCRUM-633). Usa solo la API pública, el mismo camino de la app y del panel, así que respeta RLS y los roles de cada servicio.

| Archivo | Qué es |
|---|---|
| `cargar-datos-demo.py` | El script (Python 3, sin dependencias) |
| `juego-datos.json` | El juego de datos: categorías base, clientes, empresas, técnicos, un proveedor con su equipo, cobertura y solicitudes de ejemplo. Sin contraseñas |

## Qué carga

Todo queda en el tenant del ambiente (el del canal `quickpatch-mobile`).

- **6 categorías base** del catálogo, las mismas de QA: Aire acondicionado, Cerrajería, Eléctrico, Electrodomésticos, Pintura y Plomería. Se crean solo las que falten (`POST /v1/catalog/admin/categories`). Una categoría que existe inactiva no se reactiva: eso lo decide el administrador del tenant. Producción no tenía ninguna el 28 de octubre de 2026.
- **3 clientes hogar:** `demo.cliente1`, `demo.cliente2` y `demo.cliente3` (`@demo.quickpatch.test`).
- **2 empresas clientes** con su usuario `empresa_contacto`: Inmobiliaria & Coworking Bogotá S.A.S. (NIT `900123456-8`, `demo.empresa1`) y Restaurantes y Cafés Andinos S.A.S. (NIT `901987654-0`, `demo.empresa2`). El script valida el dígito de verificación de cada NIT con el algoritmo de la DIAN y se detiene si no cuadra.
- **4 técnicos independientes** (`demo.tecnico1` a `demo.tecnico4`; Plomería, Plomería, Cerrajería y Eléctrico), aprobados y con cobertura en las 20 localidades de Bogotá.
- **1 proveedor con un técnico de su equipo:**
  - El proveedor `demo.proveedor1` se registra con `POST /v1/auth/register/technician` y `role: proveedor`, y el administrador del tenant lo aprueba. Ese registro usa el mismo cuerpo del técnico, así que **no lleva razón social ni NIT**: el contrato no tiene esos campos para proveedores.
  - El técnico del equipo `demo.tecnico.proveedor1` lo crea el proveedor con `POST /v1/providers/me/technicians`. Ese técnico nace sin contraseña y con una invitación: el script define su contraseña con `POST /v1/auth/password/setup` y el token de la invitación (la misma `QP_DEMO_PASSWORD`), y después el administrador lo aprueba y le pone cobertura. Si el técnico ya existía, pide una invitación nueva (`POST /v1/providers/me/technicians/{userId}/invitation`); un 409 ahí significa que ya tenía contraseña.
- En QA los técnicos quedan además `disponible`. **En producción no se marcan disponibles** (siguen en `no_disponible`): marcarlos haría que Matching les ofreciera trabajo de clientes reales y reintentara solicitudes en espera (RN-M10). Para una demostración en producción se ponen disponibles a mano justo antes y se vuelven a bajar después.
- **5 solicitudes de ejemplo** con direcciones de Bogotá y la descripción `[DEMO] …`.

Antes de crear cuentas, el script revisa que existan en el catálogo todas las categorías que usan los técnicos, el proveedor, su equipo y las solicitudes. Si falta alguna, se detiene y lista las que existen; no usa otra categoría en su lugar.

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
- **Cuentas que ya existen en QA con otros datos.** La corrida del 26 de octubre creó `demo.cliente1`, `demo.cliente2`, `demo.tecnico1` y `demo.tecnico2` con otros nombres («Cliente Demo Uno», «Cliente Demo Dos», «Técnico Demo Plomería», «Técnico Demo Segundo») y la empresa «Empresa Demo S.A.S.» (NIT `900123456-7`, usuario `demo.empresa@demo.quickpatch.test`), además de 2 solicitudes `[DEMO]` con otras descripciones. Como el script no modifica lo que ya existe (409), en QA esas cuentas conservan los nombres viejos. Para que QA quede igual a este juego hay que retirarlas antes por la base, con respaldo. Si no se retiran, `demo.empresa1` puede chocar con el NIT `900123456` de la empresa vieja, porque el NIT es único dentro del tenant (RN-CC1).

## Qué no cubre

- No crea tenants ni administradores. El segundo tenant de QA (`tenant-beta`, usado en las pruebas de aislamiento AC6-E2) ya existe en QA y no lo carga este script; sus cuentas se manejan aparte.
- No guarda razón social ni NIT del proveedor: el registro de proveedores no tiene esos campos.
- Las solicitudes quedan en estado inicial; no simula cotizaciones, pagos ni chat.

## Corridas

- **26 de octubre de 2026, QA real** (versión anterior del juego): la primera corrida creó 2 clientes, 1 empresa, 2 técnicos (aprobados, con cobertura y disponibles) y 2 solicitudes, sin errores; la segunda dejó todo como «ya existía».
- **28 de octubre de 2026, QA real, `--solo-categorias`:** «6 ya existían, 0 con error».
- **2 de noviembre de 2026, servidor simulado en local** (`--base-url`), con el juego actual: la primera corrida creó todo (incluidos el proveedor y el técnico de su equipo, con contraseña definida y aprobado) sin errores; la segunda dejó todo como «ya existía» y terminó con código 0. En `--ambiente produccion` no marcó a nadie disponible.
- **El juego actual todavía no se ha corrido contra QA real ni contra producción.** En producción, primero `--simular`.
