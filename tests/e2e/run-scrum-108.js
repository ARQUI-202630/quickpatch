/**
 * Ejecutor de pruebas E2E para SCRUM-108 (HU SCRUM-39): Aprobación/Rechazo de Técnicos y Proveedores (Admin)
 * Microservicios validados: Identity Service, Communication Service, API Gateway
 * Autora: Katherine Bravo — QA Lead
 * 
 * Valida:
 * - RF-19: El Administrador del Tenant aprueba o rechaza solicitudes de técnicos y proveedores.
 * - RN-TP1: Solo técnicos aprobados pueden participar en matching.
 * - Transición de estado: pendiente -> aprobado con emisión de evento technician.verification-changed.
 * - Rechazo con motivo obligatorio >= 5 caracteres (DD §8.3.13) y RFC 9457 (400 Bad Request si es inválido).
 * - Máquina de estados: bloqueo de transiciones inválidas (409 Conflict ante intento de aprobar o rechazar técnico ya aprobado).
 * - Control de Acceso (RBAC): Bloqueo a clientes y técnicos intentando aprobar (403 Forbidden).
 * - Autenticación (IDN-017): Peticiones anónimas bloqueadas (401 Unauthorized).
 * - Aislamiento Multi-Tenant (RLS): Admin Beta no puede ver ni aprobar técnicos de Tenant Alfa (404 Not Found).
 * 
 * Uso:
 *   node tests/e2e/run-scrum-108.js [--remote]
 */

const path = require('path');
const server = require('./mock-gateway-qa');

let newman;
try {
    newman = require('C:/Users/kathe/AppData/Local/npm-cache/_npx/75b90f33e80c3d7c/node_modules/newman');
} catch {
    newman = require('newman');
}

const isRemote = process.argv.includes('--remote');
const baseUrl = isRemote ? 'https://qa.quickpatch.internal' : 'http://localhost:8080';
const collectionFile = path.join(__dirname, 'scrum-108-aprobacion-rechazo.postman_collection.json');

function start() {
    console.log(`\n======================================================`);
    console.log(` EJECUTANDO: SCRUM-108 (Aprobación/Rechazo de Técnicos)`);
    console.log(` HU Padre: SCRUM-39 | RF-19 | RN-TP1 | DD §8.3.13`);
    console.log(` Modo: ${isRemote ? 'Ambiente Real QA (VM2)' : 'Simulación Preparatoria Local'}`);
    console.log(` Target: ${baseUrl}`);
    console.log(` Archivo: ${path.basename(collectionFile)}`);
    console.log(`======================================================\n`);

    newman.run({
        collection: require(collectionFile),
        environment: {
            values: [
                { key: 'baseUrl', value: baseUrl }
            ]
        },
        reporters: ['cli'],
        insecure: true
    }, (err, summary) => {
        let code = 0;
        if (err || (summary && summary.run && summary.run.failures && summary.run.failures.length > 0)) {
            code = 1;
            console.error('\n[Newman] Se encontraron fallos en la ejecución de SCRUM-108.');
        } else {
            console.log('\n[Newman] Ejecución de SCRUM-108 completada al 100% con éxito.');
        }

        if (!isRemote) {
            server.close(() => {
                console.log('[QA Mock Gateway] Servidor local cerrado.');
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
        start();
    });
} else {
    start();
}
