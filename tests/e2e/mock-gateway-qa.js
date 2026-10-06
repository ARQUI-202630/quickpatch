/**
 * Servidor Mock del API Gateway para Pruebas Locales E2E (QA)
 * 
 * Permite validar las suites de Newman localmente sin dependencias externas,
 * emulando el comportamiento de seguridad del API Gateway y los microservicios
 * definidos en los contratos OpenAPI y las reglas de negocio (RF-05, RF-21, RN-T1).
 */

const http = require('http');

const PORT = process.env.PORT || 8080;

function parseJwt(authHeader) {
    if (!authHeader || !authHeader.startsWith('Bearer ')) return null;
    const token = authHeader.substring(7);
    const parts = token.split('.');
    if (parts.length !== 3) return null;
    try {
        const payloadBase64 = parts[1].replace(/-/g, '+').replace(/_/g, '/');
        const json = Buffer.from(payloadBase64, 'base64').toString('utf8');
        return JSON.parse(json);
    } catch {
        return null;
    }
}

function sendProblemDetails(res, status, title, detail, correlationId) {
    const body = {
        type: `https://quickpatch.internal/problems/${status === 403 ? 'acceso-denegado' : 'no-autorizado'}`,
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

const server = http.createServer((req, res) => {
    const correlationId = req.headers['x-correlation-id'] || `cid-${Date.now()}`;
    const user = parseJwt(req.headers['authorization']);

    let bodyData = '';
    req.on('data', chunk => { bodyData += chunk; });
    req.on('end', () => {
        const url = req.url.split('?')[0];

        // 1. Endpoint administrativo de tenants (solo rol admin)
        if (url === '/v1/admin/tenants') {
            if (!user) {
                return sendProblemDetails(res, 401, 'No autenticado', 'Token ausente o inválido', correlationId);
            }
            if (user.role !== 'admin') {
                return sendProblemDetails(res, 403, 'Acceso Restringido', 'Operación exclusiva del rol admin (RF-05, SCRUM-65)', correlationId);
            }
            res.writeHead(req.method === 'POST' ? 201 : 200, {
                'Content-Type': 'application/json',
                'X-Correlation-Id': correlationId
            });
            return res.end(JSON.stringify({ status: 'ok', data: [] }));
        }

        // 2. Endpoint de catálogo de servicios (mutación solo por admin)
        if (url === '/v1/catalog/categories') {
            if (req.method === 'POST') {
                if (!user) {
                    return sendProblemDetails(res, 401, 'No autenticado', 'Token ausente', correlationId);
                }
                if (user.role !== 'admin') {
                    return sendProblemDetails(res, 403, 'Acceso Restringido', 'Solo administradores pueden crear categorías (CAT-010, SCRUM-65)', correlationId);
                }
                res.writeHead(201, { 'Content-Type': 'application/json', 'X-Correlation-Id': correlationId });
                return res.end(JSON.stringify({ id: 'cat-001', name: 'Nueva Categoria' }));
            }
            res.writeHead(200, { 'Content-Type': 'application/json' });
            return res.end(JSON.stringify([]));
        }

        // 3. Endpoint de solicitudes de servicio
        if (url === '/v1/service-requests') {
            if (!user) {
                return sendProblemDetails(res, 401, 'No autenticado', 'Falta token Bearer en la petición (IDN-017)', correlationId);
            }
            // Validación de tenant desactivado (SCRUM-114, RN-T1)
            if (user.tenant_status === 'inactivo' || user.tenant_id === 'd9d9d9d9-0000-1111-2222-333333333333') {
                return sendProblemDetails(res, 403, 'Tenant Inactivo', 'El tenant se encuentra suspendido/desactivado. No se permiten nuevas solicitudes (RN-T1, SCRUM-114).', correlationId);
            }
            // Validación de rol cliente (SCRUM-65, IDN-012)
            if (user.role !== 'cliente') {
                return sendProblemDetails(res, 403, 'Rol No Autorizado', 'Solo usuarios con rol cliente pueden solicitar servicios (RF-07, IDN-012)', correlationId);
            }
            res.writeHead(201, {
                'Content-Type': 'application/json',
                'X-Correlation-Id': correlationId,
                'Location': '/v1/service-requests/sr-001'
            });
            return res.end(JSON.stringify({
                id: 'sr-001',
                status: 'buscando_tecnico',
                createdAt: new Date().toISOString()
            }));
        }

        // 4. Endpoint de login / autenticación
        if (url === '/v1/auth/login') {
            try {
                const parsed = JSON.parse(bodyData || '{}');
                if (parsed.tenantId === 'd9d9d9d9-0000-1111-2222-333333333333') {
                    return sendProblemDetails(res, 403, 'Tenant Desactivado', 'Tenant is disabled. No se puede iniciar sesión en un tenant inactivo (RN-T1, IDN-019).', correlationId);
                }
            } catch {}
            res.writeHead(200, { 'Content-Type': 'application/json', 'X-Correlation-Id': correlationId });
            return res.end(JSON.stringify({ token: 'mock-jwt-token' }));
        }

        // Fallback
        res.writeHead(404, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Endpoint no encontrado' }));
    });
});

if (require.main === module) {
    server.listen(PORT, () => {
        console.log(`[QA Mock Gateway] Escuchando en http://localhost:${PORT}`);
    });
}

module.exports = server;
