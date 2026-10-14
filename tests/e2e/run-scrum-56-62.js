/**
 * Ejecutor de pruebas E2E para SCRUM-56 y SCRUM-62 con Newman (QA)
 * 
 * - SCRUM-56: Registro y Perfil de Técnico / Proveedor (Identity).
 * - SCRUM-62: Aislamiento Lógico de Datos por Tenant (Multi-tenant RLS).
 * 
 * Uso:
 *   node tests/e2e/run-scrum-56-62.js [--remote]
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const server = require('./mock-gateway-qa');

const isRemote = process.argv.includes('--remote');
const baseUrl = isRemote ? 'https://qa.quickpatch.internal' : 'http://localhost:8080';
const collectionFile = path.join(__dirname, 'scrum-56-62-registro-y-aislamiento.postman_collection.json');
const evidenciaDir = path.join(__dirname, 'evidencias');
const evidenciaFile = path.join(evidenciaDir, 'scrum-56-62-local-2026-10-14.txt');

function runNewman() {
    console.log(`\n======================================================`);
    console.log(` EJECUTANDO PRUEBAS DE SISTEMA (SCRUM-56 & SCRUM-62)`);
    console.log(` Modo: ${isRemote ? 'Ambiente Real QA (VM2)' : 'Simulación Local Preparatoria'}`);
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
        '--insecure',
        '--reporters', 'cli'
    ];

    const child = spawn(npxCmd, args, { stdio: 'inherit', shell: true });

    child.on('close', (code) => {
        if (!isRemote) {
            server.close(() => {
                console.log('\n[QA Mock Gateway] Servidor local cerrado.');
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
