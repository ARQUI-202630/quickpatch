// SCRUM-627: el enlace de recuperación vence a la hora (REC-015, SCRUM-623; identity.v1.yaml 1.10.0).
//
// La colección scrum-627-recuperacion no puede esperar una hora, así que este script cubre ese caso: registra un
// cliente, pide la recuperación, el administrador genera el enlace y el script espera a que pase `expiresAt` (más un
// margen). Pasa si el enlace vencido responde 400 `enlace-invalido`, la clave anterior sigue entrando, y un enlace nuevo
// para la misma solicitud sí sirve. Tarda algo más de una hora.
//
// Uso (Node 22 o superior, sin dependencias), con las credenciales del administrador del tenant en el entorno, nunca
// en el repositorio:
//   QA_ADMIN_EMAIL=... QA_ADMIN_PASSWORD=... NODE_EXTRA_CA_CERTS=<CA de QA> node tests/e2e/scrum-627-enlace-vencido.mjs
// QA_BASE_URL cambia el destino (por defecto https://qa.quickpatch.internal). El token y las claves solo viven en
// memoria: no se imprimen.

import { randomBytes } from 'node:crypto';

const base = (process.env.QA_BASE_URL ?? 'https://qa.quickpatch.internal').replace(/\/$/, '');
const api = `${base}/api`;
const MARGEN_MS = 90_000;
const resultados = [];

for (const variable of ['QA_ADMIN_EMAIL', 'QA_ADMIN_PASSWORD']) {
  if (!process.env[variable]) {
    console.error(`Falta ${variable} en el entorno. Defínela en tu terminal; no la escribas en el repositorio.`);
    process.exit(2);
  }
}

function registrar(ok, paso, detalle = '') {
  resultados.push({ ok, paso });
  console.log(`${new Date().toISOString()} ${ok ? 'OK   ' : 'FALLO'} ${paso}${detalle ? `  (${detalle})` : ''}`);
}

class Detenida extends Error {}

/** Corta la prueba si un paso falla y lo que sigue depende de él. */
function exigir(ok, paso, detalle) {
  registrar(ok, paso, detalle);
  if (!ok) throw new Detenida(paso);
}

async function llamar(metodo, ruta, cuerpo, token) {
  const respuesta = await fetch(`${api}${ruta}`, {
    method: metodo,
    headers: {
      'Content-Type': 'application/json',
      'X-Channel-Id': 'quickpatch-mobile',
      'X-Correlation-Id': crypto.randomUUID(),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: cuerpo === undefined ? undefined : JSON.stringify(cuerpo),
  });
  const texto = await respuesta.text();
  let datos = null;
  try {
    datos = texto ? JSON.parse(texto) : null;
  } catch {
    datos = texto;
  }
  return { status: respuesta.status, cuerpo: datos };
}

const esperar = (ms) => new Promise((r) => setTimeout(r, ms));

/** Recorre las páginas de solicitudes pendientes hasta encontrar la del correo. */
async function buscarSolicitud(adminToken, correo) {
  for (let pagina = 1; ; pagina++) {
    const r = await llamar('GET', `/v1/admin/password-recovery-requests?page=${pagina}&size=100`, undefined, adminToken);
    if (r.status !== 200) return null;
    const item = r.cuerpo.items.find((i) => i.email.toLowerCase() === correo);
    if (item || pagina * r.cuerpo.size >= r.cuerpo.totalItems) return item ?? null;
  }
}

const sufijo = Date.now().toString(36);
const correo = `rec.vencido.${sufijo}@quickpatch.test`;
const clave = `Qp_${randomBytes(6).toString('hex')}!Aa7`;
const claveNueva = `Qn_${randomBytes(6).toString('hex')}!Bb8`;

try {
  const admin = await llamar('POST', '/v1/auth/login', { email: process.env.QA_ADMIN_EMAIL, password: process.env.QA_ADMIN_PASSWORD });
  exigir(admin.status === 200, 'Login del administrador del tenant', `HTTP ${admin.status}`);
  const adminToken = admin.cuerpo.accessToken;

  const registro = await llamar('POST', '/v1/auth/register/client', { email: correo, password: clave, fullName: 'Prueba QA enlace vencido' });
  exigir(registro.status === 201, 'Registro del cliente', `HTTP ${registro.status}`);

  const pedido = await llamar('POST', '/v1/auth/password-recovery', { email: correo });
  exigir(pedido.status === 202, 'El cliente pide recuperar la contraseña', `HTTP ${pedido.status}`);

  const solicitud = await buscarSolicitud(adminToken, correo);
  exigir(Boolean(solicitud), 'El administrador ve la solicitud');

  const enlace = await llamar('POST', `/v1/admin/password-recovery-requests/${solicitud.id}/link`, undefined, adminToken);
  exigir(enlace.status === 201, 'El administrador genera el enlace', `HTTP ${enlace.status}, vence ${enlace.cuerpo?.expiresAt}`);

  const espera = Date.parse(enlace.cuerpo.expiresAt) - Date.now() + MARGEN_MS;
  console.log(`Esperando ${Math.round(espera / 60000)} minutos a que el enlace venza...`);
  await esperar(espera);

  const vencido = await llamar('POST', '/v1/auth/password-recovery/confirm', { token: enlace.cuerpo.token, password: claveNueva });
  registrar(
    vencido.status === 400 && /\/enlace-invalido$/.test(vencido.cuerpo?.type ?? ''),
    'REC-015: el enlace vencido responde 400 enlace-invalido',
    `HTTP ${vencido.status}, ${vencido.cuerpo?.type ?? ''}`,
  );

  const anterior = await llamar('POST', '/v1/auth/login', { email: correo, password: clave });
  registrar(anterior.status === 200, 'REC-015: la clave anterior sigue entrando', `HTTP ${anterior.status}`);

  // El token del administrador venció durante la espera: se pide otro.
  const admin2 = await llamar('POST', '/v1/auth/login', { email: process.env.QA_ADMIN_EMAIL, password: process.env.QA_ADMIN_PASSWORD });
  exigir(admin2.status === 200, 'Login otra vez del administrador', `HTTP ${admin2.status}`);

  const nuevo = await llamar('POST', `/v1/admin/password-recovery-requests/${solicitud.id}/link`, undefined, admin2.cuerpo.accessToken);
  exigir(nuevo.status === 201, 'REC-015: la solicitud sigue pendiente y admite un enlace nuevo', `HTTP ${nuevo.status}`);

  const confirmado = await llamar('POST', '/v1/auth/password-recovery/confirm', { token: nuevo.cuerpo.token, password: claveNueva });
  registrar(confirmado.status === 204, 'REC-015: el enlace nuevo sí sirve', `HTTP ${confirmado.status}`);

  const login = await llamar('POST', '/v1/auth/login', { email: correo, password: claveNueva });
  registrar(login.status === 200, 'REC-015: entra con la clave nueva', `HTTP ${login.status}`);
} catch (error) {
  if (!(error instanceof Detenida)) {
    registrar(false, 'Error inesperado', error.message);
  }
}

const fallos = resultados.filter((r) => !r.ok).length;
console.log(`\n${resultados.length - fallos}/${resultados.length} OK.`);
process.exit(fallos === 0 ? 0 : 1);
