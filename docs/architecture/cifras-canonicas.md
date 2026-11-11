# Cifras canónicas de QUICKPATCH

**Tarea:** SCRUM-691 (historia SCRUM-690, auditoría de consistencia del cierre)
**Fecha de corte:** 11 de noviembre de 2026, sobre `develop` del superproyecto y de cada repositorio

El profesor encontró en la entrega del Sprint 5 que la misma cifra cambiaba entre diapositivas y documentos. Esta tabla es la **fuente única**: SRS, SAD, SDD, DD, Infraestructura, TD, los informes y la presentación deben usar estos valores y citar este documento. Cada valor sale de una fuente verificable (código, contratos, repositorios o el documento dueño del dato), no de otro documento derivado.

Si un dato cambia, se cambia primero en su fuente y después aquí, en el mismo PR.

## Producto y alcance

| Cifra | Valor | Fuente de verdad | Evidencia |
|---|---|---|---|
| Roles de usuario | **6**: Cliente, Empresa (usuario autorizado de la cuenta corporativa), Técnico y Proveedor en la app móvil; Admin del tenant y Admin de plataforma en el panel web | SRS, sección 2.1 (usuarios y canal) | Roles del JWT en `quickpatch-identity`: `cliente`, `empresa_contacto`, `tecnico`, `proveedor`, `admin_tenant`, `admin_plataforma` |
| Módulos del producto | **14**: 7 de dominio (Usuarios y Cuentas, Solicitudes y Matching, Seguimiento y Calificación, Ejecución de Servicios, Gestión de Equipos, Administración y Operaciones, Pagos y Facturación) y 7 transversales (Multi-tenancy, Seguridad y Control de Acceso, Integración de Pagos, Notificaciones, Logging y Monitoreo, CI/CD, Gestión del Proyecto y Documentación) | SRS, sección 4 | — |
| Requisitos funcionales | **33** (RF-01 a RF-29 y RF-34 a RF-37) | SRS v5.6 | `docs/testing/matriz-funcionalidades-srs-v5.md` |
| Requisitos no funcionales | **14** (RNF-01 a RNF-14) | SRS | — |
| Área de operación | Bogotá D.C. | SAD, restricción R6 | — |

**Funcionalidades: unidad por decidir (SCRUM-699 / SCRUM-700).** Hoy conviven tres conteos: 33 requisitos funcionales (SRS v5.6), 78 funcionalidades por usuario (`docs/testing/avance-real-sprint5.md`) y el «37» de la presentación del Sprint 5, que no corresponde a ninguno. Hasta que SCRUM-700 fije la unidad y los cuatro indicadores (definidas, implementadas, verificadas en QA y aceptadas), **la presentación usa los 33 RF del SRS**, y las 78 funcionalidades solo como desglose por usuario.

## Arquitectura

| Cifra | Valor | Fuente de verdad | Evidencia |
|---|---|---|---|
| Microservicios definidos | **8**: Identity, Actors, Catalog, ServiceRequest, Matching, Ranking, Payments y Communication | SAD, sección 4; ADR-003 | — |
| Microservicios con código | **7**. Actors es un esqueleto: solo `Program.cs`, sin lógica (el SAD 4.2.2 ya lo marca como Planeado) | Código de `develop` | `docs/architecture/codigo/antes/README.md` (SCRUM-682) |
| Stack por servicio | 7 en ASP.NET Core / .NET 10; Matching en Java + Spring Boot | ADR-012 | `apps/backend/CLAUDE.md` |
| Repositorios | **14**: 13 de componentes (web, mobile, API Gateway, los 8 microservicios, Kafka y, desde el 11-nov, `quickpatch-shared-dotnet` de ADR-020) más el principal `quickpatch` | ADR-021 y ADR-020 | `gh repo list ARQUI-202630`: los 14 `quickpatch*` activos (`quickpatch-contracts` e `quickpatch-infrastructure` están archivados). La infraestructura vive en `quickpatch/infrastructure` (SCRUM-338), no en un repositorio propio |
| Topics de Kafka | **20** | `quickpatch-kafka`, `topics/topics.yaml` | `develop` del 11-nov-2026 |
| Esquemas de eventos | **20** | `quickpatch-kafka`, `events/` | Un esquema por topic |
| ADR | **25**: 24 aceptados y 1 propuesto (ADR-019 roles de base de datos). ADR-020 se aceptó el 11-nov (SCRUM-657). La numeración llega a ADR-028; ADR-001, ADR-008 y ADR-010 no se asignaron | `docs/architecture/adr/` | `docs/architecture/adr/README.md` |
| Bases de datos | **8** bases lógicas, una por servicio (`db_identity`, `db_actors`, `db_catalog`, `db_service_request`, `db_matching`, `db_ranking`, `db_payments`, `db_communication`), en una instancia de PostgreSQL por ambiente, más Redis y Garage | ADR-014, ADR-016; DD | `docs/infrastructure/INFRASTRUCTURE.md` |
| Ambientes | **2**, QA y producción, con datos y secretos separados, más VM1 de herramientas compartida | ADR-022, ADR-028 | INFRASTRUCTURE, ambientes |
| Máquinas virtuales | **7**: VM1 herramientas; VM3, VM4 y VM6 producción; VM2, VM5 y VM7 QA | ADR-022; SAD, restricción R10 | INFRASTRUCTURE |

## Atributos, escenarios y decisiones (SAD)

| Cifra | Valor | Fuente de verdad |
|---|---|---|
| Drivers | **8** (D1 a D8) | SAD 1.1 |
| Killers | **4** (K2, K12, K13 y K14) | SAD 1.2.1 |
| Restricciones | **9** (R1, R3, R5, R6, R7, R9, R10, R11 y R12) | SAD 1.2.2 |
| Fuera de alcance | **3** (FA1 a FA3) | SAD 1.3 |
| Atributos de calidad | **9** (AC1 a AC9, ISO/IEC 25010:2023) | SAD 2 |
| Escenarios de calidad | **52**: AC1 3, AC2 5, AC3 2, AC4 9, AC5 6, AC6 8, AC7 6, AC8 5 y AC9 8 | SAD 3; `docs/testing/matriz-escenarios-calidad-52.md` |
| Estado de los escenarios | **34 Cumple, 8 Parcial, 4 No cumple, 6 No medido** (total 52) | `docs/testing/matriz-escenarios-calidad-52.md` (SCRUM-563), al 11-nov-2026. La fuente única la cierra SCRUM-664 |
| Riesgos aceptados | **4** | SAD 6.2 |

## Discrepancias encontradas al armar esta tabla

| Dónde | Valor encontrado | Valor canónico | Tarea que lo corrige |
|---|---|---|---|
| Presentación del Sprint 5 | 37 funcionalidades, 94 % y 36 aceptadas | 33 RF; indicadores por definir | SCRUM-700 y SCRUM-701 |
| Presentación del Sprint 5 | 39 escenarios aprobados | 34 Cumple de 52 | SCRUM-664 |
| Acta UAT del Sprint 5 (`docs/testing/acta-uat-scrum-608.md`, firmada por la PO) | 37 de 37 funcionalidades aceptadas; avance de 91,92 % | 33 RF; el acta se conserva como registro histórico y no se modifica | SCRUM-700 |
| Presentación del Sprint 5 | 5 o 6 usuarios según la diapositiva | 6 roles. El «5» venía de los escenarios AC4 («4 de 5 usuarios de prueba»), que cuentan participantes de una prueba de uso, no roles; desde SCRUM-688 dicen «participantes» | SCRUM-688 (hecho) y SCRUM-706 |
| ADR-021 y textos que dicen «doce repositorios» | 12 | 12 de componentes más el principal, 13 en total | SCRUM-692 |
| INFRASTRUCTURE.md (producción) | «hoy Identity, Catalog, ServiceRequest y Matching» en el k3s de VM3 | Lo dirá el inventario por ambiente | SCRUM-671 y SCRUM-694 |
