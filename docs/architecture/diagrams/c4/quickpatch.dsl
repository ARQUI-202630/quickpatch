/*
 * QUICKPATCH — Modelo C4 completo (Structurizr DSL)
 *
 * Un solo workspace con todas las vistas C4 del SDD:
 *   C4-01  System Landscape        (1)  el entorno de software de QUICKPATCH
 *   C4-02  System Context          (1)  QUICKPATCH es un único sistema de software
 *   C4-03  Container               (1)  los contenedores de QUICKPATCH
 *   C4-04  Component               (10) uno por contenedor con estructura propia:
 *                                       las 2 apps cliente y los 8 microservicios.
 *                                       API Gateway, Kafka, PostgreSQL, Redis y Garage no
 *                                       tienen componentes propios que diseñar (son
 *                                       configuración de productos), por eso no tienen vista.
 *   C4-05  Dynamic                 (6)  un diagrama por flujo crítico, no por sistema
 *   C4-06  Deployment              (2)  uno por ambiente: producción y QA (ADR-022)
 *   C4-07  Code                         fuera de Structurizr: ver los .puml de esta carpeta
 *
 * Etiqueta "Planeado": elemento o relación diseñado en el SDD/DD que todavía no está en el
 * código de develop (7 de octubre de 2026). Se dibuja con borde punteado.
 *
 * Fuentes: SRS (roles y RIE-01 a RIE-03), SAD (4.1, ADR-003 a ADR-022), SDD (3.1 a 3.2, 4.1,
 * 5.3 a 5.9, 7.1), DD (5, 7.2, 10) y el código de los 12 repositorios. Integra el C4-L1 del
 * PR #33, el C4-L3 de ServiceRequest del PR #34 y el C4-L3 de las apps cliente (SCRUM-303).
 *
 * Exportar: Structurizr Lite o structurizr.com → cada vista en PNG. El archivo se llama
 * structurizr-<clave>.png; la clave es el segundo parámetro de cada vista.
 */
workspace "QUICKPATCH" "Plataforma multi-tenant de servicios técnicos para hogares y empresas en Bogotá D.C." {

    !identifiers flat

    model {

        # ---------------------------------------------------------------- Personas (SRS 2.1 y 2.2, DD RN-U6)
        cliente = person "Cliente" "Pide, sigue, paga y califica servicios técnicos para el hogar."
        empresaCliente = person "Empresa cliente" "Pide y paga servicios para sus sedes (RF-06)."
        tecnico = person "Técnico" "Recibe asignaciones, ejecuta el servicio y registra evidencias."
        proveedor = person "Proveedor" "Administra su equipo de técnicos (RF-16)."
        adminTenant = person "Admin del tenant" "Aprueba y suspende técnicos de su tenant (RF-19, RF-20)."
        adminPlataforma = person "Admin de plataforma" "Administra los tenants (RF-21)."
        equipo = person "Equipo de desarrollo y operación" "Desarrolla, despliega y opera QUICKPATCH." "Interno"

        # ---------------------------------------------------------------- Sistemas externos (SRS RIE-01 a RIE-03)
        pasarela = softwareSystem "Pasarela de pagos PCI-DSS" "Tokeniza la tarjeta y cobra (RIE-01, ADR-009). Proveedor por definir." "Externo"
        geocodificacion = softwareSystem "Servicio de geocodificación" "Convierte direcciones en coordenadas (RIE-02). Proveedor por definir." "Externo"
        notificaciones = softwareSystem "Proveedor de notificaciones" "Entrega correo y push (RIE-03). Proveedor por definir." "Externo"

        # ---------------------------------------------------------------- Sistemas de soporte del equipo
        github = softwareSystem "GitHub" "12 repositorios + quickpatch, GitHub Actions y GitHub Container Registry (ADR-012, ADR-021)." "Soporte"
        observabilidad = softwareSystem "Observabilidad" "Prometheus, Loki y Grafana para producción y QA (VM1, ADR-022)." "Soporte"

        # ---------------------------------------------------------------- QUICKPATCH
        quickpatch = softwareSystem "QUICKPATCH" "Plataforma multi-tenant de servicios técnicos. Microservicios con arquitectura orientada a eventos (ADR-003)." {

            group "Clientes" {
                mobile = container "Flutter Mobile" "App de clientes, empresas cliente, técnicos y proveedores." "Flutter + Dart (iOS y Android)" "Mobile App" {
                    mobNavegacion = component "Navegación" "Rutas protegidas por sesión y por rol; redirige a login o a inicio." "go_router · app/router"
                    mobConfig = component "Configuración del ambiente" "URL base, Host del gateway y huella SHA-256 del certificado de QA (pinning)." "Dart · core/config"
                    mobHttp = component "Cliente HTTP" "Adjunta JWT y X-Correlation-Id, valida el certificado y traduce problem+json en errores de la app." "Dio · core/network"
                    mobSesion = component "Sesión" "Guarda el token en el almacenamiento seguro del dispositivo y expone usuario y rol." "flutter_secure_storage · core/session"
                    mobAuth = component "Autenticación" "Login y registro de cliente, técnico y empresa." "Riverpod · features/autenticacion"
                    mobInicio = component "Inicio por rol" "Opciones habilitadas según el rol del usuario." "Flutter · features/inicio"
                    mobSolicitudes = component "Solicitudes" "Nueva solicitud en un formulario (RNF-11) y detalle con su estado." "Riverpod · features/solicitudes"
                    mobUbicacion = component "Ubicación del dispositivo" "Permiso y lectura del GPS con respaldo en LocationManager y límite de 15 s." "geolocator · features/solicitudes/data"
                    mobTiempoReal = component "Estado en tiempo real" "Recibe cambios de estado de la solicitud (RF-11, RNF-06). Canal por decidir (SAD 4.1)." "Dart · core/realtime" "Planeado"
                }
                web = container "Angular Web" "Panel de administración del tenant y de la plataforma." "Angular 22 + TypeScript" "Web Browser" {
                    webShell = component "Shell y rutas" "Rutas, layout del panel y redirección a login o acceso denegado." "Angular Router · app.routes"
                    webSesion = component "Sesión" "Conserva el token y expone usuario y rol como signals." "Angular Service · core/sesion"
                    webInterceptor = component "Interceptor HTTP" "Adjunta JWT y X-Correlation-Id; traduce 401 y 403 en estados de la UI." "Interceptor funcional · core/http"
                    webGuards = component "Guards de rol" "Permiten cada ruta según el rol (RN-U6)." "Guard funcional · core/guards"
                    webLogin = component "Inicio de sesión" "Formulario de acceso con validaciones y errores." "Angular Component · features/autenticacion"
                    webInicio = component "Inicio" "Menú según el rol del administrador." "Angular Component · features/inicio"
                    webTenants = component "Gestión de tenants" "Lista los tenants y los activa o desactiva con confirmación (SCRUM-41)." "Angular Component · features/tenants"
                    webTenantsApi = component "Cliente API de tenants" "GET y PATCH /v1/platform/tenants." "HttpClient · features/tenants"
                    webTecnicos = component "Aprobación de técnicos" "Aprueba y suspende técnicos del tenant (RF-19, RF-20)." "Angular Component · features/tecnicos" "Planeado"
                }
            }

            gateway = container "API Gateway" "Única entrada HTTP: enruta /api/<servicio>, valida el JWT y limita peticiones (SDD 3.2.1)." "Nginx (quickpatch-api-gateway)" "Gateway"

            group "Microservicios" {
                identity = container "Identity Service" "Autenticación, usuarios, tenants y auditoría." "ASP.NET Core (.NET 10)" {
                    idApi = component "API de autenticación y usuarios" "POST /v1/auth/register/client, /register/technician y /login; GET /v1/users/me." "Minimal API · Endpoints"
                    idPlatformApi = component "API de plataforma" "GET y PATCH /v1/platform/tenants; solo admin_plataforma." "Minimal API · Endpoints"
                    idSeguridad = component "Autorización y auditoría de 403" "Valida rol y tenant del JWT y registra cada acceso denegado (RNF-04)." "ASP.NET Core · Security"
                    idHttp = component "Correlación y Problem Details" "Propaga X-Correlation-Id y responde application/problem+json." "ASP.NET Core · Http"
                    idAuthCasos = component "Casos de uso de autenticación" "Login con bloqueo por intentos, registro de cliente y técnico, usuario actual." "Application · Auth"
                    idPlatformCasos = component "Casos de uso de plataforma" "Lista tenants y cambia su estado con auditoría en la misma transacción." "Application · Platform"
                    idBootstrap = component "Bootstrap de administradores" "Crea al arrancar el admin del tenant y el de plataforma desde el Secret." "Hosted service · Bootstrap"
                    idDominio = component "Dominio de identidad" "Tenant, User, TechnicianProfile, Roles y AuditEntry." "Domain"
                    idTokens = component "Emisor de tokens RS256" "Firma el JWT con la llave privada (ADR-018)." "RsaTokenIssuer · Infrastructure"
                    idHasher = component "Hasher BCrypt" "Hash de contraseñas con factor configurable (RNF-03)." "BCryptPasswordHasher · Infrastructure"
                    idPersistencia = component "Persistencia con RLS" "TenantUnitOfWork (set_config app.current_tenant) y PlatformUnitOfWork (SET LOCAL ROLE identity_platform)." "EF Core + Npgsql · Infrastructure"
                }
                actors = container "Actors Service" "Proveedores, aliados y clientes como actores de negocio." "ASP.NET Core (.NET 10)" {
                    acApi = component "API de actores" "Consulta y mantenimiento de actores del tenant." "Minimal API" "Planeado"
                    acProveedores = component "Proveedores de materiales" "Supplier: proveedor de materiales o repuestos (concepto evolutivo)." "Domain" "Planeado"
                    acAliados = component "Aliados" "Ally: técnico, profesional o empresa aliada." "Domain" "Planeado"
                    acClientes = component "Clientes" "Client: cliente hogar o empresarial." "Domain" "Planeado"
                    acPersistencia = component "Persistencia con RLS" "Repositorios de actores por tenant." "EF Core + Npgsql" "Planeado"
                }
                catalog = container "Catalog Service" "Categorías y especialidades de servicio." "ASP.NET Core (.NET 10)" {
                    catApi = component "API de categorías" "GET /v1/catalog/categories; POST y PUT /v1/catalog/admin/categories." "Minimal API · Endpoints"
                    catSeguridad = component "Contexto autenticado y auditoría de 403" "Toma usuario, tenant y rol del JWT; registra los 403." "ASP.NET Core · Security"
                    catCasos = component "Casos de uso de categorías" "Crear, actualizar y listar; nombre único por tenant (409)." "Application · Categories"
                    catDominio = component "Agregado Category" "Nombre normalizado, descripción, estado activo y updatedAt." "Domain"
                    catRepositorio = component "Repositorio de categorías" "service_categories bajo RLS." "EF Core + Npgsql · Infrastructure"
                    catOutbox = component "Registro en outbox" "Encola catalog.category-changed en la misma transacción (ADR-007)." "EF Core · Infrastructure"
                    catPublicador = component "Publicador del outbox" "Publica los eventos pendientes y marca published_at." "BackgroundService · Infrastructure"
                }
                serviceRequest = container "ServiceRequest Service" "Ciclo de vida de la solicitud de servicio." "ASP.NET Core (.NET 10)" {
                    srContexto = component "Contexto autenticado" "Toma usuario, tenant y rol de los claims del JWT; nunca del cuerpo (RN-U3)." "ASP.NET Core · Security"
                    srApi = component "API REST de solicitudes" "POST /v1/service-requests y GET /v1/service-requests/{id}; solo el rol cliente crea (403)." "Minimal API · Endpoints"
                    srCasos = component "Casos de uso de la solicitud" "Crear y consultar; al crear coordina validación, agregado, persistencia y outbox en una transacción." "Application"
                    srReglas = component "Reglas de creación" "Ubicación en Bogotá (422), categoría activa (422) y longitudes (RN-SR1, RN-SR9 a RN-SR11)." "Domain"
                    srAgregado = component "Agregado ServiceRequest" "Crea en buscando_tecnico y solo admite transiciones válidas (RN-SR2 a RN-SR7)." "Domain"
                    srRepositorio = component "Repositorio de solicitudes" "service_requests en transacción con app.current_tenant (RLS)." "EF Core + Npgsql · Infrastructure"
                    srOutbox = component "Registro en outbox" "Inserta service-request.created en outbox_events en la misma transacción." "EF Core · Infrastructure"
                    srPublicador = component "Publicador del outbox" "Lotes con FOR UPDATE SKIP LOCKED; publica y marca published_at; reintenta si Kafka falla." "BackgroundService · Infrastructure"
                    srConsumidorCategorias = component "Consumidor de catalog.category-changed" "Aplica cada evento una vez por eventId y descarta versiones viejas (RN-EV1)." "Kafka consumer · Infrastructure"
                    srReplica = component "Réplica de categorías" "service_request_categories; solo la escribe el consumidor (ADR-017)." "EF Core · Infrastructure"
                    srConsumidorResultados = component "Consumidor de matching y pagos" "Aplica matching.technician-assigned, matching.no-technician-available y payment.* al estado." "Kafka consumer" "Planeado"
                    srEvidencias = component "Evidencias y calificación" "Fotos del servicio (RF-15) y calificación del cliente; publica service-request.completed y .evaluated." "Application" "Planeado"
                }
                matching = container "Matching Service" "Asignación geoespacial de técnicos." "Java 21 + Spring Boot" {
                    maListener = component "Listener de service-request.created" "Valida el contrato, descarta mensajes inválidos y propaga correlationId en el MDC." "@KafkaListener · infrastructure/messaging"
                    maHandler = component "Manejador del evento" "En una transacción por tenant registra el evento y, si es nuevo, inicia el matching (APPLIED o DUPLICATE)." "application/events"
                    maProcesados = component "Registro de eventos procesados" "INSERT ... ON CONFLICT (event_id) DO NOTHING en processed_events." "JDBC · infrastructure/persistence"
                    maTransaccion = component "Transacción por tenant" "set_config app.current_tenant antes de cada trabajo (RLS)." "JDBC · infrastructure/persistence"
                    maBusqueda = component "Búsqueda de candidatos" "Filtra por especialidad, disponibilidad y cobertura con PostGIS y ordena (RN-M1 a RN-M7)." "PostGIS" "Planeado"
                    maAsignacion = component "Asignación y resultado" "Registra el intento y publica matching.technician-assigned o matching.no-technician-available." "Outbox" "Planeado"
                    maGeocodificador = component "Adaptador de geocodificación" "Convierte direcciones de cobertura en coordenadas." "HTTPS" "Planeado"
                }
                ranking = container "Ranking Service" "Reputación de técnicos." "ASP.NET Core (.NET 10)" {
                    raConsumidor = component "Consumidor de service-request.evaluated" "Recibe cada calificación, una vez por eventId." "Kafka consumer" "Planeado"
                    raCalculo = component "Cálculo de reputación" "Recalcula el promedio del técnico (RF-12)." "Domain" "Planeado"
                    raApi = component "API de reputación" "Consulta de la reputación del técnico." "Minimal API" "Planeado"
                    raPersistencia = component "Persistencia con RLS" "Reputación agregada por tenant." "EF Core + Npgsql" "Planeado"
                }
                payments = container "Payments Service" "Pagos tokenizados y facturación." "ASP.NET Core (.NET 10)" {
                    paApi = component "API de pagos" "Inicia el pago con el token de la tarjeta; nunca recibe PAN ni CVV (RNF-01)." "Minimal API" "Planeado"
                    paProcesamiento = component "Procesamiento de pagos" "Estados del pago y reintentos idempotentes." "Application" "Planeado"
                    paAdaptadorPsp = component "Adaptador del PSP" "Cobra con la pasarela usando la referencia del token (ADR-009)." "HTTPS" "Planeado"
                    paWebhook = component "Receptor de webhooks del PSP" "Confirma el resultado de forma idempotente." "Minimal API" "Planeado"
                    paFacturacion = component "Facturación" "Emite el comprobante a nombre de la plataforma (D4)." "Application" "Planeado"
                    paOutbox = component "Outbox de pagos" "Publica payment.approved y payment.rejected." "BackgroundService" "Planeado"
                }
                communication = container "Communication Service" "Notificaciones del ciclo de servicio." "ASP.NET Core (.NET 10)" {
                    coConsumidores = component "Consumidores de eventos" "service-request.*, matching.* y payment.*, una vez por eventId." "Kafka consumer" "Planeado"
                    coPlantillas = component "Plantillas de notificación" "Arma el mensaje según el evento y el destinatario." "Application" "Planeado"
                    coAdaptador = component "Adaptador del proveedor" "Envía correo y push por el proveedor externo (RIE-03)." "HTTPS" "Planeado"
                }
            }

            group "Mensajería y almacenamiento" {
                kafka = container "Apache Kafka" "Bus de eventos: un topic por tipo de evento (quickpatch-kafka/topics)." "Apache Kafka (KRaft)" "Queue"
                redis = container "Redis" "Caché y colas cortas; un usuario por servicio limitado a <servicio>:*." "Redis" "Database"
                garage = container "Garage" "Evidencias fotográficas y respaldos de PostgreSQL (ADR-016)." "Garage (S3)" "Database"
            }

            group "PostgreSQL + PostGIS (una instancia, una base por servicio, ADR-014)" {
                dbIdentity = container "db_identity" "tenants, users, technician_profiles, audit_logs." "PostgreSQL" "Database"
                dbActors = container "db_actors" "Actores de negocio." "PostgreSQL" "Database"
                dbCatalog = container "db_catalog" "service_categories y outbox_events." "PostgreSQL" "Database"
                dbServiceRequest = container "db_service_request" "service_requests, service_request_categories, outbox_events y processed_events." "PostgreSQL + PostGIS" "Database"
                dbMatching = container "db_matching" "Disponibilidad, cobertura, intentos y processed_events." "PostgreSQL + PostGIS" "Database"
                dbRanking = container "db_ranking" "Reputación agregada." "PostgreSQL" "Database"
                dbPayments = container "db_payments" "payments e invoices, sin PAN ni CVV." "PostgreSQL" "Database"
                dbCommunication = container "db_communication" "Notificaciones enviadas." "PostgreSQL" "Database"
            }
        }

        # ================================================================ Relaciones
        # Personas → apps
        cliente -> mobNavegacion "Pide, sigue, paga y califica servicios"
        empresaCliente -> mobNavegacion "Pide y paga servicios"
        tecnico -> mobNavegacion "Atiende sus asignaciones"
        proveedor -> mobNavegacion "Administra su equipo"
        adminTenant -> webShell "Aprueba y suspende técnicos"
        adminPlataforma -> webShell "Administra los tenants"
        equipo -> github "Desarrolla y despliega"
        equipo -> observabilidad "Opera y diagnostica"

        # Flutter Mobile
        mobNavegacion -> mobSesion "Consulta usuario y rol en"
        mobNavegacion -> mobAuth "Abre"
        mobNavegacion -> mobInicio "Abre"
        mobNavegacion -> mobSolicitudes "Abre"
        mobAuth -> mobSesion "Guarda el token en"
        mobAuth -> mobHttp "POST /v1/auth/* con"
        mobSolicitudes -> mobUbicacion "Obtiene las coordenadas con"
        mobSolicitudes -> mobHttp "GET categorías, POST y GET solicitudes con"
        mobSolicitudes -> mobTiempoReal "Escucha cambios de estado en" "" "Planeado"
        mobHttp -> mobConfig "Lee URL base y certificado de"
        mobHttp -> mobSesion "Lee el token de"
        mobHttp -> gateway "Llama a la API" "HTTPS/JSON"

        # Angular Web
        webShell -> webGuards "Protege las rutas con"
        webShell -> webLogin "Abre"
        webShell -> webInicio "Abre"
        webShell -> webTenants "Abre"
        webShell -> webTecnicos "Abre" "" "Planeado"
        webGuards -> webSesion "Lee el rol de"
        webLogin -> webSesion "Inicia sesión con"
        webSesion -> webInterceptor "Llama a /v1/auth/login con"
        webTenants -> webTenantsApi "Lista y cambia el estado con"
        webTenantsApi -> webInterceptor "Envía las peticiones por"
        webTecnicos -> webInterceptor "Envía las peticiones por" "" "Planeado"
        webInterceptor -> webSesion "Lee el token de"
        webInterceptor -> gateway "Llama a la API" "HTTPS/JSON"

        # API Gateway → servicios
        gateway -> idApi "Enruta /api/v1/auth y /api/v1/users" "HTTP"
        gateway -> idPlatformApi "Enruta /api/v1/platform" "HTTP"
        gateway -> catApi "Enruta /api/v1/catalog" "HTTP"
        gateway -> srContexto "Enruta /api/v1/service-requests" "HTTP"
        gateway -> acApi "Enruta /api/v1/actors" "HTTP" "Planeado"
        gateway -> raApi "Enruta /api/v1/ranking" "HTTP" "Planeado"
        gateway -> paApi "Enruta /api/v1/payments" "HTTP" "Planeado"

        # Identity
        idApi -> idHttp "Usa"
        idApi -> idAuthCasos "Invoca"
        idPlatformApi -> idSeguridad "Exige admin_plataforma con"
        idPlatformApi -> idPlatformCasos "Invoca"
        idAuthCasos -> idDominio "Aplica reglas de"
        idAuthCasos -> idHasher "Verifica y genera hashes con"
        idAuthCasos -> idTokens "Emite el JWT con"
        idAuthCasos -> idPersistencia "Lee y guarda en la transacción del tenant con"
        idPlatformCasos -> idPersistencia "Lee y cambia tenants en la transacción de plataforma con"
        idBootstrap -> idAuthCasos "Asegura los administradores iniciales con"
        idPersistencia -> dbIdentity "Lee y escribe (RLS)" "SQL"

        # Actors
        acApi -> acProveedores "Usa" "" "Planeado"
        acApi -> acAliados "Usa" "" "Planeado"
        acApi -> acClientes "Usa" "" "Planeado"
        acApi -> acPersistencia "Lee y escribe con" "" "Planeado"
        acPersistencia -> dbActors "Lee y escribe (RLS)" "SQL" "Planeado"

        # Catalog
        catApi -> catSeguridad "Autoriza con"
        catApi -> catCasos "Invoca"
        catCasos -> catDominio "Aplica reglas de"
        catCasos -> catRepositorio "Guarda y lista con"
        catCasos -> catOutbox "Registra catalog.category-changed con"
        catRepositorio -> dbCatalog "Lee y escribe service_categories (RLS)" "SQL"
        catOutbox -> dbCatalog "INSERT en outbox_events" "SQL"
        catPublicador -> dbCatalog "Lee pendientes y marca published_at" "SQL"
        catPublicador -> kafka "Publica catalog.category-changed" "Kafka"

        # ServiceRequest
        srContexto -> srApi "Entrega usuario, tenant y rol a"
        srApi -> srCasos "Invoca"
        srCasos -> srReglas "Valida con"
        srCasos -> srAgregado "Crea la solicitud con"
        srCasos -> srRepositorio "Guarda y consulta con"
        srCasos -> srOutbox "Registra service-request.created con"
        srReglas -> srReplica "Consulta si la categoría está activa en"
        srRepositorio -> dbServiceRequest "Lee y escribe service_requests (RLS)" "SQL"
        srOutbox -> dbServiceRequest "INSERT en outbox_events" "SQL"
        srPublicador -> dbServiceRequest "Lee pendientes y marca published_at" "SQL"
        srPublicador -> kafka "Publica service-request.created" "Kafka"
        srConsumidorCategorias -> kafka "Consume catalog.category-changed" "Kafka"
        srConsumidorCategorias -> srReplica "Reemplaza la categoría si es más reciente"
        srReplica -> dbServiceRequest "Lee y escribe service_request_categories y processed_events" "SQL"
        srConsumidorResultados -> kafka "Consume matching.* y payment.*" "Kafka" "Planeado"
        srConsumidorResultados -> srAgregado "Aplica la transición con" "" "Planeado"
        srApi -> srEvidencias "Invoca" "" "Planeado"
        srEvidencias -> garage "Guarda las fotos del servicio" "S3/HTTPS" "Planeado"
        srEvidencias -> srOutbox "Registra service-request.completed y .evaluated con" "" "Planeado"

        # Matching
        maListener -> kafka "Consume service-request.created" "Kafka"
        maListener -> maHandler "Entrega el evento válido a"
        maHandler -> maTransaccion "Abre la transacción del tenant con"
        maHandler -> maProcesados "Registra el eventId en"
        maHandler -> maBusqueda "Inicia el matching con" "" "Planeado"
        maBusqueda -> maAsignacion "Entrega el mejor candidato a" "" "Planeado"
        maBusqueda -> redis "Cachea disponibilidad en" "RESP" "Planeado"
        maAsignacion -> kafka "Publica matching.technician-assigned o matching.no-technician-available" "Kafka" "Planeado"
        maGeocodificador -> geocodificacion "Geocodifica direcciones" "HTTPS" "Planeado"
        maBusqueda -> maGeocodificador "Resuelve direcciones con" "" "Planeado"
        maProcesados -> dbMatching "INSERT en processed_events" "SQL"
        maTransaccion -> dbMatching "set_config app.current_tenant" "SQL"
        maBusqueda -> dbMatching "Consulta disponibilidad y cobertura (PostGIS)" "SQL" "Planeado"

        # Ranking
        raConsumidor -> kafka "Consume service-request.evaluated" "Kafka" "Planeado"
        raConsumidor -> raCalculo "Entrega la calificación a" "" "Planeado"
        raCalculo -> raPersistencia "Guarda la reputación con" "" "Planeado"
        raApi -> raPersistencia "Consulta con" "" "Planeado"
        raPersistencia -> dbRanking "Lee y escribe (RLS)" "SQL" "Planeado"

        # Payments
        paApi -> paProcesamiento "Invoca" "" "Planeado"
        paProcesamiento -> paAdaptadorPsp "Cobra con" "" "Planeado"
        paAdaptadorPsp -> pasarela "Tokeniza y cobra" "HTTPS" "Planeado"
        pasarela -> paWebhook "Notifica el resultado del cobro" "HTTPS" "Planeado"
        paWebhook -> paProcesamiento "Confirma el pago con" "" "Planeado"
        paProcesamiento -> paFacturacion "Emite la factura con" "" "Planeado"
        paProcesamiento -> paOutbox "Registra payment.approved o payment.rejected con" "" "Planeado"
        paProcesamiento -> dbPayments "Lee y escribe payments e invoices (RLS)" "SQL" "Planeado"
        paOutbox -> kafka "Publica payment.*" "Kafka" "Planeado"

        # Communication
        coConsumidores -> kafka "Consume service-request.*, matching.* y payment.*" "Kafka" "Planeado"
        coConsumidores -> coPlantillas "Arma el mensaje con" "" "Planeado"
        coPlantillas -> coAdaptador "Envía con" "" "Planeado"
        coAdaptador -> notificaciones "Envía correo y push" "HTTPS" "Planeado"
        coConsumidores -> dbCommunication "Registra la notificación" "SQL" "Planeado"
        notificaciones -> mobile "Entrega notificaciones push" "Push" "Planeado"
        notificaciones -> cliente "Entrega correo" "Correo" "Planeado"

        # Soporte
        github -> quickpatch "Construye imágenes y despliega con el runner de VM1" "HTTPS"
        quickpatch -> observabilidad "Envía métricas y logs" "HTTP"

        # ================================================================ Despliegue (ADR-022, INFRASTRUCTURE 3.3)
        produccion = deploymentEnvironment "Producción" {
            deploymentNode "Teléfono del usuario" "" "Android o iOS" {
                mobProd = containerInstance mobile
            }
            deploymentNode "Navegador del administrador" "" "Chrome, Edge o Firefox" {
                webBrowserProd = infrastructureNode "Navegador" "Ejecuta el panel Angular descargado de VM3." "HTML + JS"
            }
            deploymentNode "Red privada del laboratorio 10.43.x.x" "Solo el 443 de VM1 es alcanzable desde la VPN (R9); firewall default deny incoming." "" {
                deploymentNode "VM1 · Herramientas · 10.43.100.168" "Entrada única y herramientas compartidas por los dos ambientes." "4 vCPU · 11 GiB RAM · 68 GB" {
                    proxyProd = infrastructureNode "Proxy Nginx :443" "Termina TLS (autofirmado) y elige destino por nombre: quickpatch.internal → VM3:30080, grafana.quickpatch.internal → Grafana." "Nginx"
                    runnerProd = infrastructureNode "Runner de GitHub Actions" "kubectl y k6; despliega la imagen de main." "GitHub Actions runner"
                    observabilidadProd = softwareSystemInstance observabilidad
                }
                deploymentNode "VM3 · Aplicación · 10.43.98.205" "" "4 vCPU · 11 GiB RAM · 68 GB" {
                    deploymentNode "k3s (un nodo)" "" "k3s + Traefik" {
                        traefikProd = infrastructureNode "Traefik" "Ingress del clúster en NodePort 30080." "Traefik"
                        gatewayProd = containerInstance gateway
                        webProd = containerInstance web
                        identityProd = containerInstance identity
                        actorsProd = containerInstance actors
                        catalogProd = containerInstance catalog
                        serviceRequestProd = containerInstance serviceRequest
                        matchingProd = containerInstance matching
                        rankingProd = containerInstance ranking
                        paymentsProd = containerInstance payments
                        communicationProd = containerInstance communication
                    }
                }
                deploymentNode "VM4 · Datos · 10.43.98.209" "" "4 vCPU · 11 GiB RAM · 68 GB" {
                    deploymentNode "PostgreSQL 16 + PostGIS" "Una instancia, una base por servicio (ADR-014). pg_dump diario a Garage." "PostgreSQL" {
                        dbIdentityProd = containerInstance dbIdentity
                        dbActorsProd = containerInstance dbActors
                        dbCatalogProd = containerInstance dbCatalog
                        dbServiceRequestProd = containerInstance dbServiceRequest
                        dbMatchingProd = containerInstance dbMatching
                        dbRankingProd = containerInstance dbRanking
                        dbPaymentsProd = containerInstance dbPayments
                        dbCommunicationProd = containerInstance dbCommunication
                    }
                    redisProd = containerInstance redis
                }
                deploymentNode "VM6 · Mensajería y almacenamiento · 10.43.99.12" "" "4 vCPU · 11 GiB RAM · 68 GB" {
                    kafkaProd = containerInstance kafka
                    garageProd = containerInstance garage
                }
            }
            webBrowserProd -> proxyProd "Abre https://quickpatch.internal" "HTTPS"
            mobProd -> proxyProd "Llama a https://quickpatch.internal/api" "HTTPS"
            proxyProd -> traefikProd "Reenvía al gateway de producción" "HTTP"
            traefikProd -> gatewayProd "Enruta /api" "HTTP"
            traefikProd -> webProd "Sirve el panel" "HTTP"
            runnerProd -> traefikProd "kubectl apply de la imagen de main" "HTTPS"
        }

        qa = deploymentEnvironment "QA" {
            deploymentNode "Teléfono o emulador de prueba" "" "Android" {
                mobQa = containerInstance mobile
            }
            deploymentNode "Red privada del laboratorio 10.43.x.x" "QA no se conecta con producción; solo VM1 llega a los dos (ADR-022)." "" {
                deploymentNode "VM1 · Herramientas · 10.43.100.168" "Misma VM1 de producción." "4 vCPU · 11 GiB RAM · 68 GB" {
                    proxyQa = infrastructureNode "Proxy Nginx :443" "qa.quickpatch.internal → VM2:30080." "Nginx"
                    runnerQa = infrastructureNode "Runner de GitHub Actions" "Despliega release/* y corre Newman, Playwright, ZAP y k6 contra QA." "GitHub Actions runner"
                    observabilidadQa = softwareSystemInstance observabilidad
                }
                deploymentNode "VM2 · Aplicación · 10.43.98.15" "" "4 vCPU · 11 GiB RAM · 68 GB" {
                    deploymentNode "k3s (un nodo)" "" "k3s + Traefik" {
                        traefikQa = infrastructureNode "Traefik" "Ingress del clúster en NodePort 30080." "Traefik"
                        gatewayQa = containerInstance gateway
                        webQa = containerInstance web
                        identityQa = containerInstance identity
                        actorsQa = containerInstance actors
                        catalogQa = containerInstance catalog
                        serviceRequestQa = containerInstance serviceRequest
                        matchingQa = containerInstance matching
                        rankingQa = containerInstance ranking
                        paymentsQa = containerInstance payments
                        communicationQa = containerInstance communication
                    }
                }
                deploymentNode "VM5 · Datos · 10.43.98.29" "" "4 vCPU · 11 GiB RAM · 68 GB" {
                    deploymentNode "PostgreSQL 16 + PostGIS" "Datos de prueba, sin respaldo." "PostgreSQL" {
                        dbIdentityQa = containerInstance dbIdentity
                        dbActorsQa = containerInstance dbActors
                        dbCatalogQa = containerInstance dbCatalog
                        dbServiceRequestQa = containerInstance dbServiceRequest
                        dbMatchingQa = containerInstance dbMatching
                        dbRankingQa = containerInstance dbRanking
                        dbPaymentsQa = containerInstance dbPayments
                        dbCommunicationQa = containerInstance dbCommunication
                    }
                    redisQa = containerInstance redis
                }
                deploymentNode "VM7 · Mensajería y almacenamiento · 10.43.99.8" "" "4 vCPU · 11 GiB RAM · 68 GB" {
                    kafkaQa = containerInstance kafka
                    garageQa = containerInstance garage
                }
            }
            mobQa -> proxyQa "Llama a https://qa.quickpatch.internal/api (certificado fijado)" "HTTPS"
            proxyQa -> traefikQa "Reenvía al gateway de QA" "HTTP"
            traefikQa -> gatewayQa "Enruta /api" "HTTP"
            traefikQa -> webQa "Sirve el panel" "HTTP"
            runnerQa -> traefikQa "Despliega release/* y ejecuta las pruebas del sistema" "HTTPS"
        }
    }

    views {

        systemLandscape "C4-01-Landscape" "Entorno de software de QUICKPATCH: el sistema, sus sistemas externos y los sistemas de soporte del equipo." {
            include *
            autoLayout lr
        }

        systemContext quickpatch "C4-02-Contexto" "QUICKPATCH frente a las personas que lo usan y los sistemas externos (RIE-01 a RIE-03)." {
            include *
            exclude equipo github observabilidad
            autoLayout lr
        }

        container quickpatch "C4-03-Contenedores" "Contenedores de QUICKPATCH: apps cliente, API Gateway, 8 microservicios, Kafka y almacenes de datos." {
            include *
            exclude equipo github observabilidad
            autoLayout lr
        }

        component mobile "C4-04-Componentes-Mobile" "Componentes de Flutter Mobile." {
            include *
            autoLayout lr
        }
        component web "C4-04-Componentes-Web" "Componentes de Angular Web." {
            include *
            autoLayout lr
        }
        component identity "C4-04-Componentes-Identity" "Componentes de Identity Service." {
            include *
            autoLayout lr
        }
        component actors "C4-04-Componentes-Actors" "Componentes de Actors Service (diseño; el servicio es un esqueleto)." {
            include *
            autoLayout lr
        }
        component catalog "C4-04-Componentes-Catalog" "Componentes de Catalog Service." {
            include *
            autoLayout lr
        }
        component serviceRequest "C4-04-Componentes-ServiceRequest" "Componentes de ServiceRequest Service." {
            include *
            autoLayout lr
        }
        component matching "C4-04-Componentes-Matching" "Componentes de Matching Service." {
            include *
            autoLayout lr
        }
        component ranking "C4-04-Componentes-Ranking" "Componentes de Ranking Service (diseño; el servicio es un esqueleto)." {
            include *
            autoLayout lr
        }
        component payments "C4-04-Componentes-Payments" "Componentes de Payments Service (diseño; el servicio es un esqueleto)." {
            include *
            autoLayout lr
        }
        component communication "C4-04-Componentes-Communication" "Componentes de Communication Service (diseño; el servicio es un esqueleto)." {
            include *
            autoLayout lr
        }

        dynamic quickpatch "C4-05-Dinamico-InicioSesion" "Inicio de sesión: el tenant sale del canal y el JWT RS256 lo firma Identity (RN-U5, ADR-018)." {
            mobile -> gateway "POST /api/v1/auth/login con X-Channel-Id"
            gateway -> identity "Enruta /v1/auth/login"
            identity -> dbIdentity "Busca el usuario en el tenant del canal y registra el intento (RLS)"
            identity -> gateway "200 con accessToken RS256 y el usuario"
            gateway -> mobile "Entrega el token"
            autoLayout lr
        }

        dynamic quickpatch "C4-05-Dinamico-ReplicaCategorias" "Alta de una categoría y su réplica en ServiceRequest (ADR-007, ADR-017)." {
            web -> gateway "POST /api/v1/catalog/admin/categories"
            gateway -> catalog "Enruta con el JWT del admin del tenant"
            catalog -> dbCatalog "Guarda la categoría y el evento en outbox_events (una transacción)"
            catalog -> kafka "El publicador envía catalog.category-changed"
            serviceRequest -> kafka "Consume el evento"
            serviceRequest -> dbServiceRequest "Actualiza service_request_categories y processed_events"
            autoLayout lr
        }

        dynamic quickpatch "C4-05-Dinamico-CrearSolicitud" "Creación de una solicitud y matching (RF-07, RF-09, ADR-007)." {
            mobile -> gateway "POST /api/v1/service-requests"
            gateway -> serviceRequest "Enruta con el JWT del cliente"
            serviceRequest -> dbServiceRequest "Valida la categoría en la réplica y guarda solicitud y outbox (una transacción)"
            serviceRequest -> kafka "El publicador envía service-request.created"
            matching -> kafka "Consume service-request.created"
            matching -> dbMatching "Registra el eventId y busca candidatos (PostGIS)"
            matching -> kafka "Publica matching.technician-assigned o matching.no-technician-available"
            serviceRequest -> kafka "Consume el resultado y cambia el estado"
            communication -> kafka "Consume el resultado"
            communication -> notificaciones "Pide el aviso al cliente y al técnico"
            notificaciones -> mobile "Entrega la notificación push"
            autoLayout lr
        }

        dynamic quickpatch "C4-05-Dinamico-Pago" "Pago tokenizado y facturación (RF-22 a RF-24, ADR-009)." {
            mobile -> gateway "POST /api/v1/payments con el token de la tarjeta"
            gateway -> payments "Enruta con el JWT del cliente"
            payments -> pasarela "Cobra con el token (sin PAN ni CVV)"
            pasarela -> payments "Webhook con el resultado"
            payments -> dbPayments "Guarda el pago, la factura y el evento en outbox (una transacción)"
            payments -> kafka "Publica payment.approved o payment.rejected"
            serviceRequest -> kafka "Consume el resultado y pasa a pagado"
            communication -> kafka "Consume el resultado y envía el comprobante"
            autoLayout lr
        }

        dynamic quickpatch "C4-05-Dinamico-Calificacion" "Calificación del servicio y recálculo de la reputación (RF-12, RF-20)." {
            mobile -> gateway "POST la calificación del servicio"
            gateway -> serviceRequest "Enruta con el JWT del cliente"
            serviceRequest -> dbServiceRequest "Guarda la calificación y el evento en outbox"
            serviceRequest -> kafka "Publica service-request.evaluated"
            ranking -> kafka "Consume la calificación"
            ranking -> dbRanking "Recalcula la reputación del técnico"
            autoLayout lr
        }

        dynamic quickpatch "C4-05-Dinamico-GestionTenants" "Gestión de tenants por el admin de plataforma (RF-21, SCRUM-112)." {
            web -> gateway "PATCH /api/v1/platform/tenants/{id}"
            gateway -> identity "Enruta con el JWT de admin_plataforma"
            identity -> dbIdentity "SET LOCAL ROLE identity_platform, cambia el estado y escribe audit_logs (una transacción)"
            identity -> gateway "200 con el tenant actualizado"
            gateway -> web "Muestra el nuevo estado"
            autoLayout lr
        }

        deployment quickpatch produccion "C4-06-Despliegue-Produccion" "Producción: VM1 (entrada y herramientas), VM3, VM4 y VM6 (ADR-022)." {
            include *
            exclude "mobProd -> gatewayProd" "webProd -> gatewayProd"
            autoLayout lr
        }

        deployment quickpatch qa "C4-06-Despliegue-QA" "QA: copia de producción en VM2, VM5 y VM7; comparte VM1 (ADR-022)." {
            include *
            exclude "mobQa -> gatewayQa" "webQa -> gatewayQa"
            autoLayout lr
        }

        styles {
            element "Element" {
                color #ffffff
                fontSize 24
            }
            element "Person" {
                shape Person
                background #08427b
            }
            element "Interno" {
                background #5a6b7d
            }
            element "Software System" {
                background #1168bd
            }
            element "Externo" {
                background #999999
            }
            element "Soporte" {
                background #6b8fb3
            }
            element "Container" {
                background #438dd5
            }
            element "Component" {
                background #85bbf0
                color #000000
            }
            element "Database" {
                shape Cylinder
            }
            element "Queue" {
                shape Pipe
            }
            element "Web Browser" {
                shape WebBrowser
            }
            element "Mobile App" {
                shape MobileDevicePortrait
            }
            element "Gateway" {
                shape Hexagon
            }
            element "Planeado" {
                border dashed
                opacity 70
            }
            element "Infrastructure Node" {
                background #ffffff
                color #000000
            }
            relationship "Relationship" {
                fontSize 22
            }
            relationship "Planeado" {
                dashed true
                color #707070
            }
        }
    }

}
