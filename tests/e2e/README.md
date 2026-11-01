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

## Prueba de humo del flujo crítico (SCRUM-504, historia SCRUM-47)

`humo-flujo-critico.postman_collection.json` se genera con `python tests/e2e/generar-humo-flujo-critico.py` y reutiliza los pasos de las colecciones de SCRUM-490, SCRUM-96 y SCRUM-117. Es un recorrido único, sin casos negativos (RF-27, RNF-08):

1. **Preparación:** categoría propia, técnico aprobado con cobertura en toda Bogotá y disponible, y un cliente, con una clave aleatoria que no se guarda.
2. **Solicitud y asignación:** el cliente crea la solicitud, el técnico ve la oferta y la acepta.
3. **Cotización:** el técnico cotiza 185.000 y el cliente acepta.
4. **Ejecución con foto:** el técnico inicia, sube la foto y completa.
5. **Pago y comprobante:** Payments crea el pago pendiente, el cliente paga con la tarjeta simulada aprobada, la solicitud pasa a `pagado` y el comprobante coincide con el pago.
6. **Calificación:** el cliente califica con 5 (201) y una segunda calificación responde 409 `ya-calificada`.
7. **Limpieza:** suspende al técnico y desactiva la categoría. La API no borra usuarios ni solicitudes; los datos que crea llevan el sufijo de la corrida en el correo y se pueden filtrar en la base.

Falla si el recorrido pasa de 5 minutos (la última petición lo comprueba). Con el reporter `cli` no imprime credenciales ni tokens.

**En el pipeline:** el job «Humo del flujo crítico» de `pruebas-sistema.yml` la corre en cada `release/*` y a mano, y falla sin correr nada si faltan `QA_ADMIN_EMAIL` y `QA_ADMIN_PASSWORD` (sin ellos la colección omitiría todos sus pasos y saldría en verde). El job de carga espera a que pase. La compuerta de producción (`compuerta-qa`, SCRUM-415) exige que la última corrida de `pruebas-sistema.yml` haya terminado en éxito después de que la versión llegó a QA, así que un fallo del humo bloquea la promoción. El bucle de Newman del job E2E la omite para no correrla dos veces.

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

## Pago con la pasarela simulada de punta a punta (SCRUM-117)

`scrum-117-pago.postman_collection.json` la genera `generar-scrum117-pago.py`, que reutiliza los pasos de la colección de SCRUM-96 hasta dejar la solicitud en `completado`. Contratos: `payments.v1.yaml` 1.0.0 y la pasarela simulada del ADR-009 modificado. Los tokens `tok_sim_aprobada_…`, `tok_sim_rechazada_…` y `tok_sim_error_…` son los que genera el tokenizador de la app con las tres tarjetas de prueba; la colección nunca envía números de tarjeta, salvo el caso negativo que comprueba que el backend los rechaza.

1. **Pago pendiente y accesos:** el cliente ve el pago `pendiente` de 185.000 cuando Payments consume `service-request.completed`; el técnico recibe 403; otro cliente y el cliente de Beta, 404 (RLS); el número de tarjeta en lugar del token y un campo desconocido dan 400.
2. **Rechazo y pasarela sin respuesta:** la tarjeta sin fondos responde 200 `rechazado` con `fondos_insuficientes` y la solicitud sigue en `completado` (RN-SR5); la pasarela sin respuesta da 502 y un pago inmediato, 409 `pago-en-curso`; la conciliación (cada 30 s) lo cierra como `rechazado` con `pasarela_sin_respuesta` (AC9-E5).
3. **Pago aprobado:** 200 `aprobado` con `invoiceId`; ServiceRequest pasa la solicitud a `pagado` al consumir `payment.approved`; pagar otra vez da 409 `ya-pagado`.

Necesita a Payments desplegado en QA, ServiceRequest con el consumidor de `payment.*` y los topics de quickpatch-kafka v0.9.0. Igual que las demás: `adminEmail` y `adminPassword` desde el entorno y salida con `--reporters cli` en un `.txt`.

**Evidencia:** `evidencias/scrum-117-pago-qa-2026-10-22.txt`, contra QA el 22 de octubre de 2026: 69 peticiones y 57 aserciones, sin fallos.

## Comprobante del pago de punta a punta (SCRUM-495)

`scrum-495-comprobante.postman_collection.json` la genera `generar-scrum495-comprobante.py`, que reutiliza los pasos de SCRUM-117 hasta el servicio completado. Contrato: `payments.v1.yaml` 1.1.0 (`GET /v1/payments/{id}/invoice`). El comprobante no tiene validez fiscal (SRS DR-03).

1. **Pago aprobado con NIT:** el cliente paga con `tok_sim_aprobada_…` y factura a nombre de una empresa con NIT.
2. **Comprobante:** el pagador lo ve en JSON (contrato `Invoice`, NIT en `payer`, `fiscalValidity = false`) y lo descarga en PDF (`Accept: application/pdf`, adjunto con el número del comprobante). El administrador del tenant también lo ve. Un `Accept` que no es JSON ni PDF da 406.
3. **Accesos:** el técnico recibe 403; otro cliente, el cliente de Beta (RLS) y un pago inexistente, 404.

Necesita a Payments con el comprobante desplegado en QA (quickpatch-payments#8). Igual que las demás: `adminEmail` y `adminPassword` desde el entorno y salida con `--reporters cli` en un `.txt`.

## Panel operativo y geocodificación con el buzón (SCRUM-105 y SCRUM-458)

`generar-scrum105-458.py` genera dos colecciones con la preparación de SCRUM-490 y SCRUM-96:

- `scrum-105-panel-operativo.postman_collection.json` (RF-18, SCRUM-38): el administrador del tenant ve el resumen por estado y la lista de su tenant. La solicitud de la prueba aparece sin dirección ni ubicación y suma a `createdToday`. El cliente, el técnico y el cliente de Beta reciben 403, y el administrador del tenant recibe 403 en la vista de plataforma. Con `platformAdminEmail`, la vista de plataforma solo trae conteos por tenant.
- `scrum-458-geocodificacion-buzon.postman_collection.json` (ADR-024):
  - **Geocodificación:** `location-preview` con una dirección de Bogotá y con una inexistente (422 `direccion-no-encontrada`), y la solicitud creada solo con la dirección.
  - **Buzón:** `solicitud-creada` para el cliente y `oferta-recibida` para el técnico. Otro cliente, el administrador y el cliente de Beta no las ven y no pueden marcarlas como leídas (404). Marcar como leída es idempotente.
  - El caso del geocodificador sin respuesta no se provoca en QA: lo cubren las pruebas de ServiceRequest.

**Evidencia de SCRUM-458:** `evidencias/scrum-458-geocodificacion-buzon-qa-2026-10-22.txt`, contra QA el 22 de octubre de 2026 con Communication 0.3.1: 34 peticiones y 44 aserciones, sin fallos. La primera corrida, con la 0.3.0, dio 43 de 44: «mismo readAt» fallaba porque la primera respuesta de `POST /v1/notifications/{id}/read` llevaba 7 decimales y las siguientes 6 (quickpatch-communication#17).

## Dirección fuera de Bogotá (SCRUM-600)

`scrum-600-fuera-de-bogota.postman_collection.json` prueba contra QA la restricción geográfica de la SCRUM-598 (R6 del SAD, RN-SR9 del DD, SRS 2.3.1). Se genera con `python tests/e2e/generar-scrum600-fuera-de-bogota.py`. No necesita al administrador: el cliente se registra solo y usa la primera categoría del catálogo. Se puede correr sin secretos:

```bash
docker run --rm -v "$PWD/tests/e2e:/etc/newman" postman/newman:6-alpine run scrum-600-fuera-de-bogota.postman_collection.json \
  --insecure --env-var baseUrl=https://qa.quickpatch.internal --reporters cli --color off
```

1. **Lo que cumple:** la vista previa rechaza con 422 `ubicacion-fuera-de-cobertura` una dirección escrita de Cali, Soacha, Chía, Villavicencio y El Poblado (Medellín), y con 422 `direccion-no-encontrada` la que no tiene coincidencia. Crear solo con la dirección de Cali o de Villavicencio también da 422. Un punto de GPS en Soacha, Medellín, Cali, Tunja y Chía da 422 `ubicacion-fuera-de-cobertura`. Una dirección de Bogotá sí se ubica (control). Ningún caso crea una solicitud.
2. **Límite documentado (carpeta 4, SRS 2.3.1):** el geocodificador empareja por el nombre de la calle e ignora la ciudad escrita, así que una calle de Medellín, Bucaramanga o Tunja que también existe en Bogotá se ubica en Bogotá. Lo mitiga la confirmación del pin en la app (ADR-024).

La primera corrida encontró otros dos casos. Crear solo con la dirección no repetía el rechazo de la vista previa: Cali y Villavicencio daban 201 con un punto en Soacha o al norte de Bogotá. Además, un GPS en Soacha (4,5794; -74,2168) creaba la solicitud porque cae dentro del rectángulo de RN-SR9. SCRUM-636 los corrigió: al crear, el punto también debe estar en una de las 20 localidades. Esos casos pasaron a las carpetas 2 y 3 con 422.

**Evidencia:** `evidencias/scrum-600-fuera-de-bogota-qa-2026-10-28.txt`, contra QA el 28 de octubre de 2026: 24 peticiones y 59 aserciones, sin fallos, con el resumen de los hallazgos al inicio. Es anterior a SCRUM-636. La repetición con la corrección en QA es `evidencias/scrum-636-cobertura-localidades-qa-2026-10-28.txt`: 21 peticiones y 62 aserciones, sin fallos.

## Cuenta corporativa de punta a punta (SCRUM-68)

`scrum-68-cuenta-corporativa.postman_collection.json` (RF-06, SCRUM-26) la genera `generar-scrum68-cuenta-corporativa.py`. Contrato: `identity.v1.yaml` 1.8.0. **No necesita al administrador**: todas las cuentas se registran por el canal con correo, NIT y clave generados en la corrida.

1. **Registro:** la empresa y su primer usuario quedan en el tenant del canal. El perfil y el token traen `companyId` y `company_id`. Responde 409 si el NIT o el correo se repiten, y 400 por campo (`company.nit`, `user.password`…) con datos inválidos.
2. **Otro usuario con invitación:**
   - El primer usuario lo agrega. Sin usar la invitación no puede entrar (401); con ella define su contraseña (204), y el mismo enlace no sirve dos veces (400).
   - Al entrar, su token tiene la misma empresa y los dos usuarios aparecen activos.
   - Nadie recibe invitación para un usuario que ya definió su contraseña (409), así nadie toma la cuenta de otro.
3. **Aislamiento:**
   - Otra empresa del mismo tenant solo ve a su usuario y recibe 404 con usuarios ajenos.
   - El cliente hogar recibe 403 y su token no trae `company_id`. Sin token, 401.
   - El mismo NIT se registra en el tenant Beta como otra cuenta, que no ve ni toca los usuarios de Alfa (404, RLS).

Se verificó contra Identity local (PostgreSQL 16 con las migraciones y los roles). Las 61 aserciones del tenant del canal pasan; las del tenant Beta solo aplican en QA, porque el Nginx de VM1 elige el tenant por el host. Necesita quickpatch-identity#24 desplegado: migración `CuentaCorporativa`, `aplicar-roles-db.yml` y la ruta `/v1/companies` del Ingress.

## Solicitud de empresa de punta a punta (SCRUM-75)

`scrum-75-solicitud-empresa.postman_collection.json` (RF-08, SCRUM-28) la genera `generar-scrum75-solicitud-empresa.py` con la preparación de SCRUM-490 (categoría propia y técnico aprobado). Contratos: `service-request.v1.yaml` 1.9.0 e `identity.v1.yaml` 1.8.0.

1. **Empresa y usuarios:** se registra una empresa, agrega a un colega que define su contraseña con la invitación, y se registra otra empresa.
2. **Crear:** la empresa crea la solicitud con su sede (`clientType` empresa, `companyId` del token, sede sin espacios). Una sede de un carácter y la sede de un cliente hogar responden 400.
3. **Mismo flujo de matching:** el técnico recibe la oferta, la acepta, la solicitud queda asignada y el técnico ve la sede.
4. **Quién la ve (RN-SR14):**
   - El colega la ve en el detalle y en la lista de la empresa, sin dirección en la lista.
   - Otra empresa, un cliente hogar y el cliente de Beta reciben 404.
   - El administrador la ve en su lista como de empresa.
5. **Cerrar:** el colega no la cancela (404), quien la creó sí, y el técnico queda libre.

Necesita en QA a Identity con quickpatch-identity#24, a ServiceRequest con quickpatch-service-request#27 (migración `SolicitudDeEmpresa`) y a Matching. Igual que las demás: `adminEmail` y `adminPassword` desde el entorno.

## Chat de la solicitud de punta a punta (SCRUM-483)

`scrum-483-chat.postman_collection.json` (RF-37, SCRUM-473, ADR-026) la genera `generar-scrum483-chat.py` con la preparación y la asignación de SCRUM-490. Contrato: `communication.v1.yaml` 1.3.0 (`GET` y `POST /v1/service-requests/{id}/messages`). Communication conoce a los participantes por `service-request.status-changed`, así que las consultas del historial reintentan hasta que llega la réplica.

1. **Chat abierto:** con la solicitud asignada, el cliente ve el chat vacío y con `writable = true`.
2. **Conversación:** el cliente escribe (se le quitan los espacios de los extremos) y el técnico responde. Los dos ven el mismo historial, del más reciente al más antiguo, y la página 2 de tamaño 1 trae el primero.
3. **Validación y acceso:**
   - 400 con un texto vacío o de 1.001 caracteres, con campos de más (`authorId`) o con `size=500`.
   - 401 sin token y 403 para el administrador del tenant.
   - 404 para otro cliente, otro técnico y el cliente de Beta (RLS).
4. **Solo lectura (RN-CH2):** al cancelar, el historial se sigue leyendo con `writable = false`, y escribir da 409 `chat-cerrado` al cliente y al técnico.

`scrum-483-chat-tiempo-real.mjs` cubre la entrega en tiempo real, que Newman no puede probar. Arma su propia solicitud asignada y conecta al cliente y al técnico a `/v1/realtime`, como dos dispositivos. Cada uno escribe por REST, y al otro le debe llegar la trama `chat.message` con el mismo mensaje en menos de 15 s. Al final cancela la solicitud, suspende al técnico y desactiva la categoría, aunque algo haya fallado. Usa Node 22 o superior y las mismas variables de entorno del administrador:

```powershell
$env:NODE_TLS_REJECT_UNAUTHORIZED = '0'; node tests/e2e/scrum-483-chat-tiempo-real.mjs > tests/e2e/evidencias/scrum-483-chat-tiempo-real-qa-<fecha>.txt
```

Necesita a Communication con el chat desplegado en QA (quickpatch-communication#16): migración `ChatDeLaSolicitud`, `aplicar-roles-db.yml` y el `IngressRoute` `communication-chat`.

**Evidencia:** `evidencias/scrum-483-chat-qa-2026-10-22.txt` (43 peticiones y 69 aserciones, sin fallos) y `evidencias/scrum-483-chat-tiempo-real-qa-2026-10-22.txt` (23 de 23 pasos), contra QA el 22 de octubre de 2026 con Communication 0.3.1.

## Correr colecciones contra QA y guardar la evidencia

`correr-colecciones-qa.js` corre una o varias colecciones contra QA y guarda la salida de Newman (reporter cli, sin colores) en `evidencias/<coleccion>-qa-<fecha>.txt`. Las claves se leen del entorno y nunca quedan en la evidencia; el script también reemplaza cualquier aparición de la clave por `***`.

```powershell
# En tu propia terminal; las claves no van en el repositorio ni en un chat.
$env:QA_ADMIN_EMAIL = '...'; $env:QA_ADMIN_PASSWORD = '...'
# Opcional, para la vista de plataforma de SCRUM-105:
$env:QA_PLATFORM_ADMIN_EMAIL = '...'; $env:QA_PLATFORM_ADMIN_PASSWORD = '...'
node tests/e2e/correr-colecciones-qa.js scrum-490-cotizacion scrum-96-evidencia scrum-105-panel-operativo scrum-458-geocodificacion-buzon
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

---

## Suite de Registro de Técnicos y Aislamiento Multi-Tenant (SCRUM-56, SCRUM-62)

Pruebas de sistema preparatorias y de release para el registro y gestión de técnicos (SCRUM-56) y la verificación del aislamiento multi-tenant lógico (SCRUM-62):

1. **SCRUM-56 (Registro y Perfil de Técnico):**
   - **Colección:** `scrum-56-registro-tecnico.postman_collection.json` (ejecutada en CI por `.github/workflows/pruebas-sistema.yml`).
   - Semilla dinámica: consulta `GET /api/v1/catalog/categories` para usar un `specialtyId` existente en el catálogo del tenant sin IDs quemados.
   - Generación dinámica de documento (`CC-{{timestamp}}`) y correo (`tecnico-{{timestamp}}@quickpatch.test`).
   - Verificación de rechazo con 409 Conflict ante duplicación real de documento (`documento-registrado`) y correo (`correo-registrado`).
   - Validación de formato: 400 Bad Request ante payload incompleto o clave corta.
   - Autenticación y consulta de `/api/v1/users/me` verificando rol `tecnico` y `verificationStatus: "pendiente"` (RN-U1).
   - Control RBAC: rechazo con 403 Forbidden cuando el técnico intenta crear solicitudes de servicio.

2. **SCRUM-62 (Aislamiento Multi-Tenant Lógico):**
   - **Archivo:** `scrum-62-aislamiento-tenant.simulacion.json` (sufijo `.simulacion.json` para no ejecutarse en el runner de CI de QA mientras se opera en monotenant `quickpatch-api-gateway#13`).
   - Valida el rechazo de acceso cruzado entre tenants (Tenant Alfa vs Tenant Beta) en usuarios, solicitudes y catálogo.

### Ejecución Local

```bash
node tests/e2e/run-scrum-56-62.js
```

### Evidencia
- `evidencias/scrum-56-62-local-2026-10-14.txt`: 24/24 aserciones aprobadas en SCRUM-56 y 11/11 en SCRUM-62 (100% Pass).

---

## Suite de Incremento Técnico: Disponibilidad, Ofertas y Detalle Asignado (SCRUM-81, SCRUM-90, SCRUM-93)

Suite automatizada de pruebas de sistema que valida el flujo operativo del técnico en el Sprint 4 bajo los contratos `matching.v1.yaml` (1.0.0) y `service-request.v1.yaml` (1.1.0):

1. **SCRUM-90 (Disponibilidad y Cobertura Geográfica — Matching Service / HU SCRUM-33):**
   - Catálogo de 20 localidades oficiales de Bogotá (SDP/IDECA) ordenadas por código (COV-001).
   - Consulta y actualización de disponibilidad entre `disponible` y `no_disponible` (AVA-001, AVA-002), activando `SearchResumer` (RN-M10).
   - Bloqueo de cambio manual (409 Conflict con Problem Details `transicion-invalida`) cuando el técnico se encuentra en servicio activo (`ocupado`, RN-M6) (AVA-003).
   - Configuración de cobertura multi-localidad con validación en PostGIS y RLS (COV-002, COV-003).
   - Rechazo de códigos inexistentes (400 Bad Request) (COV-004), sin token (401) (AVA-004) y acceso cliente denegado (403) (AVA-005).

2. **SCRUM-81 (Aceptación y Rechazo de Ofertas de Asignación — Matching Service / HU SCRUM-30):**
   - Consulta de ofertas pendientes: expone localidad y distancia estimada, pero oculta la dirección exacta hasta la asignación efectiva (RN-SR13) (OFF-001).
   - Aceptación atómica: en una sola transacción la oferta pasa a `aceptado`, el técnico a `ocupado` (RN-M6), la solicitud a `asignado` y se publica `matching.technician-assigned` por el Transactional Outbox (OFF-002).
   - Control de conflictos: 409 Conflict (`oferta-no-disponible`) ante oferta ya respondida (OFF-003) o vencida por tiempo límite de `OfferExpirer` (RN-M8) (OFF-004).
   - Protección contra doble asignación: 409 Conflict (`tecnico-no-disponible`) si el técnico ya no está disponible al aceptar (RN-M7) (OFF-005).
   - Rechazo sin penalización: 200 OK (`rechazado`) y reasignación automática al siguiente candidato con `MatchingEngine.offerNext` (RN-M3, R12) (OFF-006).
   - Control RBAC: rechazo con 403 Forbidden para rol cliente (OFF-007).

3. **SCRUM-93 (Detalle de Solicitud para Técnico Asignado — ServiceRequest Service / HU SCRUM-34):**
   - Acceso al detalle completo: técnico asignado visualiza dirección exacta y datos de contacto del cliente (nombre y teléfono) resueltos mediante consulta interna por lote a Identity (RN-SR13) (DTL-001).
   - Restricción de acceso previo: 403 Forbidden (`solicitud-no-asignada`) si el técnico intenta consultar antes de estar asignado (`buscando_tecnico`) (DTL-002).
   - Confidencialidad: 404 Not Found cuando un técnico no asignado o de otro tenant intenta acceder (DTL-003, DTL-004).
   - Visibilidad cliente: el cliente dueño ve la solicitud con `client: null` y el bloque `technician` poblado tras la asignación (DTL-005).

### Ejecución

```bash
# Simulación preparatoria local (Newman + Mock Gateway)
node tests/e2e/run-scrum-incremento-tecnico.js

# Contra el entorno desplegado de QA (VM2)
node tests/e2e/run-scrum-incremento-tecnico.js --remote
```

### Evidencia
- `evidencias/scrum-81-90-93-local-2026-10-17.txt`: 24 peticiones ejecutadas, 63 aserciones aprobadas sin fallos (100% Pass).



