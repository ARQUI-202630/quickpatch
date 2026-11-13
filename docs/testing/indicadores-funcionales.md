# Indicadores funcionales de QUICKPATCH: fuente única (SCRUM-700)

**Código del documento:** `IND-FUNC-2026-11-12`
**Versión:** 1.0
**Fecha de corte:** 12 de noviembre de 2026, sobre `develop` (`ed3310d`)
**Responsable:** Katherine Bravo (`ka.bravo@javeriana.edu.co`), QA Lead
**Trazabilidad Jira:** subtarea SCRUM-700 de la historia SCRUM-699. La usan SCRUM-701 (informes y presentación), SCRUM-664 (escenarios) y SCRUM-695 (auditoría del TD).
**Cálculo reproducible:** `python scripts/calcular_indicadores_qa.py`. El script lee la tabla de la sección 3 y la matriz de 52 escenarios, y no tiene ninguna cifra escrita a mano.

---

## 1. Por qué existe este documento

En el Sprint 5 convivían tres conteos de funcionalidades:

- los 33 requisitos funcionales del SRS v5.6;
- las 78 funcionalidades por tipo de usuario de [`avance-real-sprint5.md`](avance-real-sprint5.md);
- las «37 funcionalidades» del Informe UAT de la Product Owner y de la presentación.

[`cifras-canonicas.md`](../architecture/cifras-canonicas.md) (SCRUM-691) dejó la unidad pendiente de esta tarea. Este documento fija la unidad, define los cuatro indicadores y los calcula. Las cifras del SAD, el TD, los informes, las estadísticas y la presentación salen de aquí.

## 2. Unidad y definición de los cuatro indicadores

**Unidad:** el requisito funcional (RF) vigente del SRS v5.6. Son **33**: RF-01 a RF-29 y RF-34 a RF-37.

- RF-30 a RF-33 se retiraron en el SRS v3.0, y su numeración no se reutiliza.
- RF-38 (recuperación de contraseña) y RF-39 (edición del perfil) están propuestos en el SRS 5.11, sección 7.6. No cuentan mientras no se aprueben.
- Las 4 extensiones (EXT-01 a EXT-04) que la PO pidió contar el 4 de noviembre se reportan aparte, en la sección 4, y no entran al denominador. Por eso «37» = 33 RF + 4 extensiones.
- Las 78 funcionalidades por usuario se quedan como desglose por rol, con su corte del 27 de octubre. No son una unidad de avance.

| Indicador | Un RF cuenta cuando… | No cuenta cuando… | Fuente del dato |
|---|---|---|---|
| **Definidas** | Tiene un ID vigente en el SRS v5.6 | Está retirado o solo propuesto | SRS v5.6, sección 5 |
| **Implementadas** | Su código está fusionado en `develop` del repositorio dueño y desplegado en QA (rama `release/*` vigente). Lo que corre con la pasarela simulada (ADR-009) cuenta, y se marca | Solo hay backend sin la pantalla que el RF exige, o el código no está desplegado en QA | `develop` de los repositorios; ramas `release/*` en QA |
| **Verificadas en QA** | Hay al menos una corrida contra QA desplegado que **llama a esa funcionalidad** y termina con 0 fallos. La corrida está guardada en `tests/` o es un run identificado de GitHub Actions | Solo hay pruebas locales o unitarias, o la evidencia no ejerce el RF | `tests/e2e/evidencias/`, `tests/security/evidencias/`, runs de `pruebas-sistema.yml` |
| **Aceptadas** | La Product Owner la marcó «Aceptado» en el Informe UAT oficial, y consta en el acta de UAT | La PO la rechazó o no la evaluó | [`informe-uat-oficial-po-2026-11-05.xlsx`](informe-uat-oficial-po-2026-11-05.xlsx), columna P; [`acta-uat-scrum-608.md`](acta-uat-scrum-608.md) (PR #272) |

Las observaciones no restan, pero quedan escritas en la tabla: pasarela simulada, prueba que no se repitió, o caso no probado. Un RF con observaciones sigue contando en su indicador, que es como lo aceptó la PO.

## 3. Estado por requisito funcional

`Sí` = cuenta en el indicador. La evidencia es la más reciente que ejerce el RF. Las rutas son relativas a la raíz del repositorio, y «run 41935076005» es la corrida de `pruebas-sistema.yml` del 4 de noviembre contra QA ([`regresion-sprint5-qa-2026-11-04.md`](../../tests/e2e/evidencias/regresion-sprint5-qa-2026-11-04.md)).

<!-- tabla-rf: la lee scripts/calcular_indicadores_qa.py; no cambiar las columnas -->
| RF | Requisito (SRS v5.6) | Prioridad | Definida | Implementada | Verificada en QA | Aceptada | Evidencia en QA | Observación |
|---|---|---|---|---|---|---|---|---|
| RF-01 | Registro de Cliente | Alta | Sí | Sí | Sí | Sí | `tests/e2e/evidencias/quickpatch-mvp-qa-2026-11-04.txt` (61 aserciones, 0 fallos) | — |
| RF-02 | Registro de Técnico/Proveedor con documentos | Alta | Sí | Sí | Sí | Sí | `tests/e2e/evidencias/scrum-56-registro-tecnico-qa-2026-10-22.txt` (23, 0 fallos); run 41935076005 | — |
| RF-03 | Inicio de sesión y bloqueo tras 5 intentos | Alta | Sí | Sí | Sí | Sí | `tests/e2e/evidencias/quickpatch-mvp-qa-2026-11-04.txt` (bloqueo con 423) | — |
| RF-04 | Aislamiento de datos por tenant | Alta | Sí | Sí | Sí | Sí | `tests/e2e/evidencias/scrum-68-cuenta-corporativa-qa-2026-11-04.txt` y demás colecciones del run 41935076005 (Beta recibe 404) | — |
| RF-05 | Acceso por rol y por canal | Alta | Sí | Sí | Sí | Sí | `tests/e2e/evidencias/scrum-105-panel-operativo-qa-2026-11-04.txt`; colección `scrum-65-roles-y-tenants` (run 41935076005) | — |
| RF-06 | Cuenta corporativa de Empresa | Alta | Sí | Sí | Sí | Sí | `tests/e2e/evidencias/scrum-68-cuenta-corporativa-qa-2026-11-04.txt` (68, 0 fallos) | — |
| RF-07 | Crear solicitud con ubicación en Bogotá | Alta | Sí | Sí | Sí | Sí | `tests/e2e/evidencias/scrum-458-geocodificacion-buzon-qa-2026-10-22.txt`; `tests/e2e/evidencias/scrum-600-fuera-de-bogota-qa-2026-10-28.txt` | — |
| RF-08 | Solicitud a nombre de la Empresa | Alta | Sí | Sí | Sí | Sí | `tests/e2e/evidencias/scrum-75-solicitud-empresa-qa-2026-10-22.txt` (56, 0 fallos) | — |
| RF-09 | Asignación automática de técnico | Alta | Sí | Sí | Sí | Sí | `tests/e2e/evidencias/scrum-78-qa-2026-10-22.txt` (43, 0 fallos) | — |
| RF-10 | Oferta al técnico con vencimiento de 3 min | Alta | Sí | Sí | Sí | Sí | `tests/e2e/evidencias/rf-10-vencimiento-oferta-qa-2026-11-05.md` (PR #269) | Aceptado con observaciones (UAT-004): no se probó el caso sin más técnicos |
| RF-11 | Estado de la solicitud en tiempo real | Alta | Sí | Sí | Sí | Sí | `tests/e2e/evidencias/scrum-84-seguimiento-estado-qa-2026-10-22.txt`; `tests/e2e/evidencias/scrum-478-aviso-tiempo-real-qa-2026-10-22.txt` | El aviso por WebSocket no se repitió en el Sprint 5 |
| RF-12 | Calificar el servicio tras el pago | Media | Sí | Sí | Sí | Sí | `tests/e2e/evidencias/scrum-639-calificacion-detalle-qa-2026-11-05.txt` (142, 0 fallos); `tests/e2e/evidencias/scrum-32-calificacion-qa-2026-11-04.txt` | — |
| RF-13 | Disponibilidad y zona de cobertura del técnico | Alta | Sí | Sí | Sí | Sí | `tests/e2e/evidencias/scrum-incremento-tecnico-qa-2026-11-04.txt`; `tests/e2e/evidencias/scrum-636-cobertura-localidades-qa-2026-10-28.txt` | — |
| RF-14 | Detalle de la solicitud asignada | Alta | Sí | Sí | Sí | Sí | `tests/e2e/evidencias/scrum-incremento-tecnico-qa-2026-11-04.txt` (DTL-001) | — |
| RF-15 | Completar con evidencia fotográfica | Alta | Sí | Sí | Sí | Sí | `tests/e2e/evidencias/scrum-96-evidencia-qa-2026-10-22.txt` (71, 0 fallos) | — |
| RF-16 | Equipo de técnicos del Proveedor | Media | Sí | Sí | Sí | Sí | `tests/e2e/evidencias/scrum-99-equipo-proveedor-qa-2026-10-22.txt` (43, 0 fallos) | — |
| RF-17 | Historial de solicitudes del técnico | Media | Sí | Sí | Sí | Sí | `tests/e2e/evidencias/scrum-37-historial-qa-2026-11-04.txt` (105, 0 fallos) | — |
| RF-18 | Panel de solicitudes activas | Alta | Sí | Sí | Sí | Sí | `tests/e2e/evidencias/scrum-105-panel-operativo-qa-2026-11-04.txt` (35, 0 fallos) | — |
| RF-19 | Aprobar o rechazar técnicos y proveedores | Alta | Sí | Sí | Sí | Sí | `tests/e2e/evidencias/scrum-108-aprobacion-rechazo-qa-2026-10-22.txt` (40, 0 fallos) | — |
| RF-20 | Suspender la cuenta de un técnico | Media | Sí | Sí | Sí | Sí | `tests/e2e/evidencias/scrum-111-suspension-tecnico-qa-2026-10-22.txt` (39, 0 fallos) | — |
| RF-21 | Activar y desactivar tenants | Media | Sí | Sí | Sí | Sí | `tests/e2e/evidencias/scrum-511-tenant-desactivado-qa-2026-11-04.txt` (24, 0 fallos) | — |
| RF-22 | Pago con tarjeta de la cotización | Alta | Sí | Sí | Sí | Sí | `tests/e2e/evidencias/scrum-117-pago-qa-2026-11-04.txt` (57, 0 fallos) | Pasarela simulada (ADR-009) |
| RF-23 | Pago a nombre de la cuenta corporativa | Alta | Sí | Sí | Sí | Sí | `tests/e2e/evidencias/scrum-496-pago-empresa-qa-2026-11-04.txt` (59, 0 fallos) | Pasarela simulada (ADR-009) |
| RF-24 | Comprobante automático | Alta | Sí | Sí | Sí | Sí | `tests/e2e/evidencias/scrum-495-comprobante-qa-2026-11-04.txt` (42, 0 fallos) | Sin validez fiscal (DR-03) |
| RF-25 | Pagos recibidos de Técnico y Proveedor | Media | Sí | Sí | Sí | Sí | `tests/e2e/evidencias/scrum-45-pagos-tecnico-qa-2026-11-04.txt` (111, 0 fallos) | — |
| RF-26 | Pipeline CI/CD con pruebas antes de desplegar | Alta | Sí | Sí | Sí | Sí | Run 41935076005 de `pruebas-sistema.yml`; [`evidencias-sprint4.md`](evidencias-sprint4.md), sección 1 | — |
| RF-27 | Prueba E2E automática del flujo crítico | Alta | Sí | Sí | Sí | Sí | `tests/e2e/evidencias/humo-flujo-critico-qa-2026-11-11.txt` (29, 0 fallos, hasta la calificación) | — |
| RF-28 | Logs con correlation-id y alertas de caída | Media | Sí | Sí | Sí | Sí | `tests/e2e/evidencias/rf-28-alerta-de-caida-y-logs-qa-2026-11-05.md` (PR #269) | — |
| RF-29 | TLS en tránsito y contraseñas con hash | Alta | Sí | Sí | Sí | Sí | `tests/security/evidencias/tls-ingress-qa-2026-10-27.txt`; `tests/e2e/evidencias/scrum-644-network-login-qa-2026-11-11.txt` | — |
| RF-34 | El técnico emite la cotización | Alta | Sí | Sí | Sí | Sí | `tests/e2e/evidencias/scrum-490-cotizacion-qa-2026-11-04.txt` (76, 0 fallos) | — |
| RF-35 | El cliente acepta o rechaza la cotización | Alta | Sí | Sí | Sí | Sí | `tests/e2e/evidencias/scrum-490-cotizacion-qa-2026-11-04.txt` (76, 0 fallos) | — |
| RF-36 | Cancelar la solicitud con motivo | Media | Sí | Sí | Sí | Sí | `tests/e2e/evidencias/scrum-478-cancelacion-qa-2026-10-19.txt` (63, 0 fallos) | — |
| RF-37 | Chat Cliente–Técnico en tiempo real | Media | Sí | Sí | Sí | Sí | `tests/e2e/evidencias/scrum-483-chat-qa-2026-11-11.txt` (69, 0 fallos) | — |
<!-- fin-tabla-rf -->

**Resultado (12 de noviembre de 2026):**

| Indicador | Cantidad | Porcentaje sobre 33 RF |
|---|---|---|
| Definidas | **33** | 100 % |
| Implementadas | **33** | 100 % (2 con la pasarela simulada: RF-22 y RF-23) |
| Verificadas en QA | **33** | 100 % |
| Aceptadas por la PO | **33** | 100 % (RF-10 con observaciones) |

De los 33 RF, 24 son de prioridad Alta y 9 de prioridad Media, y los 24 de prioridad Alta están aceptados. Ese es el dato que mide AC1-E2.

## 4. Extensiones fuera del SRS (se reportan aparte)

<!-- tabla-ext: la lee scripts/calcular_indicadores_qa.py -->
| ID | Funcionalidad | Relación con el SRS | Implementada | Verificada en QA | Aceptada | Evidencia en QA | Observación |
|---|---|---|---|---|---|---|---|
| EXT-01 | Editar el perfil propio | RF-39 propuesto (SRS 5.11, sección 7.6) | Sí | Sí | Sí | `tests/e2e/evidencias/scrum-614-perfil-qa-2026-11-04.txt` (102, 0 fallos) | — |
| EXT-02 | Botón de volver en todas las pantallas | Pedido del profesor (AC4) | Sí | Sí | Sí | `tests/e2e/evidencias/scrum-618-navegacion-capturas-qa-2026-11-04/` (23 capturas, PR #267) | — |
| EXT-03 | Descargar el APK desde la landing | Pedido del profesor | Sí | Sí | Sí | Release `v0.5.4-qa` de `quickpatch-mobile` | La descarga 302 → 200 desde la landing se verificó con `v0.5.1-qa` y no se repitió |
| EXT-04 | Recuperar la contraseña con enlace del administrador | RF-38 propuesto (SRS 5.11, sección 7.6) | Sí | Sí | Sí | `tests/e2e/evidencias/scrum-627-recuperacion-qa-2026-11-04.txt` (118, 0 fallos); `tests/e2e/evidencias/scrum-627-enlace-vencido-qa-2026-11-04.txt` | — |
<!-- fin-tabla-ext -->

Las 4 extensiones están implementadas, verificadas y aceptadas. Si el SRS aprueba RF-38 y RF-39, EXT-04 y EXT-01 pasan a la tabla de la sección 3 y la unidad queda en 35 RF.

## 5. Avance del producto

La fórmula es la del Informe UAT de la PO: 70 % funcional y 30 % calidad, un supuesto del equipo.

```
avance = 0,7 × (RF aceptadas / RF definidas) + 0,3 × (% de escenarios de calidad)
% escenarios = (Cumple × 1 + Parcial × 0,5) / 52        (fuente: matriz-escenarios-calidad-52.md)
```

| Corte | RF aceptadas | Escenarios (Cumple, Parcial, No cumple, No medido) | % escenarios | **Avance** | Estado |
|---|---|---|---|---|---|
| 12-nov-2026 (vigente) | 33 de 33 (100 %) | 35, 8, 3 y 6 | 75,00 % | **92,50 %** | Vigente. Es la cifra para la presentación final |
| 5-nov-2026 (Informe UAT de la PO, primera versión) | 37 de 37 ítems (33 RF + 4 EXT) | 34, 8, 4 y 6 | 73,08 % | 91,92 % | Histórico. Lo conserva el acta firmada (PR #272) |
| 5-nov-2026 (Informe UAT de la PO, segunda versión) | 37 de 37 ítems | 39, 7, 4 y 2 | 81,73 % | 94,52 % | **Retirado.** Contaba como Cumple AC4-E3, AC4-E4, AC4-E6, AC4-E8 y AC4-E9 sin medición ni evidencia, y eso va contra el criterio de la matriz |

Entre el 5 y el 12 de noviembre, el avance cambia solo por AC7-E5, que pasó de No cumple a Cumple el 11 de noviembre (SCRUM-657, PR #296). La parte funcional da 100 % con cualquiera de las dos unidades, 33 o 37. Lo único que cambia es el denominador.

## 6. Cómo se reproduce

```bash
python scripts/calcular_indicadores_qa.py              # imprime los indicadores, los escenarios y el avance
python scripts/calcular_indicadores_qa.py --verificar  # además busca cifras retiradas en docs/testing (sale con 1 si encuentra alguna)
```

Cuando cambie un RF o un escenario, se cambia primero la fila en este documento o en la matriz de 52, después se corre el script y, en el mismo PR, se actualizan los documentos que citan la cifra.

## 7. Control de versiones

| Versión | Fecha | Autor | Cambio |
|---|---|---|---|
| 1.0 | 12 de noviembre de 2026 | Katherine Bravo (QA Lead) | Primera versión (SCRUM-700). Fija la unidad en 33 RF, separa las 4 extensiones, define los cuatro indicadores y calcula el avance vigente (92,50 %) |
