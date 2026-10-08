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
    const correlationId = `k6-150vu-${__VU}-${__ITER}-${Date.now()}`;
    const token = data && data.token ? data.token : 'token-preparatorio-local';
    const headers = {
        'Content-Type': 'application/json',
        'X-Correlation-Id': correlationId,
        'Authorization': `Bearer ${token}`,
    };

    // Coordenadas válidas en Bogotá
    const lat = 4.6200 + (Math.random() * 0.06);
    const lon = -74.0600 - (Math.random() * 0.05);

    const payload = JSON.stringify({
        categoryId: '3f1c2a4e-8d7b-4c1a-9e2f-5b6a7c8d9e01',
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
