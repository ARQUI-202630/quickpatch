# Diagramas C4: Contexto & Contenedores — SCRUM-575/578

**Documento:** SCRUM-575/578  
**Versión:** 1.0  
**Fecha:** 2026-10-31  
**Scope:** Diagramas C4 de contexto del sistema y contenedores (servicios, BD, cache)

---

## 1. Diagrama de Contexto C4 Nivel 1

QUICKPATCH y sus actores externos.

```mermaid
graph TB
    subgraph "QUICKPATCH Platform"
        QP["🏢 QUICKPATCH<br/>Multi-tenant SaaS<br/>Technical Services"]
    end
    
    subgraph "Usuarios"
        Client["👤 Cliente<br/>(hogar o empresa)"]
        Tech["👨‍🔧 Técnico"]
        Provider["🏭 Proveedor<br/>(técnicos)"]
        Admin["👔 Admin Plataforma"]
    end
    
    subgraph "Sistemas Externos"
        Gateway["🔐 API Gateway<br/>Reverse Proxy<br/>(Nginx/Traefik)"]
        Payment["💳 Pasarela de Pago<br/>(simulada MVP)"]
        SMS["📱 SMS Gateway<br/>(ADR-024: no en MVP)"]
        Email["✉️ Email Service<br/>(ADR-024: no en MVP)"]
        Geo["🗺️ Nominatim<br/>Geocoding"]
    end
    
    Client -->|"REST API<br/>JWT"| Gateway
    Tech -->|"REST API<br/>JWT"| Gateway
    Provider -->|"REST API<br/>JWT"| Gateway
    Admin -->|"REST API<br/>JWT"| Gateway
    
    Gateway -->|"Enruta a<br/>servicios"| QP
    
    QP -->|"Paga"| Payment
    QP -->|"Geocodifica"| Geo
    QP -->|"Futuro: SMS"| SMS
    QP -->|"Futuro: Email"| Email
    
    style QP fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    style Gateway fill:#fff3e0,stroke:#f57c00
    style Payment fill:#f3e5f5,stroke:#7b1fa2
    style Geo fill:#e8f5e9,stroke:#388e3c
```

---

## 2. Diagrama de Contenedores C4 Nivel 2

Microservicios, BD, broker de mensajes.

```mermaid
graph TB
    subgraph "Load Balancer"
        LB["⚖️ Nginx/HAProxy"]
    end
    
    subgraph "API Gateway (VM1)"
        GW["API Gateway<br/>(Nginx + Spring Cloud<br/>o Kong)"]
    end
    
    subgraph "Microservicios (VM2, K3s)"
        IS["🔑 Identity Service<br/>(.NET 10)<br/>--- <br/>Puerto: 5001"]
        SR["📋 ServiceRequest Service<br/>(.NET 10)<br/>--- <br/>Puerto: 5002"]
        QT["💰 Payments Service<br/>(.NET 10)<br/>--- <br/>Puerto: 5003"]
        CTG["🏷️ Catalog Service<br/>(.NET 10)<br/>--- <br/>Puerto: 5004"]
        MT["🎯 Matching Service<br/>(Java 25 Spring Boot)<br/>--- <br/>Puerto: 8080"]
        RK["⭐ Ranking Service<br/>(.NET 10)<br/>--- <br/>Puerto: 5005"]
        CM["💬 Communication Service<br/>(.NET 10)<br/>--- <br/>Puerto: 5006"]
        BZ["📦 Buzón Service<br/>(futuro)<br/>--- <br/>Puerto: 5007"]
    end
    
    subgraph "Datos (PostgreSQL)"
        DB["🗄️ PostgreSQL<br/>+ PostGIS<br/>-- <br/>8 BD por tenant<br/>(RLS)"]
    end
    
    subgraph "Caché & Almacenamiento"
        Redis["⚡ Redis<br/>(cache)<br/>-- <br/>Sesiones, outbox<br/>staging"]
        S3["📁 Garage/MinIO<br/>(evidencia fotográfica)<br/>-- <br/>Imágenes servicios"]
    end
    
    subgraph "Event Broker"
        Kafka["📨 Apache Kafka<br/>-- <br/>1 nodo<br/>3 particiones<br/>(R10, ADR-006)"]
    end
    
    LB -->|"HTTPS"| GW
    GW -->|"HTTP/gRPC"| IS
    GW -->|"HTTP/gRPC"| SR
    GW -->|"HTTP/gRPC"| QT
    GW -->|"HTTP/gRPC"| CTG
    GW -->|"HTTP/gRPC"| MT
    GW -->|"HTTP/gRPC"| RK
    GW -->|"HTTP/gRPC"| CM
    
    IS -->|"CRUD<br/>RLS"| DB
    SR -->|"CRUD<br/>RLS"| DB
    QT -->|"CRUD<br/>RLS"| DB
    CTG -->|"CRUD<br/>RLS"| DB
    MT -->|"CRUD<br/>RLS"| DB
    RK -->|"CRUD<br/>RLS"| DB
    CM -->|"CRUD<br/>RLS"| DB
    
    IS -->|"Sesiones<br/>JWT keys"| Redis
    SR -->|"Outbox staging"| Redis
    QT -->|"Outbox staging"| Redis
    
    SR -->|"Upload"| S3
    
    SR -->|"Publica"| Kafka
    MT -->|"Publica"| Kafka
    RK -->|"Publica"| Kafka
    IS -->|"Publica"| Kafka
    QT -->|"Publica"| Kafka
    CM -->|"Consume"| Kafka
    RK -->|"Consume"| Kafka
    MT -->|"Consume"| Kafka
    SR -->|"Consume"| Kafka
    
    style GW fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    style DB fill:#f3e5f5,stroke:#7b1fa2
    style Kafka fill:#e8f5e9,stroke:#388e3c,stroke-width:2px
    style Redis fill:#fffde7,stroke:#f9a825
    style S3 fill:#fce4ec,stroke:#c2185b
```

---

## 3. Diagrama de Despliegue (Infrastructure)

Máquinas virtuales, K3s, DNS, certificados.

```mermaid
graph TB
    subgraph "Internet"
        Users["👥 Usuarios"]
    end
    
    subgraph "Cloud / On-Premises"
        DNS["🔗 DNS<br/>quickpatch.internal"]
        
        subgraph "VM1 (Nginx/API Gateway)"
            GW["API Gateway<br/>Nginx/Traefik<br/>- Reverse proxy<br/>- Enrutamiento<br/>- Rate limit"]
        end
        
        subgraph "VM2 (K3s Cluster)"
            subgraph "Pods Microservicios"
                IS_POD["Identity<br/>ReplicaSet=1"]
                SR_POD["ServiceRequest<br/>ReplicaSet=2"]
                QT_POD["Payments<br/>ReplicaSet=1"]
                CTG_POD["Catalog<br/>ReplicaSet=1"]
                MT_POD["Matching<br/>ReplicaSet=2<br/>(Java)"]
                RK_POD["Ranking<br/>ReplicaSet=1"]
                CM_POD["Communication<br/>ReplicaSet=1"]
            end
            
            subgraph "Servicios K3s"
                Svc["Services<br/>(ClusterIP)"]
            end
            
            subgraph "Ingress"
                ING["Traefik IngressRoute<br/>- /api → Gateway<br/>- /admin → Panel<br/>- PathPrefix"]
            end
        end
        
        subgraph "VM3 (PostgreSQL)"
            PG["PostgreSQL 16<br/>+ PostGIS<br/>- RLS habilitado<br/>- 8 BD (1 por tenant)<br/>- Backups diarios"]
        end
        
        subgraph "VM4 (Redis)"
            REDIS["Redis 7<br/>- Sesiones<br/>- Outbox staging<br/>- TTL 24h"]
        end
        
        subgraph "VM5 (Kafka)"
            KAFKA["Kafka 3.x<br/>- 1 broker<br/>- 20 topics<br/>- Replication=1"]
        end
        
        subgraph "VM6-7 (Almacenamiento)"
            S3["MinIO/Garage<br/>- Evidencia fotográfica<br/>- Backup replicado"]
        end
        
        subgraph "Monitoreo & Logging"
            PROM["Prometheus<br/>(métricas)"]
            LOGS["ELK Stack<br/>(logs)"]
            ALERT["AlertManager<br/>(alertas)"]
        end
    end
    
    Users -->|"HTTPS:443"| DNS
    DNS -->|"A record"| GW
    
    GW -->|"HTTP:5001-5006"| ING
    ING -->|"Service Discovery"| Svc
    Svc -->|"TCP"| IS_POD
    Svc -->|"TCP"| SR_POD
    Svc -->|"TCP"| QT_POD
    Svc -->|"TCP"| CTG_POD
    Svc -->|"TCP"| MT_POD
    Svc -->|"TCP"| RK_POD
    Svc -->|"TCP"| CM_POD
    
    IS_POD -->|"5432"| PG
    SR_POD -->|"5432"| PG
    QT_POD -->|"5432"| PG
    CTG_POD -->|"5432"| PG
    MT_POD -->|"5432"| PG
    RK_POD -->|"5432"| PG
    CM_POD -->|"5432"| PG
    
    SR_POD -->|"6379"| REDIS
    IS_POD -->|"6379"| REDIS
    QT_POD -->|"6379"| REDIS
    
    SR_POD -->|"9092"| KAFKA
    MT_POD -->|"9092"| KAFKA
    RK_POD -->|"9092"| KAFKA
    CM_POD -->|"9092"| KAFKA
    
    SR_POD -->|"S3 API"| S3
    
    IS_POD -->|"Exporta métricas"| PROM
    SR_POD -->|"Exporta métricas"| PROM
    MT_POD -->|"Exporta métricas"| PROM
    
    SR_POD -->|"Logs"| LOGS
    MT_POD -->|"Logs"| LOGS
    CM_POD -->|"Logs"| LOGS
    
    PROM -->|"Evalúa reglas"| ALERT
    ALERT -->|"Notificación"| Users
    
    style GW fill:#fff3e0,stroke:#f57c00
    style PG fill:#f3e5f5,stroke:#7b1fa2
    style KAFKA fill:#e8f5e9,stroke:#388e3c
    style REDIS fill:#fffde7,stroke:#f9a825
    style S3 fill:#fce4ec,stroke:#c2185b
    style PROM fill:#e0f2f1,stroke:#00897b
    style LOGS fill:#e0f2f1,stroke:#00897b
```

---

## 4. Flujo de Request Extremo a Extremo

Cliente → API Gateway → Microservicio → BD → Kafka → Otros servicios.

```mermaid
sequenceDiagram
    participant Client as Cliente/App
    participant DNS as DNS
    participant LB as Load Balancer
    participant GW as API Gateway
    participant SR as ServiceRequest<br/>(Pod en K3s)
    participant PG as PostgreSQL
    participant Redis as Redis
    participant Kafka as Kafka
    participant CM as Communication<br/>(Pod en K3s)
    
    Client->>DNS: resolve quickpatch.internal
    DNS->>Client: IP del Gateway
    
    Client->>LB: POST /api/v1/service-requests<br/>(HTTPS)
    LB->>GW: Enruta a servicio correcto
    
    GW->>SR: POST /v1/service-requests<br/>(auth: JWT)
    SR->>SR: Valida JWT, extrae tenant_id
    
    SR->>PG: INSERT service_requests<br/>(RLS: tenant_id)
    PG->>SR: id generado
    
    SR->>Redis: INSERT outbox_events<br/>(event, status=pending)
    
    SR->>Client: 201 Created
    Note over SR: Publicador async
    SR->>Kafka: service-request.created
    
    Kafka->>CM: event received
    CM->>CM: Procesa evento
    CM->>CM: Publica notificación<br/>(WebSocket, buzón)
```

---

## 5. Arquitectura de Red y Seguridad

```mermaid
graph TB
    Internet["🌍 Internet"]
    
    subgraph "DMZ"
        GW["🔐 API Gateway<br/>(Nginx/Traefik)<br/>- TLS 1.3<br/>- Rate limit<br/>- CORS"]
    end
    
    subgraph "Private Network"
        K3s["K3s Cluster<br/>(Internal)"]
        PG[("PostgreSQL<br/>(Internal)")]
        KAFKA["Kafka<br/>(Internal)"]
        REDIS["Redis<br/>(Internal)"]
    end
    
    subgraph "Storage"
        S3["MinIO<br/>(Backup)"]
    end
    
    Internet -->|"HTTPS:443<br/>Certificado TLS"| GW
    GW -->|"HTTP<br/>Intra-red"| K3s
    
    K3s -->|"5432"| PG
    K3s -->|"6379"| REDIS
    K3s -->|"9092"| KAFKA
    K3s -->|"S3 API"| S3
    
    Note over GW: Public<br/>Nginx/Traefik<br/>Rate limit<br/>Auth mínima
    Note over K3s: Private<br/>Solo desde GW<br/>Service Mesh (futuro)
    Note over PG: Private<br/>RLS (multi-tenancy)<br/>Backup automático
    
    style GW fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    style K3s fill:#e3f2fd,stroke:#1976d2
    style PG fill:#f3e5f5,stroke:#7b1fa2
    style KAFKA fill:#e8f5e9,stroke:#388e3c
```

---

## 6. Notas de Despliegue

### Versioning & Rollouts
- Microservicios usan semver: v1.0.0, v1.1.0, etc.
- K3s: rolling update con `maxSurge=1, maxUnavailable=0`.
- Blue-green deployment para cambios críticos.

### Escalabilidad
- **ServiceRequest:** ReplicaSet=2 (alto volumen de solicitudes).
- **Matching:** ReplicaSet=2 (búsqueda intensiva).
- **Identity:** ReplicaSet=1 (auth crítico, bajo volumen).

### Monitoreo
- Prometheus scrape de métricas cada 15s.
- Alertas: pod down, BD latencia >100ms, Kafka lag.

### Disaster Recovery
- PostgreSQL: backups diarios, PITR 7 días.
- Kafka: replication factor=1 (no redundancia en MVP per R10).
- MinIO: replicado en 2 nodos.

---

**Referencias:**
- SAD (sección 4.2: microservicios, sección 9: infraestructura)
- INFRASTRUCTURE.md (DR, backups, monitoring)
- ADR-009 (Pasarela), ADR-015 (QA), ADR-024 (Email/SMS fuera MVP)

