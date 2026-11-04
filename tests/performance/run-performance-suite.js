/**
 * QUICKPATCH — Validador y Ejecutor Real de Pruebas de Rendimiento k6 (SCRUM-396)
 * Responsable: Katherine Bravo (QA Lead - ka.bravo@javeriana.edu.co)
 * Estándares: ISO/IEC 25010:2023 (Performance Efficiency), SAD V4 (v2.28)
 * 
 * Ejecuta k6 real contra el ambiente de QA desplegado (https://qa.quickpatch.internal)
 * y exporta los resúmenes oficiales en formato JSON y texto plano.
 */

const fs = require('fs');
const path = require('path');
const { execSync, spawnSync } = require('child_process');

const evidenciasDir = path.join(__dirname, 'evidencias');
if (!fs.existsSync(evidenciasDir)) {
    fs.mkdirSync(evidenciasDir, { recursive: true });
}

function checkK6Available() {
    try {
        execSync('k6 version', { stdio: 'ignore' });
        return 'local';
    } catch {
        try {
            execSync('docker --version', { stdio: 'ignore' });
            return 'docker';
        } catch {
            return 'none';
        }
    }
}

function runK6Test(scriptName, summaryFile, textReportFile, title) {
    console.log("================================================================================");
    console.log(`EJECUTANDO: ${title}`);
    console.log("Objetivo: https://qa.quickpatch.internal");
    console.log("================================================================================");

    const scriptPath = path.join(__dirname, scriptName);
    const summaryExportPath = path.join(evidenciasDir, summaryFile);
    const textReportPath = path.join(evidenciasDir, textReportFile);

    const k6Runner = checkK6Available();

    if (k6Runner === 'local') {
        const cmd = `k6 run --insecure-skip-tls-verify --summary-export "${summaryExportPath}" "${scriptPath}"`;
        console.log(`[k6 Runner Local] Ejecutando: ${cmd}`);
        try {
            const output = execSync(cmd, { encoding: 'utf8', stdio: 'pipe' });
            fs.writeFileSync(textReportPath, output, 'utf8');
            console.log(output);
            console.log(`[Éxito] Resumen JSON guardado en: ${summaryExportPath}`);
            console.log(`[Éxito] Evidencia de texto guardada en: ${textReportPath}`);
        } catch (err) {
            console.error(`[Aviso k6] La ejecución finalizó con alertas de umbral o error:`, err.message);
            if (err.stdout) {
                fs.writeFileSync(textReportPath, err.stdout, 'utf8');
                console.log(err.stdout);
            }
        }
    } else if (k6Runner === 'docker') {
        console.log(`[k6 Docker] Ejecutando vía imagen oficial grafana/k6...`);
        const dockerCmd = `docker run --rm -i -v "${__dirname}:/scripts" -v "${evidenciasDir}:/evidencias" grafana/k6 run --insecure-skip-tls-verify --summary-export /evidencias/${summaryFile} /scripts/${scriptName}`;
        console.log(`Comando: ${dockerCmd}`);
        try {
            const output = execSync(dockerCmd, { encoding: 'utf8', stdio: 'pipe' });
            fs.writeFileSync(textReportPath, output, 'utf8');
            console.log(output);
        } catch (err) {
            console.error(`[Aviso Docker k6]:`, err.message);
            if (err.stdout) fs.writeFileSync(textReportPath, err.stdout, 'utf8');
        }
    } else {
        console.log("\n[INSTRUCCIÓN MANUAL PARA QA]");
        console.log("k6 no está instalado en el PATH ni Docker está activo.");
        console.log("Para ejecutar la prueba de rendimiento real contra QA, ejecute:");
        console.log(`\n  k6 run --insecure-skip-tls-verify --summary-export "${summaryExportPath}" "${scriptPath}"\n`);
        console.log("O mediante Docker:");
        console.log(`  docker run --rm -i -v "${__dirname}:/scripts" grafana/k6 run --insecure-skip-tls-verify /scripts/${scriptName}\n`);
    }
}

console.log("Iniciando validación de rendimiento QA...");
runK6Test('load-test-50vu.js', 'k6-load-50vu-summary.json', 'k6-load-50vu-qa-2026-10-18.txt', 'CARGA NORMAL SOSTENIDA 50 VU');
runK6Test('stress-test-150vu.js', 'k6-stress-150vu-summary.json', 'k6-stress-150vu-qa-2026-10-18.txt', 'ESTRÉS PICO 150 VU');
