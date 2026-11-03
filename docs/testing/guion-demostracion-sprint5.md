# Guion de la demostración del incremento — Sprint 5

**Historia:** SCRUM-556 (presentación de la entrega del Sprint 5). **Tarea:** SCRUM-557. Las diapositivas son de SCRUM-558 (Jorge); este guion y sus evidencias son el insumo.
**Estado del guion:** versión del 3 de noviembre de 2026, revisada contra los despliegues de QA del 2 de noviembre y los PR fusionados hasta el 3. La primera versión es del 27 de octubre, con el ensayo técnico de esa noche (sección "Ensayo"). Los pasos marcados **[requiere APK 0.5.4]** dependen de publicar ese APK (sección "Preparación"). Lo demás ya corre en QA.

## Reglas de la demostración

1. **Solo se muestra lo que corre en QA**, con la app instalada desde el APK publicado y el panel de `https://qa.quickpatch.internal`. Nada en local ni con datos simulados en la app.
2. **Datos:** las cuentas de demostración de `tests/datos-demo/` (dominio `demo.quickpatch.test`), cargadas en QA el 2 de noviembre (`tests/datos-demo/evidencias/carga-qa-2026-11-02.txt`). Las contraseñas no se muestran en pantalla ni en las diapositivas.
3. **Lo simulado se dice en voz alta:** el pago usa la pasarela simulada (ADR-009 modificado) con las tarjetas de prueba, no un proveedor certificado.
4. **Plan B:** si la VPN o QA fallan, se muestran los videos grabados en el ensayo y las evidencias de `tests/e2e/evidencias/`. No se improvisa en otro ambiente.

## Qué hay en QA y desde dónde

Versiones desplegadas en QA por las ramas `release/*` del 2 de noviembre (SCRUM-512). Después de esa fecha, `develop` de los servicios solo sumó la actualización de los submódulos de contratos (SCRUM-547), que no cambia el comportamiento.

| Qué | Dónde | Versión en QA |
|---|---|---|
| Panel web y página de presentación | `https://qa.quickpatch.internal` (VPN de la universidad; el certificado es autofirmado, se acepta una vez en el navegador) | `release/0.5.4` del panel, publicado por el gateway de QA (ADR-028) |
| App móvil | APK del release `v0.5.3-qa` de `quickpatch-mobile`, también desde el botón "Descargar" de la página de presentación. **Para la demo hace falta el `v0.5.4-qa`** (sección "Preparación") | 0.5.3, con la edición del perfil (SCRUM-612). Sin la calificación (SCRUM-86) ni el historial (SCRUM-101), que entraron a `develop` el 3 de noviembre |
| Identity | API | `release/0.7.0`: perfil propio (SCRUM-611), reputación del técnico (SCRUM-498) y `tenant.status-changed` (SCRUM-509) |
| ServiceRequest | API | `release/0.11.0`: calificación (SCRUM-85), historial con la calificación (SCRUM-100) y `422 tenant-inactivo` (SCRUM-510) |
| Payments | API | `release/0.3.0`: pagos recibidos del técnico y del equipo del proveedor (SCRUM-501) |
| Communication, Matching, Catalog y Ranking | API y Kafka | `release/0.3.3`, `0.6.1`, `0.4.1` y `0.1.0` |
| Logs | Grafana en `grafana.quickpatch.internal` | — |

## Cuentas

| Papel en la demo | Cuenta | Dónde |
|---|---|---|
| Cliente hogar | `demo.cliente1@demo.quickpatch.test` | Teléfono 1 |
| Técnico | `demo.tecnico1@demo.quickpatch.test` (Plomería, aprobado, `disponible`, con las 20 localidades). De respaldo, `demo.tecnico2` | Teléfono 2 |
| Empresa cliente | `demo.empresa1@demo.quickpatch.test` (Inmobiliaria & Coworking Bogotá S.A.S.) | Teléfono 1, después del cliente |
| Proveedor | `demo.proveedor1@demo.quickpatch.test`, con su técnico `demo.tecnico.proveedor1` | Teléfono 2, después del técnico |
| Administrador del tenant y de plataforma | Las cuentas de QA del vault (`vault_identity_admins`); las escribe quien presenta | Navegador |

Las claves de las cuentas de demostración las fija quien carga los datos (`QP_DEMO_PASSWORD`) y se reparten por el canal del equipo, no por el repositorio. `demo.cliente1`, `demo.tecnico1` y `demo.tecnico2` existen desde el 26 de octubre con otros nombres («Cliente Demo Uno», «Técnico Demo Plomería»); en pantalla se ven así.

## Preparación (el día anterior)

| Paso | Responsable | Cómo se verifica |
|---|---|---|
| **Publicar el APK `v0.5.4-qa`:** rama `release/0.5.4` de `quickpatch-mobile` desde `develop`, que ya tiene la calificación (SCRUM-86) y el historial (SCRUM-101) | DevOps | El release `v0.5.4-qa` aparece como el último y el botón "Descargar" de la página baja ese APK |
| Volver a correr la carga de datos de demostración en QA | DevOps | Al repetir el script, todo sale como "ya existía" |
| Preparar un servicio ya pagado del técnico `demo.tecnico1`, sin calificar, para el historial si el flujo en vivo se corta antes del pago | QA | Con la colección `humo-flujo-critico` sin la carpeta de la calificación, o a mano |
| Instalar el APK en dos teléfonos o emuladores (cliente y técnico) | Frontend | La pantalla de inicio de sesión abre contra QA |
| Poner disponibles a los técnicos de demostración y dejarlos sin ofertas pendientes | DevOps | `disponible` en el panel |
| Repetir el ensayo técnico (sección "Ensayo") | QA o Juan Diego | Las colecciones en verde |
| Grabar el video de respaldo de cada bloque | QA | Archivos en la carpeta compartida del equipo |

## Bloques y tiempos (unos 20 minutos)

### Bloque 1. Qué cambió desde el Sprint 4 (2 min) — Juan Diego
- Lo que observó el profesor el 24 de octubre y qué se hizo con cada punto: el gateway por ambiente (ADR-028), los diagramas C4 por componente y los dinámicos con escenario (SDD V4), la restricción geográfica (SRS 2.3.1), el mapa arquitectónico y la matriz de funcionalidades.
- Las decisiones del sprint: la calificación por eventos con la reputación en Ranking (ADR-027) y el chat (ADR-026), los dos aceptados; el pago antes de la calificación en todo el ciclo de vida (SAD 2.46, SRS P2).
- El avance real, con su fórmula y su fecha de corte (`docs/testing/avance-real-sprint5.md`, SCRUM-559). El corte del 27 de octubre dio **65.4%** de las 78 funcionalidades verificadas en QA y 82.1% implementadas. **Se actualiza con el corte final antes de presentar**, porque desde entonces llegaron a QA la calificación, el historial, el perfil, los pagos recibidos y el rechazo del tenant inactivo.

### Bloque 2. Entrada al producto (2 min)
1. Abrir `https://qa.quickpatch.internal`: la página de presentación (SCRUM-491).
2. Mostrar el botón de descarga del APK (SCRUM-628 y SCRUM-630).

### Bloque 3. Flujo crítico del cliente y del técnico (9 min)
Dos teléfonos en pantalla: `demo.cliente1` y `demo.tecnico1`.

1. **Login:** los dos inician sesión (RF-03). La app muestra el inicio según el rol.
2. **Solicitud:** el cliente crea una solicitud de plomería con una dirección de Bogotá (RF-07). Si sobra tiempo, se muestra que una dirección fuera de Bogotá se rechaza (RN-SR9).
3. **Matching:** al técnico le llega la oferta con la localidad, la distancia y la cuenta regresiva, sin la dirección (RF-09, RN-SR13), y la acepta (RF-10). El cliente ve el cambio de estado sin refrescar (RF-11, ADR-023) y la campana del buzón de notificaciones (RIE-03).
4. **Cotización:** el técnico la emite (RF-34) y el cliente la acepta (RF-35).
5. **Chat:** un mensaje de ida y vuelta (RF-37, ADR-026).
6. **Ejecución:** el técnico inicia, sube la foto de evidencia y completa (RF-15).
7. **Pago:** el cliente paga con la tarjeta de prueba aprobada (RF-22, pasarela simulada) y abre el comprobante (RF-24). La solicitud pasa a `pagado`.
8. **Calificación [requiere APK 0.5.4]:** en el detalle de la solicitud pagada, el cliente da las estrellas y un comentario (RF-12, SCRUM-86) y ve «Tu calificación». ServiceRequest publica `service-request.rated` y Ranking actualiza la reputación del técnico (ADR-027). El backend ya está probado en QA: la prueba de humo del 30 de octubre calificó con 201 y rechazó la segunda calificación con 409 `ya-calificada`.
9. **Historial [requiere APK 0.5.4]:** el técnico abre Cuenta → Historial y ve el servicio recién calificado con sus estrellas, con los filtros Completados, Pagados y Cancelados (RF-17, SCRUM-101).
10. **Perfil:** el cliente abre Cuenta → Editar perfil, cambia el teléfono y lo ve guardado sin volver a iniciar sesión; el correo y el rol se ven con candado (SCRUM-612). Ya está en el APK 0.5.3.

Sin el APK 0.5.4, los pasos 8 y 9 se reemplazan por la evidencia de la prueba de humo (`humo-flujo-critico-qa-2026-10-30.txt`) y el diagrama dinámico de la calificación (SDD, figura 27). Se dice que la pantalla ya está en `develop` de la app.

### Bloque 4. Empresa y proveedor (2 min)
1. Con `demo.empresa1`: los usuarios autorizados de la empresa (RF-06) y una solicitud de la empresa (RF-08).
2. El pago de una solicitud de la empresa hecho por otro usuario de la empresa (RF-23, RN-P6). Si no da el tiempo, se muestra la evidencia `scrum-496-pago-empresa-qa-2026-10-28.txt`.
3. **Proveedor:** con `demo.proveedor1`, su equipo con `demo.tecnico.proveedor1` y el enlace de invitación para un técnico nuevo (RF-16).

### Bloque 5. Panel web (3 min)
1. **Administrador del tenant:** el tablero y las solicitudes activas por estado (RF-18); la aprobación o el rechazo de un técnico con motivo (RF-19); la suspensión (RF-20).
2. **Administrador de plataforma:** el alta y la desactivación de un tenant (RF-21), y las solicitudes de todos los tenants.
3. **Tenant inactivo (RN-T1, SCRUM-348):** al desactivar el tenant Beta, un usuario de Beta con su token todavía vigente ya no puede crear solicitudes: responde 422 `tenant-inactivo` en segundos, sin esperar a que venza el token. La app y el panel de la demo están en el tenant principal, que no se desactiva, así que esto se muestra con la colección `scrum-511-tenant-desactivado` en una terminal (unos 30 s) o con su evidencia `tenant-desactivado-qa-2026-11-02.txt`. La colección deja Beta activo al terminar.

### Bloque 6. Calidad y operación (2 min)
- Estadísticas de pruebas y defectos del sprint (`docs/testing/estadisticas-pruebas-sprint5.md`, SCRUM-601) y la matriz de los 52 escenarios (SCRUM-563).
- El ensayo técnico de la noche anterior contra QA, sin fallos (sección "Ensayo").
- Grafana con los logs de la corrida de la demostración, filtrados por `correlationId` (RF-28).
- Lo que todavía no está en producción y su plan (SCRUM-518).

## Qué no se muestra

Estas funcionalidades no se demuestran en vivo aunque haya código, porque no están completas en QA o no tienen pantalla. Si preguntan, se responde con la fila de la matriz.

| Funcionalidad | Por qué no | Qué existe |
|---|---|---|
| Pagos recibidos del técnico y del proveedor (SCRUM-45) | La pantalla de la app (SCRUM-502) no está hecha | `GET /v1/payments/received` en QA (Payments `release/0.3.0`), con el equipo del proveedor |
| Recuperar la contraseña (SCRUM-623) | El backend está en revisión (`quickpatch-identity#29`, SCRUM-625) y las pantallas (SCRUM-626) esperan ese PR | Contrato identity 1.10.0 y modelo en el DD 5.19 |
| Editar el perfil desde el panel (SCRUM-613) | El PR del panel no está fusionado | La edición desde la app (bloque 3, paso 10) |
| La calificación al volver a abrir el detalle | `GET /v1/service-requests/{id}` no devuelve la calificación hasta service-request 1.12.0 (SCRUM-637). La app muestra «Ya calificaste este servicio» sin las estrellas | La calificación en el historial del técnico (bloque 3, paso 9) |
| La reputación en el panel (A-09) | Falta exponerla en la API y en el panel | Identity ya la guarda (SCRUM-498) |
| Producción | La promoción del MVP sigue en curso (SCRUM-518: falta promover `release/*` a `main`, SCRUM-522, y la prueba de humo, SCRUM-523) | Bases, Secrets, Nominatim y respaldo de producción listos (SCRUM-519, 520 y 521) |

## Contingencias

| Si pasa esto | Se hace esto |
|---|---|
| No hay VPN o QA no responde | Plan B: videos del ensayo y evidencias de `tests/e2e/evidencias/`. Se dice que QA corre en las VMs del laboratorio y solo se alcanza con la VPN |
| Un usuario de la demo queda bloqueado por intentos fallidos (RN-U4) | Se cambia a la cuenta de respaldo del mismo papel (`demo.cliente2`, `demo.tecnico2`). El desbloqueo no se hace en vivo |
| No existe un dato de prueba (la cuenta o la categoría no aparece) | Se repite `cargar-datos-demo.py --ambiente qa`, que es idempotente y tarda menos de un minuto. Si no se puede, se pasa al bloque siguiente y se muestra la evidencia de la carga |
| La oferta no le llega al técnico | Revisar que `demo.tecnico1` esté `disponible` y sin otra oferta pendiente (RN-M1). Si no se resuelve en un minuto, se usa `demo.tecnico2` |
| El estado no cambia solo en la app del cliente | La app consulta el detalle cada 30 s (ADR-023); se espera o se refresca y se explica |
| La tarjeta aprobada sale rechazada | Se verifica el número de prueba; el rechazo con la tarjeta de fondos insuficientes también es parte de la demo (AC9-E5) |
| No se publicó el APK 0.5.4 | Los pasos 8 y 9 del bloque 3 se muestran con la evidencia de la prueba de humo y la figura 27 del SDD |
| Una funcionalidad sigue pendiente el día de la demo | No se muestra: se nombra con su fila de "Qué no se muestra" y su tarea en Jira |
| El navegador rechaza el certificado | Se acepta la excepción del certificado autofirmado; su huella está en `tests/security/evidencias/tls-entrada-qa-2026-10-27.txt` |

## Preguntas que conviene tener preparadas

| Pregunta probable | Respuesta corta y su fuente |
|---|---|
| ¿Por qué el pago es simulado? | ADR-009 modificado: el MVP usa un puerto `IPaymentProvider` y la pasarela certificada entra sin cambiar el contrato |
| ¿Qué pasa si se cae Ranking? | La calificación se guarda igual y la reputación se pone al día al volver (ADR-027, AC5-E3) |
| ¿Por qué se califica después de pagar? | Es el ciclo de vida acordado: `completado` → `pagado` → calificación (SRS RF-12, DD RN-R3, SAD 2.46 sección 7.4) |
| ¿Cómo se entera ServiceRequest de que un tenant se desactivó? | Por el evento `tenant.status-changed` de Identity y una réplica local, sin llamar a Identity (RN-T1, ADR-017) |
| ¿Producción es igual a QA? | Todavía no: falta promover las ramas `release/*` a `main` y la prueba de humo (SCRUM-522 y SCRUM-523, historia SCRUM-518) |
| ¿Cómo se calculó el avance? | Matriz de funcionalidades por usuario (`docs/testing/inventario-funcionalidades-por-usuario.md`), con la fórmula de `docs/testing/avance-real-sprint5.md` |
| ¿Por qué solo Bogotá? | Regla de negocio y restricción de arquitectura (SRS 2.3.1, SAD R6); Sumapaz queda pendiente (P10) |
| ¿Cómo saben que lo de hoy funciona? | El ensayo técnico de la noche anterior contra QA, con sus evidencias |

## Ensayo

El criterio de la tarea es un ensayo completo antes de la presentación. Hay dos partes:

1. **Ensayo técnico (por API):** las colecciones de Newman recorren el flujo del guion contra QA. Lo puede repetir cualquiera con `node tests/e2e/correr-colecciones-qa.js <colecciones>` y las credenciales en el entorno; `QA_CA_CERT` apunta al certificado de la entrada TLS, para que Newman lo verifique.
2. **Ensayo con las apps:** el equipo hace la demo completa en los teléfonos y el navegador, con el tiempo medido. Es el que valida la narración, los tiempos y las contingencias.

### Colecciones del ensayo técnico final

Además de las nueve del 27 de octubre, el ensayo final suma las dos que cubren lo nuevo del sprint:

| Bloque del guion | Colección | Qué agrega |
|---|---|---|
| 3.7 a 3.8 Pago y calificación | `humo-flujo-critico` | El flujo completo hasta la calificación (201) y la segunda calificación (409) |
| 5.3 Tenant inactivo | `scrum-511-tenant-desactivado` | El 422 `tenant-inactivo` con el mismo token y la reactivación |

No se lanza `pruebas-sistema.yml` completo para el ensayo: su carga con k6 crea unas 40.000 solicitudes en QA.

### Ensayo técnico del 27 de octubre de 2026 (22:40 a 23:10, hora de Bogotá)

Corrido por Juan Diego contra `https://qa.quickpatch.internal`, con cuentas nuevas de clave aleatoria. Ninguna colección califica, porque en ese momento los topics de la calificación aún no estaban en QA. Se crearon después con SCRUM-514, y la prueba de humo del 30 de octubre ya calificó en QA.

| Bloque del guion | Colección | Peticiones | Aserciones | Fallos | Evidencia |
|---|---|---|---|---|---|
| 3 (login, solicitud, matching, ejecución) y 5 | `quickpatch-mvp` | 43 | 61 | 0 | `quickpatch-mvp-qa-2026-10-28.txt` |
| 3 (técnico: oferta, servicios, evidencia) | `scrum-incremento-tecnico` | 42 | 61 | 0 | `scrum-incremento-tecnico-qa-2026-10-28.txt` |
| 3.4 Cotización | `scrum-490-cotizacion` | 59 | 76 | 0 | `scrum-490-cotizacion-qa-2026-10-28.txt` |
| 3.5 Chat | `scrum-483-chat` | 43 | 69 | 0 | `scrum-483-chat-qa-2026-10-28.txt` |
| 3.7 Pago aprobado y rechazado | `scrum-117-pago` | 60 | 57 | 0 | `scrum-117-pago-qa-2026-10-28.txt` |
| 3.7 Comprobante | `scrum-495-comprobante` | 39 | 42 | 0 | `scrum-495-comprobante-qa-2026-10-28.txt` |
| 4.1 Empresa y sus usuarios | `scrum-68-cuenta-corporativa` | 32 | 68 | 0 | `scrum-68-cuenta-corporativa-qa-2026-10-28.txt` |
| 4.2 Pago de la empresa | `scrum-496-pago-empresa` | 52 | 59 | 0 | `scrum-496-pago-empresa-qa-2026-10-28.txt` |
| 5 Panel operativo | `scrum-105-panel-operativo` | 29 | 35 | 0 | `scrum-105-panel-operativo-qa-2026-10-28.txt` |
| **Total** | 9 colecciones | **399** | **528** | **0** | `tests/e2e/evidencias/` |

Las evidencias llevan la fecha UTC del inicio de la corrida (28 de octubre). El primer intento falló por completo con "self-signed certificate": el script no le pasaba a Newman el certificado de la entrada TLS de QA. Se corrigió con `QA_CA_CERT` y se repitió todo.

### Otras corridas contra QA usadas por el guion

| Fecha | Qué | Resultado | Evidencia |
|---|---|---|---|
| 30 de octubre de 2026 | Prueba de humo del flujo crítico, hasta la calificación | 30 peticiones, 29 aserciones, 0 fallos | `humo-flujo-critico-qa-2026-10-30.txt` |
| 2 de noviembre de 2026 | Tenant desactivado (SCRUM-511) | 0 verificaciones fallidas | `tenant-desactivado-qa-2026-11-02.txt` |
| 2 de noviembre de 2026 | Carga de los datos de demostración | 0 con error | `tests/datos-demo/evidencias/carga-qa-2026-11-02.txt` |

### Ensayo con las apps

| Fecha | Asistentes | Duración real | Qué falló | Ajuste |
|---|---|---|---|---|
| | | | | |
