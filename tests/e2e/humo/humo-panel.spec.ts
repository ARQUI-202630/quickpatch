import { APIRequestContext, expect, request, test } from '@playwright/test';

/**
 * Prueba de humo del panel web contra QA (SCRUM-448): el panel publicado en VM1 y los servicios reales, sin rutas
 * simuladas. Necesita las cuentas iniciales de QA (secretos QA_ADMIN_* y QA_PLATFORM_ADMIN_* del repositorio); sin
 * ellas los casos se omiten. Cada caso guarda una captura en resultados/ para el informe (SCRUM-449).
 */
const admin = { email: process.env.QA_ADMIN_EMAIL ?? '', clave: process.env.QA_ADMIN_PASSWORD ?? '' };
const plataforma = {
  email: process.env.QA_PLATFORM_ADMIN_EMAIL ?? '',
  clave: process.env.QA_PLATFORM_ADMIN_PASSWORD ?? '',
};

async function api(): Promise<APIRequestContext> {
  return request.newContext({
    baseURL: `${process.env.BASE_URL ?? 'https://qa.quickpatch.internal'}/api/`,
    ignoreHTTPSErrors: true,
    extraHTTPHeaders: { 'X-Channel-Id': 'quickpatch-mobile' },
  });
}

/** Cliente nuevo de la corrida (clave aleatoria que no se guarda) con una solicitud en curso. */
async function clienteConSolicitud(): Promise<{ email: string; clave: string; solicitud: string; corto: string }> {
  const ctx = await api();
  const sufijo = Date.now().toString(36);
  const email = `humo448.panel.${sufijo}@quickpatch.test`;
  const clave = `Qp${Math.random().toString(36).slice(2, 12)}7Z`;
  expect((await ctx.post('v1/auth/register/client', { data: { email, password: clave, fullName: 'Humo panel 448' } })).status()).toBe(201);
  const token = (await (await ctx.post('v1/auth/login', { data: { email, password: clave } })).json()).accessToken as string;
  const auth = { Authorization: `Bearer ${token}` };
  // El panel muestra al cliente por los últimos 8 caracteres de su id (SCRUM-104).
  const corto = ((await (await ctx.get('v1/users/me', { headers: auth })).json()).id as string).slice(-8);
  const categorias = await (await ctx.get('v1/catalog/categories', { headers: auth })).json();
  const creada = await ctx.post('v1/service-requests', {
    headers: auth,
    data: {
      categoryId: categorias[0].id,
      description: 'Prueba de humo del panel contra QA (SCRUM-448)',
      location: { latitude: 4.6486, longitude: -74.063 },
      addressText: 'Calle 63 # 9-45, Bogotá',
    },
  });
  expect(creada.status()).toBe(201);
  const solicitud = (await creada.json()).id as string;
  await ctx.dispose();
  return { email, clave, solicitud, corto };
}

async function iniciarSesion(page: import('@playwright/test').Page, email: string, clave: string) {
  await page.goto('/iniciar-sesion');
  await page.locator('#email').fill(email);
  await page.locator('#password').fill(clave);
  await page.getByRole('button', { name: 'Ingresar' }).click();
}

test.describe('Panel web en QA (SCRUM-448)', () => {
  test('el administrador de la plataforma inicia sesión y ve los tenants', async ({ page }, info) => {
    test.skip(!plataforma.email, 'Sin QA_PLATFORM_ADMIN_EMAIL');
    const inicio = Date.now();
    await iniciarSesion(page, plataforma.email, plataforma.clave);
    await expect(page).toHaveURL(/\/tenants$/);
    await expect(page.getByRole('heading', { name: 'Tenants' })).toBeVisible();
    await expect(page.locator('tbody tr').first()).toBeVisible();
    info.annotations.push({ type: 'tiempo', description: `${Date.now() - inicio} ms` });
    await page.screenshot({ path: 'resultados/1-tenants-plataforma.png', fullPage: true });
  });

  test('el administrador del tenant ve las solicitudes y cancela una desde el panel', async ({ page }, info) => {
    test.skip(!admin.email, 'Sin QA_ADMIN_EMAIL');
    const { solicitud, corto } = await clienteConSolicitud();
    const inicio = Date.now();
    await iniciarSesion(page, admin.email, admin.clave);
    await expect(page).toHaveURL(/\/inicio$/);
    await page.goto('/solicitudes');
    await expect(page.getByRole('heading', { name: 'Solicitudes' })).toBeVisible();
    await expect(page.getByText('Creadas hoy')).toBeVisible();
    await expect(page.locator('tbody tr').first()).toBeVisible();
    await page.screenshot({ path: 'resultados/2-solicitudes-tenant.png', fullPage: true });

    // La fila del cliente de la corrida, por su ID corto en el nombre accesible del botón.
    const boton = page.getByRole('button', { name: new RegExp(`del cliente ${corto}$`) });
    const fila = page.locator('tbody tr', { has: boton });
    await boton.click();
    await page.locator('#motivo-cancelacion').fill('Prueba de humo del panel (SCRUM-448).');
    await page.screenshot({ path: 'resultados/3-dialogo-cancelacion.png' });
    await page.getByRole('button', { name: 'Sí, cancelar' }).click();
    await expect(page.locator('dialog[open]')).toHaveCount(0);
    await expect(fila.locator('[data-etiqueta="Estado"]')).toHaveText(/Cancelado/);
    info.annotations.push({ type: 'tiempo', description: `${Date.now() - inicio} ms` });
    info.annotations.push({ type: 'solicitud', description: solicitud });
    await page.screenshot({ path: 'resultados/4-solicitud-cancelada.png', fullPage: true });
  });

  test('un cliente no entra al panel', async ({ page }) => {
    const { email, clave } = await clienteConSolicitud();
    await iniciarSesion(page, email, clave);
    await expect(page.getByRole('alert')).toContainText('app móvil');
    await expect(page).toHaveURL(/\/iniciar-sesion$/);
  });
});
