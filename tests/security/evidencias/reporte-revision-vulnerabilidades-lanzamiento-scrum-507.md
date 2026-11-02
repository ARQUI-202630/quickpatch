# Reporte de Revisión de Vulnerabilidades y Seguridad Previo al Lanzamiento

**Código del Documento:** `SEC-REV-PRELAUNCH-SCRUM-507`  
**Versión:** `2.1 Evidencia de CI reemplazada (corrida 41168063519)`  
**Fecha de Emisión:** 2 de noviembre de 2026  
**Responsable:** Katherine Bravo (`ka.bravo@javeriana.edu.co`) — QA Lead  
**Trazabilidad Jira:** Subtarea [SCRUM-507](https://jorgefortich3.atlassian.net/browse/SCRUM-507) | Historia Padre [SCRUM-49](https://jorgefortich3.atlassian.net/browse/SCRUM-49) (*Cifrado de datos sensibles en tránsito y en reposo* — Responsable: Sebastian Sanchez Olaya)  
**Ambiente Auditado:** QA Desplegado (`https://qa.quickpatch.internal` / `10.43.100.168`), ambiente candidato a promoción a Producción (Sprint 5)  
**Estándares de Referencia:** OWASP Top 10 API Security (2023), PCI-DSS v4.0 (Requisitos 3.4 y 3.5), RF-29, RNF-01, RNF-02, Compuerta de Calidad K2 (Gate 2/3)

---

## 1. Resumen Ejecutivo y Matriz de Compuerta

Conforme a los criterios de aceptación de la historia **SCRUM-49** y la subtarea **SCRUM-507**, se ejecutó la auditoría formal de seguridad y revisión de vulnerabilidades sobre el entorno integrado de QA previo a su promoción a Producción:

| Componente Auditado | Herramienta / Método | Criterio de Aceptación | Resultado Obtenido | Estado de Compuerta |
|---|---|---|---|:---:|
| **Cifrado en Tránsito (TLS)** | OpenSSL 3.5.5 `s_client` | HTTPS/TLS obligatorio; rechazo de HTTP plano y suites inseguras | TLSv1.2 y TLSv1.3 activos (`ECDHE-RSA-AES256-GCM-SHA384` y `TLS_AES_256_GCM_SHA384`). HTTP plano rechazado: el puerto 80 de VM1 no escucha | **CUMPLE** |
| **Privacidad de Pagos (PCI-DSS)** | Paso PCI-DSS del job «Seguridad» en CI (Luhn por marca + expresión de CVV) | 0 números de tarjeta (PAN) y 0 códigos de seguridad (CVV) en los logs | **0 hallazgos** en 5.000 líneas de logs de QA (`{vm="vm2"}`, últimas 24 h, con Payments desplegado), corrida de CI 41168063519 del 30 de octubre | **CUMPLE** |
| **Vulnerabilidades Web (DAST pasivo)** | OWASP ZAP Baseline (`ghcr.io/zaproxy/zaproxy:stable`), corrida de CI 41168063519 | Sin hallazgos de severidad Alta o Crítica | **0 FAIL**; 55 PASS, 4 WARN (cache-control, X-Content-Type-Options, HSTS y 10109) y 2 IGNORE (anti-clickjacking y CSP). Escaneo pasivo sobre la raíz y archivos estáticos: **no cubre el API** | **CUMPLE con alcance limitado** |
| **Protección de Credenciales** | Inspección del código de Identity | Contraseñas con hashing robusto (PBKDF2/BCrypt); 0 credenciales en texto plano | BCrypt con factor de trabajo 12 (`appsettings.json`), solo se guarda `password_hash`. Evidencia: `credenciales-bcrypt-identity-2026-11-02.txt` | **CUMPLE** *(por código)* |
| **Cifrado en Reposo (QA y Producción)** | k3s `secrets-encrypt status` / PostgreSQL VM4/VM5 | Secretos y bases cifrados en reposo, o decisión y riesgo documentado | En QA: 14 de 14 `Secret` de k3s cifrados con AES-CBC (PR #210). En Producción: pendiente (SCRUM-518). Evidencia: `cifrado-reposo-k3s-qa-2026-10-30.txt` | **PLAN DE CIERRE** *(Pendiente Prod)* |

**Dictamen de Aseguramiento de Calidad:** **COMPUERTA DE SEGURIDAD APROBADA CONDICIONADA AL PLAN DE CIERRE (GO FOR RELEASE)**. No se encontraron vulnerabilidades de severidad alta o crítica en lo revisado. El escaneo DAST fue pasivo y no tocó el API, así que no reemplaza una prueba activa sobre los endpoints REST.

---

## 2. Detalle de Pruebas y Evidencias Técnicas

### 2.1 Cifrado en Tránsito y Configuración TLS (RNF-02, INF-013)
- **Evidencias en el repositorio:** `tests/security/evidencias/tls-ingress-qa-2026-10-27.txt` y `tests/security/evidencias/tls-entrada-qa-2026-10-27.txt`.
- **Inspección técnica:**
  - El punto de entrada en VM1 (`10.43.100.168:443`, Nginx Ingress) expone exclusivamente certificados digitales con clave RSA de 4096 bits (`CN=quickpatch.internal`, SHA-256).
  - Cifrados negociados:
    - TLS 1.2: `ECDHE-RSA-AES256-GCM-SHA384`
    - TLS 1.3: `TLS_AES_256_GCM_SHA384`
  - El puerto 80 de VM1 no escucha y `ufw` solo abre el 443, por lo que no se acepta tráfico HTTP plano (`docs/infrastructure/INFRASTRUCTURE.md` §10.5). Esto garantiza la confidencialidad de tokens JWT, parámetros de geocodificación y datos de servicios en tránsito.

### 2.2 Auditoría PCI-DSS sobre Registros de Logs (Req 3.4/3.5, PAY-002, K2)
- **Corrida citada:** CI «Pruebas de sistema», corrida [41168063519](https://github.com/ARQUI-202630/quickpatch/actions/runs/41168063519), job «Seguridad (OWASP ZAP y PCI-DSS)», 30 de octubre de 2026 a las 23:28 (hora de Bogotá), con Payments ya desplegado en QA.
- **Evidencia en el repositorio:** `tests/security/evidencias/zap-pci-ci-qa-2026-10-30-run-41168063519.txt` (sección 2, línea copiada del log del job).
- **Alcance:** consulta a Loki de QA `{vm="vm2"}` (todos los logs del clúster k3s), últimas 24 horas, límite de 5.000 líneas.
- **Resultado:** `Líneas revisadas: 5000. Hallazgos: 0.` Ningún número de tarjeta (Visa, Mastercard, Amex o Discover con dígito Luhn válido) ni CVV/CVC en texto plano.
- **Antecedente:** la corrida local del 18 de octubre (`pci-dss-loki-qa-2026-10-18.txt`) revisó 100 líneas, antes del despliegue de Payments; se conserva solo como referencia.
- **Robustez del escáner:** `tests/security/run-pci-dss-suite.py` valida el detector con las marcas de tarjeta y con casos negativos (teléfonos, cédulas, NIT, UUID, montos), sin falsos positivos.

### 2.3 Escaneo Dinámico de Vulnerabilidades DAST (OWASP ZAP Baseline)
- **Corrida citada:** la misma corrida de CI 41168063519 (paso ZAP, 30 de octubre a las 23:27, hora de Bogotá) sobre `https://qa.quickpatch.internal`, con las reglas de `tests/security/zap-baseline.conf`.
- **Evidencias en el repositorio:**
  - `tests/security/evidencias/zap-pci-ci-qa-2026-10-30-run-41168063519.txt` (sección 1): las 63 líneas del resultado de ZAP copiadas del log del job.
  - `tests/security/evidencias/zap-dast-baseline-qa-2026-10-30.html`: el reporte HTML publicado como artefacto `reporte-zap` de esa corrida.
  - Antecedente: `tests/security/evidencias/zap-dast-baseline-qa-2026-10-18.txt` (corrida del 18 de octubre).
- **Alcance (importante):** ZAP baseline es un escaneo **pasivo**: solo observa las respuestas, no envía ataques (no hay reglas activas de inyección SQL ni XSS). Según el reporte, recorrió la raíz y los archivos `/robots.txt`, `/sitemap.xml` y `/favicon.ico` (ZAP cuenta 8 URLs). **No recorrió los endpoints del API REST**, así que este resultado no certifica el API.
- **Resultado (`FAIL-NEW: 0, WARN-NEW: 4, IGNORE: 2, PASS: 55`):**
  - **FAIL:** 0.
  - **WARN (4):** *Re-examine Cache-control Directives* [10015] x4, *X-Content-Type-Options Header Missing* [10021] x5, *Strict-Transport-Security Header Not Set* [10035] x5 y *Modern Web Application* [10109] x4.
  - **IGNORE (2), según `zap-baseline.conf`:** *Missing Anti-clickjacking Header* [10020] x4 y *Content Security Policy (CSP) Header Not Set* [10038] x4. CSP no se evaluó: está en IGNORE.
  - **PASS:** 55 reglas, listadas en la evidencia.
- **Tratamiento de las alertas:**
  - **HSTS [10035]:** la cabecera `Strict-Transport-Security` **no está configurada** en el Ingress. Hay que configurarla en Nginx de QA y de Producción (por ejemplo `max-age=31536000`), no basta con ajustar un bloque existente. Queda abierta y se registra como defecto.
  - **X-Content-Type-Options [10021]:** falta `nosniff` en las respuestas revisadas; se corrige en la misma configuración del Ingress.
  - **Cache-control [10015] y 10109:** informativas en la raíz estática; se revisan junto con las cabeceras anteriores.

---

## 3. Plan de Cierre para Producción (Cifrado en Reposo)

En atención a la observación técnica de DevOps, se documenta el estado diferencial entre QA y Producción y el plan de cierre requerido antes del lanzamiento final:

| Componente | Estado en QA | Estado en Producción | Plan de Cierre / Mitigación para Producción | HU / Tarea Responsable |
|---|---|---|---|:---:|
| **Secret de k3s en Reposo** | Cifrado activo desde el 30 de octubre (AES-CBC, 14 de 14 `Secret`) con `playbooks/cifrar-secretos-k3s.yml` | **Pendiente** | Ejecutar `playbooks/cifrar-secretos-k3s.yml` en el clúster k3s de Producción (VM3) | SCRUM-518 / SCRUM-49 |
| **PostgreSQL en Reposo** | Datos en volumen de VM5 sin cifrado de bloque | **Pendiente** (VM4) | Decisión documentada en `docs/infrastructure/INFRASTRUCTURE.md` §10.5: el laboratorio opera en red privada aislada (10.43.0.0/16). Riesgo asumido para el MVP | SCRUM-518 |
| **Garage S3 en Reposo** | Almacenamiento en VM7 sin cifrado del backend | **Pendiente** (VM6) | Acceso restringido por credenciales secretas de S3 administradas vía vault de Ansible | SCRUM-518 |
| **Respaldos de Base de Datos** | `pg_dump -Fc` sin cifrar en el disco de VM4 y subido a Garage por HTTP (`pg-backup.sh.j2`) | **Pendiente** | Cifrar el respaldo (`age` o GPG, con la llave en el vault) antes de subirlo a Garage | Post-MVP / DevOps |

---

## 4. Conclusión y Recomendación

1. **Subtarea SCRUM-507:** La revisión queda documentada con la evidencia real de la corrida de CI 41168063519 (ZAP pasivo y PCI-DSS sobre 5.000 líneas), sin hallazgos altos ni críticos. Quedan abiertas las cabeceras HSTS y X-Content-Type-Options del Ingress, y falta un escaneo activo sobre el API.
2. **Historia SCRUM-49:** El cierre lo decide DevOps (Sebastian Sanchez Olaya) con esta evidencia y con el plan de cierre de la sección 3 para Producción.
