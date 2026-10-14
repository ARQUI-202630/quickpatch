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
            if (!body.documentId || !body.password || body.password.length < 8) {
                return sendProblemDetails(res, 400, 'validacion-solicitud', 'Datos de registro inválidos', 'El documento y una contraseña de al menos 8 caracteres son obligatorios.', correlationId);
            }
            if (body.documentId && String(body.documentId).includes('repetido')) {
                return sendProblemDetails(res, 409, 'documento-registrado', 'El documento ya está registrado', 'El documento ya se encuentra asociado a un perfil técnico.', correlationId);
            }
            if (body.email && body.email.includes('repetido')) {
                return sendProblemDetails(res, 409, 'correo-registrado', 'El correo ya está registrado', 'El correo ya está en uso en el tenant.', correlationId);
            }

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

            // Detección de tenant (Tenant Alfa por defecto, Tenant Beta si se especifica)
            const tenantId = (body.email && body.email.includes('beta'))
                ? "22222222-2222-2222-2222-222222222222"
                : "11111111-1111-1111-1111-111111111111";

            // Técnico (SCRUM-56)
            if (body.email && body.email.includes('tecnico')) {
                const token = makeToken("usr-tec-01", "tecnico", tenantId);
                res.writeHead(200, { 'Content-Type': 'application/json', 'X-Correlation-Id': correlationId });
                return res.end(JSON.stringify({
                    accessToken: token,
                    tokenType: "Bearer",
                    expiresIn: 7200,
                    user: { id: "usr-tec-01", email: body.email, role: "tecnico", verificationStatus: "pendiente" }
                }));
            }

            // Administrador de tenant
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

        // 4.1 Consulta de solicitud por ID con aislamiento multi-tenant (ServiceRequest - SCRUM-62 / RLS)
        if (url.startsWith('/api/v1/service-requests/') && req.method === 'GET') {
            if (!user) {
                return sendProblemDetails(res, 401, 'no-autenticado', 'No autenticado', 'Token ausente (IDN-017)', correlationId);
            }
            const reqId = url.split('/').pop();
            // Solicitud sr-qa-001 pertenece a Tenant Alfa ("11111111-1111-1111-1111-111111111111")
            // Si el usuario es de Tenant Beta ("22222222-2222-2222-2222-222222222222"), RLS oculta la fila -> 404 Not Found
            if (user.tenant_id !== "11111111-1111-1111-1111-111111111111") {
                return sendProblemDetails(res, 404, 'no-encontrado', 'Solicitud no encontrada', 'La solicitud no existe en el tenant especificado (RLS Isolation)', correlationId);
            }
            res.writeHead(200, { 'Content-Type': 'application/json', 'X-Correlation-Id': correlationId });
            return res.end(JSON.stringify({
                id: reqId,
                status: "buscando_tecnico",
                categoryId: "3f1c2a4e-8d7b-4c1a-9e2f-5b6a7c8d9e01",
                tenantId: user.tenant_id
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
