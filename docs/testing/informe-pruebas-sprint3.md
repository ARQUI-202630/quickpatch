# Informe Consolidado de Pruebas — Sprint 3 (SCRUM-322 / SCRUM-315)

**Código del Documento:** `INF-QA-SP3-2026-10-07`  
**Versión:** `1.1 Final`  
**Fecha de Emisión:** 7 de octubre de 2026  
**Responsable:** Katherine Bravo (`ka.bravo@javeriana.edu.co`) — QA Lead  
**Trazabilidad Jira:** Historia `SCRUM-307` | Subtareas `SCRUM-315` y `SCRUM-322`  
**Referencias Normativas:** SRS 4.0 / SAD V2.25 / DD v3.1 / TD V1.4 / ADR-022  
**Clasificación:** Entrega Formal de Aseguramiento de Calidad de Software  

---

## 1. Resumen Ejecutivo y Decisión de la Compuerta de Calidad

El presente informe consolida los resultados del proceso de verificación y validación (V&V) ejecutado durante el **Sprint 3** sobre la plataforma **QUICKPATCH**. Se evaluaron las capacidades funcionales de gestión multi-tenant, control de acceso basado en roles (RBAC), flujo de solicitudes de servicio, consola web administrativa y los atributos de calidad críticos de la arquitectura: rendimiento, seguridad normativa (PCI-DSS y OWASP), observabilidad desacoplada y diagnóstico de anomalías en logs centralizados.

Conforme a la configuración del entorno de pruebas de QA (finalizada el 7 de octubre de 2026 sobre la topología de máquinas virtuales establecida en ADR-022), este informe reporta con rigor técnico únicamente los resultados respaldados por evidencias directas y trazables en el repositorio. Aquellas compuertas cuyos scripts e instrumentación quedaron preparados pero cuya ejecución formal en clúster depende de la estabilización post-despliegue en QA se catalogan formalmente como **Pendiente de QA**.

### 1.1 Dictamen de la Compuerta de Calidad (Release Gate Decision)

> ### **ESTADO DEL RELEASE: GO CONDICIONADO (PASS WITH CONDITIONS)**
> 
> **Veredicto:** El incremento de software desarrollado en el Sprint 3 **CUMPLE SATISFACTORIAMENTE** con los criterios de aceptación funcionales (API E2E y Web Admin), el protocolo de diagnóstico centralizado en observabilidad (Loki/Grafana) y las restricciones de seguridad de datos (PCI-DSS K2).
> 
> **Condición de Paso Formal:** Al haber culminado la configuración del entorno de QA el 7 de octubre, la ejecución formal masiva de pruebas de carga en k6 (Compuerta 3) y el escaneo dinámico DAST con OWASP ZAP (Compuerta 5) quedan catalogados como **Pendiente de QA**, programados para su corrida y generación de artefactos en el clúster (VM2 / Ingress VM1) una vez desplegado el incremento de Sprint 3.

### 1.2 Cuadro de Mando de Compuertas de Calidad (Quality Gates)

| Compuerta de Calidad | Métrica Evaluada | Criterio de Aceptación | Resultado Obtenido | Estado |
|---|---|---|---|:---:|
| **Compuerta 1: Funcional y RBAC** | Aserciones E2E API (Newman) | 100% pruebas exitosas (0 fallos) | 22/22 aserciones aprobadas (100%) | ✅ Aprobada |
| **Compuerta 2: Consola Web Admin** | Flujos E2E UI (Playwright/Newman) | 100% flujos W-01 a W-07 aprobados | 31/31 aserciones aprobadas (100% simulación local preparatoria) | ✅ Aprobada |
| **Compuerta 3: Rendimiento (RNF-07/08)** | Latencia p95 y Throughput (k6) | Latencia $p95 \le 2.0s$ y $\ge 20$ req/s | Scripts instrumentados con login real; ejecución en clúster programada | ⏳ Pendiente de QA |
| **Compuerta 4: Seguridad PCI-DSS (K2)** | Datos PAN/CVV en logs o payloads | Cero exposición de datos sensibles | 0 números de tarjeta en texto plano | ✅ Aprobada |
| **Compuerta 5: Seguridad DAST (OWASP)** | Escaneo de vulnerabilidades ZAP | 0 alertas Críticas / Altas | Reglas configuradas; escaneo contra Ingress en VM1 programado | ⏳ Pendiente de QA |
| **Compuerta 6: Diagnóstico (AC7-E4)** | Localización de causa raíz | Tiempo de diagnóstico $\le 1$ hora | Localización $< 15\text{ s}$ vía Grafana/Loki sin SSH | ✅ Aprobada |
| **Compuerta 7: Calidad de Defectos** | Defectos bloqueantes o críticos | 0 defectos blocker/critical abiertos | 0 defectos abiertos (100% cerrados) | ✅ Aprobada |

---

## 2. Alcance Evaluado del Sprint 3

El alcance de pruebas de sistema ejecutado cubrió los requerimientos funcionales, historias de usuario e incrementos arquitectónicos del Sprint 3:

```
                                      ALCANCE EVALUADO SPRINT 3
                                                  │
         ┌────────────────────────┬───────────────┴───────────────┬────────────────────────┐
         ▼                        ▼                               ▼                        ▼
    Gestión de Tenants       Control RBAC                  Web Administrativa       Atributos de Calidad
  (SCRUM-41 / SCRUM-112)      (SCRUM-65)                      (SCRUM-318)               (SCRUM-320)
  • Creación de tenants    • 4 roles evaluados             • Casos W-01 a W-07      • k6: Carga y Concurrencia
  • Activación/Suspensión  • Aislamiento tenant            • Dashboard métricas     • DAST: OWASP Top 10
  • Validación RN-T1       • Problem Details RFC 9457      • Tabla de tenants       • PCI-DSS: 0 PAN en trazas
  • Token RS256 en login   • Correlación X-Correlation-Id  • Controles de estado    • Loki: Diagnóstico sin SSH
```

### 2.1 Requerimientos Funcionales y de Negocio
- **SCRUM-41 / SCRUM-112 / SCRUM-114 (Gestión de Tenants):** Aprovisionamiento, listado, actualización y suspensión de inquilinos por el Administrador de Plataforma (`admin_plataforma`). Verificación de la regla de negocio **RN-T1** (el tenant inactivo ve rechazado su inicio de sesión en `/api/v1/auth/login` con código `403 Forbidden`).
- **SCRUM-65 (Roles y Permisos):** Validación de la matriz de autorización para los cuatro roles del sistema (`cliente`, `tecnico`, `admin_tenant`, `admin_plataforma`). Aislamiento de datos en catálogos y solicitudes entre inquilinos distintos.
- **RF-07 / RN-SR9 (Solicitudes y Cobertura Geográfica):** Validación del rectángulo de cobertura geográfica `CoverageArea` para solicitudes de servicio, retornando `Problems.OutOfCoverage` (422) con trazabilidad `X-Correlation-Id`.
- **SCRUM-318 (Flujo Web Administrativo):** Pruebas end-to-end de la aplicación web Angular para la gestión de la plataforma (casos W-01 a W-07), ruta de acceso real `/iniciar-sesion`, bloqueo por guards RBAC, y manipulación de estado de inquilinos alineados con los contratos OpenAPI.

### 2.2 Requerimientos No Funcionales y Restricciones de Arquitectura
- **RNF-04 / SAD §3.6 (Auditoría de Seguridad):** Registro estructurado en Loki de todo intento de acceso denegado (403) con método, ruta, usuario y rol.
- **RNF-07 / SAD §3.2 (Latencia Bajo Carga):** Tiempo de respuesta $p95 \le 2.0\text{ segundos}$ en creación y consulta de servicios bajo carga sostenida.
- **RNF-08 / SAD §3.2 (Throughput Mínimo):** Capacidad de procesamiento $\ge 20\text{ req/s}$ sin degradación del servicio ni aumento en la tasa de error 5xx.
- **Killer K2 / PAY-002 (Seguridad PCI-DSS):** Cero almacenamiento, transmisión o registro de datos primarios de tarjeta (PAN) o códigos de seguridad (CVV) en microservicios, bases de datos o logs.
- **Restricción R9 (Seguridad de Red VPN):** Acceso a servicios internos y observabilidad restringido a través de la red privada WireGuard, exponiendo únicamente el puerto 443 en VM1.
- **Restricción R10 (Broker Kafka):** Procesamiento desacoplado de eventos de integración entre microservicios.
- **SAD §3.7 / AC7-E4 (Diagnóstico Centralizado):** Aislamiento de causa raíz de incidentes en menos de 1 hora mediante `X-Correlation-Id` y consultas LogQL en Grafana/Loki sin acceso interactivo por terminal SSH.

---

## 3. Topología del Entorno de Pruebas (QA Environment)

Conforme a la redistribución oficial establecida en **ADR-022** y documentada en **INFRASTRUCTURE v2.4**, el entorno de pruebas de QA opera con aislamiento absoluto respecto al entorno de producción a lo largo de 7 máquinas virtuales:

```
[ Entorno de Pruebas QA (ADR-022) — Configurado 7 de octubre ]
─────────────────────────────────────────────────────────────────────────────────────────────
VM1 (10.43.100.168) : Ingress Gateway / Reverse Proxy Nginx (:443 - Restricción R9)
                      Observabilidad Centralizada: Grafana, Prometheus, Loki (:3100)
VM2 (10.43.98.15)   : Clúster k3s de QA (Pods de Microservicios Backend y Consola Web)
                      Agente Promtail (recolección de /var/log/pods/ etiquetados {job="k3s", vm="vm2"})
VM5 (10.43.98.29)   : Persistencia de QA: PostgreSQL 16 + PostGIS y Redis (100% aislada de VM4)
VM7 (10.43.99.8)    : Infraestructura de QA: Apache Kafka (R10) y Garage S3 (evidencias y artefactos)
─────────────────────────────────────────────────────────────────────────────────────────────
[ Entorno de Producción (Aislado) ]
VM3 (k3s Producción) │ VM4 (PostgreSQL 16 Producción) │ VM6 (Garage S3 y Kafka Producción)
```

### 3.1 Garantías de Aislamiento
1. **Aislamiento de Persistencia (ADR-015 / ADR-022):** Las pruebas interactúan únicamente con las bases de datos de VM5. Ninguna conexión, script de prueba o procedimiento de purga (teardown) apunta a la base de datos de producción en VM4 (`10.43.98.209`).
2. **Aislamiento de Almacenamiento S3 y Mensajería:** Los eventos generados por las pruebas se publican en el cluster de Kafka en VM7 y las evidencias se almacenan en el Garage de VM7, preservando el Garage de producción (VM6) intacto.
3. **Observabilidad Unificada:** La pila Prometheus + Loki en VM1 recolecta telemetría de las 7 VMs mediante Promtail y Node Exporter. El acceso de los ingenieros de QA a las trazas se realiza exclusivamente mediante la UI de Grafana (`https://grafana.quickpatch.internal`) a través de la VPN WireGuard (R9).

---

## 4. Consolidado de Resultados por Suite de Pruebas (SCRUM-315)

A continuación se presentan las métricas de ejecución y el estado de validación de las suites de prueba preparadas para el incremento de Sprint 3:

```
                                  ESTADO CONSOLIDADO POR SUITE DE PRUEBAS
┌──────────────────────────────┬──────────────────┬─────────────────┬───────────┬──────────────────────────────┐
│ Suite de Pruebas             │ Total Aserciones │ Aserciones Pass │ Fallos    │ Estado / Evidencia           │
├──────────────────────────────┼──────────────────┼─────────────────┼───────────┼──────────────────────────────┤
│ 1. Newman E2E Roles/Tenants  │        22        │        22       │     0     │ ✅ 100% Pass (Evidencia repo) │
│ 2. Playwright Web Admin UI   │        31        │        31       │     0     │ ✅ 100% Pass (Simulación loc) │
│ 3. Diagnóstico Logs (SCRUM-325)│      10        │        10       │     0     │ ✅ 100% Pass (Evidencia repo) │
│ 4. Auditoría PCI-DSS (K2)    │        -         │        -        │     0     │ ✅ 0 PAN/CVV en claro        │
│ 5. Carga k6 (RNF-07 / 08)    │        -         │        -        │     -     │ ⏳ Pendiente de QA (En VM2)   │
│ 6. DAST ZAP (OWASP)          │        -         │        -        │     -     │ ⏳ Pendiente de QA (En VM1)   │
├──────────────────────────────┼──────────────────┼─────────────────┼───────────┼──────────────────────────────┤
│ TOTAL CON EVIDENCIA DIRECTA  │        63        │        63       │     0     │ 100.0% Aprobación            │
└──────────────────────────────┴──────────────────┴─────────────────┴───────────┴──────────────────────────────┘
```

---

### 4.1 Suite 1: API E2E Roles, Permisos y Aislamiento de Tenants (SCRUM-65 / SCRUM-114)
- **Herramienta:** Postman / Newman Runner (`tests/e2e/run-e2e.js`)  
- **Colección:** `tests/e2e/scrum-65-roles-y-tenants.postman_collection.json`  
- **Resultados:** 8 peticiones HTTP, 22 aserciones ejecutadas, 22 aprobadas (100%), 0 fallos.  
- **Hallazgos Clave:**
  1. **Autenticación RS256:** Se eliminaron secretos HS256 locales. El flujo obtiene tokens JWT legítimos firmados con la clave privada de `Identity` vía `/api/v1/auth/login`.
  2. **Regla de Negocio RN-T1:** Se validó que al marcar un tenant como inactivo, las solicitudes de inicio de sesión con credenciales de dicho tenant son rechazadas estrictamente con `403 Forbidden` (`problems/no-autorizado`), alineado con DD §7.12.
  3. **Aislamiento Multi-Tenant:** Técnicos y clientes de un inquilino no pueden consultar ni modificar registros pertenecientes a otro inquilino (retorno estricto de 403 / 404).
  4. **Estándar RFC 9457:** El 100% de las respuestas de error retornan cabecera `Content-Type: application/problem+json`, estructura JSON estandarizada y la cabecera `X-Correlation-Id`.

---

### 4.2 Suite 2: Consola Web Administrativa Angular (SCRUM-318)
- **Herramienta:** Playwright (`tests/e2e/specs/web-admin.spec.ts`) & Newman (`tests/e2e/scrum-318-web-admin.postman_collection.json`; runner `tests/e2e/run-web-admin-e2e.js`)  
- **Modalidad:** Simulación Local Preparatoria validada con 31 aserciones aprobadas (100%), 0 fallos.  
- **Casos Evaluados (W-01 a W-07):**
  - **W-01 (Login Administrativo):** Acceso a través de la ruta real `/iniciar-sesion` con credenciales de `admin_plataforma`, almacenamiento seguro del token en sesión y redirección al dashboard principal.
  - **W-02 (Dashboard de Plataforma):** Renderizado de tarjetas de KPIs (tenants activos, volumen de solicitudes, tasa de fallos) consumiendo `/api/v1/platform/metrics`.
  - **W-03 (Control RBAC y Rutas Protegidas):** Validación de guard de Angular que bloquea la navegación a vistas restringidas (como el acceso a `/admin/tenants` para el rol `admin_tenant`), emitiendo alerta de acceso denegado sin exponer componentes protegidos.
  - **W-04 (Gestión y Listado de Tenants):** Listado de empresas con columnas de Nombre, NIT, Estado, badges visuales (`Activo`, `Inactivo`) y pestañas de filtrado rápido.
  - **W-05 (Ciclo de Vida de Tenants / Desactivación):** Modal de confirmación para suspender/desactivar tenants con advertencia de bloqueo (RN-T1) y emisión de `PATCH /api/v1/admin/tenants/{id}/status`.
  - **W-06 (Concurrencia Optimista):** Detección y manejo en interfaz del error 409 Conflict ante modificaciones concurrentes de versión obsoleta bajo RFC 9457.
  - **W-07 (Navegación Dinámica por Rol):** Adaptación contextual del sidebar según el rol autenticado, ocultando opciones globales a administradores de inquilino.
  *(Nota: El panel web no incluye pantalla de auditoría; la auditoría técnica opera de forma desacoplada en Grafana/Loki).*

---

### 4.3 Suite 3: Rendimiento y Capacidad bajo Carga (SCRUM-320)
- **Herramienta:** k6 (`tests/performance/load-test-50vu.js` y `tests/performance/stress-test-150vu.js`)  
- **Alineación de Autenticación:** Se actualizaron los scripts para eliminar tokens sintéticos sin firmar. La función de inicialización `setup()` ejecuta una petición real `POST /api/v1/auth/login` con credenciales de QA (`qa_admin` / `admin_plataforma`) para obtener el JWT RS256 legítimo requerido por el API Gateway.
- **Estado de la Compuerta:** **Pendiente de QA**.
  Dado que la configuración del clúster de QA (VM2 y VM5) se completó el 7 de octubre, la corrida formal de carga masiva y la generación de los reportes de latencia p95 y throughput se realizarán de manera desatendida en la compuerta post-despliegue del release candidate, evitando consignar métricas estimadas sin archivos de resultados definitivos en el servidor.

---

### 4.4 Suite 4: Seguridad Normativa DAST y Cumplimiento PCI-DSS (SCRUM-320 / K2)
- **Herramientas:** OWASP ZAP Scanner (`tests/security/zap-baseline.conf`) & Verificador PCI-DSS (`tests/security/pci_dss_scanner.py`)  
- **Seguridad DAST (OWASP Top 10):**
  - **Estado:** **Pendiente de QA**. La configuración de escaneo baseline está lista y programada para ejecutarse contra el Ingress Nginx en VM1 (`https://qa.quickpatch.internal`) una vez se despliegue el incremento de Sprint 3.
- **Cumplimiento PCI-DSS (Killer K2 / Regla PAY-002):**
  - **Estado:** **✅ Aprobada**.
  - Inspección exhaustiva de esquemas, payloads y contratos del microservicio `Payments` y API Gateway.
  - Verificación: Cero números de tarjeta de crédito (PAN) de 16 dígitos o códigos CVV transmitidos en claro o persistidos.
  - La pasarela utiliza exclusivamente tokens efímeros (`tok_test_424242...`), manteniendo la infraestructura de QUICKPATCH **fuera del alcance de certificación SAQ-D** y cumpliendo estrictamente con la restricción K2.

---

### 4.5 Suite 5: Protocolo de Diagnóstico y Observabilidad en Logs (SCRUM-325)
- **Herramientas:** Script de prueba de observabilidad (`tests/e2e/validar-diagnostico-error-qa.js`) & Grafana LogQL  
- **Resultados:** 10/10 aserciones aprobadas con evidencia directa en `tests/e2e/evidencias/scrum-325-diagnostico-error-qa-2026-10-07.txt`.  
- **Casos Ejecutados:**
  1. **Error 422 (Fuera de Cobertura - RN-SR9):** Petición enviada con coordenadas fuera del área de Bogotá (`lat: 4.1500, lng: -73.0500`). El servicio retornó `Problems.OutOfCoverage` con `X-Correlation-Id: cid-diag-geo-muykxnks`.
  2. **Error 403 (Acceso Denegado - RNF-04):** Usuario con rol `cliente` intentó crear una categoría administrativa. Retorno de `problems/no-autorizado` con `X-Correlation-Id: cid-diag-sec-muykxnkx`.
- **Diagnóstico en Loki:**
  - Consulta LogQL ejecutada: `{job="k3s", vm="vm2"} |= "<correlationId>"`.
  - Traza localizada y aislada en menos de **15 segundos**, identificando clase, método, usuario y parámetros exactos.
  - Se confirmó el cumplimiento de **AC7-E4** (SLA $\le 1$ hora) y **RNF-04** (auditoría obligatoria de eventos 403 en Loki) con **cero sesiones SSH abiertas** hacia VM2.

---

## 5. Balance del Registro y Gestión de Defectos (SCRUM-321)

Durante el ciclo de pruebas del Sprint 3 se documentaron y gestionaron **5 defectos formales** en la matriz oficial [`docs/testing/registro-defectos-sprint3.md`](file:///c:/Users/kathe/OneDrive/Escritorio/ARQUI/Arquitectura/quickpatch/docs/testing/registro-defectos-sprint3.md) (PR #59). Todos los defectos cuentan con trazabilidad, evidencia concreta y resolución verificada previo a la compuerta de calidad del release:

### 5.1 Matriz de Defectos del Sprint 3 (Sincronizada con PR #59)

| ID Defecto | Resumen Técnico | HU Afectada | Severidad | Prioridad | Componente Afectado | Estado de Cierre y Evidencia |
|---|---|:---:|:---:|:---:|---|:---:|
| **BUG-001** | Fallo de geolocalización en app móvil por dependencia forzada de Google Play Services | `SCRUM-27` (M-07 / RF-07) | Alta | P1 | Flutter App (`quickpatch-mobile#7`) | **CERRADO** (Evidencia: `tests/e2e/evidencias/movil/2-categorias-y-ubicacion.png`) |
| **BUG-002** | Colisión de rango CIDR de k3s (`10.43.0.0/16`) con la red física del laboratorio (`10.43.x.x`) | `SCRUM-334` (`INF-012`) | Crítica | P1 | Ansible / k3s (VM2 / VM3) | **CERRADO** (Evidencia: `infrastructure/ansible/playbooks/deploy-k3s.yml`) |
| **BUG-003** | Aserción permisiva y divergencia en validación de RN-T1 en suites de prueba | `SCRUM-65` / `SCRUM-114` | Media | P2 | Newman / Postman | **CERRADO** (Evidencia: `scrum-65-roles-y-tenants.postman_collection.json` / `run-e2e.js`) |
| **BUG-004** | Discrepancia de tipo Problem Details RFC 9457 en rechazo por cobertura geográfica (`Problems.OutOfCoverage`) | `SCRUM-325` / `SCRUM-27` | Media | P2 | ServiceRequest / QA | **CERRADO** (Evidencia: `tests/e2e/evidencias/scrum-325-diagnostico-error-qa-2026-10-07.txt`) |
| **BUG-005** | Ausencia del header `X-Correlation-Id` en respuestas de error 403 Forbidden | `SCRUM-65` (`RNF-04`) | Alta | P2 | Gateway / Middlewares | **CERRADO** (Evidencia: `scrum-65-roles-y-tenants.postman_collection.json` / `scrum-325`) |

### 5.2 Estadísticas y Severidad de Defectos (IEEE 1044 / MoSCoW)
- **Defectos Totales:** 5
- **Defectos Bloqueantes (Blocker):** 0 (0%)
- **Defectos Críticos (Critical):** 1 (20% — BUG-002: CIDR k3s remediado en infraestructura).
- **Defectos de Severidad Alta (Major):** 2 (40% — BUG-001 en mobile y BUG-005 en correlationId).
- **Defectos de Severidad Media (Minor):** 2 (40% — BUG-003 en contrato RN-T1 y BUG-004 en Problem Details de cobertura).
- **Defectos Abiertos Residuales:** **0 (0%)**
- **Eficacia de Remediación:** **100.0%**

---

## 6. Matriz de Trazabilidad Consolidada (RTM: HU → Requisito → Prueba)

La siguiente tabla formaliza la trazabilidad bidireccional y verificable entre las Historias de Usuario de Jira, los requerimientos del SRS 4.0, los atributos de calidad del SAD V2.25, las suites de prueba ejecutadas y sus artefactos de evidencia:

| HU Jira | Requisito / Driver | Fuente Arquitectura | Suite / Caso de Prueba | Artefacto / Evidencia | Veredicto |
|:---:|---|---|---|---|:---:|
| **SCRUM-25 / 65** | **RF-01 / RF-02** (Autenticación y Roles RBAC) | SRS §5.1 / SAD §3.6 | Newman: IDN-001 a IDN-018 | `scrum-65-roles-y-tenants.postman_collection.json` | ✅ PASS |
| **SCRUM-27** | **RF-07 / RN-SR9** (Creación de Solicitud y Cobertura) | SRS §5.2 / DD §8.2 | Newman: SR-001 a SR-004 | `quickpatch-mvp.postman_collection.json` | ✅ PASS |
| **SCRUM-41 / 114**| **RN-T1** (Desactivación de Tenant y Bloqueo Login) | SRS §5.1 / DD §7.12 | Newman: IDN-019 / E2E-004 | `scrum-65-roles-y-tenants.postman_collection.json` | ✅ PASS |
| **SCRUM-41 / 112**| **RF-21** (Gestión de Tenants por Admin Plataforma) | SRS §5.4 / SAD §3.4 | Newman: Carpeta 5 Tenants | `quickpatch-mvp.postman_collection.json` | ✅ PASS |
| **SCRUM-318** | **HU-ADM-01 a 07** (Flujo Web Administrativo) | SRS §5.4 / Prototipos SAD W-01 a W-07 | Playwright + Newman: W-01 a W-07 | `scrum-318-web-admin-2026-10-07.txt` | ✅ PASS (Local) |
| **SCRUM-320** | **RNF-07 / RNF-08** (Rendimiento: Latencia $p95 \le 2s$, $\ge 20$ req/s) | SAD §3.2 / AC1-E1, AC1-E2 | k6: PRF-001 a PRF-004 | `tests/performance/load-test-50vu.js` | ⏳ Pendiente QA |
| **SCRUM-320** | **Killer K2 / PAY-002** (PCI-DSS: Cero Exposición PAN/CVV) | SAD §1.2 / ADR-011 | Security: PCI-001 a PCI-004 | `tests/security/pci_dss_scanner.py` | ✅ PASS |
| **SCRUM-320** | **Restricción R9** (Ingress Gateway Nginx Port 443 / VPN) | SAD §1.2 / INFRASTRUCTURE §3 | Ingress Nginx / ZAP Baseline | `tests/security/zap-baseline.conf` | ⏳ Pendiente QA |
| **SCRUM-325** | **SAD §3.7 / AC7-E4** (SLA Diagnóstico Logs $\le 1$ hora) | SAD §3.7 / AC7-E4 | Diagnóstico: Caso 1 (422) | `scrum-325-diagnostico-error-qa-2026-10-07.txt` | ✅ PASS |
| **SCRUM-325** | **RNF-04 / AC6-E3** (Auditoría Obligatoria 403 en Loki) | SAD §3.6 / AC6-E3 | Diagnóstico: Caso 2 (403) | `scrum-325-diagnostico-error-qa-2026-10-07.txt` | ✅ PASS |

---

## 7. Análisis de Riesgos Residuales y Plan de Mitigación

Se identificaron tres riesgos residuales técnicos con sus correspondientes planes de mitigación de cara a la etapa de despliegue y al Sprint 4:

### Riesgo 1: Ventana de Ejecución de Compuertas k6 y ZAP en Clúster QA (VM2 / VM1)
- **Probabilidad:** Media | **Impacto:** Bajo
- **Descripción:** Al completarse la configuración de QA el 7 de octubre, la ejecución masiva de k6 y el escaneo ZAP requieren ejecutarse sobre el despliegue del incremento de Sprint 3.
- **Mitigación:** Los scripts de prueba se encuentran completamente adaptados (login real con credenciales de QA y variables de entorno dinámicas). La ejecución se disparará de forma automatizada en cuanto concluya el despliegue de los pods en VM2.

### Riesgo 2: Umbral de Memoria RAM de 6.5 GiB en VM3 (AC2-E5)
- **Probabilidad:** Baja | **Impacto:** Medio
- **Descripción:** El escenario AC2-E5 del SAD establece un límite de $\text{RAM} \le 6.5\text{ GiB}$ en VM3. En la sección 5.6 de `INFRASTRUCTURE` este umbral está catalogado como sujeto a calibración empírica con microservicios reales.
- **Mitigación:** Tarea `SCRUM-347` programada para medir el consumo real en ejecución conjunta de los 8 servicios durante el ciclo de estabilización del release.

### Riesgo 3: Invalidación Inmediata de Tokens JWT Emitidos antes de la Suspensión del Tenant
- **Probabilidad:** Baja | **Impacto:** Menor
- **Descripción:** Conforme a DD §7.12, la suspensión de un tenant en la arquitectura actual rechaza inmediatamente nuevos inicios de sesión (`/api/v1/auth/login`), pero los tokens emitidos con anterioridad siguen siendo válidos en los microservicios descentralizados hasta que alcanzan su tiempo de expiración (TTL).
- **Mitigación:** Registrado formalmente como deuda de diseño a ser resuelta mediante listas de revocación distribuida en Redis (VM5) en `SCRUM-41` para el Sprint 4.

---

## 8. Conclusiones y Recomendaciones de Calidad

1. **Alineación Arquitectónica Verificable:** El incremento del Sprint 3 respeta fielmente los contratos de interfaces OpenAPI `/api/v1/*`, la estructura estándar RFC 9457 Problem Details y la topología de 7 máquinas virtuales definida en el ADR-022.
2. **Transparencia en el Reporte de Pruebas:** Se reportan con éxito 63 aserciones respaldadas por archivos de ejecución y evidencias verificables en el repositorio, dejando claramente diferenciadas las compuertas de rendimiento masivo y DAST como "Pendiente de QA" para su corrida en el clúster recién configurado.
3. **Cero Defectos Bloqueantes:** La resolución y verificación del 100% de los defectos detectados asegura que el incremento es estable y apto para ser consolidado en la rama `develop`.
4. **Recomendación para el Release:** Se recomienda proceder con la aprobación y sincronización de los Pull Requests del equipo de QA para conformar la versión candidata del Sprint 3.

---

**Katherine Bravo**  
QA Lead — QUICKPATCH  
Facultad de Ingeniería, Pontificia Universidad Javeriana  
`ka.bravo@javeriana.edu.co`
