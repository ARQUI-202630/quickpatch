# ADR-021 — Doce repositorios por componente de la solución

- **Estado:** Aceptado; modifica a ADR-013
- **Fecha:** 6 de octubre de 2026
- **Decisión:** La solución tiene 12 repositorios —Flutter, Angular, API Gateway, los 8 microservicios y Apache Kafka—, unidos por el repositorio principal `quickpatch`. Los contratos REST viven en el repositorio del API Gateway y los de eventos en el de Kafka; cada repositorio tiene su propio pipeline de CI
- **Atributo priorizado:** AC7 Maintainability (Modularity: cada pieza desplegable o compartida tiene un dueño, un historial y un pipeline propios)
- **Atributo sacrificado:** costo de coordinación (los servicios dependen de dos repositorios de contratos; el CI se repite por stack en cada repositorio)
- **Implementación:** SCRUM-333 (SCRUM-335, 336, 337 y 338); `quickpatch` PR #40

## Contexto

ADR-013 dejó 12 submódulos: los 8 servicios, web, mobile, `quickpatch-contracts` (OpenAPI y eventos juntos) y `quickpatch-infrastructure` (Ansible, k3s y los workflows reutilizables de CI/CD).

En la revisión de octubre de 2026, el profesor pidió que el multirepo refleje los **componentes de la solución**, no los artefactos de apoyo: Flutter, Angular, API Gateway, Identity, Actors, Catalog, ServiceRequest, Matching, Ranking, Payments, Communication y Apache Kafka. El API Gateway y Kafka son componentes de la arquitectura (SAD, sección 4) que no tenían repositorio, mientras que contratos e infraestructura sí lo tenían.

Había además una dependencia que la nueva composición no podía conservar: todos los pipelines llamaban a workflows de `quickpatch-infrastructure@main`, así que un cambio en ese repositorio alteraba el CI de los 11 restantes.

## Decisión

|Repositorio|Contenido|
|---|---|
|`quickpatch-mobile`|Aplicación Flutter|
|`quickpatch-web`|Panel Angular|
|`quickpatch-api-gateway`|Configuración del gateway (`nginx/`) y **contratos REST** (`openapi/`)|
|`quickpatch-identity`, `-actors`, `-catalog`, `-service-request`, `-ranking`, `-payments`, `-communication`|Servicios ASP.NET Core|
|`quickpatch-matching`|Servicio Java + Spring Boot|
|`quickpatch-kafka`|**Esquemas de eventos** (`events/`), topics (`topics/topics.yaml`) y despliegue de Kafka (`deploy/`)|

- **Repositorio principal `quickpatch`:** documentación, contexto de agentes, pruebas del sistema completo y la composición de los 12 como submódulos en `apps/`. El aprovisionamiento (Ansible y k3s) pasa a la carpeta `infrastructure/` de este repositorio (SCRUM-338).
- **Contratos:** cada servicio incluye `contracts/api-gateway/` y `contracts/kafka/` como submódulos fijados en un tag; web y mobile solo `contracts/api-gateway/`. El dueño de cada contrato sigue siendo el servicio que lo provee o produce; el repositorio solo lo aloja y valida su compatibilidad.
- **CI por repositorio:** cada repositorio tiene su workflow de CI completo según su stack, sin llamar a workflows de otro repositorio. La cobertura se mide con un script dentro del mismo repositorio.
- **Recursos por servicio:** cada servicio tiene su base de datos (ADR-014) y, si los necesita, su caché en Redis y sus buckets en Garage, con credenciales propias. Esa configuración se documenta en el repositorio del servicio.
- `quickpatch-contracts` y `quickpatch-infrastructure` quedaron archivados, con su historial (SCRUM-338).

Las reglas de trabajo de ADR-013 (orden de publicación, submódulos sin rama, versión del sistema como tag del principal) siguen vigentes.

## Alternativas descartadas

- **Conservar `quickpatch-contracts` e `quickpatch-infrastructure` como repositorios de apoyo (14 en total):** menos cambios, pero no responde a la observación del profesor y mantiene la dependencia del CI en un repositorio externo.
- **Contratos en el repositorio principal:** descartado por la misma razón que en ADR-013: cada servicio tendría que incluir al principal, que a su vez lo incluye a él.
- **Un repositorio de contratos dentro de cada servicio proveedor:** cada consumidor tendría un submódulo por servicio del que depende; con 8 servicios, demasiados submódulos.
- **Workflows reutilizables en un repositorio de plantillas:** evita repetir el CI, pero vuelve a crear la dependencia que se quería quitar.

## Consecuencias

### Positivas

- El multirepo coincide con los componentes de la arquitectura: el gateway y Kafka tienen dueño, historial y pipeline.
- Los contratos quedan junto al componente que los expone (REST en el gateway, eventos en el bus) y Kafka declara sus topics junto a sus esquemas.
- Un cambio en un repositorio no altera el CI de los demás.

### Costos

- Los servicios dependen de dos repositorios de contratos en lugar de uno.
- El CI se repite en cada repositorio del mismo stack; una mejora del pipeline se aplica repositorio por repositorio.

## Evidencia

- `quickpatch-api-gateway` y `quickpatch-kafka` creados con tag `v0.2.0`, que contiene los mismos contratos que `quickpatch-contracts@develop`.
- Los 8 servicios, web y mobile pasaron a los contratos nuevos y a su CI propio, con CI en verde en el PR y en `develop` (incluye pruebas de integración).
- `tools/validate-composition.sh` comprueba los 12 submódulos y los contratos de cada consumidor en un tag.
- SCRUM-338: Ansible pasó a `infrastructure/`; la configuración de Nginx a `quickpatch-api-gateway/nginx/` y el despliegue de Kafka, con la creación de los topics, a `quickpatch-kafka/deploy/`, que Ansible usa desde los submódulos. La imagen y el despliegue a QA y producción están en el `ci-cd.yml` de cada componente, sin workflows de otros repositorios.

## Pendientes

- SCRUM-339: configuración de base de datos, Redis y Garage por servicio.
- Figuras 08 y 09 del SDD: todavía muestran `contracts/openapi/` y `contracts/events/` como rutas; la figura 07 ya se regeneró con su fuente en `diagrams/sdd/src/`.

## Trazabilidad

- SAD: sección 6 (ADR-013 y ADR-021).
- SDD: sección 6 (vista de desarrollo) y sección de contratos.
- Documento de Infraestructura: sección 6 (CI/CD).
- Relacionados: ADR-003, ADR-006, ADR-012, ADR-013, ADR-014.
