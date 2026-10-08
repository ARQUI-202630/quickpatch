/**
 * Servidor Mock del API Gateway para Pruebas E2E del Web Administrativo (SCRUM-318)
 * 
 * Emula los endpoints administrativos de Identity y Plataforma consumidos
 * por la interfaz web de Angular (mockups W-01 a W-07), aplicando RFC 9457 Problem Details
 * y control de acceso basado en roles (RBAC).
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

// Estado en memoria de tenants para las pruebas
let tenantsDB = [
  {
    id: "tenant-bogota-001",
    name: "Servicios Técnicos Bogotá S.A.S.",
    nit: "900.543.210-1",
    status: "activo",
    createdAt: "2026-01-10T08:00:00Z",
    version: 1
  },
  {
    id: "tenant-andina-002",
    name: "Soluciones Andina Express Ltda.",
    nit: "901.876.543-2",
    status: "activo",
    createdAt: "2026-02-14T11:30:00Z",
    version: 1
  },
  {
    id: "tenant-occidente-003",
    name: "Mantenimiento Integral Occidente",
    nit: "890.123.456-7",
    status: "inactivo",
    createdAt: "2025-11-20T14:15:00Z",
    version: 2
  }
];

const server = http.createServer((req, res) => {
  const correlationId = req.headers['x-correlation-id'] || `cid-${Date.now()}`;
  const user = parseJwt(req.headers['authorization']);

  let rawBody = '';
  req.on('data', chunk => { rawBody += chunk; });
  req.on('end', () => {
    const parsedUrl = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
    const pathname = parsedUrl.pathname;

    // 1. Login Administrativo (W-01, W-02, RN-U4, RN-T1)
    if (pathname === '/api/v1/auth/login' && req.method === 'POST') {
      let body = {};
      try { body = JSON.parse(rawBody || '{}'); } catch {}

      // W-02: Cuenta bloqueada tras intentos fallidos (RN-U4)
      if (body.email === 'bloqueado@quickpatch.internal' || (body.email && body.email.includes('bloqueado'))) {
        return sendProblemDetails(
          res, 423, 'cuenta-bloqueada', 'Cuenta Bloqueada Temporalmente',
          'La cuenta ha sido bloqueada temporalmente por exceso de intentos fallidos (RN-U4). Intente más tarde.',
          correlationId
        );
      }

      // W-05 / RN-T1: Login rechazado para usuario perteneciente a un tenant desactivado
      if (body.email === 'usuario@tenant-desactivado.test' || (body.email && body.email.includes('desactivado'))) {
        return sendProblemDetails(
          res, 403, 'tenant-inactivo', 'Acceso Denegado - Empresa Desactivada',
          'El acceso se encuentra inactivo porque la empresa/tenant ha sido suspendida (RN-T1).',
          correlationId
        );
      }

      // W-02: Credenciales incorrectas
      if (body.password === 'PasswordInvalidoTotal999*' || (body.password && body.password.includes('Invalido'))) {
        return sendProblemDetails(
          res, 401, 'no-autenticado', 'Credenciales Inválidas',
          'El correo electrónico o la contraseña ingresada son incorrectos.',
          correlationId
        );
      }

      // W-01: Administrador de Plataforma
      if (body.email === 'platform-admin@quickpatch.internal' || (body.email && body.email.includes('platform-admin'))) {
        const token = makeToken("usr-plat-01", "admin_plataforma");
        res.writeHead(200, { 'Content-Type': 'application/json', 'X-Correlation-Id': correlationId });
        return res.end(JSON.stringify({
          accessToken: token,
          tokenType: "Bearer",
          user: {
            id: "usr-plat-01",
            email: body.email,
            name: "Administrador de Plataforma",
            role: "admin_plataforma"
          }
        }));
      }

      // W-01 / W-07: Administrador de Tenant
      const token = makeToken("usr-adm-tenant-01", "admin_tenant", "tenant-bogota-001");
      res.writeHead(200, { 'Content-Type': 'application/json', 'X-Correlation-Id': correlationId });
      return res.end(JSON.stringify({
        accessToken: token,
        tokenType: "Bearer",
        user: {
          id: "usr-adm-tenant-01",
          email: body.email || "admin@tenant-bogota.test",
          name: "Administrador de Tenant",
          role: "admin_tenant",
          tenantId: "tenant-bogota-001"
        }
      }));
    }

    // 2. Consulta y Listado de Tenants (W-03, W-04: /api/v1/platform/tenants)
    if ((pathname === '/api/v1/platform/tenants' || pathname === '/v1/platform/tenants' || pathname === '/api/v1/admin/tenants') && req.method === 'GET') {
      // W-03: Petición anónima
      if (!user) {
        return sendProblemDetails(
          res, 401, 'no-autenticado', 'No Autenticado',
          'Se requiere un token de autenticación válido para acceder a la gestión de empresas (IDN-017).',
          correlationId
        );
      }

      // W-03: admin_tenant u otro rol no autorizado
      if (user.role !== 'admin_plataforma') {
        return sendProblemDetails(
          res, 403, 'no-autorizado', 'Acceso Denegado',
          'Solo el administrador de plataforma tiene permisos para gestionar empresas (SCRUM-64, W-03).',
          correlationId
        );
      }

      // W-04: Filtro por status
      const statusFilter = parsedUrl.searchParams.get('status');
      let result = tenantsDB;
      if (statusFilter) {
        result = tenantsDB.filter(t => t.status.toLowerCase() === statusFilter.toLowerCase());
      }

      res.writeHead(200, { 'Content-Type': 'application/json', 'X-Correlation-Id': correlationId });
      return res.end(JSON.stringify(result));
    }

    // 3. Modificación de Estado de Tenant (W-05, W-06: PATCH /api/v1/platform/tenants/:id)
    const matchStatus = pathname.match(/^\/(?:api\/)?v1\/(?:platform|admin)\/tenants\/([^/]+)(?:\/status)?$/);
    if (matchStatus && req.method === 'PATCH') {
      const tenantId = matchStatus[1];

      // Verificación de autenticación y rol
      if (!user) {
        return sendProblemDetails(res, 401, 'no-autenticado', 'No Autenticado', 'Token requerido.', correlationId);
      }
      if (user.role !== 'admin_plataforma') {
        return sendProblemDetails(res, 403, 'no-autorizado', 'Acceso Denegado', 'Permiso denegado.', correlationId);
      }

      let body = {};
      try { body = JSON.parse(rawBody || '{}'); } catch {}

      // W-06: Manejo de conflicto de concurrencia (409 Conflict si la versión es obsoleta)
      if (body.version !== undefined && body.version === 0) {
        return sendProblemDetails(
          res, 409, 'conflicto-concurrencia', 'Conflicto de Concurrencia Optimista',
          'El registro de la empresa fue modificado por otra sesión concurrente. Por favor refresque la vista.',
          correlationId
        );
      }

      const tenant = tenantsDB.find(t => t.id === tenantId) || tenantsDB[0];
      tenant.status = body.status || "inactivo";
      tenant.version = (tenant.version || 1) + 1;

      res.writeHead(200, { 'Content-Type': 'application/json', 'X-Correlation-Id': correlationId });
      return res.end(JSON.stringify({
        id: tenant.id,
        name: tenant.name,
        nit: tenant.nit,
        status: tenant.status,
        version: tenant.version,
        updatedAt: new Date().toISOString()
      }));
    }

    res.writeHead(404, { 'Content-Type': 'application/json', 'X-Correlation-Id': correlationId });
    res.end(JSON.stringify({ error: "Ruta no encontrada" }));
  });
});

if (require.main === module) {
  server.listen(PORT, () => {
    console.log(`[QA Mock Admin Gateway] Escuchando en http://localhost:${PORT}`);
  });
}

module.exports = server;
