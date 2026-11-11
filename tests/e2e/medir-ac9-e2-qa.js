#!/usr/bin/env node
/**
 * Medición de AC9-E2 en QA (SCRUM-642): técnicos con calificaciones bajas señalados en el panel, sin suspensión automática.
 *
 * Condición (SAD 3.9): promedio menor a 3,0 con al menos 5 servicios calificados.
 * Compara, para el tenant del administrador:
 *   A = técnicos del listado completo (GET /v1/admin/technicians) que cumplen la condición según averageRating y ratingCount;
 *   B = técnicos que devuelve el filtro del panel (GET /v1/admin/technicians?lowReputation=true), los que el panel señala.
 * Cumple si A = B (100 % señalados, ninguno de más) y ninguno de A quedó suspendido sin una acción del admin.
 *
 * Uso (claves solo en el entorno de tu terminal, nunca en el repositorio):
 *   export QA_ADMIN_EMAIL=... QA_ADMIN_PASSWORD=...
 *   node tests/e2e/medir-ac9-e2-qa.js > tests/e2e/evidencias/ac9-e2-reputacion-baja-qa-<fecha>.txt
 * La salida no lleva token, correos ni nombres: solo identificadores de técnico truncados y cifras.
 */
const https = require('node:https');

const baseUrl = process.env.QA_BASE_URL || 'https://qa.quickpatch.internal';
for (const variable of ['QA_ADMIN_EMAIL', 'QA_ADMIN_PASSWORD']) {
  if (!process.env[variable]) {
    console.error(`Falta ${variable} en el entorno.`);
    process.exit(2);
  }
}

function pedir(metodo, ruta, { token, cuerpo } = {}) {
  const url = new URL(ruta, baseUrl);
  const datos = cuerpo ? JSON.stringify(cuerpo) : undefined;
  return new Promise((resolve, reject) => {
    const peticion = https.request(url, {
      method: metodo,
      rejectUnauthorized: false,
      timeout: 20000,
      headers: {
        Accept: 'application/json',
        ...(datos ? { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(datos) } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    }, (respuesta) => {
      let texto = '';
      respuesta.on('data', (c) => { texto += c; });
      respuesta.on('end', () => resolve({ estado: respuesta.statusCode, json: texto ? JSON.parse(texto) : null }));
    });
    peticion.on('error', reject);
    peticion.on('timeout', () => peticion.destroy(new Error('Tiempo de espera agotado')));
    if (datos) peticion.write(datos);
    peticion.end();
  });
}

async function todas(ruta, token) {
  const items = [];
  for (let pagina = 1; pagina <= 100; pagina++) {
    const sep = ruta.includes('?') ? '&' : '?';
    const r = await pedir('GET', `${ruta}${sep}page=${pagina}&size=100`, { token });
    if (r.estado !== 200) throw new Error(`GET ${ruta} respondió ${r.estado}`);
    items.push(...r.json.items);
    if (items.length >= r.json.totalItems || r.json.items.length === 0) break;
  }
  return items;
}

const corto = (id) => `${id.slice(0, 8)}…`;

(async () => {
  const login = await pedir('POST', '/api/v1/auth/login', { cuerpo: { email: process.env.QA_ADMIN_EMAIL, password: process.env.QA_ADMIN_PASSWORD } });
  if (login.estado !== 200) {
    console.error(`El login del administrador respondió ${login.estado}.`);
    process.exit(1);
  }
  const token = login.json.accessToken;

  const listado = await todas('/api/v1/admin/technicians', token);
  const senalados = await todas('/api/v1/admin/technicians?lowReputation=true', token);

  const cumple = (t) => t.ratingCount >= 5 && t.averageRating !== null && t.averageRating < 3.0;
  const a = new Set(listado.filter(cumple).map((t) => t.userId));
  const b = new Set(senalados.map((t) => t.userId));
  const faltan = [...a].filter((id) => !b.has(id));
  const sobran = [...b].filter((id) => !a.has(id));
  const marcaIncoherente = listado.filter((t) => t.lowReputation !== cumple(t));
  const suspendidos = listado.filter((t) => a.has(t.userId) && t.verificationStatus === 'suspendido');
  const conCalificaciones = listado.filter((t) => t.ratingCount > 0);

  const fecha = new Date().toISOString();
  console.log(`Medición AC9-E2 (SCRUM-642) en QA — ${fecha}`);
  console.log(`Ambiente: ${baseUrl} · rol: admin_tenant · contrato identity.v1.yaml 1.12.0`);
  console.log('Condición: promedio < 3,0 con al menos 5 servicios calificados (SAD 3.9).');
  console.log('');
  console.log(`Técnicos del tenant en el listado: ${listado.length}`);
  console.log(`Con al menos una calificación: ${conCalificaciones.length}`);
  console.log(`Cumplen la condición (A): ${a.size}`);
  console.log(`Señalados por el panel, filtro lowReputation=true (B): ${b.size}`);
  console.log(`En A y no señalados: ${faltan.length}`);
  console.log(`Señalados sin cumplir la condición: ${sobran.length}`);
  console.log(`Filas cuya marca lowReputation no coincide con la condición: ${marcaIncoherente.length}`);
  console.log(`De A, suspendidos: ${suspendidos.length} (la suspensión solo la hace el admin; no hay suspensión automática)`);
  console.log('');
  console.log('Detalle de los técnicos con calificaciones (id truncado · promedio · calificaciones · marca · estado):');
  for (const t of conCalificaciones) {
    console.log(`  ${corto(t.userId)} · ${t.averageRating ?? '—'} · ${t.ratingCount} · ${t.lowReputation ? 'reputación baja' : '—'} · ${t.verificationStatus}`);
  }
  console.log('');
  const porcentaje = a.size === 0 ? null : Math.round((100 * (a.size - faltan.length)) / a.size);
  const resultado = faltan.length === 0 && sobran.length === 0 && marcaIncoherente.length === 0;
  console.log(`Resultado: ${resultado ? 'A = B' : 'A ≠ B'}; señalados ${porcentaje === null ? 'sin técnicos que cumplan la condición' : `${porcentaje} %`}.`);
  process.exit(resultado ? 0 : 1);
})().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
