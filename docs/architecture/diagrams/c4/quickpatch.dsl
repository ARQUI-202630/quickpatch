/*
 * QUICKPATCH — Modelo C4 completo (Structurizr DSL)
 *
 * Un solo workspace con todas las vistas C4 del SDD:
 *   C4-01  System Landscape        (1)  el entorno de software de QUICKPATCH
 *   C4-02  System Context          (1)  QUICKPATCH es un único sistema de software
 *   C4-03  Container               (2)  los contenedores de QUICKPATCH: REST y datos (a) y eventos (b)
 *   C4-04  Component               (10) uno por contenedor con estructura propia:
 *                                       las 2 apps cliente y los 8 microservicios.
 *                                       API Gateway, Kafka, PostgreSQL, Redis y Garage no
 *                                       tienen componentes propios que diseñar (son
 *                                       configuración de productos), por eso no tienen vista.
 *   C4-05  Dynamic                 (11) un diagrama por flujo crítico, no por sistema; pasos
 *                                       numerados con el evento real de contracts/kafka (SCRUM-684)
 *   C4-06  Deployment              (2)  uno por ambiente: producción y QA (ADR-022)
 *   C4-07  Code                         fuera de Structurizr: ver los .puml de esta carpeta
 *
 * Estado de cada elemento (SCRUM-707), con su estilo y en la leyenda de cada vista:
 *   Implementado  está en el código de develop y desplegado. Borde verde continuo.
 *   Planeado      diseñado en el SDD/DD, sin código en develop o sin desplegar. Borde gris discontinuo.
 *   Externo       sistema de terceros fuera de QUICKPATCH. Fondo gris.
 *   Mock          implementado como simulación del sistema real: la pasarela simulada de Payments
 *                 (ADR-009 modificado). Fondo naranja y borde de puntos.
 *
 * Revisión del 5 de noviembre de 2026: componentes de la app y del panel según los features de develop
 * (ofertas, equipo, recuperación de la contraseña, panel operativo, presentación y activación), bases
 * con sus tablas del DD 5.19, producción con los 7 servicios tras la promoción del MVP (SCRUM-518),
 * desactivación de un tenant con su réplica (RN-T1) y recuperación de la contraseña (SCRUM-623).
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
        # Seis roles (SRS 2.1): cuatro usan la app móvil y dos el panel web (SCRUM-688).
        group "Usuarios de la app móvil" {
            cliente = person "Cliente" "Pide, sigue, paga y califica servicios técnicos para el hogar."
            empresaCliente = person "Empresa cliente" "Pide y paga servicios para sus sedes (RF-06)."
            tecnico = person "Técnico" "Recibe asignaciones, ejecuta el servicio y registra evidencias."
            proveedor = person "Proveedor" "Administra su equipo de técnicos (RF-16)."
        }
        group "Administradores del panel web" {
            adminTenant = person "Admin del tenant" "Aprueba y suspende técnicos, sigue las solicitudes de su tenant y entrega los enlaces de recuperación de contraseña (RF-18 a RF-20, ADR-024)."
            adminPlataforma = person "Admin de plataforma" "Administra los tenants (RF-21)."
        }
        equipo = person "Equipo de desarrollo y operación" "Desarrolla, despliega y opera QUICKPATCH." "Interno"

        # ---------------------------------------------------------------- Sistemas externos (ADR-024: solo la pasarela, R5)
        # La geocodificación (RIE-02) corre dentro con Nominatim y las notificaciones (RIE-03) son dentro de la app.
        pasarela = softwareSystem "Pasarela de pagos PCI-DSS" "Tokeniza la tarjeta y cobra (RIE-01, ADR-009). Proveedor por definir." "Externo,Planeado"

        # ---------------------------------------------------------------- Sistemas de soporte del equipo
        github = softwareSystem "GitHub" "12 repositorios + quickpatch, GitHub Actions y GitHub Container Registry (ADR-012, ADR-021)." "Soporte,Externo"
        observabilidad = softwareSystem "Observabilidad" "Prometheus, Loki y Grafana para producción y QA (VM1, ADR-022)." "Soporte"

        # ---------------------------------------------------------------- QUICKPATCH
        quickpatch = softwareSystem "QUICKPATCH" "Plataforma multi-tenant de servicios técnicos. Microservicios con arquitectura orientada a eventos (ADR-003)." {

            group "Clientes" {
                mobile = container "App móvil" "App de clientes, empresas cliente, técnicos y proveedores." "App nativa (iOS y Android)" "Mobile App" {
                    mobNavegacion = component "Navegación" "Rutas protegidas por sesión y por rol, barra inferior según el rol (Inicio; Solicitudes, Servicios o Equipo; Cuenta; SCRUM-441) y la regla del regreso: flecha en las pantallas secundarias y botón atrás de Android a Inicio desde las pestañas (SCRUM-615)." "go_router · app/router y app/shell"
                    mobConfig = component "Configuración del ambiente" "URL base, Host del gateway y huella SHA-256 del certificado de QA (pinning)." "Dart · core/config"
                    mobHttp = component "Cliente HTTP" "Adjunta JWT y X-Correlation-Id, valida el certificado y traduce problem+json en errores de la app." "Dio · core/network"
                    mobSesion = component "Sesión" "Guarda el token en el almacenamiento seguro del dispositivo y expone usuario y rol." "Almacenamiento seguro del dispositivo · core/session"
                    mobAuth = component "Autenticación" "Login, registro de cliente hogar y de técnico o proveedor con su especialidad (SCRUM-55), registro de empresa (SCRUM-67), activación con el enlace de invitación y pedido de recuperación de la contraseña (SCRUM-626)." "Riverpod · features/autenticacion"
                    mobInicio = component "Inicio por rol" "Acceso a la nueva solicitud y categorías de Catalog para el cliente; opciones (Disponibilidad y cobertura) y aviso de verificación para técnico y proveedor (SCRUM-441)." "Riverpod · features/inicio"
                    mobCuenta = component "Cuenta" "Datos de la sesión, licencias y cierre de sesión (SCRUM-441); edición del perfil propio con PATCH /v1/users/me (SCRUM-612)." "Pantalla móvil · features/cuenta"
                    mobDiseno = component "Sistema de diseño" "Tema azul y componentes compartidos: tarjetas, chips de estado, botones, estados vacío y de error (SCRUM-439), y ConfirmarSalida y AtrasConDestino (SCRUM-617)." "Componentes móviles · app/theme y shared/widgets"
                    mobSolicitudes = component "Solicitudes" "Nueva solicitud en tres pasos en un formulario (RNF-11) y detalle con su estado (SCRUM-442)." "Riverpod · features/solicitudes"
                    mobUbicacion = component "Ubicación del dispositivo" "Permiso y lectura del GPS con respaldo en LocationManager y límite de 15 s." "geolocator · features/solicitudes/data"
                    mobDisponibilidad = component "Disponibilidad y cobertura" "Interruptor de disponibilidad (bloqueado si está ocupado, RN-M6) y elección de las localidades en el mapa o con chips sincronizados (RF-13, RN-M9; SCRUM-89)." "Riverpod · features/disponibilidad"
                    mobMapa = component "Mapa de localidades" "Límites de las 20 localidades desde un GeoJSON de IDECA dentro de la app, con los códigos de GET /v1/localities; proyección, encuadre urbano y toque por localidad, sin mapa de fondo (R5, ADR-024)." "CustomPainter · features/disponibilidad"
                    mobTiempoReal = component "Estado en tiempo real" "WebSocket /v1/realtime con el token en la primera trama; si se cae, consulta el detalle cada 30 s (RF-11, RNF-06, ADR-023)." "Dart · core/realtime"
                    mobNotificaciones = component "Buzón de notificaciones" "Lista las notificaciones del usuario, las marca leídas y abre su solicitud (RIE-03, ADR-024; SCRUM-459)." "Riverpod · features/notificaciones"
                    mobChat = component "Chat de la solicitud" "Historial paginado, envío y mensajes nuevos por la trama chat.message; solo lectura al cerrar (RF-37, ADR-026; SCRUM-482)." "Riverpod · features/chat"
                    mobEmpresa = component "Usuarios de la empresa" "Empresa cliente del usuario y alta de otros usuarios con invitación (RF-06; SCRUM-67)." "Riverpod · features/empresa"
                    mobCalificacion = component "Calificación" "Estrellas y comentario en el detalle de una solicitud pagada, para quien la creó (RF-12; SCRUM-86)." "Riverpod · features/calificacion"
                    mobHistorial = component "Historial del técnico" "Servicios atendidos con filtros Completados, Pagados y Cancelados y la calificación recibida (RF-17; SCRUM-101)." "Riverpod · features/solicitudes"
                    mobOfertas = component "Ofertas" "Oferta pendiente del técnico con localidad y distancia, aceptar o rechazar (RF-10), y aviso de oferta nueva con la trama offer.created en cualquier pestaña (SCRUM-80)." "Riverpod · features/ofertas"
                    mobEquipo = component "Equipo del proveedor" "Lista los técnicos del equipo y da de alta uno nuevo con su invitación (RF-16; SCRUM-98)." "Riverpod · features/equipo"
                    mobPagos = component "Pago, comprobante y Mis pagos" "Pago con la pasarela simulada (la tarjeta se tokeniza en el teléfono) y comprobante en PDF (RF-22 a RF-24); Mis pagos del técnico y del equipo del proveedor, por estado y por técnico (RF-25; SCRUM-502)." "Riverpod · features/pagos"
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
                    webPerfil = component "Mi perfil" "Nombre y teléfono propios con GET y PATCH /v1/users/me; correo y rol de solo lectura y confirmación al salir sin guardar (SCRUM-613)." "Componente web · features/perfil"
                    webPresentacion = component "Presentación" "Página pública en /: qué es QUICKPATCH, el ciclo del servicio, sus usuarios y la descarga de la APK del último release (SCRUM-491, SCRUM-628)." "Componente web · features/presentacion"
                    webActivacion = component "Activar cuenta" "Página pública /activar: el técnico invitado define su contraseña con el token del enlace (SCRUM-463)." "Componente web · features/activacion"
                    webSolicitudes = component "Solicitudes" "Panel operativo del admin del tenant y de plataforma: lista por estado con conteos, consulta cada minuto con la pestaña visible y cancelación con motivo (RF-18; SCRUM-38, SCRUM-105)." "Componente web · features/solicitudes"
                    webSolicitudesApi = component "Cliente API de solicitudes" "GET /v1/admin/service-requests y /v1/platform/service-requests, resumen por estado y POST cancel (service-request.v1.yaml)." "HttpClient · features/solicitudes"
                    webRecuperaciones = component "Recuperar contraseñas" "Bandeja del admin del tenant con las solicitudes pendientes, de la más antigua a la más reciente, y el enlace de un solo uso que vence en 1 hora (SCRUM-626, ADR-024)." "Componente web · features/recuperacion"
                    webRecuperar = component "Define tu contraseña nueva" "Página pública /recuperar: el usuario define la contraseña nueva con el token del enlace, que va en el cuerpo y nunca en la URL (SCRUM-626)." "Componente web · features/recuperacion"
                    webRecuperacionApi = component "Cliente API de recuperación" "GET /v1/admin/password-recovery-requests, POST .../{id}/link y POST /v1/auth/password-recovery/confirm (identity.v1.yaml 1.10.0)." "HttpClient · features/recuperacion"
                    webDiseno = component "Sistema de diseño" "Tokens azules, fuente autoalojada y componentes reutilizables del panel; contraste WCAG AA verificado en el CI (SCRUM-433)." "SCSS · styles y shared"
                }
            }

            gateway = container "API Gateway" "Única entrada HTTP: quita /api y enruta al servicio por la ruta del contrato; cada servicio valida el JWT (ADR-018, SDD 6.3)." "Nginx (quickpatch-api-gateway)" "Gateway"

            group "Microservicios" {
                identity = container "Identity Service" "Autenticación, usuarios, tenants y auditoría." "ASP.NET Core (.NET 10)" "Microservicio" {
                    # Api
                    idEndpoints = component "IdentityEndpoints" "Registro, login, /password/setup y /password-recovery (SCRUM-624); /users/me (SCRUM-611); /platform/tenants; /admin/technicians y /admin/password-recovery-requests; /providers/me/technicians; /internal/v1/users (solo en el clúster)." "Minimal API · Api/Endpoints"
                    idCompanyEndpoints = component "CompanyEndpoints" "POST /v1/auth/register/company; GET /v1/companies/me y POST /v1/companies/me/users (RF-06)." "Minimal API · Api/Endpoints"
                    idSecurity = component "AuthenticatedUser y ForbiddenAuditHandler" "Lee usuario, tenant, rol y company_id del JWT y registra cada 403 (RNF-04)." "ASP.NET Core · Api/Security"
                    idHttp = component "Problems y BadRequestExceptionHandler" "Responde application/problem+json. X-Correlation-Id y el registro estructurado vienen de quickpatch-shared-dotnet (ADR-020)." "ASP.NET Core · Api/Http"
                    idBootstrap = component "TenantAdminBootstrap" "Al arrancar crea el admin del tenant y el de plataforma desde el Secret (SCRUM-450)." "Hosted service · Api/Bootstrap"
                    # Application
                    idAuth = component "Auth" "LoginHandler (bloqueo tras 5 intentos), RegisterClientHandler, RegisterTechnicianHandler y EnsureTenantAdminHandler; Request, ListPasswordRecoveries, IssueRecoveryLink y ConfirmPasswordRecoveryHandler (SCRUM-624)." "Casos de uso · Application/Auth"
                    idCompanies = component "Companies" "RegisterCompanyHandler, GetMyCompanyHandler y CreateCompanyUserHandler (RF-06)." "Casos de uso · Application/Companies"
                    idTechnicians = component "Technicians" "ChangeVerificationHandler y ListTechniciansHandler (RF-19, RF-20); CreateTeamTechnicianHandler y ListTeamHandler (RF-16); SetupPasswordHandler y RenewInvitationHandler." "Casos de uso · Application/Technicians"
                    idPlatform = component "Platform" "ListTenantsHandler, CreateTenantHandler y UpdateTenantStatusHandler con auditoría (RF-21); al cambiar el estado deja tenant.status-changed en el Outbox (RN-T1, SCRUM-509)." "Casos de uso · Application/Platform"
                    idUsers = component "Users" "GetCurrentUserHandler, UpdateCurrentUserHandler (nombre y teléfono del perfil propio, SCRUM-611) y LookupUsersHandler (nombres por lote para otros servicios)." "Casos de uso · Application/Users"
                    # Domain
                    idDomain = component "Dominio de identidad" "User (LockoutPolicy), Tenant, TechnicianProfile (VerificationStatus), ClientCompany, PasswordSetupToken, PasswordRecoveryRequest, AuditEntry y Roles." "Domain"
                    # Infrastructure
                    idPersistence = component "TenantUnitOfWork, PlatformUnitOfWork y repositorios" "UserRepository, TenantRepository, TechnicianProfileRepository, ClientCompanyRepository, PasswordSetupTokenRepository, PasswordRecoveryRepository y AuditLog; RLS con app.current_tenant o SET LOCAL ROLE identity_platform." "EF Core + Npgsql · Infrastructure/Persistence"
                    idSecurityAdapters = component "RsaTokenIssuer, BCryptPasswordHasher y HmacEmailHasher" "Firma el JWT RS256 (ADR-018), hace el hash de las contraseñas (RNF-03) y el HMAC-SHA256 del correo de la recuperación (SCRUM-624)." "Infrastructure/Security"
                    idOutbox = component "EfOutbox" "Guarda technician.registered, technician.verification-changed y tenant.status-changed en outbox_events en la misma transacción (ADR-007)." "EF Core · Infrastructure/Messaging"
                    idPublisher = component "OutboxPublisher" "Publica los eventos pendientes y marca published_at. Es el publicador común de ADR-020: el servicio solo lo registra." "BackgroundService · quickpatch-shared-dotnet (ADR-020)"
                    idReputationConsumer = component "ReputationChangedConsumer" "Consume ranking.technician-reputation-changed y, con ApplyReputationHandler, proyecta la reputación en technician_profiles; descarta lo atrasado por changedAt (ADR-027)." "Kafka consumer · Infrastructure/Messaging"
                }
                actors = container "Actors Service" "Esqueleto sin lógica: solo Program.cs (SCRUM-696). Proveedores, aliados y clientes como actores de negocio." "ASP.NET Core (.NET 10)" "Microservicio,Planeado" {
                    acApi = component "API de actores" "Consulta y mantenimiento de actores del tenant." "Minimal API" "Planeado"
                    acProveedores = component "Proveedores de materiales" "Supplier: proveedor de materiales o repuestos (concepto evolutivo)." "Domain" "Planeado"
                    acAliados = component "Aliados" "Ally: técnico, profesional o empresa aliada." "Domain" "Planeado"
                    acClientes = component "Clientes" "Client: cliente hogar o empresarial." "Domain" "Planeado"
                    acPersistencia = component "Persistencia con RLS" "Repositorios de actores por tenant." "EF Core + Npgsql" "Planeado"
                }
                catalog = container "Catalog Service" "Categorías y especialidades de servicio." "ASP.NET Core (.NET 10)" "Microservicio" {
                    # Api
                    catEndpoints = component "CategoryEndpoints" "GET /v1/catalog/categories (obsoleta por ADR-025); POST y PATCH /v1/catalog/admin/categories." "Minimal API · Api/Endpoints"
                    catSecurity = component "AuthenticatedUser, RequestTenant y ForbiddenAuditHandler" "Usuario, tenant y rol del JWT. RequestTenant resuelve el tenant del token o, sin token, del canal (RN-U5), fuera del endpoint. Registra los 403." "ASP.NET Core · Api/Security"
                    catHttp = component "Problems y BadRequestExceptionHandler" "Responde application/problem+json. X-Correlation-Id y el registro estructurado vienen de quickpatch-shared-dotnet (ADR-020)." "ASP.NET Core · Api/Http"
                    # Application
                    catHandlers = component "Categories" "ListCategories, CreateCategory y UpdateCategory, un caso de uso por archivo; nombre único por tenant (409)." "Casos de uso · Application/Categories"
                    # Domain
                    catDomain = component "Category" "Nombre normalizado, descripción, estado activo y updatedAt." "Domain/Categories"
                    # Infrastructure
                    catPersistence = component "TenantUnitOfWork y CategoryRepository" "service_categories bajo RLS (app.current_tenant)." "EF Core + Npgsql · Infrastructure/Persistence"
                    catOutbox = component "EfOutbox" "Guarda catalog.category-changed en outbox_events en la misma transacción (ADR-007)." "EF Core · Infrastructure/Persistence"
                    catResync = component "CategoryResync" "Vuelve a publicar todas las categorías una vez, con la descripción, para la réplica de ServiceRequest (ADR-025)." "Infrastructure/Persistence"
                    catPublisher = component "OutboxPublisher" "Publica los eventos pendientes y marca published_at. Es el publicador común de ADR-020: el servicio solo lo registra." "BackgroundService · quickpatch-shared-dotnet (ADR-020)"
                }
                serviceRequest = container "ServiceRequest Service" "Ciclo de vida de la solicitud de servicio." "ASP.NET Core (.NET 10)" "Microservicio" {
                    # Api
                    srRequestEndpoints = component "Endpoints de la solicitud" "ServiceRequestEndpoints (POST y GET /v1/service-requests), LocationPreviewEndpoints (/location-preview), CancellationEndpoints (/{id}/cancel) y TechnicianServiceRequestEndpoints (GET /v1/technicians/me/service-requests). Comparten ApiResults y Routes de Api/Http, no entre sí." "Minimal API · Api/Endpoints"
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
                    srEventHandlers = component "Manejadores de eventos" "ApplyCategoryChangedHandler, MatchingStatusHandler, PaymentEventsHandler y ApplyTenantStatusChangedHandler (réplica del estado del tenant, RN-T1): aplican cada evento una vez por eventId." "Casos de uso · Application/Categories, Matching y Payments"
                    srRating = component "Ratings" "RateServiceRequestHandler: valida dueño, estado pagado y que no esté calificada (RN-R1 a RN-R3) y deja service-request.rated en el Outbox (ADR-027)." "Casos de uso · Application/Ratings"
                    # Domain
                    srDomain = component "Dominio de la solicitud" "ServiceRequest (transiciones RN-SR2 a RN-SR7), ServiceRequestRules (validación RN-SR1, RN-SR11, RN-SR12 y RF-36), Quote, ServiceEvidence, Rating, CategoryReplica, GeoPoint, CoverageArea y Locality." "Domain"
                    # Infrastructure
                    srPersistence = component "TenantUnitOfWork y repositorios" "ServiceRequestRepository, QuoteRepository, EvidenceRepository, RatingRepository, CategoryReplicaRepository y ProcessedEventRepository bajo RLS." "EF Core + Npgsql · Infrastructure/Persistence"
                    srOutbox = component "EfOutbox" "Guarda los eventos de la solicitud en outbox_events en la misma transacción (ADR-007)." "EF Core · Infrastructure/Persistence"
                    srPublisher = component "OutboxPublisher" "Lotes con FOR UPDATE SKIP LOCKED; publica y marca published_at. Es el publicador común de ADR-020: el servicio solo lo registra." "BackgroundService · quickpatch-shared-dotnet (ADR-020)"
                    srTenantConsumer = component "TenantStatusChangedConsumer" "Consume tenant.status-changed (SCRUM-510)." "Kafka consumer · Infrastructure/Messaging"
                    srCategoryConsumer = component "CategoryChangedConsumer" "Consume catalog.category-changed." "Kafka consumer · Infrastructure/Messaging"
                    srMatchingConsumer = component "MatchingEventsConsumer" "Consume matching.technician-assigned, .no-technician-available y .search-resumed." "Kafka consumer · Infrastructure/Messaging"
                    srPaymentConsumer = component "PaymentEventsConsumer" "Consume payment.approved y payment.rejected." "Kafka consumer · Infrastructure/Messaging"
                    srGeocoder = component "NominatimGeocoder" "Convierte la dirección en coordenadas dentro de Bogotá (RIE-02, ADR-024)." "HttpClient · Infrastructure/Geocoding"
                    srStorage = component "GarageEvidenceStorage" "Guarda y sirve las fotos de la evidencia (ADR-016)." "S3 · Infrastructure/Storage"
                    srUserDirectory = component "IdentityUserDirectory" "Nombres y contacto por lote con GET /internal/v1/users; si falla, devuelve vacío (ADR-025)." "HttpClient · Infrastructure/Identity"
                    srScheduling = component "QuoteExpirer y RedisDistributedLock" "Vence las cotizaciones sin respuesta; una sola réplica a la vez (RN-Q6)." "BackgroundService · Infrastructure/Scheduling"
                }
                matching = container "Matching Service" "Asignación geoespacial de técnicos." "Java 25 + Spring Boot 4.1" "Microservicio" {
                    # api
                    maOffersController = component "OffersController" "GET /v1/matching/offers y POST /v1/matching/offers/{attemptId}/accept y /reject (matching.v1.yaml); el técnico y el tenant salen del JWT (RN-U3)." "Spring MVC · api/controllers"
                    maTechniciansController = component "TechniciansController" "GET /v1/localities y GET y PUT /v1/technicians/me/availability y /coverage (RF-13)." "Spring MVC · api/controllers"
                    maSecurity = component "SecurityConfig y CorrelationIdFilter" "Valida el JWT RS256 de Identity (ADR-018) y propaga X-Correlation-Id." "Spring Security · api"
                    # application
                    maCreatedHandler = component "ServiceRequestCreatedHandler" "Registra el eventId e inicia el matching en la misma transacción del tenant (ADR-007)." "application/events"
                    maCancelledHandler = component "ServiceRequestCancelledHandler" "Cancela la oferta pendiente y la búsqueda, y libera al técnico si había aceptado (RN-M5, RN-M6)." "application/events"
                    maCompletedHandler = component "ServiceRequestCompletedHandler" "Devuelve al técnico a disponible y le ofrece la solicitud en espera más antigua (RN-M6, RN-M10)." "application/events"
                    maTechnicianHandler = component "TechnicianEventsHandler" "Mantiene la proyección del técnico y descarta eventos con updatedAt anterior (P-01, ADR-017); un técnico aprobado reanuda solicitudes en espera (RN-M10)." "application/events"
                    maEngine = component "MatchingEngine" "Guarda la solicitud, ofrece al candidato más cercano, publica el resultado y reanuda las solicitudes en espera (RN-M1, RN-M4, RN-M9, RN-M10)." "application/matching"
                    maOfferService = component "OfferService" "Lista, acepta, rechaza y vence ofertas; al aceptar, el técnico pasa a ocupado (RN-M2, RN-M3, RN-M6 a RN-M8)." "application/matching"
                    maAvailability = component "TechnicianAvailabilityService" "Disponibilidad y cobertura del técnico autenticado; un cambio puede reanudar solicitudes en espera (RF-13, RN-M10)." "application/technicians"
                    # domain
                    maDomain = component "Dominio de matching" "Matching, Technicians, VerificationStatus y los eventos (EventEnvelope, MatchingEvents y los de service-request y technician)." "domain"
                    # infrastructure
                    maCreatedListener = component "ServiceRequestCreatedListener" "Consume service-request.created." "@KafkaListener · infrastructure/messaging"
                    maCancelledListener = component "ServiceRequestCancelledListener" "Consume service-request.cancelled." "@KafkaListener · infrastructure/messaging"
                    maCompletedListener = component "ServiceRequestCompletedListener" "Consume service-request.completed." "@KafkaListener · infrastructure/messaging"
                    maTechnicianListener = component "TechnicianEventsListener" "Consume technician.registered y technician.verification-changed." "@KafkaListener · infrastructure/messaging"
                    maStores = component "JdbcMatchingStores y JdbcTechnicianStores" "Solicitudes, candidatos (PostGIS), ofertas, disponibilidad, cobertura y localidades bajo RLS." "JDBC · infrastructure/persistence"
                    maProjection = component "JdbcTechnicianProjection" "INSERT ... ON CONFLICT en technician_availability: la fila nace en no_disponible." "JDBC · infrastructure/persistence"
                    maTenantTx = component "JdbcTenantTransaction y JdbcProcessedEventStore" "Fija app.current_tenant en cada transacción y registra el eventId en processed_events. Implementan los puertos TenantTransaction y ProcessedEventStore de application/common." "JDBC · infrastructure/persistence"
                    maOutbox = component "JdbcOutbox" "Guarda los eventos de Matching en outbox_events en la misma transacción." "JDBC · infrastructure/messaging"
                    maPublisher = component "OutboxPublisher" "Publica los eventos pendientes con el rol matching_outbox y marca published_at." "@Scheduled · infrastructure/messaging"
                    maExpirer = component "OfferExpirer" "Cada MATCHING_EXPIRY_INTERVAL vence las ofertas sin respuesta y ofrece al siguiente candidato (RN-M3, RN-M8)." "@Scheduled · infrastructure/scheduling"
                    maSweeper = component "WaitingRequestsSweeper" "Barrido de respaldo de RN-M10 cada MATCHING_SWEEP_INTERVAL: reanuda las solicitudes en espera que ya tienen candidato." "@Scheduled · infrastructure/scheduling"
                }
                ranking = container "Ranking Service" "Reputación de técnicos desde las calificaciones (ADR-027)." "ASP.NET Core (.NET 10)" "Microservicio" {
                    # Application
                    raHandler = component "ServiceRequestRatedHandler" "ServiceRequestRatedContract valida el mensaje; el caso de uso suma la calificación bajo el tenant del evento, una vez por eventId y por solicitud, y deja ranking.technician-reputation-changed en el Outbox." "Casos de uso · Application/Reputation"
                    # Domain
                    raDomain = component "Dominio de reputación" "TechnicianReputation (cantidad, suma, promedio NUMERIC(2,1) y reputación baja con 5 o más calificaciones y promedio menor a 3.0, AC9-E2) y AppliedRating." "Domain/Reputation"
                    # Infrastructure
                    raPersistence = component "TenantUnitOfWork y repositorios" "ReputationRepository (FOR UPDATE por técnico) y ProcessedEventRepository bajo RLS." "EF Core + Npgsql · Infrastructure/Persistence"
                    raOutbox = component "EfOutbox" "Guarda ranking.technician-reputation-changed en outbox_events en la misma transacción (ADR-007)." "EF Core · Infrastructure/Persistence"
                    raPublisher = component "OutboxPublisher" "Publica los eventos pendientes con el rol ranking_outbox y marca published_at. Es el publicador común de ADR-020: el servicio solo lo registra." "BackgroundService · quickpatch-shared-dotnet (ADR-020)"
                    raConsumer = component "ServiceRequestRatedConsumer" "Consume service-request.rated y confirma el offset después de aplicar; solo transporte: el contrato lo valida Application." "Kafka consumer · Infrastructure/Messaging"
                }
                payments = container "Payments Service" "Pagos tokenizados y facturación." "ASP.NET Core (.NET 10)" "Microservicio" {
                    # Api
                    paPaymentEndpoints = component "PaymentEndpoints" "GET y POST /v1/service-requests/{id}/payment con el token de la tarjeta; nunca recibe PAN ni CVV (RNF-01)." "Minimal API · Api/Endpoints"
                    paInvoiceEndpoints = component "InvoiceEndpoints" "GET /v1/payments/{id}/invoice en JSON o PDF (RF-24)." "Minimal API · Api/Endpoints"
                    paSecurity = component "AuthenticatedUser y ForbiddenAuditHandler" "Usuario, tenant, rol y company_id del JWT; registra los 403." "ASP.NET Core · Api/Security"
                    # Application
                    paPayments = component "Payments" "GetPayment, Pay, PaymentSettlement y ReconcilePayments, un caso de uso por archivo." "Casos de uso · Application/Payments"
                    paCompletedHandler = component "ServiceRequestCompletedHandler" "Crea el pago pendiente con el total de la cotización aceptada (RN-P4)." "Casos de uso · Application/Payments"
                    paInvoices = component "Invoices" "GetInvoiceHandler: solo el pagador lee el comprobante; entrega InvoiceDocument al puerto IInvoicePdfRenderer." "Casos de uso · Application/Invoices"
                    # Domain
                    paDomain = component "Dominio de pagos" "Payment (estados y RejectionReasons), Invoice y Billing." "Domain/Payments"
                    # Infrastructure
                    paPersistence = component "TenantUnitOfWork y repositorios" "PaymentRepository, PaymentTechnicianRepository, ReconciliationSource y ProcessedEventRepository bajo RLS, un adaptador por archivo." "EF Core + Npgsql · Infrastructure/Persistence"
                    paOutbox = component "EfOutbox" "Guarda payment.approved o payment.rejected en outbox_events en la misma transacción." "EF Core · Infrastructure/Persistence"
                    paPublisher = component "OutboxPublisher" "Publica los eventos pendientes y marca published_at. Es el publicador común de ADR-020: el servicio solo lo registra." "BackgroundService · quickpatch-shared-dotnet (ADR-020)"
                    paCompletedConsumer = component "ServiceRequestCompletedConsumer" "Consume service-request.completed." "Kafka consumer · Infrastructure/Messaging"
                    paReconciliation = component "ReconciliationJob" "Cierra los pagos que la pasarela dejó sin respuesta (AC9-E5)." "BackgroundService · Infrastructure/Messaging"
                    paProvider = component "SimulatedPaymentProvider" "Pasarela simulada del MVP detrás del puerto IPaymentProvider (ADR-009 modificado): no cobra de verdad." "Infrastructure/Providers" "Mock"
                    paPdf = component "InvoicePdfRenderer" "Arma el PDF del comprobante, sin validez fiscal." "Infrastructure/Documents"
                    paReceived = component "ReceivedPaymentEndpoints" "GET /v1/payments/received?page=&size=: pagos del técnico y, para el proveedor, de su equipo (RF-25, payments 1.2.0)." "Minimal API · Api/Endpoints"
                    paReceivedHandler = component "ReceivedPaymentsHandler" "Lista los pagos pendientes y aprobados según el rol: el técnico ve los suyos y el proveedor los de su equipo (SCRUM-501)." "Casos de uso · Application/Payments"
                    paTechnicianHandler = component "TechnicianRegisteredHandler" "Guarda el proveedor de cada técnico en payment_technicians, una vez por eventId (DD 5.25, P-02)." "Casos de uso · Application/Payments"
                    paTechnicianConsumer = component "TechnicianRegisteredConsumer" "Consume technician.registered." "Kafka consumer · Infrastructure/Messaging"
                    paWebhook = component "Receptor de webhooks del PSP" "Confirmará el resultado de forma idempotente con la pasarela certificada." "Minimal API" "Planeado"
                }
                communication = container "Communication Service" "Notificaciones del ciclo de servicio dentro de la app: canal en tiempo real y buzón (ADR-023, ADR-024)." "ASP.NET Core (.NET 10)" "Microservicio" {
                    # Api
                    coRealtime = component "RealtimeEndpoints, RealtimeSession y TokenValidator" "WebSocket /v1/realtime: espera la trama auth, valida el JWT RS256 y cierra con los códigos del contrato (ADR-023)." "ASP.NET Core WebSockets · Api/Realtime"
                    coConnections = component "ConnectionRegistry y WebSocketClient" "Conexiones abiertas de la réplica; entrega cada aviso solo al tenant y al destinatario del evento." "Api/Realtime"
                    coInboxEndpoints = component "InboxEndpoints" "GET /v1/notifications y POST /v1/notifications/{id}/read (ADR-024)." "Minimal API · Api/Endpoints"
                    coChatEndpoints = component "ChatEndpoints" "GET y POST /v1/service-requests/{id}/messages (RF-37, ADR-026)." "Minimal API · Api/Endpoints"
                    # Application
                    coNotifier = component "RealtimeNotifier y NoticeRouter" "Valida el sobre, descarta repetidos (RecentEventIds) y decide a quién avisar: status-changed, offer.created y counts-changed." "Application/Realtime"
                    coInboxRecorder = component "InboxRecorder e InboxRules" "Convierte cada evento en una notificación por destinatario, sin dirección ni teléfono (RN-SR13)." "Application/Inbox"
                    coInboxQueries = component "ListNotificationsHandler y MarkNotificationReadHandler" "Buzón del usuario del token y marca de leída." "Application/Inbox"
                    coChatParticipants = component "ChatParticipantsRecorder" "Llena chat_participants con service-request.status-changed (RN-CH3)." "Application/Chat"
                    coChatHandlers = component "ListChatMessagesHandler y SendChatMessageHandler" "Historial y envío de mensajes; el envío sale por el canal como chat.message (RN-CH1, RN-CH2)." "Application/Chat"
                    # Domain
                    coDomain = component "Dominio de Communication" "Notification y NotificationTypes, ChatParticipants y ChatMessage, y los avisos del canal (Notices)." "Domain"
                    # Infrastructure
                    coRealtimeConsumer = component "RealtimeEventsConsumer" "Consume service-request.created, .status-changed y matching.offer-created para el canal; empieza en el último offset." "Kafka consumer · Infrastructure/Messaging"
                    coPersistentConsumer = component "PersistentEventsConsumer" "Dos grupos que leen desde el principio y confirman después de guardar: el buzón (8 topics) y la réplica del chat (status-changed)." "Kafka consumer · Infrastructure/Messaging"
                    coInboxStore = component "InboxStore" "Tabla notifications bajo RLS." "EF Core + Npgsql · Infrastructure/Persistence"
                    coChatStore = component "ChatStore" "Tablas chat_participants y chat_messages bajo RLS." "EF Core + Npgsql · Infrastructure/Persistence"
                }
            }

            group "Mensajería y almacenamiento" {
                kafka = container "Apache Kafka" "Bus de eventos: un topic por tipo de evento (quickpatch-kafka/topics)." "Apache Kafka (KRaft)" "Queue"
                redis = container "Redis" "Coordinación temporal: hoy solo el bloqueo con el que una réplica de ServiceRequest vence las cotizaciones; sin caché en el MVP. Un usuario por servicio limitado a <servicio>:*." "Redis" "Database"
                garage = container "Garage" "Evidencias fotográficas y respaldos de PostgreSQL (ADR-016)." "Garage (S3)" "Database"
            }

            geocodificador = container "Geocodificador" "Convierte direcciones de Bogotá en coordenadas; solo el mapa de Bogotá y su propio PostgreSQL (RIE-02, ADR-024, excepción a ADR-014)." "Nominatim (OpenStreetMap)"

            group "PostgreSQL + PostGIS (una instancia, una base por servicio, ADR-014)" {
                dbIdentity = container "db_identity" "tenants, users, client_companies, technician_profiles, password_setup_tokens, password_recovery_requests, password_recovery_attempts, audit_logs y outbox_events." "PostgreSQL" "Database"
                dbActors = container "db_actors" "Base y roles creados; sin servicio que la use (Actors no tiene código)." "PostgreSQL" "Database"
                dbCatalog = container "db_catalog" "service_categories y outbox_events." "PostgreSQL" "Database"
                dbServiceRequest = container "db_service_request" "service_requests, quotes, ratings, service_evidence, service_request_categories, tenant_status_replica, localities, audit_logs, outbox_events y processed_events." "PostgreSQL + PostGIS" "Database"
                dbMatching = container "db_matching" "matching_requests, matching_attempts, technician_availability, coverage_zones, localities, outbox_events y processed_events." "PostgreSQL + PostGIS" "Database"
                dbRanking = container "db_ranking" "technician_reputations, applied_ratings, processed_events y outbox_events." "PostgreSQL" "Database"
                dbPayments = container "db_payments" "payments, invoices y payment_technicians, sin PAN ni CVV; outbox_events y processed_events." "PostgreSQL" "Database"
                dbCommunication = container "db_communication" "notifications, chat_participants y chat_messages." "PostgreSQL" "Database"
            }
        }

        # ================================================================ Relaciones
        # Resumen por servicio de lo que publica y consume en Kafka (vista C4-03b, SCRUM-676).
        # Va antes de las relaciones de componentes para que Structurizr no cree la relación
        # implícita con la primera etiqueta que encuentre. Fuente: matriz de lo modelado frente a lo real.
        identity -> kafka "Publica technician.registered, technician.verification-changed y tenant.status-changed. Consume ranking.technician-reputation-changed" "Kafka"
        catalog -> kafka "Publica catalog.category-changed" "Kafka"
        serviceRequest -> kafka "Publica service-request.* (9 eventos; .started sin consumidor). Consume catalog.category-changed, tenant.status-changed, matching.technician-assigned, .no-technician-available, .search-resumed y payment.*" "Kafka"
        matching -> kafka "Publica matching.* (4 eventos). Consume service-request.created, .cancelled y .completed, technician.registered y technician.verification-changed" "Kafka"
        ranking -> kafka "Publica ranking.technician-reputation-changed. Consume service-request.rated" "Kafka"
        payments -> kafka "Publica payment.approved y payment.rejected. Consume service-request.completed y technician.registered" "Kafka"
        communication -> kafka "Consume service-request.created, .status-changed, .quoted, .quote-accepted y .quote-rejected, matching.offer-created, technician.registered y technician.verification-changed (no publica)" "Kafka"

        # Personas → apps
        cliente -> mobNavegacion "Pide, sigue, paga y califica servicios"
        empresaCliente -> mobNavegacion "Pide y paga servicios"
        tecnico -> mobNavegacion "Atiende sus asignaciones"
        proveedor -> mobNavegacion "Administra su equipo"
        adminTenant -> webShell "Aprueba técnicos, sigue las solicitudes y entrega enlaces de recuperación"
        adminPlataforma -> webShell "Administra los tenants"
        cliente -> webRecuperar "Define su contraseña nueva con el enlace que le entregó el admin"
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
        mobNavegacion -> mobOfertas "Abre"
        mobNavegacion -> mobEquipo "Abre"
        mobOfertas -> mobHttp "GET la oferta pendiente y POST accept o reject con"
        mobOfertas -> mobTiempoReal "Recibe offer.created de"
        mobEquipo -> mobHttp "GET y POST /v1/providers/me/technicians con"
        mobSolicitudes -> mobChat "Abre el chat de la solicitud en"
        mobSolicitudes -> mobPagos "Abre el pago y el comprobante en"
        mobSolicitudes -> mobCalificacion "Muestra la calificación del servicio pagado con"
        mobCalificacion -> mobHttp "POST /v1/service-requests/{id}/rating con"
        mobCuenta -> mobHistorial "Abre el historial del técnico en"
        mobCuenta -> mobPagos "Abre Mis pagos en"
        mobHistorial -> mobHttp "GET /v1/technicians/me/service-requests con"
        mobCuenta -> mobHttp "GET y PATCH /v1/users/me con"
        mobChat -> mobHttp "GET y POST mensajes con"
        mobChat -> mobTiempoReal "Recibe chat.message de"
        mobEmpresa -> mobHttp "GET y POST /v1/companies/me con"
        mobPagos -> mobHttp "GET y POST el pago, GET el comprobante y GET /v1/payments/received con"
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
        webShell -> webPerfil "Abre desde el nombre del usuario"
        webShell -> webPresentacion "Abre en / sin sesión"
        webShell -> webActivacion "Abre en /activar"
        webShell -> webRecuperar "Abre en /recuperar"
        webShell -> webSolicitudes "Abre"
        webShell -> webRecuperaciones "Abre"
        webSolicitudes -> webSolicitudesApi "Lista, cuenta y cancela con"
        webSolicitudesApi -> webInterceptor "Envía las peticiones por"
        webRecuperaciones -> webRecuperacionApi "Lista las pendientes y genera el enlace con"
        webRecuperar -> webRecuperacionApi "Confirma la contraseña nueva con"
        webRecuperacionApi -> webInterceptor "Envía las peticiones por"
        webActivacion -> webInterceptor "POST /v1/auth/password/setup por"
        webPresentacion -> github "Descarga la APK del último release de quickpatch-mobile" "HTTPS"
        webShell -> webDiseno "Arma el layout con"
        webTenants -> webDiseno "Usa los componentes de"
        webTecnicos -> webDiseno "Usa los componentes de"
        webPerfil -> webSesion "Actualiza el nombre en"
        webPerfil -> webInterceptor "GET y PATCH /v1/users/me por"
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
        gateway -> idEndpoints "Enruta /api/v1/auth, /users, /platform, /admin/technicians, /admin/password-recovery-requests y /providers" "HTTP"
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
        gateway -> paReceived "Enruta /api/v1/payments/received" "HTTP"
        gateway -> maOffersController "Enruta /api/v1/matching/offers" "HTTP"
        gateway -> maTechniciansController "Enruta /api/v1/technicians/me/availability y /coverage, y /api/v1/localities" "HTTP"
        gateway -> coRealtime "Enruta /api/v1/realtime" "WebSocket"
        gateway -> coInboxEndpoints "Enruta /api/v1/notifications" "HTTP"

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
        idPlatform -> idOutbox "Registra tenant.status-changed con"
        idPersistence -> dbIdentity "Lee y escribe (RLS)" "SQL"
        idOutbox -> dbIdentity "INSERT en outbox_events" "SQL"
        idPublisher -> dbIdentity "Lee pendientes y marca published_at" "SQL"
        idPublisher -> kafka "Publica technician.registered, technician.verification-changed y tenant.status-changed" "Kafka"
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
        srTenantConsumer -> kafka "Consume tenant.status-changed" "Kafka"
        srTenantConsumer -> srEventHandlers "Entrega el evento a"
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
        maCreatedListener -> kafka "Consume service-request.created" "Kafka"
        maCancelledListener -> kafka "Consume service-request.cancelled" "Kafka"
        maCompletedListener -> kafka "Consume service-request.completed" "Kafka"
        maTechnicianListener -> kafka "Consume technician.registered y technician.verification-changed" "Kafka"
        maCreatedListener -> maCreatedHandler "Entrega el evento válido a"
        maCancelledListener -> maCancelledHandler "Entrega el evento válido a"
        maCompletedListener -> maCompletedHandler "Entrega el evento válido a"
        maTechnicianListener -> maTechnicianHandler "Entrega el evento válido a"
        maCreatedHandler -> maTenantTx "Fija el tenant y registra el eventId con"
        maCancelledHandler -> maTenantTx "Fija el tenant y registra el eventId con"
        maCompletedHandler -> maTenantTx "Fija el tenant y registra el eventId con"
        maTechnicianHandler -> maTenantTx "Fija el tenant y registra el eventId con"
        maCreatedHandler -> maEngine "Inicia el matching con"
        maCancelledHandler -> maStores "Cancela la oferta y la búsqueda y libera al técnico en"
        maCompletedHandler -> maEngine "Libera al técnico y reanuda solicitudes en espera con"
        maTechnicianHandler -> maProjection "Actualiza la proyección con"
        maTechnicianHandler -> maEngine "Reanuda solicitudes en espera al aprobar con"
        maOffersController -> maSecurity "Toma el técnico y el tenant del JWT con"
        maTechniciansController -> maSecurity "Toma el técnico y el tenant del JWT con"
        maOffersController -> maOfferService "Lista, acepta o rechaza con"
        maTechniciansController -> maAvailability "Lee y cambia disponibilidad y cobertura con"
        maOfferService -> maEngine "Ofrece al siguiente candidato con"
        maOfferService -> maStores "Lee y cambia la oferta y la disponibilidad en"
        maOfferService -> maOutbox "Guarda matching.technician-assigned en"
        maAvailability -> maStores "Lee y cambia disponibilidad y cobertura en"
        maAvailability -> maEngine "Reanuda solicitudes en espera con"
        maEngine -> maStores "Busca candidatos y guarda solicitudes y ofertas en"
        maEngine -> maOutbox "Guarda matching.offer-created, .no-technician-available y .search-resumed en"
        maExpirer -> maOfferService "Vence las ofertas sin respuesta con"
        maSweeper -> maEngine "Reanuda las solicitudes en espera con"
        maStores -> dbMatching "Lee y escribe matching_requests, matching_attempts, technician_availability y coverage_zones (RLS, PostGIS)" "SQL"
        maProjection -> dbMatching "INSERT ... ON CONFLICT en technician_availability" "SQL"
        maTenantTx -> dbMatching "set_config app.current_tenant e INSERT en processed_events" "SQL"
        maOutbox -> dbMatching "INSERT en outbox_events" "SQL"
        maPublisher -> dbMatching "Lee los pendientes y marca published_at" "SQL"
        maPublisher -> kafka "Publica matching.offer-created, .technician-assigned, .no-technician-available y .search-resumed" "Kafka"

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
        paReceived -> paSecurity "Toma el usuario autenticado de"
        paReceived -> paReceivedHandler "Invoca"
        paReceivedHandler -> paPersistence "Lee los pagos del técnico o del equipo del proveedor con"
        paTechnicianConsumer -> kafka "Consume technician.registered" "Kafka"
        paTechnicianConsumer -> paTechnicianHandler "Entrega el evento a"
        paTechnicianHandler -> paPersistence "Guarda el proveedor del técnico con"
        paPersistence -> dbPayments "Lee y escribe payments, invoices, payment_technicians y processed_events (RLS)" "SQL"
        paOutbox -> dbPayments "INSERT en outbox_events" "SQL"
        paPublisher -> dbPayments "Lee pendientes y marca published_at" "SQL"
        paPublisher -> kafka "Publica payment.*" "Kafka"

        # Communication
        coRealtimeConsumer -> kafka "Consume service-request.created, .status-changed y matching.offer-created" "Kafka"
        coPersistentConsumer -> kafka "Consume service-request.created, .status-changed, .quoted, .quote-accepted y .quote-rejected, matching.offer-created, technician.registered y technician.verification-changed" "Kafka"
        coRealtimeConsumer -> coNotifier "Entrega cada mensaje a"
        coNotifier -> coConnections "Avisa a las conexiones del destinatario con"
        coPersistentConsumer -> coInboxRecorder "Entrega los eventos del buzón a"
        coPersistentConsumer -> coChatParticipants "Entrega service-request.status-changed a"
        coInboxRecorder -> coInboxStore "Guarda las notificaciones con"
        coChatParticipants -> coChatStore "Actualiza los participantes con"
        coRealtime -> coConnections "Registra la conexión autenticada en"
        coInboxEndpoints -> coInboxQueries "Lista y marca leídas con"
        coInboxQueries -> coInboxStore "Lee y actualiza con"
        coChatEndpoints -> coChatHandlers "Lista y envía mensajes con"
        coChatHandlers -> coChatStore "Lee y guarda mensajes con"
        coChatHandlers -> coConnections "Entrega chat.message con"
        coInboxStore -> dbCommunication "Lee y escribe notifications (RLS)" "SQL"
        coChatStore -> dbCommunication "Lee y escribe chat_participants y chat_messages (RLS)" "SQL"
        gateway -> coChatEndpoints "Enruta /api/v1/service-requests/{id}/messages (excepción de ADR-025)" "HTTP"

        # Soporte
        github -> quickpatch "Construye imágenes y despliega con el runner de VM1" "HTTPS"
        quickpatch -> observabilidad "Envía métricas y logs" "HTTP"

        # ================================================================ Despliegue (ADR-022, INFRASTRUCTURE 3.3)

        # Estado de cada elemento (SCRUM-707), visible en la leyenda de cada vista: Implementado, Planeado, Externo o Mock.
        # Las expresiones de Structurizr solo combinan dos condiciones, por eso va por pasos con etiquetas auxiliares sin
        # estilo, que no salen en la leyenda. Planeado, Externo y Mock se ponen a mano en cada elemento.
        !elements "element.tag!=Planeado && element.tag!=Mock" {
            tags "SinMarcaA"
        }
        !elements "element.tag==SinMarcaA && element.tag!=Externo" {
            tags "SinMarca"
        }
        !elements "element.tag==SinMarca && element.type==Container" {
            tags "Implementado"
        }
        !elements "element.tag==SinMarca && element.type==Component" {
            tags "Implementado"
        }
        !elements "element.tag==SinMarca && element.type==SoftwareSystem" {
            tags "Implementado"
        }
        produccion = deploymentEnvironment "Producción" {
            deploymentNode "Teléfono del usuario" "" "Android o iOS" {
                mobProd = containerInstance mobile
            }
            deploymentNode "Navegador del administrador" "" "Chrome, Edge o Firefox" {
                webProd = containerInstance web
            }
            deploymentNode "Navegador del equipo" "Quien opera consulta Grafana y Loki." "Chrome, Edge o Firefox" {
                equipoNavProd = infrastructureNode "Navegador" "Ejecuta la interfaz de Grafana que sirve VM1." "HTML + JS"
            }
            deploymentNode "Red privada del laboratorio 10.43.x.x" "Solo el 443 de VM1 es alcanzable desde la VPN (R9); firewall default deny incoming." "" {
                deploymentNode "VM1 · Herramientas · 10.43.100.168" "Entrada única y herramientas compartidas por los dos ambientes." "4 vCPU · 11 GiB RAM · 68 GB" {
                    proxyProd = infrastructureNode "Entrada Nginx :443" "Termina TLS 1.2/1.3 (autofirmado) y reenvía por nombre, sin cambiar Host: quickpatch.internal al gateway de VM3; grafana.quickpatch.internal a Grafana (ADR-028)." "Nginx"
                    runnerProd = infrastructureNode "Runner de GitHub Actions" "kubectl y k6; despliega la imagen de main y corre el humo de producción." "GitHub Actions runner"
                    observabilidadProd = softwareSystemInstance observabilidad
                }
                deploymentNode "VM3 · Aplicación · 10.43.98.205" "Los servicios llegan a VM4 (PostgreSQL 5432, Redis 6379) y a VM6 (Kafka 9092, Garage 9000)." "4 vCPU · 11 GiB RAM · 68 GB" {
                    deploymentNode "Docker, red del host" "Nginx del gateway de producción en el puerto 8080, abierto solo a VM1 (ADR-028): /api va a Traefik y / sirve el panel desde /opt/quickpatch/gateway/panel (página provisional: el panel real no se ha promovido)." "Docker" {
                        gatewayProd = containerInstance gateway
                        panelProd = infrastructureNode "Archivos del panel" "Build de Angular (HTML, JS y CSS) en /opt/quickpatch/gateway/panel. El Nginx los entrega: no los ejecuta, se ejecutan en el navegador." "Archivos estáticos"
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
                        rankingProd = containerInstance ranking
                        paymentsProd = containerInstance payments
                        communicationProd = containerInstance communication
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
            webProd -> proxyProd "Pide el panel y llama a /api en https://quickpatch.internal" "HTTPS"
            panelProd -> webProd "Entrega el panel al navegador (vía VM1)" "HTTPS"
            equipoNavProd -> proxyProd "Abre https://grafana.quickpatch.internal" "HTTPS"
            mobProd -> proxyProd "Llama a https://quickpatch.internal/api (certificado fijado)" "HTTPS"
            proxyProd -> gatewayProd "Reenvía quickpatch.internal a VM3:8080" "HTTP"
            gatewayProd -> traefikProd "Envía /api a :30080" "HTTP"
            runnerProd -> traefikProd "kubectl apply de la imagen de main" "HTTPS"
        }

        qa = deploymentEnvironment "QA" {
            deploymentNode "Teléfono o emulador de prueba" "" "Android" {
                mobQa = containerInstance mobile
            }
            deploymentNode "Navegador del administrador" "" "Chrome, Edge o Firefox" {
                webQa = containerInstance web
            }
            deploymentNode "Navegador del equipo" "Quien opera consulta Grafana y Loki." "Chrome, Edge o Firefox" {
                equipoNavQa = infrastructureNode "Navegador" "Ejecuta la interfaz de Grafana que sirve VM1." "HTML + JS"
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
                        panelQa = infrastructureNode "Archivos del panel" "Build de Angular (HTML, JS y CSS) de release/* en el Nginx de QA. Los entrega: no los ejecuta, se ejecutan en el navegador." "Archivos estáticos"
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
                        rankingQa = containerInstance ranking
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
            webQa -> proxyQa "Pide el panel y llama a /api en https://qa.quickpatch.internal" "HTTPS"
            panelQa -> webQa "Entrega el panel al navegador (vía VM1)" "HTTPS"
            equipoNavQa -> proxyQa "Abre https://grafana.quickpatch.internal" "HTTPS"
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
            title "Contexto del sistema QUICKPATCH (C4 nivel 1)"
            include *
            exclude equipo github observabilidad
            autoLayout tb 150 120
        }

        # La vista de contenedores se parte en dos (SCRUM-676): con Kafka y las bases en la
        # misma imagen, las líneas hacia el bus cruzaban todo el diagrama.
        container quickpatch "C4-03a-Contenedores-Sincrono" "Contenedores de QUICKPATCH, comunicación síncrona y datos: clientes, API Gateway, microservicios, una base PostgreSQL por servicio (ADR-014), Redis, Garage y el geocodificador. Los eventos están en C4-03b." {
            title "Contenedores de QUICKPATCH: REST y datos (C4 nivel 2)"
            include *
            exclude equipo github observabilidad
            # Actors está planeado y no tiene despliegue: no se dibuja lo que todavía no existe.
            exclude actors dbActors
            # Los eventos van en C4-03b-Contenedores-Eventos.
            exclude kafka
            autoLayout tb 200 100
        }

        container quickpatch "C4-03b-Contenedores-Eventos" "Contenedores de QUICKPATCH, comunicación por eventos: qué servicio publica y cuál consume en Kafka (ADR-006, ADR-007; SDD 8.6)." {
            title "Contenedores de QUICKPATCH: eventos en Kafka (C4 nivel 2)"
            include kafka identity catalog serviceRequest matching ranking payments communication
            # La consulta interna de usuarios es REST y está en C4-03a.
            exclude "serviceRequest -> identity"
            autoLayout lr 500 60
        }

        component mobile "C4-04-Componentes-Mobile" "Componentes de la App móvil." {
            include *
            # La relación existe en el modelo, pero dibujada cruza Ubicación del dispositivo.
            exclude "mobDisponibilidad -> mobDiseno"
            autoLayout tb 220 140
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
            autoLayout tb 120 70
        }
        component serviceRequest "C4-04-Componentes-ServiceRequest" "Componentes de ServiceRequest Service por capa: Api, Application, Domain e Infrastructure (SDD 10.3.1)." {
            include *
            # Identity aparece por la consulta interna; su publicación a Kafka no es de esta vista.
            exclude "identity -> kafka"
            exclude "gateway -> identity"
            autoLayout tb 100 60
        }
        component matching "C4-04-Componentes-Matching" "Componentes de Matching Service por capa, con sus clases: consumidores de service-request.created, .cancelled y .completed y de technician.*, motor de matching, ofertas de 3 minutos, barridos programados y Outbox (RN-M1 a RN-M10)." {
            include *
            autoLayout tb 150 80
        }
        component ranking "C4-04-Componentes-Ranking" "Componentes de Ranking Service por capa (ADR-027): consume service-request.rated y publica ranking.technician-reputation-changed con Outbox; sin API REST desde el gateway (ADR-025). Desplegado en QA (SCRUM-512) y en producción (SCRUM-522)." {
            include *
            autoLayout tb 150 80
        }
        component payments "C4-04-Componentes-Payments" "Componentes de Payments Service por capa (SDD 10.3.1): pago con la pasarela simulada del MVP y comprobante (ADR-009 modificado); pagos recibidos del técnico y del equipo del proveedor (RF-25)." {
            include *
            autoLayout tb 120 70
        }
        component communication "C4-04-Componentes-Communication" "Componentes de Communication Service por capa, con sus clases: canal en tiempo real, buzón y chat de la solicitud, con sus consumidores de Kafka (ADR-023, ADR-024 y ADR-026)." {
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

        dynamic quickpatch "C4-05-Dinamico-CreacionAsignacion" "Desde que el cliente crea la solicitud hasta que ve a su técnico (RF-07, RF-09, RF-10, RF-11; RN-M2, RN-M6, RN-M9; ADR-007, ADR-023). Si el técnico rechaza o la oferta vence a los 3 min, Matching repite los pasos 8 a 13 con el siguiente candidato (RN-M3). Sin candidatos, ver C4-05-Dinamico-SinTecnico." {
            title "Escenario: creación de la solicitud y asignación del técnico"
            mobile -> gateway "Las apps del cliente y del técnico abren el WebSocket /api/v1/realtime (ADR-023)" "WebSocket (wss)"
            gateway -> communication "Enruta el WebSocket; Communication valida el token"
            mobile -> gateway "El cliente crea la solicitud: POST /api/v1/service-requests con categoría, descripción, dirección y ubicación" "HTTPS/JSON"
            gateway -> serviceRequest "Enruta con el JWT del cliente (el tenant sale del token, ADR-018)"
            serviceRequest -> dbServiceRequest "Valida la categoría en su réplica (ADR-017), guarda la solicitud en buscando_tecnico y service-request.created en el Outbox (una transacción); responde 201"
            serviceRequest -> kafka "El publicador envía service-request.created"
            matching -> kafka "Consume service-request.created (una vez por eventId)"
            matching -> dbMatching "Busca candidatos aprobados, disponibles, de la especialidad y con cobertura, por cercanía (RN-M9, PostGIS); registra la oferta con vencimiento a 3 min y matching.offer-created en el Outbox"
            matching -> kafka "Publica matching.offer-created"
            communication -> kafka "Consume service-request.created y matching.offer-created"
            communication -> dbCommunication "Guarda en el buzón «Recibimos tu solicitud» para el cliente y la oferta para el técnico"
            communication -> gateway "Avisa por WebSocket: al cliente, buscando_tecnico; al técnico, la oferta"
            gateway -> mobile "La app del técnico muestra la oferta con localidad y distancia, sin la dirección (RN-SR13)" "WebSocket (wss)"
            mobile -> gateway "El técnico acepta: POST /api/v1/matching/offers/{attemptId}/accept" "HTTPS/JSON"
            gateway -> matching "Enruta con el JWT del técnico"
            matching -> dbMatching "Acepta solo si la oferta sigue pendiente, es suya y no venció; el técnico pasa a ocupado y matching.technician-assigned queda en el Outbox (RN-M2, RN-M6; una transacción)"
            matching -> kafka "Publica matching.technician-assigned"
            serviceRequest -> kafka "Consume matching.technician-assigned (una vez por eventId)"
            serviceRequest -> dbServiceRequest "Pasa la solicitud a asignado y guarda service-request.status-changed en el Outbox (una transacción)"
            serviceRequest -> kafka "Publica service-request.status-changed"
            communication -> kafka "Consume service-request.status-changed (no matching.technician-assigned, SCRUM-466)"
            communication -> gateway "Guarda la notificación y avisa al cliente y al técnico por su WebSocket"
            gateway -> mobile "La app del cliente pide el detalle por REST y muestra al técnico asignado" "WebSocket (wss)"
            autoLayout lr 250 120
            properties {
                "structurizr.groups" false
            }
        }

        dynamic quickpatch "C4-05-Dinamico-SinTecnico" "Sin técnico disponible (AC9-E4; RN-M9, RN-M10; ADR-007). Matching no relaja los filtros: la solicitud espera hasta que aparece un técnico que podría atenderla (se marca disponible, cambia su cobertura, lo aprueban o termina otro servicio). Después del paso 16 la oferta sigue como en C4-05-Dinamico-CreacionAsignacion desde el paso 10." {
            title "Escenario: solicitud sin técnico disponible y reanudación de la búsqueda"
            mobile -> gateway "Las apps del cliente y del técnico tienen abierto el WebSocket /api/v1/realtime (ADR-023)" "WebSocket (wss)"
            gateway -> communication "Enruta el WebSocket; Communication valida el token"
            serviceRequest -> kafka "Publica service-request.created desde el Outbox (la solicitud quedó en buscando_tecnico)"
            matching -> kafka "Consume service-request.created (una vez por eventId)"
            matching -> dbMatching "No hay candidatos que cumplan todos los filtros (RN-M9); deja la búsqueda en espera y matching.no-technician-available en el Outbox"
            matching -> kafka "Publica matching.no-technician-available"
            serviceRequest -> kafka "Consume matching.no-technician-available"
            serviceRequest -> dbServiceRequest "Pasa la solicitud a en_espera y guarda service-request.status-changed en el Outbox (una transacción)"
            serviceRequest -> kafka "Publica service-request.status-changed"
            communication -> kafka "Consume service-request.status-changed"
            communication -> gateway "Guarda la notificación y avisa al cliente por su WebSocket"
            gateway -> mobile "La app del cliente muestra que la solicitud está en espera" "WebSocket (wss)"
            matching -> dbMatching "Más tarde un técnico queda disponible: toma la solicitud en espera más antigua para la que es candidato y le registra la oferta (RN-M10)"
            matching -> kafka "Publica matching.search-resumed y matching.offer-created"
            serviceRequest -> kafka "Consume matching.search-resumed"
            serviceRequest -> dbServiceRequest "Vuelve la solicitud a buscando_tecnico y guarda service-request.status-changed en el Outbox"
            autoLayout lr 250 120
            properties {
                "structurizr.groups" false
            }
        }

        dynamic quickpatch "C4-05-Dinamico-Cotizacion" "Desde que el técnico asignado cotiza hasta que el cliente acepta (RF-34, RF-35; RN-Q2, RN-Q8; ADR-007, ADR-023). Si el cliente rechaza (POST .../reject), ServiceRequest vuelve la solicitud a asignado y publica service-request.quote-rejected en lugar de los pasos 10 a 16; con la tercera rechazada cancela la solicitud (RN-Q7). Sin respuesta en 24 h, la cotización vence y la solicitud se cancela (RN-Q6)." {
            title "Escenario: cotización del servicio"
            mobile -> gateway "Las apps del cliente y del técnico tienen abierto el WebSocket /api/v1/realtime (ADR-023)" "WebSocket (wss)"
            gateway -> communication "Enruta el WebSocket; Communication valida el token"
            mobile -> gateway "El técnico cotiza: POST /api/v1/service-requests/{id}/quotes con mano de obra, materiales y detalle" "HTTPS/JSON"
            gateway -> serviceRequest "Enruta con el JWT del técnico asignado"
            serviceRequest -> dbServiceRequest "Guarda la cotización pendiente (de 1 a 3, vence en 24 h), pasa la solicitud a cotizado y guarda service-request.quoted y status-changed en el Outbox (una transacción)"
            serviceRequest -> kafka "Publica service-request.quoted y service-request.status-changed"
            communication -> kafka "Consume service-request.quoted (buzón) y service-request.status-changed (tiempo real), una vez por eventId"
            communication -> gateway "Guarda la cotización en el buzón del cliente y le avisa por su WebSocket el cambio a cotizado"
            gateway -> mobile "La app del cliente muestra la cotización con el total y el vencimiento" "WebSocket (wss)"
            mobile -> gateway "El cliente acepta: POST /api/v1/service-requests/{id}/quotes/{quoteId}/accept" "HTTPS/JSON"
            gateway -> serviceRequest "Enruta con el JWT del cliente dueño"
            serviceRequest -> dbServiceRequest "Acepta la cotización, pasa la solicitud a cotizacion_aceptada y guarda service-request.quote-accepted y status-changed en el Outbox"
            serviceRequest -> kafka "Publica service-request.quote-accepted y service-request.status-changed"
            communication -> kafka "Consume service-request.quote-accepted (buzón) y service-request.status-changed (tiempo real)"
            communication -> gateway "Guarda «Aceptaron tu cotización» en el buzón del técnico y le avisa por su WebSocket"
            gateway -> mobile "La app del técnico habilita Iniciar el servicio (C4-05-Dinamico-Ejecucion)" "WebSocket (wss)"
            autoLayout lr 250 120
            properties {
                "structurizr.groups" false
            }
        }

        dynamic quickpatch "C4-05-Dinamico-Ejecucion" "Desde que el técnico inicia el servicio hasta que sube la evidencia (RF-14, RF-15; RN-SR3; ADR-007, ADR-016, ADR-023). Solo se inicia desde cotizacion_aceptada; si no, 409 transicion-invalida. Sin al menos una foto, completar se rechaza (paso 5 de C4-05-Dinamico-Pago). Nadie consume service-request.started hoy (topics.yaml)." {
            title "Escenario: ejecución del servicio y evidencia"
            mobile -> gateway "Las apps del cliente y del técnico tienen abierto el WebSocket /api/v1/realtime (ADR-023)" "WebSocket (wss)"
            gateway -> communication "Enruta el WebSocket; Communication valida el token"
            mobile -> gateway "El técnico inicia: POST /api/v1/service-requests/{id}/start" "HTTPS/JSON"
            gateway -> serviceRequest "Enruta con el JWT del técnico asignado"
            serviceRequest -> dbServiceRequest "Pasa la solicitud de cotizacion_aceptada a en_progreso y guarda service-request.started y status-changed en el Outbox (una transacción)"
            serviceRequest -> kafka "Publica service-request.started y service-request.status-changed"
            communication -> kafka "Consume service-request.status-changed"
            communication -> gateway "Guarda la notificación y avisa al cliente por su WebSocket"
            gateway -> mobile "La app del cliente muestra el servicio en progreso" "WebSocket (wss)"
            mobile -> gateway "El técnico sube la foto: POST /api/v1/service-requests/{id}/evidence (multipart)" "HTTPS/JSON"
            gateway -> serviceRequest "Enruta con el JWT del técnico asignado"
            serviceRequest -> garage "Guarda la foto en el bucket de evidencias (ADR-016)" "S3/HTTPS"
            serviceRequest -> dbServiceRequest "Registra la referencia en service_evidence; responde 201"
            autoLayout lr 250 120
            properties {
                "structurizr.groups" false
            }
        }

        dynamic quickpatch "C4-05-Dinamico-Pago" "Desde que el técnico completa hasta que el cliente tiene el comprobante (RF-22 a RF-24; RN-P1, RN-P4, RN-SR4; ADR-007, ADR-009 modificado). Si la pasarela rechaza, Payments publica payment.rejected en el paso 14 y la solicitud sigue en completado para reintentar (RN-SR5); si no responde, la conciliación cierra el pago (AC9-E5)." {
            title "Escenario: pago del servicio y comprobante"
            mobile -> gateway "Las apps del cliente y del técnico tienen abierto el WebSocket /api/v1/realtime (ADR-023)" "WebSocket (wss)"
            gateway -> communication "Enruta el WebSocket; Communication valida el token"
            mobile -> gateway "El técnico completa: POST /api/v1/service-requests/{id}/complete" "HTTPS/JSON"
            gateway -> serviceRequest "Enruta con el JWT del técnico asignado"
            serviceRequest -> dbServiceRequest "Verifica que haya evidencia (RN-SR3), pasa la solicitud a completado y guarda service-request.completed (con el total) y status-changed en el Outbox (una transacción)"
            serviceRequest -> kafka "Publica service-request.completed"
            payments -> kafka "Consume service-request.completed (una vez por eventId)"
            payments -> dbPayments "Crea el pago pendiente con el total de la cotización aceptada (RN-P4)"
            matching -> kafka "Consume service-request.completed (una vez por eventId)"
            matching -> dbMatching "El técnico vuelve a disponible y se le ofrece la solicitud en espera más antigua (RN-M6, RN-M10)"
            mobile -> gateway "El cliente paga: POST /api/v1/service-requests/{id}/payment con el token de la tarjeta, que se tokeniza en el teléfono (RN-P1)" "HTTPS/JSON"
            gateway -> payments "Enruta con el JWT del cliente"
            payments -> dbPayments "Cobra con la pasarela simulada (adaptador dentro de Payments, ADR-009) y guarda el pago aprobado, el comprobante y payment.approved en el Outbox (una transacción)"
            payments -> kafka "Publica payment.approved"
            serviceRequest -> kafka "Consume payment.approved"
            serviceRequest -> dbServiceRequest "Pasa la solicitud a pagado (RN-SR4) y guarda service-request.status-changed en el Outbox"
            serviceRequest -> kafka "Publica service-request.status-changed"
            communication -> kafka "Consume service-request.status-changed"
            communication -> gateway "Avisa al cliente y al técnico por su WebSocket"
            gateway -> mobile "La app del cliente abre el comprobante: GET /api/v1/payments/{id}/invoice en PDF" "WebSocket (wss)"
            autoLayout lr 250 120
            properties {
                "structurizr.groups" false
            }
        }

        dynamic quickpatch "C4-05-Dinamico-Cancelacion" "El cliente dueño cancela antes de que empiece el servicio (RF-36; RN-Q5, RN-M5, RN-M6; ADR-007). Desde en_progreso responde 409 transicion-invalida. El admin_tenant también puede cancelar desde el panel, y queda en audit_logs. Communication no consume service-request.cancelled: avisa con service-request.status-changed." {
            title "Escenario: cancelación de una solicitud"
            mobile -> gateway "Las apps del cliente y del técnico tienen abierto el WebSocket /api/v1/realtime (ADR-023)" "WebSocket (wss)"
            gateway -> communication "Enruta el WebSocket; Communication valida el token"
            mobile -> gateway "El cliente cancela: POST /api/v1/service-requests/{id}/cancel con el motivo (5 a 500 caracteres)" "HTTPS/JSON"
            gateway -> serviceRequest "Enruta con el JWT del cliente dueño"
            serviceRequest -> dbServiceRequest "Bloquea la solicitud (FOR UPDATE), la pasa a cancelado, anula la cotización pendiente (RN-Q5) y guarda service-request.cancelled y status-changed en el Outbox (una transacción)"
            serviceRequest -> kafka "Publica service-request.cancelled y service-request.status-changed"
            matching -> kafka "Consume service-request.cancelled (una vez por eventId)"
            matching -> dbMatching "Cancela la oferta pendiente y no ofrece a más candidatos (RN-M5); si había técnico, vuelve a disponible (RN-M6)"
            communication -> kafka "Consume service-request.status-changed"
            communication -> gateway "Avisa al cliente y al técnico asignado por su WebSocket"
            gateway -> mobile "Las apps muestran la solicitud cancelada" "WebSocket (wss)"
            autoLayout lr 250 120
            properties {
                "structurizr.groups" false
            }
        }

        dynamic quickpatch "C4-05-Dinamico-Calificacion" "Escenario: calificación del servicio y reputación del técnico (RF-12, RF-20, AC9-E2; ADR-027; Ranking en QA desde SCRUM-512)." {
            title "Escenario: calificación del servicio y reputación del técnico"
            mobile -> gateway "El cliente califica: POST /api/v1/service-requests/{id}/rating con score y comment opcional" "HTTPS/JSON"
            gateway -> serviceRequest "Enruta con el JWT del cliente"
            serviceRequest -> dbServiceRequest "Valida dueño y estado pagado; guarda ratings y service-request.rated en outbox (una transacción)"
            serviceRequest -> kafka "Publica service-request.rated (sin el comentario)"
            ranking -> kafka "Consume service-request.rated (una vez por eventId)"
            ranking -> dbRanking "Suma la calificación, recalcula el promedio y la marca; guarda el evento en outbox"
            ranking -> kafka "Publica ranking.technician-reputation-changed"
            identity -> kafka "Consume ranking.technician-reputation-changed (una vez por eventId)"
            identity -> dbIdentity "Actualiza technician_profiles.average_rating y la marca de reputación baja"
            autoLayout lr 200 100
            properties {
                "structurizr.groups" false
            }
        }

        dynamic quickpatch "C4-05-Dinamico-GestionTenants" "El admin de plataforma desactiva un tenant y ServiceRequest deja de aceptar sus solicitudes aunque el token siga vigente (RF-21, RN-T1; ADR-007, ADR-017; SCRUM-508 a SCRUM-511)." {
            title "Escenario: desactivación de un tenant"
            web -> gateway "PATCH /api/v1/platform/tenants/{id} con status inactivo" "HTTPS/JSON"
            gateway -> identity "Enruta con el JWT de admin_plataforma"
            identity -> dbIdentity "SET LOCAL ROLE identity_platform: cambia el estado, escribe audit_logs y guarda tenant.status-changed en el Outbox (una transacción)"
            identity -> gateway "200 con el tenant actualizado; desde ahora el login de sus usuarios responde 403"
            gateway -> web "Muestra el nuevo estado"
            identity -> kafka "El publicador envía tenant.status-changed con el estado completo y updatedAt"
            serviceRequest -> kafka "Consume tenant.status-changed (una vez por eventId)"
            serviceRequest -> dbServiceRequest "Actualiza tenant_status_replica y descarta los eventos con updatedAt anterior (ADR-017)"
            mobile -> gateway "Un usuario del tenant con la sesión abierta: POST /api/v1/service-requests" "HTTPS/JSON"
            gateway -> serviceRequest "Enruta con el JWT, todavía vigente"
            serviceRequest -> gateway "422 tenant-inactivo, sin llamar a Identity (RN-T1)"
            gateway -> mobile "La app muestra que la empresa está desactivada" "HTTPS/JSON"
            autoLayout lr 200 100
            properties {
                "structurizr.groups" false
            }
        }

        dynamic quickpatch "C4-05-Dinamico-RecuperacionContrasena" "Recuperación de la contraseña olvidada sin correo (RN-U7; ADR-024; identity.v1.yaml 1.10.0; SCRUM-623). Pedir responde 202 exista o no la cuenta, y el cuarto pedido en la hora da 429. Generar otro enlace anula el anterior; uno vencido o ya usado da 400 enlace-invalido." {
            title "Escenario: recuperación de la contraseña olvidada"
            mobile -> gateway "El usuario pide la recuperación: POST /api/v1/auth/password-recovery con su correo" "HTTPS/JSON"
            gateway -> identity "Enruta con el X-Channel-Id del tenant"
            identity -> dbIdentity "Cuenta el pedido por el HMAC del correo (máximo 3 por hora) y, si la cuenta existe, deja una solicitud pendiente; responde 202 siempre"
            web -> gateway "El admin del tenant abre Recuperar contraseñas: GET /api/v1/admin/password-recovery-requests" "HTTPS/JSON"
            gateway -> identity "Enruta con el JWT del admin_tenant"
            identity -> dbIdentity "Lista las solicitudes pendientes de su tenant (RLS), sin tokens"
            web -> gateway "Genera el enlace: POST /api/v1/admin/password-recovery-requests/{id}/link" "HTTPS/JSON"
            gateway -> identity "Enruta con el JWT del admin_tenant"
            identity -> dbIdentity "Guarda solo el hash del token, de un solo uso y con vencimiento a 1 hora, y anula el anterior"
            identity -> gateway "201 con el enlace; el admin se lo entrega al usuario por el medio que usen"
            web -> gateway "El usuario abre /recuperar y envía la contraseña nueva: POST /api/v1/auth/password-recovery/confirm con el token en el cuerpo" "HTTPS/JSON"
            gateway -> identity "Enruta sin sesión"
            identity -> dbIdentity "Valida el token, cambia la contraseña, desbloquea la cuenta, marca usados el token y las invitaciones pendientes y cierra la solicitud (una transacción)"
            mobile -> gateway "El usuario entra a la app con la contraseña nueva: POST /api/v1/auth/login" "HTTPS/JSON"
            autoLayout lr 200 100
            properties {
                "structurizr.groups" false
            }
        }

        deployment quickpatch produccion "C4-06-Despliegue-Produccion" "Producción al 4 de noviembre de 2026, tras la promoción del MVP (SCRUM-518): los 7 servicios con código en el k3s de VM3, con VM4 y VM6 (ADR-022) y la entrada de VM1; gateway en el Nginx de VM3 (ADR-028). El panel se ejecuta en el navegador del administrador; el Nginx solo entrega sus archivos. Punteado: Actors, sin código." {
            include *
            exclude "mobProd -> gatewayProd" "webProd -> gatewayProd"
            exclude "* -> kafkaProd" "* -> redisProd" "* -> garageProd"
            include "serviceRequestProd -> kafkaProd"
            autoLayout lr 250 150
        }

        deployment quickpatch qa "C4-06-Despliegue-QA" "QA al 4 de noviembre de 2026: los 7 servicios con código en el k3s de VM2, con VM5 y VM7 y la misma VM1 (ADR-022); gateway en el Nginx de VM2 (ADR-028). El panel (release/0.6.0) se ejecuta en el navegador del administrador; el Nginx solo entrega sus archivos. Punteado: Actors, sin código." {
            include *
            exclude "mobQa -> gatewayQa" "webQa -> gatewayQa"
            exclude "* -> kafkaQa" "* -> redisQa" "* -> garageQa"
            include "serviceRequestQa -> kafkaQa"
            autoLayout lr 250 150
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
            element "Soporte" {
                background #6b8fb3
            }
            element "Externo" {
                background #999999
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
            # Estado (SCRUM-707): borde verde continuo, gris punteado, gris de fondo o naranja de puntos.
            element "Implementado" {
                stroke #2e7d32
                strokeWidth 4
                border solid
            }
            element "Planeado" {
                border dashed
                opacity 70
                stroke #707070
                strokeWidth 4
            }
            element "Mock" {
                border dotted
                stroke #e65100
                strokeWidth 8
                background #ffcc80
                color #000000
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
