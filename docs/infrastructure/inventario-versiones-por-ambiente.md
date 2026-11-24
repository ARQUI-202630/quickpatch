# Inventario de versiones por ambiente y traza release → QA → producción

| Campo | Valor |
|---|---|
| Historias | SCRUM-670 (subtareas SCRUM-671 y SCRUM-672) |
| Fecha de corte | 23 de noviembre de 2026 |
| Fuente | Corridas de GitHub Actions de cada repositorio: último job de despliegue exitoso por ambiente |
| Documento relacionado | [INFRASTRUCTURE.md](INFRASTRUCTURE.md), secciones 4.3 y 6.2 |

## 1. Cómo se obtuvo

Cada repositorio despliega solo desde su pipeline (Documento de Infraestructura, 6.2): un push a `release/*` despliega en QA con el job **Despliegue en qa**, y un push a `main` despliega en producción con **Despliegue en produccion**, que exige la aprobación del ambiente `produccion`. Los dos jobs hacen `kubectl set image` y esperan `kubectl rollout status`: si el pod no llega a `Ready`, el job falla y deshace el cambio (`rollout undo`). Por eso el último job exitoso de cada ambiente dice qué versión corre allí.

La consulta se hizo con `gh run list` y `gh run view` sobre los 11 repositorios desplegables. La versión de producción sale del mensaje del commit de `main` («Merge pull request #N from …/release/x.y.z»).

Las imágenes llevan como etiqueta el hash de su contenido (`t-<árbol>`, sección 6.1), no el número de versión. Por eso la versión se lee del pipeline y no del nombre de la imagen.

**Pendiente de este inventario:** la salida de `kubectl get deploy -n quickpatch -o wide` en VM2 y VM3, que confirma la imagen en el clúster. Desde el equipo de desarrollo no hay acceso SSH ni `kubeconfig`: la toma Sebastián (DevOps) y se agrega como anexo.

## 2. Inventario al 23 de noviembre de 2026

| Componente | QA (VM2) | Desplegado en QA | Producción (VM3) | Desplegado en producción |
|---|---|---|---|---|
| Identity | 0.10.5 (`6631e7f`) | [23-nov](https://github.com/ARQUI-202630/quickpatch-identity/actions/runs/45316891282) | 0.8.1 (`e8208bd`) | [4-nov](https://github.com/ARQUI-202630/quickpatch-identity/actions/runs/41782130389) |
| Actors | 0.2.0 (`5c85eb6`); Deployment `actors`; roles aplicados y reinicio el 23 de noviembre | [23-nov](https://github.com/ARQUI-202630/quickpatch-actors/actions/runs/45274256368) | 0.2.0 (`5c85eb6`), misma imagen `t-dfd6da88c157`; roles aplicados y reinicio el 24 de noviembre | [24-nov](https://github.com/ARQUI-202630/quickpatch-actors/actions/runs/45333645185) |
| Catalog | 0.4.4 (`6345700`) | [12-nov](https://github.com/ARQUI-202630/quickpatch-catalog/actions/runs/43137979426) | 0.4.1 (`7f0049e`) | [4-nov](https://github.com/ARQUI-202630/quickpatch-catalog/actions/runs/41783794405) |
| ServiceRequest | 0.12.4 (`04391e4`) | [23-nov](https://github.com/ARQUI-202630/quickpatch-service-request/actions/runs/45317630297) | 0.11.2 (`28536b6`) | [4-nov](https://github.com/ARQUI-202630/quickpatch-service-request/actions/runs/41937038241) |
| Matching | 0.6.2 (`8e6450c`) | [11-nov](https://github.com/ARQUI-202630/quickpatch-matching/actions/runs/43021330188) | 0.6.1 (`f1504d4`) | [4-nov](https://github.com/ARQUI-202630/quickpatch-matching/actions/runs/41785365995) |
| Ranking | 0.1.3 (`1679652`) | [12-nov](https://github.com/ARQUI-202630/quickpatch-ranking/actions/runs/43139423581) | 0.1.0 (`4fdb02e`) | [4-nov](https://github.com/ARQUI-202630/quickpatch-ranking/actions/runs/41787397479) |
| Payments | 0.3.4 (`a665f4f`) | [23-nov](https://github.com/ARQUI-202630/quickpatch-payments/actions/runs/45318314188) | 0.3.0 (`6d09d89`) | [4-nov](https://github.com/ARQUI-202630/quickpatch-payments/actions/runs/41786075940) |
| Communication | 0.3.6 (`ccd314d`) | [19-nov](https://github.com/ARQUI-202630/quickpatch-communication/actions/runs/44540054039) | 0.3.3 (`2ee5a3d`) | [4-nov](https://github.com/ARQUI-202630/quickpatch-communication/actions/runs/41786768003) |
| Panel web (Angular) | 0.7.1 (`c2ea0cb`) | [23-nov](https://github.com/ARQUI-202630/quickpatch-web/actions/runs/45316896304) (job «Panel en qa») | 0.5.5 | [4-nov](https://github.com/ARQUI-202630/quickpatch-web/actions/runs/41929037853) (job «Panel en produccion») |
| App móvil (APK) | `v0.6.1-qa` (`5403323`) | [23-nov](https://github.com/ARQUI-202630/quickpatch-mobile/actions/runs/45316901323) | 0.5.4 (`73fbb4b`) | [4-nov](https://github.com/ARQUI-202630/quickpatch-mobile/actions/runs/41932016106) (job «Publicar el APK de producción») |
| Gateway (Nginx) | Se instala con `deploy-gateway.yml` desde Ansible, no desde un pipeline; el contrato está en `v0.24.0` | Ansible | Igual que QA | Ansible |

El 19-nov, `https://qa.quickpatch.internal/` y `https://quickpatch.internal/` responden los dos con el panel real («QUICKPATCH — Panel administrativo»). En producción ya no está la página provisional.

**QA va adelante de producción en los 7 servicios desplegados, el panel y la app.** Esas versiones corrigen y refactorizan sobre el MVP del Sprint 6 (SCRUM-644, 650, 656 y 657) y no se han promovido. Promoverlas es parte de SCRUM-670 y lo decide el equipo con la PO, con la UAT de cierre (SCRUM-658) como compuerta.

## 3. Traza release → QA → producción (SCRUM-672)

Para cada versión en producción se buscó un push de su rama `release/*` cuyo job de QA terminara bien **antes** del despliegue en producción.

| Componente | Versión en producción | Corrida en QA de esa misma rama | Resultado del job de QA | Producción después de QA |
|---|---|---|---|---|
| Identity | release/0.8.1 | [4-nov, 05:24](https://github.com/ARQUI-202630/quickpatch-identity/actions/runs/41779018676) | Despliegue en qa: success | Sí (4-nov, 06:07) |
| Catalog | release/0.4.1 | [2-nov](https://github.com/ARQUI-202630/quickpatch-catalog/actions/runs/41521829614) | Despliegue en qa: success | Sí (4-nov) |
| ServiceRequest | release/0.11.2 | [4-nov](https://github.com/ARQUI-202630/quickpatch-service-request/actions/runs/41837932598) | Despliegue en qa: success | Sí (4-nov, 23:54) |
| Matching | release/0.6.1 | [2-nov](https://github.com/ARQUI-202630/quickpatch-matching/actions/runs/41514038766) | Despliegue en qa: success | Sí (4-nov) |
| Ranking | release/0.1.0 | [28-oct](https://github.com/ARQUI-202630/quickpatch-ranking/actions/runs/40711518181) | Despliegue en qa: success | Sí (4-nov) |
| Payments | release/0.3.0 | [2-nov](https://github.com/ARQUI-202630/quickpatch-payments/actions/runs/41473326330) | Despliegue en qa: success | Sí (4-nov) |
| Communication | release/0.3.3 | [2-nov](https://github.com/ARQUI-202630/quickpatch-communication/actions/runs/41514037383) | Despliegue en qa: success | Sí (4-nov) |
| Panel web | release/0.5.5 | [4-nov](https://github.com/ARQUI-202630/quickpatch-web/actions/runs/41773269075) | Panel en qa: success | Sí (4-nov) |
| App móvil | release/0.5.4 | [4-nov](https://github.com/ARQUI-202630/quickpatch-mobile/actions/runs/41773266842) | Publicar el APK: success | Sí (4-nov, 23:21) |

**Resultado: 0 versiones en producción sin corrida de QA.** Las 9 tienen un despliegue exitoso de la misma rama en QA antes de llegar a `main`. Además, el pipeline de producción vuelve a pasar la compuerta automática de QA (RNF-08), que comprueba el humo de los frontends contra la versión que ya corre en QA. Esa compuerta bloqueó una vez a identity el 4-nov; el caso está en INFRASTRUCTURE.md, 4.3.

Las pruebas del sistema en QA que acompañaron la promoción (`humo-frontends.yml` y `pruebas-sistema.yml` del superproyecto) pasaron el 4-nov ([humo](https://github.com/ARQUI-202630/quickpatch/actions/runs/41935071280), [sistema](https://github.com/ARQUI-202630/quickpatch/actions/runs/41935076005)). La última corrida de `pruebas-sistema.yml` es del [11-nov](https://github.com/ARQUI-202630/quickpatch/actions/runs/42957062365).

**Excepciones**

- **Gateway:** no tiene pipeline de despliegue. Se instala con Ansible (`deploy-gateway.yml`, y `verificar-gateway-ambiente.yml` comprueba que cada ambiente apunte a su propio k3s). Como no hay corrida de CI que enlazar, la traza del gateway es el registro de Ansible de DevOps.
- **Actors:** desplegado en QA (23 de noviembre) y en producción (24 de noviembre) con la misma imagen `t-dfd6da88c157`. Siguió el flujo `release/0.2.0` → QA → `main` (PR #10 de `quickpatch-actors`), y la producción usó la imagen de QA sin reconstruirla.

## 4. Versiones de QA del 23 de noviembre (SCRUM-709)

Identity 0.10.5, ServiceRequest 0.12.4 y Payments 0.3.4 reorganizan el código por capas sin cambiar contratos ni eventos (SCRUM-710 a SCRUM-712). El panel 0.7.1 mueve un helper a `core/` (SCRUM-713). El APK `v0.6.1-qa` corta las dependencias entre features (SCRUM-714) e incluye la corrección de la prueba de humo (quickpatch-mobile#61). Cada despliegue terminó con el `rollout status` en verde. La regresión contra QA del 23 de noviembre pasó sin fallos: 26 colecciones de Newman (1.138 peticiones y 1.594 aserciones) que cubren Identity, ServiceRequest y Payments de punta a punta, el chat en tiempo real (23 de 23), el aviso de cancelación (6 de 6) y el enlace de recuperación vencido (11 de 11). Las evidencias están en `tests/e2e/evidencias/*-qa-2026-11-23.txt` y `*-qa-2026-11-24.txt` (la corrida cruzó la medianoche UTC).

En esta corrida se corrigió el cargador local de credenciales, que dejaba vacía la clave del administrador de plataforma: Newman saltaba sin avisar los pasos que la usan. En la regresión del 19 de noviembre (sección 5) esos pasos no corrieron; las colecciones 105, 478-cancelación, 511 y 627-recuperación se repitieron el 23 de noviembre con ellos y pasaron.

## 5. Regresión de las versiones de QA del 19 de noviembre

Después de desplegar Identity 0.10.4 y Communication 0.3.6 se corrieron contra QA 11 colecciones de Newman: 364 peticiones y 591 aserciones, 0 fallos. También pasaron las dos pruebas de tiempo real, la del chat con 23 de 23 y la del aviso de cancelación con 6 de 6. Las evidencias están en `tests/e2e/evidencias/*-qa-2026-11-19.txt`.
