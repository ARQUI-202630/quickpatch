# Evidencias del Sprint 4 en QA

**Historia:** SCRUM-449 (insumo de SCRUM-394, informe de pruebas, y SCRUM-429, presentación).
**Corte:** 20 de octubre de 2026.
**Ambiente:** QA. Entrada por el gateway de VM1 (`https://qa.quickpatch.internal`), k3s en VM2, PostgreSQL y Redis en VM5, Kafka y Garage en VM7.

Este documento reúne en un solo lugar las ejecuciones contra QA que respaldan el Sprint 4: pipelines, versiones desplegadas, pruebas de sistema, humo de los frontends, evidencias por historia y capturas. Todo lo citado se ejecutó contra QA, salvo donde se indica. No es el informe de pruebas: el dictamen de las compuertas y la matriz de defectos van en SCRUM-394 (subtarea SCRUM-398).

## 1. Versiones desplegadas y pipelines

Cada release corrió su CI/CD completo: lint o compilación, pruebas con cobertura, `quality-gate`, imagen en GHCR y despliegue en QA.

|Componente|Rama|Commit|Fecha|Run de GitHub Actions|
|---|---|---|---|---|
|Identity|`release/0.4.0`|`c56a2af`|2026-10-19|[39194216422](https://github.com/ARQUI-202630/quickpatch-identity/actions/runs/39194216422)|
|ServiceRequest|`release/0.4.0`|`0fbf79d`|2026-10-19|[39294353940](https://github.com/ARQUI-202630/quickpatch-service-request/actions/runs/39294353940)|
|Matching|`release/0.5.0`|`1f0b94f`|2026-10-19|[39294360938](https://github.com/ARQUI-202630/quickpatch-matching/actions/runs/39294360938)|
|Communication|`release/0.2.0`|`d48817f`|2026-10-19|[39320061607](https://github.com/ARQUI-202630/quickpatch-communication/actions/runs/39320061607)|
|Catalog|`release/0.3.0`|`7102d15`|2026-10-14|[38607521315](https://github.com/ARQUI-202630/quickpatch-catalog/actions/runs/38607521315)|
|Panel web|`release/0.4.0`|`aa3628f`|2026-10-19|[39325987842](https://github.com/ARQUI-202630/quickpatch-web/actions/runs/39325987842) (job «Panel en qa»)|
|App móvil|`release/0.4.1`|`fca06c3`|2026-10-20|[39357022109](https://github.com/ARQUI-202630/quickpatch-mobile/actions/runs/39357022109) (APK de QA)|

Contratos: `quickpatch-api-gateway` v0.10.0 y `quickpatch-kafka` v0.6.0. Su CI en `develop` está en verde ([gateway](https://github.com/ARQUI-202630/quickpatch-api-gateway/actions/runs/39364238956), [kafka](https://github.com/ARQUI-202630/quickpatch-kafka/actions/runs/39364187837)).

El primer despliegue del incremento, del 14 de octubre, con salud de los Deployments, rutas por el gateway y el flujo del técnico de punta a punta, está en `tests/e2e/evidencias/incremento-sprint4-qa-2026-10-14.txt`.

## 2. Accesos para la demostración

|Qué|Dónde|
|---|---|
|Panel web (administrador de la plataforma y del tenant)|`https://qa.quickpatch.internal`, con la VPN de la universidad y el certificado de la CA interna del laboratorio|
|Tenant Beta|`https://beta.qa.quickpatch.internal`|
|APK de QA (`release/0.4.1`, huella del certificado actual)|Artefacto `apk-qa` del run [39357022109](https://github.com/ARQUI-202630/quickpatch-mobile/actions/runs/39357022109/artifacts/12235294704), 25,9 MB. **Vence el 19 de noviembre de 2026.**|

Las cuentas de prueba no se escriben aquí. Las del administrador están en los secretos `QA_ADMIN_*` y `QA_PLATFORM_ADMIN_*` del repositorio.

## 3. Pruebas de sistema en QA

Workflow «Pruebas de sistema» (`.github/workflows/pruebas-sistema.yml`) en el runner de VM1. Última corrida completa, del 19 de octubre, sobre las versiones de la sección 1: [39322882186](https://github.com/ARQUI-202630/quickpatch/actions/runs/39322882186) (commit `dd05896`). Los tres jobs terminaron en verde.

### 3.1 E2E con Newman

|Colección|Peticiones|Aserciones|Fallidas|
|---|---|---|---|
|`quickpatch-mvp.postman_collection.json`|43|61|0|
|`scrum-478-cancelacion.postman_collection.json`|52|71|0|
|`scrum-65-roles-y-tenants.postman_collection.json`|9|23|0|

El job todavía no corre Playwright (no existe `tests/e2e/package.json`). El panel se prueba con el humo de la sección 4.

### 3.2 Carga con k6

|Prueba|VU|Duración|Peticiones|Fallidas|p95|Checks|
|---|---|---|---|---|---|---|
|`load-test-50vu.js`|50|2 min 30 s|5.738|0,00 %|64,5 ms (catálogo 29,7 ms, crear solicitud 77,1 ms)|99,90 % (11 de 2.868 creaciones por encima del umbral de p95; `tasa_errores` 0,19 %)|
|`stress-test-150vu.js`|150|4 min|38.916|0,00 %, sin 5xx|399,7 ms|100 %|

Las corridas de k6 dejaban solicitudes vivas en el tenant compartido: unas 237.000 al 19 de octubre. Esas solicitudes saturaron Matching y el outbox, y retrasaron los avisos en tiempo real.

- El 20 de octubre se limpiaron con `infrastructure/ansible/playbooks/limpiar-carga-qa.yml -e borrar=si` (quickpatch#120), con respaldo `pg_dump` en VM5.
- Desde quickpatch#121, cada solicitud que k6 crea se cancela.
- El job de carga ya no corre en las ejecuciones manuales salvo con `carga: true`.
- La próxima corrida de k6 debe hacerse con ese cambio para tener cifras sobre QA limpio.

### 3.3 Seguridad

- **OWASP ZAP baseline** contra `https://qa.quickpatch.internal`, 7 URL: `FAIL-NEW: 0`, `WARN-NEW: 4`, `IGNORE: 2`, `PASS: 55`. Las cuatro advertencias:
  - `Re-examine Cache-control Directives` [10015];
  - `X-Content-Type-Options Header Missing` [10021];
  - `Strict-Transport-Security Header Not Set` [10035];
  - `Modern Web Application` [10109].

  Las dos de encabezados se corrigen en el Nginx del gateway y quedan como riesgo abierto para el informe.
- **Escáner PCI-DSS** (`tests/security/pci_dss_scanner.py`) sobre los logs de QA: 5.000 líneas revisadas, 0 hallazgos. La revisión con consultas LogQL en Loki es la subtarea SCRUM-397.

## 4. Humo de los frontends (SCRUM-448)

Resultado completo en `tests/e2e/evidencias/humo-qa-2026-10-19/README.txt`.

- **Panel:** `tests/e2e/humo/humo-panel.spec.ts` con Playwright 1.48.2, en el workflow «Humo de los frontends en QA», run [39328587806](https://github.com/ARQUI-202630/quickpatch/actions/runs/39328587806). 3 de 3 pasan en 19 s: administrador de la plataforma en `/tenants`; administrador del tenant con los conteos, la lista y la cancelación de una solicitud; y un cliente rechazado en el panel.
- **App:** `integration_test/humo_qa_test.dart` en emulador Android 16 contra QA. 7 de 7 pasan en 15 s: inicio de sesión, categorías, «¿Es aquí?», solicitud creada, diálogo y solicitud cancelada.

## 5. Evidencias por historia

|Historia|Qué se probó en QA|Evidencia|
|---|---|---|
|SCRUM-388 (incremento del técnico)|Despliegue, salud, WebSocket por el gateway y el flujo del técnico: registro, verificación, cobertura, disponibilidad, oferta y aceptación|`tests/e2e/evidencias/incremento-sprint4-qa-2026-10-14.txt`|
|SCRUM-62 (tenant Beta)|Registro e inicio de sesión por el host Beta, `tenant_id` del token y aislamiento entre canales|`tests/e2e/evidencias/tenant-beta-qa-2026-10-15.txt`|
|SCRUM-472 / SCRUM-478 (cancelación)|Colección de cancelación con cliente, administradores y Matching; aviso en tiempo real en 950 ms (6/6) después de limpiar la carga|`tests/e2e/evidencias/scrum-478-cancelacion-qa-2026-10-19.txt`, runs [39318080663](https://github.com/ARQUI-202630/quickpatch/actions/runs/39318080663) y [39322882186](https://github.com/ARQUI-202630/quickpatch/actions/runs/39322882186)|
|SCRUM-448 (humo de los frontends)|Panel y app contra QA|`tests/e2e/evidencias/humo-qa-2026-10-19/`|
|SCRUM-486 a SCRUM-489 (cotización)|Backend y app terminados con pruebas unitarias, de integración y de widget; **todavía no están desplegados en QA**|Pendiente: SCRUM-490|

### 5.1 Corrección verificada: cierre 4002 del canal en tiempo real

El 14 de octubre, el canal `/api/v1/realtime` cortaba a los 10 s sin la trama de cierre que pide el contrato. Communication lo corrigió en SCRUM-469 (quickpatch-communication#9), que salió en `release/0.2.0`.

El 20 de octubre a las 14:27 UTC se probó contra QA: se abrió el canal (101 en 206 ms) sin enviar `auth`, y el servidor cerró con `4002 sin-autenticacion` a los 10,2 s.

## 6. Capturas

|Archivo|Qué muestra|Origen|
|---|---|---|
|`tests/e2e/evidencias/humo-qa-2026-10-19/1-tenants-plataforma.png`|Tenants del administrador de la plataforma|Playwright contra QA, 19 oct|
|`.../2-solicitudes-tenant.png`|Conteos y solicitudes del tenant|Playwright contra QA, 19 oct|
|`.../3-dialogo-cancelacion.png`|Diálogo de cancelación con motivo|Playwright contra QA, 19 oct|
|`.../4-solicitud-cancelada.png`|Fila «Cancelado»|Playwright contra QA, 19 oct|
|`tests/e2e/evidencias/movil/1-inicio-cliente.png` a `4-solicitud-creada.png`|Nueva solicitud en la app|7 oct, **antes del despliegue del Sprint 4**: no sirven como evidencia de QA|

Capturas que faltan para la presentación. Se toman en la app de QA (APK de la sección 2) y en el panel durante el ensayo:

1. Técnico: registro, pendiente de verificación y aprobación en el panel.
2. Técnico: cobertura en el mapa y disponibilidad.
3. Técnico: oferta con cuenta regresiva y aceptación; cliente con «Técnico asignado» en vivo.
4. Cliente: cancelación desde la app y aviso al técnico.
5. Cotización (cuando SCRUM-490 la despliegue): formulario del técnico con el total, y tarjeta del cliente con aceptar y rechazar.

## 7. Pendientes y riesgos para el informe

- **Cotización en QA (SCRUM-490):**
  - Falta desplegar ServiceRequest con la tabla `quotes`, el rol `service_request_scheduler` y Redis, Communication 0.3.0 y los topics de `quickpatch-kafka` v0.6.0.
  - Falta también sacar un APK con quickpatch-mobile#30.
  - Después se corre la colección de punta a punta.
- **k6 sobre QA limpio:** repetir la carga con quickpatch#121 y comparar con la sección 3.2.
- **Encabezados de seguridad del gateway** (HSTS y `X-Content-Type-Options`), advertidos por ZAP.
- **Loki y LogQL (SCRUM-397):** las consultas de la revisión PCI-DSS sobre Loki no están en esta evidencia.
- **APK descargable:** el artefacto de GitHub Actions vence el 19 de noviembre de 2026. Para la entrega conviene publicarlo como release de `quickpatch-mobile`.
