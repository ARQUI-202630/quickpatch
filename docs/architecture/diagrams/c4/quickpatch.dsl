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
 *   C4-05  Dynamic                 (7)  un diagrama por flujo crítico, no por sistema
 *   C4-06  Deployment              (2)  uno por ambiente: producción y QA (ADR-022)
 *   C4-07  Code                         fuera de Structurizr: ver los .puml de esta carpeta
 *
 * Etiqueta "Planeado": elemento o relación diseñado en el SDD/DD que todavía no está en el
 * código de develop (22 de octubre de 2026). Se dibuja con borde punteado.
 *
 * Fuentes: SRS (roles y RIE-01 a RIE-03), SAD (4.1, ADR-003 a ADR-024), SDD (secciones 3 a 9),
 * DD (5, 7.2, 10) y el código de los 12 repositorios. Integra el C4-L1 del
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

        # ---------------------------------------------------------------- Sistemas externos (ADR-024: solo la pasarela, R5)
        # La geocodificación (RIE-02) corre dentro con Nominatim y las notificaciones (RIE-03) son dentro de la app.
        pasarela = softwareSystem "Pasarela de pagos PCI-DSS" "Tokeniza la tarjeta y cobra (RIE-01, ADR-009). Proveedor por definir." "Externo"

        # ---------------------------------------------------------------- Sistemas de soporte del equipo
        github = softwareSystem "GitHub" "12 repositorios + quickpatch, GitHub Actions y GitHub Container Registry (ADR-012, ADR-021)." "Soporte"
        observabilidad = softwareSystem "Observabilidad" "Prometheus, Loki y Grafana para producción y QA (VM1, ADR-022)." "Soporte"

        # ---------------------------------------------------------------- QUICKPATCH
        quickpatch = softwareSystem "QUICKPATCH" "Plataforma multi-tenant de servicios técnicos. Microservicios con arquitectura orientada a eventos (ADR-003)." {

            group "Clientes" {
                mobile = container "App móvil" "App de clientes, empresas cliente, técnicos y proveedores." "App nativa (iOS y Android)" "Mobile App" {
                    mobNavegacion = component "Navegación" "Rutas protegidas por sesión y por rol, y barra inferior según el rol: Inicio, Solicitudes u Ofertas o Equipo, y Cuenta (SCRUM-441)." "go_router · app/router y app/shell"
                    mobConfig = component "Configuración del ambiente" "URL base, Host del gateway y huella SHA-256 del certificado de QA (pinning)." "Dart · core/config"
                    mobHttp = component "Cliente HTTP" "Adjunta JWT y X-Correlation-Id, valida el certificado y traduce problem+json en errores de la app." "Dio · core/network"
                    mobSesion = component "Sesión" "Guarda el token en el almacenamiento seguro del dispositivo y expone usuario y rol." "Almacenamiento seguro del dispositivo · core/session"
                    mobAuth = component "Autenticación" "Login, registro de cliente hogar y registro de técnico o proveedor con su especialidad (SCRUM-55); registro de empresa con razón social, NIT y primer usuario (SCRUM-67)." "Riverpod · features/autenticacion"
                    mobInicio = component "Inicio por rol" "Acceso a la nueva solicitud y categorías de Catalog para el cliente; opciones (Disponibilidad y cobertura) y aviso de verificación para técnico y proveedor (SCRUM-441)." "Riverpod · features/inicio"
                    mobCuenta = component "Cuenta" "Datos de la sesión, licencias y cierre de sesión (SCRUM-441)." "Pantalla móvil · features/inicio"
                    mobDiseno = component "Sistema de diseño" "Tema azul con tokens y tipografía, y componentes compartidos: tarjeta de solicitud, chip de estado, selector de categoría, botones y estados vacío, de error y de carga (SCRUM-439)." "Componentes móviles · app/theme y shared/widgets"
                    mobSolicitudes = component "Solicitudes" "Nueva solicitud en tres pasos en un formulario (RNF-11) y detalle con su estado (SCRUM-442)." "Riverpod · features/solicitudes"
                    mobUbicacion = component "Ubicación del dispositivo" "Permiso y lectura del GPS con respaldo en LocationManager y límite de 15 s." "geolocator · features/solicitudes/data"
                    mobDisponibilidad = component "Disponibilidad y cobertura" "Interruptor de disponibilidad (bloqueado si está ocupado, RN-M6) y elección de las localidades en el mapa o con chips sincronizados (RF-13, RN-M9; SCRUM-89)." "Riverpod · features/disponibilidad"
                    mobMapa = component "Mapa de localidades" "Límites de las 20 localidades desde un GeoJSON de IDECA dentro de la app, con los códigos de GET /v1/localities; proyección, encuadre urbano y toque por localidad, sin mapa de fondo (R5, ADR-024)." "CustomPainter · features/disponibilidad"
                    mobTiempoReal = component "Estado en tiempo real" "WebSocket /v1/realtime con el token en la primera trama; si se cae, consulta el detalle cada 30 s (RF-11, RNF-06, ADR-023)." "Dart · core/realtime"
                    mobNotificaciones = component "Buzón de notificaciones" "Lista las notificaciones del usuario, las marca leídas y abre su solicitud (RIE-03, ADR-024; SCRUM-459)." "Riverpod · features/notificaciones"
                    mobChat = component "Chat de la solicitud" "Historial paginado, envío y mensajes nuevos por la trama chat.message; solo lectura al cerrar (RF-37, ADR-026; SCRUM-482)." "Riverpod · features/chat"
                    mobEmpresa = component "Usuarios de la empresa" "Empresa cliente del usuario y alta de otros usuarios con invitación (RF-06; SCRUM-67)." "Riverpod · features/empresa"
                    mobPagos = component "Pago y comprobante" "Pago con la pasarela simulada (la tarjeta se tokeniza en el teléfono) y comprobante en PDF (RF-22 a RF-24)." "Riverpod · features/pagos"
                }
                web = container "Panel web" "Panel de administración del tenant y de la plataforma." "SPA web + TypeScript" "Web Browser" {
                    webShell = component "Shell y rutas" "Rutas, layout con barra lateral y encabezado, y redirección a login o al inicio del rol (SCRUM-435)." "Enrutador web · app.routes y layout"
                    webSesion = component "Sesión" "Conserva el token y expone usuario y rol como signals." "Servicio web · core/sesion"
                    webInterceptor = component "Interceptor HTTP" "Adjunta JWT y X-Correlation-Id; ante un 401 cierra la sesión y vuelve al login." "Interceptor funcional · core/http"
                    webGuards = component "Guards de rol" "Permiten cada ruta según el rol y envían al inicio del rol si no corresponde (RN-U6)." "Guard funcional · core/guards"
                    webLogin = component "Inicio de sesión" "Formulario de acceso con validaciones y errores." "Componente web · features/autenticacion"
                    webInicio = component "Inicio" "Menú según el rol del administrador; la tarjeta de Técnicos lleva a su pantalla." "Componente web · features/inicio"
                    webTenants = component "Gestión de tenants" "Lista y busca los tenants, crea uno con nombre y NIT, y los activa o desactiva con confirmación (SCRUM-41, SCRUM-61)." "Componente web · features/tenants"
                    webTenantsApi = component "Cliente API de tenants" "GET, POST y PATCH /v1/platform/tenants." "HttpClient · features/tenants"
                    webTecnicos = component "Aprobación de técnicos" "Lista técnicos y proveedores del tenant por estado de verificación, con paginación; aprueba, rechaza, suspende y reactiva con confirmación y motivo (RF-19, RF-20; SCRUM-107, SCRUM-110)." "Componente web · features/tecnicos"
                    webTecnicosApi = component "Cliente API de técnicos" "GET /v1/admin/technicians y POST approve, reject y suspend (identity.v1.yaml); nombres de especialidad con GET /v1/catalog/categories." "HttpClient · features/tecnicos"
                    webDiseno = component "Sistema de diseño" "Tokens azules, fuente autoalojada y componentes reutilizables del panel; contraste WCAG AA verificado en el CI (SCRUM-433)." "SCSS · styles y shared"
                }
            }

            gateway = container "API Gateway" "Única entrada HTTP: quita /api y enruta al servicio por la ruta del contrato; cada servicio valida el JWT (ADR-018, SDD 6.3)." "Nginx (quickpatch-api-gateway)" "Gateway"

            group "Microservicios" {
                identity = container "Identity Service" "Autenticación, usuarios, tenants y auditoría." "ASP.NET Core (.NET 10)" "Microservicio" {
                    # Api
                    idEndpoints = component "IdentityEndpoints" "POST /v1/auth/register/client, /register/technician, /login y /password/setup; GET /v1/users/me; /v1/platform/tenants; /v1/admin/technicians (aprobar, rechazar, suspender); /v1/providers/me/technicians; GET /internal/v1/users (solo dentro del clúster)." "Minimal API · Api/Endpoints"
                    idCompanyEndpoints = component "CompanyEndpoints" "POST /v1/auth/register/company; GET /v1/companies/me y POST /v1/companies/me/users (RF-06)." "Minimal API · Api/Endpoints"
                    idSecurity = component "AuthenticatedUser y ForbiddenAuditHandler" "Lee usuario, tenant, rol y company_id del JWT y registra cada 403 (RNF-04)." "ASP.NET Core · Api/Security"
                    idHttp = component "CorrelationId y Problems" "Propaga X-Correlation-Id y responde application/problem+json." "ASP.NET Core · Api/Http"
                    idBootstrap = component "TenantAdminBootstrap" "Al arrancar crea el admin del tenant y el de plataforma desde el Secret (SCRUM-450)." "Hosted service · Api/Bootstrap"
                    # Application
                    idAuth = component "Auth" "LoginHandler (bloqueo tras 5 intentos), RegisterClientHandler, RegisterTechnicianHandler y EnsureTenantAdminHandler." "Casos de uso · Application/Auth"
                    idCompanies = component "Companies" "RegisterCompanyHandler, GetMyCompanyHandler y CreateCompanyUserHandler (RF-06)." "Casos de uso · Application/Companies"
                    idTechnicians = component "Technicians" "ChangeVerificationHandler y ListTechniciansHandler (RF-19, RF-20); CreateTeamTechnicianHandler y ListTeamHandler (RF-16); SetupPasswordHandler y RenewInvitationHandler." "Casos de uso · Application/Technicians"
                    idPlatform = component "Platform" "ListTenantsHandler, CreateTenantHandler y UpdateTenantStatusHandler con auditoría (RF-21)." "Casos de uso · Application/Platform"
                    idUsers = component "Users" "GetCurrentUserHandler y LookupUsersHandler (nombres por lote para otros servicios)." "Casos de uso · Application/Users"
                    # Domain
                    idDomain = component "Dominio de identidad" "User (LockoutPolicy), Tenant, TechnicianProfile (VerificationStatus), ClientCompany, PasswordSetupToken, AuditEntry y Roles." "Domain"
                    # Infrastructure
                    idPersistence = component "TenantUnitOfWork, PlatformUnitOfWork y repositorios" "UserRepository, TenantRepository, TechnicianProfileRepository, ClientCompanyRepository, PasswordSetupTokenRepository y AuditLog; RLS con app.current_tenant o SET LOCAL ROLE identity_platform." "EF Core + Npgsql · Infrastructure/Persistence"
                    idSecurityAdapters = component "RsaTokenIssuer y BCryptPasswordHasher" "Firma el JWT RS256 (ADR-018) y hace el hash de las contraseñas (RNF-03)." "Infrastructure/Security"
                    idOutbox = component "EfOutbox" "Guarda technician.registered y technician.verification-changed en outbox_events en la misma transacción (ADR-007)." "EF Core · Infrastructure/Messaging"
                    idPublisher = component "OutboxPublisher" "Publica los eventos pendientes y marca published_at." "BackgroundService · Infrastructure/Messaging"
                    idReputationConsumer = component "ReputationChangedConsumer" "Consume ranking.technician-reputation-changed y, con ApplyReputationHandler, proyecta average_rating, rating_count y low_reputation en technician_profiles; descarta lo atrasado por changedAt (ADR-027, ADR-017)." "Kafka consumer · Infrastructure/Messaging"
                }
                actors = container "Actors Service" "Proveedores, aliados y clientes como actores de negocio." "ASP.NET Core (.NET 10)" "Microservicio" {
                    acApi = component "API de actores" "Consulta y mantenimiento de actores del tenant." "Minimal API" "Planeado"
                    acProveedores = component "Proveedores de materiales" "Supplier: proveedor de materiales o repuestos (concepto evolutivo)." "Domain" "Planeado"
                    acAliados = component "Aliados" "Ally: técnico, profesional o empresa aliada." "Domain" "Planeado"
                    acClientes = component "Clientes" "Client: cliente hogar o empresarial." "Domain" "Planeado"
                    acPersistencia = component "Persistencia con RLS" "Repositorios de actores por tenant." "EF Core + Npgsql" "Planeado"
                }
                catalog = container "Catalog Service" "Categorías y especialidades de servicio." "ASP.NET Core (.NET 10)" "Microservicio" {
                    # Api
                    catEndpoints = component "CategoryEndpoints" "GET /v1/catalog/categories (obsoleta por ADR-025); POST y PATCH /v1/catalog/admin/categories." "Minimal API · Api/Endpoints"
                    catSecurity = component "AuthenticatedUser, ChannelOptions y ForbiddenAuditHandler" "Usuario, tenant y rol del JWT; sin token, el tenant del canal. Registra los 403." "ASP.NET Core · Api/Security"
                    catHttp = component "CorrelationId y Problems" "Propaga X-Correlation-Id y responde application/problem+json." "ASP.NET Core · Api/Http"
                    # Application
                    catHandlers = component "Categories" "ListCategoriesHandler, CreateCategoryHandler y UpdateCategoryHandler; nombre único por tenant (409)." "Casos de uso · Application/Categories"
                    # Domain
                    catDomain = component "Category" "Nombre normalizado, descripción, estado activo y updatedAt." "Domain/Categories"
                    # Infrastructure
                    catPersistence = component "TenantUnitOfWork y CategoryRepository" "service_categories bajo RLS (app.current_tenant)." "EF Core + Npgsql · Infrastructure/Persistence"
                    catOutbox = component "EfOutbox" "Guarda catalog.category-changed en outbox_events en la misma transacción (ADR-007)." "EF Core · Infrastructure/Persistence"
                    catResync = component "CategoryResync" "Vuelve a publicar todas las categorías una vez, con la descripción, para la réplica de ServiceRequest (ADR-025)." "Infrastructure/Persistence"
                    catPublisher = component "OutboxPublisher" "Publica los eventos pendientes y marca published_at." "BackgroundService · Infrastructure/Messaging"
                }
                serviceRequest = container "ServiceRequest Service" "Ciclo de vida de la solicitud de servicio." "ASP.NET Core (.NET 10)" "Microservicio" {
                    # Api
                    srRequestEndpoints = component "ServiceRequestEndpoints" "POST, GET y lista de /v1/service-requests, POST /location-preview, POST /{id}/cancel y GET /v1/technicians/me/service-requests." "Minimal API · Api/Endpoints"
                    srReferenceEndpoints = component "ReferenceEndpoints" "GET /v1/service-requests/categories y /localities desde las réplicas (ADR-025)." "Minimal API · Api/Endpoints"
                    srQuoteEndpoints = component "QuoteEndpoints" "GET y POST /v1/service-requests/{id}/quotes, accept y reject (RF-34, RF-35)." "Minimal API · Api/Endpoints"
                    srExecutionEndpoints = component "ExecutionEndpoints" "POST /start, /evidence y /complete; GET de las evidencias (RF-14, RF-15)." "Minimal API · Api/Endpoints"
                    srRatingEndpoints = component "RatingEndpoints" "POST /v1/service-requests/{id}/rating: dueño de la solicitud pagada; 403, 404 y 409 (RF-12, DD 8.3.11)." "Minimal API · Api/Endpoints"
                    srAdminEndpoints = component "AdminServiceRequestEndpoints" "Lista y resumen por estado del admin del tenant y de plataforma (RF-18)." "Minimal API · Api/Endpoints"
                    srSecurity = component "AuthenticatedUser y ForbiddenAuditHandler" "Usuario, tenant, rol y company_id de los claims del JWT, nunca del cuerpo (RN-U3); registra los 403." "ASP.NET Core · Api/Security"
                    # Application
                    srRequests = component "ServiceRequests" "CreateServiceRequestHandler, GetServiceRequestHandler, CancelServiceRequestHandler, PreviewLocationHandler, ListTechnicianServiceRequestsHandler y los de administración." "Casos de uso · Application/ServiceRequests"
                    srReferences = component "References" "ListCategoriesHandler y ListLocalitiesHandler." "Casos de uso · Application/References"
                    srQuotes = component "Quotes" "IssueQuoteHandler, RespondQuoteHandler y ExpireQuoteHandler (máximo 3, vencimiento)." "Casos de uso · Application/Quotes"
                    srExecution = component "Execution" "StartServiceHandler, UploadEvidenceHandler y CompleteServiceHandler." "Casos de uso · Application/Execution"
                    srEventHandlers = component "Manejadores de eventos" "ApplyCategoryChangedHandler, MatchingStatusHandler y PaymentEventsHandler: aplican cada evento una vez por eventId." "Casos de uso · Application/Categories, Matching y Payments"
                    srRating = component "Ratings" "RateServiceRequestHandler: valida dueño, estado pagado y que no esté calificada (RN-R1 a RN-R3) y deja service-request.rated en el Outbox (ADR-027)." "Casos de uso · Application/Ratings"
                    # Domain
                    srDomain = component "Dominio de la solicitud" "ServiceRequest (transiciones RN-SR2 a RN-SR7), Quote, ServiceEvidence, Rating, CategoryReplica, GeoPoint, CoverageArea y Locality." "Domain"
                    # Infrastructure
                    srPersistence = component "TenantUnitOfWork y repositorios" "ServiceRequestRepository, QuoteRepository, EvidenceRepository, RatingRepository, CategoryReplicaRepository y ProcessedEventRepository bajo RLS." "EF Core + Npgsql · Infrastructure/Persistence"
                    srOutbox = component "EfOutbox" "Guarda los eventos de la solicitud en outbox_events en la misma transacción (ADR-007)." "EF Core · Infrastructure/Persistence"
                    srPublisher = component "OutboxPublisher" "Lotes con FOR UPDATE SKIP LOCKED; publica y marca published_at." "BackgroundService · Infrastructure/Messaging"
                    srCategoryConsumer = component "CategoryChangedConsumer" "Consume catalog.category-changed." "Kafka consumer · Infrastructure/Messaging"
                    srMatchingConsumer = component "MatchingEventsConsumer" "Consume matching.technician-assigned, .no-technician-available y .search-resumed." "Kafka consumer · Infrastructure/Messaging"
                    srPaymentConsumer = component "PaymentEventsConsumer" "Consume payment.approved y payment.rejected." "Kafka consumer · Infrastructure/Messaging"
                    srGeocoder = component "NominatimGeocoder" "Convierte la dirección en coordenadas dentro de Bogotá (RIE-02, ADR-024)." "HttpClient · Infrastructure/Geocoding"
                    srStorage = component "GarageEvidenceStorage" "Guarda y sirve las fotos de la evidencia (ADR-016)." "S3 · Infrastructure/Storage"
                    srUserDirectory = component "IdentityUserDirectory" "Nombres y contacto por lote con GET /internal/v1/users; si falla, devuelve vacío (ADR-025)." "HttpClient · Infrastructure/Identity"
                    srScheduling = component "QuoteExpirer y RedisDistributedLock" "Vence las cotizaciones sin respuesta; una sola réplica a la vez (RN-Q6)." "BackgroundService · Infrastructure/Scheduling"
                }
                matching = container "Matching Service" "Asignación geoespacial de técnicos." "Java 25 + Spring Boot 4.1" "Microservicio" {
                    maListener = component "Listener de service-request.created" "Valida el contrato, descarta mensajes inválidos y propaga correlationId en el MDC." "@KafkaListener · infrastructure/messaging"
                    maHandler = component "Manejador del evento" "En una transacción por tenant registra el evento y, si es nuevo, inicia el matching (APPLIED o DUPLICATE)." "application/events"
                    maProcesados = component "Registro de eventos procesados" "INSERT ... ON CONFLICT (event_id) DO NOTHING en processed_events." "JDBC · infrastructure/persistence"
                    maTransaccion = component "Transacción por tenant" "set_config app.current_tenant antes de cada trabajo (RLS)." "JDBC · infrastructure/persistence"
                    maBusqueda = component "Búsqueda de candidatos" "Técnicos aprobados, disponibles, de la especialidad, con cobertura en la ubicación y sin otra oferta pendiente; los ordena por distancia (RN-M9, PostGIS)." "PostGIS"
                    maOfertas = component "Ofertas y asignación" "Registra la oferta con vencimiento a 3 min (RN-M1, RN-M8) y publica matching.offer-created; al aceptar, el técnico pasa a ocupado y publica matching.technician-assigned (RN-M2, RN-M4, RN-M6, RN-M7); si rechaza o vence, ofrece al siguiente (RN-M3); sin candidatos publica matching.no-technician-available." "Outbox"
                    maApi = component "API de técnicos y ofertas" "Localidades; disponibilidad y cobertura del técnico; ofertas pendientes, aceptar y rechazar (matching.v1.yaml 1.0.0)." "Spring MVC"
                    maProyeccion = component "Proyección del técnico" "Consume technician.registered y technician.verification-changed y guarda especialidad y verificación (P-01, ADR-017); reanuda solicitudes en espera (RN-M10)." "@KafkaListener"
                }
                ranking = container "Ranking Service" "Reputación de técnicos desde las calificaciones (ADR-027)." "ASP.NET Core (.NET 10)" "Microservicio" {
                    # Application
                    raHandler = component "ServiceRequestRatedHandler" "Suma la calificación bajo el tenant del evento, una vez por eventId y por solicitud, y deja ranking.technician-reputation-changed en el Outbox." "Casos de uso · Application/Reputation"
                    # Domain
                    raDomain = component "Dominio de reputación" "TechnicianReputation (cantidad, suma, promedio NUMERIC(2,1) y reputación baja con 5 o más calificaciones y promedio menor a 3.0, AC9-E2) y AppliedRating." "Domain/Reputation"
                    # Infrastructure
                    raPersistence = component "TenantUnitOfWork y repositorios" "ReputationRepository (FOR UPDATE por técnico) y ProcessedEventRepository bajo RLS." "EF Core + Npgsql · Infrastructure/Persistence"
                    raOutbox = component "EfOutbox" "Guarda ranking.technician-reputation-changed en outbox_events en la misma transacción (ADR-007)." "EF Core · Infrastructure/Persistence"
                    raPublisher = component "OutboxPublisher" "Publica los eventos pendientes con el rol ranking_outbox y marca published_at." "BackgroundService · Infrastructure/Messaging"
                    raConsumer = component "ServiceRequestRatedConsumer" "Consume service-request.rated; confirma el offset después de aplicar y descarta lo que no cumple el contrato." "Kafka consumer · Infrastructure/Messaging"
                }
                payments = container "Payments Service" "Pagos tokenizados y facturación." "ASP.NET Core (.NET 10)" "Microservicio" {
                    # Api
                    paPaymentEndpoints = component "PaymentEndpoints" "GET y POST /v1/service-requests/{id}/payment con el token de la tarjeta; nunca recibe PAN ni CVV (RNF-01)." "Minimal API · Api/Endpoints"
                    paInvoiceEndpoints = component "InvoiceEndpoints" "GET /v1/payments/{id}/invoice en JSON o PDF (RF-24)." "Minimal API · Api/Endpoints"
                    paSecurity = component "AuthenticatedUser y ForbiddenAuditHandler" "Usuario, tenant, rol y company_id del JWT; registra los 403." "ASP.NET Core · Api/Security"
                    # Application
                    paPayments = component "Payments" "GetPaymentHandler, PayHandler y ReconcilePaymentsHandler." "Casos de uso · Application/Payments"
                    paCompletedHandler = component "ServiceRequestCompletedHandler" "Crea el pago pendiente con el total de la cotización aceptada (RN-P4)." "Casos de uso · Application/Payments"
                    paInvoices = component "Invoices" "GetInvoiceHandler: solo el pagador lee el comprobante." "Casos de uso · Application/Invoices"
                    # Domain
                    paDomain = component "Dominio de pagos" "Payment (estados y RejectionReasons), Invoice y Billing." "Domain/Payments"
                    # Infrastructure
                    paPersistence = component "TenantUnitOfWork y repositorios" "PaymentRepository y ProcessedEventRepository bajo RLS." "EF Core + Npgsql · Infrastructure/Persistence"
                    paOutbox = component "EfOutbox" "Guarda payment.approved o payment.rejected en outbox_events en la misma transacción." "EF Core · Infrastructure/Persistence"
                    paPublisher = component "OutboxPublisher" "Publica los eventos pendientes y marca published_at." "BackgroundService · Infrastructure/Messaging"
                    paCompletedConsumer = component "ServiceRequestCompletedConsumer" "Consume service-request.completed." "Kafka consumer · Infrastructure/Messaging"
                    paReconciliation = component "ReconciliationJob" "Cierra los pagos que la pasarela dejó sin respuesta (AC9-E5)." "BackgroundService · Infrastructure/Messaging"
                    paProvider = component "SimulatedPaymentProvider" "Pasarela simulada del MVP detrás del puerto IPaymentProvider (ADR-009 modificado)." "Infrastructure/Providers"
                    paPdf = component "InvoicePdfRenderer" "Arma el PDF del comprobante, sin validez fiscal." "Infrastructure/Documents"
                    paReceived = component "Pagos recibidos" "GET /v1/payments/received?page=&size= para el técnico (RF-25, DD 8)." "Minimal API" "Planeado"
                    paWebhook = component "Receptor de webhooks del PSP" "Confirmará el resultado de forma idempotente con la pasarela certificada." "Minimal API" "Planeado"
                }
                communication = container "Communication Service" "Notificaciones del ciclo de servicio dentro de la app: canal en tiempo real y buzón (ADR-023, ADR-024)." "ASP.NET Core (.NET 10)" "Microservicio" {
                    coConsumidores = component "Consumidores de eventos" "service-request.*, matching.* y payment.*, una vez por eventId." "Kafka consumer"
                    coPlantillas = component "Plantillas de notificación" "Arma el mensaje según el evento y el destinatario." "Application"
                    coCanal = component "Canal en tiempo real" "WebSocket /v1/realtime: valida el token de la primera trama y avisa a cada usuario conectado, dentro de su tenant (ADR-023)." "ASP.NET Core WebSockets"
                    coChat = component "Chat de la solicitud" "Réplica de participantes desde service-request.status-changed, mensajes en chat_messages y GET y POST /v1/service-requests/{id}/messages; entrega chat.message por el canal (RF-37, ADR-026)." "Minimal API + Kafka consumer"
                    coBuzon = component "Buzón de notificaciones" "Guarda cada notificación por usuario y tenant y la expone a la app (ADR-024)." "Minimal API"
                }
            }

            group "Mensajería y almacenamiento" {
                kafka = container "Apache Kafka" "Bus de eventos: un topic por tipo de evento (quickpatch-kafka/topics)." "Apache Kafka (KRaft)" "Queue"
                redis = container "Redis" "Coordinación temporal: hoy solo el bloqueo con el que una réplica de ServiceRequest vence las cotizaciones; sin caché en el MVP. Un usuario por servicio limitado a <servicio>:*." "Redis" "Database"
                garage = container "Garage" "Evidencias fotográficas y respaldos de PostgreSQL (ADR-016)." "Garage (S3)" "Database"
            }

            geocodificador = container "Geocodificador" "Convierte direcciones de Bogotá en coordenadas; solo el mapa de Bogotá y su propio PostgreSQL (RIE-02, ADR-024, excepción a ADR-014)." "Nominatim (OpenStreetMap)"

            group "PostgreSQL + PostGIS (una instancia, una base por servicio, ADR-014)" {
                dbIdentity = container "db_identity" "tenants, users, client_companies, technician_profiles, password_setup_tokens y audit_logs." "PostgreSQL" "Database"
                dbActors = container "db_actors" "Actores de negocio." "PostgreSQL" "Database"
                dbCatalog = container "db_catalog" "service_categories y outbox_events." "PostgreSQL" "Database"
                dbServiceRequest = container "db_service_request" "service_requests, service_request_categories, outbox_events y processed_events." "PostgreSQL + PostGIS" "Database"
                dbMatching = container "db_matching" "Disponibilidad, cobertura, intentos y processed_events." "PostgreSQL + PostGIS" "Database"
                dbRanking = container "db_ranking" "technician_reputations, applied_ratings, processed_events y outbox_events." "PostgreSQL" "Database"
                dbPayments = container "db_payments" "payments e invoices, sin PAN ni CVV; outbox_events y processed_events." "PostgreSQL" "Database"
                dbCommunication = container "db_communication" "Buzón por usuario y chat de la solicitud." "PostgreSQL" "Database"
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

        # App móvil
        mobNavegacion -> mobSesion "Consulta usuario y rol en"
        mobNavegacion -> mobAuth "Abre"
        mobNavegacion -> mobInicio "Abre"
        mobNavegacion -> mobSolicitudes "Abre"
        mobNavegacion -> mobCuenta "Abre"
        mobNavegacion -> mobDisponibilidad "Abre"
        mobNavegacion -> mobNotificaciones "Abre"
        mobNavegacion -> mobEmpresa "Abre"
        mobSolicitudes -> mobChat "Abre el chat de la solicitud en"
        mobSolicitudes -> mobPagos "Abre el pago y el comprobante en"
        mobChat -> mobHttp "GET y POST mensajes con"
        mobChat -> mobTiempoReal "Recibe chat.message de"
        mobEmpresa -> mobHttp "GET y POST /v1/companies/me con"
        mobPagos -> mobHttp "GET y POST el pago y GET el comprobante con"
        mobInicio -> mobHttp "GET categorías con"
        mobInicio -> mobDiseno "Arma las pantallas con"
        mobSolicitudes -> mobDiseno "Arma las pantallas con"
        mobDisponibilidad -> mobDiseno "Arma la pantalla con"
        mobDisponibilidad -> mobMapa "Elige las localidades en"
        mobDisponibilidad -> mobHttp "GET localidades; GET y PUT disponibilidad y cobertura con"
        mobAuth -> mobSesion "Guarda el token en"
        mobAuth -> mobHttp "POST /v1/auth/* con"
        mobSolicitudes -> mobUbicacion "Obtiene las coordenadas con"
        mobSolicitudes -> mobHttp "GET categorías, POST y GET solicitudes con"
        mobSolicitudes -> mobTiempoReal "Escucha cambios de estado en"
        mobNotificaciones -> mobHttp "GET el buzón con"
        mobHttp -> mobConfig "Lee URL base y certificado de"
        mobHttp -> mobSesion "Lee el token de"
        # Primero la relación HTTPS: Structurizr crea una sola relación implícita entre dos contenedores.
        mobHttp -> gateway "Llama a la API" "HTTPS/JSON"
        # El canal de ADR-023 es otra conexión entre los mismos contenedores: se declara explícita.
        mobile -> gateway "Abre /api/v1/realtime" "WebSocket (wss)"
        mobTiempoReal -> gateway "Abre /api/v1/realtime" "WebSocket (wss)"

        # Panel web
        webShell -> webGuards "Protege las rutas con"
        webShell -> webLogin "Abre"
        webShell -> webInicio "Abre"
        webShell -> webTenants "Abre"
        webShell -> webTecnicos "Abre"
        webShell -> webDiseno "Arma el layout con"
        webTenants -> webDiseno "Usa los componentes de"
        webTecnicos -> webDiseno "Usa los componentes de"
        webGuards -> webSesion "Lee el rol de"
        webLogin -> webSesion "Inicia sesión con"
        webSesion -> webInterceptor "Llama a /v1/auth/login con"
        webTenants -> webTenantsApi "Lista, crea y cambia el estado con"
        webTenantsApi -> webInterceptor "Envía las peticiones por"
        webTecnicos -> webTecnicosApi "Lista y cambia la verificación con"
        webTecnicosApi -> webInterceptor "Envía las peticiones por"
        webInterceptor -> webSesion "Lee el token de"
        webInterceptor -> gateway "Llama a la API" "HTTPS/JSON"

        # API Gateway → servicios
        gateway -> idEndpoints "Enruta /api/v1/auth, /users, /platform, /admin/technicians y /providers" "HTTP"
        gateway -> idCompanyEndpoints "Enruta /api/v1/auth/register/company y /api/v1/companies" "HTTP"
        gateway -> catEndpoints "Enruta /api/v1/catalog" "HTTP"
        gateway -> srRequestEndpoints "Enruta /api/v1/service-requests y /api/v1/technicians/me/service-requests" "HTTP"
        gateway -> srReferenceEndpoints "Enruta /api/v1/service-requests/categories y /localities" "HTTP"
        gateway -> srQuoteEndpoints "Enruta /api/v1/service-requests/{id}/quotes" "HTTP"
        gateway -> srExecutionEndpoints "Enruta /start, /evidence y /complete" "HTTP"
        gateway -> srRatingEndpoints "Enruta /api/v1/service-requests/{id}/rating" "HTTP"
        gateway -> srAdminEndpoints "Enruta /api/v1/admin y /api/v1/platform/service-requests" "HTTP"
        gateway -> acApi "Enruta /api/v1/actors" "HTTP" "Planeado"
        gateway -> paPaymentEndpoints "Enruta /api/v1/service-requests/{id}/payment" "HTTP"
        gateway -> paInvoiceEndpoints "Enruta /api/v1/payments" "HTTP"
        gateway -> paReceived "Enrutará /api/v1/payments/received" "HTTP" "Planeado"
        gateway -> maApi "Enruta /api/v1/matching, /api/v1/technicians y /api/v1/localities" "HTTP"
        gateway -> coCanal "Enruta /api/v1/realtime" "WebSocket"
        gateway -> coBuzon "Enruta /api/v1/notifications" "HTTP"

        # Identity
        idEndpoints -> idSecurity "Autoriza por rol con"
        idEndpoints -> idHttp "Responde errores con"
        idCompanyEndpoints -> idSecurity "Autoriza por rol con"
        idEndpoints -> idAuth "Invoca"
        idEndpoints -> idTechnicians "Invoca"
        idEndpoints -> idPlatform "Invoca"
        idEndpoints -> idUsers "Invoca"
        idCompanyEndpoints -> idCompanies "Invoca"
        idBootstrap -> idAuth "Asegura los administradores iniciales con"
        idAuth -> idDomain "Aplica las reglas de"
        idCompanies -> idDomain "Aplica las reglas de"
        idTechnicians -> idDomain "Aplica las reglas de"
        idAuth -> idSecurityAdapters "Verifica la contraseña y emite el JWT con"
        idCompanies -> idSecurityAdapters "Emite el token con company_id con"
        idAuth -> idPersistence "Lee y guarda por ITenantUnitOfWork con"
        idCompanies -> idPersistence "Guarda la empresa y sus usuarios con"
        idTechnicians -> idPersistence "Cambia la verificación y el equipo con"
        idUsers -> idPersistence "Consulta usuarios del tenant con"
        idPlatform -> idPersistence "Cambia tenants por IPlatformUnitOfWork con"
        idAuth -> idOutbox "Registra technician.registered con"
        idTechnicians -> idOutbox "Registra technician.registered y technician.verification-changed con"
        idPersistence -> dbIdentity "Lee y escribe (RLS)" "SQL"
        idOutbox -> dbIdentity "INSERT en outbox_events" "SQL"
        idPublisher -> dbIdentity "Lee pendientes y marca published_at" "SQL"
        idPublisher -> kafka "Publica technician.registered y technician.verification-changed" "Kafka"
        idReputationConsumer -> kafka "Consume ranking.technician-reputation-changed" "Kafka"
        idReputationConsumer -> idPersistence "Actualiza la reputación del técnico con"

        # Actors
        acApi -> acProveedores "Usa" "" "Planeado"
        acApi -> acAliados "Usa" "" "Planeado"
        acApi -> acClientes "Usa" "" "Planeado"
        acApi -> acPersistencia "Lee y escribe con" "" "Planeado"
        acPersistencia -> dbActors "Lee y escribe (RLS)" "SQL" "Planeado"

        # Catalog
        catEndpoints -> catSecurity "Autoriza con"
        catEndpoints -> catHttp "Responde errores con"
        catEndpoints -> catHandlers "Invoca"
        catHandlers -> catDomain "Aplica las reglas de"
        catHandlers -> catPersistence "Guarda y lista por ITenantUnitOfWork con"
        catHandlers -> catOutbox "Registra catalog.category-changed con"
        catResync -> catOutbox "Registra el estado completo de cada categoría con"
        catPersistence -> dbCatalog "Lee y escribe service_categories (RLS)" "SQL"
        catOutbox -> dbCatalog "INSERT en outbox_events" "SQL"
        catPublisher -> dbCatalog "Lee pendientes y marca published_at" "SQL"
        catPublisher -> kafka "Publica catalog.category-changed" "Kafka"

        # ServiceRequest
        srRequestEndpoints -> srSecurity "Toma el usuario autenticado de"
        srRequestEndpoints -> srRequests "Invoca"
        srReferenceEndpoints -> srReferences "Invoca"
        srQuoteEndpoints -> srQuotes "Invoca"
        srExecutionEndpoints -> srExecution "Invoca"
        srAdminEndpoints -> srRequests "Invoca los casos de administración de"
        srRequests -> srDomain "Crea y cambia el estado con"
        srQuotes -> srDomain "Aplica las reglas de la cotización con"
        srExecution -> srDomain "Inicia y completa con"
        srEventHandlers -> srDomain "Aplica la transición con"
        srRequests -> srGeocoder "Obtiene las coordenadas de la dirección con"
        srRequests -> srUserDirectory "Pide nombres y contacto con"
        srExecution -> srStorage "Guarda las fotos con"
        srRequests -> srPersistence "Guarda y consulta por ITenantUnitOfWork con"
        srReferences -> srPersistence "Lee las réplicas con"
        srQuotes -> srPersistence "Guarda las cotizaciones con"
        srExecution -> srPersistence "Guarda las evidencias con"
        srEventHandlers -> srPersistence "Registra el eventId y aplica el cambio con"
        srRequests -> srOutbox "Registra .created, .status-changed y .cancelled con"
        srQuotes -> srOutbox "Registra .quoted, .quote-accepted y .quote-rejected con"
        srExecution -> srOutbox "Registra .started y .completed con"
        srRating -> srOutbox "Registra service-request.rated con"
        srRating -> srPersistence "Guarda la calificación con"
        srRating -> srDomain "Valida el puntaje y el comentario con"
        srRatingEndpoints -> srSecurity "Toma el usuario autenticado de"
        srRatingEndpoints -> srRating "Invoca"
        srCategoryConsumer -> kafka "Consume catalog.category-changed" "Kafka"
        srMatchingConsumer -> kafka "Consume matching.*" "Kafka"
        srPaymentConsumer -> kafka "Consume payment.*" "Kafka"
        srCategoryConsumer -> srEventHandlers "Entrega el evento a"
        srMatchingConsumer -> srEventHandlers "Entrega el evento a"
        srPaymentConsumer -> srEventHandlers "Entrega el evento a"
        srScheduling -> srQuotes "Vence las cotizaciones con"
        srScheduling -> redis "Toma el candado de la tarea" "RESP"
        srPersistence -> dbServiceRequest "Lee y escribe service_requests, réplicas y processed_events (RLS)" "SQL"
        srOutbox -> dbServiceRequest "INSERT en outbox_events" "SQL"
        srPublisher -> dbServiceRequest "Lee pendientes y marca published_at" "SQL"
        srPublisher -> kafka "Publica service-request.*" "Kafka"
        srGeocoder -> geocodificador "Busca la dirección en Bogotá" "HTTP"
        srStorage -> garage "Guarda y lee las fotos del servicio" "S3/HTTPS"
        srUserDirectory -> idEndpoints "GET /internal/v1/users con el JWT del usuario" "HTTP"
        idEndpoints -> idUsers "Resuelve la consulta interna con"

        # Matching
        maListener -> kafka "Consume service-request.created" "Kafka"
        maListener -> maHandler "Entrega el evento válido a"
        maHandler -> maTransaccion "Abre la transacción del tenant con"
        maHandler -> maProcesados "Registra el eventId en"
        maHandler -> maBusqueda "Inicia el matching con"
        maBusqueda -> maOfertas "Entrega el candidato más cercano a"
        maBusqueda -> redis "Cachea disponibilidad en" "RESP" "Planeado"
        maOfertas -> kafka "Publica matching.offer-created, .technician-assigned, .no-technician-available y .search-resumed" "Kafka"
        maOfertas -> dbMatching "Registra el intento y su respuesta en matching_attempts (RLS)" "SQL"
        maApi -> maOfertas "Acepta o rechaza la oferta con"
        maApi -> dbMatching "Lee y cambia disponibilidad y cobertura (RLS)" "SQL"
        maProyeccion -> kafka "Consume technician.registered y technician.verification-changed" "Kafka"
        maProyeccion -> dbMatching "Actualiza la proyección en technician_availability" "SQL"
        maProyeccion -> maBusqueda "Reanuda las solicitudes en espera con (RN-M10)"
        maProcesados -> dbMatching "INSERT en processed_events" "SQL"
        maTransaccion -> dbMatching "set_config app.current_tenant" "SQL"
        maBusqueda -> dbMatching "Consulta disponibilidad y cobertura (PostGIS)" "SQL"

        # Ranking
        raConsumer -> kafka "Consume service-request.rated" "Kafka"
        raConsumer -> raHandler "Entrega la calificación a"
        raHandler -> raDomain "Recalcula la reputación con"
        raHandler -> raPersistence "Registra el eventId y guarda la reputación con"
        raHandler -> raOutbox "Registra ranking.technician-reputation-changed con"
        raPersistence -> dbRanking "Lee y escribe technician_reputations, applied_ratings y processed_events (RLS)" "SQL"
        raOutbox -> dbRanking "INSERT en outbox_events" "SQL"
        raPublisher -> dbRanking "Lee pendientes y marca published_at" "SQL"
        raPublisher -> kafka "Publica ranking.technician-reputation-changed" "Kafka"

        # Payments
        paPaymentEndpoints -> paSecurity "Toma el usuario autenticado de"
        paInvoiceEndpoints -> paSecurity "Toma el usuario autenticado de"
        paPaymentEndpoints -> paPayments "Invoca"
        paInvoiceEndpoints -> paInvoices "Invoca"
        paCompletedConsumer -> kafka "Consume service-request.completed" "Kafka"
        paCompletedConsumer -> paCompletedHandler "Entrega el evento a"
        paReconciliation -> paPayments "Concilia los pagos sin respuesta con"
        paPayments -> paDomain "Aplica los estados del pago con"
        paCompletedHandler -> paDomain "Crea el pago pendiente con"
        paPayments -> paProvider "Cobra por IPaymentProvider con"
        paProvider -> pasarela "Cobrará con la pasarela certificada" "HTTPS" "Planeado"
        pasarela -> paWebhook "Notifica el resultado del cobro" "HTTPS" "Planeado"
        paWebhook -> paPayments "Confirmará el pago con" "" "Planeado"
        paInvoices -> paPdf "Arma el PDF con"
        paPayments -> paPersistence "Guarda el pago y la factura por ITenantUnitOfWork con"
        paCompletedHandler -> paPersistence "Registra el eventId y el pago con"
        paInvoices -> paPersistence "Lee el comprobante con"
        paPayments -> paOutbox "Registra payment.approved o payment.rejected con"
        paReceived -> paPersistence "Leerá los pagos aprobados del técnico con" "" "Planeado"
        paPersistence -> dbPayments "Lee y escribe payments, invoices y processed_events (RLS)" "SQL"
        paOutbox -> dbPayments "INSERT en outbox_events" "SQL"
        paPublisher -> dbPayments "Lee pendientes y marca published_at" "SQL"
        paPublisher -> kafka "Publica payment.*" "Kafka"

        # Communication
        coConsumidores -> kafka "Consume service-request.*, matching.* y payment.*" "Kafka"
        coConsumidores -> coPlantillas "Arma el mensaje con"
        coPlantillas -> coCanal "Avisa a los usuarios conectados con"
        coPlantillas -> coBuzon "Guarda la notificación con"
        coBuzon -> dbCommunication "Lee y escribe el buzón (RLS)" "SQL"
        coChat -> kafka "Consume service-request.status-changed" "Kafka"
        coChat -> coCanal "Entrega chat.message con"
        coChat -> dbCommunication "Lee y escribe chat_participants y chat_messages (RLS)" "SQL"
        gateway -> coChat "Enruta /api/v1/service-requests/{id}/messages (excepción de ADR-025)" "HTTP"

        # Soporte
        github -> quickpatch "Construye imágenes y despliega con el runner de VM1" "HTTPS"
        quickpatch -> observabilidad "Envía métricas y logs" "HTTP"

        # ================================================================ Despliegue (ADR-022, INFRASTRUCTURE 3.3)
        produccion = deploymentEnvironment "Producción" {
            deploymentNode "Teléfono del usuario" "" "Android o iOS" {
                mobProd = containerInstance mobile
            }
            deploymentNode "Navegador del administrador" "" "Chrome, Edge o Firefox" {
                webBrowserProd = infrastructureNode "Navegador" "Ejecuta el panel web que sirve el gateway de VM3." "HTML + JS"
            }
            deploymentNode "Red privada del laboratorio 10.43.x.x" "Solo el 443 de VM1 es alcanzable desde la VPN (R9); firewall default deny incoming." "" {
                deploymentNode "VM1 · Herramientas · 10.43.100.168" "Entrada única y herramientas compartidas por los dos ambientes." "4 vCPU · 11 GiB RAM · 68 GB" {
                    proxyProd = infrastructureNode "Entrada Nginx :443" "Termina TLS 1.2/1.3 (autofirmado) y reenvía por nombre, sin cambiar Host: quickpatch.internal al gateway de VM3; grafana.quickpatch.internal a Grafana (ADR-028)." "Nginx"
                    runnerProd = infrastructureNode "Runner de GitHub Actions" "kubectl y k6; despliega la imagen de main." "GitHub Actions runner"
                    observabilidadProd = softwareSystemInstance observabilidad
                }
                deploymentNode "VM3 · Aplicación · 10.43.98.205" "Los servicios llegan a VM4 (PostgreSQL 5432, Redis 6379) y a VM6 (Kafka 9092, Garage 9000)." "4 vCPU · 11 GiB RAM · 68 GB" {
                    deploymentNode "Docker, red del host" "Nginx del gateway de producción en el puerto 8080, abierto solo a VM1 (ADR-028): /api va a Traefik y / sirve el panel desde /opt/quickpatch/gateway/panel (hoy, página provisional)." "Docker" {
                        gatewayProd = containerInstance gateway
                        webProd = containerInstance web
                    }
                    deploymentNode "k3s (un nodo)" "" "k3s + Traefik" {
                        traefikProd = infrastructureNode "Traefik" "Ingress del clúster en NodePort 30080." "Traefik"
                        identityProd = containerInstance identity
                        actorsProd = containerInstance actors {
                            tags "Planeado"
                        }
                        catalogProd = containerInstance catalog
                        serviceRequestProd = containerInstance serviceRequest
                        matchingProd = containerInstance matching
                        rankingProd = containerInstance ranking {
                            tags "Planeado"
                        }
                        paymentsProd = containerInstance payments {
                            tags "Planeado"
                        }
                        communicationProd = containerInstance communication {
                            tags "Planeado"
                        }
                    }
                }
                deploymentNode "VM4 · Datos · 10.43.98.209" "Recibe 5432 y 6379 desde VM3; respaldo diario a Garage de VM6." "4 vCPU · 11 GiB RAM · 68 GB" {
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
                    geocodificadorProd = containerInstance geocodificador
                }
                deploymentNode "VM6 · Mensajería y almacenamiento · 10.43.99.12" "Recibe 9092 y 9000 desde VM3 y 9000 desde VM4." "4 vCPU · 11 GiB RAM · 68 GB" {
                    kafkaProd = containerInstance kafka
                    garageProd = containerInstance garage
                }
            }
            webBrowserProd -> proxyProd "Abre https://quickpatch.internal" "HTTPS"
            mobProd -> proxyProd "Llama a https://quickpatch.internal/api (certificado fijado)" "HTTPS"
            proxyProd -> gatewayProd "Reenvía quickpatch.internal a VM3:8080" "HTTP"
            gatewayProd -> traefikProd "Envía /api a :30080" "HTTP"
            runnerProd -> traefikProd "kubectl apply de la imagen de main" "HTTPS"
        }

        qa = deploymentEnvironment "QA" {
            deploymentNode "Teléfono o emulador de prueba" "" "Android" {
                mobQa = containerInstance mobile
            }
            deploymentNode "Red privada del laboratorio 10.43.x.x" "QA no se conecta con producción; solo VM1 llega a los dos (ADR-022)." "" {
                deploymentNode "VM1 · Herramientas · 10.43.100.168" "Misma VM1 de producción." "4 vCPU · 11 GiB RAM · 68 GB" {
                    proxyQa = infrastructureNode "Entrada Nginx :443" "La misma entrada: qa.quickpatch.internal al gateway de VM2, solo desde las redes del equipo (ADR-028)." "Nginx"
                    runnerQa = infrastructureNode "Runner de GitHub Actions" "Despliega release/* y corre Newman, Playwright, ZAP y k6 contra QA." "GitHub Actions runner"
                    observabilidadQa = softwareSystemInstance observabilidad
                }
                deploymentNode "VM2 · Aplicación · 10.43.98.15" "Los servicios llegan a VM5 (5432, 6379) y a VM7 (9092, 9000)." "4 vCPU · 11 GiB RAM · 68 GB" {
                    deploymentNode "Docker, red del host" "Nginx del gateway de QA en el puerto 8080, abierto solo a VM1 (ADR-028): /api va a Traefik y / sirve el panel de QA (build de release/*)." "Docker" {
                        gatewayQa = containerInstance gateway
                        webQa = containerInstance web
                    }
                    deploymentNode "k3s (un nodo)" "" "k3s + Traefik" {
                        traefikQa = infrastructureNode "Traefik" "Ingress del clúster en NodePort 30080." "Traefik"
                        identityQa = containerInstance identity
                        actorsQa = containerInstance actors {
                            tags "Planeado"
                        }
                        catalogQa = containerInstance catalog
                        serviceRequestQa = containerInstance serviceRequest
                        matchingQa = containerInstance matching
                        rankingQa = containerInstance ranking {
                            tags "Planeado"
                        }
                        paymentsQa = containerInstance payments
                        communicationQa = containerInstance communication
                    }
                }
                deploymentNode "VM5 · Datos · 10.43.98.29" "Recibe 5432 y 6379 desde VM2; sin respaldo." "4 vCPU · 11 GiB RAM · 68 GB" {
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
                    geocodificadorQa = containerInstance geocodificador
                }
                deploymentNode "VM7 · Mensajería y almacenamiento · 10.43.99.8" "Recibe 9092 y 9000 desde VM2." "4 vCPU · 11 GiB RAM · 68 GB" {
                    kafkaQa = containerInstance kafka
                    garageQa = containerInstance garage
                }
            }
            mobQa -> proxyQa "Llama a https://qa.quickpatch.internal/api (certificado fijado)" "HTTPS"
            proxyQa -> gatewayQa "Reenvía qa.quickpatch.internal a VM2:8080" "HTTP"
            gatewayQa -> traefikQa "Envía /api a :30080" "HTTP"
            runnerQa -> traefikQa "Despliega release/* y ejecuta las pruebas del sistema" "HTTPS"
        }
    }

    views {

        systemLandscape "C4-01-Landscape" "Entorno de software de QUICKPATCH: el sistema, sus sistemas externos y los sistemas de soporte del equipo." {
            include *
            autoLayout tb 200 80
        }

        systemContext quickpatch "C4-02-Contexto" "QUICKPATCH frente a las personas que lo usan y su único sistema externo, la pasarela de pagos (RIE-01, R5, ADR-024)." {
            include *
            exclude equipo github observabilidad
            autoLayout lr
        }

        container quickpatch "C4-03-Contenedores" "Contenedores de QUICKPATCH: apps cliente, API Gateway, 8 microservicios, Kafka y almacenes de datos." {
            include *
            exclude equipo github observabilidad
            autoLayout tb 200 80
            properties {
                "structurizr.groups" false
            }
        }

        component mobile "C4-04-Componentes-Mobile" "Componentes de la App móvil." {
            include *
            # La relación existe en el modelo, pero dibujada cruza Ubicación del dispositivo.
            exclude "mobDisponibilidad -> mobDiseno"
            autoLayout tb 150 80
        }
        component web "C4-04-Componentes-Web" "Componentes del Panel web." {
            include *
            autoLayout lr
        }
        component identity "C4-04-Componentes-Identity" "Componentes de Identity Service por capa: Api, Application, Domain e Infrastructure (SDD 10.3.1)." {
            include *
            # ServiceRequest aparece por la consulta interna; sus otras relaciones no son de esta vista.
            exclude "serviceRequest -> kafka"
            exclude "gateway -> serviceRequest"
            autoLayout lr
        }
        component actors "C4-04-Componentes-Actors" "Componentes de Actors Service (diseño; el servicio es un esqueleto)." {
            include *
            autoLayout lr
        }
        component catalog "C4-04-Componentes-Catalog" "Componentes de Catalog Service por capa: Api, Application, Domain e Infrastructure (SDD 10.3.1)." {
            include *
            autoLayout lr
        }
        component serviceRequest "C4-04-Componentes-ServiceRequest" "Componentes de ServiceRequest Service por capa: Api, Application, Domain e Infrastructure (SDD 10.3.1)." {
            include *
            # Identity aparece por la consulta interna; su publicación a Kafka no es de esta vista.
            exclude "identity -> kafka"
            exclude "gateway -> identity"
            autoLayout tb 100 60
        }
        component matching "C4-04-Componentes-Matching" "Componentes de Matching Service." {
            include *
            autoLayout tb 150 80
        }
        component ranking "C4-04-Componentes-Ranking" "Componentes de Ranking Service por capa (ADR-027): consume service-request.rated y publica ranking.technician-reputation-changed con Outbox; sin API REST desde el gateway (ADR-025). Implementado; todavía sin desplegar (SCRUM-512)." {
            include *
            autoLayout tb 150 80
        }
        component payments "C4-04-Componentes-Payments" "Componentes de Payments Service por capa (SDD 10.3.1): pago con la pasarela simulada del MVP y comprobante (ADR-009 modificado); pagos recibidos del técnico planeados (RF-25)." {
            include *
            autoLayout lr
        }
        component communication "C4-04-Componentes-Communication" "Componentes de Communication Service: canal en tiempo real, buzón y chat de la solicitud (ADR-023, ADR-024 y ADR-026)." {
            include *
            autoLayout tb 150 80
        }

        dynamic quickpatch "C4-05-Dinamico-InicioSesion" "Inicio de sesión: el tenant sale del canal y el JWT RS256 lo firma Identity (RN-U5, ADR-018)." {
            mobile -> gateway "POST /api/v1/auth/login con X-Channel-Id" "HTTPS/JSON"
            gateway -> identity "Enruta /v1/auth/login"
            identity -> dbIdentity "Busca el usuario en el tenant del canal y registra el intento (RLS)"
            identity -> gateway "200 con accessToken RS256 y el usuario"
            gateway -> mobile "Entrega el token" "HTTPS/JSON"
            autoLayout lr
        }

        dynamic quickpatch "C4-05-Dinamico-ReplicaCategorias" "Alta de una categoría y su réplica en ServiceRequest (ADR-007, ADR-017)." {
            web -> gateway "POST /api/v1/catalog/admin/categories"
            gateway -> catalog "Enruta con el JWT del admin del tenant"
            catalog -> dbCatalog "Guarda la categoría y el evento en outbox_events (una transacción)"
            catalog -> kafka "El publicador envía catalog.category-changed"
            serviceRequest -> kafka "Consume el evento"
            serviceRequest -> dbServiceRequest "Actualiza service_request_categories y processed_events"
            autoLayout lr 200 100
            properties {
                "structurizr.groups" false
            }
        }

        dynamic quickpatch "C4-05-Dinamico-CrearSolicitud" "Creación de una solicitud, búsqueda del técnico y oferta (RF-07, RF-09, RN-M9, ADR-007, ADR-023). La aceptación está en C4-05-Dinamico-AsignacionTecnico." {
            title "Escenario: creación de una solicitud y búsqueda del técnico"
            mobile -> gateway "Abre el WebSocket /api/v1/realtime (ADR-023)" "WebSocket (wss)"
            gateway -> communication "Enruta el WebSocket; Communication valida el token"
            mobile -> gateway "POST /api/v1/service-requests" "HTTPS/JSON"
            gateway -> serviceRequest "Enruta con el JWT del cliente"
            serviceRequest -> dbServiceRequest "Valida la categoría en la réplica y guarda solicitud y outbox (una transacción)"
            serviceRequest -> kafka "El publicador envía service-request.created"
            matching -> kafka "Consume service-request.created"
            matching -> dbMatching "Registra el eventId, busca candidatos (RN-M9, PostGIS) y registra la oferta con vencimiento a 3 min"
            matching -> kafka "Publica matching.offer-created o, sin candidatos, matching.no-technician-available"
            serviceRequest -> kafka "Sin candidatos, consume el resultado y pasa la solicitud a en_espera"
            communication -> kafka "Consume matching.offer-created o, sin candidatos, service-request.status-changed (en_espera)"
            communication -> dbCommunication "Guarda la notificación en el buzón del destinatario"
            communication -> gateway "Avisa por el WebSocket abierto: al técnico, la oferta (ADR-023)"
            gateway -> mobile "Entrega el aviso; la app pide el detalle por REST" "WebSocket (wss)"
            autoLayout lr 200 100
            properties {
                "structurizr.groups" false
            }
        }

        dynamic quickpatch "C4-05-Dinamico-AsignacionTecnico" "Desde que se crea la solicitud hasta que el cliente ve a su técnico (RF-09, RF-10, RF-11; RN-M2, RN-M6, RN-M9; ADR-007, ADR-023). Si el técnico rechaza o la oferta vence a los 3 min, Matching repite los pasos 5 a 9 con el siguiente candidato (RN-M3)." {
            title "Escenario: asignación de técnico a una solicitud"
            mobile -> gateway "Las apps del técnico y del cliente abren el WebSocket /api/v1/realtime (ADR-023)" "WebSocket (wss)"
            gateway -> communication "Enruta el WebSocket; Communication valida el token"
            serviceRequest -> kafka "Publica service-request.created desde el Outbox (la solicitud quedó en buscando_tecnico)"
            matching -> kafka "Consume service-request.created (una vez por eventId)"
            matching -> dbMatching "Busca candidatos aprobados, disponibles, de la especialidad y con cobertura, por cercanía (RN-M9, PostGIS), y registra la oferta con vencimiento a 3 min"
            matching -> kafka "Publica matching.offer-created"
            communication -> kafka "Consume matching.offer-created"
            communication -> gateway "Avisa al técnico por su WebSocket /v1/realtime"
            gateway -> mobile "La app del técnico muestra la oferta: localidad y distancia, sin la dirección (RN-SR13)" "WebSocket (wss)"
            mobile -> gateway "El técnico acepta: POST /api/v1/matching/offers/{attemptId}/accept" "HTTPS/JSON"
            gateway -> matching "Enruta con el JWT del técnico"
            matching -> dbMatching "Acepta solo si la oferta sigue pendiente, es suya y no venció; el técnico pasa a ocupado (RN-M2, RN-M6; una transacción con el Outbox)"
            matching -> kafka "Publica matching.technician-assigned"
            serviceRequest -> kafka "Consume matching.technician-assigned"
            serviceRequest -> dbServiceRequest "Pasa la solicitud a asignado y guarda service-request.status-changed en el Outbox (una transacción)"
            serviceRequest -> kafka "Publica service-request.status-changed"
            communication -> kafka "Consume service-request.status-changed"
            communication -> gateway "Avisa al cliente por su WebSocket"
            gateway -> mobile "La app del cliente pide el detalle por REST y muestra al técnico asignado" "WebSocket (wss)"
            autoLayout lr 250 120
            properties {
                "structurizr.groups" false
            }
        }

        dynamic quickpatch "C4-05-Dinamico-Pago" "Pago tokenizado y facturación (RF-22 a RF-24, ADR-009)." {
            mobile -> gateway "POST /api/v1/payments con el token de la tarjeta" "HTTPS/JSON"
            gateway -> payments "Enruta con el JWT del cliente"
            payments -> pasarela "Cobra con el token (sin PAN ni CVV)"
            pasarela -> payments "Webhook con el resultado"
            payments -> dbPayments "Guarda el pago, la factura y el evento en outbox (una transacción)"
            payments -> kafka "Publica payment.approved o payment.rejected"
            serviceRequest -> kafka "Consume el resultado y pasa a pagado"
            communication -> kafka "Consume el resultado y envía el comprobante"
            autoLayout rl 200 100
            properties {
                "structurizr.groups" false
            }
        }

        dynamic quickpatch "C4-05-Dinamico-Calificacion" "Escenario: calificación del servicio y reputación del técnico (RF-12, RF-20, AC9-E2; ADR-027; Ranking todavía sin desplegar, SCRUM-512)." {
            title "Escenario: calificación del servicio y reputación del técnico"
            mobile -> gateway "POST /v1/service-requests/{id}/rating con score y comment opcional" "HTTPS/JSON"
            gateway -> serviceRequest "Enruta con el JWT del cliente"
            serviceRequest -> dbServiceRequest "Valida dueño y estado pagado; guarda ratings y service-request.rated en outbox (una transacción)"
            serviceRequest -> kafka "Publica service-request.rated (sin el comentario)"
            ranking -> kafka "Consume service-request.rated, una vez por eventId"
            ranking -> dbRanking "Suma la calificación, recalcula el promedio y la marca; guarda el evento en outbox"
            ranking -> kafka "Publica ranking.technician-reputation-changed"
            identity -> kafka "Consume la reputación"
            identity -> dbIdentity "Actualiza technician_profiles.average_rating y la marca de reputación baja"
            autoLayout lr 200 100
            properties {
                "structurizr.groups" false
            }
        }

        dynamic quickpatch "C4-05-Dinamico-GestionTenants" "Gestión de tenants por el admin de plataforma (RF-21, SCRUM-112)." {
            web -> gateway "PATCH /api/v1/platform/tenants/{id}"
            gateway -> identity "Enruta con el JWT de admin_plataforma"
            identity -> dbIdentity "SET LOCAL ROLE identity_platform, cambia el estado y escribe audit_logs (una transacción)"
            identity -> gateway "200 con el tenant actualizado"
            gateway -> web "Muestra el nuevo estado"
            autoLayout lr
        }

        deployment quickpatch produccion "C4-06-Despliegue-Produccion" "Producción al 27 de octubre de 2026 (Documento de Infraestructura V4, 4.3): VM1 (entrada y herramientas), VM3, VM4 y VM6 (ADR-022); gateway y panel en el Nginx de VM3 (ADR-028). Punteado: sin desplegar; Payments y Communication llegan con la promoción del MVP (SCRUM-518)." {
            include *
            exclude "mobProd -> gatewayProd" "webProd -> gatewayProd"
            exclude "* -> kafkaProd" "* -> redisProd" "* -> garageProd"
            include "serviceRequestProd -> kafkaProd"
            autoLayout lr 200 60
        }

        deployment quickpatch qa "C4-06-Despliegue-QA" "QA al 27 de octubre de 2026 (Documento de Infraestructura V4, 4.3): VM2, VM5 y VM7, con la misma VM1 (ADR-022); gateway y panel en el Nginx de VM2 (ADR-028). Punteado: sin desplegar." {
            include *
            exclude "mobQa -> gatewayQa" "webQa -> gatewayQa"
            exclude "* -> kafkaQa" "* -> redisQa" "* -> garageQa"
            include "serviceRequestQa -> kafkaQa"
            autoLayout lr 200 60
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
            # Observación del profesor (22 de octubre): el API Gateway es un rectángulo y los microservicios, hexágonos.
            element "Gateway" {
                shape Box
            }
            element "Microservicio" {
                shape Hexagon
            }
            element "Planeado" {
                border dashed
                opacity 70
            }
            element "Deployment Node" {
                color #000000
            }
            element "Infrastructure Node" {
                background #ffffff
                color #000000
            }
            relationship "Relationship" {
                fontSize 22
                dashed false
            }
            relationship "Planeado" {
                dashed true
                color #707070
            }
        }
    }

}
