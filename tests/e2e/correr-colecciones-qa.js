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

/**
 * Un solo login del administrador antes de correr nada. Cada colección hace su propio login, e Identity bloquea la
 * cuenta 15 minutos al quinto intento fallido (RN-U4): con una clave equivocada, varias colecciones seguidas la
 * bloquearían. Devuelve el código HTTP y el rol, nunca el token.
 */
function verificarAdministrador() {
  const https = require('node:https');
  const http = require('node:http');
  const url = new URL('/api/v1/auth/login', baseUrl);
  const cuerpo = JSON.stringify({ email: process.env.QA_ADMIN_EMAIL, password: process.env.QA_ADMIN_PASSWORD });
  const cliente = url.protocol === 'https:' ? https : http;
  return new Promise((resolve) => {
    const peticion = cliente.request(url, {
      method: 'POST',
      rejectUnauthorized: false,
      timeout: 15000,
      headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(cuerpo) },
    }, (respuesta) => {
      let datos = '';
      respuesta.on('data', (trozo) => { datos += trozo; });
      respuesta.on('end', () => {
        let rol = null;
        try { rol = JSON.parse(datos).user?.role ?? null; } catch { /* Problem Details o cuerpo vacío */ }
        resolve({ estado: respuesta.statusCode, rol });
      });
    });
    peticion.on('timeout', () => peticion.destroy(new Error('sin respuesta en 15 s')));
    peticion.on('error', (e) => resolve({ estado: null, rol: null, error: e.message }));
    peticion.end(cuerpo);
  });
}

async function principal() {
  const { estado, rol, error } = await verificarAdministrador();
  if (estado !== 200 || rol !== 'admin_tenant') {
    const motivo = error ? `error de red (${error})`
      : estado === 401 ? '401: el correo o la clave no son los del administrador del tenant de QA'
      : estado === 423 || estado === 429 ? `${estado}: la cuenta está bloqueada; espera 15 minutos`
      : estado === 200 ? `200, pero el rol es ${rol} y no admin_tenant`
      : `HTTP ${estado}`;
    console.error(`No se corrió ninguna colección. Login del administrador: ${motivo}.`);
    console.error('Identity bloquea la cuenta 15 minutos al quinto intento fallido seguido; revisa las credenciales antes de reintentar.');
    process.exit(2);
  }
  console.log('Login del administrador del tenant: OK');
  correr();
}

function correr() {
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
    // Las fotos de fixtures/ se resuelven desde aquí, como en pruebas-sistema.yml (/etc/newman = tests/e2e).
    '--working-dir', aqui,
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
  const corrida = spawnSync(npx, args, { cwd: aqui, encoding: 'utf8', shell: process.platform === 'win32', maxBuffer: 64 * 1024 * 1024 });
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
  const tablaMatch = salida.match(/┌─+[\s\S]*?└─+/);
  if (tablaMatch) {
    console.log(tablaMatch[0]);
  }
  if (corrida.status !== 0) fallidas++;
}

process.exit(fallidas === 0 ? 0 : 1);
}

principal();
