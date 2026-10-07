# ADR-003 — Microservicios con arquitectura orientada a eventos (EDA)

- **Estado:** Aceptado
- **Fecha:** agosto de 2026 (SAD 1.0)
- **Decisión:** Ocho microservicios de dominio que se comunican por REST cuando el usuario necesita respuesta inmediata y por eventos en Kafka para coordinar procesos entre dominios
- **Atributos priorizados:** AC8 Flexibility, AC5 Reliability
- **Atributo sacrificado:** AC7 Maintainability (complejidad de un sistema distribuido)
- **Escenarios que la sustentan:** AC5-E3, AC5-E4 (Alta/Alta) y AC8-E2

## Contexto

QUICKPATCH tiene dominios con ritmos y cargas distintos: la búsqueda de técnicos cercanos (D1) concentra la carga en hora pico, el seguimiento en tiempo real (D2) genera muchos cambios de estado, y pagos, reputación y notificaciones reaccionan a esos cambios. Una caída en un dominio secundario (por ejemplo, el cálculo de reputación) no debería detener la creación de solicitudes ni la asignación de técnicos.

El SAD fija ocho dominios: Identity, Actors, Catalog, ServiceRequest, Matching, Ranking, Payments y Communication.

## Decisión

- Cada dominio es un **microservicio** con su propia base de datos (ADR-014), su propia imagen y su propio despliegue en k3s (ADR-011), en su propio repositorio (ADR-013).
- **REST/HTTPS** solo cuando el usuario necesita una respuesta inmediata, siempre a través del API Gateway.
- **Kafka** (ADR-006) para los hechos de dominio y la coordinación entre servicios: un servicio no llama a otro de forma síncrona para cumplir su función (SAD, sección 4.3). Cuando un servicio necesita datos de otro, mantiene una réplica local alimentada por eventos (ADR-017).
- Ningún servicio importa código ni lee tablas de otro; solo comparten contratos versionados en `quickpatch-contracts`.

## Alternativas descartadas

- **Monolito modular:** más simple de desarrollar y probar, pero una falla o un pico de carga en un módulo afecta a todos, y no permite escalar Matching por separado (AC8-E2).
- **Microservicios con llamadas REST síncronas entre ellos:** menos piezas, pero acopla la disponibilidad de cada servicio a la de los que llama; una caída de Ranking o Communication se propagaría a la creación de solicitudes (AC5-E3).
- **Pocos servicios grandes (por ejemplo, tres):** reduce la complejidad operativa, pero mezcla dominios con requisitos de calidad distintos (pagos con PCI-DSS, matching con carga geoespacial).

## Consecuencias

### Positivas
- Fallos aislados: si un servicio cae, los eventos esperan en Kafka y se procesan cuando vuelve (AC5-E3, AC5-E4).
- Cada servicio se escala y se despliega por separado (AC8-E2).
- Matching puede usar otro stack (Java) sin afectar a los demás (ADR-012).

### Costos
- Consistencia eventual: una réplica puede ir unos segundos atrás de su fuente.
- Más piezas que operar, observar y probar (AC7): contratos, Outbox, idempotencia, correlación de logs entre servicios.
- Riesgo frente a R3 y R7: un equipo de estudiantes administra un sistema distribuido sin guardias.
- La lógica transversal (correlación, errores, autenticación, Outbox) se repite en cada servicio; ver ADR-020.

## Evidencia

- ServiceRequest, Catalog e Identity implementados con bases separadas y comunicación por eventos (`catalog.category-changed`, `service-request.created`), con pruebas de integración contra PostgreSQL y Kafka reales.
- Pendiente: POC-BE-001 de punta a punta entre .NET y Spring Boot (`docs/architecture/poc/`).

## Trazabilidad

- SAD: secciones 4.2, 4.3 y 6; drivers D1, D2 y D6.
- SDD: vista lógica y C4 nivel 2.
- Relacionados: ADR-006, ADR-007, ADR-011, ADR-012, ADR-013, ADR-014, ADR-017.
