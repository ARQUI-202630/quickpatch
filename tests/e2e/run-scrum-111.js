/**
 * Ejecutor de pruebas E2E para SCRUM-111 (HU SCRUM-40): Suspensión de Cuenta de Técnico (Admin)
 * Microservicios validados: Identity Service, Matching Service, Communication Service, API Gateway
 * Autora: Katherine Bravo — QA Lead
 * 
 * Valida:
 * - RF-20: El Administrador suspende la cuenta de un técnico con motivo registrado.
 * - RN-TP2: Un técnico suspendido no puede recibir nuevas solicitudes (matching bloqueado).
 * - Reactivación: Transición de suspendido -> aprobado permitida según DD §8.3.13.
 * - Validación: Motivo obligatorio >= 5 caracteres (400 Bad Request según RFC 9457).
 * - Máquina de estados: Bloqueo de transiciones inválidas (409 Conflict).
 * - Control de Acceso (RBAC): Clientes y técnicos bloqueados de suspender cuentas (403 Forbidden).
 * - Autenticación (IDN-017): Peticiones anónimas bloqueadas (401 Unauthorized).
 * - Aislamiento Multi-Tenant (RLS): Admin Beta no puede suspender técnicos de Alfa (404 Not Found).
 * 
 * Uso:
 *   node tests/e2e/run-scrum-111.js [--remote]
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
const collectionFile = path.join(__dirname, 'scrum-111-suspension-tecnico.postman_collection.json');

function start() {
    console.log(`\n======================================================`);
    console.log(` EJECUTANDO: SCRUM-111 (Suspensión de Cuenta de Técnico)`);
    console.log(` HU Padre: SCRUM-40 | RF-20 | RN-TP2 | DD §8.3.13`);
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
            console.error('\n[Newman] Se encontraron fallos en la ejecución de SCRUM-111.');
        } else {
            console.log('\n[Newman] Ejecución de SCRUM-111 completada al 100% con éxito.');
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
