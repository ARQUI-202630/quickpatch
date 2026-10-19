/**
 * Ejecutor de pruebas E2E para SCRUM-78 (HU SCRUM-29): Motor de Matching y Asignación Automática
 * Microservicios validados: Matching Service, ServiceRequest, API Gateway
 * Autora: Katherine Bravo — QA Lead
 * 
 * Valida:
 * - RF-09: Asignación automática de técnico basada en cercanía, especialidad y disponibilidad.
 * - RF-10: Ofertas secuenciales a candidatos elegibles.
 * - RN-M9: Exclusión de técnicos no aprobados, ocupados o fuera de polígono de cobertura.
 * - RN-M10: Transición a estado en_espera ante ausencia de candidatos y reintento.
 * - RNF-05: Tiempo de primer intento de asignación < 60 segundos (SLA de emparejamiento).
 * - AC5-E5: Consumo idempotente de eventos de Kafka registrado en db_matching.processed_events.
 * - SAD AC6-E2: Aislamiento multi-tenant estricto vía Row-Level Security en PostgreSQL.
 * 
 * Uso:
 *   node tests/e2e/run-scrum-78.js [--remote]
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
const collectionFile = path.join(__dirname, 'scrum-78-motor-matching.postman_collection.json');

function start() {
    console.log(`\n======================================================`);
    console.log(` EJECUTANDO: SCRUM-78 (Motor de Matching y Asignación)`);
    console.log(` HU Padre: SCRUM-29 | RF-09 | RF-10 | RN-M9 | RN-M10`);
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
            console.error('\n[Newman] Se encontraron fallos en la ejecución de SCRUM-78.');
        } else {
            console.log('\n[Newman] Ejecución de SCRUM-78 completada al 100% con éxito.');
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
