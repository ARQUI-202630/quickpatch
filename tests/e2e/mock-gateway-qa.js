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

        // 2. Login de usuarios (Identity)
        if (url === '/api/v1/auth/login' && req.method === 'POST') {
            let body = {};
            try { body = JSON.parse(rawBody || '{}'); } catch {}

            // Caso de Tenant Inactivo (RN-T1, IDN-019)
            if (body.email && body.email.includes('inactivo')) {
                return sendProblemDetails(res, 403, 'no-autorizado', 'Tenant Desactivado', 'El tenant se encuentra suspendido/desactivado (RN-T1).', correlationId);
            }

            // Administrador de tenant
            if (body.email && body.email.includes('admin')) {
                const token = makeToken("usr-admin-01", "admin_tenant");
                res.writeHead(200, { 'Content-Type': 'application/json', 'X-Correlation-Id': correlationId });
                return res.end(JSON.stringify({
                    accessToken: token,
                    tokenType: "Bearer",
                    user: { id: "usr-admin-01", email: body.email, role: "admin_tenant" }
                }));
            }

            // Cliente
            const token = makeToken("usr-client-01", "cliente");
            res.writeHead(200, { 'Content-Type': 'application/json', 'X-Correlation-Id': correlationId });
            return res.end(JSON.stringify({
                accessToken: token,
                tokenType: "Bearer",
                user: { id: "usr-client-01", email: body.email, role: "cliente" }
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
                active: true
            }));
        }

        // 4. Creación de solicitudes de servicio (ServiceRequest - solo rol cliente)
        if (url === '/api/v1/service-requests') {
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
                createdAt: new Date().toISOString()
            }));
        }

        res.writeHead(404, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: "Ruta no encontrada" }));
    });
});

if (require.main === module) {
    server.listen(PORT, () => {
        console.log(`[QA Mock Gateway] Escuchando en http://localhost:${PORT}`);
    });
}

module.exports = server;
