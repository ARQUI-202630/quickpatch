/**
 * Ejecutor de pruebas E2E para SCRUM-56 (y simulación SCRUM-62) con Newman (QA)
 * 
 * - SCRUM-56: Colección E2E contra QA real (scrum-56-registro-tecnico.postman_collection.json)
 * - SCRUM-62: Suite de simulación RLS (*.simulacion.json, no ejecutada en CI de QA)
 * 
 * Uso:
 *   node tests/e2e/run-scrum-56-62.js [--remote]
 */

const { spawn } = require('child_process');
const path = require('path');
const server = require('./mock-gateway-qa');

const isRemote = process.argv.includes('--remote');
const baseUrl = isRemote ? 'https://qa.quickpatch.internal' : 'http://localhost:8080';
const scrum56Collection = path.join(__dirname, 'scrum-56-registro-tecnico.postman_collection.json');
const scrum62Simulation = path.join(__dirname, 'scrum-62-aislamiento-tenant.simulacion.json');

const npxCmd = process.platform === 'win32' ? 'npx.cmd' : 'npx';

function runCollection(file, title, callback) {
    console.log(`\n======================================================`);
    console.log(` EJECUTANDO: ${title}`);
    console.log(` Modo: ${isRemote ? 'Ambiente Real QA (VM2)' : 'Simulación Local Preparatoria'}`);
    console.log(` Target: ${baseUrl}`);
    console.log(` Archivo: ${path.basename(file)}`);
    console.log(`======================================================\n`);

    const args = [
        '--yes',
        'newman',
        'run',
        file,
        '--env-var', `baseUrl=${baseUrl}`,
        '--env-var', `adminEmail=admin@quickpatch.test`,
        '--env-var', `adminPassword=PasswordAdmin123*`,
        '--insecure',
        '--reporters', 'cli'
    ];

    const child = spawn(npxCmd, args, { stdio: 'inherit', shell: true });

    child.on('close', (code) => {
        if (code !== 0) {
            console.error(`\n[Newman] Error en la ejecución de ${title} (código ${code})`);
        }
        if (callback) callback(code);
    });
}

function start() {
    // 1. Ejecutar SCRUM-56 (Colección oficial para QA)
    runCollection(scrum56Collection, 'SCRUM-56 (Registro y Perfil de Técnico)', (code56) => {
        if (code56 !== 0 || isRemote) {
            // En QA remoto no corremos la simulación monotenant
            finish(code56);
            return;
        }

        // 2. En local, ejecutar también la simulación de aislamiento SCRUM-62
        runCollection(scrum62Simulation, 'SCRUM-62 (Simulación de Aislamiento RLS)', (code62) => {
            finish(code62);
        });
    });
}

function finish(code) {
    if (!isRemote) {
        server.close(() => {
            console.log('\n[QA Mock Gateway] Servidor local cerrado.');
            process.exit(code);
        });
    } else {
        process.exit(code);
    }
}

if (!isRemote) {
    server.listen(8080, () => {
        console.log('[QA Mock Gateway] Inicializado en http://localhost:8080');
        start();
    });
} else {
    start();
}
