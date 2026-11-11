# Diagramas C4: contexto, contenedores y despliegue — SCRUM-575/578

**Versión:** 2.0
**Fecha:** 2026-11-02
**Alineado con:** `docs/architecture/diagrams/c4/quickpatch.dsl`, Documento de Infraestructura (secciones 2.1, 3.3, 3.4 y 4.3), ADR-016, ADR-022, ADR-023, ADR-024 y ADR-028.

**El SDD (secciones 4, 5 y 9; figuras 2, 3, 30 y 31) y `quickpatch.dsl` mandan.** Este documento es solo un resumen de las vistas C4 de nivel 1 y 2 y del reparto de las VMs; si algo difiere, vale el SDD.

---

## 1. Contexto (C4 nivel 1)

Las personas que usan QUICKPATCH y su único sistema externo de producción, la pasarela de pagos (RIE-01, R5, ADR-024). La geocodificación es propia (Nominatim dentro de las VMs) y el API Gateway es un contenedor de QUICKPATCH, no un sistema externo.

```mermaid
graph TB
    Cliente["Cliente"]
    Empresa["Empresa cliente"]
    Tecnico["Técnico"]
    Proveedor["Proveedor"]
    AdminT["Admin del tenant"]
    AdminP["Admin de plataforma"]

    QP["QUICKPATCH<br/>Plataforma multi-tenant de servicios técnicos"]
    Pasarela["Pasarela de pagos PCI-DSS<br/>(simulada en el MVP, ADR-009)"]

    Cliente -->|"Pide, sigue, paga y califica (app móvil)"| QP
    Empresa -->|"Pide y paga para sus sedes (app móvil)"| QP
    Tecnico -->|"Recibe ofertas, cotiza y ejecuta (app móvil)"| QP
    Proveedor -->|"Administra su equipo (app móvil)"| QP
    AdminT -->|"Aprueba técnicos y opera su tenant (panel web)"| QP
    AdminP -->|"Administra los tenants (panel web)"| QP
    QP -->|"Tokeniza y cobra"| Pasarela
```

Imagen formal: `docs/architecture/diagrams/c4/C4-02-Contexto.png`.

---

## 2. Contenedores (C4 nivel 2)

```mermaid
graph TB
    Mobile["App móvil<br/>(Flutter)"]
    Web["Panel web<br/>(Angular)"]
    GW["API Gateway<br/>Nginx (quickpatch-api-gateway)"]

    subgraph Servicios["Microservicios"]
        IS["Identity<br/>.NET 10"]
        CT["Catalog<br/>.NET 10"]
        SR["ServiceRequest<br/>.NET 10"]
        MT["Matching<br/>Java 25 + Spring Boot"]
        RK["Ranking<br/>.NET 10"]
        PY["Payments<br/>.NET 10"]
        CM["Communication<br/>.NET 10<br/>canal en tiempo real, buzón y chat"]
    end

    PG[("PostgreSQL + PostGIS<br/>una base por servicio (ADR-014)<br/>cada una con su outbox_events")]
    KF["Apache Kafka<br/>un topic por tipo de evento"]
    RD[("Redis<br/>candado de tareas programadas<br/>de ServiceRequest")]
    GA[("Garage (S3)<br/>evidencias y respaldos (ADR-016)")]
    NOM["Geocodificador<br/>Nominatim, solo Bogotá (ADR-024)"]

    Mobile -->|"HTTPS /api"| GW
    Web -->|"HTTPS /api"| GW
    Mobile -->|"WebSocket /api/v1/realtime"| GW
    GW -->|"HTTP, quita /api"| IS
    GW -->|"HTTP"| SR
    GW -->|"HTTP"| PY
    GW -->|"HTTP"| CM
    GW -->|"HTTP: /v1/catalog/admin/categories"| CT
    GW -->|"HTTP: disponibilidad, cobertura y ofertas"| MT

    IS --> PG
    CT --> PG
    SR --> PG
    MT --> PG
    RK --> PG
    PY --> PG
    CM --> PG

    IS -->|"technician.*, tenant.status-changed"| KF
    CT -->|"catalog.category-changed"| KF
    SR -->|"service-request.*"| KF
    MT -->|"matching.*"| KF
    RK -->|"ranking.technician-reputation-changed"| KF
    PY -->|"payment.*"| KF
    KF -->|"service-request.created, .cancelled y .completed,<br/>technician.registered y .verification-changed"| MT
    KF -->|"matching.technician-assigned, .no-technician-available<br/>y .search-resumed, payment.approved y .rejected,<br/>catalog.category-changed, tenant.status-changed"| SR
    KF -->|"service-request.rated"| RK
    KF -->|"ranking.technician-reputation-changed"| IS
    KF -->|"service-request.completed, technician.registered"| PY
    KF -->|"service-request.created, .status-changed, .quoted,<br/>.quote-accepted y .quote-rejected, matching.offer-created,<br/>technician.registered y .verification-changed"| CM

    SR -->|"candado"| RD
    SR -->|"fotos del servicio"| GA
    SR -->|"busca la dirección"| NOM
```

Notas:

- El gateway es un **Nginx** por ambiente (ADR-028). Según ADR-025, el REST principal va a Identity, ServiceRequest y Payments, con excepciones explícitas: las acciones del técnico en Matching (disponibilidad, cobertura y ofertas: `/v1/matching`, `/v1/technicians/me/availability` y `/coverage`), la administración del catálogo en Catalog (`/v1/catalog/admin/categories`) y, en Communication, el buzón (`/v1/notifications`), el canal en tiempo real (`/v1/realtime`) y el chat (`/v1/service-requests/{id}/messages`). Ranking no recibe REST.
- El cobro con la pasarela lo hace Payments con un adaptador simulado dentro del servicio (ADR-009), así que no hay flecha hacia un sistema externo en esta vista.
- **El buzón no es un servicio aparte:** vive dentro de Communication, junto con el canal en tiempo real y el chat (ADR-023, ADR-024, ADR-026).
- **El outbox es la tabla `outbox_events` de la base de cada servicio**, escrita en la misma transacción que el cambio (ADR-007). Redis no guarda outbox ni sesiones: hoy solo lo usa ServiceRequest como candado de sus tareas programadas.

Imagen formal: desde SCRUM-676 la vista está partida en `docs/architecture/diagrams/c4/C4-03a-Contenedores-Sincrono.png` (REST y datos) y `C4-03b-Contenedores-Eventos.png` (eventos).

---

## 3. Despliegue

La vista de despliegue por ambiente ya está en `develop` y es la referencia vigente:

- Producción: `docs/architecture/diagrams/c4/C4-06-Despliegue-Produccion.png`
- QA: `docs/architecture/diagrams/c4/C4-06-Despliegue-QA.png`

Reparto de las 7 VMs (ADR-022, Documento de Infraestructura 2.1):

|VM|Ambiente|Qué corre|
|---|---|---|
|VM1|Herramientas|Nginx :443 de entrada TLS que reenvía por nombre (`quickpatch.internal`, `qa.quickpatch.internal`, `grafana.quickpatch.internal`); runner de GitHub con kubectl y k6; Prometheus, Loki y Grafana de los dos ambientes|
|VM2|QA, aplicación|k3s de un nodo: Nginx del gateway :8080 con el panel, Traefik :30080 y los microservicios|
|VM3|Producción, aplicación|Igual que VM2|
|VM4|Producción, datos|PostgreSQL + PostGIS :5432, Redis :6379 y Nominatim :8088|
|VM5|QA, datos|Igual que VM4|
|VM6|Producción, mensajería y almacenamiento|Kafka :9092 y Garage :9000|
|VM7|QA, mensajería y almacenamiento|Igual que VM6|

```mermaid
graph TB
    VPN(["VPN de la universidad"])
    subgraph VM1["VM1 · Herramientas"]
        NGX["Nginx :443"]
        OBS["Prometheus, Loki, Grafana"]
        RUN["Runner, kubectl, k6"]
    end
    subgraph PROD["Producción"]
        VM3["VM3 · k3s<br/>gateway Nginx, panel, servicios"]
        VM4[("VM4 · PostgreSQL, Redis, Nominatim")]
        VM6["VM6 · Kafka y Garage"]
    end
    subgraph QA["QA"]
        VM2["VM2 · k3s<br/>gateway Nginx, panel, servicios"]
        VM5[("VM5 · PostgreSQL, Redis, Nominatim")]
        VM7["VM7 · Kafka y Garage"]
    end

    VPN -->|"443"| NGX
    NGX -->|"quickpatch.internal :8080"| VM3
    NGX -->|"qa.quickpatch.internal :8080"| VM2
    NGX -->|"grafana.quickpatch.internal"| OBS
    VM3 -->|"5432, 6379, 8088"| VM4
    VM3 -->|"9092, 9000"| VM6
    VM4 -.->|"respaldo diario :9000"| VM6
    VM2 -->|"5432, 6379, 8088"| VM5
    VM2 -->|"9092, 9000"| VM7
    RUN -->|"despliegue :6443"| VM3
    RUN -->|"despliegue :6443 y pruebas"| VM2
```

Los dos ambientes no se conectan entre sí; solo VM1 llega a ambos. Las 7 VMs envían métricas y logs a VM1 (no se dibujan para no cruzar todas las flechas). QA no tiene respaldo: sus datos son de prueba.

---

## 4. Flujo de una petición: crear una solicitud

```mermaid
sequenceDiagram
    participant App as App móvil
    participant E as Nginx VM1
    participant G as Gateway Nginx (VM3)
    participant SR as ServiceRequest (k3s)
    participant DB as db_service_request (VM4)
    participant K as Kafka (VM6)
    participant M as Matching (k3s)

    App->>E: POST /api/v1/service-requests (HTTPS, JWT)
    E->>G: reenvía por nombre
    G->>SR: POST /v1/service-requests (quita /api)
    SR->>SR: valida el JWT; tenant del token (RN-T3, DD 7.1)
    SR->>DB: lee tenant_status_replica (RN-T1)
    SR->>DB: INSERT service_requests + INSERT outbox_events (misma transacción, ADR-007)
    SR-->>App: 201 Created
    SR->>K: el publicador envía service-request.created
    K->>M: consume service-request.created
```

---

**Referencias:** Documento de Infraestructura (2.1, 3.3, 3.4, 4.3 y 10); ADR-007, ADR-014, ADR-016, ADR-022, ADR-023, ADR-024, ADR-025, ADR-026 y ADR-028; `quickpatch.dsl`.
