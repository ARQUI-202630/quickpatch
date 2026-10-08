# Pruebas de Seguridad — QUICKPATCH

Este directorio contiene las herramientas y reglas de validación de seguridad de la compuerta de aseguramiento de calidad (Gate 2 / CI y Gate 3 / QA).

---

## 1. Alcance de las Pruebas

| Componente | Herramienta | Requisito / Escenario | Criterio de Aserción |
| :--- | :--- | :--- | :--- |
| **Escaneo Dinámico DAST** | OWASP ZAP Baseline | INF-013, SAD 4.2 | Inspección de vulnerabilidades sobre el API Gateway (`qa.quickpatch.internal`). Las reglas críticas (SQLi, XSS, RCE, Traversal) detienen el pipeline (`FAIL`), mientras que advertencias informativas se reportan sin bloquear. |
| **Escáner de Privacidad PCI-DSS** | Python (`pci_dss_scanner.py`) | PAY-002, K2 | Inspección sobre los logs centralizados de QA (Loki) garantizando que ningún PAN (validado con algoritmo de Luhn) ni códigos CVV/CVC hayan sido registrados en texto plano. Hallazgos esperados = 0. |

---

## 2. Configuración de OWASP ZAP (`zap-baseline.conf`)

El archivo `zap-baseline.conf` define las directivas aplicadas al escáner `ghcr.io/zaproxy/zaproxy:stable`:

* **`FAIL`:** Rompe el build ante vulnerabilidades de riesgo alto (SQL Injection `40018`, XSS `40026`, Command Injection `90020`, Divulgación de código `10045`).
* **`IGNORE`:** Descarta falsos positivos típicos de APIs REST JSON stateless (como la ausencia de tokens Anti-CSRF basados en cookies `10202`, ya que se utiliza autenticación por Bearer JWT).
* **`WARN`:** Alerta sobre encabezados de endurecimiento recomendados (`X-Content-Type-Options`, `Strict-Transport-Security`).

---

## 3. Instrucciones de Ejecución

### Ejecución del Escáner PCI-DSS
Para escanear directamente los logs de QA en Loki:

```bash
python tests/security/pci_dss_scanner.py --loki http://10.43.100.168:3100 --horas 24
```

O para verificar un archivo de log local:

```bash
python tests/security/pci_dss_scanner.py --file logs/qa_api_gateway.log
```

### Ejecución de OWASP ZAP (Docker)
En el runner de CI/CD (VM1) o máquina con Docker:

```bash
docker run --rm -v "${PWD}/tests/security:/zap/wrk:rw" \
  ghcr.io/zaproxy/zaproxy:stable zap-baseline.py \
  -t "https://qa.quickpatch.internal" \
  -c zap-baseline.conf \
  -I -r reporte_zap.html
```
