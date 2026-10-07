# Pruebas de Rendimiento y Carga — QUICKPATCH

Este directorio contiene los scripts oficiales de pruebas de rendimiento implementados con **k6**, orientados a evaluar la latencia, concurrencia y resiliencia del sistema bajo carga en el ambiente de QA (ADR-015, ADR-022).

---

## 1. Alcance de las Suites

| Script | Escenario | Concurrencia | Duración | Criterios de Aceptación y Umbrales (Thresholds) | Requisitos / SAD |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `load-test-50vu.js` | Carga Normal Sostenida | 50 VU | 2.5 min | • Catálogo (`GET /api/v1/catalog/categories`) p95 < **200 ms**.<br>• Creación (`POST /api/v1/service-requests`) p95 < **2.0 s**.<br>• Tasa de errores < **1.0%**. | PRF-001, PRF-002, PRF-007 (RNF-06), AC2-E1, AC2-E2 |
| `stress-test-150vu.js` | Estrés Pico Inesperado | 150 VU | 4.0 min | • Cero caídas de pod y **0% errores 5xx** (`errores_5xx == 0`).<br>• Latencia p95 < **5.0 s** bajo estrés extremo.<br>• Tasa global de fallos no controlados < **5.0%**. | PRF-004, PRF-005, PRF-009, AC2-E4, AC2-E5, R10 |

---

## 2. Aislamiento de Entornos (ADR-015 / ADR-022)

* **Objetivo:** Todas las pruebas de carga y estrés se ejecutan **exclusivamente contra el ambiente de QA** (`qa.quickpatch.internal`), distribuido en VM2 (k3s aplicación), VM5 (PostgreSQL 16 + PostGIS y Redis) y VM7 (Kafka y Garage S3).
* **Protección de Producción:** El entorno de producción (`quickpatch.internal` en VM3, VM4 y VM6) está estrictamente aislado y **no recibe tráfico de prueba ni estrés rutinario**.
* **Tenant de Carga:** Se utiliza el identificador dedicado `tenant_qa_loadtest` (`a1a1a1a1-bbbb-cccc-dddd-eeeeeeeeeeee`), el cual es purgado de forma independiente en la base de datos de QA (VM5) al concluir la compuerta de pruebas.

---

## 3. Instrucciones de Ejecución

### Ejecución en el Runner de CI/CD (VM1)
El flujo `.github/workflows/pruebas-sistema.yml` ejecuta automáticamente todos los scripts encontrados en este directorio:

```bash
for s in tests/performance/*.js; do
  nombre=$(basename "$s" .js)
  k6 run --insecure-skip-tls-verify -e BASE_URL="$BASE_URL" \
    --summary-export "resultados-k6/$nombre.json" "$s"
done
```

### Ejecución Local o Manual
Para ejecutar los scripts individualmente utilizando k6:

```bash
# Carga normal (50 VU)
k6 run --insecure-skip-tls-verify -e BASE_URL="https://qa.quickpatch.internal" tests/performance/load-test-50vu.js

# Estrés pico (150 VU)
k6 run --insecure-skip-tls-verify -e BASE_URL="https://qa.quickpatch.internal" tests/performance/stress-test-150vu.js
```
