// SCRUM-478: el aviso de la cancelación llega en tiempo real (RF-36, RNF-06; realtime.v1.yaml).
//
// Newman no habla WebSocket, así que este script cubre esa parte de la colección scrum-478-cancelacion:
// un cliente de prueba crea una solicitud, abre /v1/realtime, envía la trama `auth` y la cancela. Pasa si llega
// `service-request.status-changed` con `cancelado` para esa solicitud antes de 15 s.
//
// Uso (Node 22 o superior, sin dependencias):
//   NODE_TLS_REJECT_UNAUTHORIZED=0 node tests/e2e/scrum-478-aviso-tiempo-real.mjs [https://qa.quickpatch.internal]
// El certificado de QA es de la CA interna del laboratorio; por eso se desactiva la verificación solo en esta prueba.

import { randomBytes } from 'node:crypto';

const base = (process.argv[2] ?? 'https://qa.quickpatch.internal').replace(/\/$/, '');
const api = `${base}/api`;
const LIMITE_MS = 15_000;
const resultados = [];

function registrar(ok, paso, detalle = '') {
  resultados.push({ ok, paso });
  console.log(`${ok ? 'OK   ' : 'FALLO'} ${paso}${detalle ? `  (${detalle})` : ''}`);
}

async function llamar(metodo, ruta, cuerpo, token) {
  const respuesta = await fetch(`${api}${ruta}`, {
    method: metodo,
    headers: {
      'Content-Type': 'application/json',
      'X-Channel-Id': 'quickpatch-mobile',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: cuerpo === undefined ? undefined : JSON.stringify(cuerpo),
  });
  const texto = await respuesta.text();
  return { status: respuesta.status, cuerpo: texto ? JSON.parse(texto) : null };
}

const sufijo = Date.now().toString(36);
// Clave de la cuenta de prueba de esta corrida; no se guarda en ningún lado.
const clave = `Qp${randomBytes(6).toString('hex')}7Z`;
const correo = `aviso478.${sufijo}@quickpatch.test`;

const registro = await llamar('POST', '/v1/auth/register/client', { email: correo, password: clave, fullName: 'Aviso 478' });
registrar(registro.status === 201, 'Registro del cliente', `HTTP ${registro.status}`);
const sesion = await llamar('POST', '/v1/auth/login', { email: correo, password: clave });
registrar(sesion.status === 200, 'Login del cliente', `HTTP ${sesion.status}`);
const token = sesion.cuerpo.accessToken;

const categorias = await llamar('GET', '/v1/catalog/categories', undefined, token);
const solicitud = await llamar(
  'POST',
  '/v1/service-requests',
  {
    categoryId: categorias.cuerpo[0].id,
    description: 'Prueba del aviso de cancelación en tiempo real (SCRUM-478)',
    location: { latitude: 4.6486, longitude: -74.063 },
    addressText: 'Calle 63 # 9-45, apto 201',
  },
  token,
);
registrar(solicitud.status === 201, 'Solicitud creada', `HTTP ${solicitud.status}, ${solicitud.cuerpo?.status}`);
const id = solicitud.cuerpo.id;

const canal = new WebSocket(`${base.replace(/^http/, 'ws')}/api/v1/realtime`);
const aviso = new Promise((resolver, rechazar) => {
  const plazo = setTimeout(() => rechazar(new Error(`sin aviso en ${LIMITE_MS / 1000} s`)), LIMITE_MS);
  canal.addEventListener('open', () => canal.send(JSON.stringify({ type: 'auth', token })));
  canal.addEventListener('close', (e) => rechazar(new Error(`el canal se cerró con ${e.code}`)));
  canal.addEventListener('message', async (evento) => {
    const mensaje = JSON.parse(evento.data);
    if (mensaje.type === 'auth.accepted') {
      registrar(true, 'Canal /v1/realtime autenticado', 'auth.accepted');
      const inicio = Date.now();
      const cancelada = await llamar('POST', `/v1/service-requests/${id}/cancel`, { reason: 'Prueba del aviso en tiempo real.' }, token);
      registrar(cancelada.status === 200, 'El cliente cancela', `HTTP ${cancelada.status}`);
      canal.inicio = inicio;
    } else if (
      mensaje.type === 'service-request.status-changed' &&
      mensaje.serviceRequestId === id &&
      mensaje.status === 'cancelado'
    ) {
      clearTimeout(plazo);
      resolver(Date.now() - canal.inicio);
    }
  });
});

try {
  const ms = await aviso;
  registrar(true, 'Llega service-request.status-changed con cancelado', `${ms} ms después de cancelar`);
} catch (e) {
  registrar(false, 'Llega service-request.status-changed con cancelado', e.message);
} finally {
  canal.close();
}

const fallos = resultados.filter((r) => !r.ok).length;
console.log(`\n${resultados.length - fallos}/${resultados.length} OK. Cliente de prueba: ${correo}; solicitud ${id}.`);
process.exit(fallos === 0 ? 0 : 1);
