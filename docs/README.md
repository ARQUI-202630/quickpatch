# Índice — Documentación QUICKPATCH

Plataforma Digital Multi-tenant de Servicios Técnicos para el Hogar y las Empresas — Arquitectura de Software.

Este archivo es el punto de entrada a la documentación formal del proyecto.

## Documentos vigentes

| Documento | Propósito |
|---|---|
| `SRS.md` | Requisitos funcionales, no funcionales, interfaces y alcance. |
| `SAD.md` | Arquitectura, drivers, killers, atributos de calidad, escenarios y ADR. |
| `SDD.md` | Diseño por vistas y relación entre componentes, procesos y despliegue. |
| `architecture/mapa-arquitectonico.md` | Mapa de la arquitectura documentada frente a la implementada, con la decisión de cada diferencia (SCRUM-570). |
| `design/DD.md` | Documento de Diseño vigente temporal: datos y contratos. |
| `Documento de Infraestructura.md` | Topología, ambientes, despliegue, observabilidad y operación. |
| `Documento Politicas y Herramientas.md` | GitFlow, colaboración, herramientas, calidad y uso de IA. |
| `testing/TD.md` | Documento de Pruebas (TD V1): Estrategia de pruebas automatizadas, compuertas de calidad, RTM y catálogo de pruebas. |
| `testing/evidencias-sprint4.md` | Evidencias del Sprint 4 en QA (SCRUM-449): versiones y pipelines, pruebas de sistema, humo de los frontends, evidencias por historia y capturas. Insumo del informe (SCRUM-394) y la presentación (SCRUM-429). |
| `testing/inventario-funcionalidades-por-usuario.md` | Inventario de 78 funcionalidades por tipo de usuario, con su RF y su HU (SCRUM-560). |
| `testing/avance-real-sprint5.md` | Avance real del producto con fórmula, fecha de corte y clasificación de cada funcionalidad con su evidencia (SCRUM-562). |

## Documento histórico

`archive/DD-v1.md` corresponde a la versión histórica anterior del Documento de Diseño. La versión vigente y única fuente de verdad para nuevas decisiones es `design/DD.md`.

## Precedencia

Cuando exista una aparente contradicción:

1. El SRS define **qué debe hacer** el producto.
2. El SAD define **qué arquitectura y restricciones** gobiernan la solución.
3. El SDD define **cómo se diseña** la solución respetando SRS y SAD.
4. El DD define **cómo se representan datos y contratos concretos**.
5. Infraestructura define **cómo se despliega y opera**.
6. Políticas define **cómo colabora el equipo**.

Una contradicción real no se resuelve silenciosamente: debe corregirse en la fuente correspondiente y mantener trazabilidad.

## Contexto para asistentes de IA

Los agentes no deben cargar toda esta carpeta por defecto.

Punto de entrada:

- `../AGENTS.md`
- `../CLAUDE.md`
- `../.ai/PROJECT_CONTEXT.md`
