import { test, expect } from '@playwright/test';

/**
 * Suite E2E de Interfaz Web Administrativa (SCRUM-318)
 * 
 * Valida los flujos de usuario, componentes de Angular y reglas de negocio
 * basados en la implementación real de apps/web:
 *  - Rutas reales: /iniciar-sesion, /inicio, /tenants (app.routes.ts)
 *  - Guards y control RBAC: redirigirPorRol y requiereRol (core/guards.ts)
 *  - Formulario de login: InicioSesion (#email, #password, 'Ingresar')
 *  - Gestión de tenants: TenantsApi (/v1/platform/tenants) y componente Tenants
 * 
 * Casos evaluados:
 *  - W-01: Autenticación de Administradores (Plataforma a /tenants, Tenant a /inicio)
 *  - W-02: Manejo de errores de inicio de sesión (401 credenciales y 423 bloqueo RN-U4)
 *  - W-03: Control de acceso RBAC por guards (admin_tenant a /tenants redirige a /inicio)
 *  - W-04: Listado de empresas/tenants (tabla, columnas, estado, indicador de carga)
 *  - W-05: Confirmación de cambio de estado de tenant (RN-T1 / PATCH /v1/platform/tenants/:id)
 *  - W-06: Manejo visual de errores en mutación (409 Conflict optimista en <p class="error">)
 *  - W-07: Redirección inicial según rol en la raíz (redirigirPorRol)
 */

test.describe('Web Admin — Autenticación y Login (W-01 & W-02)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/iniciar-sesion');
  });

  test('[W-01] Renderizado correcto del formulario de login en /iniciar-sesion', async ({ page }) => {
    await expect(page.locator('#email, input[formControlName="email"]')).toBeVisible();
    await expect(page.locator('#password, input[formControlName="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toContainText(/Ingresar|Ingresando/i);
    // En la vista administrativa no debe existir selector de tenant visible
    await expect(page.locator('select[name="tenantId"], [data-testid="tenant-selector"]')).toHaveCount(0);
  });

  test('[W-01] Login exitoso de Administrador de Plataforma navega a /tenants', async ({ page }) => {
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

    await page.fill('#email', 'platform-admin@quickpatch.internal');
    await page.fill('#password', 'PasswordPlataforma123*');
    await page.click('button[type="submit"]');

    // El componente navega a /tenants para admin_plataforma
    await expect(page).toHaveURL(/.*\/tenants/);
  });

  test('[W-01] Login exitoso de Administrador de Tenant navega a /inicio', async ({ page }) => {
    await page.route('**/api/v1/auth/login', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          accessToken: 'mock-tenant-jwt-token',
          tokenType: 'Bearer',
          user: {
            id: 'usr-tenant-01',
            email: 'tenant-admin@bogota.test',
            role: 'admin_tenant',
            name: 'Admin Empresa'
          }
        })
      });
    });

    await page.fill('#email', 'tenant-admin@bogota.test');
    await page.fill('#password', 'PasswordTenant123*');
    await page.click('button[type="submit"]');

    // El componente navega a /inicio para admin_tenant
    await expect(page).toHaveURL(/.*\/inicio/);
  });

  test('[W-02] Credenciales inválidas muestran mensaje de error (401)', async ({ page }) => {
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

    await page.fill('#email', 'admin@quickpatch.internal');
    await page.fill('#password', 'PasswordInvalidoTotal999*');
    await page.click('button[type="submit"]');

    const alertError = page.locator('p.error[role="alert"], .alert-danger, [role="alert"]');
    await expect(alertError).toBeVisible();
    await expect(alertError).toContainText(/incorrect|inválid|no autenticado|error/i);
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

    await page.fill('#email', 'bloqueado@quickpatch.internal');
    await page.fill('#password', 'CualquierPassword123*');
    await page.click('button[type="submit"]');

    const alertLocked = page.locator('p.error[role="alert"], [role="alert"]');
    await expect(alertLocked).toBeVisible();
    await expect(alertLocked).toContainText(/bloqueada|temporalmente|intentos/i);
  });
});

test.describe('Web Admin — Guards de Navegación y RBAC (W-03 & W-07)', () => {
  test('[W-03] Usuario sin autenticar intentando entrar a /tenants es redirigido a /iniciar-sesion', async ({ page }) => {
    // Sin sesión en localStorage
    await page.goto('/tenants');
    // El guard requiereRol('admin_plataforma') redirige al inicio de sesión
    await expect(page).toHaveURL(/.*\/iniciar-sesion/);
  });

  test('[W-03] Rol admin_tenant al intentar entrar a /tenants es redirigido a /inicio por guard', async ({ page }) => {
    // Simular sesión iniciada con rol admin_tenant
    await page.addInitScript(() => {
      localStorage.setItem('auth_token', 'mock-tenant-admin-token');
      localStorage.setItem('user_role', 'admin_tenant');
    });

    await page.goto('/tenants');

    // Conforme a core/guards.ts: si no tiene el rol admin_plataforma, redirige a /inicio
    // NO existe pantalla de acceso denegado ni .access-denied
    await expect(page).toHaveURL(/.*\/inicio/);
    await expect(page.locator('table caption:has-text("Empresas oferentes")')).toHaveCount(0);
  });

  test('[W-07] Redirección inicial en la raíz (/) según el rol autenticado', async ({ page }) => {
    // Con rol admin_plataforma, redirigirPorRol lleva a /tenants
    await page.addInitScript(() => {
      localStorage.setItem('auth_token', 'mock-platform-admin-token');
      localStorage.setItem('user_role', 'admin_plataforma');
    });

    await page.goto('/');
    await expect(page).toHaveURL(/.*\/tenants/);
  });
});

test.describe('Web Admin — Gestión de Tenants (W-04, W-05 & W-06)', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('auth_token', 'mock-platform-admin-token');
      localStorage.setItem('user_role', 'admin_plataforma');
    });
  });

  test('[W-04] Vista /tenants muestra tabla de empresas con columnas oficiales y badges de estado', async ({ page }) => {
    // Interceptar la llamada a /v1/platform/tenants que hace TenantsApi
    await page.route('**/platform/tenants*', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 'tenant-bogota-001',
            name: 'Servicios Técnicos Bogotá S.A.S.',
            nit: '900.543.210-1',
            status: 'activo',
            createdAt: '2026-01-10T08:00:00Z'
          },
          {
            id: 'tenant-andina-002',
            name: 'Soluciones Andina Express Ltda.',
            nit: '901.876.543-2',
            status: 'inactivo',
            createdAt: '2026-02-14T11:30:00Z'
          }
        ])
      });
    });

    await page.goto('/tenants');

    // Estructura real de app-tenants
    const table = page.locator('table');
    await expect(table).toBeVisible();
    await expect(page.locator('caption')).toContainText(/Empresas oferentes de la plataforma/i);

    // Encabezados de tabla
    await expect(table.locator('th:has-text("Nombre")')).toBeVisible();
    await expect(table.locator('th:has-text("NIT")')).toBeVisible();
    await expect(table.locator('th:has-text("Estado")')).toBeVisible();
    await expect(table.locator('th:has-text("Creado")')).toBeVisible();

    // Badges de estado en el DOM real
    await expect(page.locator('span.estado:has-text("Activo")')).toBeVisible();
    await expect(page.locator('span.estado.inactivo:has-text("Inactivo")')).toBeVisible();
  });

  test('[W-05] Confirmación inline para cambiar estado de tenant (RN-T1 / PATCH /v1/platform/tenants/:id)', async ({ page }) => {
    await page.route('**/platform/tenants*', async route => {
      if (route.request().method() === 'GET') {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            {
              id: 'tenant-bogota-001',
              name: 'Servicios Técnicos Bogotá S.A.S.',
              nit: '900.543.210-1',
              status: 'activo',
              createdAt: '2026-01-10T08:00:00Z'
            }
          ])
        });
      }
      if (route.request().method() === 'PATCH') {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'tenant-bogota-001',
            name: 'Servicios Técnicos Bogotá S.A.S.',
            nit: '900.543.210-1',
            status: 'inactivo',
            createdAt: '2026-01-10T08:00:00Z'
          })
        });
      }
    });

    await page.goto('/tenants');

    // Botón inicial de acción en la tabla: 'Desactivar'
    const btnPedirCambio = page.locator('button:has-text("Desactivar")').first();
    await expect(btnPedirCambio).toBeVisible();
    await btnPedirCambio.click();

    // Confirmación inline según features/tenants/tenants.ts:
    // <span class="confirmacion">¿Desactivar {name}? <button>Confirmar</button> <button class="secundario">Cancelar</button></span>
    const confirmacion = page.locator('.confirmacion');
    await expect(confirmacion).toBeVisible();
    await expect(confirmacion).toContainText(/¿Desactivar Servicios Técnicos Bogotá/i);

    // Botones de confirmar y cancelar
    const btnConfirmar = confirmacion.locator('button:has-text("Confirmar")');
    const btnCancelar = confirmacion.locator('button:has-text("Cancelar")');
    await expect(btnConfirmar).toBeVisible();
    await expect(btnCancelar).toBeVisible();

    // Al confirmar, envía el PATCH y actualiza la lista
    await btnConfirmar.click();
    await expect(page.locator('span.estado.inactivo:has-text("Inactivo")')).toBeVisible();
  });

  test('[W-06] Manejo visual de error en mutación de tenant (409 Conflict)', async ({ page }) => {
    await page.route('**/platform/tenants*', async route => {
      if (route.request().method() === 'GET') {
        return route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            {
              id: 'tenant-bogota-001',
              name: 'Servicios Técnicos Bogotá S.A.S.',
              nit: '900.543.210-1',
              status: 'activo',
              createdAt: '2026-01-10T08:00:00Z'
            }
          ])
        });
      }
      if (route.request().method() === 'PATCH') {
        return route.fulfill({
          status: 409,
          contentType: 'application/problem+json',
          body: JSON.stringify({
            type: 'https://quickpatch.internal/problems/conflicto-concurrencia',
            title: 'Conflicto de Concurrencia Optimista',
            status: 409,
            detail: 'El registro fue modificado por otra sesión. Por favor refresque la página.',
            correlationId: 'cid-test-409'
          })
        });
      }
    });

    await page.goto('/tenants');

    await page.click('button:has-text("Desactivar")');
    await page.click('.confirmacion button:has-text("Confirmar")');

    // El componente captura el error y renderiza: <p class="error" role="alert">{{ error() }}</p>
    const errorAlert = page.locator('p.error[role="alert"]');
    await expect(errorAlert).toBeVisible();
    await expect(errorAlert).toContainText(/conflicto|modificado|error/i);
  });
});
