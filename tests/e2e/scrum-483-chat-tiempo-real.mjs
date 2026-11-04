// SCRUM-483: los mensajes del chat llegan en tiempo real al otro participante (RF-37, ADR-026; realtime.v1.yaml 1.1.0).
//
// Newman no habla WebSocket, así que este script cubre esa parte de la colección scrum-483-chat: arma una solicitud
// asignada (categoría propia, técnico aprobado, cliente y oferta aceptada), abre /v1/realtime con el cliente y con el
// técnico como dos dispositivos, y cada uno escribe por REST. Pasa si al otro le llega la trama `chat.message` con el
// mismo mensaje antes de 15 s. Al final cancela la solicitud, suspende al técnico y desactiva la categoría.
//
// Uso (Node 22 o superior, sin dependencias), con las credenciales del administrador del tenant en el entorno, nunca
// en el repositorio:
//   QA_ADMIN_EMAIL=... QA_ADMIN_PASSWORD=... NODE_TLS_REJECT_UNAUTHORIZED=0 node tests/e2e/scrum-483-chat-tiempo-real.mjs
// QA_BASE_URL cambia el destino (por defecto https://qa.quickpatch.internal). El certificado de QA es de la CA interna
// del laboratorio; por eso se desactiva la verificación solo en esta prueba. No imprime tokens ni claves.

import { randomBytes } from 'node:crypto';

const base = (process.env.QA_BASE_URL ?? 'https://qa.quickpatch.internal').replace(/\/$/, '');
const api = `${base}/api`;
const LIMITE_MS = 15_000;
const resultados = [];

for (const variable of ['QA_ADMIN_EMAIL', 'QA_ADMIN_PASSWORD']) {
  if (!process.env[variable]) {
    console.error(`Falta ${variable} en el entorno. Defínela en tu terminal; no la escribas en el repositorio.`);
    process.exit(2);
  }
}

function registrar(ok, paso, detalle = '') {
  resultados.push({ ok, paso });
  console.log(`${ok ? 'OK   ' : 'FALLO'} ${paso}${detalle ? `  (${detalle})` : ''}`);
}

function terminar() {
  const fallos = resultados.filter((r) => !r.ok).length;
  console.log(`\n${resultados.length - fallos}/${resultados.length} OK.`);
  process.exit(fallos === 0 ? 0 : 1);
}

class Detenida extends Error {}

/** Corta la prueba si un paso falla y lo que sigue depende de él; la limpieza se hace igual. */
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

/** Repite la llamada hasta que `listo` se cumpla: los efectos llegan por Kafka y no son inmediatos. */
async function hasta(llamada, listo, intentos = 20, espera = 2000) {
  let ultima;
  for (let i = 0; i < intentos; i++) {
    ultima = await llamada();
    if (listo(ultima)) return ultima;
    await esperar(espera);
  }
  return ultima;
}

const sufijo = Date.now().toString(36);
// Clave de las cuentas de esta corrida; no se guarda en ningún lado.
const clave = `Qp_${randomBytes(6).toString('hex')}!Aa7`;
const correo = (prefijo) => `${prefijo}.chat483.${sufijo}@quickpatch.test`;

let adminToken;
let categoriaId;
let tecnicoId;

try {
  // 1. Preparación
  const admin = await llamar('POST', '/v1/auth/login', {
    email: process.env.QA_ADMIN_EMAIL,
    password: process.env.QA_ADMIN_PASSWORD,
  });
  exigir(
    admin.status === 200 && admin.cuerpo?.user?.role === 'admin_tenant',
    'Login del administrador del tenant',
    `HTTP ${admin.status}`,
  );
  adminToken = admin.cuerpo.accessToken;

  const categoria = await llamar(
    'POST',
    '/v1/catalog/admin/categories',
    {
      name: `SCRUM-483 ${sufijo}`,
      description: 'Categoría de la prueba del chat en tiempo real; se desactiva al final',
    },
    adminToken,
  );
  exigir(categoria.status === 201, 'Categoría solo para esta corrida', `HTTP ${categoria.status}`);
  categoriaId = categoria.cuerpo.id;

  const tecnico = await llamar('POST', '/v1/auth/register/technician', {
    email: correo('tecnico'),
    password: clave,
    fullName: 'Técnico chat 483',
    phone: '3007654321',
    documentId: String(Date.now()).slice(-10),
    specialtyId: categoriaId,
    role: 'tecnico',
  });
  exigir(tecnico.status === 201, 'Registro del técnico', `HTTP ${tecnico.status}`);
  tecnicoId = tecnico.cuerpo.id;

  let tecnicoToken;
  const aprobado = await llamar('POST', `/v1/admin/technicians/${tecnicoId}/approve`, undefined, adminToken);
  exigir(aprobado.status === 200, 'El administrador aprueba al técnico', `HTTP ${aprobado.status}`);
  const sesionTecnico = await llamar('POST', '/v1/auth/login', { email: correo('tecnico'), password: clave });
  exigir(sesionTecnico.status === 200, 'Login del técnico', `HTTP ${sesionTecnico.status}`);
  tecnicoToken = sesionTecnico.cuerpo.accessToken;

  const localidades = Array.from({ length: 20 }, (_, i) => String(i + 1).padStart(2, '0'));
  const cobertura = await hasta(
    () => llamar('PUT', '/v1/technicians/me/coverage', { localityCodes: localidades }, tecnicoToken),
    (r) => r.status === 200,
  );
  exigir(cobertura.status === 200, 'El técnico cubre toda Bogotá', `HTTP ${cobertura.status}`);
  const disponible = await hasta(
    () => llamar('PUT', '/v1/technicians/me/availability', { status: 'disponible' }, tecnicoToken),
    (r) => r.status === 200,
  );
  exigir(disponible.status === 200, 'El técnico queda disponible', `HTTP ${disponible.status}`);

  const cliente = await llamar('POST', '/v1/auth/register/client', {
    email: correo('cliente'),
    password: clave,
    fullName: 'Cliente chat 483',
  });
  exigir(cliente.status === 201, 'Registro del cliente', `HTTP ${cliente.status}`);
  const sesionCliente = await llamar('POST', '/v1/auth/login', { email: correo('cliente'), password: clave });
  exigir(sesionCliente.status === 200, 'Login del cliente', `HTTP ${sesionCliente.status}`);
  const clienteToken = sesionCliente.cuerpo.accessToken;

  const solicitud = await hasta(
    () =>
      llamar(
        'POST',
        '/v1/service-requests',
        {
          categoryId: categoriaId,
          description: 'Prueba del chat en tiempo real (SCRUM-483)',
          location: { latitude: 4.6486, longitude: -74.063 },
          addressText: 'Calle 63 # 9-45, apto 201',
        },
        clienteToken,
      ),
    (r) => r.status !== 422,
    10,
  );
  exigir(solicitud.status === 201, 'Solicitud creada', `HTTP ${solicitud.status}`);
  const id = solicitud.cuerpo.id;

  const ofertas = await hasta(
    () => llamar('GET', '/v1/matching/offers?status=pendiente', undefined, tecnicoToken),
    (r) => r.status === 200 && r.cuerpo.items.some((o) => o.serviceRequestId === id),
  );
  const oferta = ofertas.cuerpo?.items?.find((o) => o.serviceRequestId === id);
  exigir(Boolean(oferta), 'El técnico recibe la oferta');
  const aceptada = await llamar('POST', `/v1/matching/offers/${oferta.attemptId}/accept`, undefined, tecnicoToken);
  exigir(aceptada.status === 200, 'El técnico acepta la oferta', `HTTP ${aceptada.status}`);
  const asignada = await hasta(
    () => llamar('GET', `/v1/service-requests/${id}`, undefined, clienteToken),
    (r) => r.cuerpo?.status === 'asignado',
  );
  exigir(asignada.cuerpo?.status === 'asignado', 'La solicitud queda asignada');
  const chat = await hasta(
    () => llamar('GET', `/v1/service-requests/${id}/messages`, undefined, clienteToken),
    (r) => r.status === 200 && r.cuerpo.writable === true,
  );
  exigir(
    chat.status === 200 && chat.cuerpo.writable === true,
    'El chat está abierto (Communication tiene la réplica)',
    `HTTP ${chat.status}`,
  );

  // 2. Dos dispositivos conectados al canal
  function abrirCanal(token, quien) {
    const ws = new WebSocket(`${base.replace(/^http/, 'ws')}/api/v1/realtime`);
    const tramas = [];
    const esperando = [];
    ws.addEventListener('message', (evento) => {
      const trama = JSON.parse(evento.data);
      tramas.push(trama);
      for (const e of [...esperando]) {
        if (e.condicion(trama)) {
          esperando.splice(esperando.indexOf(e), 1);
          e.resolver(trama);
        }
      }
    });
    const recibir = (condicion) =>
      new Promise((resolver, rechazar) => {
        const previa = tramas.find(condicion);
        if (previa) return resolver(previa);
        const plazo = setTimeout(() => rechazar(new Error(`sin la trama en ${LIMITE_MS / 1000} s`)), LIMITE_MS);
        esperando.push({
          condicion,
          resolver: (t) => {
            clearTimeout(plazo);
            resolver(t);
          },
        });
      });
    ws.addEventListener('open', () => ws.send(JSON.stringify({ type: 'auth', token })));
    ws.addEventListener('close', (e) => {
      if (e.code !== 1000 && e.code !== 1005) console.log(`      (canal del ${quien} cerrado con ${e.code})`);
    });
    return { ws, recibir };
  }

  const canalCliente = abrirCanal(clienteToken, 'cliente');
  const canalTecnico = abrirCanal(tecnicoToken, 'técnico');
  try {
    await Promise.all([
      canalCliente.recibir((t) => t.type === 'auth.accepted'),
      canalTecnico.recibir((t) => t.type === 'auth.accepted'),
    ]);
    registrar(true, 'Cliente y técnico conectados a /v1/realtime', 'auth.accepted en los dos');
  } catch (e) {
    exigir(false, 'Cliente y técnico conectados a /v1/realtime', e.message);
  }

  async function conversar(quien, token, otro, canalOtro, texto, rol) {
    const inicio = Date.now();
    const enviado = await llamar('POST', `/v1/service-requests/${id}/messages`, { text: texto }, token);
    registrar(
      enviado.status === 201 && enviado.cuerpo.authorRole === rol,
      `El ${quien} escribe`,
      `HTTP ${enviado.status}`,
    );
    try {
      const trama = await canalOtro.recibir((t) => t.type === 'chat.message' && t.message?.id === enviado.cuerpo?.id);
      const igual = trama.serviceRequestId === id && trama.message.text === texto && trama.message.authorRole === rol;
      registrar(igual, `Al ${otro} le llega chat.message con el mismo mensaje`, `${Date.now() - inicio} ms`);
    } catch (e) {
      registrar(false, `Al ${otro} le llega chat.message con el mismo mensaje`, e.message);
    }
  }

  await conversar('técnico', tecnicoToken, 'cliente', canalCliente, 'Voy en camino, llego en 20 minutos.', 'tecnico');
  await conversar('cliente', clienteToken, 'técnico', canalTecnico, 'Perfecto, lo espero en la portería.', 'cliente');

  canalCliente.ws.close(1000);
  canalTecnico.ws.close(1000);

  // 3. Cierre
  const cancelada = await llamar(
    'POST',
    `/v1/service-requests/${id}/cancel`,
    { reason: 'Fin de la prueba SCRUM-483.' },
    clienteToken,
  );
  registrar(cancelada.status === 200, 'El cliente cancela la solicitud', `HTTP ${cancelada.status}`);
  const cerrado = await hasta(
    () => llamar('GET', `/v1/service-requests/${id}/messages`, undefined, tecnicoToken),
    (r) => r.status === 200 && r.cuerpo.writable === false,
  );
  registrar(
    cerrado.cuerpo?.writable === false && cerrado.cuerpo?.totalItems === 2,
    'El técnico conserva el historial en solo lectura',
    `${cerrado.cuerpo?.totalItems} mensajes`,
  );
} catch (e) {
  if (!(e instanceof Detenida)) registrar(false, 'Error inesperado', e.message);
} finally {
  // Limpieza: aunque algo falle, el técnico y la categoría de la prueba no quedan activos en QA.
  if (tecnicoId) {
    const suspendido = await llamar(
      'POST',
      `/v1/admin/technicians/${tecnicoId}/suspend`,
      { reason: 'Cuenta de una prueba de QA.' },
      adminToken,
    );
    registrar(suspendido.status === 200, 'Limpieza: suspender al técnico', `HTTP ${suspendido.status}`);
  }
  if (categoriaId) {
    const desactivada = await llamar(
      'PATCH',
      `/v1/catalog/admin/categories/${categoriaId}`,
      { active: false },
      adminToken,
    );
    registrar(desactivada.status === 200, 'Limpieza: desactivar la categoría', `HTTP ${desactivada.status}`);
  }
}

terminar();
