# Matriz de lo modelado frente a lo real

**Tarea:** SCRUM-697 (historia SCRUM-696, alinear el modelado con la implementación final)
**Fecha de corte:** 11 de noviembre de 2026

El profesor pidió que la arquitectura mostrada refleje el código real y preguntó qué servicios estaban implementados. Esta matriz recorre cada elemento del modelo C4 (`diagrams/c4/quickpatch.dsl`), del SAD y del SDD, y le asigna un estado verificado. SCRUM-698 corrige los documentos y diagramas a partir de ella.

**Estados:** **Implementado** (hay código en `develop`) · **Desplegado QA** y **Desplegado producción** (corre en el k3s o en el Nginx de ese ambiente) · **Planeado** (diseñado, sin código) · **Eliminado** (estuvo en el modelo y ya no aplica).

**Fuentes:** las VM de cada pieza salen de INFRASTRUCTURE 2.1 y 3; el código de `develop` de cada repositorio; para las versiones desplegadas, el Documento de Infraestructura 4.16 (SCRUM-694, quickpatch#275: `kubectl` de solo lectura del 10 de noviembre) y, para los frontends en producción, el cierre de SCRUM-641 (quickpatch-web#34 y quickpatch-mobile#56).

## Contenedores de QUICKPATCH

| Elemento | Implementado | QA | Producción | Estado | Evidencia |
|---|---|---|---|---|---|
| App móvil (Flutter) | Sí | APK `v0.6.0-qa` | APK `v0.5.4` | Implementado y desplegado en los dos ambientes | INFRA 4.16; SCRUM-641 |
| Panel web (Angular) | Sí | `release/0.7.0` | `v0.5.5` | Implementado y desplegado en los dos ambientes. **Discrepancia:** INFRA 4.3 todavía dice «página provisional» en producción, y SCRUM-694 no lo verificó | SCRUM-641 (panel verificado en producción el 4-nov); INFRA 4.16 |
| API Gateway (Nginx) | Sí | Sí, VM2 | Sí, VM3 | Implementado y desplegado | ADR-028 |
| Identity | Sí | 0.10.1 | 0.8.1 | Implementado y desplegado; en QA está la 0.10.x (contraseña cifrada, SCRUM-644; reputación en el panel, SCRUM-642; correlación de `quickpatch-shared-dotnet`, ADR-020), todavía no en producción | INFRA 4.16; CI de `release/0.10.1` del 11-nov |
| Actors | **No**: solo `Program.cs`, sin lógica | No | No | **Planeado** (esqueleto). `db_actors` existe y nadie la usa | `codigo/antes/README.md`; SAD 4.2.2 |
| Catalog | Sí | 0.4.3 | 0.4.1 | Implementado y desplegado; la 0.4.x (refactor SCRUM-651 y código compartido de ADR-020) está solo en QA | INFRA 4.16; CI del 11-nov |
| ServiceRequest | Sí | 0.12.2 | 0.11.2 | Implementado y desplegado; la 0.12.x (con el refactor SCRUM-652 y el código compartido de ADR-020) está solo en QA | INFRA 4.16; CI del 11-nov |
| Matching | Sí | 0.6.2 | 0.6.1 | Implementado y desplegado; la 0.6.2 (refactor SCRUM-653) está solo en QA | INFRA 4.16; CI del 11-nov |
| Ranking | Sí | 0.1.2 | 0.1.0 | Implementado y desplegado; la 0.1.x (refactor SCRUM-654 y código compartido de ADR-020) está solo en QA | INFRA 4.16; CI del 11-nov |
| Payments | Sí | 0.3.2 | 0.3.0 | Implementado y desplegado, con la pasarela **simulada**; la 0.3.x (refactor SCRUM-655 y código compartido de ADR-020) está solo en QA | INFRA 4.16; CI del 11-nov; ADR-009 modificado |
| Communication | Sí | 0.3.4 | 0.3.3 | Implementado y desplegado; la 0.3.4 (correlación de `quickpatch-shared-dotnet`, ADR-020) está solo en QA | INFRA 4.16; CI del 11-nov |
| Apache Kafka (KRaft) | — | VM7 | VM6 | Desplegado | ADR-006, ADR-022 |
| Redis | — | VM5 | VM4 | Desplegado; solo el candado de las cotizaciones | ADR-022; DSL |
| Garage (S3) | — | VM7 | VM6 | Desplegado; evidencias y respaldos | ADR-016 |
| Geocodificador (Nominatim, Bogotá) | — | VM5 | VM4 | Desplegado | ADR-024; SCRUM-520; INFRA 2.1 |
| PostgreSQL + PostGIS | — | VM5 | VM4 | Desplegado; 8 bases, 7 en uso | ADR-014 |

Las versiones de QA que no están en producción (Identity 0.10.1, Catalog 0.4.3, ServiceRequest 0.12.2, Matching 0.6.2, Ranking 0.1.2, Payments 0.3.2, Communication 0.3.4 y el panel 0.7.0; desplegadas en QA el 11 de noviembre) se promueven solo por `release/*` → `main`, después de pasar QA (ADR-022, RNF-08). La traza la verifica SCRUM-672.

## Sistemas externos y de soporte

| Elemento | Estado | Nota |
|---|---|---|
| Pasarela de pagos PCI-DSS | **Planeado** | El MVP cobra con `SimulatedPaymentProvider` detrás del puerto `IPaymentProvider` (ADR-009 modificado). Las relaciones con la pasarela ya están punteadas como «Planeado» en el DSL |
| Receptor de webhooks del PSP (componente de Payments) | **Planeado** | Depende de la pasarela certificada |
| Observabilidad (Prometheus, Loki, Grafana) | Desplegado en VM1 | La consulta el equipo desde su navegador (SCRUM-674, quickpatch#276) |
| GitHub (repositorios, Actions, GHCR) | En uso | 14 repositorios (cifras canónicas; el 14 es `quickpatch-shared-dotnet`, ADR-020) |

## Componentes

| Elemento | Estado | Nota |
|---|---|---|
| Componentes de Identity, Catalog, ServiceRequest, Matching, Ranking, Payments y Communication | Implementados | Nombres del código de `develop`; los de Catalog, ServiceRequest, Matching, Ranking y Payments se actualizaron tras el refactor (SCRUM-678, quickpatch#283). Identity y Communication esperan SCRUM-650 y 656 |
| Componentes de Actors (API, proveedores, aliados, clientes, persistencia) | **Planeado** | Ya etiquetados «Planeado» en el DSL |

## Eventos (topics de Kafka)

Los 20 topics de `quickpatch-kafka` tienen productor en el código. Todos tienen al menos un consumidor, salvo `service-request.started`, que ServiceRequest publica y ningún servicio consume hoy.

| Topic | Servicios que lo usan en `develop` |
|---|---|
| `service-request.created` | service-request (productor), matching, communication |
| `catalog.category-changed` | catalog (productor), service-request |
| `technician.registered` | identity (productor), matching, payments, communication |
| `technician.verification-changed` | identity (productor), matching, communication |
| `matching.offer-created` | matching (productor), communication |
| `matching.technician-assigned`, `.no-technician-available`, `.search-resumed` | matching (productor), service-request |
| `service-request.status-changed` | service-request (productor), communication |
| `service-request.cancelled` | service-request (productor), matching |
| `service-request.quoted`, `.quote-accepted`, `.quote-rejected` | service-request (productor), communication |
| `service-request.started` | service-request (productor); **sin consumidor** |
| `service-request.completed` | service-request (productor), matching, payments |
| `payment.approved`, `payment.rejected` | payments (productor), service-request |
| `service-request.rated` | service-request (productor), ranking |
| `ranking.technician-reputation-changed` | ranking (productor), identity |
| `tenant.status-changed` | identity (productor), service-request |

## Qué corrige SCRUM-698 con esta matriz

1. Que Actors no se presente como implementado en ningún diagrama ni diapositiva. El SAD 4.2.2 y la vista de contenedores ya lo hacen bien; falta revisar la presentación y los textos que hablan de «8 microservicios implementados».
2. Que la pasarela certificada y el receptor de webhooks sigan como «Planeado», y que el pago se describa como simulado.
3. Que la sección 4.3 del Documento de Infraestructura muestre los frontends promovidos en SCRUM-641; lo coordina Sebastián (SCRUM-694).
4. Que `service-request.started` se documente como publicado sin consumidor, o que se defina su consumidor, en el SDD 8.6 y el DD.
5. Que ninguna diapositiva muestre en producción las versiones que solo están en QA (las de la nota bajo la tabla de contenedores).
