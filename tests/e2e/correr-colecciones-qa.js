#!/usr/bin/env node
/**
 * Corre colecciones de tests/e2e contra QA y guarda la salida de Newman (reporter cli, sin colores) como evidencia en
 * tests/e2e/evidencias/<coleccion>-qa-<fecha>.txt.
 *
 * Uso (en una terminal propia, nunca pegando las claves en un chat ni en un archivo del repositorio):
 *   PowerShell:  $env:QA_ADMIN_EMAIL = '...'; $env:QA_ADMIN_PASSWORD = '...'
 *   Bash:        export QA_ADMIN_EMAIL=... QA_ADMIN_PASSWORD=...
 *   node tests/e2e/correr-colecciones-qa.js scrum-490-cotizacion scrum-96-evidencia
 *
 * Opcionales: QA_PLATFORM_ADMIN_EMAIL y QA_PLATFORM_ADMIN_PASSWORD (vista de plataforma de SCRUM-105) y QA_BASE_URL
 * (por defecto https://qa.quickpatch.internal). Las claves viajan a Newman como --env-var y no se escriben en la
 * evidencia: el reporter cli no imprime cuerpos ni encabezados. Nunca se usa el reporter JSON, que sí los guarda.
 */
const { spawnSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');

const aqui = __dirname;
const colecciones = process.argv.slice(2);
if (colecciones.length === 0) {
  console.error('Indica al menos una colección, por ejemplo: scrum-490-cotizacion');
  process.exit(2);
}

for (const variable of ['QA_ADMIN_EMAIL', 'QA_ADMIN_PASSWORD']) {
  if (!process.env[variable]) {
    console.error(`Falta ${variable} en el entorno. Defínela en tu terminal; no la escribas en el repositorio.`);
    process.exit(2);
  }
}

const baseUrl = process.env.QA_BASE_URL || 'https://qa.quickpatch.internal';
const fecha = new Date().toISOString().slice(0, 10);
const npx = process.platform === 'win32' ? 'npx.cmd' : 'npx';
const sinColor = (texto) => texto.replace(/\u001b\[[0-9;]*m/g, '');
let fallidas = 0;

for (const nombre of colecciones) {
  const archivo = path.join(aqui, `${nombre.replace(/\.postman_collection\.json$/, '')}.postman_collection.json`);
  if (!fs.existsSync(archivo)) {
    console.error(`No existe ${archivo}`);
    fallidas++;
    continue;
  }

  const args = [
    '--yes', 'newman@6', 'run', archivo,
    '--insecure', '--reporters', 'cli', '--color', 'off',
    '--env-var', `baseUrl=${baseUrl}`,
    '--env-var', `adminEmail=${process.env.QA_ADMIN_EMAIL}`,
    '--env-var', `adminPassword=${process.env.QA_ADMIN_PASSWORD}`,
  ];
  if (process.env.QA_PLATFORM_ADMIN_EMAIL && process.env.QA_PLATFORM_ADMIN_PASSWORD) {
    args.push('--env-var', `platformAdminEmail=${process.env.QA_PLATFORM_ADMIN_EMAIL}`);
    args.push('--env-var', `platformAdminPassword=${process.env.QA_PLATFORM_ADMIN_PASSWORD}`);
  }

  const inicio = new Date();
  console.log(`\n▶ ${nombre} contra ${baseUrl}`);
  const corrida = spawnSync(npx, args, { encoding: 'utf8', shell: process.platform === 'win32', maxBuffer: 64 * 1024 * 1024 });
  let salida = sinColor(`${corrida.stdout || ''}${corrida.stderr || ''}`);
  for (const secreto of [process.env.QA_ADMIN_PASSWORD, process.env.QA_PLATFORM_ADMIN_PASSWORD].filter(Boolean)) {
    salida = salida.split(secreto).join('***');
  }

  const evidencia = path.join(aqui, 'evidencias', `${nombre}-qa-${fecha}.txt`);
  const encabezado = [
    `${nombre} contra QA, ${fecha}`,
    `Colección: tests/e2e/${path.basename(archivo)} (newman 6, reporter cli). Ambiente: ${baseUrl}.`,
    `Inicio: ${inicio.toISOString()}. Duración: ${Math.round((Date.now() - inicio.getTime()) / 1000)} s. Código de salida: ${corrida.status}.`,
    'Cuentas de prueba nuevas con clave aleatoria; las claves y los tokens no se guardan en esta evidencia.',
    '',
  ].join('\n');
  fs.writeFileSync(evidencia, `${encabezado}\n${salida}`, 'utf8');
  console.log(`${corrida.status === 0 ? 'OK' : 'CON FALLOS'}  ${path.relative(process.cwd(), evidencia)}`);
  if (corrida.status !== 0) fallidas++;
}

process.exit(fallidas === 0 ? 0 : 1);
