/**
 * Ejecutor de pruebas E2E para SCRUM-99 (HU SCRUM-36): Gestión de Equipo de Técnicos (Proveedor)
 * Microservicios validados: Identity Service, Communication Service, API Gateway
 * Autora: Katherine Bravo — QA Lead
 * 
 * Valida:
 * - RF-16: El Proveedor registra y administra su equipo de técnicos.
 * - RN-TP3: El técnico dado de alta hereda el tenant del proveedor, rol "tecnico", y queda en "pendiente" hasta aprobación de admin_tenant.
 * - RN-TP4: Un proveedor solo puede consultar y administrar los técnicos asociados a su propio usuario (provider_id = user.id).
 * - Filtros por estado: ?status=activo vs ?status=inactivo (DD §8.3.14).
 * - Unicidad (RN-U1): Rechazo por cédula o correo duplicado (409 Conflict).
 * - Validación: Rechazo por campos obligatorios faltantes (400 Bad Request).
 * - Control de Acceso (RBAC): Bloqueo a clientes y técnicos (403 Forbidden).
 * - Autenticación (IDN-017): Bloqueo a peticiones anónimas (401 Unauthorized).
 * - Aislamiento Intra-Tenant: Proveedor 2 no visualiza técnicos de Proveedor 1.
 * - Aislamiento Multi-Tenant (RLS): Proveedor de Tenant Beta no visualiza técnicos de Tenant Alfa.
 * 
 * Uso:
 *   node tests/e2e/run-scrum-99.js [--remote]
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
const collectionFile = path.join(__dirname, 'scrum-99-equipo-proveedor.postman_collection.json');

function start() {
    console.log(`\n======================================================`);
    console.log(` EJECUTANDO: SCRUM-99 (Gestión de Equipo de Técnicos)`);
    console.log(` HU Padre: SCRUM-36 | RF-16 | RN-TP3 | RN-TP4`);
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
            console.error('\n[Newman] Se encontraron fallos en la ejecución de SCRUM-99.');
        } else {
            console.log('\n[Newman] Ejecución de SCRUM-99 completada al 100% con éxito.');
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
