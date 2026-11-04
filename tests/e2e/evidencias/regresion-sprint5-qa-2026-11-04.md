# Corrida de las colecciones del Sprint 5 y regresión contra QA (SCRUM-525)

Fecha: 2026-11-04. Responsable: Katherine Bravo (QA). Historia: SCRUM-524.

Este registro reúne en un solo lugar dónde está la evidencia de cada colección Newman vigente en `tests/e2e/`.
No es una corrida nueva. Apunta a corridas reales contra QA (`https://qa.quickpatch.internal`) del 4 de noviembre de 2026.

## 1. Fuentes

| Fuente | Qué es | Fecha |
|---|---|---|
| Workflow «Pruebas de sistema», corrida 41794907667 | GitHub Actions sobre `develop` (commit `d847126`, después del PR #247), job «E2E (Playwright y Newman)», paso «Newman (colecciones de API)», y job «Humo del flujo crítico» | 2026-11-04 07:49 UTC |
| Corridas con el runner (`tests/e2e/correr-colecciones-qa.js`) | Archivos `tests/e2e/evidencias/*-qa-2026-11-04.txt` del ensayo de demostración (PR #239) y de los PR #243 y #249 | 2026-11-04 |

https://github.com/ARQUI-202630/quickpatch/actions/runs/41794907667

En los dos casos, cada colección crea sus propios datos (usuarios con clave aleatoria). No usa usuarios fijos, y no se guardan claves ni tokens.

## 2. Resultado por colección

Las 27 colecciones de `tests/e2e/*.postman_collection.json` tienen evidencia del 4 de noviembre, y todas terminaron sin fallos.

| # | Colección | Corrida de CI 41794907667 (peticiones / aserciones) | Archivo de evidencia del 2026-11-04 (peticiones / aserciones) |
|---|---|---|---|
| 1 | `humo-flujo-critico` | 29 / 29 | `humo-flujo-critico-qa-2026-11-04.txt`: 27 / 29 |
| 2 | `quickpatch-mvp` | 43 / 61 | `quickpatch-mvp-qa-2026-11-04.txt`: 43 / 61 |
| 3 | `scrum-105-panel-operativo` | 29 / 35 | `scrum-105-panel-operativo-qa-2026-11-04.txt`: 29 / 35 |
| 4 | `scrum-108-aprobacion-rechazo` | 30 / 40 | (solo CI) |
| 5 | `scrum-111-suspension-tecnico` | 29 / 39 | (solo CI) |
| 6 | `scrum-117-pago` | 62 / 57 | `scrum-117-pago-qa-2026-11-04.txt`: 71 / 57 |
| 7 | `scrum-32-calificacion` | (no estaba en `develop` a esa hora) | `scrum-32-calificacion-qa-2026-11-04.txt`: 101 / 127 |
| 8 | `scrum-37-historial` | (no estaba en `develop` a esa hora) | `scrum-37-historial-qa-2026-11-04.txt`: 91 / 101 |
| 9 | `scrum-45-pagos-tecnico` (SCRUM-503) | 86 / 103 | `scrum-45-pagos-tecnico-qa-2026-11-04.txt`: 85 / 103 |
| 10 | `scrum-458-geocodificacion-buzon` | 35 / 44 | (solo CI) |
| 11 | `scrum-478-cancelacion` | 52 / 71 | (solo CI) |
| 12 | `scrum-483-chat` | 42 / 69 | `scrum-483-chat-qa-2026-11-04.txt`: 43 / 69 |
| 13 | `scrum-490-cotizacion` | 60 / 76 | `scrum-490-cotizacion-qa-2026-11-04.txt`: 60 / 76 |
| 14 | `scrum-495-comprobante` | 39 / 42 | `scrum-495-comprobante-qa-2026-11-04.txt`: 39 / 42 |
| 15 | `scrum-496-pago-empresa` | 51 / 59 | `scrum-496-pago-empresa-qa-2026-11-04.txt`: 51 / 59 |
| 16 | `scrum-511-tenant-desactivado` | 17 / 24 | `scrum-511-tenant-desactivado-qa-2026-11-04.txt`: 16 / 24 |
| 17 | `scrum-56-registro-tecnico` | 8 / 23 | (solo CI) |
| 18 | `scrum-600-fuera-de-bogota` | 21 / 62 | (solo CI) |
| 19 | `scrum-614-perfil` | (no estaba en `develop` a esa hora) | `scrum-614-perfil-qa-2026-11-04.txt`: 56 / 102 |
| 20 | `scrum-65-roles-y-tenants` | 9 / 23 | (solo CI) |
| 21 | `scrum-68-cuenta-corporativa` | 32 / 68 | `scrum-68-cuenta-corporativa-qa-2026-11-04.txt`: 32 / 68 |
| 22 | `scrum-75-solicitud-empresa` | 44 / 56 | (solo CI) |
| 23 | `scrum-78-motor-matching` | 21 / 43 | (solo CI) |
| 24 | `scrum-84-seguimiento-estado` | 37 / 42 | (solo CI) |
| 25 | `scrum-96-evidencia` | 47 / 71 | (solo CI) |
| 26 | `scrum-99-equipo-proveedor` | 25 / 43 | (solo CI) |
| 27 | `scrum-incremento-tecnico` | 42 / 61 | `scrum-incremento-tecnico-qa-2026-11-04.txt`: 42 / 61 |

Totales:
- Corrida de CI 41794907667: humo con 29 peticiones y 29 aserciones; job E2E con 23 colecciones, 878 peticiones y 1157 aserciones; 0 fallos.
- Archivos del 2026-11-04: 15 colecciones, 786 peticiones y 1014 aserciones; 0 fallos.

El número de peticiones de una misma colección puede variar un poco entre corridas. Eso pasa porque algunas colecciones repiten una consulta hasta que el evento llega (por ejemplo, la espera del pago o de la asignación). El número de aserciones no cambia.

## 3. Corridas anteriores del sprint

Las corridas 41515531669 y 41522853302 del 2 de noviembre, sobre `develop`, también terminaron en verde: 21 colecciones cada una, 771 y 775 peticiones, 1030 aserciones y 0 fallos.

## 4. Observaciones

- **Playwright:** el paso «Playwright (E2E-001 a E2E-012)» termina en verde, pero no ejecuta pruebas. El log dice «Todavía no hay pruebas de Playwright (tests/e2e/package.json)» y no se genera `tests/e2e/playwright-report`. Por eso este registro no da por probados E2E-001 a E2E-012.
- **k6:** la corrida no ejecutó k6. Ese job está apagado por defecto y se trata en SCRUM-526.
- **SCRUM-32 (calificación):** la primera corrida del 4 de noviembre encontró que ServiceRequest aceptaba `{"score":"5"}` con 201. Se corrigió en quickpatch-service-request#39 (`release/0.11.2`), y la corrida que queda en el archivo pasó sin fallos.
