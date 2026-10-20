# Pruebas E2E y de Sistema (API) — QUICKPATCH

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

## Cancelación de la solicitud de punta a punta (SCRUM-478)

`scrum-478-cancelacion.postman_collection.json` prueba RF-36 (SCRUM-472) contra QA. Se genera con `python tests/e2e/generar-scrum478-cancelacion.py`.

1. **Preparación (administrador del tenant):** una categoría solo para la corrida y un técnico con esa especialidad, aprobado, que cubre toda Bogotá y queda disponible. Así la oferta le llega a él y no a otro técnico de QA.
2. **Cliente con la oferta pendiente:** el técnico ve la oferta; motivo de 4 caracteres (400 con `reason`), sin token (401), otro cliente del tenant (404), cliente del tenant Beta por `beta.qa.quickpatch.internal` (404, con el `tenant_id` del token distinto) y técnico (403). Después el cliente cancela (200, `CancelledServiceRequest`), el detalle trae la fecha y el motivo sin espacios, cancelar otra vez da 409 `transicion-invalida`, el técnico deja de ver la oferta (Matching consumió `service-request.cancelled`), aceptarla da 409 `oferta-no-disponible` y el técnico sigue disponible.
3. **Administrador con el técnico asignado:** el técnico acepta, la solicitud queda `asignado` y el técnico `ocupado`; el administrador de la plataforma no puede cancelar (403); el administrador del tenant cancela (`admin_tenant`), el cliente ve su motivo y el técnico vuelve a `disponible`.
4. **Release 0.4.0 de ServiceRequest:** `location-preview` ubica una dirección en Bogotá con su localidad (Nominatim de QA); el `admin_tenant` ve los conteos de su tenant con las cancelaciones de la corrida; el `admin_plataforma` ve los conteos por tenant sin datos de las solicitudes (rol `service_request_platform`), y el cliente no ve los conteos (403).
5. **Limpieza:** suspende al técnico y desactiva la categoría de la corrida.

Sin `adminEmail` y `adminPassword` los pasos de técnico, ofertas y administrador se omiten (`pm.execution.skipRequest`), para poder correr el resto sin secretos. Cada corrida usa cuentas nuevas con una clave aleatoria que no se guarda.

`scrum-478-aviso-tiempo-real.mjs` cubre el aviso, que Newman no puede probar porque no habla WebSocket: abre `/v1/realtime`, cancela y espera `service-request.status-changed` con `cancelado` en menos de 15 s. Usa Node 22 o superior, sin dependencias:

```bash
NODE_TLS_REJECT_UNAUTHORIZED=0 node tests/e2e/scrum-478-aviso-tiempo-real.mjs https://qa.quickpatch.internal
```

**Evidencia:** `evidencias/scrum-478-cancelacion-qa-2026-10-19.txt`, con el resultado de cada paso y su `correlationId`. No se suben las exportaciones JSON de Newman porque traen los tokens y las claves de las cuentas de prueba.

## Cotización y ejecución con evidencia de punta a punta (SCRUM-490 y SCRUM-96)

`scrum-490-cotizacion.postman_collection.json` y `scrum-96-evidencia.postman_collection.json` se generan con `python tests/e2e/generar-scrum490-96-cotizacion-evidencia.py`, que también escribe las fotos de prueba de `fixtures/`. Las dos arrancan igual: el administrador del tenant crea una categoría para la corrida, aprueba a un técnico con esa especialidad, que cubre las 20 localidades y queda disponible, y se registran un cliente, otro cliente del mismo tenant, un cliente del tenant Beta y un técnico sin aprobar.

**SCRUM-490, cotización (service-request 1.6.0):**

1. **Tres rechazadas (RN-Q7):** lista vacía; monto sin decimales (400 en `laborAmount`); el cliente no cotiza (403); cotización 1 (201, `quoteNumber` 1, total calculado) y la solicitud pasa a `cotizado`; otra con una pendiente (409 `transicion-invalida`); el técnico no acepta (403); otro cliente (404); el cliente de Beta no ve las cotizaciones (404 por RLS); motivo corto (400); rechazos con y sin motivo; la tercera rechazada cancela la solicitud con «Cotizaciones rechazadas.», el técnico ve las tres en orden y Matching lo libera.
2. **Rechazar y aceptar:** rechaza la primera, acepta la segunda (`cotizacion_aceptada`, quedan 1), aceptar otra vez y cotizar con una aceptada (409), y el técnico sigue `ocupado`.
3. **Cierre:** el cliente cancela la solicitud 2 (todavía se puede antes de iniciar, RN-SR7) y el técnico vuelve a `disponible`.

El vencimiento (RN-Q6) no entra: `Quotes__Ttl` es de 24 horas en QA.

**SCRUM-96, iniciar, evidencia y completar (service-request 1.7.0):** después de la cotización aceptada:

1. **Iniciar:** subir o completar antes de iniciar (409), el cliente no inicia (403), otro técnico (404), el asignado inicia (`StartedServiceRequest`), iniciar otra vez y cancelar después de iniciar (409).
2. **Evidencia en Garage:** completar sin fotos (422 `evidencia-requerida`); un archivo de texto con nombre `.jpg` (400 en `file`: el tipo se reconoce por el contenido); otro técnico (404); la foto se sube (201, solo `id` y `uploadedAt`); el cliente la lista y la descarga con `image/png` y el mismo tamaño; el `admin_tenant` la ve; otro cliente y el cliente de Beta reciben 404.
3. **Completar:** `CompletedServiceRequest`, el detalle trae `startedAt` y `completedAt`, subir o completar otra vez da 409, y el técnico vuelve a `disponible` cuando Matching consume `service-request.completed`.

Los límites de 10 MB y de 10 fotos los cubren las pruebas del backend. Las dos colecciones necesitan `adminEmail` y `adminPassword`; sin ellos, todo se omite. Correr con `--reporters cli` y guardar la salida en un `.txt`: el reporte JSON de Newman guarda los cuerpos con tokens y no se sube. En `pruebas-sistema.yml` entran solas por el patrón `tests/e2e/*.postman_collection.json`, con `tests/e2e` como carpeta de trabajo, que es donde Newman busca `fixtures/`.

Para correrlas a mano (no lanzar el workflow completo, que incluye k6):

```bash
docker run --rm -v "$PWD/tests/e2e:/etc/newman" postman/newman:6-alpine run scrum-490-cotizacion.postman_collection.json   --insecure --reporters cli --env-var "baseUrl=https://qa.quickpatch.internal"   --env-var "adminEmail=$QA_ADMIN_EMAIL" --env-var "adminPassword=$QA_ADMIN_PASSWORD" > scrum-490.txt
```

## Orden del despliegue del MVP en QA

1. Infraestructura de QA (Ansible): bases `db_<servicio>` con su `_migrator` y su `_app`, PostGIS en `db_service_request` y `db_matching`, Redis, Kafka con los topics de `quickpatch-kafka/topics/topics.yaml` y Garage.
2. Secretos de Kubernetes de cada servicio (`deploy/k8s/README.md` de Identity, Catalog, ServiceRequest y Matching). Un solo par de llaves RSA: la privada para Identity y la pública para los demás.
3. `kubectl apply -f deploy/k8s/<servicio>.yaml` en cada repositorio.
4. Rama `release/*` en cada servicio: el pipeline publica la imagen y la despliega en QA; los init containers aplican las migraciones.
5. Solo la primera vez: `db/roles.sql` de cada servicio, el alta del tenant (`identity/db/seed-tenant.example.sql`) y `kubectl -n quickpatch rollout restart deployment` para que Identity cree los administradores iniciales (`admin-email` y `platform-admin-email` del Secret `identity-secretos`).
6. Panel web: el administrador de la plataforma entra en `https://qa.quickpatch.internal`, ve los tenants y los activa o desactiva (SCRUM-41).
7. Rama `release/*` en este repositorio: corre esta colección contra QA.
8. App móvil: `config/qa.json` con la huella del certificado de VM1 (`quickpatch-mobile`, README).

---

## Validación y Diagnóstico de Errores (SCRUM-325)

Procedimiento automatizado que demuestra la trazabilidad de errores y la capacidad de diagnóstico en los logs centralizados de Loki (VM1) sin acceso interactivo por SSH (SAD §3.7 / AC7-E4 y SAD §3.6 / RNF-04 / AC6-E3):

1. **Provocación de errores controlados:**
   - **422 Unprocessable Entity:** Creación de solicitud con coordenadas fuera del área de cobertura (`POST /api/v1/service-requests`), retornando RFC 9457 Problem Details (`Problems.OutOfCoverage`, RN-SR9) y `X-Correlation-Id`.
   - **403 Forbidden:** Intento de acceso no autorizado a endpoint administrativo de catálogo (`POST /api/v1/catalog/admin/categories`) por rol cliente, validando la auditoría de seguridad RNF-04.
2. **Diagnóstico en Loki:**
   - Búsqueda en Grafana (`https://grafana.quickpatch.internal`) mediante LogQL con etiquetas Promtail:
     `{job="k3s", vm="vm2"} |= "<correlationId>"`
   - Extracción de la traza estructurada con causa raíz (`CoverageArea` o regla de autorización) en segundos.

### Ejecución
```bash
node tests/e2e/validar-diagnostico-error-qa.js
```
O contra el entorno real de QA en VM2:
```bash
node tests/e2e/validar-diagnostico-error-qa.js --remote
```

### Documentación y Evidencia
- Guía detallada: `docs/testing/diagnostico-error-qa.md`.
- Evidencia de simulación: `tests/e2e/evidencias/scrum-325-diagnostico-error-qa-2026-10-07.txt`.

---

## Suite E2E de Roles, Permisos y Aislamiento de Tenants (SCRUM-65, SCRUM-114)

Esta suite complementa la verificación de seguridad del release validando específicamente el control de acceso por roles (RBAC), el aislamiento multi-tenant y la regla de ciclo de vida de tenants (RN-T1) según SAD, DD y el Documento de Pruebas (TD V1.4):

- **Colección:** `scrum-65-roles-y-tenants.postman_collection.json`
- **Casos cubiertos:**
  - `IDN-001` a `IDN-003`: Autenticación RS256 contra `/api/v1/auth/login` y registro legítimo de cliente.
  - `IDN-012` & `CAT-010`: Rechazo de creación de solicitud por `admin_tenant` (403) y creación de categoría administrativa por `cliente` (403), verificando RFC 9457 `problems/no-autorizado`.
  - `IDN-017`: Rechazo inmediato de peticiones anónimas sin token (401), retornando `problems/no-autenticado`.
  - `IDN-019` & `E2E-004`: regla **RN-T1** (rechazo de inicio de sesión de un tenant inactivo). **Pendiente en el MVP** y marcada como `skipped` en la colección: el login usa el tenant del canal (RN-U5), que es el de la plataforma y no se puede desactivar (409), así que no hay un tenant inactivo que probar. Se activa con un segundo tenant de prueba (SCRUM-41). Mientras tanto la colección verifica que un correo inexistente recibe 401 en Problem Details con `correlationId`.
  - `TEN-001`: Control positivo de procesamiento de solicitudes para tenants activos (`buscando_tecnico`).
  *(Nota: mientras IDN-019 está pendiente en QA, el rechazo por tenant inactivo también se ejecuta contra el simulador en `scrum-318-web-admin.simulacion.json`, caso 5.3).*

### Ejecución

#### Simulación Local Preparatoria
Para validar la suite en entorno local de desarrollo antes del despliegue en QA:
```bash
node tests/e2e/run-e2e.js
```
*Nota:* Ejecuta una simulación preparatoria con el mock local (`mock-gateway-qa.js`) que valida el 100% de contratos y aserciones. La ejecución formal contra el clúster de QA queda programada para ejecutarse una vez finalice el despliegue de VM2.

#### Ejecución contra el Entorno de QA (VM2)
```bash
node tests/e2e/run-e2e.js --remote
```
O directamente con Newman:
```bash
npx --yes newman run tests/e2e/scrum-65-roles-y-tenants.postman_collection.json \
  --env-var "baseUrl=https://qa.quickpatch.internal" \
  --insecure \
  --reporters cli
```

---

## Flujo Web Administrativo y Gestión de Tenants (SCRUM-318)

Pruebas de sistema de extremo a extremo que validan el flujo de administración web en Angular, los contratos REST de Identity/Plataforma y el control de acceso RBAC según los mockups de diseño W-01 a W-07 y DD 7.12. Se mantiene como archivo de simulación `scrum-318-web-admin.simulacion.json` para desacoplarlo del runner de CI (`*.postman_collection.json`) de QA:

1. **Autenticación administrativa (W-01):** inicio de sesión en `/iniciar-sesion` para `admin_plataforma` (usando `{{platformAdminEmail}}` y `{{platformAdminPassword}}`) y `admin_tenant` verificando claims de JWT y ausencia de selector manual de tenant en la interfaz.
2. **Manejo de errores de acceso (W-02):** rechazo de credenciales inválidas (401) y detección de cuenta bloqueada tras múltiples intentos fallidos (423 Locked bajo RN-U4).
3. **Control de acceso por roles RBAC (W-03):** intentos de acceso de `admin_tenant` a la gestión de empresas devuelven 403 Forbidden (`/problems/no-autorizado`), interceptados por el guard de Angular con notificación toast y bloqueo de acceso.
4. **Consulta y filtros de empresas (W-04):** listado de tenants por `admin_plataforma`, filtros por estado activo/inactivo y presencia de atributos requeridos (nombre, NIT, estado).
5. **Desactivación de tenant (W-05):** actualización de estado a inactivo (SCRUM-113) y confirmación de que sus usuarios no pueden iniciar sesión (RN-T1 / SCRUM-114).
6. **Estados de interfaz y concurrencia (W-06):** manejo de skeleton, estados vacíos y rechazo por conflicto de concurrencia optimista (409 Conflict con `/problems/conflicto-concurrencia`).
7. **Navegación dinámica (W-07):** adaptación del sidebar según el rol (`admin_tenant` no visualiza la opción de tenants).

### Ejecución

#### Simulación Local Preparatoria
Para correr las pruebas localmente con el servidor mock del gateway:
```bash
node tests/e2e/run-web-admin-e2e.js
```
*Nota:* Ejecución preparatoria en desarrollo contra `scrum-318-web-admin.simulacion.json`. La corrida formal contra el panel web desplegado en k3s (VM2) queda agendada para el pipeline de release.

#### Ejecución contra el Ambiente de QA en VM2
```bash
node tests/e2e/run-web-admin-e2e.js --remote
```

### Ejecución de Pruebas de Interfaz (Playwright)
La especificación de pruebas de interfaz en navegador se encuentra definida en `specs/web-admin.spec.ts`, modelando la sesión en `sessionStorage` con la clave `quickpatch.sesion` conforme a la arquitectura real de `apps/web/src/app/core/sesion.ts`. Su ejecución contra el navegador queda agendada para el entorno desplegado de QA una vez el panel web esté publicado en VM2. Para evitar que el runner de CI de `release/*` intente levantar un navegador headless sin el panel desplegado, el paquete se mantiene desacoplado del root de `tests/e2e/`.

### Evidencia de Validación de Contratos (Newman)
`evidencias/scrum-318-web-admin-2026-10-07.txt`: corrida local preparatoria ejecutada con **Newman** sobre la suite `scrum-318-web-admin.simulacion.json` contra el simulador de API del panel administrativo (`mock-admin-gateway.js`), con un resultado de **11 peticiones y 31 aserciones aprobadas sin fallos (100% Pass)**.

