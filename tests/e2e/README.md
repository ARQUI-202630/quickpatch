# e2e

Pruebas de sistema de QUICKPATCH contra el ambiente de QA. Las corre `.github/workflows/pruebas-sistema.yml` desde el runner de VM1 en cada `release/*` (compuerta 2 del Documento de Pruebas).

## Colección del MVP de Sprint 3

`quickpatch-mvp.postman_collection.json` recorre el flujo de punta a punta (SCRUM-27):

1. **Administrador del tenant:** inicia sesión y crea una categoría. Catalog publica `catalog.category-changed`.
2. **Cliente:** se registra, inicia sesión y ve la categoría nueva.
3. **Solicitud:** crea la solicitud. ServiceRequest valida la categoría en su réplica (si todavía no llegó, reintenta hasta 10 veces cada 2 s), la guarda en `buscando_tecnico` y publica `service-request.created`, que consume Matching. Después consulta el detalle.
4. **Casos negativos:** sin token (401), administrador creando una solicitud (403), cliente administrando categorías (403), ubicación fuera de Bogotá (422) y descripción corta (400 con el error por campo), con Problem Details y `correlationId`.
5. **Administrador de la plataforma (SCRUM-112):** inicia sesión y lista los tenants. Comprueba también que el administrador del tenant no puede listarlos (403), que el cliente no puede cambiarlos (403), que el tenant de la plataforma no se puede desactivar (409) y que activarlo es idempotente (200). Cubre además un estado fuera del contrato (400 por campo) y un tenant inexistente (404). Ningún paso deja un tenant inactivo, así que la carpeta se puede repetir en el QA compartido.

La colección se genera con `python tests/e2e/generar-coleccion.py`: se edita el script y se regenera el JSON.

### Variables

|Variable|Valor|
|---|---|
|`baseUrl`|`https://qa.quickpatch.internal` (sin `/api`; la colección lo agrega)|
|`adminEmail`, `adminPassword`|Administrador inicial de QA: el mismo `admin-email`/`admin-password` del Secret `identity-secretos`. En GitHub, secretos `QA_ADMIN_EMAIL` y `QA_ADMIN_PASSWORD` del repositorio. Nunca en la colección|
|`platformAdminEmail`, `platformAdminPassword`|Administrador de la plataforma de QA: `platform-admin-email`/`platform-admin-password` del mismo Secret. En GitHub, secretos `QA_PLATFORM_ADMIN_EMAIL` y `QA_PLATFORM_ADMIN_PASSWORD`. Nunca en la colección|

```bash
docker run --rm -v "$PWD/tests/e2e:/etc/newman" postman/newman:6-alpine run quickpatch-mvp.postman_collection.json \
  --insecure --env-var baseUrl=https://qa.quickpatch.internal --env-var adminEmail=... --env-var adminPassword=... \
  --env-var platformAdminEmail=... --env-var platformAdminPassword=...
```

### Evidencia

`evidencias/mvp-local-2026-10-07.txt`: corrida local con los cuatro servicios reales (Identity, Catalog, ServiceRequest y Matching), PostgreSQL+PostGIS, Kafka y un Nginx con las mismas rutas del gateway. Resultado: 13 peticiones y 18 aserciones sin fallos. Se verificó además en la base que el Outbox publicó `service-request.created` y que Matching lo registró en `processed_events`.

`evidencias/scrum-112-local-2026-10-07.txt`: la misma corrida local con la carpeta 5. Resultado: 21 peticiones y 30 aserciones sin fallos. Como la carpeta no desactiva ningún tenant, la evidencia agrega un cambio real sobre un segundo tenant de prueba: desactivarlo y reactivarlo deja dos registros en `audit_logs` (`desactivar_tenant` y `activar_tenant`), con el estado anterior, el nuevo y el `correlationId`.

### Evidencia en la app móvil

`evidencias/movil/`: app Flutter en un emulador Android 16 (Pixel 6) contra el mismo backend local, 7 de octubre de 2026:

1. inicio del cliente después del login (Identity);
2. categorías reales de Catalog y ubicación en Bogotá (después de rechazar el diálogo de "Location Accuracy" de Google, quickpatch-mobile#7);
3. formulario completo;
4. solicitud creada en "Buscando técnico".

En la base: la solicitud quedó en `buscando_tecnico` con su punto, el Outbox publicó `service-request.created` y Matching lo registró en `processed_events`.

## Orden del despliegue del MVP en QA

1. Infraestructura de QA (Ansible): bases `db_<servicio>` con su `_migrator` y su `_app`, PostGIS en `db_service_request` y `db_matching`, Redis, Kafka con los topics de `quickpatch-kafka/topics/topics.yaml` y Garage.
2. Secretos de Kubernetes de cada servicio (`deploy/k8s/README.md` de Identity, Catalog, ServiceRequest y Matching). Un solo par de llaves RSA: la privada para Identity y la pública para los demás.
3. `kubectl apply -f deploy/k8s/<servicio>.yaml` en cada repositorio.
4. Rama `release/*` en cada servicio: el pipeline publica la imagen y la despliega en QA; los init containers aplican las migraciones.
5. Solo la primera vez: `db/roles.sql` de cada servicio, el alta del tenant (`identity/db/seed-tenant.example.sql`) y `kubectl -n quickpatch rollout restart deployment` para que Identity cree los administradores iniciales (`admin-email` y `platform-admin-email` del Secret `identity-secretos`).
6. Panel web: el administrador de la plataforma entra en `https://qa.quickpatch.internal`, ve los tenants y los activa o desactiva (SCRUM-41).
7. Rama `release/*` en este repositorio: corre esta colección contra QA.
8. App móvil: `config/qa.json` con la huella del certificado de VM1 (`quickpatch-mobile`, README).

## Flujo Web Administrativo y Gestión de Tenants (SCRUM-318)

Pruebas de sistema de extremo a extremo que validan el flujo de administración web en Angular, los contratos REST de Identity/Plataforma y el control de acceso RBAC según los mockups de diseño W-01 a W-07 y DD 7.12:

1. **Autenticación administrativa (W-01):** inicio de sesión de `admin_plataforma` y `admin_tenant` verificando claims de JWT y ausencia de selector manual de tenant en la interfaz.
2. **Manejo de errores de acceso (W-02):** rechazo de credenciales inválidas (401) y detección de cuenta bloqueada tras múltiples intentos fallidos (423 Locked bajo RN-U4).
3. **Control de acceso por roles RBAC (W-03):** intentos de acceso de `admin_tenant` a la gestión de empresas devuelven 403 Forbidden (`/problems/no-autorizado`), y accesos anónimos devuelven 401 Unauthorized (`/problems/no-autenticado`).
4. **Consulta y filtros de empresas (W-04):** listado de tenants por `admin_plataforma`, filtros por estado activo/inactivo y presencia de atributos requeridos (nombre, NIT, estado).
5. **Desactivación de tenant (W-05):** actualización de estado a inactivo (SCRUM-113) y confirmación de que sus usuarios no pueden iniciar sesión (RN-T1 / SCRUM-114).
6. **Estados de interfaz y concurrencia (W-06):** manejo de skeleton, estados vacíos y rechazo por conflicto de concurrencia optimista (409 Conflict con `/problems/conflicto-concurrencia`).
7. **Navegación dinámica (W-07):** adaptación del sidebar según el rol (`admin_tenant` no visualiza la opción de tenants).

### Ejecución de Newman

La colección `scrum-318-web-admin.postman_collection.json` se regenera con:
```bash
python tests/e2e/generar-scrum318-admin.py
```

Para correr las pruebas localmente con el servidor mock del gateway:
```bash
node tests/e2e/run-web-admin-e2e.js
```

O contra el ambiente de QA en VM2:
```bash
node tests/e2e/run-web-admin-e2e.js --remote
```

### Ejecución de Playwright

Las pruebas de componentes e interfaz web se definen en `specs/web-admin.spec.ts` y corren con:
```bash
npx playwright test specs/web-admin.spec.ts
```

### Evidencia local

`evidencias/scrum-318-web-admin-2026-10-07.txt`: corrida local con 11 peticiones y 31 aserciones aprobadas sin fallos.
