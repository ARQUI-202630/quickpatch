import { defineConfig, devices } from '@playwright/test';

/**
 * Prueba de humo del panel web contra QA (SCRUM-448). Aparte de ../specs (suite simulada de SCRUM-318), para que solo
 * corra cuando se pide: workflow «Humo de los frontends en QA» o `npx playwright test` en esta carpeta.
 */
export default defineConfig({
  testDir: '.',
  timeout: 60_000,
  expect: { timeout: 15_000 },
  workers: 1,
  reporter: [['list'], ['json', { outputFile: 'resultados/resultado.json' }]],
  use: {
    baseURL: process.env.BASE_URL || 'https://qa.quickpatch.internal',
    ignoreHTTPSErrors: true,
    locale: 'es-CO',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  outputDir: 'resultados/artefactos',
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
});
