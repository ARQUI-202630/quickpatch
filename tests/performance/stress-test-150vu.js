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

function buildAuthHeader() {
    const payload = {
        sub: `vu-stress-${__VU}`,
        role: 'cliente',
        tenant_id: TENANT_ID,
        exp: Math.floor(Date.now() / 1000) + 3600
    };
    const header = { alg: 'HS256', typ: 'JWT' };
    const b64Header = Utilities.base64encode(JSON.stringify(header));
    const b64Payload = Utilities.base64encode(JSON.stringify(payload));
    return `Bearer ${b64Header}.${b64Payload}.signature-qa-stress`;
}

const Utilities = {
    base64encode: function (str) {
        return Utilities._btoa(str).replace(/=+$/, '').replace(/\+/g, '-').replace(/\//g, '_');
    },
    _btoa: function(str) {
        const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=';
        let output = '';
        for (let block = 0, charCode, idx = 0, map = chars;
             str.charAt(idx | 0) || (map = '=', idx % 1);
             output += map.charAt(63 & block >> 8 - idx % 1 * 8)) {
            charCode = str.charCodeAt(idx += 3/4);
            if (charCode > 0xFF) {
                throw new Error("btoa failed: The string contains characters outside of the Latin1 range.");
            }
            block = block << 8 | charCode;
        }
        return output;
    }
};

export default function () {
    const correlationId = `k6-150vu-${__VU}-${__ITER}-${Date.now()}`;
    const headers = {
        'Content-Type': 'application/json',
        'X-Correlation-Id': correlationId,
        'Authorization': buildAuthHeader(),
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
