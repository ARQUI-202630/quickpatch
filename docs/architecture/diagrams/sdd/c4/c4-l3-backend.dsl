/*
 * QUICKPATCH — SDD · C4 nivel 3: componentes de ServiceRequest Service
 * Jira: SCRUM-299 (HU SCRUM-256). Se alinea con el C4 de contenedores (SDD 3.1.4).
 *
 * Contenedor elegido: ServiceRequest, porque es el del incremento del Sprint 3 (SCRUM-27,
 * creación de solicitud) y concentra las decisiones de diseño del backend: reglas de negocio
 * sobre una réplica local, máquina de estados, aislamiento por tenant con RLS, Transactional
 * Outbox y consumo idempotente de eventos. Los otros siete microservicios no se repiten aquí.
 *
 * Capas (SDD 4.1): API / Interface → Application → Domain; Infrastructure implementa
 * persistencia y mensajería. La tecnología de cada componente indica su capa.
 *
 * Fuentes: SDD 3.2.5, 4.1, 4.2 y 5.9; DD 5.5, 5.15 a 5.17, 7.4 (RN-SR1 a RN-SR11), 7.11 y 10;
 * quickpatch-contracts: openapi/service-request.v1.yaml, events/service-request.created.v1.json
 * y events/catalog.category-changed.v1.json.
 *
 * Alcance: solo los componentes que el incremento usa. Los consumidores de
 * matching.technician-assigned, matching.no-technician-available y payment.* (SDD 3.2.5) y los
 * endpoints de cotización, inicio, evidencia, cierre y calificación no tienen contrato todavía
 * y se agregarán cuando lo tengan.
 *
 * Multi-tenancy (DD 10.3): en las peticiones REST el tenant sale del JWT que propaga el API
 * Gateway; en el consumo de eventos, del tenantId del sobre. Nunca del cuerpo (RN-U3).
 */
workspace "QUICKPATCH — C4-L3 Backend" "Componentes de ServiceRequest Service para el incremento de Sprint 3." {

    model {
        clienteEmpresa = person "Cliente y empresa cliente" "Piden, siguen y pagan servicios."

        quickpatch = softwareSystem "QUICKPATCH" "Plataforma multi-tenant de servicios técnicos." {

            mobile = container "Flutter Mobile" "App de clientes, empresas cliente, técnicos y proveedores." "Flutter 3.47.5 + Dart 3.13.4" "Mobile App"
            gateway = container "API Gateway" "Enruta, autentica y limita." "Nginx + gateway" "Gateway"

            serviceRequest = container "ServiceRequest" "Ciclo de vida de la solicitud." "ASP.NET Core" {
                srContexto = component "Contexto autenticado" "Toma el usuario (sub), el tenant (tenant_id) y el rol de los claims del JWT que propaga el API Gateway. Nunca lee el tenant del cuerpo (RN-U3)." "ASP.NET Core Middleware · API"
                srApi = component "API REST de solicitudes" "POST /v1/service-requests y GET /v1/service-requests/{id}. Valida el formato de entrada, solo deja crear al rol cliente (403) y responde application/problem+json con X-Correlation-Id." "ASP.NET Core Controller · API" {
                    properties {
                        "HU" "SCRUM-27"
                    }
                }
                srCasosUso = component "Casos de uso de la solicitud" "Crear y consultar una solicitud. Al crear, coordina validación, agregado, persistencia y outbox en una sola transacción local." "Application · CasosDeUso" {
                    properties {
                        "HU" "SCRUM-27"
                    }
                }
                srReglas = component "Validación de reglas de creación" "Ubicación válida (RN-SR1) dentro del área de Bogotá configurada (RN-SR9, 422 ubicacion-fuera-de-cobertura), categoría activa en el tenant (RN-SR10, 422 categoria-no-disponible) y longitudes de descripción y dirección (RN-SR11)." "Domain · Reglas" {
                    properties {
                        "Reglas" "RN-SR1, RN-SR9, RN-SR10, RN-SR11"
                    }
                }
                srAgregado = component "Agregado ServiceRequest y máquina de estados" "Crea la solicitud en buscando_tecnico, sin técnico (RN-SR2), y solo admite las transiciones de la máquina de estados del DD (7.4)." "Domain · State Validation" {
                    properties {
                        "Reglas" "RN-SR2 a RN-SR7"
                    }
                }
                srRepositorio = component "Repositorio de solicitudes" "Lee y escribe service_requests en una transacción que fija SET LOCAL app.current_tenant; RLS filtra por tenant, y una solicitud de otro tenant o de otro cliente responde 404." "EF Core + Npgsql · Infrastructure"
                srOutbox = component "Registro en outbox" "Inserta service-request.created en outbox_events en la misma transacción que la solicitud (ADR-007). El tenant_id lo fija la base con el tenant de la sesión." "EF Core + Npgsql · Infrastructure"
                srPublicador = component "Publicador del outbox" "Proceso en segundo plano: lee los eventos con published_at nulo, los publica en el topic service-request.created con clave serviceRequestId y marca published_at. Si Kafka no responde, reintenta con backoff." "Outbox Worker · Infrastructure"
                srConsumidor = component "Consumidor de catalog.category-changed" "Aplica cada evento con el tenantId del sobre, una sola vez por eventId (processed_events, RN-EV1), y descarta los que traen un updatedAt anterior al guardado." "Kafka Consumer · Infrastructure"
                srReplica = component "Réplica de categorías" "Lee y escribe service_request_categories (categoryId, nombre, activa, updatedAt) y processed_events bajo RLS. Solo la escribe el consumidor; la validación de RN-SR10 solo la lee." "EF Core + Npgsql · Infrastructure"
            }

            matching = container "Matching" "Asignación geoespacial." "Java, Spring Boot"
            communication = container "Communication" "Notificaciones." "ASP.NET Core"
            catalog = container "Catalog" "Especialidades y servicios." "ASP.NET Core"
            kafka = container "Apache Kafka" "Bus de eventos." "Kafka" "Queue"
            db = container "db_service_request" "Base de ServiceRequest en la instancia de PostgreSQL + PostGIS (ADR-014)." "PostgreSQL + PostGIS" "Database"
        }

        # Persona y cliente
        clienteEmpresa -> mobile "Crea y consulta una solicitud (el contrato v1 solo admite el rol cliente)"
        mobile -> gateway "POST /v1/service-requests · GET /v1/service-requests/{id}" "HTTPS/JSON"
        gateway -> srContexto "Enruta la petición con el JWT validado" "REST"

        # ServiceRequest: componentes internos
        srContexto -> srApi "Entrega usuario, tenant y rol a"
        srApi -> srCasosUso "Invoca crear y consultar"
        srCasosUso -> srReglas "Valida la solicitud con"
        srCasosUso -> srAgregado "Crea la solicitud en buscando_tecnico con"
        srCasosUso -> srRepositorio "Guarda y consulta la solicitud con"
        srCasosUso -> srOutbox "Registra service-request.created con"
        srReglas -> srReplica "Consulta si la categoría está activa en"
        srConsumidor -> srReplica "Reemplaza la categoría si updatedAt es más reciente y registra el eventId en processed_events, en la misma transacción"

        # ServiceRequest → base de datos
        srRepositorio -> db "Lee y escribe service_requests (RLS por tenant)" "SQL"
        srOutbox -> db "INSERT en outbox_events, en la misma transacción" "SQL"
        srPublicador -> db "Lee los pendientes y marca published_at (rol service_request_outbox)" "SQL"
        srReplica -> db "Lee y escribe service_request_categories y processed_events (RLS por tenant)" "SQL"

        # Eventos
        srPublicador -> kafka "Publica service-request.created v1" "Kafka"
        srConsumidor -> kafka "Consume catalog.category-changed v1, que publica Catalog" "Kafka"
        catalog -> kafka "Publica catalog.category-changed v1" "Kafka"
        matching -> kafka "Consume service-request.created v1 para iniciar el matching" "Kafka"
        communication -> kafka "Consume service-request.created v1 para confirmar al cliente" "Kafka"
    }

    views {
        component serviceRequest "C4-L3-Backend" "C4-L3 · Componentes de ServiceRequest Service — Sprint 3" {
            include *
            include clienteEmpresa mobile matching communication
            autoLayout tb
        }

        styles {
            element "Element" {
                color #ffffff
            }
            element "Person" {
                shape Person
                background #08427b
            }
            element "Container" {
                background #438dd5
            }
            element "Component" {
                background #85bbf0
                color #000000
            }
            element "Mobile App" {
                shape MobileDevicePortrait
            }
            element "Gateway" {
                shape Hexagon
            }
            element "Queue" {
                shape Pipe
            }
            element "Database" {
                shape Cylinder
            }
            relationship "Contrato pendiente" {
                color #c0392b
                dashed true
            }
        }
    }

}
