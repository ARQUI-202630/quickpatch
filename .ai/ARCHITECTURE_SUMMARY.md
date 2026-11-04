# QUICKPATCH — Resumen arquitectónico para agentes

## Fuentes

- SRS: `docs/requirements/SRS.md`
- SAD: `docs/architecture/SAD.md`
- SDD: `docs/architecture/SDD.md`
- DD: `docs/design/DD.md`
- Infraestructura: `docs/infrastructure/INFRASTRUCTURE.md`
- ADR tecnológica: `docs/architecture/adr/ADR-012-stack-tecnologico-polyglot.md`
- Índice de ADR: `docs/architecture/adr/README.md` (leer solo el ADR relacionado con la tarea)

## Canales

- Admin: Angular Web.
- Cliente/técnico: Flutter Mobile.

## Servicios

| Servicio | Stack |
|---|---|
| Identity | ASP.NET Core |
| Actors | ASP.NET Core |
| Catalog | ASP.NET Core |
| ServiceRequest | ASP.NET Core |
| Matching | Java + Spring Boot |
| Ranking | ASP.NET Core |
| Payments | ASP.NET Core |
| Communication | ASP.NET Core |

## Integración

### REST
Interacción síncrona cuando el usuario inicia una acción y necesita la respuesta en ese momento. Desde ADR-025, el API Gateway tiene REST principal solo hacia **Identity, ServiceRequest y Payments**. Actors, Catalog, Matching, Ranking y Communication se integran por Kafka. Excepciones explícitas, listadas en el ADR: acciones del técnico en Matching (disponibilidad, cobertura, ofertas), administración del catálogo, y buzón y WebSocket de Communication. Una ruta nueva va a uno de los tres servicios REST; si no, se agrega como excepción al ADR-025 con su motivo. Las categorías y las localidades las sirve ServiceRequest desde sus réplicas (`/v1/service-requests/categories` y `/localities`).

### Kafka
Hechos de dominio y coordinación asíncrona, con un topic por tipo de evento (ADR-006); las familias del diagrama (`service-request.events`, …) son el prefijo del topic. Los servicios no se llaman entre sí por REST para cumplir su función. Usar eventos con semántica de dominio, no como reemplazo de una llamada REST.

### Datos
PostgreSQL/PostGIS. Cada servicio mantiene ownership lógico de sus datos.

### Infraestructura
8 microservicios en VM3/k3s; resto de roles distribuidos entre las 7 VMs según `INFRASTRUCTURE.md`.

## Restricciones

- multi-tenancy;
- tokenización y PCI-DSS;
- 7 VMs;
- infraestructura propia;
- Bogotá como alcance MVP;
- contratos explícitos;
- tiempo académico limitado.
