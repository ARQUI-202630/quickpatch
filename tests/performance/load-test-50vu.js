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

/**
 * Fase de inicialización de k6:
 * - Autenticación real contra Identity con credenciales de QA (sin contraseña hardcodeada).
 * - Envío obligatorio del encabezado X-Channel-Id.
 * - Aborta inmediatamente si el inicio de sesión falla (no usa tokens falsos).
 * - Obtiene dinámicamente un categoryId existente de Catalog para evitar 422.
 */
export function setup() {
    const loginUrl = `${BASE_URL}/api/v1/auth/login`;
    const email = __ENV.QA_CLIENT_EMAIL || 'cliente.qa@quickpatch.internal';
    const password = __ENV.QA_CLIENT_PASSWORD;

    if (!password) {
        throw new Error('[Setup QA] Variable QA_CLIENT_PASSWORD es requerida para autenticación en QA');
    }

    const loginPayload = JSON.stringify({ email, password });
    const loginHeaders = {
        'Content-Type': 'application/json',
        'X-Channel-Id': __ENV.CHANNEL_ID || 'quickpatch-web',
        'X-Correlation-Id': `k6-setup-login-${Date.now()}`
    };

    const resLogin = http.post(loginUrl, loginPayload, { headers: loginHeaders });
    if (resLogin.status !== 200) {
        throw new Error(`[Setup QA] Inicio de sesión en QA falló con HTTP ${resLogin.status}: ${resLogin.body}`);
    }

    let token = null;
    try {
        const body = JSON.parse(resLogin.body);
        token = body.accessToken || body.token;
    } catch (e) {
        throw new Error(`[Setup QA] Error al parsear respuesta JSON de login: ${e.message}`);
    }

    if (!token) {
        throw new Error('[Setup QA] Respuesta de login no contiene accessToken');
    }

    // Obtener categoría válida del catálogo para que las solicitudes no fallen con 422
    let categoryId = __ENV.QA_CATEGORY_ID;
    if (!categoryId) {
        const catRes = http.get(`${BASE_URL}/api/v1/catalog/categories`, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'X-Correlation-Id': `k6-setup-cat-${Date.now()}`
            }
        });

        if (catRes.status === 200) {
            try {
                const cats = JSON.parse(catRes.body);
                if (Array.isArray(cats) && cats.length > 0) {
                    categoryId = cats[0].id;
                }
            } catch (e) {
                console.warn('[Setup QA] Error al parsear categorías del catálogo:', e);
            }
        }
    }

    if (!categoryId) {
        throw new Error('[Setup QA] No se pudo obtener una categoría válida de /api/v1/catalog/categories para la prueba');
    }

    return { token, categoryId };
}

export default function (data) {
    const correlationId = `k6-50vu-${__VU}-${__ITER}-${Date.now()}`;
    const token = data.token;
    const categoryId = data.categoryId;
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
        categoryId: categoryId,
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
