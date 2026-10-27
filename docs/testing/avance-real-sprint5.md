# Avance real del producto — corte del 27 de octubre de 2026

**Historia:** SCRUM-559. **Tarea:** SCRUM-562 (cálculo y publicación del avance).
**Fecha de corte:** 27 de octubre de 2026, 17:00 (hora de Bogotá).
**Fuentes:**
- El inventario de 78 funcionalidades (`docs/testing/inventario-funcionalidades-por-usuario.md`, SCRUM-560).
- Los estados que llenó QA en SCRUM-561 (rama `feature/qa/scrum-561-inventario-funcionalidades`, commit `e1fe335`, todavía sin fusionar).
- Las evidencias de `tests/e2e/evidencias/` y `tests/security/evidencias/` en `develop`.
- Los PR fusionados hasta la fecha de corte.

## Cómo se calcula

Cada funcionalidad cae en una sola clase:

| Clase | Criterio |
|---|---|
| **Implementada y verificada** | Existe en el código y hay una evidencia en QA que **llama a esa funcionalidad**. La evidencia se revisó abriendo el archivo: no basta con que el archivo exista |
| **Implementada, pendiente de QA** | Existe en el código, pero no hay evidencia en QA que la ejerza. Incluye lo que solo se probó en local y lo que es solo de la interfaz (cerrar sesión, landing) sin prueba de interfaz en QA |
| **Parcial** | Una parte existe (por ejemplo, el backend sin pantalla, o el flujo sin su último paso) |
| **No implementada** | No hay código que la haga |

**Fórmula (SCRUM-559):**

```
avance = implementadas y verificadas / total de funcionalidades
```

Se calcula por tipo de usuario y global. Lo que corre con un simulador (la pasarela de pagos, ADR-009 modificado) cuenta como verificado y se marca aparte. Como segundo indicador se publica la **cobertura de implementación**:

```
cobertura de implementación = (verificadas + pendientes de QA) / total
```

## Resultado

| Tipo de usuario | Total | Verificadas | Pendientes de QA | Parciales | No implementadas | **Avance** | Cobertura de implementación |
|---|---|---|---|---|---|---|---|
| Visitante de la landing | 2 | 0 | 2 | 0 | 0 | **0.0%** | 100.0% |
| Cliente hogar | 14 | 10 | 1 | 1 | 2 | **71.4%** | 78.6% |
| Empresa cliente | 16 | 12 | 1 | 1 | 2 | **75.0%** | 81.3% |
| Técnico | 15 | 9 | 3 | 0 | 3 | **60.0%** | 80.0% |
| Proveedor | 9 | 5 | 1 | 0 | 3 | **55.6%** | 66.7% |
| Administrador del tenant | 9 | 6 | 2 | 1 | 0 | **66.7%** | 88.9% |
| Administrador de plataforma | 6 | 3 | 3 | 0 | 0 | **50.0%** | 100.0% |
| Transversal | 7 | 6 | 0 | 1 | 0 | **85.7%** | 85.7% |
| **Global** | **78** | **51** | **13** | **4** | **10** | **65.4%** | **82.1%** |

- **Avance global: 65.4%** (51 de 78). Dos de las 51 son con la pasarela simulada (C-12 y E-14); sin ellas, el avance es 62.8%.
- **Cobertura de implementación: 82.1%** (64 de 78). Es lo que llegaría a contar con solo correr en QA las pruebas que faltan, sin escribir funcionalidades nuevas.
- **Producción: 0 funcionalidades de usuario utilizables.**
  - El `main` de Identity, Catalog, ServiceRequest y Matching es del 8 de octubre, y Payments y Communication no están (Infraestructura 4.3, SCRUM-518).
  - El panel de producción es una página provisional.
  - El APK publicado apunta a QA (`v0.5.2-qa`).
  - Por eso, en esta medición la columna "Producción" de SCRUM-561 no cuenta para el avance.

## Clasificación por funcionalidad

| ID | Clase | Fuente que lo sostiene | Nota |
|---|---|---|---|
| V-01 | Pendiente de QA | — | `scrum-105` prueba el panel operativo por API, no la página de presentación |
| V-02 | Pendiente de QA | — | La descarga existe (SCRUM-628), pero no hay prueba guardada |
| C-01 | Verificada | `mvp-qa-sprint4-2026-10-18.txt` (`POST /v1/auth/register/client`) | QA citó `tenant-beta`, que no registra clientes |
| C-02 | Verificada | `mvp-qa-sprint4-2026-10-18.txt` | |
| C-03 | Pendiente de QA | — | Cerrar sesión es de la app; una colección de API no la prueba |
| C-04 | No implementada | — | SCRUM-609, contrato pendiente (SCRUM-610) |
| C-05 | No implementada | — | SCRUM-623 |
| C-06 | Verificada | `scrum-75-solicitud-empresa-qa-2026-10-22.txt` | |
| C-07 | Verificada | `scrum-84-seguimiento-estado-qa-2026-10-22.txt` | |
| C-08 | Verificada | `scrum-490-cotizacion-qa-2026-10-22.txt` | |
| C-09 | Verificada | `scrum-478-cancelacion-qa-2026-10-19.txt` | |
| C-10 | Verificada | `scrum-483-chat-qa-2026-10-22.txt` | |
| C-11 | Verificada | `scrum-458-geocodificacion-buzon-qa-2026-10-22.txt` | |
| C-12 | Verificada (simulada) | `scrum-117-pago-qa-2026-10-22.txt` | Pasarela simulada |
| C-13 | Verificada | `scrum-495-comprobante-qa-2026-10-22.txt` | |
| C-14 | Parcial | quickpatch-service-request#29 | Backend fusionado el 27 de octubre (SCRUM-85); faltan la pantalla (SCRUM-86) y QA (SCRUM-87) |
| E-01 | Verificada | `scrum-68-cuenta-corporativa-qa-2026-10-22.txt` | |
| E-02 | Verificada | `scrum-68-cuenta-corporativa-qa-2026-10-22.txt` | |
| E-03 | Verificada | `scrum-68-cuenta-corporativa-qa-2026-10-22.txt` (`POST /v1/auth/password/setup`) | |
| E-04 | Verificada | `mvp-qa-sprint4-2026-10-18.txt` | |
| E-05 | Pendiente de QA | — | Igual que C-03 |
| E-06 | No implementada | — | SCRUM-609 |
| E-07 | No implementada | — | SCRUM-623 |
| E-08 | Verificada | `scrum-75-solicitud-empresa-qa-2026-10-22.txt` | |
| E-09 | Verificada | `scrum-84-seguimiento-estado-qa-2026-10-22.txt` | Mismo endpoint que el cliente |
| E-10 | Verificada | `scrum-496-pago-empresa-qa-2026-10-27.txt` | Quien creó la solicitud de la empresa acepta la cotización |
| E-11 | Verificada | `scrum-478-cancelacion-qa-2026-10-19.txt` | Mismo endpoint que el cliente |
| E-12 | Verificada | `scrum-483-chat-qa-2026-10-22.txt` | |
| E-13 | Verificada | `scrum-458-geocodificacion-buzon-qa-2026-10-22.txt` | |
| E-14 | Verificada (simulada) | `scrum-496-pago-empresa-qa-2026-10-27.txt` | Pasarela simulada |
| E-15 | Verificada | `scrum-496-pago-empresa-qa-2026-10-27.txt` | |
| E-16 | Parcial | quickpatch-service-request#29 | Igual que C-14 |
| T-01 | Verificada | `scrum-56-registro-tecnico-qa-2026-10-22.txt` | |
| T-02 | Pendiente de QA | — | `scrum-99` no llama a la activación (`/v1/auth/password/setup`) |
| T-03 | Verificada | `mvp-qa-sprint4-2026-10-18.txt` | |
| T-04 | Pendiente de QA | — | Igual que C-03 |
| T-05 | No implementada | — | SCRUM-609 |
| T-06 | No implementada | — | SCRUM-623 |
| T-07 | Verificada | `scrum-incremento-tecnico-qa-2026-10-22.txt` (`PUT /availability` y `/coverage`) | |
| T-08 | Verificada | `scrum-78-qa-2026-10-22.txt` | |
| T-09 | Verificada | `scrum-incremento-tecnico-qa-2026-10-22.txt` | |
| T-10 | Verificada | `scrum-490-cotizacion-qa-2026-10-22.txt` | |
| T-11 | Verificada | `scrum-96-evidencia-qa-2026-10-22.txt` | |
| T-12 | Verificada | `scrum-483-chat-qa-2026-10-22.txt` | |
| T-13 | Verificada | `scrum-458-geocodificacion-buzon-qa-2026-10-22.txt` | |
| T-14 | Pendiente de QA | — | Ninguna evidencia llama a `GET /v1/technicians/me/service-requests`; QA citó `scrum-incremento-tecnico`, que no lo hace (SCRUM-102) |
| T-15 | No implementada | — | SCRUM-45 |
| P-01 | Verificada | `scrum-56-registro-tecnico-qa-2026-10-22.txt` | |
| P-02 | Verificada | `mvp-qa-sprint4-2026-10-18.txt` | |
| P-03 | Pendiente de QA | — | Igual que C-03 |
| P-04 | No implementada | — | SCRUM-609 |
| P-05 | No implementada | — | SCRUM-623 |
| P-06 | Verificada | `scrum-99-equipo-proveedor-qa-2026-10-22.txt` | |
| P-07 | Verificada | `scrum-99-equipo-proveedor-qa-2026-10-22.txt` | |
| P-08 | Verificada | `scrum-458-geocodificacion-buzon-qa-2026-10-22.txt` | |
| P-09 | No implementada | — | SCRUM-45 |
| A-01 | Verificada | `scrum-108-aprobacion-rechazo-qa-2026-10-22.txt` | Por API; el panel usa las mismas rutas |
| A-02 | Pendiente de QA | — | La activación solo está probada para usuarios de empresa, no para el administrador |
| A-03 | Pendiente de QA | — | Igual que C-03 |
| A-04 | Verificada | `scrum-105-panel-operativo-qa-2026-10-22.txt` | |
| A-05 | Verificada | `scrum-105-panel-operativo-qa-2026-10-22.txt` | |
| A-06 | Verificada | `scrum-478-cancelacion-qa-2026-10-19.txt` | Cancelación del `admin_tenant` |
| A-07 | Verificada | `scrum-108-aprobacion-rechazo-qa-2026-10-22.txt` | |
| A-08 | Verificada | `scrum-111-suspension-tecnico-qa-2026-10-22.txt` | |
| A-09 | Parcial | quickpatch-ranking#7, quickpatch-identity#26 | La reputación ya llega a Identity; falta exponerla en la API y en el panel (SCRUM-497, SCRUM-86) |
| AP-01 | Verificada | `scrum-105-panel-operativo-qa-2026-10-22.txt` | |
| AP-02 | Pendiente de QA | — | Igual que C-03 |
| AP-03 | Pendiente de QA | — | No hay ningún `POST /v1/platform/tenants` en las evidencias |
| AP-04 | Pendiente de QA | — | La activación y desactivación (`PATCH /v1/platform/tenants/{id}`) solo se probó en local; en QA la evidencia solo muestra 401 |
| AP-05 | Verificada | `scrum-105-panel-operativo-qa-2026-10-22.txt` | |
| AP-06 | Verificada | `scrum-105-panel-operativo-qa-2026-10-22.txt` | |
| X-01 | Verificada | `scrum-108`, `scrum-490`, `scrum-496` (404 entre tenants) | |
| X-02 | Verificada | `scrum-108-aprobacion-rechazo-qa-2026-10-22.txt` (403 por rol) | |
| X-03 | Verificada | `scrum-78-qa-2026-10-22.txt` | |
| X-04 | Verificada | Pipelines de cada repositorio (job de despliegue a QA en verde, SAD 2.2, RNF-07) | |
| X-05 | Parcial | `scrum-incremento-tecnico-qa-2026-10-22.txt` | El flujo crítico de RF-27 termina en la calificación, que aún no está en el E2E |
| X-06 | Verificada | `tests/security/evidencias/loki_qa_k3s.json` | |
| X-07 | Verificada | `tests/security/evidencias/tls-entrada-qa-2026-10-27.txt` | |

## Diferencias con lo que marcó SCRUM-561

1. **Columna Producción.** QA marcó como "Sí" casi todas las funcionalidades, pero en producción solo corre el `main` del 8 de octubre de cuatro servicios, sin panel real ni app de producción. Ninguna de esas filas está lista para producción.
2. **Pruebas que no prueban esa fila:**
   - V-01: la landing.
   - C-01: el registro; la evidencia correcta es `mvp-qa-sprint4`.
   - T-02, A-02 y AP-03: activación y alta de tenant.
   - AP-04: en QA solo hay un 401.
   - T-14: el historial.
   - C-03, E-05, T-04, P-03, A-03 y AP-02: cerrar sesión, que es de la interfaz.
3. **Calificación y reputación (C-14, E-16 y A-09):** pasan de "No" a "Parcial", porque el backend quedó fusionado el 27 de octubre (SCRUM-85 y SCRUM-498).

## Qué sube el avance en el Sprint 5

| Acción | Filas | Avance si se logra |
|---|---|---|
| Correr en QA lo que ya existe: activación, alta y desactivación de tenant, historial, y una prueba de interfaz de cerrar sesión y de la landing (Playwright o capturas guardadas) | 13 pendientes de QA | 82.1% |
| Terminar la calificación (pantalla y QA) y la reputación en el panel | C-14, E-16, A-09, X-05 | +5.1 puntos |
| Perfil y recuperación de contraseña (SCRUM-609 y SCRUM-623) | 8 | +10.3 puntos |
| Pagos recibidos (SCRUM-45) | T-15, P-09 | +2.6 puntos |

Con todo lo anterior, el avance llegaría al 100% de las 78 funcionalidades. La primera fila es la más barata: no requiere código nuevo.

## Uso en la planeación

La matriz se actualiza al cierre de cada sprint con el mismo método. El cálculo se repite contando las clases de la tabla de clasificación y dividiendo entre las filas de cada tipo de usuario.
