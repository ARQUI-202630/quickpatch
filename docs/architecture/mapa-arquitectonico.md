# Mapa arquitectónico: arquitectura documentada frente a la implementada

| Campo | Valor |
|---|---|
| **Historia** | SCRUM-570 (subtarea SCRUM-571) |
| **Fecha de la revisión** | 26 de octubre de 2026 |
| **Fuentes** | SAD V2.38 (secciones 4 y 5), SDD (10.3.1 y figura 5), DD, ADR-003 a ADR-028, `develop` de los 12 repositorios y el Documento de Infraestructura V4 (sección 4.3, estado medido el 26 de octubre) |
| **Responsable** | Juan Diego Rojas |

## 1. Cómo se lee

El profesor preguntó en la revisión del Sprint 4 si al entrar al repositorio se ve lo que muestran los diagramas. Este mapa responde elemento por elemento con uno de tres estados:

- **Implementado:** existe en `develop` como lo describe el diseño.
- **Diferente al diseño:** existe, pero no como lo dice el documento.
- **Pendiente:** está diseñado y todavía no existe.

Cada diferencia termina en una decisión de la sección 9: **corregir el código**, **corregir el documento** o **registrar un ADR**. El mapa se revisa antes de planear cada sprint; las cifras de despliegue son las del Documento de Infraestructura, sección 4.3.

## 2. Microservicios (SAD 4.2.2)

| Servicio | Diseño | Código en `develop` | QA | Producción | Estado | Diferencia |
|---|---|---|---|---|---|---|
| Identity | Auth, Tenants, Users | Auth, usuarios, empresas, técnicos, plataforma; equipo del proveedor (`/v1/providers`) | Desplegado | Desplegado | Implementado | El equipo del proveedor vive en Identity y no en Actors: ya documentado en DD P-02 (D-05) |
| Actors | Suppliers, Allies, Clients | Esqueleto (salud y pruebas base) | No desplegado | No desplegado | Pendiente | Su función del MVP (RF-16) la cubre Identity (D-05) |
| Catalog | Especialidades | Categorías y su administración; publica `catalog.category-changed` | Desplegado | Desplegado | Implementado | — |
| Matching (Java) | Matching, CoverageZone | Búsqueda, ofertas, disponibilidad y cobertura; réplica de técnicos | Desplegado | Desplegado | Diferente al diseño | No consume `catalog.category-changed` (D-03); expone `/v1/localities`, obsoleta por ADR-025 (D-02) |
| ServiceRequest | Cotización → prestación → evaluación | Solicitudes, cotizaciones, evidencia, cancelación, réplicas de categorías y localidades, vencimientos | Desplegado | Desplegado | Implementado (evaluación pendiente) | Falta la calificación (RF-12, ADR-027, D-07) |
| Ranking | Reputación del técnico | Esqueleto | No desplegado | No desplegado | Pendiente | ADR-027 define cómo se construye (D-07) |
| Payments | Payments, Billing, Payroll-lite | Pago con pasarela simulada (ADR-009) y comprobante | Desplegado | **No desplegado** | Diferente al diseño | Faltan pagos recibidos (RF-25) y el pago de la empresa en QA (RF-23, D-08); no está en producción (D-10) |
| Communication | Notificaciones y chat (ADR-026) | Canal en tiempo real, buzón y chat | Desplegado | **No desplegado** | Implementado en QA | No está en producción (D-10) |

## 3. Clientes y gateway

| Elemento | Diseño | Implementado | Estado | Diferencia |
|---|---|---|---|---|
| App Flutter | Usuarios operativos (SAD 4.2.1) | `quickpatch-mobile`, APK en GitHub Releases (`v0.5.1-qa`) | Diferente al diseño | Pide categorías a Catalog y localidades a Matching, no a ServiceRequest (D-02). Llama a `/v1/payments/received`, que no existe (D-08) |
| Panel Angular | Solo administradores, sin sitio público (FA2) | `quickpatch-web`, con una página de presentación y descarga del APK | Diferente al diseño | Pide categorías a Catalog (D-02). La página de presentación no está en el SAD (D-06) |
| API Gateway | Nginx por ambiente detrás de la entrada TLS de VM1 (ADR-028) | `quickpatch-api-gateway/nginx/`; el enrutamiento por ruta lo hacen los `Ingress` de cada servicio en Traefik | Implementado | — |
| Canal en tiempo real | WebSocket `/v1/realtime` a Communication (ADR-023) | `asyncapi/realtime.v1.yaml` y Communication | Implementado | — |

## 4. Rutas REST frente a ADR-025

| Servicio | Rutas en el gateway (`Ingress`) | ADR-025 | Estado |
|---|---|---|---|
| Identity | `/v1/auth`, `/v1/users`, `/v1/companies`, `/v1/providers`, `/v1/admin/technicians`, `/v1/platform` | REST principal | Implementado |
| ServiceRequest | `/v1/service-requests`, `/v1/technicians/me/service-requests`, `/v1/admin/service-requests`, `/v1/platform/service-requests` | REST principal | Implementado |
| Payments | `/v1/service-requests/{id}/payment`, `/v1/payments` | REST principal | Implementado |
| Catalog | `/v1/catalog` | Solo la administración es excepción; `GET /v1/catalog/categories` es obsoleta | Diferente al diseño (D-02) |
| Matching | `/v1/technicians/me` (disponibilidad y cobertura), `/v1/matching` (ofertas), `/v1/localities` | Acciones del técnico son excepción; `/v1/localities` es obsoleta | Diferente al diseño (D-02) |
| Communication | `/v1/notifications`, `/v1/realtime` | Excepción (buzón y canal) | Implementado |

La única llamada REST entre servicios es ServiceRequest → Identity (`GET /internal/v1/users`, `identity-internal.v1.yaml`): de solo lectura, tolera fallos y no pasa por el gateway. ADR-025 la permite de forma explícita, así que no es una diferencia.

## 5. Eventos de Kafka

Los 17 topics de `quickpatch-kafka/topics/topics.yaml` existen en el código con el productor y los consumidores declarados, salvo uno:

| Topic | Productor | Consumidores declarados | Consumidores en el código | Estado |
|---|---|---|---|---|
| `service-request.created` | ServiceRequest | Matching, Communication | Matching, Communication | Implementado |
| `service-request.status-changed` | ServiceRequest | Communication | Communication (aviso, buzón y cierre del chat) | Implementado |
| `service-request.cancelled` | ServiceRequest | Matching | Matching | Implementado |
| `service-request.quoted`, `quote-accepted`, `quote-rejected` | ServiceRequest | Communication | Communication | Implementado |
| `service-request.started` | ServiceRequest | — | — | Implementado (sin consumidores, como dice el topic) |
| `service-request.completed` | ServiceRequest | Matching, Payments | Matching, Payments | Implementado |
| `catalog.category-changed` | Catalog | ServiceRequest, Matching | **Solo ServiceRequest** | Diferente al diseño (D-03) |
| `technician.registered`, `technician.verification-changed` | Identity | Matching, Communication | Matching, Communication | Implementado |
| `matching.offer-created` | Matching | Communication | Communication | Implementado |
| `matching.technician-assigned`, `no-technician-available`, `search-resumed` | Matching | ServiceRequest | ServiceRequest | Implementado |
| `payment.approved`, `payment.rejected` | Payments | ServiceRequest | ServiceRequest | Implementado |
| `service-request.rated`, `ranking.technician-reputation-changed` | ServiceRequest, Ranking | Ranking, Identity | — | Pendiente (ADR-027, D-07) |

El SAD 4.2.4 todavía nombra los eventos como `SERVICE_REQUESTED`, `SERVICE_EVALUATED` y `PAYMENT_APPROVED`, y dice que Communication consume `PAYMENT_APPROVED`. En el código los nombres son los de la tabla, y el aviso del pago sale de `service-request.status-changed` (D-01).

## 6. Patrones transversales

| Patrón | Dónde aplica | En el código | Estado |
|---|---|---|---|
| Outbox (ADR-007) | Servicios que publican | Identity, Catalog, ServiceRequest, Payments y Matching | Implementado |
| Idempotencia por `eventId` (ADR-007) | Servicios que consumen | ServiceRequest, Payments, Matching y Communication | Implementado |
| RLS por tenant (ADR-005) | Todas las bases | Políticas en Identity, Catalog, ServiceRequest, Payments, Communication y Matching; `verificar-rls.yml` | Implementado |
| JWT RS256 validado en cada servicio (ADR-018) | Todos los servicios con REST | Los seis servicios desplegados | Implementado |
| Réplicas locales por eventos (ADR-017) | ServiceRequest (categorías), Matching (técnicos) | Sí | Implementado; falta la de categorías en Matching (D-03) |
| Convención de paquetes (SDD 10.3.1) | Todos los servicios | Identity, Catalog, ServiceRequest y Payments cumplen | Diferente en Communication y Matching (SCRUM-588) |

## 7. Datos

| Elemento | Diseño | Implementado | Estado | Diferencia |
|---|---|---|---|---|
| PostgreSQL + PostGIS | Una base por servicio (ADR-014) | Las 8 bases con roles `_migrator` y `_app` en los dos ambientes | Implementado | Las de Actors y Ranking están vacías |
| Redis | "Caché y colas de corta duración" (SAD 4.2.3) | Solo ServiceRequest, para coordinar los vencimientos (DD RN-Q6). Ningún servicio lo usa como caché | Diferente al diseño (D-04) | El SAD promete una caché que no existe |
| Garage (ADR-016) | Evidencias y respaldos de PostgreSQL | Bucket `evidencias` (ServiceRequest) y respaldo diario a `backups-postgres` | Implementado | — |
| Nominatim (ADR-024) | Uno por ambiente, con el mapa de Bogotá | En QA (VM5) | Pendiente en producción (D-10) | VM4 todavía no lo tiene (SCRUM-520) |

## 8. Infraestructura (SAD 5)

| Elemento | Diseño | Implementado | Estado | Diferencia |
|---|---|---|---|---|
| Reparto de VMs (ADR-022) | 3 de producción, 3 de QA y VM1 de herramientas | Aplicado el 7 de octubre | Implementado | El SAD 5.1 todavía dice "implementación en curso (SCRUM-334)" (D-09) |
| Gateway por ambiente (ADR-028) | Nginx en VM3 y VM2, TLS en VM1 | En los dos ambientes | Implementado | — |
| k3s con los 8 servicios | 8 servicios en VM3 y en VM2 | QA: 6. Producción: 4 (sin Payments ni Communication). Actors y Ranking en ninguno | Pendiente (D-10) | — |
| Kafka y topics | Los topics se crean de forma explícita en cada ambiente | QA: 17 topics. Producción: 2 | Pendiente en producción (D-10) | — |
| Observabilidad | Prometheus, Loki y Grafana en VM1 | Desplegada | Implementado | — |
| CI/CD | Pipeline por repositorio, QA antes de producción | Pipeline por repositorio; la prueba de humo bloquea la promoción (SCRUM-505) | Implementado | — |

## 9. Diferencias y decisiones

| ID | Diferencia | Decisión | Responsable | Tarea |
|---|---|---|---|---|
| D-01 | SAD 4.2.4 usa nombres de evento viejos (`SERVICE_REQUESTED`, `SERVICE_EVALUATED`, `PAYMENT_APPROVED`) y un consumidor que no existe | Corregir el documento con los nombres de `topics.yaml` | Juan Diego | SCRUM-544 |
| D-02 | La app y el panel piden categorías a Catalog y localidades a Matching; ADR-025 las dejó obsoletas | Corregir el código: fusionar quickpatch-mobile#33 y quickpatch-web#21 y después retirar las dos rutas del gateway | Juan Diego (PR), Sebastián (rutas) | ADR-025 |
| D-03 | Matching no consume `catalog.category-changed`: las ofertas salen con `categoryName` en null, aunque el DD dice que sale de su réplica | Corregir el código: réplica de categorías en Matching | Backend (Matching) | Por crear |
| D-04 | El SAD presenta Redis como caché y colas; solo se usa para coordinar los vencimientos de ServiceRequest | Corregir el documento: Redis como coordinación temporal; la caché no está en el MVP | Juan Diego | SCRUM-544 |
| D-05 | El equipo del proveedor (RF-16) vive en Identity, no en Actors | Ya documentado en DD P-02. Marcar Actors como planeado en los diagramas | Juan Diego | SCRUM-544 y SCRUM-549 |
| D-06 | El panel tiene una página pública de presentación con la descarga del APK; el SAD 4.2.1 dice que el panel no tiene sitio público | Corregir el documento: página de presentación sin datos ni indexación, pedida en la revisión del Sprint 4 (SCRUM-628) | Juan Diego | SCRUM-544 |
| D-07 | La calificación y la reputación no existen (RF-12, AC9-E2) | ADR-027 (quickpatch#157); contratos de José e implementación del Backend | José, Juan Diego | SCRUM-497, SCRUM-85, SCRUM-498 |
| D-08 | La app llama a `/v1/payments/received`, que Payments no tiene (RF-25); el pago de la empresa (RF-23) no está en QA | Corregir el código: contrato y endpoint de pagos recibidos; release de quickpatch-payments#11 y quickpatch-mobile#41 | José, Angy, Miguel, Juan Diego | SCRUM-500 a 502; SCRUM-118, 119 y 496 |
| D-09 | El SAD 5.1 dice que ADR-022 está "en curso" | Corregir el documento: aplicado el 7 de octubre | Juan Diego | SCRUM-544 |
| D-10 | Producción no tiene Payments, Communication, Nominatim ni los topics del incremento | Corregir la infraestructura antes de promover el MVP | Sebastián | SCRUM-518 a 521 |
| D-11 | Actors y Ranking no están desplegados en ningún ambiente | Ranking se despliega con ADR-027; Actors queda planeado y marcado así en los diagramas | Sebastián, Juan Diego | SCRUM-544 y SCRUM-549 |

Los diagramas del SAD y del SDD deben marcar como **planeado** (borde punteado o gris, como ya hace la figura 5 del SDD) a Actors, Ranking, la calificación y los pagos recibidos, para no confundirlos con lo implementado (SCRUM-549 y SCRUM-550).
