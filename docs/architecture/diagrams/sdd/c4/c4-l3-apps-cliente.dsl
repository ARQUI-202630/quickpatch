/*
 * QUICKPATCH — SDD · C4 nivel 3: componentes de las aplicaciones cliente
 * Jira: SCRUM-303 (HU SCRUM-256). Se alinea con el C4 de contenedores (SDD 3.1.4).
 *
 * Alcance: incremento Sprint 3.
 *   - Angular Web    → admin del tenant y admin de plataforma: login, RBAC (SCRUM-25/64),
 *                      gestión de tenants (SCRUM-41/113).
 *   - Flutter Mobile → cliente, empresa cliente, técnico y proveedor: login y creación de
 *                      solicitud (SCRUM-27/71).
 *
 * Componentes lógicos: no fijan librerías de estado, navegación ni cliente HTTP porque esas
 * decisiones no están documentadas. La tecnología indica la carpeta del repositorio donde vive
 * cada componente (apps/web/src/app/{core,features,shared}, apps/mobile/lib/{core,features}).
 *
 * Contratos: quickpatch-api-gateway/openapi (service-request.v1.yaml, catalog.v1.yaml) y SDD 3.4.1.
 * Las relaciones con la etiqueta "Contrato pendiente" aún no tienen especificación OpenAPI.
 *
 * Multi-tenancy (DD 10.3): en el login y el registro el tenant sale del canal por el que llega
 * la petición (RN-U5); en las peticiones autenticadas, del JWT que propaga el API Gateway.
 * Las apps cliente nunca envían tenant_id (RN-U3).
 */
workspace "QUICKPATCH — C4-L3 Apps Cliente" "Componentes de Angular Web y Flutter Mobile para el incremento de Sprint 3." {

    model {
        clienteEmpresa = person "Cliente y empresa cliente" "Piden, siguen y pagan servicios."
        tecnicoProveedor = person "Técnico y proveedor" "Prestan servicios; el proveedor administra su equipo (RF-16)."
        adminTenant = person "Admin del tenant" "Aprueba y suspende técnicos de su tenant (RF-19, RF-20)."
        adminPlataforma = person "Admin de plataforma" "Administra los tenants (RF-21)."

        quickpatch = softwareSystem "QUICKPATCH" "Plataforma multi-tenant de servicios técnicos." {

            web = container "Angular Web" "Panel de administración del tenant y de la plataforma." "Angular 22 + TypeScript 6" "Web Browser" {
                webShell = component "Shell y enrutamiento" "Define rutas, layout del panel y redirecciones a login o a acceso denegado." "Angular Router · app.routes"
                webLogin = component "Login administrativo" "Formulario de acceso con validaciones y estados de carga y error." "Angular Component · features/auth" {
                    properties {
                        "HU" "SCRUM-23"
                    }
                }
                webAuth = component "Servicio de autenticación y sesión" "Autentica, conserva el token de la sesión y expone el usuario y su rol." "Angular Service · core/auth" {
                    properties {
                        "HU" "SCRUM-23, SCRUM-25"
                    }
                }
                webGuards = component "Guards de rol (RBAC)" "Permiten o niegan el acceso a cada ruta y opción de menú según el rol del usuario." "Angular Route Guard · core/auth" {
                    properties {
                        "HU" "SCRUM-25 / SCRUM-64"
                    }
                }
                webInterceptor = component "Interceptor HTTP" "Adjunta el JWT y X-Correlation-Id a cada petición y traduce 401, 403 y 409 en estados de la UI. No envía tenant_id." "Angular HttpInterceptor · core/http"
                webTenants = component "Gestión de tenants" "Listado de tenants y acciones de activar y desactivar con confirmación, con estados de carga, vacío y error." "Angular Feature · features/tenants" {
                    properties {
                        "HU" "SCRUM-41 / SCRUM-113"
                    }
                }
                webTenantsApi = component "Cliente API de tenants" "Cliente HTTP generado a partir del contrato de administración de tenants." "Angular Service · features/tenants" {
                    properties {
                        "HU" "SCRUM-41 / SCRUM-113"
                    }
                }
                webUi = component "UI compartida" "Componentes reutilizables de carga, vacío, error y acceso denegado." "Angular Components · shared"
            }

            mobile = container "Flutter Mobile" "App de clientes, empresas cliente, técnicos y proveedores." "Flutter 3.47.5 + Dart 3.13.4" "Mobile App" {
                mobRouter = component "Navegación" "Define pantallas, rutas protegidas y el flujo entre los pasos de la solicitud." "Flutter Navigation · core"
                mobLogin = component "Login" "Formulario de acceso con validaciones y estados de carga y error." "Flutter Screen · features/auth/presentation" {
                    properties {
                        "HU" "SCRUM-23"
                    }
                }
                mobSession = component "Sesión" "Autentica, guarda el token en almacenamiento seguro del dispositivo y expone el usuario y su rol." "Dart Service · core/auth" {
                    properties {
                        "HU" "SCRUM-23"
                    }
                }
                mobWizard = component "Asistente de nueva solicitud" "Pasos: categoría, ubicación, descripción y resumen, confirmación." "Flutter Screens · features/service_requests/presentation" {
                    properties {
                        "HU" "SCRUM-27 / SCRUM-71"
                    }
                }
                mobFormState = component "Estado y reglas de la solicitud" "Conserva los datos entre pasos y valida antes de enviar: categoría, ubicación, dirección (5 a 255) y descripción (10 a 1000)." "Dart · features/service_requests/domain" {
                    properties {
                        "HU" "SCRUM-27 / SCRUM-71"
                    }
                }
                mobCatalogRepo = component "Repositorio de catálogo" "Obtiene las categorías activas del tenant para crear la solicitud." "Dart Repository · features/service_requests/data" {
                    properties {
                        "HU" "SCRUM-27 / SCRUM-71"
                    }
                }
                mobRequestRepo = component "Repositorio de solicitudes" "Crea la solicitud y consulta su detalle para la confirmación." "Dart Repository · features/service_requests/data" {
                    properties {
                        "HU" "SCRUM-27 / SCRUM-71"
                    }
                }
                mobApiClient = component "Cliente HTTP" "Adjunta el JWT y X-Correlation-Id, aplica timeouts y traduce respuestas problem+json (400, 401, 403, 404, 422) en errores de la app. No envía tenant_id." "Dart HTTP Client · core/http"
                mobLocation = component "Ubicación del dispositivo" "Pide el permiso de ubicación y obtiene las coordenadas (latitude, longitude) del GPS del dispositivo." "Dart Service · core/location" {
                    properties {
                        "HU" "SCRUM-27 / SCRUM-71"
                    }
                }
                mobUi = component "UI compartida" "Widgets reutilizables de carga, vacío y error." "Flutter Widgets · core/ui"
            }

            gateway = container "API Gateway" "Enruta, autentica y limita." "Nginx + gateway" "Gateway"
        }

        # Personas → Angular Web
        adminPlataforma -> webLogin "Inicia sesión"
        adminPlataforma -> webTenants "Activa y desactiva tenants"
        adminTenant -> webLogin "Inicia sesión"

        # Personas → Flutter Mobile
        clienteEmpresa -> mobLogin "Inicia sesión"
        clienteEmpresa -> mobWizard "Crea una solicitud de servicio (el contrato v1 solo admite el rol cliente)"
        tecnicoProveedor -> mobLogin "Inicia sesión"

        # Angular Web: componentes internos
        webShell -> webGuards "Protege las rutas con"
        webShell -> webLogin "Redirige si no hay sesión"
        webShell -> webTenants "Carga la ruta de tenants"
        webGuards -> webAuth "Consulta el rol del usuario en"
        webLogin -> webAuth "Envía las credenciales a"
        webLogin -> webUi "Muestra estados con"
        webTenants -> webTenantsApi "Lista, activa y desactiva tenants con"
        webTenants -> webUi "Muestra estados con"
        webAuth -> webInterceptor "Entrega el token a"
        webInterceptor -> webShell "Redirige ante 401/403 mediante"

        # Angular Web → Gateway
        webAuth -> gateway "POST /v1/auth/login · GET /v1/users/me (SDD 3.4.1)" "HTTPS/JSON" "Contrato pendiente"
        webTenantsApi -> gateway "Administración de tenants" "HTTPS/JSON" "Contrato pendiente"

        # Flutter Mobile: componentes internos
        mobRouter -> mobLogin "Redirige si no hay sesión"
        mobRouter -> mobWizard "Navega entre los pasos de"
        mobLogin -> mobSession "Envía las credenciales a"
        mobLogin -> mobUi "Muestra estados con"
        mobWizard -> mobFormState "Lee y actualiza"
        mobWizard -> mobUi "Muestra estados con"
        mobFormState -> mobLocation "Obtiene las coordenadas de"
        mobFormState -> mobCatalogRepo "Obtiene categorías de"
        mobFormState -> mobRequestRepo "Envía la solicitud confirmada a"
        mobSession -> mobApiClient "Entrega el token a"
        mobCatalogRepo -> mobApiClient "Usa"
        mobRequestRepo -> mobApiClient "Usa"
        mobApiClient -> mobRouter "Redirige a login ante 401 mediante"

        # Flutter Mobile → Gateway
        mobSession -> gateway "POST /v1/auth/login · GET /v1/users/me (SDD 3.4.1)" "HTTPS/JSON" "Contrato pendiente"
        mobCatalogRepo -> gateway "GET /v1/catalog/categories" "HTTPS/JSON"
        mobRequestRepo -> gateway "POST /v1/service-requests · GET /v1/service-requests/{id}" "HTTPS/JSON"
    }

    views {
        component web "C4-L3-Web" "C4-L3 · Componentes de Angular Web — Sprint 3" {
            include *
            autoLayout tb
        }

        component mobile "C4-L3-Mobile" "C4-L3 · Componentes de Flutter Mobile — Sprint 3" {
            include *
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
            element "Web Browser" {
                shape WebBrowser
            }
            element "Mobile App" {
                shape MobileDevicePortrait
            }
            element "Gateway" {
                shape Hexagon
            }
            relationship "Contrato pendiente" {
                color #c0392b
                dashed true
            }
        }
    }

}
