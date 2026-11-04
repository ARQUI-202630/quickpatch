# Evidencia consolidada del despliegue en QA (SCRUM-517, historia SCRUM-512)

Fecha de corte: 2026-11-04. Responsable: Katherine Bravo (QA).

Este registro reúne en un solo lugar las versiones desplegadas, la salud del ambiente y las corridas de prueba
del Sprint 5. No reemplaza las evidencias originales: cada fila apunta al archivo o a la corrida de donde sale el dato.

## 1. Fuentes

- Comentarios de despliegue en SCRUM-512 (estado del 2026-11-02 y actualización del 2026-11-04).
- Medición de QA de DevOps del 2026-11-04 a las 21:17 UTC (solo lectura), publicada en la revisión del PR #255: imágenes, pods y lag de Kafka.
- Evidencias Newman en `tests/e2e/evidencias/` con fecha 2026-11-04 (ensayo de demostración, PR #239, y corridas de SCRUM-503, SCRUM-87, SCRUM-102 y SCRUM-614).
- Corridas de GitHub Actions «Pruebas de sistema» y «Humo frontends».
- Humo contra producción (SCRUM-523, PR #247).

## 2. Versiones desplegadas en QA (medidas el 2026-11-04 a las 21:17 UTC)

| Componente | Versión en QA | Imagen | Commit | Nota |
|---|---|---|---|---|
| identity | release/0.8.1 | `t-725ca2766944` | `db8a7a7` | Desplegada en QA el 2026-11-04 hacia las 05:32 UTC (antes, 0.8.0). Es la misma imagen que corre en producción desde ese día |
| service-request | release/0.11.2 | `t-ac1b1e017129` | `13fcc84` | Desplegada en QA el 2026-11-04 hacia las 13:25 UTC, con el arreglo de la calificación como texto (SCRUM-87, quickpatch-service-request#39). Producción corre la 0.11.1. Contrato 1.11.0 (api-gateway v0.21.0) |
| catalog | release/0.4.1 | `t-d736888c075f` | `4ee19af` | Corrige quickpatch-catalog#14 (outbox drenado) |
| matching | release/0.6.1 | `t-87db6e59ecba` | `c1b6013` | |
| payments | release/0.3.0 | `t-4df89e5d7de8` | `005e75e` | |
| communication | release/0.3.3 | `t-514c72ca0a9c` | `00247d2` | Probe con timeoutSeconds 3 |
| ranking | release/0.1.0 | `t-ea4bd70a1283` | `7a5ca65` | |
| web (panel) | release/0.5.5 | | | 0.5.4 el 2026-11-02 |
| mobile (APK) | v0.5.4-qa | | | v0.5.3-qa el 2026-11-02 |
| kafka (topics) | v0.10.0 | | | Incluye tenant.status-changed |

## 3. Salud del ambiente

Medición del 2026-11-04 a las 21:17 UTC:
- Los 7 servicios (catalog, communication, identity, matching, payments, ranking y service-request) están en 1/1 Running, con 0 reinicios.
- Kafka tiene 20 topics y 28 pares grupo-topic con lag 0 (`operar-kafka-grupos.yml`, solo lectura).

El 2026-11-02 se registró lo mismo en SCRUM-512: 7 pods en 1/1, 20 topics y lag 0. Ese día también:
- las migraciones se aplicaron con el init container, sin intervención manual;
- los datos de QA se limpiaron para la UAT (SCRUM-607).

## 4. Corridas de GitHub Actions

| Workflow | Rama o fecha | Run | Resultado |
|---|---|---|---|
| Pruebas de sistema | (2026-11-02) | 41515531669 | verde (smoke, ZAP + PCI-DSS, Playwright, Newman) |
| Pruebas de sistema | (2026-11-02) | 41522853302 | verde |
| Pruebas de sistema | develop (2026-11-04 07:49) | 41794907667 | verde |
| Humo frontends | develop | 41794903519 | verde |

## 5. Resultados Newman contra QA (2026-11-04)

Todas las corridas terminaron con código de salida 0. La hora es la de inicio que trae cada archivo, en UTC.
Las versiones de identity y service-request salen de comparar esa hora con los despliegues del 4 de noviembre:
- identity 0.8.1 hacia las 05:32;
- service-request 0.11.2 hacia las 13:25.
Los demás servicios no cambiaron de versión ese día.

| Evidencia | Inicio (UTC) | identity | service-request | Peticiones | Aserciones | Fallos |
|---|---|---|---|---|---|---|
| `scrum-490-cotizacion-qa-2026-11-04.txt` | 01:28 | 0.8.0 | anterior a 0.11.2 | 60 | 76 | 0 |
| `scrum-incremento-tecnico-qa-2026-11-04.txt` | 01:28 | 0.8.0 | anterior a 0.11.2 | 42 | 61 | 0 |
| `scrum-117-pago-qa-2026-11-04.txt` | 01:29 | 0.8.0 | anterior a 0.11.2 | 71 | 57 | 0 |
| `scrum-483-chat-qa-2026-11-04.txt` | 01:29 | 0.8.0 | anterior a 0.11.2 | 43 | 69 | 0 |
| `scrum-495-comprobante-qa-2026-11-04.txt` | 01:31 | 0.8.0 | anterior a 0.11.2 | 39 | 42 | 0 |
| `scrum-496-pago-empresa-qa-2026-11-04.txt` | 01:31 | 0.8.0 | anterior a 0.11.2 | 51 | 59 | 0 |
| `scrum-68-cuenta-corporativa-qa-2026-11-04.txt` | 01:31 | 0.8.0 | anterior a 0.11.2 | 32 | 68 | 0 |
| `humo-flujo-critico-qa-2026-11-04.txt` | 01:32 | 0.8.0 | anterior a 0.11.2 | 27 | 29 | 0 |
| `quickpatch-mvp-qa-2026-11-04.txt` | 01:36 | 0.8.0 | anterior a 0.11.2 | 43 | 61 | 0 |
| `scrum-105-panel-operativo-qa-2026-11-04.txt` | 01:36 | 0.8.0 | anterior a 0.11.2 | 29 | 35 | 0 |
| `scrum-511-tenant-desactivado-qa-2026-11-04.txt` | 01:37 | 0.8.0 | anterior a 0.11.2 | 16 | 24 | 0 |
| `scrum-45-pagos-tecnico-qa-2026-11-04.txt` | 03:13 | 0.8.0 | anterior a 0.11.2 | 85 | 103 | 0 |
| `scrum-614-perfil-qa-2026-11-04.txt` | 13:16 | 0.8.1 | anterior a 0.11.2 | 56 | 102 | 0 |
| `scrum-37-historial-qa-2026-11-04.txt` | 13:17 | 0.8.1 | anterior a 0.11.2 | 91 | 101 | 0 |
| `scrum-32-calificacion-qa-2026-11-04.txt` | 13:32 | 0.8.1 | 0.11.2 | 101 | 127 | 0 |
| **Total (15 colecciones)** | | | | **786** | **1014** | **0** |

La corrida de CI 41794907667 de «Pruebas de sistema» (07:49 UTC) usó identity 0.8.1 y una versión de service-request anterior a la 0.11.2.

## 6. Producción (SCRUM-523)

- `humo-flujo-critico-produccion-2026-11-04.txt`: 31 peticiones, 29 aserciones, 0 fallos.
- `humo-produccion-lectura-2026-11-04.txt`: 14/14 en verde; repetido después de desplegar service-request 0.11.1 (corrige el apagado de QuoteExpirer), de nuevo 14/14 y pod 1/1 sin reinicios.
- `limpieza-humo-produccion-2026-11-04.txt`: respaldo previo y borrado de los datos de prueba (quedan 2 administradores, 0 técnicos, 0 solicitudes y las 6 categorías base).
- `humo-flujo-critico-produccion-2026-11-04-intento1-fallido.txt`: se conserva sin retocar; documenta el error del corredor y el hallazgo de QuoteExpirer.

## 7. Pendientes conocidos

- service-request 0.11.2 está en QA, pero no en producción (allá corre la 0.11.1).
- La app móvil no tiene prueba automatizada; su verificación es manual (APK v0.5.4-qa).
- Las corridas de «Pruebas de sistema» cubren el panel web contra el gateway, no la app móvil.

## 8. Conclusión

El ambiente de QA del Sprint 5 está desplegado y sano, con 15 colecciones Newman (786 peticiones, 1014 aserciones)
y las corridas de CI en verde, sin fallos. Los pendientes de la sección 7 no bloquean esta evidencia y quedan registrados
para seguimiento.
