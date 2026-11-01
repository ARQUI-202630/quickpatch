# Reporte de Revisión de Vulnerabilidades y Seguridad Previo al Lanzamiento

**Código del Documento:** `SEC-REV-PRELAUNCH-SCRUM-507`  
**Versión:** `1.0 Final`  
**Fecha de Emisión:** 31 de octubre de 2026  
**Responsable:** Katherine Bravo (`ka.bravo@javeriana.edu.co`) — QA Lead  
**Trazabilidad Jira:** Subtarea [SCRUM-507](https://arqui-202630.atlassian.net/browse/SCRUM-507) | Historia Padre [SCRUM-49](https://arqui-202630.atlassian.net/browse/SCRUM-49) (*Cifrado de datos sensibles en tránsito y en reposo* — Responsable: Sebastian Sanchez Olaya)  
**Ambiente Auditado:** QA Desplegado (`https://qa.quickpatch.internal` / `10.43.100.168`), ambiente candidato a promoción a Producción (Sprint 5)  
**Estándares de Referencia:** OWASP Top 10 API Security (2023), PCI-DSS v4.0 (Requisitos 3.4 y 3.5), RF-29, RNF-01, RNF-02, Compuerta de Calidad K2 (Gate 2/3)

---

## 1. Resumen Ejecutivo

Conforme a los criterios de aceptación de la historia **SCRUM-49** y la subtarea **SCRUM-507**, se ejecutó la auditoría formal de seguridad y revisión de vulnerabilidades sobre el entorno integrado de QA previo a su promoción a Producción.

| Componente Auditado | Herramienta / Método | Criterio de Aceptación | Resultado Obtenido | Estado |
|---|---|---|---|:---:|
| **Cifrado en Tránsito (TLS)** | OpenSSL 3.5.5 `s_client` | HTTPS/TLS obligatorio; rechazo de HTTP plano y suites inseguras | TLSv1.2 y TLSv1.3 activos con cifrado AES-256-GCM. 0 tráfico en texto plano | **CUMPLE** |
| **Privacidad de Pagos (PCI-DSS)** | `tests/security/pci_dss_scanner.py` (Luhn Mod 10 + CVV Regex) | 0 números de tarjeta (PAN) y 0 códigos de seguridad (CVV) en BD y logs | **0 violaciones** sobre 2.649 registros auditados en Loki | **CUMPLE** |
| **Vulnerabilidades Web/API (DAST)** | OWASP ZAP Baseline (`ghcr.io/zaproxy/zaproxy:stable`) | Sin hallazgos de severidad Alta o Crítica en endpoints públicos | **0 hallazgos Altos/Críticos**; 2 advertencias informativas documentadas | **CUMPLE** |
| **Protección de Credenciales** | Inspección de esquema Identity y logs | Contraseñas con hashing robusto (PBKDF2/BCrypt); 0 credenciales en texto plano | Verificado: campos `password_hash` con salt; cero contraseñas en logs | **CUMPLE** |
| **Cifrado de Secretos en Reposo** | k3s `encryption-config.yaml` / PostgreSQL RLS | Secretos de Kubernetes cifrados en reposo; aislamiento por tenant | Verificado en QA (SCRUM-49 / PR #210) y RLS activo en PostgreSQL | **CUMPLE** |

**Dictamen de Aseguramiento de Calidad:** **COMPUERTA DE SEGURIDAD APROBADA (GO FOR RELEASE)**. No existen vulnerabilidades de severidad alta o crítica que bloqueen la promoción a Producción ni el cierre de la historia **SCRUM-49**.

---

## 2. Detalle de Pruebas y Evidencias

### 2.1 Cifrado en Tránsito y Configuración TLS (RNF-02, INF-013)
- **Evidencias de soporte:** [tls-ingress-qa-2026-10-27.txt](file:///c:/Users/kathe/OneDrive/Escritorio/ARQUI/Arquitectura/quickpatch/tests/security/evidencias/tls-ingress-qa-2026-10-27.txt) y [tls-entrada-qa-2026-10-27.txt](file:///c:/Users/kathe/OneDrive/Escritorio/ARQUI/Arquitectura/quickpatch/tests/security/evidencias/tls-entrada-qa-2026-10-27.txt).
- **Inspección técnica:**
  - El punto de entrada en VM1 (`10.43.100.168:443`, Nginx Ingress) expone exclusivamente certificados digitales con clave RSA de 4096 bits (`CN=quickpatch.internal`, SHA-256).
  - Cifrados negociados:
    - TLS 1.2: `ECDHE-RSA-AES256-GCM-SHA384`
    - TLS 1.3: `TLS_AES_256_GCM_SHA384`
  - Se confirmó que cualquier solicitud HTTP entrante por puerto 80 es redirigida mediante HTTP 301/308 permanente hacia HTTPS, garantizando la confidencialidad de tokens JWT, parámetros de geocodificación y datos de servicios en tránsito.

### 2.2 Auditoría PCI-DSS sobre Registros de Logs (Req 3.4/3.5, PAY-002, K2)
- **Herramienta:** [pci_dss_scanner.py](file:///c:/Users/kathe/OneDrive/Escritorio/ARQUI/Arquitectura/quickpatch/tests/security/pci_dss_scanner.py) ejecutado a través de [run-pci-dss-suite.py](file:///c:/Users/kathe/OneDrive/Escritorio/ARQUI/Arquitectura/quickpatch/tests/security/run-pci-dss-suite.py).
- **Evidencia de soporte:** [pci-dss-loki-qa-2026-10-18.txt](file:///c:/Users/kathe/OneDrive/Escritorio/ARQUI/Arquitectura/quickpatch/tests/security/evidencias/pci-dss-loki-qa-2026-10-18.txt).
- **Resultados de validación unitaria y de robustez:**
  - 6 marcas de tarjeta válidas detectadas con 100% de efectividad (Visa 16/13 dígitos, Mastercard rangos 51-55 y 2221-2720, Amex 15 dígitos, Discover 16 dígitos).
  - 16 pruebas negativas extremas aprobadas sin falsos positivos (números con suma de verificación inválida, teléfonos celulares colombianos con prefijo `+57`, cédulas de ciudadanía, NITs con dígito de verificación, UUIDs de tenants y categorías, correlation IDs, montos COP, tokens de pasarela, inyecciones SQL/XSS y caracteres emoji).
  - Reglas de CVV verificadas: detección precisa de palabras clave (`cvv`, `cvc`, `security_code`) sin confundir métricas de duración ni códigos de estado HTTP.
- **Resultado del escaneo sobre QA:**
  - Archivo de logs analizado: `tests/security/evidencias/loki_qa_k3s.json` (recopilación de trazas de API Gateway, Payments Service, Identity Service y Service Request).
  - **Violaciones detectadas:** **0 (CERO)**.
  - La aplicación móvil tokeniza la información en origen mediante la pasarela simulada/mock (ADR-009) transmitiendo únicamente tokens opacos (`tok_test_...`), asegurando que ningún PAN ni código de seguridad toque el backend ni quede expuesto en el almacenamiento centralizado de Loki.

### 2.3 Escaneo Dinámico de Vulnerabilidades DAST (OWASP ZAP Baseline)
- **Herramienta:** OWASP ZAP Baseline Scanner (`zap-baseline.py`) sobre `https://qa.quickpatch.internal`.
- **Reglas:** [zap-baseline.conf](file:///c:/Users/kathe/OneDrive/Escritorio/ARQUI/Arquitectura/quickpatch/tests/security/zap-baseline.conf).
- **Evidencias de soporte:** [zap-dast-baseline-qa-2026-10-18.txt](file:///c:/Users/kathe/OneDrive/Escritorio/ARQUI/Arquitectura/quickpatch/tests/security/evidencias/zap-dast-baseline-qa-2026-10-18.txt), `zap.json` y `zap.html`.
- **Métricas del escaneo:**
  - Reglas evaluadas: 61 reglas pasivas y de línea base.
  - Reglas aprobadas (**PASS**): **59 reglas (96.7%)**, incluyendo ausencia de inyección SQL (40018), XSS reflejado/almacenado (40026), Command Injection (90020), divulgación de código fuente (10045) y divulgación de información sensible en URLs/headers.
  - Hallazgos Críticos / Altos (**FAIL**): **0 (CERO)**.
  - Hallazgos Medios: **0 (CERO)**.
  - Advertencias defensivas informativas (**WARN**): 2 hallazgos menores:
    1. *Missing Anti-clickjacking Header (10020)* en ciertas rutas REST API stateless: se descarta como riesgo para APIs JSON consumidas por apps móviles y clientes programáticos (mitigado por Bearer JWT y Content-Type estricto).
    2. *Content-Security-Policy (CSP) Header (10038)* en endpoints de salud: clasificado como advertencia informativa sin impacto operativo.

---

## 3. Conclusión y Recomendación de Cierre

1. **Cierre de SCRUM-507:** La subtarea cuenta con todas las evidencias de escaneo requeridas, confirmando ausencia de vulnerabilidades altas/críticas y pleno cumplimiento de las compuertas de seguridad.
2. **Desbloqueo de SCRUM-49:** El responsable de DevOps e Infraestructura (Sebastian Sanchez Olaya) queda habilitado para cerrar la historia **SCRUM-49** integrando este informe como evidencia formal de QA previa al despliegue en Producción.
