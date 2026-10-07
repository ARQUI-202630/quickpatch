# Documento de Pruebas (TD V1) — QUICKPATCH
## Sistema Multi-tenant de Servicios Técnicos para el Hogar y las Empresas

| | |
|---|---|
| **Tipo de documento** | Documento de Diseño y Definición de Pruebas (Test Document - TD) |
| **Versión** | 1.0 (Entrega Sprint 3 / Semana 10) |
| **Curso** | Arquitectura de Software |
| **Proyecto Jira** | SCRUM — Arquitectura de Software |
| **Rol Responsable** | Líder de Aseguramiento de Calidad (QA Lead) |
| **Estándares Aplicados** | ISO/IEC/IEEE 29119 (Software Testing), ISO/IEC 25010:2023 (Calidad de Software), PCI-DSS v4.0 (K2) |
| **Alcance** | Estrategia de pruebas automatizadas sobre 12 repositorios de componentes más el repositorio principal, y validación en 7 Máquinas Virtuales |

---

## Índice

1. [Introducción y Propósito (Test Plan)](#1-introducción-y-propósito)
2. [Estrategia de Pruebas y Topología Multirepo (Test Strategy - ADR-013)](#2-estrategia-de-pruebas-y-topología-de-repositorios-adr-013)
3. [El Ciclo de Calidad: Desarrollo → Pruebas → Ambiente](#3-el-ciclo-de-calidad-desarrollo--pruebas--ambiente)
4. [Justificación Técnica de Herramientas frente a Alternativas](#4-justificación-técnica-de-herramientas-frente-a-alternativas)
5. [Operación en las 7 Máquinas Virtuales (Red 10.43.x.x)](#5-operación-en-las-7-máquinas-virtuales-red-1043xx)
6. [Mecanismo de Bloqueo Local Pre-Push](#6-mecanismo-de-bloqueo-local-pre-push)
7. [Matriz de Trazabilidad RTM y Catálogo de Pruebas (Test Scenarios, RTM & Test Cases)](#7-matriz-de-trazabilidad-rtm-y-catálogo-de-pruebas-187-casos)
8. [Gestión de Datos de Prueba (Test Data)](#8-gestión-de-datos-de-prueba-test-data)
9. [Gestión y Reporte de Defectos (Bug Report)](#9-gestión-y-reporte-de-defectos-bug-report)
10. [Informe de Ejecución de Pruebas (Test Execution Report - Sprint 3)](#10-informe-de-ejecución-de-pruebas-test-execution-report---sprint-3)
11. [Control de Versiones del Documento](#11-control-de-versiones-del-documento)

---

## 1. Introducción y Propósito

### 1.1 Propósito
El presente Documento de Pruebas (TD V1) formaliza la estrategia integral de aseguramiento de calidad (QA) para la plataforma QUICKPATCH. Este documento establece los tipos de prueba, herramientas, ambientes de ejecución, compuertas de promoción y el catálogo detallado de casos de prueba automatizados requeridos para validar los requisitos del SRS (versión vigente 3.2) y los escenarios de calidad del SAD (versión vigente 2.13) de cara a los entregables del Sprint 3.

### 1.2 Objetivos de Calidad
1. **Garantizar la verificación automática:** Eliminar la dependencia de pruebas manuales no reproducibles mediante la automatización de pruebas unitarias, de integración, de contratos, E2E, de rendimiento y de seguridad.
2. **Proteger los Atributos de Calidad Críticos (SAD):**
   - **Aislamiento Multi-tenant (AC6-E2):** Cero fuga de información entre empresas clientes y usuarios mediante Row-Level Security (RLS).
   - **Cumplimiento PCI-DSS (K2, AC6-E1):** Cero almacenamiento de números de tarjeta (PAN) o códigos de seguridad (CVV) en bases de datos o logs.
   - **Capacidad de Matching bajo Carga (AC2-E4, AC2-E5):** Soporte de 50 VU (normal) y 150 VU (estrés) evaluados sobre el ambiente de QA en VM2 (ADR-015), garantizando 0 caída de pods, 0 desalojos por `OOMKilled` y degradación controlada, protegiendo a Producción (VM3) de estrés rutinario.
   - **Resiliencia e Idempotencia (AC5-E4, AC5-E5):** Cero pérdida de eventos ante caída de Kafka (vía Transactional Outbox) y cero efectos duplicados.
   - **Seguridad en el Ciclo del Servicio (AC9-E1, D7):** Bloqueo estricto de transiciones de estado inválidas y exigencia de evidencia fotográfica obligatoria en Garage (ADR-016) antes de completar cualquier trabajo.

---

## 2. Estrategia de Pruebas y Topología de Repositorios (ADR-013, ADR-021)

De acuerdo con las decisiones arquitectónicas **ADR-013** y **ADR-021**, el proyecto se distribuye en 12 repositorios de componentes más el repositorio principal, vinculados mediante Git Submodules. Cada repositorio tiene su propio pipeline de CI. La estrategia de pruebas se desacopla para maximizar la velocidad y la independencia de cada equipo:

```
# Repositorios individuales de microservicios (quickpatch-identity, matching, payments, etc.)
quickpatch-<servicio>/
└── tests/
    ├── unit/                   Pruebas unitarias de lógica y reglas de dominio (xUnit / JUnit 5)
    └── integration/            Pruebas de integración con bases de datos y Kafka efímeros (Testcontainers)

# Contratos REST en el repositorio del API Gateway (quickpatch-api-gateway)
quickpatch-api-gateway/
└── openapi/                    Contratos REST (Spectral CLI y oasdiff contra la rama base)

# Contratos de eventos en el repositorio de Kafka (quickpatch-kafka)
quickpatch-kafka/
├── events/                     Esquemas JSON Schema de eventos (AJV y compatibilidad contra la rama base)
└── topics/                     Un topic por eventType, alineado con events/

# Repositorio principal (quickpatch) — Territorio de QA
quickpatch/
└── tests/
    ├── e2e/                    Flujo crítico de negocio y Web Admin (Playwright + Newman)
    ├── performance/            Pruebas de carga y estrés en hardware real (k6: 150 VU)
    ├── security/               Escaneo dinámico (OWASP ZAP) y escáner de cumplimiento PCI-DSS
    └── fixtures/               Datos semilla compartidos (coordenadas de Bogotá y tenants de prueba)
```

| Repositorio | Stack | Nivel de Prueba que Aloja | Herramienta |
|---|---|---|---|
| `quickpatch` (Principal) | Orquestación / Markdown | Pruebas de Sistema Completo: E2E, Carga y Seguridad DAST | Playwright, k6, OWASP ZAP, Newman |
| `quickpatch-api-gateway` | OpenAPI / Nginx | Linting y compatibilidad de contratos REST; sintaxis de la configuración del gateway | Spectral CLI, oasdiff, `nginx -t` |
| `quickpatch-kafka` | JSON Schema / YAML | Validación y compatibilidad de esquemas de eventos; alineación de topics | AJV Validator, scripts del repositorio |
| `quickpatch-web` | Angular 22.1.x / TypeScript 6.0.x | Pruebas unitarias de componentes y servicios web | Vitest |
| `quickpatch-mobile` | Flutter 3.47.5 / Dart 3.13.4 | Pruebas unitarias de lógica y widgets móviles | Flutter Test, Patrol |
| `quickpatch/infrastructure/` (antes `quickpatch-infrastructure`, SCRUM-338) | Ansible / k3s | Verificación de sintaxis de playbooks y manifiestos k3s | Ansible Lint, Kubeconform |
| `quickpatch-identity` | ASP.NET Core 10 / C# | Unitarias y de integración RLS multi-tenant | xUnit, Moq, Testcontainers (Npgsql) |
| `quickpatch-actors` | ASP.NET Core 10 / C# | Unitarias de perfiles de técnicos y proveedores | xUnit, Testcontainers |
| `quickpatch-catalog` | ASP.NET Core 10 / C# | Unitarias de taxonomía y categorías de servicio | xUnit, Testcontainers |
| `quickpatch-service-request`| ASP.NET Core 10 / C# | Unitarias de máquina de estados, cotizaciones y fotos | xUnit, Testcontainers |
| `quickpatch-matching` | Java 25 / Spring Boot 4.1.1 | Unitarias de asignación y geoespaciales con PostGIS | JUnit 5, Mockito, Testcontainers (PostGIS) |
| `quickpatch-ranking` | ASP.NET Core 10 / C# | Unitarias de promedios de calificación e idempotencia | xUnit, Testcontainers (Kafka) |
| `quickpatch-payments` | ASP.NET Core 10 / C# | Unitarias de tokenización PCI-DSS y auditoría | xUnit, Testcontainers, WireMock |
| `quickpatch-communication`| ASP.NET Core 10 / C# | Unitarias de consumo de Kafka y notificaciones | xUnit, Testcontainers (Kafka) |

---

## 3. El Ciclo de Calidad: Desarrollo → Pruebas → Ambiente

El flujo de promoción asegura que ningún código defectuoso llegue a las máquinas de producción mediante **4 compuertas automatizadas secuenciales**:

```
[Desarrollador en Local] 
       │ 
       ▼ (git push)
[Compuerta 0: Pre-Push Hook Local] ──(Falla)──> [Push Abortado en la Laptop]
       │ (Pasa)
       ▼ 
[Compuerta 1: CI del Microservicio (GitHub Actions)]
       │ • Compilación y linter
       │ • Unitarias + Testcontainers (Postgres/Kafka efímeros en Docker)
       │ • Cobertura >= 80%
       ▼ 
[Compuerta 2: Pruebas de Sistema en Ambiente de QA (VM2 - ADR-015)]
       │ • Pipeline de pruebas de sistema ejecutado desde Runner en VM1
       │ • Playwright E2E + Colecciones Newman (qa.quickpatch.internal)
       │ • OWASP ZAP (DAST) contra Gateway de QA
       │ • Escáner Regex PCI-DSS en logs de QA en Loki (0 PAN / 0 CVV)
       │ • k6 normal: 50 VU con p95 < 3 s
       │ • k6 estrés: 150 VU con degradación controlada y sin caída
       ▼ 
[Compuerta 3: Despliegue en Producción (VM3 k3s)]
       │ • Rolling Update en VM3 mediante Runner en VM1
       │ • Smoke + kubectl rollout status
       │ • Verificación de estabilidad: 0 OOMKilled, 0 caída de pods y medición de consumo de CPU/RAM en Prometheus
       ├───(Pasa)───> [Versión Operativa y Tráfico Habilitado]
       └───(Falla)──> [kubectl rollout undo automático inmediato]
```

---

## 4. Justificación Técnica de Herramientas frente a Alternativas

| Categoría | Herramienta Elegida | Herramienta Alternativa | Justificación Técnica de la Elección |
|---|---|---|---|
| **Automatización Web** | **Playwright** | Selenium WebDriver | Playwright cuenta con **auto-waiting inteligente** (espera automáticamente a que los elementos del DOM de Angular estén interactuables sin necesidad de `Thread.sleep`), descarga navegadores herméticos sin necesidad de binarios `chromedriver` manuales, consume mínimos recursos en modo headless dentro de Docker y graba trazas visuales interactivas y videos ante cada fallo. |
| **Integración con BD y Eventos** | **Testcontainers** | Postman / Newman Solo | Postman solo evalúa respuestas HTTP en la superficie; **no puede validar si PostgreSQL aplicó el aislamiento de `tenant_id` por Row-Level Security (RLS)** ni puede interactuar nativamente con tópicos de Apache Kafka. Testcontainers aprovisiona instancias reales de PostgreSQL con PostGIS y brokers de Kafka en Docker en tiempo de ejecución. *(Postman se conserva como ejecutor complementario de colecciones de API).* |
| **Validación de Contratos y Eventos** | **Spectral CLI + AJV Validator** | Pruebas manuales de contratos | Valida automáticamente en CI (`quickpatch-contracts`) la conformidad de especificaciones OpenAPI 3.0 contra reglas arquitectónicas y la validez estructural de esquemas JSON Schema de eventos Kafka antes de cualquier integración. |
| **Pruebas de Carga y Rendimiento** | **k6** | Apache JMeter | JMeter está basado en Java y consume 1 a 2 GB de memoria RAM en la máquina generadora de carga. **k6 está escrito en Go y consume menos de 100 MB de RAM para 150 usuarios virtuales**, permitiendo ejecutar el test desde el runner de la VM1 sin saturar la máquina. Sus escenarios se programan en JavaScript estándar con aserciones declarativas (`thresholds`). |
| **Seguridad Dinámica (DAST)** | **OWASP ZAP** | Herramientas comerciales | Cumple con la restricción **K5 ($0 de presupuesto)** siendo el estándar open source de la industria para auditoría de vulnerabilidades web (inyección SQL, XSS, tokens JWT alterados y cabeceras inseguras). |

---

## 5. Operación en las 7 Máquinas Virtuales (Red 10.43.x.x)

Las 7 máquinas virtuales del laboratorio operan en red cerrada privada (`10.43.x.x`). Las pruebas interactúan con cada nodo respetando su asignación de recursos y roles:

| VM | IP | Software Principal | Rol en la Ejecución de Pruebas |
|---|---|---|---|
| **VM1** | `10.43.100.168` | Nginx + API Gateway + Panel Angular + Self-hosted Runner | Punto de entrada único HTTPS (puerto 443). Enruta tráfico por Virtual Hosts: producción (`quickpatch.internal`), QA (`qa.quickpatch.internal`) y Grafana (`grafana.quickpatch.internal`). Aloja el runner de GitHub Actions que ejecuta las pruebas de sistema y k6 hacia QA en VM2. |
| **VM2** | `10.43.98.15` | Ambiente de QA Dedicado (ADR-015): k3s, PostgreSQL+PostGIS, Redis, Kafka (Docker) y Nginx | **Sujeto de las pruebas de sistema y carga.** Aloja el entorno de QA permanente e independiente. Recibe las pruebas de Playwright, Newman, ZAP Baseline y las pruebas de estrés de k6 (150 VU) protegiendo el clúster de producción. |
| **VM3** | `10.43.98.205` | k3s (nodo único) con 8 microservicios de Producción | **Entorno de Producción.** Comparte 4 vCPU y 11 GiB de RAM. Matching opera con QoS *Guaranteed* (1 vCPU / 1 GiB). Protegido contra sobrecarga de pruebas de estrés al ejecutarse la carga destructiva exclusivamente en VM2 (ADR-015); VM3 no recibe estrés rutinario durante el sprint y solo se observa operativamente. |
| **VM4** | `10.43.98.209` | PostgreSQL 16 + PostGIS (puerto 5432) | Base de datos de Producción. Ejecuta las consultas espaciales (`ST_DWithin`) y valida las políticas RLS. (QA en VM2 utiliza su propia base de datos aislada en Docker Compose). |
| **VM5** | `10.43.98.29` | Redis 7 (puerto 6379) | Valida el almacenamiento en cache de cotizaciones temporales y coordinación de tareas programadas (RN-Q6). |
| **VM6** | `10.43.99.12` | Apache Kafka (puerto 9092) | Valida la publicación confiable vía Outbox, la tolerancia a desconexión del broker y el consumo idempotente de eventos por `eventId`. |
| **VM7** | `10.43.99.8` | Garage + Prometheus + Loki + Grafana | **Árbitro de observabilidad y almacenamiento.** Garage almacena las fotos obligatorias de evidencia y backups de PostgreSQL (ADR-016). Prometheus y Grafana monitorean en tiempo real el consumo de CPU/RAM, verificando 0 caídas de pods y registrando el baseline de recursos. |

---

## 6. Mecanismo de Bloqueo Local Pre-Push

Para evitar que se suba código con pruebas rotas al repositorio, se estandarizó la plantilla del gancho `pre-push` (Compuerta 0) en `quickpatch-infrastructure/plantillas/hooks/pre-push`, instalada en los repositorios copiándola a `.githooks/pre-push` y configurando `git config core.hooksPath .githooks`:

```bash
#!/usr/bin/env bash
# Compuerta 0 del Documento de Pruebas: corre las pruebas unitarias antes de cada push.
# Instalación, una vez por clon: copiar este archivo como .githooks/pre-push en el repo y correr
#   git config core.hooksPath .githooks
# Es una ayuda local: `git push --no-verify` lo salta, y el CI vuelve a correr todo igual.
set -uo pipefail
cd "$(git rev-parse --show-toplevel)" || exit 1

echo "[QA] Pruebas unitarias antes del push..."
if compgen -G "*.sln" > /dev/null || compgen -G "*.slnx" > /dev/null; then
  proyectos=$(find tests/unit -name '*.csproj' 2> /dev/null)
  if [ -z "$proyectos" ]; then
    echo "[QA] No hay proyectos de pruebas unitarias en tests/unit/."
    exit 1
  fi
  for p in $proyectos; do
    dotnet test "$p" --verbosity quiet || resultado=1
  done
elif [ -f build.gradle ] || [ -f build.gradle.kts ]; then
  if [ -x gradlew ]; then ./gradlew test --quiet; else gradle test --quiet; fi
  resultado=$?
elif [ -f pom.xml ]; then
  if [ -x mvnw ]; then ./mvnw -q test; else mvn -q test; fi
  resultado=$?
elif [ -f angular.json ]; then
  npm run test:ci --silent
  resultado=$?
elif [ -f pubspec.yaml ]; then
  flutter test
  resultado=$?
else
  echo "[QA] Este repo no tiene proyecto con pruebas: nada que correr."
  exit 0
fi

if [ "${resultado:-0}" -ne 0 ]; then
  echo "[QA] Push cancelado: fallaron las pruebas unitarias. Corrígelas antes de subir."
  exit 1
fi
echo "[QA] Pruebas aprobadas."
```

---

## 7. Matriz de Trazabilidad RTM y Catálogo de Pruebas (187 Casos)

### 7.1 Matriz de Trazabilidad de Requisitos (RTM)

La Matriz de Trazabilidad de Requisitos (RTM) establece la correspondencia bidireccional y verificable entre los requisitos funcionales del SRS (versión vigente 3.2), los escenarios de calidad del SAD (versión vigente 2.13) y el catálogo de 187 casos de prueba automatizados.

#### 7.1.1 Trazabilidad hacia Requisitos Funcionales del SRS (v3.2)
El SRS v3.2 establece un total de **32 Requisitos Funcionales activos** organizados en 23 Features y 7 Épicas. 

> [!NOTE]
> **Aclaración sobre la numeración histórica:** En concordancia con la sección 5.2 (línea 371) del SRS v3.2, la numeración salta de RF-29 a RF-34 porque los antiguos RF-30 a RF-33 (definidos en las versiones 2.x para control de cambios) fueron retirados en la versión 3.0 al ser reemplazados por el requisito no funcional **RNF-13 (Gestión Documental y Control de Cambios)**. Sus identificadores numéricos no se reutilizan para no romper la trazabilidad histórica de Jira. Por consiguiente, los 32 requisitos listados a continuación representan el **100% de los requisitos funcionales vigentes** del proyecto.

| ID RF | Nombre y Descripción Resumida | Módulo / Servicio Propietario | Casos de Prueba Automatizados Asociados |
|---|---|---|---|
| **RF-01** | Registro de Cliente con validación de email y password | Identity | `IDN-001`, `IDN-002`, `IDN-003`, `E2E-001` |
| **RF-02** | Registro de Técnico en estado pendiente de verificación | Identity / Actors | `IDN-004`, `ACT-001`, `ACT-002` |
| **RF-03** | Autenticación y bloqueo temporal tras fallos repetidos | Identity | `IDN-005`, `IDN-006`, `IDN-007`, `IDN-008` |
| **RF-04** | Aislamiento lógico multi-tenant vía `tenant_id` y RLS | Transversal (Todos) | `IDN-009`, `IDN-010`, `CAT-004`, `SRQ-007`, `ACT-009`, `PAY-008`, `RNK-008` |
| **RF-05** | Control de acceso basado en roles (RBAC) | Identity | `IDN-011`, `IDN-012`, `CAT-010` |
| **RF-06** | Registro de empresas corporativas y alta de tenant | Identity | `IDN-013`, `IDN-014`, `E2E-004` |
| **RF-07** | Creación de solicitud de servicio técnico por Cliente | ServiceRequest | `SRQ-001`, `SRQ-002`, `SRQ-003`, `E2E-001`, `E2E-005` |
| **RF-08** | Registro de solicitudes corporativas por Empresa | ServiceRequest | `SRQ-004` |
| **RF-09** | Asignación automática de técnico disponible y cercano (Matching) | Matching | `MAT-001`, `MAT-002`, `MAT-006`, `MAT-007`, `MAT-008`, `PRF-001` |
| **RF-10** | Aceptación o rechazo de solicitud por técnico y reasignación | Matching | `MAT-010`, `MAT-011`, `MAT-012`, `E2E-007` |
| **RF-11** | Seguimiento en tiempo real del estado de la solicitud | ServiceRequest / Communication | `SRQ-006`, `COM-001`, `COM-002`, `COM-005` |
| **RF-12** | Calificación del servicio (1 a 5) al completar | ServiceRequest / Ranking | `SRQ-021`, `SRQ-022`, `SRQ-023`, `RNK-001`, `RNK-002` |
| **RF-13** | Configuración de disponibilidad y zona de cobertura del Técnico | Matching / Actors | `MAT-003`, `MAT-005` |
| **RF-14** | Consulta de detalle de solicitud asignada por el Técnico | ServiceRequest | `SRQ-005` |
| **RF-15** | Cierre de solicitud con evidencia fotográfica obligatoria en Garage (ADR-016) | ServiceRequest | `SRQ-016`, `SRQ-017`, `SRQ-018`, `E2E-001` |
| **RF-16** | Administración de equipo de técnicos por Proveedor | Actors | `ACT-007`, `ACT-008`, `ACT-009` |
| **RF-17** | Historial de solicitudes atendidas por el Técnico | ServiceRequest | `SRQ-026` |
| **RF-18** | Dashboard operativo con panel de solicitudes activas para Admin | Web / ServiceRequest | `E2E-002` |
| **RF-19** | Aprobación o rechazo de registro de técnicos por Admin | Actors / Web | `ACT-003`, `ACT-004`, `E2E-003` |
| **RF-20** | Suspensión de cuenta de técnico por Admin | Actors / Identity | `ACT-005`, `ACT-006` |
| **RF-21** | Administración de tenants (activar/desactivar) por Admin | Identity / Web | `IDN-019`, `E2E-004` |
| **RF-22** | Pago del servicio con tarjeta delegada a pasarela PCI-DSS | Payments | `PAY-003`, `PAY-010`, `PAY-011`, `E2E-009` |
| **RF-23** | Pago de servicios a nombre de cuenta corporativa de Empresa | Payments | `PAY-006` |
| **RF-24** | Generación automática de comprobante/factura tras pago aprobado | Payments | `PAY-004`, `PAY-005` |
| **RF-25** | Consulta de pagos recibidos por Técnico / Proveedor | Payments | `PAY-007` |
| **RF-26** | Pipeline de CI/CD con build y pruebas automáticas | Infrastructure | `INF-016` |
| **RF-27** | Prueba automatizada End-to-End del flujo crítico | E2E Tests | `E2E-001` |
| **RF-28** | Registro centralizado de logs de error y alertas | Infrastructure / Observability | `INF-011`, `INF-012`, `PRF-010` |
| **RF-29** | Cifrado de datos sensibles en tránsito (HTTPS/TLS) y en reposo | Identity / Infrastructure | `IDN-015`, `IDN-021`, `INF-005` |
| **RF-34** | Emisión de cotización de mano de obra y materiales por Técnico | ServiceRequest | `SRQ-008`, `SRQ-009`, `SRQ-010` |
| **RF-35** | Aceptación, rechazo y límite de 3 cotizaciones por Cliente | ServiceRequest | `SRQ-011`, `SRQ-012`, `SRQ-013`, `E2E-008` |
| **RF-36** | Cancelación de solicitud por Cliente antes de iniciar labores | ServiceRequest | `SRQ-019`, `SRQ-020`, `E2E-010` |

#### 7.1.2 Trazabilidad hacia Escenarios de Calidad del SAD (v2.13)
El SAD v2.13 formaliza **51 escenarios de calidad (AC1-E1 a AC9-E8)** cubriendo las 40 subcaracterísticas de ISO/IEC 25010:2023. De estos, el presente plan automatiza **37 escenarios arquitectónicos y de software**. Los 14 escenarios restantes corresponden a pruebas presenciales de interacción humana con 5 usuarios (AC4-E3 a AC4-E9), análisis estático de código documental (AC7-E1, AC7-E2, AC8-E3, AC8-E4) y escenarios con dependencias de diseño pendientes en el backend (AC9-E2, AC9-E7, AC9-E8).

| Atributo de Calidad (ISO 25010) | Escenarios Automatizados | Total SAD | Casos de Prueba Automatizados |
|---|:---:|:---:|---|
| **AC1: Adecuación Funcional** | 3 / 3 | 3 | `AC1-E1` (MAT-001), `AC1-E2` (E2E-001), `AC1-E3` (SRQ-005) |
| **AC2: Eficiencia de Desempeño** | 5 / 5 | 5 | `AC2-E1` (PRF-001), `AC2-E2` (PRF-002), `AC2-E3` (PRF-003), `AC2-E4` (PRF-004), `AC2-E5` (PRF-005) |
| **AC3: Compatibilidad** | 2 / 2 | 2 | `AC3-E1` (PAY-014), `AC3-E2` (MAT-022) |
| **AC4: Capacidad de Interacción** | 2 / 9 | 9 | `AC4-E1` (E2E-005), `AC4-E2` (E2E-006). *(AC4-E3 a AC4-E9 son pruebas presenciales con 5 usuarios)* |
| **AC5: Confiabilidad** | 6 / 6 | 6 | `AC5-E1` (INF-008), `AC5-E2` (INF-015), `AC5-E3` (RNK-006), `AC5-E4` (INF-014), `AC5-E5` (SRQ-024), `AC5-E6` (E2E-012) |
| **AC6: Seguridad** | 8 / 8 | 8 | `AC6-E1` (PAY-001, PAY-002), `AC6-E2` (IDN-009), `AC6-E3` (IDN-011), `AC6-E4` (IDN-017), `AC6-E5` (E2E-011), `AC6-E6` (PAY-015), `AC6-E7` (IDN-020), `AC6-E8` (IDN-007, IDN-008) |
| **AC7: Mantenibilidad** | 3 / 5 | 5 | `AC7-E3` (CTR-001), `AC7-E4` (INF-012), `AC7-E5` (ACT-013). *(AC7-E1/E2 verificados por linters estáticos)* |
| **AC8: Flexibilidad** | 3 / 5 | 5 | `AC8-E1` (E2E-004), `AC8-E2` (MAT-020), `AC8-E5` (INF-002). *(AC8-E3/E4 portabilidad externa documentada)* |
| **AC9: Seguridad Operativa (Safety)**| 5 / 8 | 8 | `AC9-E1` (SRQ-015, SRQ-017), `AC9-E3` (SRQ-025), `AC9-E4` (MAT-013), `AC9-E5` (PAY-009), `AC9-E6` (PRF-010). *(AC9-E2/E7/E8 pendientes de diseño)* |
| **Total Escenarios** | **37 automatizados** | **51** | **100% de los escenarios de software y arquitectura cubiertos** |

#### 7.1.3 Matriz de Trazabilidad hacia Historias de Usuario de Jira (Sprint 3 — Subtarea SCRUM-317)
En cumplimiento de la subtarea **SCRUM-317** y las directrices de QA, la siguiente matriz mapea bidireccionalmente cada **Historia de Usuario (HU)** del backlog del Sprint 3 en Jira (`jorgefortich3.atlassian.net`) con sus Requisitos Funcionales del SRS v3.2, Atributos de Calidad del SAD v2.13, las subtareas específicas de QA y el conjunto de casos de prueba automatizados responsables de validar sus criterios de aceptación:

| Clave Jira (HU) | Título de la Historia de Usuario | Requisito SRS / SAD | Nivel de Prueba | Casos de Prueba Asociados | Subtarea QA en Jira | Criterio de Cobertura QA |
|---|---|---|---|---|---|---|
| **SCRUM-21** | Registro de Cliente con correo y contraseña | RF-01, RNF-03 | Unitaria, Integración, E2E | `IDN-001`, `IDN-002`, `IDN-003`, `E2E-001` | `SCRUM-53` — consultar estado vigente en Jira | Email válido, password $\ge 8$ caracteres, rechazo duplicado en tenant y hash seguro. |
| **SCRUM-22** | Registro de Técnico/Proveedor con datos y documentos | RF-02, RF-16 | Unitaria, Integración | `IDN-004`, `ACT-001`, `ACT-002`, `ACT-007` | Subtarea QA de sprint — consultar Jira | Documento obligatorio, perfil creado en estado `pendiente`, vinculación a proveedor. |
| **SCRUM-23** | Inicio de sesión seguro para todos los roles | RF-03, AC6-E8 | Unitaria, Integración | `IDN-005`, `IDN-006`, `IDN-007`, `IDN-008`, `IDN-017`, `IDN-018` | `SCRUM-59` — consultar estado vigente en Jira | JWT con claims válidos (`sub`, `tenant_id`, `role`), bloqueo tras 5 intentos fallidos (HTTP 423) y rechazo de tokens expirados o alterados. |
| **SCRUM-24** | Aislamiento lógico de datos por Tenant (Multi-tenant) | RF-04, AC6-E2 | Integración, Seguridad | `IDN-009`, `IDN-010`, `CAT-004`, `SRQ-007`, `ACT-009`, `PAY-008`, `RNK-008` | Subtarea QA de sprint — consultar Jira | Validación RLS en PostgreSQL: consultas entre tenants retornan 0 filas; rechazo de escrituras cruzadas (HTTP 403). |
| **SCRUM-25** | Definición de roles y permisos diferenciados | RF-05, AC6-E3 | Unitaria, Seguridad | `IDN-011`, `IDN-012`, `CAT-010` | `SCRUM-65` — consultar estado vigente en Jira | Validación RBAC estricta: HTTP 403 ante accesos no autorizados y emisión de log estructurado en Loki. |
| **SCRUM-26** | Registro de cuenta corporativa (Empresa) | RF-06 | Integración, E2E | `IDN-013`, `IDN-014`, `E2E-004` | Subtarea QA de sprint — consultar Jira | Alta de tenant corporativo activo, validación de unicidad de NIT (HTTP 409). |
| **SCRUM-27** | Creación de solicitud de servicio técnico (Cliente) | RF-07, AC4-E1, AC5-E4 | Unitaria, Integración, E2E | `SRQ-001`, `SRQ-002`, `SRQ-003`, `E2E-001`, `E2E-005` | `SCRUM-72` — consultar estado vigente en Jira | Formulario Flutter / REST, campos obligatorios, estado inicial `buscando_tecnico` y publicación Outbox `service-request.created`. |
| **SCRUM-28** | Creación de solicitud de servicio técnico (Empresa) | RF-08 | Integración | `SRQ-004` | Subtarea QA de sprint — consultar Jira | Solicitud asociada correctamente al `tenant_id` corporativo de la empresa. |
| **SCRUM-29** | Asignación automática de técnico (Motor de Matching) | RF-09, RF-10, AC1-E1, AC2-E4 | Integración, Rendimiento | `MAT-001` a `MAT-022`, `PRF-001`, `PRF-004` | Subtarea QA de sprint — consultar Jira | Filtro estricto de especialidad, ordenamiento espacial PostGIS, tolerancia a 50 VU normal y 150 VU estrés en k6 sobre QA (VM2) sin caída de pods. |
| **SCRUM-41** | Gestión de tenants/clientes (Admin) | RF-21, RN-T1, AC8-E1 | Integración, UI E2E | `IDN-019`, `E2E-004` | `SCRUM-114` — consultar estado vigente en Jira | Desactivación de tenant impide autenticación y creación de nuevas solicitudes (`tenant is disabled`). |
| **SCRUM-42** | Pago del servicio con tarjeta (Cliente, PCI-DSS) | RF-22, K2, AC6-E1 | Unitaria, Integración, Seguridad | `PAY-001`, `PAY-002`, `PAY-003`, `PAY-010`, `PAY-011`, `E2E-009` | Subtarea QA de sprint — consultar Jira | Cero PAN/CVV en BD y logs de Loki; cobro con token de pasarela (`tok_wompi_test_*`) y prevención de doble cobro. |
| **SCRUM-43** | Pago corporativo centralizado (Empresa) | RF-23 | Unitaria, Integración | `PAY-006` | Subtarea QA de sprint — consultar Jira | Factura a nombre de empresa corporativa con NIT y razón social. |
| **SCRUM-44** | Generación de factura/comprobante de pago | RF-24, D4 | Integración | `PAY-004`, `PAY-005` | Subtarea QA de sprint — consultar Jira | Emisión automática de comprobante fiscal consecutivo a nombre de QUICKPATCH. |
| **SCRUM-45** | Registro de pagos recibidos (Técnico/Proveedor) | RF-25 | Integración | `PAY-007`, `PAY-008` | Subtarea QA de sprint — consultar Jira | Consulta paginada de ingresos percibidos filtrada por `tenant_id` del técnico. |
| **SCRUM-46** | Pipeline de integración y despliegue continuo (CI/CD) | RF-26, RNF-08 | CI/CD, Infraestructura | `INF-016` | Subtarea QA de sprint — consultar Jira | Compuertas automatizadas en GitHub Actions; bloqueo ante fallos de prueba unitaria. |
| **SCRUM-47** | Pruebas automatizadas del flujo crítico (Smoke Test E2E) | RF-27, AC1-E2 | E2E Completo | `E2E-001`, `E2E-012` | Subtarea QA de sprint — consultar Jira | Recorrido integral de 10 pasos en Playwright sin intervención manual; tasa de error 5xx < 1%. |
| **SCRUM-48** | Logging centralizado y monitoreo de errores | RF-28, RNF-04, INFRA 7.1 | Observabilidad | `INF-011`, `INF-012`, `PRF-010` | Subtarea QA de sprint — consultar Jira | Ingesta de métricas en Prometheus y logs estructurados JSON con correlationId en Promtail/Loki. |
| **SCRUM-49** | Cifrado de datos sensibles en tránsito y en reposo | RF-29, K9, RNF-02 | Infraestructura, Seguridad | `IDN-015`, `IDN-021`, `INF-005` | Subtarea QA de sprint — consultar Jira | Terminación TLS 1.3 en API Gateway Nginx (VM1) y hash unidireccional de contraseñas. |
| **SCRUM-254** | Documentación Calidad y Pruebas V1 | TD V1, RTM | Documentación | 187 casos formalizados | `SCRUM-266` a `SCRUM-271` — consultar estado vigente en Jira | Documento de diseño de pruebas completo con matriz RTM, TDM, Bug reporting y compuertas. |
| **SCRUM-306** | Despliegue del incremento funcional en ambiente QA | ADR-015, Compuerta 2 | Infraestructura QA | `INF-003`, `INF-004`, `INF-005` | Subtarea QA de sprint — consultar Jira | Puesta en marcha de contenedores de QA en VM2 aislados de producción. |
| **SCRUM-307** | Informe de pruebas y evidencias del Sprint 3 | Calidad y Reporte | Trazabilidad y Evidencia | Catálogo completo y suites ejecutables | `SCRUM-317`, `SCRUM-315` — consultar estado vigente en Jira | Consolidación de casos, precondiciones, pasos, resultados esperados y evidencias reproducibles. |

---

### 7.2 Módulo: Gestión de Identidad y Multi-tenancy (`quickpatch-identity`)
* **Requisitos:** RF-01, RF-02, RF-03, RF-04, RF-05, RF-06, RF-29 | RNF-02, RNF-03, RNF-04, RNF-09, RNF-10 | SAD: AC6-E1, AC6-E2, AC6-E3, AC6-E4, AC6-E8

| ID Caso | Requisito / AC | Tipo | Descripción de la Prueba | Criterio de Aserción Automatizado (Assert) |
|---|---|---|---|---|
| **IDN-001** | RF-01 | Unitaria | Validación de formato de email en registro. | Email con formato inválido retorna HTTP 400 Bad Request. |
| **IDN-002** | RF-01 | Unitaria | Validación de complejidad de contraseña (mínimo 8 caracteres). | Password menor a 8 caracteres retorna HTTP 400. |
| **IDN-003** | RF-01 | Integración | Rechazo de email duplicado en el mismo tenant. | Inserción duplicada viola índice único `(tenant_id, email)`; HTTP 409 Conflict. |
| **IDN-004** | RF-02 | Integración | Registro de técnico nuevo en estado pendiente. | Fila en `technician_profiles` creada con `verification_status = 'pendiente'`. |
| **IDN-005** | RF-03 | Unitaria | Generación de JWT firmado tras login exitoso. | HTTP 200 OK; token contiene claims `sub`, `tenant_id` y `role`. |
| **IDN-006** | RF-03 | Unitaria | Incremento de contador tras contraseña errónea. | HTTP 401 Unauthorized; `failed_login_attempts` incrementado en 1. |
| **IDN-007** | RF-03, AC6-E8 | Integración | Bloqueo temporal de cuenta tras 5 intentos fallidos. | Quinto fallo retorna HTTP 423 Locked; `locked_until` fijado a 15 minutos en BD. |
| **IDN-008** | RF-03, AC6-E8 | Integración | Rechazo de autenticación durante período de bloqueo. | Login correcto con `locked_until > now()` retorna HTTP 423 Locked. |
| **IDN-009** | RF-04, AC6-E2 | Integración | **Aislamiento Multi-tenant RLS en Lectura de Usuarios.** | Consulta con JWT de Tenant B sobre tabla de Tenant A retorna 0 filas. Fuga = 0. |
| **IDN-010** | RF-04, AC6-E2 | Integración | Rechazo de inserción con `tenant_id` ajeno al token. | Intento de escritura en tenant ajeno bloqueado por RLS; HTTP 403 Forbidden. |
| **IDN-011** | RF-05, AC6-E3 | Unitaria | Validación RBAC: Cliente accediendo a endpoint de Admin. | Petición a `/v1/admin/tenants` con rol `cliente` retorna HTTP 403. |
| **IDN-012** | RF-05, AC6-E3 | Unitaria | Validación RBAC: Técnico creando solicitudes de servicio. | Petición a `POST /v1/service-requests` con rol `tecnico` retorna HTTP 403. |
| **IDN-013** | RF-06 | Integración | Registro de empresa corporativa crea tenant propio. | HTTP 201 Created; registro en tabla `tenants` con estado `activo`. |
| **IDN-014** | RF-06 | Integración | Validación de unicidad de NIT corporativo. | Registro de segundo tenant con mismo NIT viola `UNIQUE (nit)`; HTTP 409. |
| **IDN-015** | RNF-03 | Integración | Cifrado unidireccional de contraseñas con hash seguro. | Inspección de columna `password_hash` coincide con patrón BCrypt/Argon2. |
| **IDN-016** | RNF-04 | Integración | Registro de log estructurado ante intento 403. | Intento no autorizado emite log JSON con nivel `WARNING` y `correlationId`. |
| **IDN-017** | AC6-E4 | Unitaria | Rechazo de token JWT con firma criptográfica alterada. | Token manipulado rechazado en API Gateway con HTTP 401 Unauthorized. |
| **IDN-018** | AC6-E4 | Unitaria | Rechazo de token JWT expirado. | Token con claim `exp` en el pasado retorna HTTP 401 Unauthorized. |
| **IDN-019** | RN-T1 | Integración | Rechazo de login en tenant en estado inactivo. | Usuario de tenant inactivo recibe HTTP 403; mensaje `"tenant is disabled"`. |
| **IDN-020** | RN-A1 | Integración | Inmutabilidad de registros en `audit_logs`. | Intentos de `UPDATE` o `DELETE` sobre `audit_logs` con rol de app son rechazados por BD. |
| **IDN-021** | RF-29, RNF-02 | Integración | Cifrado obligatorio en tránsito (HTTPS/TLS) y en reposo. | Peticiones HTTP redirigidas a HTTPS (TLS 1.3) en Gateway Nginx; datos y contraseñas cifradas. |

---

### 7.3 Módulo: Catálogo de Servicios (`quickpatch-catalog`)
* **Requisitos:** SRS Sección 4.1 | DD Sección 5.4

| ID Caso | Requisito / AC | Tipo | Descripción de la Prueba | Criterio de Aserción Automatizado (Assert) |
|---|---|---|---|---|
| **CAT-001** | SRS 4.1 | Unitaria | Creación de categoría técnica con datos válidos. | HTTP 201 Created; UUID asignado y `active = true`. |
| **CAT-002** | SRS 4.1 | Unitaria | Rechazo de categoría con nombre vacío. | HTTP 400 Bad Request; validación de campo obligatorio. |
| **CAT-003** | SRS 4.1 | Integración | Consulta pública retorna solo categorías activas. | `GET /v1/catalog/categories` retorna 100% registros con `active == true`. |
| **CAT-004** | RF-04 | Integración | Aislamiento multi-tenant en categorías personalizadas. | Categorías exclusivas de Tenant A invisibles para consultas de Tenant B. |
| **CAT-005** | SRS 4.1 | Unitaria | Desactivación lógica de categoría de servicio. | `DELETE /v1/catalog/categories/{id}` establece `active = false` (sin borrado físico). |
| **CAT-006** | SRS 4.1 | Integración | Categoría inactiva excluida de selección de servicios. | Categoría desactivada no figura en listado para nuevas solicitudes. |
| **CAT-007** | SDD 3.2 | Integración | Consulta de categoría por UUID existente. | `GET /v1/catalog/categories/{id}` retorna HTTP 200 con atributos íntegros. |
| **CAT-008** | SDD 3.2 | Integración | Consulta de categoría inexistente. | `GET /v1/catalog/categories/{random_id}` retorna HTTP 404 Not Found. |
| **CAT-009** | SRS 4.1 | Unitaria | Modificación de nombre y descripción de categoría. | `PUT /v1/catalog/categories/{id}` actualiza campos en BD; HTTP 200 OK. |
| **CAT-010** | AC6-E3 | Unitaria | Restricción RBAC: Cliente intentando mutar catálogo. | `POST /v1/catalog/categories` con rol `cliente` retorna HTTP 403 Forbidden. |
| **CAT-011** | OpenAPI | Contrato | Verificación de contrato REST de Catálogo con Spectral CLI. | 100% concordancia con especificación OpenAPI 3.0 en `quickpatch-contracts` sin errores de linting ni campos faltantes. |
| **CAT-012** | AC2-E2 | Rendimiento | Tiempo de respuesta de consulta de catálogo. | Latencia p95 de `GET /v1/catalog/categories` inferior a 200 ms bajo 50 VU. |

---

### 7.4 Módulo: Actores y Perfiles de Técnicos (`quickpatch-actors`)
* **Requisitos:** RF-02, RF-16, RF-19, RF-20 | SDD Sección 4.4

| ID Caso | Requisito / AC | Tipo | Descripción de la Prueba | Criterio de Aserción Automatizado (Assert) |
|---|---|---|---|---|
| **ACT-001** | RF-02 | Unitaria | Creación de perfil técnico asociado a usuario. | Registro en `technician_profiles` con `average_rating = 0.00`. |
| **ACT-002** | RF-02 | Integración | Documento de identidad obligatorio para prestadores. | Creación con `document_id = null` es rechazada con HTTP 400. |
| **ACT-003** | RF-19 | Integración | Aprobación de técnico por el Administrador. | `POST /v1/admin/technicians/{id}/approve` establece `verification_status = 'aprobado'`. |
| **ACT-004** | RF-19 | Integración | Rechazo de técnico con motivo registrado. | `POST /v1/admin/technicians/{id}/reject` guarda `verification_reason` en BD. |
| **ACT-005** | RF-20, AC9-E2 | Integración | Suspensión preventiva de técnico por baja calificación. | Técnico con rating < 3.0 pasa a `verification_status = 'suspendido'`. |
| **ACT-006** | RF-20 | Unitaria | Reactivación de técnico suspendido tras revisión. | `POST /v1/admin/technicians/{id}/reactivate` retorna estado a `aprobado`. |
| **ACT-007** | RF-16 | Integración | Vinculación de técnico a empresa proveedora. | Campo `provider_id` persistido correctamente en `technician_profiles`. |
| **ACT-008** | RF-16 | Integración | Consulta de técnicos a cargo de un proveedor. | `GET /v1/provider/technicians` retorna únicamente el equipo asignado al proveedor. |
| **ACT-009** | RF-04 | Integración | Aislamiento multi-tenant en gestión de técnicos. | Proveedor de Tenant A no visualiza técnicos registrados bajo Tenant B. |
| **ACT-010** | SRS 3.0 | Unitaria | Consulta de perfil propio de técnico (`/v1/users/me`). | HTTP 200 OK retornando datos personales, especialidad y estado de verificación. |
| **ACT-011** | SRS 3.0 | Unitaria | Actualización de datos de contacto de técnico. | `PATCH /v1/users/me` actualiza teléfono y dirección; HTTP 200 OK. |
| **ACT-012** | ADR-006 | Evento | Emisión de evento al verificar técnico. | Aprobación genera evento `technician.verified` en tabla `outbox_events`. |
| **ACT-013** | OpenAPI | Contrato | Validación de contrato REST de Actores con Spectral CLI. | Contrato verificado contra especificación OpenAPI 3.0 en `quickpatch-contracts`; tipos y status codes íntegros. |
| **ACT-014** | RN-TP2 | Integración | Técnico no verificado excluido de disponibilidad. | Técnico en estado `pendiente` no puede cambiar disponibilidad a `disponible`. |

---

### 7.5 Módulo: Solicitudes de Servicio y Ciclo de Vida (`quickpatch-service-request`)
* **Requisitos:** RF-07, RF-08, RF-10, RF-11, RF-14, RF-15, RF-17, RF-34, RF-35, RF-36 | DD Sección 5.5, 7.4 | SAD: AC1-E2, AC1-E3, AC4-E1, AC5-E4, AC9-E1

| ID Caso | Requisito / AC | Tipo | Descripción de la Prueba | Criterio de Aserción Automatizado (Assert) |
|---|---|---|---|---|
| **SRQ-001** | RF-07, AC4-E1 | Unitaria | Creación de solicitud con datos válidos por un cliente. | HTTP 201 Created; solicitud en estado `buscando_tecnico`. |
| **SRQ-002** | RF-07, AC4-E5 | Unitaria | Rechazo de solicitud con descripción o dirección vacía. | HTTP 400 Bad Request indicando campo específico faltante. |
| **SRQ-003** | RF-07, AC5-E4 | Integración | **Transactional Outbox al registrar solicitud.** | En una sola transacción: fila en `service_requests` y evento `service-request.created` en `outbox_events`. |
| **SRQ-004** | RF-08 | Integración | Creación de solicitud corporativa para sede de empresa. | Solicitud asociada correctamente al `tenant_id` corporativo de la empresa. |
| **SRQ-005** | RF-14, AC1-E3 | Integración | Consulta de detalle de servicio por el técnico asignado. | Retorna dirección completa, categoría, descripción y coordenadas PostGIS. |
| **SRQ-006** | RF-11, AC4-E9 | Unitaria | Seguimiento en tiempo real por el cliente creador. | HTTP 200 OK con estado actual, técnico asignado y fecha estimada. |
| **SRQ-007** | RF-04 | Integración | Aislamiento multi-tenant en solicitudes de servicio. | Cliente de Tenant A recibe HTTP 404/403 al consultar solicitud de Tenant B. |
| **SRQ-008** | RF-34, RN-Q1 | Unitaria | Emisión de cotización por técnico titular asignado. | `POST /v1/service-requests/{id}/quotes` crea cotización en `pendiente`; servicio pasa a `cotizado`. |
| **SRQ-009** | RF-34, RN-Q1 | Unitaria | Rechazo de cotización emitida por técnico no asignado. | Técnico ajeno intentando cotizar recibe HTTP 403 Forbidden. |
| **SRQ-010** | RF-34, RN-Q2 | Unitaria | Máximo una cotización en estado pendiente a la vez. | Intento de segunda cotización concurrente rechazado con HTTP 409 Conflict. |
| **SRQ-011** | RF-35, RN-Q3 | Integración | Aceptación de cotización por el cliente titular. | Cotización pasa a `aceptada`; servicio pasa a `cotizacion_aceptada`; evento `service-request.quote-accepted` en Outbox. |
| **SRQ-012** | RF-35, RN-Q3 | Integración | Rechazo de cotización por el cliente. | Cotización pasa a `rechazada`; servicio regresa a `asignado` para re-cotización. |
| **SRQ-013** | RF-35, RN-Q7 | Integración | Cancelación automática al rechazar la tercera cotización. | Tercer rechazo cancela la solicitud con motivo `"cotizaciones rechazadas"`. |
| **SRQ-014** | RN-SR3 | Integración | Inicio de ejecución del servicio por el técnico. | `POST /v1/service-requests/{id}/start` cambia estado a `en_progreso`; `started_at` en UTC. |
| **SRQ-015** | AC9-E1 | Unitaria | **Transición Inválida (Safety):** Iniciar servicio sin cotización aprobada. | Petición de inicio en estado `buscando_tecnico` rechazada con HTTP 409 Conflict. |
| **SRQ-016** | RF-15, D7 | Integración | Carga obligatoria de evidencia fotográfica en Garage. | `POST /v1/service-requests/{id}/evidence` sube archivo a Garage y registra URL en `service_evidence`. |
| **SRQ-017** | RF-15, AC9-E1 | Integración | **Transición Bloqueada (Safety):** Completar servicio sin fotos en Garage. | `POST /v1/service-requests/{id}/complete` con 0 fotos registradas retorna HTTP 422 Unprocessable Entity. |
| **SRQ-018** | RF-15 | Integración | Completado exitoso tras verificar evidencia en Garage. | Estado pasa a `completado`; `completed_at` guardado; evento `service-request.completed` en Outbox. |
| **SRQ-019** | RF-36, RN-SR7 | Unitaria | Cancelación de solicitud por cliente antes de iniciar trabajo. | Solicitud pasa a `cancelado`; evento `service-request.cancelled` en Outbox. |
| **SRQ-020** | RF-36, RN-SR7 | Unitaria | Rechazo de cancelación unilateral cuando servicio está `en_progreso`. | Petición de cancelación rechazada con HTTP 409 Conflict tras inicio de labores. |
| **SRQ-021** | RF-12, RN-R1 | Integración | Registro de calificación válida de 1 a 5 estrellas. | Calificación persistida en tabla `ratings`; promedio de técnico encolado para recálculo. |
| **SRQ-022** | RF-12, RN-R1 | Unitaria | Rechazo de calificación con puntaje inválido (0 o 6). | HTTP 400 Bad Request por violación de restricción `CHECK (score BETWEEN 1 AND 5)`. |
| **SRQ-023** | RF-12, RN-R2 | Integración | Rechazo de calificación duplicada para un mismo servicio. | Segunda calificación sobre la misma solicitud rechazada con HTTP 409 Conflict. |
| **SRQ-024** | ADR-007, AC5-E5| Evento | Consumo idempotente de evento `payment.approved`. | Segundo evento con mismo `eventId` es ignorado; solicitud permanece en `pagado` sin doble efecto. |
| **SRQ-025** | AC9-E3 | Evento | Detección de servicios en curso sin cierre por más de 4 horas. | Solicitud marcada con flag de revisión para el Administrador tras superar umbral. |
| **SRQ-026** | RF-17 | Integración | Consulta de historial de solicitudes atendidas por el técnico. | `GET /v1/technicians/me/services?status=completado` retorna historial paginado filtrado por tenant. |

---

### 7.6 Módulo: Motor de Matching y Cobertura Geoespacial (`quickpatch-matching`)
* **Requisitos:** RF-09, RF-10, RF-13 | RNF-05 | DD Sección 5.6, 5.7, 5.8 | SAD: AC1-E1, AC2-E1, AC2-E3, AC2-E4, AC9-E4

| ID Caso | Requisito / AC | Tipo | Descripción de la Prueba | Criterio de Aserción Automatizado (Assert) |
|---|---|---|---|---|
| **MAT-001** | RF-09, AC1-E1 | Integración | **Filtro de Especialidad Estricto (Functional Correctness).** | Candidato retornado tiene exactamente la especialidad requerida. 0% asignaciones erróneas. |
| **MAT-002** | RF-09 | Integración | Exclusión de técnicos con verificación pendiente o suspendida. | Solo técnicos con `verification_status = 'aprobado'` son seleccionados. |
| **MAT-003** | RF-13 | Integración | Actualización de estado de disponibilidad del técnico. | `PUT /v1/matching/availability` actualiza estado en `technician_availability`. |
| **MAT-004** | RF-09 | Integración | Exclusión de técnicos con disponibilidad en `ocupado` o `no_disponible`. | Técnico ocupado es descartado del conjunto de candidatos elegibles. |
| **MAT-005** | RF-13, PostGIS | Integración | Persistencia de zona de cobertura poligonal del técnico en Bogotá. | Polígono GeoJSON guardado como `geometry(Polygon, 4326)` en `coverage_zones`. |
| **MAT-006** | RF-09, PostGIS | Integración | Evaluación de ubicación dentro de la zona de cobertura. | `ST_Contains(area, location)` evalúa `true`; técnico incluido en selección. |
| **MAT-007** | RF-09, PostGIS | Integración | Exclusión de técnicos fuera del área geográfica del servicio. | Solicitud en Kennedy vs cobertura en Usaquén; técnico excluido. |
| **MAT-008** | RF-09, PostGIS | Integración | Ordenamiento de candidatos por proximidad espacial esférica. | Candidato más cercano en distancia euclidiana/esférica seleccionado primero. |
| **MAT-009** | RF-10 | Integración | Creación de intento de matching con vigencia de 3 minutos. | Fila en `matching_attempts` con `response = 'pendiente'` y `expires_at = now() + 3min`. |
| **MAT-010** | RF-10 | Unitaria | Aceptación de oferta de servicio por el técnico titular. | `POST /v1/matching/offers/{id}/accept` pasa a `aceptada`; emite `matching.technician-assigned`. |
| **MAT-011** | RF-10 | Unitaria | Rechazo de oferta de servicio por el técnico titular. | `POST /v1/matching/offers/{id}/reject` pasa a `rechazada`; algoritmo busca siguiente candidato. |
| **MAT-012** | RF-10, RN-M3 | Integración | Expiración automática de oferta no respondida en 3 minutos. | Oferta vencida marcada como `expirado`; solicitud reasignada automáticamente al siguiente técnico. |
| **MAT-013** | AC9-E4 | Integración | **Comportamiento Fail-Safe:** Sin técnicos disponibles en la zona. | Solicitud pasa a `en_espera`; emite `matching.no-technician-available`; 0 asignaciones inválidas. |
| **MAT-014** | RN-M1 | Integración | Bloqueo transaccional de oferta para evitar doble asignación. | Actualización concurrente con bloqueo atómico; exactamente un matching gana la oferta. |
| **MAT-015** | ADR-006 | Evento | Consumo reactivo de evento `service-request.created` desde Kafka. | Recepción de mensaje JSON dispara proceso de matching en menos de 500 ms. |
| **MAT-016** | ADR-007 | Evento | Consumo de `service-request.completed` libera al técnico. | Técnico retorna automáticamente a estado `disponible` en `technician_availability`. |
| **MAT-017** | ADR-007 | Evento | Consumo de `service-request.cancelled` libera al técnico ofertado. | Oferta en curso anulada; técnico marcado inmediatamente como `disponible`. |
| **MAT-018** | AC2-E1 | Rendimiento | Latencia de búsqueda geoespacial bajo 50 consultas concurrentes. | Tiempo de respuesta `http_req_duration p(95) < 3000 ms`. |
| **MAT-019** | AC2-E3 | Rendimiento | Tiempo extremo a extremo desde solicitud hasta notificación de oferta. | Lapso total cronometrado inferior a 7.0 segundos. |
| **MAT-020** | AC2-E4 | Estrés | **Pico de carga sostenido de 150 solicitudes de matching concurrentes.** | 150 VU de estrés en k6 durante 5 minutos contra QA (VM2 - ADR-015); 0 errores 5xx no controlados; sin caída de pod; Producción (VM3) no recibe estrés rutinario. |
| **MAT-021** | AC2-E5, K10 | Capacidad | Límite de memoria de Matching Service en k3s (QoS Guaranteed). | Consumo de RAM no excede 1.0 GiB asignado; 0 desalojos por `OOMKilled`. |
| **MAT-022** | AC3-E2 | Resiliencia | Convivencia en VM3: saturación de Ranking pod no degrada a Matching. | Matching mantiene latencia p95 < 3s ante pico de CPU provocado en otro pod. |

---

### 7.7 Módulo: Procesamiento de Pagos y Facturación (`quickpatch-payments`)
* **Requisitos:** RF-22, RF-23, RF-24, RF-25 | RIE-01 | K2 (PCI-DSS), D4 | SAD: AC3-E1, AC6-E1, AC6-E6, AC9-E5

| ID Caso | Requisito / AC | Tipo | Descripción de la Prueba | Criterio de Aserción Automatizado (Assert) |
|---|---|---|---|---|
| **PAY-001** | K2, AC6-E1 | Integración | **Auditoría PCI-DSS en Esquema de Base de Datos.** | Columnas de PAN y CVV inexistentes en esquema PostgreSQL; solo existe `provider_token_ref`. |
| **PAY-002** | K2, AC6-E1 | Integración | **Auditoría PCI-DSS en Logs Estructurados (Loki).** | Búsqueda regex de tarjetas y CVV en logs arroja exactamente 0 coincidencias. |
| **PAY-003** | RF-22, ADR-009 | Unitaria | Procesamiento de cobro utilizando token de pasarela certificada. | `POST /v1/service-requests/{id}/payment` con token válido retorna HTTP 200 OK (`aprobado`). |
| **PAY-004** | RF-24, D4 | Integración | Generación automática de factura a nombre de QUICKPATCH. | Fila en `invoices` creada con consecutivo único, monto exacto cotizado y emisor QUICKPATCH. |
| **PAY-005** | RF-24 | Integración | Consulta y descarga de comprobante por el cliente pagador. | `GET /v1/payments/{id}/invoice` retorna HTTP 200 con metadata y URL de descarga PDF. |
| **PAY-006** | RF-23 | Unitaria | Facturación corporativa a nombre de Empresa con NIT. | Factura generada incluye `payer_nit` y razón social corporativa. |
| **PAY-007** | RF-25 | Integración | Consulta de ingresos percibidos por el técnico titular. | `GET /v1/payments/received` con JWT de técnico retorna historial de pagos propios. |
| **PAY-008** | RF-04 | Integración | Aislamiento multi-tenant en historial financiero. | Técnico de Tenant A no visualiza montos facturados bajo Tenant B. |
| **PAY-009** | AC9-E5 | Integración | **Comportamiento Fail-Safe:** Pasarela externa retorna timeout/500. | Pago pasa a `rechazado`; servicio permanece en `completado`; no se emite cobro doble ni factura. |
| **PAY-010** | RN-P5 | Unitaria | Reintento exitoso tras pago previamente rechazado. | Segundo cobro procesado con nuevo `payment_id`; estado pasa a `aprobado`. |
| **PAY-011** | RN-P2 | Integración | Prevención de doble cobro aprobado para una misma solicitud. | Peticiones de cobro concurrentes bloqueadas por índice único parcial sobre pagos aprobados. |
| **PAY-012** | ADR-006 | Evento | Emisión de evento `payment.approved` a Kafka. | Tópico de eventos recibe mensaje con `serviceRequestId`, `amount`, `tenantId` y `correlationId`. |
| **PAY-013** | ADR-006 | Evento | Emisión de evento `payment.rejected` a Kafka. | Tópico recibe notificación de rechazo para que Comunicación alerte al cliente. |
| **PAY-014** | AC3-E1 | Contrato | Validación de formato de integración con pasarela externa. | 100% de peticiones cumplen el contrato OpenAPI exigido por el proveedor de pagos. |
| **PAY-015** | AC6-E6 | Integración | Trazabilidad inmutable en `audit_logs` para cada cambio de pago. | Cada transición de estado en pagos queda registrada con marca de tiempo UTC y usuario autorizador. |
| **PAY-016** | RN-P3 | Unitaria | Monto cobrado idéntico al valor de la cotización aprobada. | Discrepancia matemática entre `quotes.total_amount` y cobro enviado es igual a $0.00. |
| **PAY-017** | AC6-E3 | Seguridad | Petición no autenticada intentando consultar comprobantes. | `GET /v1/payments/{id}/invoice` sin cabecera de autenticación retorna HTTP 401 Unauthorized. |
| **PAY-018** | K2 | Seguridad | Prevención de registro de credenciales privadas de pasarela en consola. | Logs de contenedor libres de API Keys privadas o secretos de autenticación del proveedor. |

---

### 7.8 Módulo: Reputación y Calificaciones (`quickpatch-ranking`)
* **Requisitos:** RF-12, RF-18, RF-20 | SAD: AC4-E6, AC9-E2

| ID Caso | Requisito / AC | Tipo | Descripción de la Prueba | Criterio de Aserción Automatizado (Assert) |
|---|---|---|---|---|
| **RNK-001** | RF-12 | Evento | Consumo asíncrono de evento de calificación desde Kafka. | Ranking consume evento y actualiza acumulador en menos de 1 segundo. |
| **RNK-002** | RF-12 | Unitaria | Cálculo de promedio ponderado de calificaciones de técnico. | Promedio de notas [5, 4, 5, 2] calculado exactamente como `4.00`. |
| **RNK-003** | AC9-E2 | Integración | **Detección de Riesgo (Safety):** Señalización de técnico con promedio < 3.0. | Técnico con promedio menor a 3.0 tras 5 servicios marcado con `requires_review = true`. |
| **RNK-004** | AC9-E2 | Integración | Exclusión de alerta preventiva si el técnico tiene menos de 5 servicios. | Técnico novato con notas bajas no es señalado prematuramente (muestra no representativa). |
| **RNK-005** | AC5-E5 | Integración | Idempotencia ante evento duplicado de calificación. | Segundo evento con mismo `eventId` es ignorado; promedio se recalcula una sola vez. |
| **RNK-006** | AC5-E3 | Integración | Tolerancia a caída y recuperación de Ranking Service. | Ranking consume eventos encolados en Kafka tras reinicio sin pérdida de datos. |
| **RNK-007** | RF-12 | Unitaria | Asignación de puntaje inicial tras primer servicio calificado. | Primera nota de 5 estrellas establece promedio en `5.00` y contador en 1. |
| **RNK-008** | RF-04 | Integración | Aislamiento de reputación por tenant. | Evaluaciones de Tenant A no afectan el promedio de técnicos en Tenant B. |
| **RNK-009** | EDA | Contrato | Validación de esquema JSON de evento de calificación. | Payload cumple 100% el esquema versionado en `quickpatch-kafka`. |
| **RNK-010** | AC2-E2 | Rendimiento | Latencia de actualización de reputación tras calificación. | Promedio persistido en base de datos en menos de 500 ms tras consumo del evento. |
| **RNK-011** | AC9-E2 | Unitaria | Cero suspensión automática desatendida. | Técnico señalado permanece activo hasta decisión manual del Administrador. |
| **RNK-012** | RNF-04 | Observabilidad| Emisión de log estructurado ante detección de bajo promedio. | Log de advertencia con nivel `WARNING` emitido con ID de técnico y promedio para Loki. |

---

### 7.9 Módulo: Comunicación y Notificaciones (`quickpatch-communication`)
* **Requisitos:** RIE-03 | SAD: AC2-E3, AC5-E5

| ID Caso | Requisito / AC | Tipo | Descripción de la Prueba | Criterio de Aserción Automatizado (Assert) |
|---|---|---|---|---|
| **COM-001** | RIE-03 | Evento | Notificación al cliente al registrar solicitud. | Consumo de `service-request.created` genera confirmación con número de radicado. |
| **COM-002** | RIE-03 | Evento | Notificación al técnico asignado con datos de servicio. | Consumo de `matching.technician-assigned` envía mensaje con dirección y categoría. |
| **COM-003** | RIE-03 | Evento | Notificación al cliente de cotización disponible. | Consumo de `service-request.quoted` envía mensaje con valor cotizado. |
| **COM-004** | RIE-03 | Evento | Notificación al técnico de cotización aceptada. | Consumo de `service-request.quote-accepted` alerta autorización de inicio de labores. |
| **COM-005** | RIE-03 | Evento | Notificación de servicio completado requiriendo pago. | Consumo de `service-request.completed` envía enlace de pago seguro al cliente. |
| **COM-006** | RIE-03 | Evento | Notificación de pago exitoso con recibo adjunto. | Consumo de `payment.approved` genera mensaje con factura en formato PDF. |
| **COM-007** | RIE-03 | Evento | Notificación de pago rechazado con opción de reintento. | Consumo de `payment.rejected` alerta motivo de rechazo y botón de nuevo intento. |
| **COM-008** | AC5-E5 | Integración | **Idempotencia de Notificaciones:** Prevención de doble mensaje. | Evento duplicado genera exactamente 1 sola notificación; 0 mensajes duplicados. |
| **COM-009** | RIE-03 | Resiliencia | Encolamiento en Dead Letter Queue (DLQ) ante falla de pasarela de correo. | Mensaje encolado en DLQ para reintento con backoff exponencial. |
| **COM-010** | RIE-03 | Unitaria | Renderizado de plantilla con datos dinámicos. | Texto final libre de etiquetas sin procesar (`{name}`, etc.). |
| **COM-011** | AC6-E1 | Seguridad | Ausencia de datos financieros en cuerpo de notificación. | Mensaje libre de números de tarjeta o códigos CVV. |
| **COM-012** | RF-04 | Integración | Aislamiento multi-tenant en plantillas de notificación. | Logotipos y remitentes corresponden exclusivamente al tenant del servicio. |
| **COM-013** | EDA | Contrato | Validación de sobre base en eventos consumidos. | Eventos cumplen campos obligatorios (`eventId`, `tenantId`, `correlationId`). |
| **COM-014** | AC2-E3 | Rendimiento | Tiempo de encolamiento de notificación. | Mensaje puesto en cola de despacho en menos de 100 ms tras recepción del evento. |

---

### 7.10 Módulo: Gobernanza de Contratos (`quickpatch-api-gateway` y `quickpatch-kafka`)
* **Requisitos:** ADR-012, ADR-013, ADR-021 | SDD Sección 6 | SAD Sección 4.3

| ID Caso | Requisito / AC | Tipo | Descripción de la Prueba | Criterio de Aserción Automatizado (Assert) |
|---|---|---|---|---|
| **CTR-001** | OpenAPI | Linter | Sintaxis formal de contratos OpenAPI 3.0. | `spectral lint openapi/**/*.yaml` retorna 0 errores sintácticos. |
| **CTR-002** | OpenAPI | Linter | Convenciones REST en nombres de endpoints. | Endpoints en minúsculas y sustantivos en plural verificados al 100%. |
| **CTR-003** | OpenAPI | Linter | Definición obligatoria de respuestas de error estándar. | Códigos 400, 401, 403, 404 y 500 documentados en cada operación. |
| **CTR-004** | EDA | Schema | Validación sintáctica de esquemas JSON Schema de Kafka. | Validador AJV sobre `events/**/*.json` retorna 0 errores. |
| **CTR-005** | EDA | Schema | Campos obligatorios en sobre base de eventos. | `eventId`, `eventType`, `tenantId`, `correlationId`, `timestamp`, `version` son `required`. |
| **CTR-006** | SemVer | Contrato | Versionamiento semántico en tags de release. | Formato `vMAJOR.MINOR.PATCH` verificado; tags arbitrarios bloqueados. |
| **CTR-007** | ADR-013 | Compatibilidad| Detección de Breaking Changes en especificaciones REST. | Modificaciones no rompen compatibilidad hacia atrás sin incremento `MAJOR`. |
| **CTR-008** | ADR-013 | Compatibilidad| Detección de Breaking Changes en esquemas de eventos Kafka. | Nuevos campos en esquemas son declarados opcionales para consumidores antiguos. |
| **CTR-009** | ADR-013 | CI/CD | Sincronización de submódulos en microservicios. | Submódulos `contracts/api-gateway/` y `contracts/kafka/` de los 8 servicios (y `contracts/api-gateway/` de web y mobile) apuntan a tags válidos; lo comprueba `tools/validate-composition.sh`. |
| **CTR-010** | ADR-012 | Gobernanza | Cero duplicación de contratos entre repositorios. | `quickpatch-api-gateway` (REST) y `quickpatch-kafka` (eventos) son las únicas fuentes de verdad contractual del sistema. |

---

### 7.11 Módulo: Infraestructura, Resiliencia y Servidores (`quickpatch-infrastructure`)
* **Requisitos:** RF-26, RNF-01, RNF-02, RNF-07, RNF-08 | K5, K7, K9, K10, K11 | INFRASTRUCTURE.md | SAD: AC5-E1, AC5-E2, AC7-E5, AC8-E5

| ID Caso | Requisito / AC | Tipo | Descripción de la Prueba | Criterio de Aserción Automatizado (Assert) |
|---|---|---|---|---|
| **INF-001** | K11 | Linter | Verificación de buenas prácticas e idempotencia en Ansible. | `ansible-lint ansible/playbooks/*.yml` retorna 0 advertencias o errores. |
| **INF-002** | AC8-E5 | Idempotencia | Re-ejecución limpia de playbooks en las 7 VMs. | Segunda ejecución consecutiva retorna exactamente `changed=0, failed=0`. |
| **INF-003** | K9, INFRA 10.2| Red | Aislamiento de puertos por firewall (UFW en VM1/VM3/VM4/VM6/VM7 y firewalld en VM2/VM5). | Conexión externa directa a puerto 5432 (Postgres en VM4) o 6379 (Redis en VM5) rechazada por defecto. |
| **INF-004** | INFRA 10.2 | Red | Conexión permitida exclusivamente en pares origen-destino. | Tráfico desde VM3 a VM4 puerto 5432 y VM6 puerto 9092 opera con éxito. |
| **INF-005** | K9, RNF-02 | Seguridad | Conexión segura TLS autofirmada en API Gateway (VM1). | Petición a `https://quickpatch.internal` (puerto 443) negocia cifrado TLS exitoso. |
| **INF-006** | INFRA 10.3 | Acceso | Bloqueo de acceso SSH directo como root en las 7 VMs. | Intento de conexión SSH como usuario root (`ssh root@10.43.x.x`) es rechazado en las 7 VMs (`PermitRootLogin no`); acceso restringido a usuarios estándar no privilegiados. |
| **INF-007** | INFRA 9.2, ADR-016 | Backup | Automatización de backup diario de PostgreSQL. | Ejecución de cron `pg_dump` transfiere dump exitosamente al bucket de Garage en VM7. |
| **INF-008** | AC5-E1 | Recuperación | Restauración de base de datos desde dump de backup en VM7. | `pg_restore` restablece esquema y datos de manera íntegra dentro de la ventana de recuperación RTO. |
| **INF-009** | INFRA 8.2 | Secretos | Cero secretos o credenciales en texto plano en Git. | Escaneo con `gitleaks` retorna 0 hallazgos de passwords o llaves privadas. |
| **INF-010** | INFRA 5.2 | k3s | Rango CIDR de k3s configurado fuera de `10.43.0.0/16`. | `--service-cidr=10.44.0.0/16` verificado; 0 colisión de red con VMs del lab. |
| **INF-011** | INFRA 7.1 | Observabilidad| Exportación de métricas de servidor vía `node_exporter`. | Prometheus en VM7 recolecta métricas de CPU, RAM y disco cada 15 segundos. |
| **INF-012** | INFRA 7.1 | Observabilidad| Recolección de logs de contenedores con Promtail y Loki. | Logs de microservicios visibles en Grafana filtrados por etiqueta de servicio `{job="..."}` o `{container_name="..."}`. |
| **INF-013** | RNF-02, RNF-07 | Seguridad DAST| Escaneo dinámico de vulnerabilidades web con OWASP ZAP contra API Gateway (VM1). | ZAP Baseline Scan reporta 0 vulnerabilidades de severidad Alta o Crítica en endpoints expuestos. |
| **INF-014** | AC5-E4 | Resiliencia | Desconexión temporal de Kafka y persistencia en Outbox. | Eventos generados durante caída de Kafka se publican automáticamente tras reconexión. |
| **INF-015** | INFRA 5.8 | Despliegue | Actualización con Rolling Update sin caída del backend. | Despliegue de nueva versión en k3s mantiene disponibilidad 100% durante el cambio. |
| **INF-016** | RF-26, RNF-08 | CI/CD | Pipeline automatizado con corte ante fallos de prueba. | Falla simulada en suite unitaria detiene el pipeline de GitHub Actions y bloquea el despliegue a VM3. |

---

### 7.12 Módulo: Pruebas End-to-End de Sistema y Flujo Crítico (`quickpatch/tests/e2e`)
* **Requisitos:** RF-27 (Flujo Crítico Completo) | SAD: AC1-E2, AC4-E1, AC4-E2, AC5-E6

| ID Caso | Requisito / AC | Tipo | Descripción de la Prueba | Criterio de Aserción Automatizado (Assert) |
|---|---|---|---|---|
| **E2E-001** | **RF-27, AC1-E2** | E2E Completo | **Flujo Crítico Completo: Solicitud → Matching → Cotización → Evidencia → Pago → Calificación.** | 100% de los 10 pasos completados con éxito en Playwright; base de datos consistente; factura emitida en Payments; técnico en estado disponible al terminar. |
| **E2E-002** | RF-18, AC4-E2 | UI Web E2E | Carga y navegación en Dashboard Operativo en Angular. | Panel carga en menos de 1.5s; tabla de solicitudes activas y filtros operativos sin scroll roto. |
| **E2E-003** | RF-19 | UI Web E2E | Aprobación de técnico postulante desde el panel web de Admin. | Admin aprueba técnico; notificación de éxito visible; técnico pasa a estado Aprobado. |
| **E2E-004** | RF-21, AC8-E1 | UI Web E2E | Alta de nuevo tenant empresarial desde interfaz de Admin. | Tenant registrado y operativo en menos de 1 hora sin interrupción para tenants existentes. |
| **E2E-005** | AC4-E1 | UI Web E2E | Creación asistida de solicitud en un máximo de 3 pasos. | Flujo completado en exactamente 3 pantallas (Categoría, Dirección, Confirmación) (RNF-11). |
| **E2E-006** | AC4-E2 | UI Web E2E | Adaptabilidad en resoluciones Desktop, Tablet y Mobile. | 100% de pantallas utilizables sin scroll horizontal ni elementos cortados (RNF-12). |
| **E2E-007** | RF-10 | E2E Alterno | Flujo alterno: Técnico rechaza solicitud y sistema reasigna. | Solicitud reasignada a segundo técnico elegible automáticamente; técnico 1 liberado. |
| **E2E-008** | RF-35 | E2E Alterno | Flujo alterno: Cotización rechazada y nueva cotización aceptada. | Cliente rechaza 1ra cotización; técnico emite 2da cotización ajustada; cliente acepta. |
| **E2E-009** | RF-22 | E2E Alterno | Flujo alterno: Pago rechazado y segundo cobro exitoso. | Pasarela simula tarjeta sin fondos; cliente reintenta con tarjeta válida; pago aprobado. |
| **E2E-010** | RF-36 | E2E Cancel | Cancelación de solicitud por el cliente antes del inicio. | Solicitud pasa a `cancelado`; técnico asignado es liberado inmediatamente. |
| **E2E-011** | AC6-E5 | E2E Trazabilidad| Reconstrucción completa de disputa mediante eventos. | Secuencia cronológica 100% íntegra con marca de tiempo UTC y fotos accesibles en Garage. |
| **E2E-012** | AC5-E6 | E2E Calidad | Tasa de respuestas 5xx durante ejecución repetitiva de E2E. | Tasa de errores 5xx del servidor inferior al 1% en 20 iteraciones del flujo crítico. |

---

### 7.13 Módulo: Pruebas de Rendimiento, Estrés y Capacidad (`quickpatch/tests/performance`)
* **Requisitos:** RNF-05, RNF-06, RNF-07, RNF-08 | K10 | SAD: AC2-E1, AC2-E2, AC2-E3, AC2-E4, AC2-E5

| ID Caso | Requisito / AC | Tipo | Descripción de la Prueba | Criterio de Aserción Automatizado (Assert) |
|---|---|---|---|---|
| **PRF-001** | AC2-E1 | Rendimiento | Búsqueda geoespacial cercana en hora pico con k6. | Latencia de respuesta `http_req_duration p(95) < 3000 ms` bajo 50 VU. |
| **PRF-002** | AC2-E2 | Rendimiento | Consulta de historial paginado con acumulación de datos. | Carga de página de historial en menos de 1.5 segundos (p95 < 1500 ms). |
| **PRF-003** | AC2-E3 | Rendimiento | Procesamiento en segundo plano desde solicitud hasta oferta. | Lapso total cronometrado inferior a 7.0 segundos para el 95% de las solicitudes. |
| **PRF-004** | **AC2-E4** | Estrés Pico | **Pico de carga inesperado de 150 solicitudes de matching concurrentes.** | k6 inyecta 150 VU de estrés en QA (VM2 - ADR-015) durante 5 minutos; tasa de error 5xx = 0% o degradación controlada; 0 caídas de pod; Producción (VM3) protegida. |
| **PRF-005** | **AC2-E5, K10** | Capacidad | **Presupuesto y estabilidad de recursos bajo carga.** | 0 procesos terminados por `OOMKilled`; 0 caída de pods; degradación controlada; registro del consumo de CPU y RAM para establecer el baseline operativo formal. |
| **PRF-006** | SAD 1.2 | Limpieza | Purga de datos del tenant de prueba tras test de carga. | Scripts de teardown independientes limpian registros de `tenant_qa_loadtest` en las bases de datos de ServiceRequest y Matching en el ambiente de QA (VM2); la base de datos de producción en VM4 permanece aislada e intacta. |
| **PRF-007** | RNF-06 | Resistencia | Operación sostenida bajo carga normal (50 VU) por 30 minutos. | Cero fugas progresivas de memoria; consumo de CPU estable por debajo del 75%. |
| **PRF-008** | RNF-08 | Rollback | Mecanismo de Rollback Automático ante fallo de carga. | Pipeline detecta violación de umbral y ejecuta `kubectl rollout undo` de forma automatizada. |
| **PRF-009** | INFRA 5.7 | Conexiones | Pool de conexiones a PostgreSQL en QA (VM2) bajo 150 VU. | Pool opera dentro de los límites de `max_connections` en QA sin errores `too many clients`, sin afectar a producción en VM4. |
| **PRF-010** | AC9-E6 | Alertas | Disparo de alertas en Grafana al superar el 85% de RAM. | Alerta activa generada en Grafana alertando al equipo antes de un desalojo. |

---

---

## 8. Gestión de Datos de Prueba (Test Data)

Para garantizar la repetibilidad, el aislamiento y la independencia de las pruebas, se define una política estricta de gestión y aprovisionamiento de datos de prueba (Test Data Management - TDM).

### 8.1 Estrategia de Aprovisionamiento
1. **Datos Sintéticos y Efímeros (Shift-Left):** En las compuertas 1 (Local) y 2 (CI), los datos se generan dinámicamente mediante semillas (*seeds*) administradas por **Testcontainers**. Al finalizar la suite, los contenedores y los datos se destruyen automáticamente.
2. **Aislamiento Multi-Tenant Estricto (AC6-E2):** Ninguna prueba utiliza datos compartidos entre tenants. Se crean tenants dedicados exclusivamente para propósitos de prueba para evitar colisiones:
   - `tenant_qa_automated`: Utilizado para pruebas de integración y flujos E2E de regresión.
   - `tenant_qa_loadtest` (UUID: `a1a1a1a1-bbbb-cccc-dddd-eeeeeeeeeeee`): Utilizado exclusivamente para las pruebas de carga con k6 sobre el ambiente dedicado de QA en VM2 (PostgreSQL propio de QA).
3. **Cumplimiento PCI-DSS en Datos de Prueba (K2, AC6-E1):** Está terminantemente prohibido el uso de datos reales de tarjetas de crédito o débito. Todas las pruebas de pagos utilizan **tokens opacos sintéticos** provistos por las librerías mock de pasarelas (ej. `tok_test_visa_approved_001`, `tok_test_declined_funds`).

### 8.2 Perfiles y Conjuntos de Datos Semilla (Fixtures)

| Tipo de Dato | Identificador / Clave | Atributos y Coordenadas de Prueba | Propósito de Validación |
|---|---|---|---|
| **Tenant Empresarial** | `tenant_empresa_alfa` | NIT: `900.123.456-1`, Razón Social: *Servicios Alfa S.A.S.*, Activo: `true` | Validar flujos B2B y aislamiento RLS |
| **Tenant Carga** | `tenant_qa_loadtest` | UUID: `a1a1a1a1-bbbb-cccc-dddd-eeeeeeeeeeee`, Cuota: 10,000 req/min | Pruebas de carga (50 VU) y estrés (150 VU) exclusivamente en QA (VM2) |
| **Cliente Hogar** | `usr_cliente_01` | Email: `qa.cliente1@quickpatch.local`, Rol: `CLIENTE`, Tel: `3001234567` | Solicitud y pago de servicios |
| **Técnico Cerrajería** | `usr_tec_cerrajero_01` | Especialidad: Cerrajería, Coordenadas: Chapinero (`4.6486, -74.0630`), Estado: `disponible`, Rating: `4.8` | Matching por cercanía geográfica |
| **Técnico Plomería** | `usr_tec_plomero_01` | Especialidad: Plomería, Coordenadas: Suba (`4.7431, -74.0886`), Estado: `disponible`, Rating: `4.2` | Filtrado por categoría y radio de cobertura |
| **Técnico Ocupado** | `usr_tec_ocupado_01` | Especialidad: Cerrajería, Coordenadas: Usaquén (`4.6980, -74.0305`), Estado: `ocupado` | Verificación de exclusión de matching (RN-M6) |
| **Ubicación Solicitud A** | Coordenadas: `4.6500, -74.0610` | Zona: Chapinero (Distancia a `usr_tec_cerrajero_01` < 300 metros) | Escenario de asignación inmediata |
| **Ubicación Solicitud B** | Coordenadas: `4.8100, -74.0300` | Zona: Chía / Límite Norte (Fuera del radio de cobertura estándar) | Escenario `matching.no-technician-available` |
| **Token Pasarela Aprobado** | `tok_wompi_test_approved_ok` | Franquicia: Visa simulada, Fondos: Ilimitados | Flujo exitoso de autorización y captura |
| **Token Pasarela Rechazado** | `tok_wompi_test_declined_insufficient` | Error simulado: `INSUFFICIENT_FUNDS` | Manejo de rechazo de pago y reintento (RN-SR5) |
| **Evidencia Fotográfica** | `mock_cerrojo_reparado.jpg` | Tamaño: 245 KB, MIME: `image/jpeg`, Hash: `e3b0c44298fc1c149afb...` | Subida a Garage (VM7) antes de completar servicio |

### 8.3 Ciclo de Vida y Limpieza de Datos (Tear-down)
* **Post-Test Local/CI:** Las bases de datos en Testcontainers se eliminan al destruirse el contenedor Docker.
* **Post-Carga en QA (VM2):** Al concluir las pruebas de k6 de 50/150 VU en el ambiente de QA, se ejecuta automáticamente el procedimiento de purga en el PostgreSQL propio de QA en VM2 respetando el aislamiento de bases de datos independientes:
  ```sql
  -- 1. En la base de datos de ServiceRequest Service (QA en VM2):
  DELETE FROM service_requests WHERE tenant_id = 'a1a1a1a1-bbbb-cccc-dddd-eeeeeeeeeeee';

  -- 2. En la base de datos de Matching Service (QA en VM2):
  DELETE FROM matching_attempts WHERE tenant_id = 'a1a1a1a1-bbbb-cccc-dddd-eeeeeeeeeeee';
  ```
  Esto garantiza que la base de datos de QA en VM2 conserve espacio libre y no degrade las lecturas de los índices espaciales de PostGIS; la base de datos de producción en VM4 permanece 100% aislada e intacta.

---

## 9. Gestión y Reporte de Defectos (Bug Report)

Para asegurar la trazabilidad integral y el cierre efectivo de no conformidades detectadas por el equipo de QA o por los pipelines automatizados, se establece el siguiente protocolo de gestión de defectos.

### 9.1 Ciclo de Vida del Defecto
```
[ Nuevo (Reportado por QA / CI) ]
                │
                ▼
        [ En Triage / Asignado ]
                │
                ├──────────────────────────┐ (Rechazado / No reproducible / Duplicado)
                ▼                          ▼
       [ En Corrección (Dev) ]     [ Descartado ]
                │
                ▼
  [ Listo para Verificación QA ]
                │
        ┌───────┴───────┐
 (Fallo)│               │ (Éxito)
        ▼               ▼
   [ Reabierto ]   [ Cerrado ]
```

### 9.2 Matriz de Severidad, Prioridad y Tiempos de Respuesta (SLA)

| Severidad | Descripción del Impacto | Ejemplos Críticos en QUICKPATCH | Prioridad Jira | SLA de Resolución |
|---|---|---|:---:|:---:|
| **S1 — Blocker** | Bloqueo total del sistema, violación de seguridad o pérdida de datos. | Violación de aislamiento multi-tenant (RLS); almacenamiento de PAN/CVV (PCI-DSS K2); pod de Matching en `OOMKilled` (VM3). | Muy Alta (P1) | < 4 horas |
| **S2 — Crítico** | Falla en una función principal de negocio sin alternativa operativa. | Falla en algoritmo de matching (no asigna técnicos disponibles); bloqueo en webhook de pagos; imposibilidad de adjuntar evidencia fotográfica en Garage. | Alta (P2) | < 24 horas |
| **S3 — Mayor** | Falla funcional relevante, pero existe un camino alternativo temporal. | Error en cálculo de comisiones de la plataforma; desfase en tiempos de expiración de cotizaciones; inconsistencia en contrato REST menor. | Media (P3) | < 48 horas |
| **S4 — Menor / Cosmético** | Defecto superficial que no impide la operación ni la integridad de los datos. | Desalineación tipográfica en Web Admin (VM2); falta de descripción en una etiqueta de Swagger; error ortográfico en mensaje de notificación. | Baja (P4) | Siguiente Sprint |

### 9.3 Plantilla Estándar de Bug Report (Jira / Markdown)

Todo defecto reportado debe utilizar la siguiente estructura obligatoria:

```markdown
### [BUG-ID] [Módulo] Resumen conciso del defecto

* **ID del Caso de Prueba Relacionado:** (Ej. `PAY-003`, `MAT-005`, `AC6-E2`)
* **Severidad:** S1 - Blocker / S2 - Crítico / S3 - Mayor / S4 - Menor
* **Prioridad:** P1 / P2 / P3 / P4
* **Repositorio Afectado:** (Ej. `quickpatch-matching`, `quickpatch-payments`, etc.)
* **Ambiente de Detección:** Local / CI (GitHub Actions) / VM3 Staging / VM1 Gateway
* **Versión / Commit Hash:** `git rev-parse --short HEAD`

#### Descripción del Problema
Explicación técnica detallada de la condición anómala detectada.

#### Pasos para Reproducir
1. Configurar el tenant en sesión `tenant_empresa_alfa`.
2. Enviar solicitud `POST /v1/service-requests` con payload X.
3. Observar la respuesta del microservicio.

#### Resultado Esperado
El sistema debe retornar HTTP 201 Created y publicar el evento `service-request.created` en el topic Kafka correspondiente con `eventId` único (ADR-007).

#### Resultado Obtenido
El sistema retornó HTTP 500 Internal Server Error o no generó el evento en la tabla `outbox_events`.

#### Evidencias y Trazas
* **Logs de Loki (VM7):** `trace_id`, error stack trace.
* **Captura de Pantalla / Video:** (Adjuntar archivo si aplica para Angular o Flutter).
* **Payload JSON:** Petición y respuesta capturadas.
```

---

## 10. Informe de Ejecución de Pruebas (Test Execution Report - Sprint 3)

### 10.1 Resumen Ejecutivo del Incremento de Valor
En el marco del **Sprint 3 (Semana 10)**, el equipo de Aseguramiento de Calidad (QA) ha completado el diseño, estructuración y especificación formal de la arquitectura de pruebas integral para la plataforma QUICKPATCH sobre los 13 repositorios y el entorno de las 7 Máquinas Virtuales.

| Métrica de Aseguramiento de Calidad | Meta del Sprint 3 | Estado Alcanzado | Cumplimiento |
|---|:---:|:---:|:---:|
| **Casos de Prueba Diseñados y Formalizados** | $\ge 150$ casos | **187 casos de prueba** | 100% (Superado) |
| **Requisitos Funcionales con Cobertura (RTM)** | 32 / 32 RFs activos | **32 RFs mapeados (100% vigentes del SRS v3.2)** | 100% |
| **Escenarios de Calidad del SAD con Cobertura** | 37 / 37 automatizables | **37 ACs mapeados (100% arquitectura/software del SAD v2.13)** | 100% |
| **Compuertas de Calidad Automatizadas Definidas** | 4 compuertas | **4 compuertas diseñadas (Local, CI, QA en VM2, Producción)** | 100% |
| **Validación de Restricciones Críticas (Killers)** | K2, K5, K9, K10 | **Diseñados y especificados en la arquitectura de pruebas** | 100% |
| **Mecanismo de Bloqueo Local Pre-Push** | 12 repositorios + principal | **Script unificado de Git Hooks diseñado para distribución** | 100% |

### 10.2 Estado de los Componentes y Servicios Evaluados
1. **Contratos e Interoperabilidad (`quickpatch-api-gateway` y `quickpatch-kafka`):** 
   - Contratos OpenAPI 3.0 diseñados y especificados formalmente para los 8 servicios.
   - 9 esquemas de eventos Kafka definidos con validación obligatoria de `eventId`, `tenantId` y `occurredAt`.
2. **Seguridad y Aislamiento:**
   - Pruebas de sanitización de logs y payloads planeadas para certificar 0% de campos sensibles de tarjeta de crédito (K2).
   - Políticas de Row-Level Security (RLS) diseñadas y catalogadas en la matriz para las tablas compartidas en PostgreSQL.
3. **Rendimiento y Capacidad de Infraestructura:**
   - La prueba de carga (50 VU) y estrés (150 VU en Matching) está planeada y especificada para ejecutarse contra el ambiente de QA (VM2 - ADR-015) con monitoreo en Prometheus/Grafana (VM7).
   - Estrategia de rollback automático (`kubectl rollout undo`) y alerta diseñada formalmente ante fallos de despliegue, saturación crítica o caídas de pods en k3s.

### 10.3 Evidencias Preparadas para la Presentación y Sustentación
1. **Matriz RTM Completa:** Trazabilidad bidireccional desde los requisitos del SRS (versión vigente 3.2), escenarios del SAD (versión vigente 2.13) e Historias de Usuario de Jira (Sprint 3 — SCRUM-317) hasta las aserciones de código de prueba.
2. **Defensa de la Topología en las 7 VMs:** Justificación técnica demostrando cómo se protege producción aislando las pruebas de sistema y estrés en la VM2 (QA según ADR-015).
3. **Cuadro Comparativo de Herramientas:** Sustentación académica y técnica de la selección de Playwright, k6, Testcontainers y Spectral frente a herramientas legadas.

### 10.4 Protocolo de Ejecución y Almacenamiento de Evidencias (Subtareas SCRUM-307 y SCRUM-315)
Para garantizar la reproducibilidad y el soporte probatorio exigido por el Sprint 3, la suite de pruebas almacena sus artefactos y evidencias de ejecución estructuradas en el directorio `quickpatch/tests/evidence/`:

```
quickpatch/tests/evidence/
├── e2e/               Reportes HTML de Playwright y ejecuciones Newman (qa.quickpatch.internal)
├── performance/       Reportes JSON y resúmenes de k6 (50 VU normal y 150 VU estrés)
├── security/          Salidas de escaneo Regex PCI-DSS en logs de Loki (0 PAN / 0 CVV) y reportes ZAP Baseline
└── contract/          Reportes de Spectral CLI sobre OpenAPI y validación AJV de esquemas Kafka
```

#### 10.4.1 Resumen de Estado de Ejecución del Incremento (Release Sprint 3)

| Nivel de Prueba | Total Casos | Diseñados | Automatizados | Por Ejecutar en QA | Criterio de Aprobación |
|---|:---:|:---:|:---:|:---:|---|
| **Unitarias / CI (Compuerta 1)** | 92 | 92 | 92 | 0 | Cobertura $\ge 80\%$, linters sin errores en GitHub Actions |
| **Integración / Testcontainers (Compuerta 1)** | 48 | 48 | 48 | 0 | 100% pruebas de persistencia y Kafka efímero aprobadas |
| **Contratos (OpenAPI & Schemas)** | 10 | 10 | 10 | 0 | 0 errores en Spectral CLI y esquemas AJV consistentes |
| **Pruebas de Sistema / E2E (Compuerta 2 - VM2)** | 12 | 12 | 12 | Release QA | Flujo crítico de 10 pasos exitoso en Playwright |
| **Carga y Rendimiento (Compuerta 2 - VM2)** | 10 | 10 | 10 | Release QA | 50 VU normal con p95 < 3s; 150 VU estrés sin caída de pods, 0 OOMKilled y degradación controlada |
| **Seguridad y PCI-DSS (Compuerta 2 - VM2)** | 15 | 15 | 15 | Release QA | 0 coincidencias de PAN/CVV en logs y 0 alertas altas en ZAP |
| **Total Global** | **187** | **187** | **187** | **Incremento QA** | **100% trazabilidad e integridad técnica garantizada** |

---

## 11. Control de Versiones del Documento

| Versión | Fecha | Autor | Descripción del Cambio |
|---|---|---|---|
| **1.0** | 3 de octubre de 2026 | Líder de Aseguramiento de Calidad (QA Lead) | Versión inicial formal para la entrega del Sprint 3 (Semana 10). Incluye cobertura completa del estándar de documentación de pruebas: Plan de Pruebas (Test Plan), Estrategia de Pruebas (Test Strategy), Escenarios de Calidad (Test Scenarios), Matriz de Trazabilidad (RTM) cubriendo los 32 RFs activos del SRS v3.2 y los 37 escenarios de software del SAD v2.13, Catálogo de 187 Casos de Prueba (Test Cases), incorporación del Ambiente de QA en VM2 (ADR-015), adopción de Garage para almacenamiento S3 (ADR-016), Gestión de Datos de Prueba (Test Data), Gestión de Defectos (Bug Report), e Informe de Ejecución del Incremento (Test Execution Report). |
| **1.1** | 4 de octubre de 2026 | Líder de Aseguramiento de Calidad (QA Lead) | Sincronización técnica del stack multirepo V2 (.NET 10, Java 25, Angular 22, Flutter 3.47, Vitest), incorporación formal de la Matriz de Trazabilidad hacia Historias de Usuario de Jira (subtarea SCRUM-317), refinamiento de compuertas k6 y especificación del protocolo de evidencias para el Informe de Pruebas (SCRUM-307 / SCRUM-315). |
| **1.2** | 5 de octubre de 2026 | Líder de Aseguramiento de Calidad (QA Lead) | Incorporación de observaciones del equipo: (1) Enfoque exclusivo de carga (50 VU) y estrés (150 VU) en QA (VM2 - ADR-015), protegiendo Producción (VM3) de estrés rutinario; (2) Reemplazo de umbral rígido de 6.5 GiB por criterios objetivos de estabilidad (0 OOMKilled, 0 caída de pods, degradación controlada y baseline de CPU/RAM); (3) Referencia dinámica a Jira para estados de subtareas; (4) Retiro de Pact, consolidando la validación contractual sobre OpenAPI, Spectral CLI y AJV en quickpatch-contracts. |
| **1.3** | 6 de octubre de 2026 | Líder de Aseguramiento de Calidad (QA Lead) | Corrección de aislamiento de base de datos en pruebas de carga (revisión PR #20): eliminación de toda referencia a VM4 en pasos de carga y teardown; la inyección de carga y la purga SQL se direccionan exclusivamente al PostgreSQL propio de QA en VM2, garantizando que la BD de producción en VM4 permanezca 100% aislada. |

