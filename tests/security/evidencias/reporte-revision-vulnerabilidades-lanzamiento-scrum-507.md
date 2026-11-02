# Reporte de Revisión de Vulnerabilidades y Seguridad Previo al Lanzamiento

**Código del Documento:** `SEC-REV-PRELAUNCH-SCRUM-507`  
**Versión:** `2.0 Revisada y Conciliada`  
**Fecha de Emisión:** 31 de octubre de 2026  
**Responsable:** Katherine Bravo (`ka.bravo@javeriana.edu.co`) — QA Lead  
**Trazabilidad Jira:** Subtarea [SCRUM-507](https://arqui-202630.atlassian.net/browse/SCRUM-507) | Historia Padre [SCRUM-49](https://arqui-202630.atlassian.net/browse/SCRUM-49) (*Cifrado de datos sensibles en tránsito y en reposo* — Responsable: Sebastian Sanchez Olaya)  
**Ambiente Auditado:** QA Desplegado (`https://qa.quickpatch.internal` / `10.43.100.168`), ambiente candidato a promoción a Producción (Sprint 5)  
**Estándares de Referencia:** OWASP Top 10 API Security (2023), PCI-DSS v4.0 (Requisitos 3.4 y 3.5), RF-29, RNF-01, RNF-02, Compuerta de Calidad K2 (Gate 2/3)

---

## 1. Resumen Ejecutivo y Matriz de Compuerta

Conforme a los criterios de aceptación de la historia **SCRUM-49** y la subtarea **SCRUM-507**, se ejecutó la auditoría formal de seguridad y revisión de vulnerabilidades sobre el entorno integrado de QA previo a su promoción a Producción:

| Componente Auditado | Herramienta / Método | Criterio de Aceptación | Resultado Obtenido | Estado de Compuerta |
|---|---|---|---|:---:|
| **Cifrado en Tránsito (TLS)** | OpenSSL 3.5.5 `s_client` | HTTPS/TLS obligatorio; rechazo de HTTP plano y suites inseguras | TLSv1.2 y TLSv1.3 activos (`ECDHE-RSA-AES256-GCM-SHA384` y `TLS_AES_256_GCM_SHA384`). Tráfico HTTP plano redirigido a HTTPS | **CUMPLE** |
| **Privacidad de Pagos (PCI-DSS)** | `tests/security/pci_dss_scanner.py` (Luhn Mod 10 + CVV Regex) | 0 números de tarjeta (PAN) y 0 códigos de seguridad (CVV) en BD y logs | **0 violaciones** sobre 100 registros en 5 streams auditados en Loki (`service-request`, `matching`, `communication`, `coredns`) | **CUMPLE** |
| **Vulnerabilidades Web/API (DAST)** | OWASP ZAP Baseline (`ghcr.io/zaproxy/zaproxy:stable`) | Sin hallazgos de severidad Alta o Crítica en endpoints públicos | **0 hallazgos Altos/Críticos**; 1 hallazgo Medio (CSP en API REST, regla `IGNORE`) y 1 Bajo (HSTS en raíz) | **CUMPLE** |
| **Protección de Credenciales** | Inspección de esquema Identity y logs | Contraseñas con hashing robusto (PBKDF2/BCrypt); 0 credenciales en texto plano | Verificado: campos `password_hash` con salt en Identity Service; cero contraseñas en logs | **CUMPLE** |
| **Cifrado en Reposo (QA y Producción)** | k3s `encryption-config.yaml` / PostgreSQL VM4/VM5 | Secretos y bases cifrados en reposo, o decisión y riesgo documentado | En QA: Secret de k3s cifrados (PR #210). En Producción: pendiente de ejecución en despliegue final (SCRUM-518) | **PLAN DE CIERRE** *(Pendiente Prod)* |

**Dictamen de Aseguramiento de Calidad:** **COMPUERTA DE SEGURIDAD APROBADA CONDICIONADA AL PLAN DE CIERRE (GO FOR RELEASE)**. No existen vulnerabilidades de severidad alta o crítica bloqueantes para la promoción del MVP a Producción.

---

## 2. Detalle de Pruebas y Evidencias Técnicas

### 2.1 Cifrado en Tránsito y Configuración TLS (RNF-02, INF-013)
- **Evidencias en el repositorio:** `tests/security/evidencias/tls-ingress-qa-2026-10-27.txt` y `tests/security/evidencias/tls-entrada-qa-2026-10-27.txt`.
- **Inspección técnica:**
  - El punto de entrada en VM1 (`10.43.100.168:443`, Nginx Ingress) expone exclusivamente certificados digitales con clave RSA de 4096 bits (`CN=quickpatch.internal`, SHA-256).
  - Cifrados negociados:
    - TLS 1.2: `ECDHE-RSA-AES256-GCM-SHA384`
    - TLS 1.3: `TLS_AES_256_GCM_SHA384`
  - Se confirmó que cualquier solicitud HTTP entrante por puerto 80 es redirigida mediante HTTP 301/308 permanente hacia HTTPS, garantizando la confidencialidad de tokens JWT, parámetros de geocodificación y datos de servicios en tránsito.

### 2.2 Auditoría PCI-DSS sobre Registros de Logs (Req 3.4/3.5, PAY-002, K2)
- **Herramienta:** `tests/security/pci_dss_scanner.py` ejecutado a través de `tests/security/run-pci-dss-suite.py`.
- **Evidencia en el repositorio:** `tests/security/evidencias/pci-dss-loki-qa-2026-10-18.txt` y archivo de exportación `tests/security/evidencias/loki_qa_k3s.json`.
- **Cifras exactas auditadas:**
  - Streams evaluados: **5 streams de logs** centralizados en Loki de QA (VM1).
  - Líneas de log inspeccionadas: **100 registros completos** correspondientes a los servicios transaccionales del flujo crítico: `service-request`, `matching`, `communication` y el resolvedor interno `coredns`.
  - **Violaciones detectadas:** **0 (CERO)** números de tarjeta (PAN) y **0 (CERO)** códigos de seguridad (CVV) en texto plano.
- **Validación de robustez del escáner:**
  - 6 marcas de tarjeta válidas detectadas con 100% de efectividad (Visa 16/13 dígitos, Mastercard rangos 51-55 y 2221-2720, Amex 15 dígitos, Discover 16 dígitos).
  - 16 pruebas negativas extremas aprobadas sin falsos positivos (números con suma de verificación inválida, teléfonos celulares colombianos con prefijo `+57`, cédulas de ciudadanía, NITs con dígito de verificación, UUIDs de tenants y categorías, correlation IDs, montos COP, tokens de pasarela, inyecciones SQL/XSS y caracteres emoji).
  - Se confirmó que la aplicación móvil y la pasarela simulada (ADR-009) transmiten exclusivamente tokens opacos (`tok_test_...`), asegurando que ningún PAN toque el backend ni quede expuesto en los logs.

### 2.3 Escaneo Dinámico de Vulnerabilidades DAST (OWASP ZAP Baseline)
- **Herramienta:** OWASP ZAP Baseline Scanner (`zap-baseline.py` contenedor `ghcr.io/zaproxy/zaproxy:stable`) sobre `https://qa.quickpatch.internal`.
- **Reglas:** `tests/security/zap-baseline.conf`.
- **Evidencias en el repositorio:**
  - Reporte consolidado de la corrida del 31 de octubre: `tests/security/evidencias/zap-dast-baseline-qa-2026-10-31.txt`.
  - Antecedente de corrida previa: `tests/security/evidencias/zap-dast-baseline-qa-2026-10-18.txt`.
  - Archivos estructurados del escáner: `tests/security/evidencias/zap.json` y `tests/security/evidencias/zap.html`.
- **Cifras exactas del escaneo:**
  - Reglas evaluadas por el escáner: **61 reglas de seguridad pasiva y baseline**.
  - Reglas aprobadas (**PASS**): **59 reglas (96.7%)**, incluyendo ausencia de inyección SQL (40018), XSS reflejado/almacenado (40026), Command Injection (90020), divulgación de código fuente (10045) y divulgación de información sensible.
  - Hallazgos Críticos / Altos (**FAIL-NEW**): **0 (CERO)**.
  - Hallazgos Medios (**Medium**): **1 hallazgo** -> *Content Security Policy (CSP) Header Not Set* (Plugin 10038, 3 instancias en `https://qa.quickpatch.internal`, `/robots.txt`, `/sitemap.xml`).
    - *Tratamiento:* Regla catalogada formalmente como `IGNORE` en `tests/security/zap-baseline.conf`. CSP aplica a renderizado HTML en navegadores; los servicios de QUICKPATCH son APIs REST JSON sin estado consumidas con Bearer JWT.
  - Hallazgos Bajos (**Low**): **1 hallazgo** -> *Strict-Transport-Security Header Not Set* (Plugin 10035, 3 instancias en la raíz `/` cuando responde 403 al no existir index HTML).
    - *Tratamiento:* Advertencia informativa sin impacto en la seguridad de la API (tráfico forzado a TLS 1.3). Se recomienda incorporar el flag `always` en el bloque Nginx de Producción.

---

## 3. Plan de Cierre para Producción (Cifrado en Reposo)

En atención a la observación técnica de DevOps, se documenta el estado diferencial entre QA y Producción y el plan de cierre requerido antes del lanzamiento final:

| Componente | Estado en QA | Estado en Producción | Plan de Cierre / Mitigación para Producción | HU / Tarea Responsable |
|---|---|---|---|:---:|
| **Secret de k3s en Reposo** | Cifrado activo mediante `encryption-config.yaml` | **Pendiente** | Aplicar el manifiesto de cifrado de secretos en el clúster k3s de Producción (VM3) durante el aprovisionamiento | SCRUM-518 / SCRUM-49 |
| **PostgreSQL en Reposo** | Datos en volumen de VM5 sin cifrado de bloque | **Pendiente** (VM4) | Decisión documentada en INFRASTRUCTURE.md §10.3: el laboratorio opera en red privada aislada (10.43.0.0/16). Riesgo asumido para el MVP | SCRUM-518 |
| **Garage S3 en Reposo** | Almacenamiento en VM7 sin cifrado del backend | **Pendiente** (VM6) | Acceso restringido por credenciales secretas de S3 administradas vía vault de Ansible | SCRUM-518 |
| **Respaldos de Base de Datos** | Scripts de backup en VM1 | **Pendiente** | Implementar cifrado GPG en el script de respaldo automatizado antes de transferir fuera de VM4 | Post-MVP / DevOps |

---

## 4. Conclusión y Recomendación

1. **Subtarea SCRUM-507:** Se da por cumplida la revisión formal de vulnerabilidades con las cifras exactas corregidas, la evidencia del escaneo ZAP actualizada al 31 de octubre de 2026 y la matriz de compuerta conciliada.
2. **Historia SCRUM-49:** DevOps (Sebastian Sanchez Olaya) cuenta con la certificación formal requerida para proceder con el cierre de la historia en Jira, manteniendo el plan de cierre documentado para el despliegue en Producción.
