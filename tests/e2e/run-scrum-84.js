/**
 * Ejecutor de pruebas E2E para SCRUM-84 (HU SCRUM-31): Seguimiento de Estado en Tiempo Real
 * Componentes validados: ServiceRequest, Communication, API Gateway
 * Autora: Katherine Bravo — QA Lead
 * 
 * Valida:
 * - Ciclo de 4 estados: buscando_tecnico -> asignado -> en_progreso -> completado
 * - Reflejo de estado en menos de 1 minuto tras la actualización del técnico (< 60s)
 * - Visibilidad de técnico asignado (nombre, especialidad) para el cliente
 * - Canal en tiempo real WebSocket (/api/v1/realtime) bajo ADR-023 y SCRUM-451
 * - Emisión del evento service-request.status-changed (SCRUM-466)
 * - Confidencialidad intra-tenant (Cliente 2 no ve orden de Cliente 1) y multi-tenant RLS (Tenant Beta no ve Alfa)
 * - Bloqueo de transiciones inválidas (409 Conflict) y control RBAC (403 Forbidden)
 * 
 * Uso:
 *   node tests/e2e/run-scrum-84.js [--remote]
 */

const path = require('path');
const server = require('./mock-gateway-qa');

let newman;
try {
    newman = require('newman');
} catch {
    const { execSync } = require('child_process');
    try {
        const globalDir = execSync('npm root -g', { encoding: 'utf8' }).trim();
        newman = require(path.join(globalDir, 'newman'));
    } catch {
        console.error('Error: newman no está instalado. Ejecute "npm install -g newman"');
        process.exit(1);
    }
}

const isRemote = process.argv.includes('--remote');
const baseUrl = isRemote ? 'https://qa.quickpatch.internal' : 'http://localhost:8080';
const collectionFile = path.join(__dirname, 'scrum-84-seguimiento-estado.postman_collection.json');

function start() {
    console.log(`\n======================================================`);
    console.log(` EJECUTANDO: SCRUM-84 (Seguimiento de Estado en Tiempo Real)`);
    console.log(` HU Padre: SCRUM-31 | ADR-023 | SCRUM-451 | SCRUM-466`);
    console.log(` Modo: ${isRemote ? 'Ambiente Real QA (VM2)' : 'Simulación Preparatoria Local'}`);
    console.log(` Target: ${baseUrl}`);
    console.log(` Archivo: ${path.basename(collectionFile)}`);
    console.log(`======================================================\n`);

    newman.run({
        collection: require(collectionFile),
        environment: {
            values: [
                { key: 'baseUrl', value: baseUrl },
                { key: 'clienteEmail', value: 'cliente@quickpatch.test' },
                { key: 'tecnicoEmail', value: 'tecnico@quickpatch.test' },
                { key: 'cliente2Email', value: 'cliente2@quickpatch.test' },
                { key: 'clienteBetaEmail', value: 'cliente.beta@quickpatch.test' }
            ]
        },
        reporters: ['cli'],
        insecure: true
    }, (err, summary) => {
        let code = 0;
        if (err || (summary && summary.run && summary.run.failures && summary.run.failures.length > 0)) {
            code = 1;
            console.error('\n[Newman] Se encontraron fallos en la ejecución de SCRUM-84.');
        } else {
            console.log('\n[Newman] Ejecución de SCRUM-84 completada al 100% con éxito.');
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
