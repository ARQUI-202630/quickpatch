# Cierre del proyecto QUICKPATCH

**Tarea:** SCRUM-703 (historia SCRUM-702)
**Estado:** borrador del 11 de noviembre de 2026. Las secciones de calidad, UAT y avance funcional se completan cuando cierren SCRUM-664 (escenarios), SCRUM-658 (UAT) y SCRUM-700 (indicadores funcionales); hasta entonces muestran el último valor verificado y dicen que está pendiente.
**Fuentes:** SRS 5.12, SAD 2.50, SDD V4 + cierre, cifras canónicas (`docs/architecture/cifras-canonicas.md`) y matriz de lo modelado frente a lo real (`docs/architecture/matriz-modelado-vs-real.md`).

## 1. La necesidad y el problema

En Bogotá, quien necesita un técnico para el hogar o para una sede de su empresa (plomería, electricidad y otras especialidades) depende de conocidos o de directorios. No sabe quién está disponible y cerca, no conoce el precio antes de que empiece el trabajo, no puede seguir el servicio y no tiene una prueba de que el trabajo se hizo ni un comprobante del pago. Las empresas que ofrecen técnicos, por su parte, no tienen una plataforma donde operar con sus propios técnicos y datos sin mezclarse con otras empresas.

## 2. Objetivo

Construir un MVP de una plataforma **multi-tenant** de servicios técnicos para hogares y empresas en **Bogotá D.C.** que asigne automáticamente un técnico **disponible y cercano**, y que permita cotizar antes de empezar, seguir el servicio, cerrarlo con **evidencia fotográfica obligatoria**, pagar con **comprobante** y **calificar**, con aislamiento de datos entre empresas (SRS 2.2).

## 3. Alcance definido

| Elemento | Alcance | Fuente |
|---|---|---|
| Roles | 6: Cliente, Empresa, Técnico y Proveedor en la app móvil; Admin del tenant y Admin de plataforma en el panel web | SRS 2.1 |
| Funciones | 8 funciones del producto, 33 requisitos funcionales y 14 no funcionales | SRS 2.2, 5.2 y 5.3 |
| Zona | Bogotá D.C. y sus localidades | SAD, restricción R6; SRS 2.3.1 |
| Pagos | Pago tokenizado a nombre de la plataforma, sin guardar PAN ni CVV; en el MVP, con una pasarela **simulada** | SAD, killer K2; ADR-009 modificado |
| Fuera de alcance | Modo sin conexión (FA1), sitio con SEO (FA2), módulo de reclamos (FA3) y funciones de ERP (R1) | SAD 1.2.2 y 1.3 |

## 4. Qué construimos

| Función (SRS 2.2) | Qué hay | Dónde |
|---|---|---|
| Registro, autenticación y aislamiento por tenant | Identity con JWT RS256, seis roles y RLS en PostgreSQL. Desde SCRUM-644, la contraseña viaja cifrada con RSA-OAEP-256 | ADR-005, ADR-018; Identity |
| Solicitud, cotización y aceptación | ServiceRequest: solicitud con dirección geocodificada en Bogotá, hasta 3 cotizaciones y aceptación del cliente antes de empezar | ServiceRequest; ADR-024 |
| Asignación automática | Matching (Java + Spring Boot + PostGIS): oferta al técnico disponible más cercano de la especialidad, con vencimiento de 3 minutos y reintento con el siguiente | Matching; ADR-004 |
| Ejecución con evidencia y seguimiento | Inicio, **evidencia fotográfica obligatoria** en Garage y cierre; seguimiento en tiempo real por WebSocket y buzón; chat de la solicitud | ServiceRequest, Communication; ADR-016, ADR-023, ADR-026 |
| Pago y comprobante | Payments con la pasarela simulada, pago de la empresa y comprobante en JSON y PDF, sin validez fiscal (DR-03); pagos recibidos del técnico y del proveedor | Payments; ADR-009 |
| Calificación y reputación | Calificación del servicio pagado; Ranking calcula la reputación por eventos y el panel señala a los técnicos con reputación baja (SCRUM-642, AC9-E2 medido en QA: 100 %) | ServiceRequest, Ranking, Identity; ADR-027 |
| Administración | Verificación y suspensión de técnicos, gestión de tenants y panel operativo | Panel web, Identity |
| Infraestructura y calidad | 14 repositorios con CI propio; 2 ambientes (QA y producción) en 7 VM; promoción a producción solo desde `release/*` probado en QA; observabilidad con Prometheus, Loki y Grafana | ADR-021, ADR-022, ADR-028 |

**Arquitectura final.** 8 microservicios definidos, de los cuales 7 tienen código y están desplegados en QA y en producción; Actors es un esqueleto (planeado). Hay 20 eventos de Kafka con Outbox e idempotencia, y 8 bases lógicas en una instancia de PostgreSQL por ambiente. En el Sprint 6, cinco servicios se refactorizaron con reglas de dependencia verificadas por pruebas de arquitectura en su CI. Matching y Payments quedaron sin ciclos entre paquetes, y el nivel de código se genera desde el código (SDD 7.3).

## 5. Qué no construimos

| Elemento | Por qué | Dónde queda registrado |
|---|---|---|
| Pasarela de pagos certificada real | Sin presupuesto ni dominio público (R5, R9); se usa la simulada detrás del mismo puerto | ADR-009 modificado; matriz de lo modelado frente a lo real |
| Actors Service | Sus conceptos siguen siendo evolutivos; el equipo del proveedor vive en Identity mientras tanto | SAD 4.2.2 |
| Regla de 4 horas para servicios sin cierre (AC9-E3) | Función nueva que no estaba comprometida; quedó fuera por el feature freeze | Working Agreements (SCRUM-646) |
| Contexto de tenant e idempotencia compartidos (resto de AC7-E5) | Están mezclados con reglas de cada servicio; la v0.1.0 de ADR-020 cubre la correlación, el rol de sesión y el publicador del Outbox | SCRUM-657 |
| Módulo de reclamos, modo sin conexión y SEO | Fuera de alcance del MVP | SAD 1.3 |

## 6. Evidencia de lo logrado

| Indicador | Valor | Estado |
|---|---|---|
| Escenarios de calidad | 52: 34 Cumple, 8 Parcial, 4 No cumple, 6 No medido (al 11-nov) | **Pendiente:** cifra final de SCRUM-664 |
| Escenarios que no cumplen | AC7-E2 (78,6 % frente a 80 %), AC7-E3 (Ranking tocó 2 servicios), AC7-E5 (lógica copiada) y AC9-E3 (sin regla de 4 horas), con su decisión | SCRUM-669 |
| Requisitos funcionales | 33 definidos; implementados, verificados en QA y aceptados | **Pendiente:** indicadores de SCRUM-700 |
| UAT | UAT por RF con la Product Owner (SCRUM-605, acta de SCRUM-608) | **Pendiente:** UAT de cierre con los 6 roles (SCRUM-658) |
| Separación QA / producción | El token de QA es rechazado por producción (401); versiones verificadas con `kubectl` | `tests/e2e/evidencias/separacion-qa-produccion-2026-11-10.txt`; INFRA 4.16 |
| Confiabilidad | Kafka caído: el Outbox retuvo los eventos y los publicó solos en 34 s; consumidor caído: réplica al día 24 s después de volver | `tests/e2e/evidencias/confiabilidad-ac5-e3-e4-qa-2026-11-10.txt` |

## 7. Restricciones y riesgos aceptados

- **Restricciones que marcaron el diseño:** 7 VM fijas (R10), sin presupuesto (R5), red privada sin dominio público (R9), una sola persona en infraestructura (R11) y unos 3 meses de proyecto (R3).
- **Riesgos aceptados** (SAD 6.2): un solo nodo por componente en producción; un sistema distribuido con un equipo pequeño; lógica transversal copiada en .NET (AC7-E5); y los demás de esa sección.
- **Riesgos del cierre:** AC9-E3 sin cubrir. Los cambios del Sprint 6 (SCRUM-642 y los refactors de cinco servicios) están en QA desde el 11 de noviembre y todavía no en producción. El secreto `PasswordEncryption__PrivateKeyPem` debe existir antes de escalar Identity a más de una réplica.

## 8. Conclusión

**Pendiente** de la revisión de la Product Owner (SCRUM-704) y de las cifras finales de las secciones 6 y 7. Lo que ya se puede afirmar con evidencia: el flujo completo, desde la solicitud hasta el pago, el comprobante y la calificación, pasó en QA (humo del flujo crítico del 30 de octubre, `tests/e2e/evidencias/humo-flujo-critico-qa-2026-10-30.txt`), y los 7 servicios con código están desplegados en producción desde el 4 de noviembre (SCRUM-518). Lo que falta se declara en la sección 5 con su motivo.
