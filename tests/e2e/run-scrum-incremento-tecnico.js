/**
 * Ejecutor de pruebas E2E para el incremento del técnico (SCRUM-81, SCRUM-90, SCRUM-93)
 * Autor: Katherine Bravo — QA
 * 
 * - SCRUM-90: Disponibilidad y Cobertura Geográfica (Matching Service / HU SCRUM-33)
 * - SCRUM-81: Aceptación y Rechazo de Ofertas (Matching Service / HU SCRUM-30)
 * - SCRUM-93: Detalle de Solicitud para Técnico Asignado (ServiceRequest Service / HU SCRUM-34)
 * 
 * Uso:
 *   node tests/e2e/run-scrum-incremento-tecnico.js [--remote]
 */

const { spawn } = require('child_process');
const path = require('path');
const server = require('./mock-gateway-qa');

const isRemote = process.argv.includes('--remote');
const baseUrl = isRemote ? 'https://qa.quickpatch.internal' : 'http://localhost:8080';
const collectionFile = path.join(__dirname, 'scrum-incremento-tecnico.postman_collection.json');

const npxCmd = process.platform === 'win32' ? 'npx.cmd' : 'npx';

function runCollection(file, title, callback) {
    console.log(`\n======================================================`);
    console.log(` EJECUTANDO: ${title}`);
    console.log(` Modo: ${isRemote ? 'Ambiente Real QA (VM2)' : 'Simulación Preparatoria Local'}`);
    console.log(` Target: ${baseUrl}`);
    console.log(` Archivo: ${path.basename(file)}`);
    console.log(`======================================================\n`);

    const args = [
        '--yes',
        'newman',
        'run',
        file,
        '--env-var', `baseUrl=${baseUrl}`,
        '--env-var', `tecnicoEmail=tecnico@quickpatch.test`,
        '--env-var', `tecnicoOcupadoEmail=tecnico.ocupado@quickpatch.test`,
        '--env-var', `tecnicoOtroEmail=tecnico.otro@quickpatch.test`,
        '--env-var', `clienteEmail=cliente@quickpatch.test`,
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
    runCollection(collectionFile, 'INCREMENTO TÉCNICO (SCRUM-81, SCRUM-90, SCRUM-93)', (code) => {
        finish(code);
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
