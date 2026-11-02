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

Para correr la suite completa con pruebas de robustez y casos de borde:

```bash
python tests/security/run-pci-dss-suite.py
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

Para procesar y validar el informe ZAP contra las reglas de compuerta:

```bash
python tests/security/run-dast-zap-suite.py
```

---

## 4. Trazabilidad de Evidencias Previo al Lanzamiento (SCRUM-507 / SCRUM-49)

Las evidencias y reportes formales generados para la compuerta de seguridad previa al lanzamiento a Producción se encuentran archivados en `tests/security/evidencias/`:

| Archivo de Evidencia | Descripción y Alcance | Trazabilidad Jira |
|---|---|---|
| `reporte-revision-vulnerabilidades-lanzamiento-scrum-507.md` | Informe v2.1 de revisión de vulnerabilidades para la compuerta de lanzamiento, con la evidencia de la corrida de CI 41168063519 | **SCRUM-507**, **SCRUM-49** |
| `zap-pci-ci-qa-2026-10-30-run-41168063519.txt` | Líneas de ZAP baseline y del paso PCI-DSS copiadas del log de la corrida de CI 41168063519 (30 de octubre): 0 FAIL, 4 WARN, 2 IGNORE, 55 PASS; 5.000 líneas de logs de QA con 0 hallazgos | **SCRUM-507**, **SCRUM-49** |
| `zap-dast-baseline-qa-2026-10-30.html` | Reporte HTML de ZAP publicado como artefacto `reporte-zap` de esa corrida | **SCRUM-507** |
| `credenciales-bcrypt-identity-2026-11-02.txt` | Inspección del código de Identity: BCrypt con factor de trabajo 12 y solo `password_hash` en la base | **SCRUM-507**, **SCRUM-49** |
| `cifrado-reposo-k3s-qa-2026-10-30.txt` | Estado del cifrado en reposo de los `Secret` de k3s según `INFRASTRUCTURE.md` (QA cifrado, Producción pendiente) | **SCRUM-49**, **SCRUM-518** |
| `zap-dast-baseline-qa-2026-10-18.txt` | Escaneo dinámico DAST OWASP ZAP Baseline sobre el API Gateway (corrida inicial de referencia) | **SCRUM-507**, **SCRUM-526** |
| `pci-dss-loki-qa-2026-10-18.txt` | Antecedente: auditoría PCI-DSS local sobre 100 líneas exportadas de Loki, antes del despliegue de Payments (0 PAN, 0 CVV) | **SCRUM-507**, **SCRUM-527** |
| `tls-ingress-qa-2026-10-27.txt` | Certificación OpenSSL de cifrado en tránsito en Ingress Nginx (RSA 4096-bit, TLS 1.2/1.3) | **SCRUM-49**, **RNF-02** |
| `tls-entrada-qa-2026-10-27.txt` | Verificación de suites criptográficas activas en Nginx Ingress | **SCRUM-49**, **RNF-02** |
