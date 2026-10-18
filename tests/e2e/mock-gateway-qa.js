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

const providerTechniciansDb = {
    "11111111-1111-1111-1111-111111111111": []
};

const adminTechniciansDb = {
    "11111111-1111-1111-1111-111111111111": {
        "usr-tec-pending-01": {
            userId: "usr-tec-pending-01",
            fullName: "Hernando López",
            email: "hernando.lopez@quickpatch.test",
            documentId: "CC-1122334455",
            phone: "+573104443322",
            specialty: "Cerrajería",
            verificationStatus: "pendiente",
            tenantId: "11111111-1111-1111-1111-111111111111",
            role: "tecnico"
        },
        "usr-tec-pending-02": {
            userId: "usr-tec-pending-02",
            fullName: "Gloria Martínez",
            email: "gloria.martinez@quickpatch.test",
            documentId: "CC-2233445566",
            phone: "+573109998877",
            specialty: "Electricidad",
            verificationStatus: "pendiente",
            tenantId: "11111111-1111-1111-1111-111111111111",
            role: "tecnico"
        },
        "usr-tec-approved-01": {
            userId: "usr-tec-approved-01",
            fullName: "Carlos Pérez (Aprobado)",
            email: "carlos.aprobado@quickpatch.test",
            documentId: "CC-3344556677",
            phone: "+573001234567",
            specialty: "Plomería",
            verificationStatus: "aprobado",
            tenantId: "11111111-1111-1111-1111-111111111111",
            role: "tecnico"
        },
        "usr-tec-suspended-01": {
            userId: "usr-tec-suspended-01",
            fullName: "Raúl Sánchez (Suspendido)",
            email: "raul.suspendido@quickpatch.test",
            documentId: "CC-4455667788",
            phone: "+573151234567",
            specialty: "Pintura",
            verificationStatus: "suspendido",
            suspensionReason: "Reiteradas quejas de clientes por incumplimiento",
            tenantId: "11111111-1111-1111-1111-111111111111",
            role: "tecnico"
        }
    },
    "22222222-2222-2222-2222-222222222222": {
        "usr-tec-beta-01": {
            userId: "usr-tec-beta-01",
            fullName: "Técnico Beta",
            email: "tecnico.beta@quickpatch.test",
            documentId: "CC-9988776655",
            phone: "+573112223344",
            specialty: "Gasodomésticos",
            verificationStatus: "pendiente",
            tenantId: "22222222-2222-2222-2222-222222222222",
            role: "tecnico"
        }
    }
};

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

            // Proveedor (SCRUM-36 / SCRUM-99 / RF-16)
            if (body.email && body.email.includes('proveedor')) {
                const provSub = (body.email.includes('segundo') || body.email.includes('proveedor2') || body.email.includes('ajeno'))
                    ? "usr-prov-02"
                    : "usr-prov-01";
                const token = makeToken(provSub, "proveedor", tenantId);
                res.writeHead(200, { 'Content-Type': 'application/json', 'X-Correlation-Id': correlationId });
                return res.end(JSON.stringify({
                    accessToken: token,
                    tokenType: "Bearer",
                    expiresIn: 7200,
                    user: { id: provSub, email: body.email, role: "proveedor" }
                }));
            }

            // Cliente (SCRUM-31: Soporte para cliente propietario usr-client-01 y cliente ajeno usr-client-02 en mismo tenant)
            const clientSub = (body.email && (body.email.includes('cliente2') || body.email.includes('ajeno') || body.email.includes('otrocliente')))
                ? "usr-client-02"
                : "usr-client-01";
            const token = makeToken(clientSub, "cliente", tenantId);
            res.writeHead(200, { 'Content-Type': 'application/json', 'X-Correlation-Id': correlationId });
            return res.end(JSON.stringify({
                accessToken: token,
                tokenType: "Bearer",
                expiresIn: 7200,
                user: { id: clientSub, email: body.email, role: "cliente" }
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

        // 4. Creación de solicitudes de servicio (ServiceRequest / Matching - solo rol cliente)
        if ((url === '/api/v1/service-requests' || url === '/v1/service-requests') && req.method === 'POST') {
            if (!user) {
                return sendProblemDetails(res, 401, 'no-autenticado', 'No autenticado', 'Token ausente en la petición (IDN-017)', correlationId);
            }
            if (user.role !== 'cliente') {
                return sendProblemDetails(res, 403, 'no-autorizado', 'Acceso Denegado', 'Solo el rol cliente puede crear solicitudes de servicio (IDN-012, SCRUM-65)', correlationId);
            }
            let body = {};
            try { body = JSON.parse(rawBody || '{}'); } catch {}

            const isNoCandidates = (body.description && body.description.includes('sin_candidatos')) ||
                                   (body.location && (body.location.latitude > 4.75 || body.location.latitude < 4.50));
            const isMatchingExplicit = body.description && (body.description.includes('asignación') || body.description.includes('matching') || body.description.includes('urgente'));

            let initialStatus = "buscando_tecnico";
            let assignedTech = null;

            if (isNoCandidates) {
                initialStatus = "en_espera";
                assignedTech = null;
            } else if (isMatchingExplicit) {
                initialStatus = "asignado";
                assignedTech = "usr-tec-approved-01";
            }

            const reqId = body.id || (isNoCandidates ? `sr-mat-espera-${Date.now()}` : (isMatchingExplicit ? `sr-mat-${Date.now()}` : (url.includes('tracking') ? 'sr-tracking-01' : 'sr-qa-001')));

            serviceRequestsDb[reqId] = {
                id: reqId,
                status: initialStatus,
                technicianId: assignedTech,
                clientId: user.sub,
                tenantId: user.tenant_id,
                description: body.description || "Solicitud de servicio estándar",
                location: body.location || { latitude: 4.6533, longitude: -74.0836 },
                addressText: body.addressText || "Calle 45 # 13-20",
                assignedAt: assignedTech ? new Date().toISOString() : null,
                createdAt: new Date().toISOString()
            };

            res.writeHead(201, {
                'Content-Type': 'application/json',
                'X-Correlation-Id': correlationId,
                'Location': `/api/v1/service-requests/${reqId}`
            });
            return res.end(JSON.stringify({
                id: reqId,
                status: initialStatus,
                categoryId: body.categoryId || "3f1c2a4e-8d7b-4c1a-9e2f-5b6a7c8d9e01",
                description: serviceRequestsDb[reqId].description,
                location: serviceRequestsDb[reqId].location,
                addressText: serviceRequestsDb[reqId].addressText,
                technicianId: assignedTech,
                assignedAt: serviceRequestsDb[reqId].assignedAt,
                tenantId: user.tenant_id,
                createdAt: serviceRequestsDb[reqId].createdAt
            }));
        }

        // 4.1 Consulta de solicitud por ID con seguimiento en tiempo real y aislamiento (SCRUM-31, SCRUM-62, SCRUM-78, SCRUM-84, SCRUM-93)
        if (url.startsWith('/api/v1/service-requests/') && !url.endsWith('/status') && req.method === 'GET') {
            if (!user) {
                return sendProblemDetails(res, 401, 'no-autenticado', 'No autenticado', 'Token ausente (IDN-017)', correlationId);
            }
            const reqId = url.split('/').pop();
            // Aislamiento por Tenant (SCRUM-62 / RLS)
            if (user.tenant_id !== "11111111-1111-1111-1111-111111111111") {
                return sendProblemDetails(res, 404, 'no-encontrado', 'Solicitud no encontrada', 'La solicitud no existe en el tenant especificado (RLS Isolation)', correlationId);
            }

            const currentReq = serviceRequestsDb[reqId] || {
                status: (reqId === 'sr-assigned-01' ? 'asignado' : (reqId.includes('espera') ? 'en_espera' : 'buscando_tecnico')),
                technicianId: (reqId === 'sr-assigned-01' ? 'usr-tec-01' : null),
                clientId: 'usr-client-01'
            };

            const isAssignedOrBeyond = ['asignado', 'en_progreso', 'completado'].includes(currentReq.status) || reqId === 'sr-assigned-01';
            const assignedTechId = isAssignedOrBeyond ? (currentReq.technicianId || "usr-tec-approved-01") : null;

            if (user.role === 'tecnico') {
                // Caso DTL-002: Técnico asignado pero la solicitud está fuera de rango (buscando_tecnico / en_espera) -> 403
                if (reqId === 'sr-unassigned-01' || currentReq.status === 'buscando_tecnico' || currentReq.status === 'en_espera') {
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
                    status: currentReq.status,
                    categoryId: "3f1c2a4e-8d7b-4c1a-9e2f-5b6a7c8d9e01",
                    tenantId: user.tenant_id,
                    addressText: currentReq.addressText || "Calle 63 # 9-45, apto 502, Chapinero",
                    location: currentReq.location || { latitude: 4.6486, longitude: -74.063 },
                    description: currentReq.description || "Fuga de agua en lavaplatos principal",
                    technicianId: assignedTechId,
                    client: {
                        id: currentReq.clientId || "usr-client-01",
                        fullName: "Ana Gómez",
                        phone: "+573009876543"
                    },
                    technician: {
                        id: user.sub,
                        fullName: "Carlos Pérez (Técnico)",
                        specialty: "Plomería"
                    },
                    assignedAt: currentReq.assignedAt || new Date().toISOString()
                }));
            }

            // Rol Cliente: Aislamiento intra-tenant (Cliente 2 no puede ver la solicitud de Cliente 1)
            const ownerId = currentReq.clientId || "usr-client-01";
            if (user.role === 'cliente' && user.sub !== ownerId && !reqId.startsWith('sr-mat') && reqId !== 'sr-qa-001') {
                return sendProblemDetails(res, 404, 'no-encontrado', 'Solicitud no encontrada', 'La solicitud no pertenece al cliente autenticado (Confidencialidad intra-tenant)', correlationId);
            }

            // Cliente dueño consultando su solicitud en tiempo real (SCRUM-31, DTL-005, SCRUM-78)
            res.writeHead(200, { 'Content-Type': 'application/json', 'X-Correlation-Id': correlationId });
            return res.end(JSON.stringify({
                id: reqId,
                status: currentReq.status,
                categoryId: "3f1c2a4e-8d7b-4c1a-9e2f-5b6a7c8d9e01",
                tenantId: user.tenant_id,
                addressText: currentReq.addressText || "Calle 63 # 9-45, apto 502, Chapinero",
                location: currentReq.location || { latitude: 4.6486, longitude: -74.063 },
                description: currentReq.description || "Fuga de agua en lavaplatos principal",
                technicianId: assignedTechId,
                client: null,
                technician: isAssignedOrBeyond ? {
                    id: assignedTechId,
                    fullName: "Carlos Pérez (Técnico)",
                    specialty: "Plomería",
                    phone: "+573109876543"
                } : null,
                updatedAt: currentReq.updatedAt || currentReq.createdAt || new Date().toISOString()
            }));
        }

        // 4.2 Actualización de estado por técnico (ServiceRequest / SCRUM-31 / SCRUM-84)
        if (url.startsWith('/api/v1/service-requests/') && url.endsWith('/status') && (req.method === 'PATCH' || req.method === 'PUT')) {
            if (!user) {
                return sendProblemDetails(res, 401, 'no-autenticado', 'No autenticado', 'Token ausente (IDN-017)', correlationId);
            }
            if (user.role !== 'tecnico') {
                return sendProblemDetails(res, 403, 'no-autorizado', 'Acceso Denegado', 'Solo el técnico asignado puede actualizar el estado del servicio (SCRUM-31)', correlationId);
            }

            const parts = url.split('/');
            const reqId = parts[parts.length - 2];
            let body = {};
            try { body = JSON.parse(rawBody || '{}'); } catch {}

            const current = serviceRequestsDb[reqId] || {
                status: 'asignado',
                technicianId: 'usr-tec-01',
                clientId: 'usr-client-01'
            };

            // Control de asignación de técnico
            if (current.technicianId && current.technicianId !== user.sub) {
                return sendProblemDetails(res, 403, 'no-autorizado', 'Acceso Denegado', 'El técnico no está asignado a esta solicitud', correlationId);
            }

            const targetStatus = body.status;
            // Transiciones válidas según máquina de estados:
            // asignado -> en_progreso
            // en_progreso -> completado
            const validTransitions = {
                'buscando_tecnico': ['asignado'],
                'asignado': ['en_progreso', 'cancelado'],
                'en_progreso': ['completado', 'cancelado']
            };

            const allowed = validTransitions[current.status] || [];
            if (!allowed.includes(targetStatus)) {
                return sendProblemDetails(res, 409, 'transicion-invalida', 'Transición Inválida', `No se permite transicionar de ${current.status} a ${targetStatus} (RN-SR6)`, correlationId);
            }

            const previousStatus = current.status;
            current.status = targetStatus;
            current.updatedAt = new Date().toISOString();
            serviceRequestsDb[reqId] = current;

            res.writeHead(200, { 'Content-Type': 'application/json', 'X-Correlation-Id': correlationId });
            return res.end(JSON.stringify({
                serviceRequestId: reqId,
                previousStatus: previousStatus,
                status: targetStatus,
                technicianId: user.sub,
                occurredAt: current.updatedAt,
                noticeEmitted: "service-request.status-changed"
            }));
        }

        // 4.3 Canal en tiempo real (Communication / Gateway - ADR-023, SCRUM-451, SCRUM-84)
        if (url === '/api/v1/realtime') {
            if (!user) {
                return sendProblemDetails(res, 401, 'no-autenticado', 'No autenticado', 'Token ausente en handshake de tiempo real (IDN-017)', correlationId);
            }
            res.writeHead(200, {
                'Content-Type': 'application/json',
                'X-Correlation-Id': correlationId,
                'X-Realtime-Channel': 'active',
                'X-Transport': 'websocket'
            });
            return res.end(JSON.stringify({
                status: "connected",
                channel: "realtime",
                transport: "websocket",
                tenantId: user.tenant_id,
                userId: user.sub,
                subscribedEvents: [
                    "service-request.status-changed",
                    "service-request.created",
                    "matching.offer-created"
                ],
                connectedAt: new Date().toISOString()
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

        // =========================================================================
        // 8. GESTIÓN DE EQUIPO DE TÉCNICOS (Proveedor - RF-16, SCRUM-36, SCRUM-99)
        // =========================================================================
        // 8.1 Registro de técnico en el equipo del proveedor (POST /api/v1/providers/me/technicians)
        if ((url === '/api/v1/providers/me/technicians' || url === '/v1/providers/me/technicians') && req.method === 'POST') {
            if (!user) {
                return sendProblemDetails(res, 401, 'no-autenticado', 'No autenticado', 'Token ausente en registro de técnico de equipo (IDN-017)', correlationId);
            }
            if (user.role !== 'proveedor') {
                return sendProblemDetails(res, 403, 'no-autorizado', 'Acceso Denegado', 'Solo usuarios con rol proveedor pueden dar de alta técnicos en su equipo (RN-TP3, SCRUM-36)', correlationId);
            }

            let body = {};
            try { body = JSON.parse(rawBody || '{}'); } catch {}

            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!body.documentId || !body.fullName || !body.email || !emailRegex.test(body.email) || !body.phone || !body.specialtyId) {
                return sendProblemDetails(res, 400, 'validacion-solicitud', 'Datos de registro de técnico inválidos', 'El documento, nombre completo, correo válido, teléfono y especialidad son campos obligatorios.', correlationId);
            }

            if (registeredDocuments.has(String(body.documentId))) {
                return sendProblemDetails(res, 409, 'documento-registrado', 'El documento ya está registrado', 'El documento de identidad ya se encuentra registrado en el tenant.', correlationId);
            }
            if (registeredEmails.has(body.email)) {
                return sendProblemDetails(res, 409, 'correo-registrado', 'El correo ya está registrado', 'El correo electrónico ya se encuentra registrado en el tenant.', correlationId);
            }

            registeredDocuments.add(String(body.documentId));
            registeredEmails.add(body.email);

            const tecId = `usr-tec-team-${Date.now()}`;
            const newTec = {
                userId: tecId,
                fullName: body.fullName,
                email: body.email,
                documentId: String(body.documentId),
                phone: body.phone,
                specialty: body.specialty || "Plomería",
                specialtyId: body.specialtyId,
                role: "tecnico",
                providerId: user.sub,
                tenantId: user.tenant_id,
                verificationStatus: "pendiente",
                createdAt: new Date().toISOString()
            };

            providerTechniciansDb[user.tenant_id] = providerTechniciansDb[user.tenant_id] || [];
            providerTechniciansDb[user.tenant_id].push(newTec);

            res.writeHead(201, {
                'Content-Type': 'application/json',
                'X-Correlation-Id': correlationId
            });
            return res.end(JSON.stringify({
                userId: tecId,
                fullName: newTec.fullName,
                email: newTec.email,
                role: "tecnico",
                providerId: user.sub,
                tenantId: user.tenant_id,
                verificationStatus: "pendiente",
                noticeEmitted: "technician.registered",
                createdAt: newTec.createdAt
            }));
        }

        // 8.2 Listado de técnicos del equipo del proveedor (GET /api/v1/providers/me/technicians)
        if ((url === '/api/v1/providers/me/technicians' || url === '/v1/providers/me/technicians') && req.method === 'GET') {
            if (!user) {
                return sendProblemDetails(res, 401, 'no-autenticado', 'No autenticado', 'Token ausente en consulta de equipo (IDN-017)', correlationId);
            }
            if (user.role !== 'proveedor') {
                return sendProblemDetails(res, 403, 'no-autorizado', 'Acceso Denegado', 'Solo usuarios con rol proveedor pueden consultar su equipo de técnicos (RN-TP4, SCRUM-36)', correlationId);
            }

            const tenantList = providerTechniciansDb[user.tenant_id] || [];
            let myTechnicians = tenantList.filter(t => t.providerId === user.sub);

            const urlObj = new URL(req.url, 'http://localhost');
            const statusFilter = urlObj.searchParams.get('status');
            if (statusFilter === 'activo') {
                myTechnicians = myTechnicians.filter(t => t.verificationStatus === 'aprobado');
            } else if (statusFilter === 'inactivo') {
                myTechnicians = myTechnicians.filter(t => ['pendiente', 'rechazado', 'suspendido'].includes(t.verificationStatus));
            }

            res.writeHead(200, {
                'Content-Type': 'application/json',
                'X-Correlation-Id': correlationId
            });
            return res.end(JSON.stringify({
                items: myTechnicians.map(t => ({
                    userId: t.userId,
                    fullName: t.fullName,
                    email: t.email,
                    phone: t.phone,
                    specialty: t.specialty,
                    verificationStatus: t.verificationStatus,
                    providerId: t.providerId
                })),
                total: myTechnicians.length
            }));
        }

        // =========================================================================
        // 9. VERIFICACIÓN, APROBACIÓN Y RECHAZO DE TÉCNICOS (Admin - RF-19, SCRUM-39, SCRUM-108)
        // =========================================================================
        // 9.1 Listado de técnicos por estado de verificación (GET /api/v1/admin/technicians)
        if ((url === '/api/v1/admin/technicians' || url === '/v1/admin/technicians') && req.method === 'GET') {
            if (!user) {
                return sendProblemDetails(res, 401, 'no-autenticado', 'No autenticado', 'Token ausente en consulta de verificación (IDN-017)', correlationId);
            }
            if (user.role !== 'admin_tenant' && user.role !== 'admin' && user.role !== 'admin_plataforma') {
                return sendProblemDetails(res, 403, 'no-autorizado', 'Acceso Denegado', 'Solo administradores de tenant pueden consultar técnicos para verificación (RF-19)', correlationId);
            }

            const tenantTechsMap = adminTechniciansDb[user.tenant_id] || {};
            let list = Object.values(tenantTechsMap);

            const urlObj = new URL(req.url, 'http://localhost');
            const statusFilter = urlObj.searchParams.get('verificationStatus');
            if (statusFilter) {
                list = list.filter(t => t.verificationStatus === statusFilter);
            }

            res.writeHead(200, {
                'Content-Type': 'application/json',
                'X-Correlation-Id': correlationId
            });
            return res.end(JSON.stringify({
                items: list,
                total: list.length,
                page: 1,
                pageSize: 20
            }));
        }

        // 9.2 Aprobación de técnico (POST /api/v1/admin/technicians/{userId}/approve)
        if ((url.startsWith('/api/v1/admin/technicians/') || url.startsWith('/v1/admin/technicians/')) && url.endsWith('/approve') && req.method === 'POST') {
            if (!user) {
                return sendProblemDetails(res, 401, 'no-autenticado', 'No autenticado', 'Token ausente (IDN-017)', correlationId);
            }
            if (user.role !== 'admin_tenant' && user.role !== 'admin' && user.role !== 'admin_plataforma') {
                return sendProblemDetails(res, 403, 'no-autorizado', 'Acceso Denegado', 'Solo administradores pueden aprobar perfiles técnicos (RF-19)', correlationId);
            }

            const parts = url.split('/');
            const techUserId = parts[parts.length - 2];
            const tenantTechsMap = adminTechniciansDb[user.tenant_id] || {};
            const tech = tenantTechsMap[techUserId];

            if (!tech) {
                return sendProblemDetails(res, 404, 'no-encontrado', 'Técnico no encontrado', 'El técnico no existe en el tenant especificado (Aislamiento RLS)', correlationId);
            }

            // Transiciones válidas (DD §8.3.13): pendiente -> aprobado, rechazado -> aprobado, suspendido -> aprobado
            if (tech.verificationStatus === 'aprobado') {
                return sendProblemDetails(res, 409, 'transicion-invalida', 'Transición Inválida', 'No se permite aprobar un técnico que ya se encuentra en estado aprobado (DD §8.3.13)', correlationId);
            }

            tech.verificationStatus = 'aprobado';
            tech.verifiedAt = new Date().toISOString();
            tech.verifiedBy = user.sub;

            res.writeHead(200, {
                'Content-Type': 'application/json',
                'X-Correlation-Id': correlationId
            });
            return res.end(JSON.stringify({
                userId: tech.userId,
                fullName: tech.fullName,
                verificationStatus: "aprobado",
                verifiedAt: tech.verifiedAt,
                verifiedBy: tech.verifiedBy,
                noticeEmitted: "technician.verification-changed"
            }));
        }

        // 9.3 Rechazo de técnico con motivo (POST /api/v1/admin/technicians/{userId}/reject)
        if ((url.startsWith('/api/v1/admin/technicians/') || url.startsWith('/v1/admin/technicians/')) && url.endsWith('/reject') && req.method === 'POST') {
            if (!user) {
                return sendProblemDetails(res, 401, 'no-autenticado', 'No autenticado', 'Token ausente (IDN-017)', correlationId);
            }
            if (user.role !== 'admin_tenant' && user.role !== 'admin' && user.role !== 'admin_plataforma') {
                return sendProblemDetails(res, 403, 'no-autorizado', 'Acceso Denegado', 'Solo administradores pueden rechazar perfiles técnicos (RF-19)', correlationId);
            }

            const parts = url.split('/');
            const techUserId = parts[parts.length - 2];
            const tenantTechsMap = adminTechniciansDb[user.tenant_id] || {};
            const tech = tenantTechsMap[techUserId];

            if (!tech) {
                return sendProblemDetails(res, 404, 'no-encontrado', 'Técnico no encontrado', 'El técnico no existe en el tenant especificado (Aislamiento RLS)', correlationId);
            }

            let body = {};
            try { body = JSON.parse(rawBody || '{}'); } catch {}

            if (!body.reason || body.reason.trim().length < 5) {
                return sendProblemDetails(res, 400, 'validacion-solicitud', 'Motivo inválido', 'El motivo de rechazo es obligatorio y debe tener al menos 5 caracteres (DD §8.3.13).', correlationId);
            }

            // Transiciones válidas (DD §8.3.13): solo desde 'pendiente'
            if (tech.verificationStatus !== 'pendiente') {
                return sendProblemDetails(res, 409, 'transicion-invalida', 'Transición Inválida', `No se permite rechazar un técnico en estado ${tech.verificationStatus} (DD §8.3.13)`, correlationId);
            }

            tech.verificationStatus = 'rechazado';
            tech.rejectionReason = body.reason;
            tech.rejectedAt = new Date().toISOString();
            tech.rejectedBy = user.sub;

            res.writeHead(200, {
                'Content-Type': 'application/json',
                'X-Correlation-Id': correlationId
            });
            return res.end(JSON.stringify({
                userId: tech.userId,
                fullName: tech.fullName,
                verificationStatus: "rechazado",
                reason: body.reason,
                rejectedAt: tech.rejectedAt,
                rejectedBy: tech.rejectedBy,
                noticeEmitted: "technician.verification-changed"
            }));
        }

        // 9.4 Suspensión de cuenta de técnico con motivo (POST /api/v1/admin/technicians/{userId}/suspend)
        if ((url.startsWith('/api/v1/admin/technicians/') || url.startsWith('/v1/admin/technicians/')) && url.endsWith('/suspend') && req.method === 'POST') {
            if (!user) {
                return sendProblemDetails(res, 401, 'no-autenticado', 'No autenticado', 'Token ausente (IDN-017)', correlationId);
            }
            if (user.role !== 'admin_tenant' && user.role !== 'admin' && user.role !== 'admin_plataforma') {
                return sendProblemDetails(res, 403, 'no-autorizado', 'Acceso Denegado', 'Solo administradores pueden suspender perfiles técnicos (RF-20)', correlationId);
            }

            const parts = url.split('/');
            const techUserId = parts[parts.length - 2];
            const tenantTechsMap = adminTechniciansDb[user.tenant_id] || {};
            const tech = tenantTechsMap[techUserId];

            if (!tech) {
                return sendProblemDetails(res, 404, 'no-encontrado', 'Técnico no encontrado', 'El técnico no existe en el tenant especificado (Aislamiento RLS)', correlationId);
            }

            let body = {};
            try { body = JSON.parse(rawBody || '{}'); } catch {}

            if (!body.reason || body.reason.trim().length < 5) {
                return sendProblemDetails(res, 400, 'validacion-solicitud', 'Motivo de suspensión inválido', 'El motivo de suspensión es obligatorio y debe tener al menos 5 caracteres (DD §8.3.13).', correlationId);
            }

            // Transiciones válidas (DD §8.3.13): solo desde 'aprobado'
            if (tech.verificationStatus !== 'aprobado') {
                return sendProblemDetails(res, 409, 'transicion-invalida', 'Transición Inválida', `No se permite suspender un técnico en estado ${tech.verificationStatus} (DD §8.3.13)`, correlationId);
            }

            tech.verificationStatus = 'suspendido';
            tech.suspensionReason = body.reason;
            tech.suspendedAt = new Date().toISOString();
            tech.suspendedBy = user.sub;

            res.writeHead(200, {
                'Content-Type': 'application/json',
                'X-Correlation-Id': correlationId
            });
            return res.end(JSON.stringify({
                userId: tech.userId,
                fullName: tech.fullName,
                verificationStatus: "suspendido",
                reason: body.reason,
                suspendedAt: tech.suspendedAt,
                suspendedBy: tech.suspendedBy,
                matchingBlocked: true,
                noticeEmitted: "technician.verification-changed"
            }));
        }

        // 10. Métricas de Matching y Auditoría de Intentos (Matching Service - SCRUM-78 / RN-M9 / RNF-05)
        if ((url.startsWith('/api/v1/matching/attempts/') || url.startsWith('/v1/matching/attempts/')) && req.method === 'GET') {
            if (!user) {
                return sendProblemDetails(res, 401, 'no-autenticado', 'No autenticado', 'Token ausente (IDN-017)', correlationId);
            }
            const reqId = url.split('/').pop();

            // Aislamiento multi-tenant RLS
            if (user.tenant_id !== "11111111-1111-1111-1111-111111111111") {
                return sendProblemDetails(res, 404, 'no-encontrado', 'Intento de matching no encontrado', 'Aislamiento multi-tenant RLS: El intento no existe en el tenant activo.', correlationId);
            }

            const currentReq = serviceRequestsDb[reqId];
            const isEnEspera = reqId.includes('espera') || (currentReq && currentReq.status === 'en_espera');

            res.writeHead(200, { 'Content-Type': 'application/json', 'X-Correlation-Id': correlationId });
            return res.end(JSON.stringify({
                serviceRequestId: reqId,
                tenantId: user.tenant_id,
                attemptCount: isEnEspera ? 0 : 1,
                firstAttemptDurationMs: 340, // Cumple RNF-05 (< 60.000 ms)
                candidateEvaluation: {
                    evaluatedTotal: 5,
                    excludedNotApproved: 2, // Descartados por verificationStatus == 'pendiente'
                    excludedWrongSpecialty: 1, // Descartados por especialidad distinta
                    excludedOutOfCoverage: 1, // Descartados por ubicación fuera de polígono
                    eligibleCandidateAssigned: isEnEspera ? null : "usr-tec-approved-01"
                },
                status: isEnEspera ? "sin_candidatos" : "asignado"
            }));
        }

        // 10.1 Prueba de Idempotencia del Consumidor de Eventos (processed_events - SCRUM-78 / AC5-E5)
        if ((url === '/api/v1/matching/events/simulate-event' || url === '/v1/matching/events/simulate-event') && req.method === 'POST') {
            const eventId = req.headers['x-event-id'] || 'evt-initial-123';
            let body = {};
            try { body = JSON.parse(rawBody || '{}'); } catch {}

            const isDuplicate = body.isDuplicate === true;
            res.writeHead(200, { 'Content-Type': 'application/json', 'X-Correlation-Id': correlationId });
            return res.end(JSON.stringify({
                eventId: eventId,
                eventType: "service-request.created",
                idempotentOutcome: isDuplicate ? "SKIPPED_ALREADY_PROCESSED" : "APPLIED_FIRST_TIME",
                processedEventsTable: "db_matching.processed_events",
                duplicateHandledGracefully: true
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
