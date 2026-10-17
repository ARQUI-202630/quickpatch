/**
 * Servidor Mock del API Gateway para Pruebas Locales E2E (QA)
 * 
 * Emulador ligero en Node.js de las rutas y reglas de seguridad del Gateway
 * bajo los contratos OpenAPI (/api/v1/*), permitiendo validar colecciones
 * de Postman en entornos locales de desarrollo.
 */

const http = require('http');

const PORT = process.env.PORT || 8080;

function parseJwt(authHeader) {
    if (!authHeader || !authHeader.startsWith('Bearer ')) return null;
    const token = authHeader.substring(7);
    const parts = token.split('.');
    if (parts.length < 2) return null;
    try {
        const payloadBase64 = parts[1].replace(/-/g, '+').replace(/_/g, '/');
        const json = Buffer.from(payloadBase64, 'base64').toString('utf8');
        return JSON.parse(json);
    } catch {
        return null;
    }
}

function sendProblemDetails(res, status, problemType, title, detail, correlationId) {
    const body = {
        type: `https://quickpatch.internal/problems/${problemType}`,
        title: title,
        status: status,
        detail: detail,
        correlationId: correlationId || `cid-${Date.now()}`
    };
    res.writeHead(status, {
        'Content-Type': 'application/problem+json',
        'X-Correlation-Id': body.correlationId
    });
    res.end(JSON.stringify(body, null, 2));
}

function makeToken(sub, role, tenantId) {
    const header = Buffer.from(JSON.stringify({ alg: "RS256", typ: "JWT" })).toString("base64url");
    const payload = Buffer.from(JSON.stringify({
        sub: sub,
        role: role,
        tenant_id: tenantId || "a1a1a1a1-bbbb-cccc-dddd-eeeeeeeeeeee",
        exp: Math.floor(Date.now() / 1000) + 7200
    })).toString("base64url");
    return `${header}.${payload}.mock-signature-rs256`;
}

const registeredDocuments = new Set(["CC-1020304050"]);
const registeredEmails = new Set(["tecnico.existente@quickpatch.test"]);

const validLocalityCodes = new Set([
    "01", "02", "03", "04", "05", "06", "07", "08", "09", "10",
    "11", "12", "13", "14", "15", "16", "17", "18", "19", "20"
]);

const techniciansState = {
    "usr-tec-01": { status: "no_disponible", localityCodes: ["02", "12", "13"] },
    "usr-tec-02": { status: "ocupado", localityCodes: ["01", "02"] },
    "usr-tec-03": { status: "disponible", localityCodes: ["08", "09"] }
};

const offersDb = {
    "usr-tec-01": [
        {
            attemptId: "attempt-valid-01",
            serviceRequestId: "sr-assigned-01",
            categoryName: "Plomería",
            locality: "Chapinero",
            distanceM: 1450.5,
            description: "Fuga de agua en lavaplatos principal",
            status: "pendiente",
            offeredAt: new Date(Date.now() - 30000).toISOString(),
            expiresAt: new Date(Date.now() + 60000).toISOString()
        },
        {
            attemptId: "attempt-reject-01",
            serviceRequestId: "sr-reject-01",
            categoryName: "Cerrajería",
            locality: "Teusaquillo",
            distanceM: 2100.0,
            description: "Cambio de chapa de seguridad",
            status: "pendiente",
            offeredAt: new Date(Date.now() - 20000).toISOString(),
            expiresAt: new Date(Date.now() + 70000).toISOString()
        }
    ]
};

const serviceRequestsDb = {
    "sr-assigned-01": {
        status: "asignado",
        technicianId: "usr-tec-01",
        clientId: "usr-client-01"
    },
    "sr-unassigned-01": {
        status: "buscando_tecnico",
        technicianId: null,
        clientId: "usr-client-01"
    }
};

const server = http.createServer((req, res) => {
    const correlationId = req.headers['x-correlation-id'] || `cid-${Date.now()}`;
    const user = parseJwt(req.headers['authorization']);

    let rawBody = '';
    req.on('data', chunk => { rawBody += chunk; });
    req.on('end', () => {
        const url = req.url.split('?')[0];

        // 1. Registro de cliente (Identity)
        if (url === '/api/v1/auth/register/client' && req.method === 'POST') {
            res.writeHead(201, {
                'Content-Type': 'application/json',
                'X-Correlation-Id': correlationId
            });
            return res.end(JSON.stringify({ message: "Usuario cliente registrado exitosamente" }));
        }

        // 1.1 Registro de técnico / proveedor (Identity - SCRUM-56)
        if (url === '/api/v1/auth/register/technician' && req.method === 'POST') {
            let body = {};
            try { body = JSON.parse(rawBody || '{}'); } catch {}

            // Validaciones de contrato (RFC 9457)
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!body.documentId || !body.password || body.password.length < 8 || !body.email || !emailRegex.test(body.email)) {
                return sendProblemDetails(res, 400, 'validacion-solicitud', 'Datos de registro inválidos', 'El documento, correo válido y contraseña de al menos 8 caracteres son obligatorios.', correlationId);
            }
            if (registeredDocuments.has(String(body.documentId))) {
                return sendProblemDetails(res, 409, 'documento-registrado', 'El documento ya está registrado', 'El documento ya se encuentra asociado a un perfil técnico.', correlationId);
            }
            if (registeredEmails.has(body.email)) {
                return sendProblemDetails(res, 409, 'correo-registrado', 'El correo ya está registrado', 'El correo ya está en uso en el tenant.', correlationId);
            }

            // Registrar en memoria para que duplicados posteriores en la misma corrida respondan 409
            registeredDocuments.add(String(body.documentId));
            registeredEmails.add(body.email);

            res.writeHead(201, {
                'Content-Type': 'application/json',
                'X-Correlation-Id': correlationId
            });
            return res.end(JSON.stringify({
                id: `tec-${Date.now()}`,
                email: body.email,
                fullName: body.fullName || "Técnico QA",
                role: body.role || "tecnico",
                phone: body.phone || "3001234567",
                verificationStatus: "pendiente"
            }));
        }

        // 2. Login de usuarios (Identity)
        if (url === '/api/v1/auth/login' && req.method === 'POST') {
            let body = {};
            try { body = JSON.parse(rawBody || '{}'); } catch {}

            // IDN-019 / RN-T1 está PENDIENTE en el MVP (un solo tenant, SCRUM-41). El sistema real responde 401
            // credenciales-invalidas a un correo que no existe, y eso es lo que simula este mock.
            if (body.email && body.email.includes('inactivo')) {
                return sendProblemDetails(res, 401, 'credenciales-invalidas', 'Correo o contraseña incorrectos', 'Correo o contraseña incorrectos.', correlationId);
            }

            const tenantId = (body.email && body.email.includes('beta'))
                ? "22222222-2222-2222-2222-222222222222"
                : "11111111-1111-1111-1111-111111111111";

            // Administrador de tenant (evaluar antes de tecnico para evitar colisiones)
            if (body.email && body.email.includes('admin')) {
                const token = makeToken("usr-admin-01", "admin_tenant", tenantId);
                res.writeHead(200, { 'Content-Type': 'application/json', 'X-Correlation-Id': correlationId });
                return res.end(JSON.stringify({
                    accessToken: token,
                    tokenType: "Bearer",
                    expiresIn: 7200,
                    user: { id: "usr-admin-01", email: body.email, role: "admin_tenant" }
                }));
            }

            // Técnico (SCRUM-56, SCRUM-81, SCRUM-90, SCRUM-93)
            if (body.email && (body.email.includes('tecnico') || registeredEmails.has(body.email))) {
                const techSub = (body.email.includes('segundo') || body.email.includes('ocupado'))
                    ? "usr-tec-02"
                    : (body.email.includes('otro') ? "usr-tec-03" : "usr-tec-01");
                const token = makeToken(techSub, "tecnico", tenantId);
                res.writeHead(200, { 'Content-Type': 'application/json', 'X-Correlation-Id': correlationId });
                return res.end(JSON.stringify({
                    accessToken: token,
                    tokenType: "Bearer",
                    expiresIn: 7200,
                    user: { id: techSub, email: body.email, role: "tecnico", verificationStatus: "pendiente" }
                }));
            }

            // Cliente
            const token = makeToken("usr-client-01", "cliente", tenantId);
            res.writeHead(200, { 'Content-Type': 'application/json', 'X-Correlation-Id': correlationId });
            return res.end(JSON.stringify({
                accessToken: token,
                tokenType: "Bearer",
                expiresIn: 7200,
                user: { id: "usr-client-01", email: body.email, role: "cliente" }
            }));
        }

        // 2.1 Perfil del usuario autenticado (Identity - SCRUM-56)
        if (url === '/api/v1/users/me' && req.method === 'GET') {
            if (!user) {
                return sendProblemDetails(res, 401, 'no-autenticado', 'No autenticado', 'Token ausente o inválido (IDN-017)', correlationId);
            }
            res.writeHead(200, { 'Content-Type': 'application/json', 'X-Correlation-Id': correlationId });
            return res.end(JSON.stringify({
                id: user.sub,
                email: user.email || (user.role === 'tecnico' ? 'tecnico@quickpatch.test' : 'cliente@quickpatch.test'),
                role: user.role,
                verificationStatus: user.role === 'tecnico' ? 'pendiente' : null
            }));
        }

        // 3. Catálogo administrativo de categorías (Catalog - solo admin_tenant)
        if (url === '/api/v1/catalog/admin/categories') {
            if (!user) {
                return sendProblemDetails(res, 401, 'no-autenticado', 'No autenticado', 'Token ausente (IDN-017)', correlationId);
            }
            if (user.role !== 'admin_tenant' && user.role !== 'admin') {
                return sendProblemDetails(res, 403, 'no-autorizado', 'Acceso Denegado', 'Solo administradores pueden crear categorías (CAT-010, SCRUM-65)', correlationId);
            }
            res.writeHead(201, {
                'Content-Type': 'application/json',
                'X-Correlation-Id': correlationId
            });
            return res.end(JSON.stringify({
                id: "3f1c2a4e-8d7b-4c1a-9e2f-5b6a7c8d9e01",
                name: "Plomería QA",
                active: true,
                tenantId: user.tenant_id
            }));
        }

        // 3.1 Consulta pública de catálogo con aislamiento tenant (Catalog - SCRUM-62)
        if (url === '/api/v1/catalog/categories' && req.method === 'GET') {
            if (!user) {
                return sendProblemDetails(res, 401, 'no-autenticado', 'No autenticado', 'Token ausente', correlationId);
            }
            // Aislamiento RLS: Categoría de Tenant Alfa no es visible para Tenant Beta
            const categories = [
                { id: "cat-global-01", name: "Cerrajería Global", active: true, tenantId: null }
            ];
            if (user.tenant_id === "11111111-1111-1111-1111-111111111111") {
                categories.push({ id: "3f1c2a4e-8d7b-4c1a-9e2f-5b6a7c8d9e01", name: "Plomería Exclusiva Alfa", active: true, tenantId: user.tenant_id });
            }
            res.writeHead(200, { 'Content-Type': 'application/json', 'X-Correlation-Id': correlationId });
            return res.end(JSON.stringify(categories));
        }

        // 4. Creación de solicitudes de servicio (ServiceRequest - solo rol cliente)
        if (url === '/api/v1/service-requests' && req.method === 'POST') {
            if (!user) {
                return sendProblemDetails(res, 401, 'no-autenticado', 'No autenticado', 'Token ausente en la petición (IDN-017)', correlationId);
            }
            if (user.role !== 'cliente') {
                return sendProblemDetails(res, 403, 'no-autorizado', 'Acceso Denegado', 'Solo el rol cliente puede crear solicitudes de servicio (IDN-012, SCRUM-65)', correlationId);
            }
            res.writeHead(201, {
                'Content-Type': 'application/json',
                'X-Correlation-Id': correlationId,
                'Location': '/api/v1/service-requests/sr-qa-001'
            });
            return res.end(JSON.stringify({
                id: "sr-qa-001",
                status: "buscando_tecnico",
                categoryId: "3f1c2a4e-8d7b-4c1a-9e2f-5b6a7c8d9e01",
                tenantId: user.tenant_id,
                createdAt: new Date().toISOString()
            }));
        }

        // 4.1 Consulta de solicitud por ID con aislamiento multi-tenant y detalle por rol (SCRUM-62, SCRUM-91, SCRUM-93)
        if (url.startsWith('/api/v1/service-requests/') && req.method === 'GET') {
            if (!user) {
                return sendProblemDetails(res, 401, 'no-autenticado', 'No autenticado', 'Token ausente (IDN-017)', correlationId);
            }
            const reqId = url.split('/').pop();
            // Aislamiento por Tenant (SCRUM-62 / RLS)
            if (user.tenant_id !== "11111111-1111-1111-1111-111111111111") {
                return sendProblemDetails(res, 404, 'no-encontrado', 'Solicitud no encontrada', 'La solicitud no existe en el tenant especificado (RLS Isolation)', correlationId);
            }

            // Simulación de estados de solicitud:
            // sr-unassigned-01: buscando_tecnico (no asignada)
            // sr-assigned-01: asignado a usr-tec-01
            // sr-qa-001: buscando_tecnico
            const isAssignedTest = reqId === 'sr-assigned-01' || serviceRequestsDb[reqId]?.status === 'asignado';
            const assignedTechId = isAssignedTest ? (serviceRequestsDb[reqId]?.technicianId || "usr-tec-01") : null;

            if (user.role === 'tecnico') {
                // Caso DTL-002: Técnico asignado pero la solicitud está fuera de rango (buscando_tecnico) -> 403
                if (reqId === 'sr-unassigned-01') {
                    return sendProblemDetails(res, 403, 'solicitud-no-asignada', 'Acceso Denegado', 'El técnico no puede consultar el detalle de una solicitud que no le ha sido asignada (RN-SR13, SCRUM-34)', correlationId);
                }
                // Caso DTL-003: Técnico no asignado a la solicitud -> 404 (confidencialidad)
                if (assignedTechId && assignedTechId !== user.sub) {
                    return sendProblemDetails(res, 404, 'no-encontrado', 'Solicitud no encontrada', 'La solicitud no existe o no está asignada al técnico (RN-SR13)', correlationId);
                }
                // Caso DTL-001: Técnico asignado ve detalle completo con contacto del cliente (RN-SR13)
                res.writeHead(200, { 'Content-Type': 'application/json', 'X-Correlation-Id': correlationId });
                return res.end(JSON.stringify({
                    id: reqId,
                    status: "asignado",
                    categoryId: "3f1c2a4e-8d7b-4c1a-9e2f-5b6a7c8d9e01",
                    tenantId: user.tenant_id,
                    addressText: "Calle 63 # 9-45, apto 502, Chapinero",
                    location: { latitude: 4.6486, longitude: -74.063 },
                    description: "Fuga de agua en lavaplatos principal",
                    client: {
                        id: "usr-client-01",
                        fullName: "Ana Gómez",
                        phone: "+573009876543"
                    },
                    technician: {
                        id: user.sub,
                        fullName: "Carlos Pérez (Técnico)"
                    },
                    assignedAt: new Date().toISOString()
                }));
            }

            // Cliente dueño consultando su solicitud (DTL-005)
            res.writeHead(200, { 'Content-Type': 'application/json', 'X-Correlation-Id': correlationId });
            return res.end(JSON.stringify({
                id: reqId,
                status: isAssignedTest ? "asignado" : "buscando_tecnico",
                categoryId: "3f1c2a4e-8d7b-4c1a-9e2f-5b6a7c8d9e01",
                tenantId: user.tenant_id,
                addressText: "Calle 63 # 9-45, apto 502, Chapinero",
                location: { latitude: 4.6486, longitude: -74.063 },
                description: "Fuga de agua en lavaplatos principal",
                client: null,
                technician: isAssignedTest ? { id: "usr-tec-01", fullName: "Carlos Pérez (Técnico)" } : null
            }));
        }

        // =========================================================================
        // 5. LOCALIDADES Y COBERTURA (Matching Service - SCRUM-88, SCRUM-90)
        // =========================================================================
        // 5.1 Catálogo público de 20 localidades oficiales de Bogotá (COV-001)
        if (url === '/api/v1/localities' && req.method === 'GET') {
            const localities = [
                { code: "01", name: "Usaquén" },
                { code: "02", name: "Chapinero" },
                { code: "03", name: "Santa Fe" },
                { code: "04", name: "San Cristóbal" },
                { code: "05", name: "Usme" },
                { code: "06", name: "Tunjuelito" },
                { code: "07", name: "Bosa" },
                { code: "08", name: "Kennedy" },
                { code: "09", name: "Fontibón" },
                { code: "10", name: "Engativá" },
                { code: "11", name: "Suba" },
                { code: "12", name: "Barrios Unidos" },
                { code: "13", name: "Teusaquillo" },
                { code: "14", name: "Los Mártires" },
                { code: "15", name: "Antonio Nariño" },
                { code: "16", name: "Puente Aranda" },
                { code: "17", name: "La Candelaria" },
                { code: "18", name: "Rafael Uribe Uribe" },
                { code: "19", name: "Ciudad Bolívar" },
                { code: "20", name: "Sumapaz" }
            ];
            res.writeHead(200, { 'Content-Type': 'application/json', 'X-Correlation-Id': correlationId });
            return res.end(JSON.stringify(localities));
        }

        // 5.2 Disponibilidad del técnico autenticado (AVA-001 a AVA-005)
        if (url === '/api/v1/technicians/me/availability') {
            if (!user) {
                return sendProblemDetails(res, 401, 'no-autenticado', 'No autenticado', 'Token ausente o inválido (IDN-017)', correlationId);
            }
            if (user.role !== 'tecnico') {
                return sendProblemDetails(res, 403, 'no-autorizado', 'Acceso Denegado', 'Solo técnicos pueden gestionar su disponibilidad (SCRUM-33)', correlationId);
            }

            const techId = user.sub;
            if (!techniciansState[techId]) {
                techniciansState[techId] = { status: 'no_disponible', localityCodes: [] };
            }

            if (req.method === 'GET') {
                res.writeHead(200, { 'Content-Type': 'application/json', 'X-Correlation-Id': correlationId });
                return res.end(JSON.stringify({
                    status: techniciansState[techId].status,
                    available: techniciansState[techId].status === 'disponible',
                    busy: techniciansState[techId].status === 'ocupado',
                    updatedAt: new Date().toISOString()
                }));
            }

            if (req.method === 'PUT') {
                let body = {};
                try { body = JSON.parse(rawBody || '{}'); } catch {}

                // RN-M6: Si el técnico está ocupado con un servicio, no puede cambiar estado manualmente -> 409
                if (techniciansState[techId].status === 'ocupado') {
                    return sendProblemDetails(res, 409, 'transicion-invalida', 'Técnico Ocupado', 'El técnico se encuentra en servicio activo y no puede cambiar disponibilidad manualmente (RN-M6)', correlationId);
                }

                if (!body.status || !['disponible', 'no_disponible'].includes(body.status)) {
                    return sendProblemDetails(res, 400, 'validacion-solicitud', 'Estado Inválido', 'El estado debe ser disponible o no_disponible', correlationId);
                }

                techniciansState[techId].status = body.status;
                res.writeHead(200, { 'Content-Type': 'application/json', 'X-Correlation-Id': correlationId });
                return res.end(JSON.stringify({
                    status: techniciansState[techId].status,
                    available: techniciansState[techId].status === 'disponible',
                    busy: false,
                    updatedAt: new Date().toISOString()
                }));
            }
        }

        // 5.3 Cobertura geográfica del técnico (COV-002 a COV-004)
        if (url === '/api/v1/technicians/me/coverage') {
            if (!user) {
                return sendProblemDetails(res, 401, 'no-autenticado', 'No autenticado', 'Token ausente o inválido (IDN-017)', correlationId);
            }
            if (user.role !== 'tecnico') {
                return sendProblemDetails(res, 403, 'no-autorizado', 'Acceso Denegado', 'Solo técnicos pueden gestionar su zona de cobertura', correlationId);
            }

            const techId = user.sub;
            if (!techniciansState[techId]) {
                techniciansState[techId] = { status: 'no_disponible', localityCodes: [] };
            }

            if (req.method === 'GET') {
                res.writeHead(200, { 'Content-Type': 'application/json', 'X-Correlation-Id': correlationId });
                return res.end(JSON.stringify({
                    localityCodes: techniciansState[techId].localityCodes,
                    updatedAt: new Date().toISOString()
                }));
            }

            if (req.method === 'PUT') {
                let body = {};
                try { body = JSON.parse(rawBody || '{}'); } catch {}

                // Validación: debe ser array no vacío y con códigos del 01 al 20
                if (!Array.isArray(body.localityCodes) || body.localityCodes.length === 0) {
                    return sendProblemDetails(res, 400, 'validacion-solicitud', 'Cobertura Inválida', 'Debe seleccionar al menos una localidad válida de Bogotá (DD 8.3.6)', correlationId);
                }
                const invalidCodes = body.localityCodes.filter(c => !validLocalityCodes.has(c));
                if (invalidCodes.length > 0) {
                    return sendProblemDetails(res, 400, 'validacion-solicitud', 'Localidad Inexistente', `Códigos de localidad no reconocidos: ${invalidCodes.join(', ')}`, correlationId);
                }

                techniciansState[techId].localityCodes = body.localityCodes;
                res.writeHead(200, { 'Content-Type': 'application/json', 'X-Correlation-Id': correlationId });
                return res.end(JSON.stringify({
                    localityCodes: techniciansState[techId].localityCodes,
                    updatedAt: new Date().toISOString()
                }));
            }
        }

        // =========================================================================
        // 6. OFERTAS DE ASIGNACIÓN (Matching Service - SCRUM-79, SCRUM-81)
        // =========================================================================
        // 6.1 Consultar ofertas pendientes del técnico (OFF-001)
        if (url === '/api/v1/matching/offers' && req.method === 'GET') {
            if (!user) {
                return sendProblemDetails(res, 401, 'no-autenticado', 'No autenticado', 'Token ausente o inválido (IDN-017)', correlationId);
            }
            if (user.role !== 'tecnico') {
                return sendProblemDetails(res, 403, 'no-autorizado', 'Acceso Denegado', 'Solo técnicos pueden consultar sus ofertas de asignación', correlationId);
            }

            const techId = user.sub;
            const offers = offersDb[techId] || [];
            const pendingOffers = offers.filter(o => o.status === 'pendiente');

            // Retorna oferta con localidad y distancia pero SIN dirección exacta (RN-SR13)
            res.writeHead(200, { 'Content-Type': 'application/json', 'X-Correlation-Id': correlationId });
            return res.end(JSON.stringify({
                items: pendingOffers.map(o => ({
                    attemptId: o.attemptId,
                    serviceRequestId: o.serviceRequestId,
                    categoryName: o.categoryName,
                    locality: o.locality,
                    distanceM: o.distanceM,
                    description: o.description,
                    offeredAt: o.offeredAt,
                    expiresAt: o.expiresAt
                })),
                total: pendingOffers.length
            }));
        }

        // 6.2 Aceptar oferta (OFF-002 a OFF-005, OFF-007)
        if (url.startsWith('/api/v1/matching/offers/') && url.endsWith('/accept') && req.method === 'POST') {
            if (!user) {
                return sendProblemDetails(res, 401, 'no-autenticado', 'No autenticado', 'Token ausente', correlationId);
            }
            if (user.role !== 'tecnico') {
                return sendProblemDetails(res, 403, 'no-autorizado', 'Acceso Denegado', 'Solo rol técnico puede responder ofertas (SCRUM-30)', correlationId);
            }

            const parts = url.split('/');
            const attemptId = parts[parts.length - 2];
            const techId = user.sub;

            // Caso OFF-004: Oferta vencida por OfferExpirer (RN-M8)
            if (attemptId === 'attempt-expired-01') {
                return sendProblemDetails(res, 409, 'oferta-no-disponible', 'Oferta Vencida', 'La oferta ha expirado por tiempo límite sin respuesta (RN-M8)', correlationId);
            }

            // Caso OFF-005: Técnico ya ocupado en otro servicio (RN-M7)
            if (techniciansState[techId]?.status === 'ocupado' && attemptId !== 'attempt-valid-01') {
                return sendProblemDetails(res, 409, 'tecnico-no-disponible', 'Técnico Ocupado', 'El técnico ya no está disponible para aceptar la oferta (RN-M7)', correlationId);
            }

            const offers = offersDb[techId] || [];
            const offer = offers.find(o => o.attemptId === attemptId);

            // Caso OFF-003: Oferta inexistente, ajena o ya respondida
            if (!offer || offer.status !== 'pendiente') {
                return sendProblemDetails(res, 409, 'oferta-no-disponible', 'Oferta No Disponible', 'La oferta no existe, ya fue respondida o pertenece a otro técnico (RN-M2)', correlationId);
            }

            // Éxito: Transacción atómica
            offer.status = 'aceptado';
            techniciansState[techId] = techniciansState[techId] || {};
            techniciansState[techId].status = 'ocupado'; // RN-M6
            serviceRequestsDb[offer.serviceRequestId] = {
                status: 'asignado',
                technicianId: techId
            };

            res.writeHead(200, { 'Content-Type': 'application/json', 'X-Correlation-Id': correlationId });
            return res.end(JSON.stringify({
                attemptId: attemptId,
                response: "aceptado",
                serviceRequestId: offer.serviceRequestId,
                technicianId: techId,
                assignedAt: new Date().toISOString()
            }));
        }

        // 6.3 Rechazar oferta (OFF-006)
        if (url.startsWith('/api/v1/matching/offers/') && url.endsWith('/reject') && req.method === 'POST') {
            if (!user) {
                return sendProblemDetails(res, 401, 'no-autenticado', 'No autenticado', 'Token ausente', correlationId);
            }
            if (user.role !== 'tecnico') {
                return sendProblemDetails(res, 403, 'no-autorizado', 'Acceso Denegado', 'Solo rol técnico puede rechazar ofertas', correlationId);
            }

            const parts = url.split('/');
            const attemptId = parts[parts.length - 2];
            const techId = user.sub;

            const offers = offersDb[techId] || [];
            const offer = offers.find(o => o.attemptId === attemptId);

            if (!offer || offer.status !== 'pendiente') {
                return sendProblemDetails(res, 409, 'oferta-no-disponible', 'Oferta No Disponible', 'La oferta no existe o ya fue respondida', correlationId);
            }

            // Rechazo sin penalización (RF-10, R12)
            offer.status = 'rechazado';
            res.writeHead(200, { 'Content-Type': 'application/json', 'X-Correlation-Id': correlationId });
            return res.end(JSON.stringify({
                attemptId: attemptId,
                response: "rechazado",
                nextCandidateNotified: true
            }));
        }

        res.writeHead(404, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: "Ruta no encontrada" }));
    });
});

if (require.main === module) {
    server.listen(PORT, () => {
        console.log(`[Simulación Preparatoria] Mock Gateway escuchando en http://localhost:${PORT}`);
    });
}

module.exports = server;
