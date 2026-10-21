/**
 * Ejecutor local de pruebas E2E para el Web Administrativo (SCRUM-318)
 * 
 * Permite ejecutar la colección Postman con Newman contra el mock local o contra QA:
 *   node tests/e2e/run-web-admin-e2e.js [--remote]
 */

const { spawn } = require('child_process');
const path = require('path');
const server = require('./mock-admin-gateway');

const isRemote = process.argv.includes('--remote');
const baseUrl = isRemote ? 'https://qa.quickpatch.internal' : 'http://localhost:8080';
const collectionFile = path.join(__dirname, 'scrum-318-web-admin.simulacion.json');

/**
 * Credenciales de QA: solo desde variables de entorno (las mismas que los secretos QA_* del CI). Nunca se escriben
 * en el repositorio. En la simulación local el mock acepta cualquier contraseña, así que se usa un valor de prueba.
 */
function credencial(nombre, valorLocal) {
  if (!isRemote) return valorLocal;
  const valor = process.env[nombre];
  if (!valor) {
    console.error(`Falta la variable de entorno ${nombre}. Las credenciales de QA no se guardan en el repositorio.`);
    process.exit(2);
  }
  return valor;
}

function runNewman() {
  console.log(`\n======================================================`);
  console.log(` EJECUTANDO PRUEBAS E2E WEB ADMINISTRATIVO (SCRUM-318)`);
  console.log(` Modo: ${isRemote ? 'Ejecución Remota contra QA (VM2)' : 'Simulación Local Preparatoria'}`);
  console.log(` Target: ${baseUrl}`);
  console.log(` Colección: ${path.basename(collectionFile)}`);
  console.log(`======================================================\n`);

  const npxCmd = process.platform === 'win32' ? 'npx.cmd' : 'npx';
  const args = [
    '--yes',
    'newman',
    'run',
    collectionFile,
    '--env-var', `baseUrl=${baseUrl}`,
    '--env-var', `adminEmail=${credencial('QA_ADMIN_EMAIL', 'admin@quickpatch.internal')}`,
    '--env-var', `adminPassword=${credencial('QA_ADMIN_PASSWORD', 'simulacion-local')}`,
    '--env-var', `platformAdminEmail=${credencial('QA_PLATFORM_ADMIN_EMAIL', 'platform-admin@quickpatch.internal')}`,
    '--env-var', `platformAdminPassword=${credencial('QA_PLATFORM_ADMIN_PASSWORD', 'simulacion-local')}`,
    '--insecure',
    '--reporters', 'cli'
  ];

  const child = spawn(npxCmd, args, { stdio: 'inherit', shell: true });

  child.on('close', (code) => {
    if (!isRemote) {
      server.close(() => {
        console.log('\n[QA Mock Gateway] Servidor cerrado.');
        process.exit(code);
      });
    } else {
      process.exit(code);
    }
  });
}

if (!isRemote) {
  server.listen(8080, () => {
    console.log('[QA Mock Gateway] Inicializado en http://localhost:8080');
    runNewman();
  });
} else {
  runNewman();
}
