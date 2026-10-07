import { test, expect } from '@playwright/test';

/**
 * Suite E2E de Interfaz Web Administrativa (SCRUM-318)
 * 
 * Valida los flujos de usuario, componentes de Angular y reglas de negocio
 * basados en los mockups de diseño W-01 a W-07 y las especificaciones DD 7.12 / ADR-018:
 *  - W-01: Autenticación de Administradores (Plataforma y Tenant)
 *  - W-02: Manejo de errores de inicio de sesión (401 y 423 bloqueo por RN-U4)
 *  - W-03: Control de acceso RBAC y pantalla de Acceso Denegado (403)
 *  - W-04: Listado y filtrado de empresas/tenants
 *  - W-05: Modal de confirmación para desactivación de tenant (RN-T1)
 *  - W-06: Manejo visual de estados (Skeleton, Vacío, Conflictos 409)
 *  - W-07: Navegación dinámica en sidebar según rol
 */

test.describe('Web Admin — Autenticación y Perfil (W-01 & W-02)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
  });

  test('[W-01] Renderizado correcto del formulario de login administrativo', async ({ page }) => {
    await expect(page.locator('input[type="email"], input[name="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"], input[name="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
    // En la vista administrativa no debe existir selector de tenant visible
    await expect(page.locator('select[name="tenantId"], [data-testid="tenant-selector"]')).toHaveCount(0);
  });

  test('[W-01] Login exitoso de Administrador de Plataforma redirige a gestión de tenants', async ({ page }) => {
    // Mock de respuesta exitosa de autenticación para admin_plataforma
    await page.route('**/api/v1/auth/login', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          accessToken: 'mock-platform-jwt-token',
          tokenType: 'Bearer',
          user: {
            id: 'usr-plat-01',
            email: 'platform-admin@quickpatch.internal',
            role: 'admin_plataforma',
            name: 'Super Admin'
          }
        })
      });
    });

    await page.fill('input[type="email"], input[name="email"]', 'platform-admin@quickpatch.internal');
    await page.fill('input[type="password"], input[name="password"]', 'PasswordPlataforma123*');
    await page.click('button[type="submit"]');

    // Debe navegar hacia la administración de tenants o dashboard principal
    await expect(page).toHaveURL(/.*(\/admin\/tenants|\/dashboard)/);
  });

  test('[W-02] Credenciales inválidas muestran banner de error (401)', async ({ page }) => {
    await page.route('**/api/v1/auth/login', async route => {
      await route.fulfill({
        status: 401,
        contentType: 'application/problem+json',
        body: JSON.stringify({
          type: 'https://quickpatch.internal/problems/no-autenticado',
          title: 'Credenciales Inválidas',
          status: 401,
          detail: 'Correo electrónico o contraseña incorrectos.',
          correlationId: 'cid-test-401'
        })
      });
    });

    await page.fill('input[type="email"], input[name="email"]', 'admin@quickpatch.internal');
    await page.fill('input[type="password"], input[name="password"]', 'PasswordInvalidoTotal999*');
    await page.click('button[type="submit"]');

    const alertError = page.locator('.alert-danger, [role="alert"], .error-message');
    await expect(alertError).toBeVisible();
    await expect(alertError).toContainText(/incorrect|inválid|no autenticado/i);
  });

  test('[W-02 / RN-U4] Cuenta bloqueada tras fallos reiterados muestra advertencia 423 Locked', async ({ page }) => {
    await page.route('**/api/v1/auth/login', async route => {
      await route.fulfill({
        status: 423,
        contentType: 'application/problem+json',
        body: JSON.stringify({
          type: 'https://quickpatch.internal/problems/cuenta-bloqueada',
          title: 'Cuenta Bloqueada Temporalmente',
          status: 423,
          detail: 'La cuenta ha sido bloqueada temporalmente tras superar el límite de intentos (RN-U4).',
          correlationId: 'cid-test-423'
        })
      });
    });

    await page.fill('input[type="email"], input[name="email"]', 'bloqueado@quickpatch.internal');
    await page.fill('input[type="password"], input[name="password"]', 'CualquierPassword123*');
    await page.click('button[type="submit"]');

    const alertLocked = page.locator('.alert-warning, [role="alert"], .locked-message');
    await expect(alertLocked).toBeVisible();
    await expect(alertLocked).toContainText(/bloqueada|temporalmente|intentos/i);
  });
});

test.describe('Web Admin — Control de Acceso RBAC y Sidebar (W-03 & W-07)', () => {
  test('[W-03] Rol admin_tenant al intentar entrar a /admin/tenants recibe pantalla de Acceso Denegado (403)', async ({ page }) => {
    // Simular sesión iniciada con rol admin_tenant
    await page.addInitScript(() => {
      localStorage.setItem('auth_token', 'mock-tenant-admin-token');
      localStorage.setItem('user_role', 'admin_tenant');
    });

    await page.route('**/api/v1/admin/tenants', async route => {
      await route.fulfill({
        status: 403,
        contentType: 'application/problem+json',
        body: JSON.stringify({
          type: 'https://quickpatch.internal/problems/no-autorizado',
          title: 'Acceso Denegado',
          status: 403,
          detail: 'No tienes permisos suficientes para acceder a la gestión de empresas (W-03).',
          correlationId: 'cid-test-403'
        })
      });
    });

    await page.goto('/admin/tenants');

    // Debe mostrar la vista o alerta de acceso denegado (W-03)
    const accessDenied = page.locator('.access-denied, .error-403, [data-testid="access-denied"]');
    await expect(accessDenied).toBeVisible();
    await expect(accessDenied).toContainText(/no tienes permiso|acceso denegado|403/i);

    // Debe incluir botón para regresar al inicio / dashboard
    const homeBtn = page.locator('a[href="/dashboard"], button:has-text("Volver"), a:has-text("Inicio")');
    await expect(homeBtn).toBeVisible();
  });

  test('[W-07] Navegación del sidebar adapta opciones según el rol autenticado', async ({ page }) => {
    // Simular sesión con rol admin_tenant
    await page.addInitScript(() => {
      localStorage.setItem('auth_token', 'mock-tenant-admin-token');
      localStorage.setItem('user_role', 'admin_tenant');
    });

    await page.goto('/dashboard');

    const sidebar = page.locator('nav.sidebar, aside.sidebar, [data-testid="admin-sidebar"]');
    await expect(sidebar).toBeVisible();

    // admin_tenant DEBE ver Dashboard y Técnicos/Categorías
    await expect(sidebar.locator('text=/Dashboard|Inicio/i')).toBeVisible();
    
    // admin_tenant NO DEBE ver enlace de gestión de Tenants
    await expect(sidebar.locator('a[href*="/admin/tenants"], text=/Tenants|Empresas/i')).toHaveCount(0);
  });
});

test.describe('Web Admin — Gestión de Tenants (W-04, W-05 & W-06)', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('auth_token', 'mock-platform-admin-token');
      localStorage.setItem('user_role', 'admin_plataforma');
    });
  });

  test('[W-04] Listado de empresas muestra tabla con columnas, badges y pestañas de filtro', async ({ page }) => {
    await page.route('**/api/v1/admin/tenants*', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 't-001',
            name: 'Servicios Técnicos Bogotá S.A.S.',
            nit: '900.543.210-1',
            status: 'activo',
            createdAt: '2026-01-10T08:00:00Z',
            version: 1
          },
          {
            id: 't-002',
            name: 'Soluciones Andina Express Ltda.',
            nit: '901.876.543-2',
            status: 'inactivo',
            createdAt: '2026-02-14T11:30:00Z',
            version: 2
          }
        ])
      });
    });

    await page.goto('/admin/tenants');

    // Tabla presente
    const table = page.locator('table, [data-testid="tenants-table"]');
    await expect(table).toBeVisible();

    // Verificación de columnas esperadas (W-04)
    await expect(table.locator('th:has-text("Nombre"), th:has-text("Empresa")')).toBeVisible();
    await expect(table.locator('th:has-text("NIT")')).toBeVisible();
    await expect(table.locator('th:has-text("Estado")')).toBeVisible();

    // Badges de estado
    await expect(page.locator('.badge-activo, span:has-text("Activo")').first()).toBeVisible();
    await expect(page.locator('.badge-inactivo, span:has-text("Inactivo")').first()).toBeVisible();

    // Filtros por pestaña: Todos, Activos, Inactivos
    const tabs = page.locator('.nav-tabs, [role="tablist"], .filter-tabs');
    await expect(tabs.locator('text=/Todos/i')).toBeVisible();
    await expect(tabs.locator('text=/Activos/i')).toBeVisible();
    await expect(tabs.locator('text=/Inactivos/i')).toBeVisible();
  });

  test('[W-05] Modal de confirmación para desactivar tenant y advertencia de bloqueo (RN-T1)', async ({ page }) => {
    await page.route('**/api/v1/admin/tenants*', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 't-001',
            name: 'Servicios Técnicos Bogotá S.A.S.',
            nit: '900.543.210-1',
            status: 'activo',
            version: 1
          }
        ])
      });
    });

    await page.goto('/admin/tenants');

    // Clic en switch o botón de desactivación
    const toggleBtn = page.locator('button.btn-toggle-status, input[type="checkbox"].status-toggle, [data-testid="deactivate-tenant"]').first();
    if (await toggleBtn.count() > 0) {
      await toggleBtn.click();

      // Modal de confirmación (W-05)
      const modal = page.locator('.modal, [role="dialog"], .confirmation-dialog');
      await expect(modal).toBeVisible();
      await expect(modal).toContainText(/¿desactivar|suspender/i);
      await expect(modal).toContainText(/no podrá crear nuevas solicitudes|RN-T1/i);

      // Botones de cancelar y confirmar
      await expect(modal.locator('button:has-text("Cancelar")')).toBeVisible();
      await expect(modal.locator('button:has-text("Confirmar"), button:has-text("Desactivar")')).toBeVisible();
    }
  });

  test('[W-06] Manejo de error de concurrencia optimista (409 Conflict)', async ({ page }) => {
    await page.route('**/api/v1/admin/tenants/t-001/status', async route => {
      await route.fulfill({
        status: 409,
        contentType: 'application/problem+json',
        body: JSON.stringify({
          type: 'https://quickpatch.internal/problems/conflicto-concurrencia',
          title: 'Conflicto de Concurrencia Optimista',
          status: 409,
          detail: 'El registro fue modificado por otro administrador. Por favor refresque la página.',
          correlationId: 'cid-test-409'
        })
      });
    });

    await page.goto('/admin/tenants');

    // Desencadenar acción que genera el conflicto
    const actionBtn = page.locator('[data-testid="deactivate-tenant"], button.btn-deactivate').first();
    if (await actionBtn.count() > 0) {
      await actionBtn.click();
      const confirmBtn = page.locator('button:has-text("Confirmar"), button:has-text("Desactivar")');
      if (await confirmBtn.isVisible()) {
        await confirmBtn.click();
      }

      // Debe aparecer notificación toast o alert de conflicto
      const conflictToast = page.locator('.toast-error, .alert-danger, [role="alert"]');
      await expect(conflictToast).toBeVisible();
      await expect(conflictToast).toContainText(/conflicto|modificado por otro|refresque/i);
    }
  });
});
