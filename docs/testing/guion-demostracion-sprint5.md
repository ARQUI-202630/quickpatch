# Guion de la demostración del incremento — Sprint 5

**Historia:** SCRUM-556 (presentación de la entrega del Sprint 5). **Tarea:** SCRUM-557. Las diapositivas son de SCRUM-558 (Jorge); este guion y sus evidencias son el insumo.
**Estado del guion:** versión del 27 de octubre de 2026, con el ensayo técnico contra QA de esa noche (sección "Ensayo"). Antes de presentar se repasa contra el estado final del sprint: los pasos marcados **[si llega]** solo se muestran si su historia está en Finalizado y tiene evidencia en QA.

## Reglas de la demostración

1. **Solo se muestra lo que corre en QA**, con la app instalada desde el APK publicado y el panel de `https://qa.quickpatch.internal`. Nada en local ni con datos simulados en la app.
2. **Datos:** las cuentas de demostración de `tests/datos-demo/` (dominio `demo.quickpatch.test`). Se cargan con `cargar-datos-demo.py --ambiente qa` el día anterior. Las contraseñas no se muestran en pantalla ni en las diapositivas.
3. **Lo simulado se dice en voz alta:** el pago usa la pasarela simulada (ADR-009 modificado) con las tarjetas de prueba, no un proveedor certificado.
4. **Plan B:** si la VPN o QA fallan, se muestran los videos grabados en el ensayo y las evidencias de `tests/e2e/evidencias/`. No se improvisa en otro ambiente.

## Qué hay en QA y desde dónde

| Qué | Dónde | Versión al 27 de octubre |
|---|---|---|
| Panel web y página de presentación | `https://qa.quickpatch.internal` (VPN de la universidad; el certificado es autofirmado, se acepta una vez en el navegador) | `develop` del panel, publicado por el gateway de QA (ADR-028) |
| App móvil | APK del release `v0.5.2-qa` de `quickpatch-mobile`, también desde el botón "Descargar" de la página de presentación | 0.5.2 |
| API (para el plan B) | `https://qa.quickpatch.internal/api/v1/...` | Identity 0.6.0, ServiceRequest 0.8.0, el resto según el último release a `develop` |
| Logs | Grafana en `grafana.quickpatch.internal` | — |

## Cuentas

| Papel en la demo | Cuenta | Dónde |
|---|---|---|
| Cliente hogar | `demo.cliente1@demo.quickpatch.test` | Teléfono 1 |
| Técnico | `demo.tecnico1@demo.quickpatch.test` (aprobado, `disponible`, con las 20 localidades) | Teléfono 2 |
| Empresa cliente | `demo.empresa@demo.quickpatch.test` (Empresa Demo S.A.S.) | Teléfono 1, después del cliente |
| Administrador del tenant y de plataforma | Las cuentas de QA del vault (`vault_identity_admins`); las escribe quien presenta | Navegador |

Las claves de las cuentas de demostración las fija quien carga los datos (`QP_DEMO_PASSWORD`) y se reparten por el canal del equipo, no por el repositorio.

## Preparación (el día anterior)

| Paso | Responsable | Cómo se verifica |
|---|---|---|
| Cargar los datos de demostración en QA | DevOps | Al repetir el script, todo sale como "ya existía" |
| Instalar el APK del último release en dos teléfonos o emuladores (cliente y técnico) | Frontend | La pantalla de inicio de sesión abre contra QA |
| Poner disponibles a los técnicos de demostración | DevOps | `disponible` en el panel |
| Revisar que QA tenga las versiones del cierre del sprint | DevOps | Releases y job de despliegue en verde |
| Repetir el ensayo técnico (sección "Ensayo") | QA o Juan Diego | Las nueve colecciones en verde |
| Grabar el video de respaldo de cada bloque | QA | Archivos en la carpeta compartida del equipo |

## Bloques y tiempos (unos 20 minutos)

### Bloque 1. Qué cambió desde el Sprint 4 (2 min) — Juan Diego
- Lo que observó el profesor el 24 de octubre y qué se hizo con cada punto: el gateway por ambiente (ADR-028), los diagramas C4 por componente y los dinámicos con escenario, la restricción geográfica (SRS 2.3.1), el mapa arquitectónico y la matriz de funcionalidades.
- El avance real, con su fórmula y su fecha de corte (`docs/testing/avance-real-sprint5.md`, SCRUM-559). Al 27 de octubre: **65.4%** de las 78 funcionalidades verificadas en QA y 82.1% implementadas. Se muestra con la tabla por tipo de usuario y se explica qué falta para subirlo; se actualiza con el corte final antes de presentar.

### Bloque 2. Entrada al producto (2 min)
1. Abrir `https://qa.quickpatch.internal`: la página de presentación (SCRUM-491).
2. Mostrar el botón de descarga del APK (SCRUM-628 y SCRUM-630).

### Bloque 3. Flujo crítico del cliente y del técnico (8 min)
Dos teléfonos en pantalla: `demo.cliente1` y `demo.tecnico1`.

1. **Login:** los dos inician sesión (RF-03). La app muestra el inicio según el rol.
2. **Solicitud:** el cliente crea una solicitud de plomería con una dirección de Bogotá (RF-07). Si sobra tiempo, se muestra que una dirección fuera de Bogotá se rechaza (RN-SR9).
3. **Matching:** al técnico le llega la oferta con la localidad, la distancia y la cuenta regresiva, sin la dirección (RF-09, RN-SR13), y la acepta (RF-10). El cliente ve el cambio de estado sin refrescar (RF-11, ADR-023) y su buzón de notificaciones (RIE-03).
4. **Cotización:** el técnico la emite (RF-34) y el cliente la acepta (RF-35).
5. **Chat:** un mensaje de ida y vuelta (RF-37, ADR-026).
6. **Ejecución:** el técnico inicia, sube la foto de evidencia y completa (RF-15).
7. **Pago:** el cliente paga con la tarjeta de prueba aprobada (RF-22, pasarela simulada) y abre el comprobante (RF-24). La solicitud pasa a `pagado`.
8. **[si llega] Calificación:** el cliente califica el servicio (RF-12, ADR-027) y la reputación del técnico se actualiza. Requiere las tres cosas: la pantalla de la app (SCRUM-86), los topics de la calificación en el Kafka de QA y Ranking desplegado (SCRUM-512). El backend de ServiceRequest ya está en QA (0.8.0). Si falta algo, se muestra el diagrama dinámico de la calificación (SDD, figura 27) y se explica.
9. **[si llega] Historial:** el técnico ve sus servicios atendidos con la calificación de cada uno (RF-17). La API ya la devuelve (SCRUM-100); falta mostrarla en la app (SCRUM-101). Sin eso, se muestra la lista de servicios del técnico como está hoy.

### Bloque 4. Empresa y proveedor (2 min)
1. Con `demo.empresa`: los usuarios autorizados de la empresa (RF-06) y una solicitud de la empresa (RF-08).
2. El pago de una solicitud de la empresa hecho por otro usuario de la empresa (RF-23, RN-P6). Si no da el tiempo, se muestra la evidencia `scrum-496-pago-empresa-qa-2026-10-28.txt`.
3. **Proveedor:** el equipo del proveedor con su enlace de invitación (RF-16). Si no hay una cuenta de proveedor en los datos de demostración, se muestra la evidencia `scrum-99-equipo-proveedor-qa-2026-10-22.txt`.

### Bloque 5. Panel web (3 min)
1. **Administrador del tenant:** el tablero y las solicitudes activas por estado (RF-18); la aprobación o el rechazo de un técnico con motivo (RF-19); la suspensión (RF-20).
2. **Administrador de plataforma:** el alta y la desactivación de un tenant (RF-21), y las solicitudes de todos los tenants.

### Bloque 6. Calidad y operación (3 min)
- Estadísticas de pruebas y defectos del sprint (`docs/testing/estadisticas-pruebas-sprint5.md`, SCRUM-601) y la matriz de los 52 escenarios (SCRUM-563).
- El ensayo técnico de la noche anterior: nueve colecciones contra QA, sin fallos (sección "Ensayo").
- Grafana con los logs de la corrida de la demostración, filtrados por `correlationId` (RF-28).
- Lo que todavía no está en producción (Documento de Infraestructura, 4.3) y su plan (SCRUM-518).

## Qué no se muestra

Estas funcionalidades no se demuestran en vivo aunque haya código, porque no están completas en QA. Si preguntan, se responde con la fila de la matriz.

| Funcionalidad | Por qué no | Qué existe |
|---|---|---|
| Editar el perfil propio (SCRUM-609) | No hay pantalla en la app ni en el panel (SCRUM-612 y SCRUM-613) | `PATCH /v1/users/me` en QA (identity 0.6.0) |
| Recuperar la contraseña (SCRUM-623) | Sin contrato ni backend todavía (SCRUM-624 y SCRUM-625) | Nada |
| Pagos recibidos del técnico y del proveedor (SCRUM-45) | Contrato en revisión (SCRUM-500) | Nada en el backend |
| Rechazo inmediato de un tenant inactivo (SCRUM-348) | Evento en diseño (SCRUM-508) | El token del tenant desactivado sigue sirviendo hasta que vence |
| La reputación en el panel (A-09) | Falta exponerla en la API y en el panel | Identity ya la guarda (SCRUM-498) |
| Producción | Corre el `main` del 8 de octubre de cuatro servicios | Plan en SCRUM-518 |
| **Calificar en QA antes de que existan sus topics** | Detendría la publicación de eventos de ServiceRequest | Ver contingencias |

## Contingencias

| Si pasa esto | Se hace esto |
|---|---|
| No hay VPN o QA no responde | Plan B: videos del ensayo y evidencias de `tests/e2e/evidencias/` |
| La oferta no le llega al técnico | Revisar que `demo.tecnico1` esté `disponible` y sin otra oferta pendiente (RN-M1). Si no se resuelve en un minuto, se usa `demo.tecnico2` |
| El estado no cambia solo en la app del cliente | La app consulta el detalle cada 30 s (ADR-023); se espera o se refresca y se explica |
| La tarjeta aprobada sale rechazada | Se verifica el número de prueba; el rechazo con la tarjeta de fondos insuficientes también es parte de la demo (AC9-E5) |
| No existen los topics de la calificación en QA | No se califica. Una calificación sin su topic detiene el Outbox de ServiceRequest; se muestra el diagrama dinámico (SDD, figura 27) |
| El navegador rechaza el certificado | Se acepta la excepción del certificado autofirmado; su huella está en `tests/security/evidencias/tls-entrada-qa-2026-10-27.txt` |

## Preguntas que conviene tener preparadas

| Pregunta probable | Respuesta corta y su fuente |
|---|---|
| ¿Por qué el pago es simulado? | ADR-009 modificado: el MVP usa un puerto `IPaymentProvider` y la pasarela certificada entra sin cambiar el contrato |
| ¿Qué pasa si se cae Ranking? | La calificación se guarda igual y la reputación se pone al día al volver (ADR-027, AC5-E3) |
| ¿Producción es igual a QA? | Todavía no: le faltan Payments, Communication y los topics del incremento (Infraestructura 4.3, SCRUM-518), y Ranking no está desplegado en ningún ambiente (SCRUM-512) |
| ¿Cómo se calculó el avance? | Matriz de funcionalidades por usuario (`docs/testing/inventario-funcionalidades-por-usuario.md`), con la fórmula de `docs/testing/avance-real-sprint5.md` |
| ¿Por qué solo Bogotá? | Regla de negocio y restricción de arquitectura (SRS 2.3.1, SAD R6); Sumapaz queda pendiente (P10) |
| ¿Cómo saben que lo de hoy funciona? | El ensayo técnico de la noche anterior contra QA, con sus evidencias |

## Ensayo

El criterio de la tarea es un ensayo completo antes de la presentación. Hay dos partes:

1. **Ensayo técnico (por API):** las colecciones de Newman recorren el flujo del guion contra QA. Lo puede repetir cualquiera con `node tests/e2e/correr-colecciones-qa.js <colecciones>` y las credenciales en el entorno; `QA_CA_CERT` apunta al certificado de la entrada TLS, para que Newman lo verifique.
2. **Ensayo con las apps:** el equipo hace la demo completa en los teléfonos y el navegador, con el tiempo medido. Es el que valida la narración, los tiempos y las contingencias.

### Ensayo técnico del 27 de octubre de 2026 (22:40 a 23:10, hora de Bogotá)

Corrido por Juan Diego contra `https://qa.quickpatch.internal`, con cuentas nuevas de clave aleatoria. Ninguna colección califica, porque los topics de la calificación aún no están en QA.

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

### Ensayo con las apps

| Fecha | Asistentes | Duración real | Qué falló | Ajuste |
|---|---|---|---|---|
| | | | | |
