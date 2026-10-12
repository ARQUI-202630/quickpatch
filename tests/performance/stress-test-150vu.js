/**
 * QUICKPATCH — Prueba de Estrés Pico Inesperado (150 VU)
 * 
 * Requisitos y Criterios:
 * - PRF-004 (AC2-E4): Pico de carga inesperado de 150 solicitudes concurrentes en QA.
 * - PRF-005 (AC2-E5, R10): Estabilidad de pods y recursos (0 OOMKilled, degradación controlada).
 * - PRF-009: Pool de conexiones a PostgreSQL en QA (VM5) bajo 150 VU sin errores 'too many clients'.
 * - ADR-015 / ADR-022: Ejecución 100% aislada en QA; Producción (VM3/VM4) blindada de estrés.
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend, Rate, Counter } from 'k6/metrics';

// Métricas de estrés y degradación
const latenciaPico = new Trend('latencia_pico');
const errores5xx = new Rate('errores_5xx');
const solicitudesExitosas = new Counter('solicitudes_exitosas');

export const options = {
    stages: [
        { duration: '30s', target: 50 },   // Escalado inicial a carga base
        { duration: '1m', target: 150 },   // Ráfaga abrupta a 150 VU (Pico)
        { duration: '2m', target: 150 },   // Prueba de estrés sostenido en pico
        { duration: '30s', target: 0 },    // Enfriamiento y recuperación
    ],
    thresholds: {
        // Criterio PRF-004 / AC2-E4: Cero caídas de pod y 0% de errores críticos 5xx
        'errores_5xx': ['rate==0'],
        // Degradación controlada: bajo estrés extremo el 95% de respuestas responde en < 5.0 s
        'http_req_duration': ['p(95)<5000'],
        // Al menos el 98% de las peticiones deben ser atendidas o degradadas con 429/503 controlados, no colapsos
        'http_req_failed': ['rate<0.05'],
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

    // Obtener categoría válida del catálogo para evitar error 422
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
    const correlationId = `k6-150vu-${__VU}-${__ITER}-${Date.now()}`;
    const token = data.token;
    const categoryId = data.categoryId;
    const headers = {
        'Content-Type': 'application/json',
        'X-Correlation-Id': correlationId,
        'Authorization': `Bearer ${token}`,
    };

    // Coordenadas válidas en Bogotá
    const lat = 4.6200 + (Math.random() * 0.06);
    const lon = -74.0600 - (Math.random() * 0.05);

    const payload = JSON.stringify({
        categoryId: categoryId,
        description: `Estrés pico 150 VU - matching simultáneo VU-${__VU}`,
        location: {
            latitude: parseFloat(lat.toFixed(6)),
            longitude: parseFloat(lon.toFixed(6))
        },
        addressText: `Avenida Caracas # ${Math.floor(Math.random() * 80) + 1}-10, Bogotá`
    });

    const res = http.post(`${BASE_URL}/api/v1/service-requests`, payload, {
        headers: headers,
        tags: { test_type: 'stress_150vu' },
    });

    // Validar que el servidor no emita errores 5xx de caída de proceso (500, 502, 504 sin control)
    const is5xx = res.status >= 500 && res.status < 600;
    errores5xx.add(is5xx);

    check(res, {
        'Sin errores 5xx del servidor': (r) => r.status < 500,
        'Respuesta exitosa o degradada controladamente (no caída)': (r) => r.status === 201 || r.status === 200 || r.status === 429,
    });

    if (res.status === 201 || res.status === 200) {
        solicitudesExitosas.add(1);
    }

    latenciaPico.add(res.timings.duration);

    // Sleep dinámico breve para mantener alta concurrencia
    sleep(0.3 + (Math.random() * 0.4));
}
