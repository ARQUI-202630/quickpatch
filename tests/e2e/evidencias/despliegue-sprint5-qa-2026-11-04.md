# Evidencia consolidada del despliegue en QA (SCRUM-517, historia SCRUM-512)

Fecha de corte: 2026-11-04. Responsable: Katherine Bravo (QA).

Este registro reúne en un solo lugar las versiones desplegadas, la salud del ambiente y las corridas de prueba
del Sprint 5. No reemplaza las evidencias originales: cada fila apunta al archivo o a la corrida de donde sale el dato.

## 1. Fuentes

- Comentarios de despliegue en SCRUM-512 (estado del 2026-11-02 y actualización del 2026-11-04).
- Evidencias Newman en `tests/e2e/evidencias/` con fecha 2026-11-04 (ensayo de demostración, PR #239, y corridas de SCRUM-503, SCRUM-87, SCRUM-102 y SCRUM-614).
- Corridas de GitHub Actions «Pruebas de sistema» y «Humo frontends».
- Humo contra producción (SCRUM-523, PR #247).

## 2. Versiones desplegadas en QA

| Componente | Versión | Nota |
|---|---|---|
| identity | release/0.8.0 | 0.7.0 el 2026-11-02; 0.8.1 pendiente (ver sección 7) |
| service-request | 0.11.0 | contrato 1.11.0 publicado en api-gateway v0.21.0 |
| payments | 0.3.0 | |
| communication | 0.3.3 | probe con timeoutSeconds 3 |
| matching | 0.6.1 | |
| catalog | release/0.4.1 | corrige quickpatch-catalog#14 (outbox drenado) |
| ranking | 0.1.0 | |
| web (panel) | release/0.5.5 | 0.5.4 el 2026-11-02 |
| mobile (APK) | v0.5.4-qa | v0.5.3-qa el 2026-11-02 |
| kafka (topics) | v0.10.0 | incluye tenant.status-changed |

## 3. Salud del ambiente

- 7 pods de servicio (catalog, communication, identity, matching, payments, ranking, service-request) en 1/1 Running, 0 reinicios.
- Migraciones aplicadas por el init container, sin intervención manual.
- Kafka: 20 topics; lag 0 en los 28 pares grupo-topic.
- Datos de QA limpiados para la UAT (SCRUM-607).

## 4. Corridas de GitHub Actions

| Workflow | Rama o fecha | Run | Resultado |
|---|---|---|---|
| Pruebas de sistema | (2026-11-02) | 41515531669 | verde (smoke, ZAP + PCI-DSS, Playwright, Newman) |
| Pruebas de sistema | (2026-11-02) | 41522853302 | verde |
| Pruebas de sistema | develop (2026-11-04 07:49) | 41794907667 | verde |
| Humo frontends | develop | 41794903519 | verde |

## 5. Resultados Newman contra QA (2026-11-04)

Todas las corridas terminaron con código de salida 0.

| Evidencia | Peticiones | Aserciones | Fallos |
|---|---|---|---|
| `humo-flujo-critico-qa-2026-11-04.txt` | 27 | 29 | 0 |
| `quickpatch-mvp-qa-2026-11-04.txt` | 43 | 61 | 0 |
| `scrum-105-panel-operativo-qa-2026-11-04.txt` | 29 | 35 | 0 |
| `scrum-117-pago-qa-2026-11-04.txt` | 71 | 57 | 0 |
| `scrum-32-calificacion-qa-2026-11-04.txt` | 101 | 127 | 0 |
| `scrum-37-historial-qa-2026-11-04.txt` | 91 | 101 | 0 |
| `scrum-45-pagos-tecnico-qa-2026-11-04.txt` | 85 | 103 | 0 |
| `scrum-483-chat-qa-2026-11-04.txt` | 43 | 69 | 0 |
| `scrum-490-cotizacion-qa-2026-11-04.txt` | 60 | 76 | 0 |
| `scrum-495-comprobante-qa-2026-11-04.txt` | 39 | 42 | 0 |
| `scrum-496-pago-empresa-qa-2026-11-04.txt` | 51 | 59 | 0 |
| `scrum-511-tenant-desactivado-qa-2026-11-04.txt` | 16 | 24 | 0 |
| `scrum-614-perfil-qa-2026-11-04.txt` | 56 | 102 | 0 |
| `scrum-68-cuenta-corporativa-qa-2026-11-04.txt` | 32 | 68 | 0 |
| `scrum-incremento-tecnico-qa-2026-11-04.txt` | 42 | 61 | 0 |
| **Total (15 colecciones)** | **786** | **1014** | **0** |

## 6. Producción (SCRUM-523)

- `humo-flujo-critico-produccion-2026-11-04.txt`: 31 peticiones, 29 aserciones, 0 fallos.
- `humo-produccion-lectura-2026-11-04.txt`: 14/14 en verde; repetido después de desplegar service-request 0.11.1 (corrige el apagado de QuoteExpirer), de nuevo 14/14 y pod 1/1 sin reinicios.
- `limpieza-humo-produccion-2026-11-04.txt`: respaldo previo y borrado de los datos de prueba (quedan 2 administradores, 0 técnicos, 0 solicitudes y las 6 categorías base).
- `humo-flujo-critico-produccion-2026-11-04-intento1-fallido.txt`: se conserva sin retocar; documenta el error del corredor y el hallazgo de QuoteExpirer.

## 7. Pendientes conocidos

- identity 0.8.1 (identity#34, ajuste de Ingress) aún no desplegada en QA.
- La app móvil no tiene prueba automatizada; su verificación es manual (APK v0.5.4-qa).
- Las corridas de «Pruebas de sistema» cubren el panel web contra el gateway, no la app móvil.

## 8. Conclusión

El ambiente de QA del Sprint 5 está desplegado y sano, con 15 colecciones Newman (786 peticiones, 1014 aserciones)
y las corridas de CI en verde, sin fallos. Los pendientes de la sección 7 no bloquean esta evidencia y quedan registrados
para seguimiento.
