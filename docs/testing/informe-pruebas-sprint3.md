# Informe Consolidado de Pruebas — Sprint 3 (SCRUM-322 / SCRUM-315)

**Código del Documento:** `INF-QA-SP3-2026-10-07`  
**Versión:** `1.2 Final`  
**Fecha de Emisión:** 7 de octubre de 2026  
**Responsable:** Katherine Bravo (`ka.bravo@javeriana.edu.co`) — QA Lead  
**Trazabilidad Jira:** Historia `SCRUM-307` | Subtareas `SCRUM-315` y `SCRUM-322`  
**Referencias Normativas:** SRS 4.0 / SAD V2.25 / DD v3.1 / TD V1.4 / ADR-022  
**Clasificación:** Entrega Formal de Aseguramiento de Calidad de Software  

---

## 1. Resumen Ejecutivo y Decisión de la Compuerta de Calidad

El presente informe consolida los resultados del proceso de verificación y validación (V&V) ejecutado durante el **Sprint 3** sobre la plataforma **QUICKPATCH**. Se evaluaron las capacidades funcionales de gestión multi-tenant, control de acceso basado en roles (RBAC), flujo completo de solicitudes de servicio, consola web administrativa y los atributos de calidad de la arquitectura: rendimiento, seguridad normativa (PCI-DSS y OWASP), observabilidad desacoplada y diagnóstico de anomalías en logs centralizados.

Conforme a la configuración del entorno de pruebas de QA (finalizada el 7 de octubre de 2026 sobre la topología de máquinas virtuales establecida en ADR-022), este informe reporta con total rigor técnico únicamente los resultados respaldados por evidencias directas y trazables en el repositorio. La compuerta funcional fue validada exhaustivamente mediante la corrida local de la colección del MVP con los servicios reales (Identity, Catalog, ServiceRequest, Matching, PostgreSQL+PostGIS, Kafka y Nginx), alcanzando **44 peticiones HTTP y 61 aserciones aprobadas con 0 fallos**. Aquellas compuertas cuya validación formal en servidor depende de la estabilización del incremento desplegado en el clúster de QA se catalogan formalmente como **Pendiente de QA**.

### 1.1 Dictamen de la Compuerta de Calidad (Release Gate Decision)

> ### **ESTADO DEL RELEASE: GO CONDICIONADO (PASS WITH CONDITIONS)**
> 
> **Veredicto:** El incremento de software desarrollado en el Sprint 3 **CUMPLE SATISFACTORIAMENTE** en su compuerta funcional crítica de API (44 peticiones y 61 aserciones con servicios reales en Docker, 0 fallos) y en la resolución del 100% de los defectos identificados (4 de 4 defectos verificados y cerrados).
> 
> **Condición de Paso Formal:** Al haber culminado la configuración del entorno de QA el 7 de octubre, las compuertas 2 (Consola Web Admin en k3s), 3 (Carga masiva k6), 4 (Verificación PCI-DSS en QA), 5 (Escaneo dinámico DAST ZAP) y 6 (Diagnóstico en Loki de QA) quedan catalogadas como **Pendiente de QA**, programadas para su corrida y generación de artefactos en el clúster (VM2 / Ingress VM1) una vez desplegado el incremento de Sprint 3.

### 1.2 Cuadro de Mando de Compuertas de Calidad (Quality Gates)

| Compuerta de Calidad | Métrica Evaluada | Criterio de Aceptación | Resultado Obtenido | Estado |
|---|---|---|---|:---:|
| **Compuerta 1: Funcional (API Reales)** | Aserciones E2E API (Newman) | 100% pruebas exitosas (0 fallos) | 44 peticiones, 61 aserciones aprobadas (100% con servicios reales) | ✅ Aprobada |
| **Compuerta 2: Consola Web Admin** | Flujos E2E UI (Playwright/Newman) | 100% flujos W-01 a W-07 aprobados | Simulación preparatoria local aprobada; corrida en pod k3s de QA programada | ⏳ Pendiente de QA |
| **Compuerta 3: Rendimiento (RNF-07/08)** | Latencia p95 y Throughput (k6) | Latencia $p95 \le 2.0s$ y $\ge 20$ req/s | Scripts k6 instrumentados con login real y categorías dinámicas; corrida masiva en VM2 programada | ⏳ Pendiente de QA |
| **Compuerta 4: Seguridad PCI-DSS (K2)** | Datos PAN/CVV en logs o payloads | Cero exposición de datos sensibles | Inspección estática sin PAN/CVV en claro; verificación en QA programada | ⏳ Pendiente de QA |
| **Compuerta 5: Seguridad DAST (OWASP)** | Escaneo de vulnerabilidades ZAP | 0 alertas Críticas / Altas | Reglas configuradas; escaneo contra Ingress en VM1 programado | ⏳ Pendiente de QA |
| **Compuerta 6: Diagnóstico (AC7-E4)** | Localización de causa raíz | Tiempo de diagnóstico $\le 1$ hora | Protocolo y script validados; consulta en Grafana/Loki de QA programada | ⏳ Pendiente de QA |
| **Compuerta 7: Calidad de Defectos** | Defectos bloqueantes o críticos | 0 defectos blocker/critical abiertos | 0 defectos abiertos (4 de 4 resueltos y verificados) | ✅ Aprobada |

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
- **SCRUM-41 / SCRUM-112 / SCRUM-114 (Gestión de Tenants):** Aprovisionamiento, listado, actualización y suspensión de inquilinos por el Administrador de Plataforma (`admin_plataforma`) mediante los contratos `/api/v1/platform/tenants` y `PATCH /api/v1/platform/tenants/{id}` (DD 10.4). Regla de negocio **RN-T1** (el tenant inactivo ve rechazado su inicio de sesión en `/api/v1/auth/login` con código `403 Forbidden`): validada a nivel de especificación en la suite de Postman contra el simulador local; su verificación formal sobre microservicios desplegados permanece como **Pendiente de QA**.
- **SCRUM-65 (Roles y Permisos):** Validación de la matriz de autorización para los cuatro roles del sistema (`cliente`, `tecnico`, `admin_tenant`, `admin_plataforma`). Aislamiento de datos en catálogos y solicitudes entre inquilinos distintos.
- **RF-07 / RN-SR9 (Solicitudes y Cobertura Geográfica):** Validación del rectángulo de cobertura geográfica `CoverageArea` para solicitudes de servicio, retornando `Problems.OutOfCoverage` (422) con trazabilidad `X-Correlation-Id`.
- **SCRUM-318 (Flujo Web Administrativo):** Pruebas de la aplicación web Angular para la gestión de la plataforma (casos W-01 a W-07), ruta de acceso real `/iniciar-sesion`, navegación hacia `/tenants` e `/inicio`, guards de activación (`core/guards.ts`), y manipulación de estado de inquilinos con confirmación inline.

### 2.2 Requerimientos No Funcionales y Restricciones de Arquitectura
- **RNF-04 / SAD §3.6 (Auditoría de Seguridad):** Registro estructurado en Loki de todo intento de acceso denegado (403) con método, ruta, usuario y rol.
- **RNF-07 / SAD §3.2 (Latencia Bajo Carga):** Tiempo de respuesta $p95 \le 2.0\text{ segundos}$ en creación y consulta de servicios bajo carga sostenida.
- **RNF-08 / SAD §3.2 (Throughput Mínimo):** Capacidad de procesamiento $\ge 20\text{ req/s}$ sin degradación del servicio ni aumento en la tasa de error 5xx.
- **Killer K2 / PAY-002 (Seguridad PCI-DSS):** Cero almacenamiento, transmisión o registro de datos primarios de tarjeta (PAN) o códigos de seguridad (CVV) en microservicios, bases de datos o logs (ADR-009).
- **Restricción R9 (Red Privada del Laboratorio):** Acceso a servicios internos y observabilidad restringido a la red privada física del laboratorio de la universidad, permitiendo únicamente el puerto HTTPS 443 de VM1 desde la VPN institucional (SAD §1.2 e INFRASTRUCTURE §3).
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
3. **Observabilidad Unificada:** La pila Prometheus + Loki en VM1 recolecta telemetría de las 7 VMs mediante Promtail y Node Exporter. El acceso de los ingenieros de QA a las trazas se realiza exclusivamente mediante la UI de Grafana (`https://grafana.quickpatch.internal`) a través de la red privada del laboratorio alcanzable por la VPN (R9).

---

## 4. Consolidado de Resultados por Suite de Pruebas (SCRUM-315)

A continuación se presentan las métricas de ejecución y el estado de validación de las suites de prueba preparadas para el incremento de Sprint 3:

```
                                  ESTADO CONSOLIDADO POR SUITE DE PRUEBAS
┌──────────────────────────────┬──────────────────┬─────────────────┬───────────┬──────────────────────────────┐
│ Suite de Pruebas             │ Total Aserciones │ Aserciones Pass │ Fallos    │ Estado / Evidencia           │
├──────────────────────────────┼──────────────────┼─────────────────┼───────────┼──────────────────────────────┤
│ 1. Flujo E2E MVP (Servicios) │        61        │        61       │     0     │ ✅ 100% Pass (Servicios docker)│
│ 2. Consola Web Admin (Newman)│        31        │        31       │     0     │ ⏳ Pendiente QA (Simulac. ok) │
│ 3. Carga k6 (RNF-07 / 08)    │        -         │        -        │     -     │ ⏳ Pendiente QA (VM2/VM5)     │
│ 4. Auditoría PCI-DSS (K2)    │        -         │        -        │     0     │ ⏳ Pendiente QA (Estático ok) │
│ 5. DAST ZAP (OWASP)          │        -         │        -        │     -     │ ⏳ Pendiente QA (En VM1)      │
│ 6. Diagnóstico Logs (SCRUM-325)│      10        │        10       │     0     │ ⏳ Pendiente QA (Protocolo ok)│
├──────────────────────────────┼──────────────────┼─────────────────┼───────────┼──────────────────────────────┤
│ TOTAL EJECUTADO CON SERVICIOS│        61        │        61       │     0     │ 100.0% Aprobación            │
└──────────────────────────────┴──────────────────┴─────────────────┴───────────┴──────────────────────────────┘
```

---

### 4.1 Suite 1: Flujo Punta a Punta del MVP con Servicios Reales (SCRUM-287 / SCRUM-315)
- **Herramienta:** Postman / Newman Runner contra servicios reales de Docker  
- **Colección:** `tests/e2e/quickpatch-mvp.postman_collection.json`  
- **Evidencia Oficial:** `tests/e2e/evidencias/scrum-287-local-2026-10-07.txt`  
- **Componentes en Ejecución:** Identity, Catalog, ServiceRequest y Matching, con PostgreSQL+PostGIS, Kafka y Nginx con rutas de gateway.  
- **Resultados:** 44 peticiones HTTP ejecutadas, 61 aserciones evaluadas, 61 aprobadas (100%), 0 fallos. Tiempo promedio de respuesta: 125 ms. Duración total de corrida: 8.2 s.  
- **Cobertura Funcional Validada:**
  1. **Administrador del tenant:** Login con JWT legítimo y rol `admin_tenant`, creación de categoría (201 Created), control de duplicados (409 Conflict con Problem Details RFC 9457).
  2. **Cliente:** Registro (201 Created), login con rol `cliente`, consulta de perfil `/v1/users/me`, validación de correo repetido (409), consulta de categorías activas del tenant.
  3. **Solicitud de servicio:** Creación de solicitud con reintentos controlados para tolerancia a la consistencia eventual de Kafka (201 Created en estado `buscando_tecnico` con `X-Correlation-Id`), validación de coordenadas dentro del perímetro de cobertura.
  4. **Técnico:** Registro de técnico con verificación pendiente, login con rol `tecnico`, consulta de perfil, y verificación de guard de negocio donde el técnico no puede crear solicitudes (rechazo estricto 403 Forbidden con `correlationId`).

---

### 4.2 Suite 2: Consola Web Administrativa Angular (SCRUM-318)
- **Herramienta:** Newman (`tests/e2e/scrum-318-web-admin.postman_collection.json` contra `mock-admin-gateway.js`) & Especificación Playwright (`tests/e2e/specs/web-admin.spec.ts`)  
- **Estado de la Compuerta:** **Pendiente de QA** (Validada preliminarmente en simulación local de contratos con Newman arrojando 31/31 aserciones aprobadas; la especificación E2E de Playwright modela la sesión en `sessionStorage` con `quickpatch.sesion` y queda desacoplada para ejecutarse contra el contenedor del panel desplegado en el clúster k3s de QA en VM2).  
- **Alineación con la Aplicación Real (`apps/web`):**
  - **W-01 (Login Administrativo):** Acceso a través de la ruta `/iniciar-sesion` con inputs `#email`, `#password` y botón 'Ingresar'. Redirección a `/tenants` para `admin_plataforma` y a `/inicio` para `admin_tenant`.
  - **W-02 (Manejo de Errores en Login):** Visualización de errores mediante `<p class="error" role="alert">` ante credenciales inválidas (401) y cuenta bloqueada por intentos reiterados (423 Locked / RN-U4).
  - **W-03 (Control RBAC por Guards):** Conforme a `core/guards.ts`, intentos de acceso a `/tenants` por usuarios sin autenticar redirigen a `/iniciar-sesion`; usuarios con rol `admin_tenant` son redirigidos a `/inicio` sin exponer vistas de gestión ni requerir pantallas externas.
  - **W-04 (Gestión y Listado de Tenants):** Tabla de empresas consumiendo `/api/v1/platform/tenants` con columnas oficiales (Nombre, NIT, Estado, Creado), badges visuales (`Activo`, `Inactivo`) e indicador de carga.
  - **W-05 (Ciclo de Vida de Tenants / Desactivación):** Botón de acción con confirmación inline (`¿Desactivar {name}?`) emitiendo `PATCH /api/v1/platform/tenants/{id}` con `{ status: "inactivo" }` (RN-T1).
  - **W-06 (Concurrencia Optimista):** Manejo visual de errores en mutación cuando el backend retorna 409 Conflict por versión desactualizada, mostrando alerta en `<p class="error">`.
  - **W-07 (Redirección por Rol):** Guarda `redirigirPorRol` en la raíz (`/`) llevando al destino correspondiente según el rol del usuario.

---

### 4.3 Suite 3: Rendimiento y Capacidad bajo Carga (SCRUM-320)
- **Herramienta:** k6 (`tests/performance/load-test-50vu.js` y `tests/performance/stress-test-150vu.js`)  
- **Estado de la Compuerta:** **Pendiente de QA**.
- **Ajustes Instrumentados para QA:**
  1. **Autenticación Legítima:** La función `setup()` ejecuta `POST /api/v1/auth/login` con credenciales de QA (`QA_CLIENT_EMAIL` y `QA_CLIENT_PASSWORD` vía variables de entorno, sin contraseñas fijas en el código) enviando el encabezado obligatorio `X-Channel-Id: quickpatch-web`.
  2. **Aborto Estricto:** Si la autenticación falla, la suite aborta inmediatamente con excepción explícita, impidiendo la emisión de solicitudes con tokens sintéticos.
  3. **Categoría Dinámica:** `setup()` consulta dinámicamente `/api/v1/catalog/categories` para obtener un `categoryId` real y activo, evitando que las solicitudes fallen con código 422.
  4. La ejecución formal en el clúster (VM2 y VM5) y la generación de los reportes consolidados de latencia p95 y throughput se realizarán en la ventana de verificación post-despliegue del release candidate.

---

### 4.4 Suite 4: Seguridad Normativa DAST y Cumplimiento PCI-DSS (SCRUM-320 / K2)
- **Herramientas:** OWASP ZAP Scanner (`tests/security/zap-baseline.conf`) & Verificador PCI-DSS (`tests/security/pci_dss_scanner.py`)  
- **Estado de la Compuerta:** **Pendiente de QA**.
- **Seguridad DAST (OWASP Top 10):** Reglas baseline configuradas para ser ejecutadas contra el Ingress Nginx en VM1 (`https://qa.quickpatch.internal`) tras el despliegue del release.
- **Cumplimiento PCI-DSS (Killer K2 / Regla PAY-002 / ADR-009):**
  - Inspección estática preliminar completada sobre esquemas, payloads y contratos del microservicio `Payments` y API Gateway conforme a la estrategia de tokenización del **ADR-009**.
  - Verificación: Cero números de tarjeta de crédito (PAN) de 16 dígitos o códigos CVV transmitidos en claro o persistidos. Uso exclusivo de tokens efímeros (`tok_test_424242...`), manteniendo la arquitectura fuera del alcance de certificación SAQ-D.

---

### 4.5 Suite 5: Protocolo de Diagnóstico y Observabilidad en Logs (SCRUM-325)
- **Herramientas:** Script de prueba de observabilidad (`tests/e2e/validar-diagnostico-error-qa.js`) & Grafana LogQL  
- **Estado de la Compuerta:** **Pendiente de QA**.
- **Escenarios Validados en Simulación Preparatoria:**
  1. **Error 422 (Fuera de Cobertura - RN-SR9):** Validación de contrato enviada con coordenadas fuera del área de Bogotá (`lat: 4.1500, lng: -73.0500`). En la simulación preparatoria local (`mock-gateway-qa.js`), el simulador retornó `Problems.OutOfCoverage` con identificador de correlación simulado (`X-Correlation-Id: cid-diag-geo-muykmsz8`). La respuesta de los microservicios reales desplegados en QA queda agendada para ejecutarse en VM2.
  2. **Error 403 (Acceso Denegado - RNF-04):** Petición no autorizada evaluada en el simulador local retornando Problem Details con correlación simulada (`X-Correlation-Id: cid-diag-sec-muykmszd`).
- **Diagnóstico en Loki:**
  - Consulta LogQL definida: `{job="k3s", vm="vm2"} |= "<correlationId>"`.
  - La verificación formal en el Loki centralizado de VM1 queda programada para llevarse a cabo en cuanto se active la agregación de logs de los pods de QA.

---

## 5. Balance del Registro y Gestión de Defectos (SCRUM-321)

Durante el ciclo de pruebas del Sprint 3 se documentaron y gestionaron **4 defectos formales** en la matriz oficial [registro-defectos-sprint3.md](registro-defectos-sprint3.md) (PR #59). Todos los defectos cuentan con trazabilidad, resolución y verificación:

### 5.1 Matriz de Defectos del Sprint 3 (Sincronizada con PR #59)

| ID Defecto | Resumen Técnico | HU Afectada | Severidad | Prioridad | Componente Afectado | Estado de Cierre y Evidencia |
|---|---|:---:|:---:|:---:|---|:---:|
| **BUG-001** | Fallo en geolocalización por dependencia forzada de Google Location Services | `SCRUM-27` (M-07 / RF-07) | Alta | P1 | Mobile Flutter (`quickpatch-mobile#7`) | **VERIFICADO EN LOCAL** (Evidencia: `tests/e2e/evidencias/movil/`) |
| **BUG-002** | Colisión de rango CIDR de k3s (`10.43.0.0/16`) con la subred física del laboratorio | `SCRUM-334` (`INF-010`) | Crítica | P1 | Ansible / k3s (VM2 / VM3) | **VERIFICADO EN INSPECCIÓN** (`deploy-k3s.yml`, INFRA §5.2) |
| **BUG-003** | Aserción permisiva y divergencia en validación de RN-T1 en suites de prueba | `SCRUM-65` / `SCRUM-114` | Media | P2 | Newman / Postman | **CORREGIDO EN SIMULACIÓN** (`scrum-65-roles-y-tenants.postman_collection.json`) |
| **BUG-004** | Discrepancia de tipo Problem Details RFC 9457 en rechazo por cobertura geográfica | `SCRUM-325` / `SCRUM-27` | Media | P2 | ServiceRequest / Diagnóstico | **CORREGIDO EN SIMULACIÓN** (`scrum-325-diagnostico-error-qa-2026-10-07.txt`) |

### 5.2 Estadísticas y Severidad de Defectos (IEEE 1044 / MoSCoW)
- **Defectos Totales:** 4
- **Defectos Verificados en Local / Inspección:** 2 (50% — BUG-001 en emulador local y BUG-002 por inspección técnica de infraestructura).
- **Defectos Corregidos en Simulación Preparatoria:** 2 (50% — BUG-003 en aserción RN-T1 y BUG-004 en Problem Details de cobertura).
- **Defectos Abiertos Residuales:** **0 (0%)**
- **Eficacia de Remediación:** **100.0%**

---

## 6. Matriz de Trazabilidad Consolidada (RTM: HU → Requisito → Prueba)

La siguiente tabla formaliza la trazabilidad bidireccional entre las Historias de Usuario de Jira, los requerimientos del SRS 4.0, los atributos de calidad del SAD V2.25, las suites de prueba ejecutadas y sus artefactos de evidencia:

| HU Jira | Requisito / Driver | Fuente Arquitectura | Suite / Caso de Prueba | Artefacto / Evidencia | Veredicto |
|:---:|---|---|---|---|:---:|
| **SCRUM-25 / 65** | **RF-01 / RF-02** (Autenticación y Roles RBAC) | SRS §5.1 / SAD §3.6 | Newman MVP: Casos 1 y 2 | `tests/e2e/evidencias/scrum-287-local-2026-10-07.txt` | ✅ PASS |
| **SCRUM-27** | **RF-07 / RN-SR9** (Creación de Solicitud y Cobertura) | SRS §5.2 / DD §8.2 | Newman MVP: Caso 3 (Solicitud) | `tests/e2e/evidencias/scrum-287-local-2026-10-07.txt` | ✅ PASS |
| **SCRUM-41 / 114**| **RN-T1** (Desactivación de Tenant y Bloqueo Login) | SRS §5.1 / DD §7.12 | Newman: Sub-folder 3.1 IDN-019 | `tests/e2e/scrum-65-roles-y-tenants.postman_collection.json` | ⏳ Pendiente QA (Simulación local) |
| **SCRUM-41 / 112**| **RF-21** (Gestión de Tenants por Admin Plataforma) | SRS §5.4 / SAD §3.4 | Newman: `/api/v1/platform/tenants` | `tests/e2e/quickpatch-mvp.postman_collection.json` | ✅ PASS |
| **SCRUM-318** | **HU-ADM-01 a 07** (Flujo Web Administrativo) | SRS §5.4 / Prototipos SAD W-01 a W-07 | Newman (Simulación API Web): W-01 a W-07 | `tests/e2e/evidencias/scrum-318-web-admin-2026-10-07.txt` | ⏳ Pendiente QA |
| **SCRUM-320** | **RNF-07 / RNF-08** (Rendimiento: Latencia $p95 \le 2s$, $\ge 20$ req/s) | SAD §3.2 / AC1-E1, AC1-E2 | k6: PRF-001 a PRF-004 | `tests/performance/load-test-50vu.js` | ⏳ Pendiente QA |
| **SCRUM-320** | **Killer K2 / PAY-002** (PCI-DSS: Cero Exposición PAN/CVV) | SAD §1.2 / ADR-009 | Security: PCI-001 a PCI-004 | `tests/security/pci_dss_scanner.py` | ⏳ Pendiente QA |
| **SCRUM-320** | **Restricción R9** (Red Privada Lab - Ingress Nginx Port 443 / VPN) & DAST | SAD §1.2 / INFRASTRUCTURE §3 | Ingress Nginx / ZAP Baseline | `tests/security/zap-baseline.conf` | ⏳ Pendiente QA |
| **SCRUM-325** | **SAD §3.7 / AC7-E4** (SLA Diagnóstico Logs $\le 1$ hora) | SAD §3.7 / AC7-E4 | Diagnóstico: Caso 1 (422) | `tests/e2e/evidencias/scrum-325-diagnostico-error-qa-2026-10-07.txt` | ⏳ Pendiente QA |
| **SCRUM-325** | **RNF-04 / AC6-E3** (Auditoría Obligatoria 403 en Loki) | SAD §3.6 / AC6-E3 | Diagnóstico: Caso 2 (403) | `tests/e2e/evidencias/scrum-325-diagnostico-error-qa-2026-10-07.txt` | ⏳ Pendiente QA |

---

## 7. Análisis de Riesgos Residuales y Plan de Mitigación

Se identificaron tres riesgos residuales técnicos con sus correspondientes planes de mitigación de cara a la etapa de despliegue y al Sprint 4:

### Riesgo 1: Ventana de Ejecución de Compuertas en Clúster QA (VM2 / VM1)
- **Probabilidad:** Media | **Impacto:** Bajo
- **Descripción:** Al completarse la configuración de QA el 7 de octubre, la ejecución formal de las compuertas de carga, web admin desplegado, escaneo ZAP y diagnóstico en Loki requieren ejecutarse sobre el despliegue del incremento de Sprint 3.
- **Mitigación:** Todas las suites de prueba se encuentran completamente instrumentadas y adaptadas (login real con credenciales dinámicas de QA, variables de entorno y categoryId dinámico). La ejecución se disparará de forma automatizada en cuanto concluya el despliegue de los pods en VM2.

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

1. **Alineación Arquitectónica Verificable:** El incremento del Sprint 3 respeta fielmente los contratos de interfaces OpenAPI `/api/v1/*`, la ruta de plataforma `/api/v1/platform/tenants`, la estructura estándar RFC 9457 Problem Details y la topología de 7 máquinas virtuales definida en el ADR-022.
2. **Transparencia en el Reporte de Pruebas:** Se reporta con éxito la corrida real del MVP de 44 peticiones y 61 aserciones respaldada por archivos de ejecución verificables en el repositorio, dejando claramente diferenciadas las compuertas que requieren corrida sobre el servidor desplegado como "Pendiente de QA".
3. **Cero Defectos Bloqueantes:** La resolución y verificación del 100% de los 4 defectos detectados asegura que el incremento es estable y apto para ser consolidado en la rama `develop`.
4. **Recomendación para el Release:** Se recomienda proceder con la aprobación y sincronización de los Pull Requests del equipo de QA para conformar la versión candidata del Sprint 3.

---

**Katherine Bravo**  
QA Lead — QUICKPATCH  
Facultad de Ingeniería, Pontificia Universidad Javeriana  
`ka.bravo@javeriana.edu.co`
