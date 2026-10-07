# ADR-013 — Estrategia de repositorios: un repositorio por componente, unidos con submódulos

- **Estado:** Aceptado
- **Fecha:** 2026-10-01
- **Decisión:** Multirepo por componente, con un repositorio principal que referencia a los demás como submódulos de Git
- **Implementación:** PR #9 de `quickpatch` (organización `ARQUI-202630`)

## Contexto

QUICKPATCH tenía todo su código y su documentación en un solo repositorio (monorepo): los 8 microservicios, el panel web, la aplicación móvil, la infraestructura y los contratos compartidos.

La arquitectura ya trataba a cada microservicio como una unidad independiente: un Deployment propio en k3s, una imagen Docker propia y un pipeline propio (SAD, sección 4.2; Documento de Infraestructura, secciones 5.8 y 6.1). El repositorio era la única pieza que no reflejaba esa independencia. Nada impedía que un servicio importara código de otro, y todos compartían historial, versiones y tags.

El profesor del curso señaló esta inconsistencia: con una arquitectura de microservicios se espera un repositorio por componente funcional, y sugirió usar submódulos de Git para mantener un punto de entrada único.

## Decisión

Cada componente que se construye y se despliega por separado tiene su propio repositorio en la organización `ARQUI-202630`:

| Repositorio | Contenido | Stack |
|---|---|---|
| `quickpatch-identity`, `quickpatch-actors`, `quickpatch-catalog`, `quickpatch-service-request`, `quickpatch-ranking`, `quickpatch-payments`, `quickpatch-communication` | Código, pruebas unitarias y de integración, `Dockerfile` y pipeline de cada servicio | ASP.NET Core |
| `quickpatch-matching` | Ídem | Java + Spring Boot |
| `quickpatch-web` | Panel administrativo | Angular |
| `quickpatch-mobile` | Aplicación de clientes y técnicos | Flutter |
| `quickpatch-contracts` | OpenAPI y esquemas de eventos Kafka, versionados con tags SemVer | OpenAPI, JSON Schema |
| `quickpatch-infrastructure` | Playbooks de Ansible y manifiestos de k3s | Ansible, k3s |

El repositorio principal, `quickpatch`, contiene la documentación, la composición versionada y las pruebas del sistema completo (E2E, carga y seguridad). Los artefactos operativos de Docker Compose, Ansible y k3s pertenecen a `quickpatch-infrastructure`. El superproyecto referencia a los 12 repositorios componentes como submódulos; los contratos viven en `contracts/` mediante `quickpatch-contracts`.

Cada repositorio que consume contratos —los ocho servicios, Web y Mobile— incluye `quickpatch-contracts` como submódulo en `contracts/`, fijando el commit correspondiente a una versión SemVer. Así cada componente declara exactamente contra qué contratos se construye.

## Reglas de trabajo

1. Los submódulos del repositorio principal siguen la rama `develop` de cada componente.
2. Un cambio se hace, revisa y fusiona en el repositorio del componente. Después se actualiza el puntero en el repositorio principal. El orden importa: primero el componente, después el principal.
3. Dentro de un submódulo hay que cambiarse a una rama antes de trabajar, porque Git deja los submódulos sin rama por defecto.
4. Cambiar la versión de contratos de un servicio es un commit explícito en ese servicio.
5. Una versión del sistema completo es un tag del repositorio principal (por ejemplo `v0.3.0`), que fija qué commit de cada componente forma parte de la entrega.
6. En el superproyecto se recomienda `submodule.recurse=false`, `fetch.recurseSubmodules=false` y `push.recurseSubmodules=check`. La composición se sincroniza explícitamente con `git submodule update --init --recursive`, evitando que un `pull` avance accidentalmente los submódulos anidados de contratos.

## Consecuencias

### Positivas

- Cada componente tiene historial, versiones, pipeline y dueño propios.
- Ningún servicio puede depender del código interno de otro: solo comparten contratos versionados, como exige el ADR-012.
- El repositorio principal conserva un punto de entrada único y registra qué versiones de los componentes van juntas.
- Las pruebas del sistema completo prueban exactamente la combinación de versiones que fija el repositorio principal.

### Costos

- Un cambio que afecta a varios componentes, por ejemplo un contrato, requiere varios Pull Requests coordinados.
- El equipo debe aprender el flujo de submódulos y respetar el orden de publicación.
- Son 13 repositorios para configurar: ramas, CI, permisos y enlaces con Jira.
- El desarrollo e integración del sistema completo utilizan los artefactos de entorno mantenidos en `quickpatch-infrastructure`, fijados por el submódulo `infrastructure/`.

## Decisiones descartadas

### Mantener el monorepo

Se descartó porque la independencia entre servicios dependía solo de la disciplina del equipo, y no reflejaba en el repositorio la independencia que la arquitectura ya establece.

### Agrupar varios servicios por dominio en un mismo repositorio

Se descartó porque vuelve a juntar servicios en un mismo historial. Además, `Matching` está en Java y el resto en .NET, lo que mezclaría dos toolchains en un solo repositorio.

### Contratos en el repositorio principal

Se descartó porque cada servicio necesita los contratos para construirse en su propio CI. Si vivieran en el principal, cada servicio tendría que incluir al principal como submódulo, que a su vez incluye al servicio.

### Publicar los contratos como paquetes (NuGet y Maven)

Se descartó por ahora porque exige mantener dos registros de paquetes, y una sola persona administra la infraestructura (R11).

### `git subtree` en lugar de submódulos

Se descartó porque copia el código de cada componente dentro del principal y vuelve a juntarlo todo en un solo historial.

## Pendientes

- Crear los teams de la organización y asignar el acceso por repositorio.
- Mover a cada servicio las pruebas de integración y de contrato que hoy están en `tests/integration/` y `tests/contract/` del repositorio principal.
- Ajustar el Documento de Infraestructura (sección 6, un pipeline por repositorio) y el documento de Políticas (GitFlow por repositorio y responsable de actualizar los punteros).
- Regenerar la Figura 13 del SDD, que todavía dibuja `contracts/` dentro de `docs/`.

## Trazabilidad

Esta decisión se refleja en:

- `README.md`
- `docs/architecture/SDD.md` (sección 6)
- `docs/architecture/adr/ADR-012-stack-tecnologico-polyglot.md` (ruta de contratos)
- `AGENTS.md`, `CLAUDE.md`, `.ai/roles/`, `apps/backend/AGENTS.md`, `apps/backend/CLAUDE.md`
- `.github/CODEOWNERS.example`
