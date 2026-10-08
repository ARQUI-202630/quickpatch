# Infraestructura QUICKPATCH

Implementación de `docs/infrastructure/INFRASTRUCTURE.md` con la distribución de VMs del ADR-022:

- **Herramientas (VM1):** Gateway Nginx (entrada de producción y de QA), panel Angular de producción, runner de despliegue, Prometheus, Loki y Grafana.
- **Producción:** VM3 (k3s con los microservicios), VM4 (PostgreSQL + PostGIS y Redis) y VM6 (Kafka y Garage).
- **QA:** VM2 (k3s), VM5 (PostgreSQL + PostGIS y Redis) y VM7 (Kafka y Garage).

Hasta el Sprint 3 vivía en el repositorio `quickpatch-infrastructure`, que se archivó (SCRUM-338).

## Contenido

|Carpeta|Contenido|
|---|---|
|[`ansible/`](ansible/README.md)|Aprovisionamiento de las VMs con Ansible (`./ap playbooks/<playbook>.yml`).|
|[`CI-CD.md`](CI-CD.md)|Pipelines de cada repositorio y compuertas del Documento de Pruebas.|
|`plantillas/hooks/pre-push`|Hook local (compuerta 0) para instalar en cada clon.|

## Qué está en otros repositorios

Cada componente es dueño de su despliegue (ADR-021):

|Qué|Dónde|Cómo lo usa Ansible|
|---|---|---|
|Configuración de Nginx del gateway|`quickpatch-api-gateway/nginx/` (submódulo `apps/api-gateway`)|`deploy-gateway.yml` escribe la plantilla del submódulo|
|Despliegue de Kafka y creación de topics|`quickpatch-kafka/deploy/` (submódulo `apps/kafka`)|`deploy-kafka.yml` importa el playbook del submódulo|
|Manifiestos de k3s de cada servicio|`deploy/k8s/` de cada repositorio de servicio|`primer-despliegue-servicios.yml` los descarga de la rama indicada|
|Imagen y despliegue en QA y producción|`.github/workflows/ci-cd.yml` de cada repositorio|No lo usa: lo ejecuta el runner de VM1|

Por eso, antes de correr Ansible, se inicializan los dos submódulos:

```bash
git submodule update --init apps/api-gateway apps/kafka
cd infrastructure/ansible && docker build -t quickpatch-ansible . && ./ap playbooks/diagnostico.yml -k -K
```

Ansible aplica la versión del gateway y de Kafka que fija cada submódulo. Para desplegar un cambio de esos repositorios se publica su tag y se actualiza el submódulo en este repositorio.
