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
* **Datos de Carga y Contexto:** Las pruebas operan con un usuario legítimo con rol cliente autenticado formalmente contra Identity (`POST /api/v1/auth/login`). No se utiliza ningún tenant sintético purgado ni tokens falsos; las solicitudes de prueba se crean bajo el contexto estándar del cliente en el entorno de QA.

---

## 3. Prerrequisitos y Configuración de Credenciales

### Prerrequisito Obligatorio
Antes de ejecutar cualquiera de los scripts de k6, **el usuario de prueba debe existir previamente en Identity**:
* Debe haber sido registrado previamente mediante `POST /api/v1/auth/register` o insertado vía datos semilla en la base de datos de Identity de QA (VM5).
* El usuario debe contar con el rol `cliente` y sus credenciales activas.
* Si el inicio de sesión falla durante la fase `setup()`, el script aborta la ejecución inmediatamente por diseño para garantizar que no se emita tráfico con tokens inválidos o simulados.

### Variables de Entorno

| Variable | Descripción | Valor por Defecto | Obligatoria |
| :--- | :--- | :--- | :---: |
| `BASE_URL` | URL base del Gateway de QA | `https://qa.quickpatch.internal` | No |
| `QA_CLIENT_EMAIL` | Correo electrónico del cliente de pruebas en QA | `cliente.qa@quickpatch.internal` | No |
| `QA_CLIENT_PASSWORD` | Contraseña del usuario de pruebas en QA | *(Sin valor por defecto)* | **Sí** |
| `CHANNEL_ID` | Encabezado `X-Channel-Id` requerido por el Gateway | `quickpatch-web` | No |
| `QA_CATEGORY_ID` | Categoría para las solicitudes técnicas | Obtenida dinámicamente de `/api/v1/catalog/categories` | No |

---

## 4. Instrucciones de Ejecución

### Ejecución en el Runner de CI/CD (VM1)
El flujo `.github/workflows/pruebas-sistema.yml` ejecuta automáticamente los scripts encontrados en este directorio proveyendo las credenciales configuradas en los secretos del repositorio:

```bash
for s in tests/performance/*.js; do
  nombre=$(basename "$s" .js)
  k6 run --insecure-skip-tls-verify \
    -e BASE_URL="$BASE_URL" \
    -e QA_CLIENT_EMAIL="$QA_CLIENT_EMAIL" \
    -e QA_CLIENT_PASSWORD="$QA_CLIENT_PASSWORD" \
    --summary-export "resultados-k6/$nombre.json" "$s"
done
```

### Ejecución Local o Manual
Para ejecutar los scripts individualmente utilizando k6 (asegurar el suministro de `QA_CLIENT_PASSWORD`):

```bash
# Carga normal (50 VU)
k6 run --insecure-skip-tls-verify \
  -e BASE_URL="https://qa.quickpatch.internal" \
  -e QA_CLIENT_EMAIL="cliente.qa@quickpatch.internal" \
  -e QA_CLIENT_PASSWORD="PasswordSeguroQA123*" \
  tests/performance/load-test-50vu.js

# Estrés pico (150 VU)
k6 run --insecure-skip-tls-verify \
  -e BASE_URL="https://qa.quickpatch.internal" \
  -e QA_CLIENT_EMAIL="cliente.qa@quickpatch.internal" \
  -e QA_CLIENT_PASSWORD="PasswordSeguroQA123*" \
  tests/performance/stress-test-150vu.js
```

