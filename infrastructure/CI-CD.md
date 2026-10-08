# CI/CD de QUICKPATCH

Cada repositorio tiene su pipeline completo en `.github/workflows/` (`ci-cd.yml` en los componentes, `ci.yml` en los contratos), sin workflows de otros repositorios: el CI desde SCRUM-337 y el despliegue desde SCRUM-338. Antes los pipelines eran workflows reutilizables de `quickpatch-infrastructure`, que se archivó.

**Qué se prueba** y con qué herramientas sigue el Documento de Pruebas (`docs/testing/TD.md`). **Dónde y cuándo se despliega** sigue el ADR-015 con las VMs del ADR-022: QA con `release/*` y producción con `main`, siempre desde el runner de VM1.

## Compuertas del Documento de Pruebas

| Compuerta | Dónde está implementada |
|---|---|
| 0. Pre-push local | `.githooks/pre-push` de cada repositorio (plantilla en `plantillas/hooks/pre-push`) |
| 1. CI del componente: lint, unitarias, Testcontainers, cobertura ≥ 80% | Job `ci` del `ci-cd.yml` de cada componente; contratos en el `ci.yml` de `quickpatch-api-gateway` y `quickpatch-kafka` |
| 2. Pruebas de sistema: E2E, OWASP ZAP, escáner PCI-DSS | `.github/workflows/pruebas-sistema.yml` de este repositorio, contra QA en `release/*` |
| 3. Carga con k6 | El mismo `pruebas-sistema.yml`, después de E2E y seguridad |

Todos los PR exigen el check `quality-gate`, que reúne los jobs del pipeline de cada repositorio.

## Qué corre en cada rama

| Evento | Servicios (.NET y Java) | Panel web (Angular) | App móvil (Flutter) |
|---|---|---|---|
| PR a `develop` | Lint, pruebas unitarias, cobertura y dependency review | Lint, pruebas, cobertura, build y dependency review | Formato, análisis, pruebas, cobertura y dependency review |
| Push a `develop` | Además, pruebas de integración (Testcontainers) | Lo mismo | Lo mismo |
| Push a `release/*` | Además, imagen en GHCR y **despliegue en QA** (k3s de VM2) | Además, **publica el panel en QA** (VM2) | Además, APK de release |
| Push a `main` | **Despliegue en producción** (k3s de VM3) con la misma imagen de QA | **Publica el panel en producción** (VM1) | APK de release |

QA solo cambia cuando se prepara una versión (`release/*`), no con cada push a `develop`.

### Jobs de despliegue de cada servicio

- **`imagen`** construye y publica `ghcr.io/arqui-202630/<repo>`. La etiqueta es el hash del contenido (`t-<árbol>`), no el del commit: cuando `release/x.y.z` se fusiona en `main` sin otros cambios, la imagen ya existe y producción despliega exactamente la que se probó en QA. Si `main` trae algo que no pasó por `release/*`, construye una imagen nueva y deja un aviso.
- **`desplegar`** corre en el runner de VM1: `kubectl set image` sobre el Deployment del servicio, espera el rolling update y, si falla, hace `kubectl rollout undo`. El ambiente sale de la rama (`release/*` → `qa`, `main` → `produccion`).

El panel tiene un único job `desplegar`, que copia el build en VM1 (producción) o en VM2 por SSH (QA).

## Dónde corre cada cosa

- **Runners de GitHub** (`ubuntu-latest`): lint, pruebas, build y publicación de imágenes.
- **Runner self-hosted de VM1** (etiquetas `self-hosted`, `vm1`, `red-laboratorio`): todo lo que tiene que llegar a la red del laboratorio, es decir los despliegues y las pruebas de sistema contra QA. Los runners de GitHub no alcanzan `10.43.x.x`.

El runner usa los kubeconfig de `~quickpatch/.kube/config-qa` y `config-produccion` que deja `deploy-runner.yml`, así que no hay credenciales de Kubernetes en GitHub. Para el panel de QA usa una llave SSH de VM1 a VM2 que también deja ese playbook.

## CI de este repositorio

`pr-quality.yml` corre en cada PR a `develop` y a `main`:

| Job | Qué revisa |
|---|---|
| `composition` | Los 12 repositorios como submódulos y los contratos de cada consumidor en una versión etiquetada |
| `docs-consistency` | Referencias obsoletas en los documentos |
| `workflows` | actionlint sobre `.github/workflows/` |
| `ansible` | Sintaxis de todos los playbooks y ansible-lint con perfil `production` (INF-001), incluido el playbook de Kafka del submódulo |
| `secretos` | gitleaks sobre el historial de `infrastructure/` y `.github/` (INF-009) |

## Convenciones para los equipos

Salen de la sección 2 del Documento de Pruebas; el pipeline depende de ellas.

- **Cobertura:** mínimo 80% de líneas (compuerta 1). Sin reporte de cobertura, el pipeline falla.
- **.NET:** una solución (`.slnx`) en la raíz del repo; pruebas unitarias en `tests/unit/` y de integración en `tests/integration/`; los proyectos de pruebas referencian `coverlet.collector`.
- **Java (Matching):** `pom.xml` con su wrapper; Failsafe con `*IT.java` para las pruebas de integración y JaCoCo con reporte XML.
- **Angular:** los scripts `lint`, `test:ci` (sin modo watch, navegador headless) y `build` en `package.json`.
- **Imagen:** un `Dockerfile` en la raíz del repo del servicio.
- **Deployment:** el nombre del Deployment en k3s es el nombre del repo sin `quickpatch-` (por ejemplo `identity`), en el namespace `quickpatch`. Su manifiesto está en `deploy/k8s/` del repo y lo aplica `primer-despliegue-servicios.yml` antes del primer despliegue.
- **Pruebas de sistema (este repositorio):** colecciones de Postman en `tests/e2e/*.postman_collection.json`, scripts de k6 en `tests/performance/*.js` y reglas opcionales de ZAP en `tests/security/zap-baseline.conf`.

## Seguridad del runner

Los repositorios son públicos, así que un PR desde un fork no debe ejecutar código en VM1:

- Los jobs que corren en el runner solo se disparan con `push` (o `workflow_dispatch`), nunca con `pull_request`.
- Organización → Settings → Actions → General → "Fork pull request workflows": exigir aprobación para todos los colaboradores externos.
- El grupo del runner tiene activado "Allow public repositories" para que los repositorios públicos lo usen.
- **Aprobación para producción:** en cada repo, Settings → Environments → `produccion` → Required reviewers.

## Pendiente

- Prueba de humo después de desplegar en producción.
- Pruebas de contrato con Pact entre servicios (el Documento de Pruebas las menciona en CAT-011 y ACT-013).
- Limpieza de los datos del tenant de prueba después de k6 (PRF-006).
- Publicar el panel de QA en VM1 en lugar de VM2 (hoy `location /` de QA va al Traefik de VM2).
