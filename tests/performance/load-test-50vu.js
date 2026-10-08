/**
 * QUICKPATCH — Prueba de Carga Normal Sostenida (50 VU)
 * 
 * Requisitos y Criterios:
 * - PRF-001 / PRF-002: Latencia de procesamiento de solicitudes y consultas.
 * - PRF-007 (RNF-06): Operación continua y sostenida bajo carga normal (50 VU).
 * - SAD: AC2-E1 (creación de solicitud p95 < 2.0s), AC2-E2 (catálogo p95 < 200ms).
 * - ADR-015 / ADR-022: Ejecución exclusiva sobre el ambiente de QA (qa.quickpatch.internal).
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend, Rate } from 'k6/metrics';

// Métricas personalizadas
const catalogoDuration = new Trend('catalogo_duration');
const solicitudDuration = new Trend('solicitud_duration');
const tasaErrores = new Rate('tasa_errores');

export const options = {
    stages: [
        { duration: '30s', target: 25 },  // Rampa de subida inicial
        { duration: '1m30s', target: 50 }, // Carga sostenida a 50 VU
        { duration: '30s', target: 0 },   // Rampa de bajada controlada
    ],
    thresholds: {
        // Criterio AC2-E2: Consulta de catálogo p95 inferior a 200 ms
        'http_req_duration{endpoint:catalogo}': ['p(95)<200'],
        // Criterio AC2-E1: Creación de solicitud p95 inferior a 2.0 s (2000 ms)
        'http_req_duration{endpoint:crear_solicitud}': ['p(95)<2000'],
        // Criterio RNF-06: Tasa de fallos menor al 1%
        'http_req_failed': ['rate<0.01'],
        'tasa_errores': ['rate<0.01'],
    },
};

const BASE_URL = __ENV.BASE_URL || 'https://qa.quickpatch.internal';
const TENANT_ID = 'a1a1a1a1-bbbb-cccc-dddd-eeeeeeeeeeee'; // tenant_qa_loadtest

/**
 * Fase de inicialización de k6: obtiene token JWT RS256 legítimo mediante
 * inicio de sesión real contra Identity con credenciales parametrizadas de QA.
 */
export function setup() {
    const loginUrl = `${BASE_URL}/api/v1/auth/login`;
    const email = __ENV.QA_CLIENT_EMAIL || 'cliente.qa@quickpatch.internal';
    const password = __ENV.QA_CLIENT_PASSWORD || 'PasswordQA123*';

    const res = http.post(loginUrl, JSON.stringify({ email, password }), {
        headers: { 'Content-Type': 'application/json' },
    });

    if (res.status === 200) {
        try {
            const body = JSON.parse(res.body);
            return { token: body.accessToken || body.token };
        } catch (e) {
            console.warn('[Setup QA] Error al parsear respuesta de login:', e);
        }
    } else {
        console.warn(`[Setup QA] Inicio de sesión retornó HTTP ${res.status}. Modo preparatorio sin clúster activo.`);
    }

    return { token: 'token-preparatorio-local' };
}

export default function (data) {
    const correlationId = `k6-50vu-${__VU}-${__ITER}-${Date.now()}`;
    const token = data && data.token ? data.token : 'token-preparatorio-local';
    const headers = {
        'Content-Type': 'application/json',
        'X-Correlation-Id': correlationId,
        'Authorization': `Bearer ${token}`,
    };

    // 1. Paso 1: Consulta del catálogo de servicios técnicos (AC2-E2)
    const resCatalogo = http.get(`${BASE_URL}/api/v1/catalog/categories`, {
        headers: headers,
        tags: { endpoint: 'catalogo' },
    });

    const catalogoOk = check(resCatalogo, {
        'Catalogo responde 200 OK': (r) => r.status === 200,
        'Catalogo p95 dentro de umbral': (r) => r.timings.duration < 200,
    });

    catalogoDuration.add(resCatalogo.timings.duration);
    tasaErrores.add(!catalogoOk);

    sleep(0.5);

    // 2. Paso 2: Creación de solicitud de servicio técnico (AC2-E1)
    // Coordenadas aleatorias dentro del perímetro urbano de Bogotá (RN-SR1, RN-SR9)
    const lat = 4.6097 + (Math.random() * 0.08); // 4.60 a 4.68
    const lon = -74.0817 - (Math.random() * 0.04); // -74.08 a -74.12

    const payloadSolicitud = JSON.stringify({
        categoryId: '3f1c2a4e-8d7b-4c1a-9e2f-5b6a7c8d9e01',
        description: `Solicitud de carga k6 normal VU-${__VU} iter-${__ITER}`,
        location: {
            latitude: parseFloat(lat.toFixed(6)),
            longitude: parseFloat(lon.toFixed(6)),
        },
        addressText: `Calle ${Math.floor(Math.random() * 100) + 1} # ${Math.floor(Math.random() * 50) + 1}-20, Bogotá D.C.`
    });

    const resSolicitud = http.post(`${BASE_URL}/api/v1/service-requests`, payloadSolicitud, {
        headers: headers,
        tags: { endpoint: 'crear_solicitud' },
    });

    const solicitudOk = check(resSolicitud, {
        'Solicitud responde 201 Created o 200': (r) => r.status === 201 || r.status === 200,
        'Solicitud p95 dentro de umbral': (r) => r.timings.duration < 2000,
    });

    solicitudDuration.add(resSolicitud.timings.duration);
    tasaErrores.add(!solicitudOk);

    // Pausa proporcional entre iteraciones para mantener 50 VU estables
    sleep(1);
}
