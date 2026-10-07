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
const collectionFile = path.join(__dirname, 'scrum-318-web-admin.postman_collection.json');

function runNewman() {
  console.log(`\n======================================================`);
  console.log(` EJECUTANDO PRUEBAS E2E WEB ADMINISTRATIVO (SCRUM-318)`);
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
    '--env-var', `adminEmail=admin@quickpatch.internal`,
    '--env-var', `adminPassword=PasswordAdmin123*`,
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
