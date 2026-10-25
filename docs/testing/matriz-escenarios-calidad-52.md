# Matriz de Evaluación de los 52 Escenarios de Calidad del SAD (SCRUM-565)

**Código del Documento:** `MTX-CAL-SAD-52-2026-10-25`  
**Versión:** `2.0 Final`  
**Fecha:** 25 de octubre de 2026  
**Responsable:** Katherine Bravo (`ka.bravo@javeriana.edu.co`) — QA Lead  
**Trazabilidad Jira:** Tarea `SCRUM-565` | SAD V2.24 (52 Escenarios de Arquitectura) | Documento de Pruebas `TD.md` V3.0  
**Criterio de Evaluación:** Conforme a la directriz técnica de QA, un escenario se clasifica como **Cumple** únicamente si cuenta con una **medición cuantitativa explícita**, **fecha de ejecución** y **archivo de evidencia verificable** en el repositorio. Todo escenario sin medición cuantitativa formal permanece como **Pendiente**.

---

## 1. Convenciones de Estado

* **Cumple:** Escenario evaluado con medición cuantitativa objetiva (tiempo de respuesta, tasa de error, número de trazas, códigos HTTP verificados), fecha exacta y archivo de evidencia en el repositorio.
* **Pendiente:** Escenario en proceso de instrumentación o cuya medición cuantitativa formal está programada para fases posteriores (ej. UAT presencial con PO, inyección de fallas de infraestructura).
* **No Cumple:** Escenario ejecutado cuya medición violó el umbral de aceptación establecido en el SAD.

---

## 2. Matriz Consolidada de los 52 Escenarios de Calidad

| ID Escenario | Atributo de Calidad | Descripción del Escenario de Arquitectura | Medida de Respuesta Esperada (SAD) | Medición Cuantitativa Obtenida | Estado de Evaluación | Archivo de Evidencia (Ruta Relativa) | Fecha de Medición |
|---|---|---|---|---|:---:|---|:---:|
| **AC1-E1** | Usability | Registro de cliente en interfaz móvil | Tiempo de compleción $\le 2\text{ min}$ | Sin medición presencial en dispositivo | **Pendiente** | `docs/testing/uat-product-owner.md` | *(Pendiente)* |
| **AC1-E2** | Usability | Solicitud de servicio de emergencia | $\le 3\text{ clics}$ o $\le 60\text{ s}$ | Sin medición de interacción de usuario | **Pendiente** | `docs/testing/uat-product-owner.md` | *(Pendiente)* |
| **AC1-E3** | Usability | Claridad en visualización de estados | Comprensión inmediata $\le 5\text{ s}$ | Sin prueba de usabilidad presencial | **Pendiente** | `docs/testing/uat-product-owner.md` | *(Pendiente)* |
| **AC1-E4** | Usability | Consulta de comprobante de pago | Acceso y descarga $\le 10\text{ s}$ | Sin prueba de usabilidad presencial | **Pendiente** | `docs/testing/uat-product-owner.md` | *(Pendiente)* |
| **AC1-E5** | Usability | Panel de administración web para técnicos | Aprobación/rechazo en $\le 30\text{ s}$ | Sin medición cronometrada con admin | **Pendiente** | `docs/testing/uat-product-owner.md` | *(Pendiente)* |
| **AC1-E6** | Usability | Accesibilidad y contraste WCAG 2.1 AA | 100% contraste $\ge 4.5:1$ | Sin escaneo formal con Axe/Lighthouse | **Pendiente** | `docs/testing/capacidad-interaccion-scrum-569.md` | *(Pendiente)* |
| **AC2-E1** | Performance | Latencia de asignación automática (Matching) | Latencia $\le 60\text{ s}$ en percentil 95 | **p95 = 73.55 ms** en flujo de matching | **Cumple** | `tests/performance/evidencias/k6-load-50vu-summary.json` | 18/10/2026 |
| **AC2-E2** | Performance | Carga concurrente moderada (50 VU) | $p95 \le 2.0\text{ s}$ y error $< 1\%$ | **p95 = 73.55 ms**, **Error = 0.00%** (0/5,755) | **Cumple** | `tests/performance/evidencias/k6-load-50vu-summary.json` | 18/10/2026 |
| **AC2-E3** | Performance | Carga concurrente extrema de estrés (150 VU) | $p95 \le 5.0\text{ s}$ y error $< 5\%$ | **p95 = 415.39 ms**, **Error = 0.00%** (0/38,876) | **Cumple** | `tests/performance/evidencias/k6-stress-150vu-summary.json` | 18/10/2026 |
| **AC2-E4** | Performance | Throughput sostenido en ráfagas de demanda | Capacidad de procesamiento continuo | **160.45 req/s** sostenidas durante 4 min | **Cumple** | `tests/performance/evidencias/k6-stress-150vu-summary.json` | 18/10/2026 |
| **AC2-E5** | Performance | Estabilidad de memoria bajo estrés | 0 caídas, RAM en VM3 $\le 6.5\text{ GiB}$ | **0 OOMKilled**, **0 caídas de pods** en estrés | **Cumple** | `tests/performance/evidencias/k6-stress-150vu-qa-2026-10-18.txt` | 18/10/2026 |
| **AC2-E6** | Performance | Latencia de consulta de catálogo con caché | $p95 \le 100\text{ ms}$ en lectura Redis | **p95 = 20.94 ms** en GET `/categories` | **Cumple** | `tests/performance/evidencias/k6-load-50vu-summary.json` | 18/10/2026 |
| **AC3-E1** | Availability | Caída de un pod de microservicio stateless | Reemplazo y recuperación $\le 30\text{ s}$ | Sin prueba de inyección de caos (Chaos) | **Pendiente** | `infrastructure/ansible/` | *(Pendiente)* |
| **AC3-E2** | Availability | Indisponibilidad temporal de broker Kafka | Reintento vía Outbox sin pérdida de datos | Sin corte simulado de broker Kafka | **Pendiente** | `apps/kafka/` | *(Pendiente)* |
| **AC3-E3** | Availability | Caída de réplica primaria PostgreSQL | Failover de base de datos $\le 60\text{ s}$ | Sin simulación de caída de nodo VM5 | **Pendiente** | `infrastructure/ansible/` | *(Pendiente)* |
| **AC3-E4** | Availability | Aislamiento ante fallo en pasarela de pagos | Degradación controlada sin caída de app | Sin timeout simulado de pasarela externa | **Pendiente** | `apps/backend/services/payments/` | *(Pendiente)* |
| **AC3-E5** | Availability | Recuperación ante corte de conectividad | Sincronización offline $\le 10\text{ s}$ | Sin desconexión forzada en red móvil | **Pendiente** | `apps/mobile/` | *(Pendiente)* |
| **AC3-E6** | Availability | Disponibilidad general de la plataforma | Uptime mensual $\ge 99.5\%$ | En recolección de telemetría de clúster | **Pendiente** | `docs/testing/TD.md` §3 | *(Pendiente)* |
| **AC4-E1** | Scalability | Escalado automático ante incremento de carga | Incremento de réplicas HPA $\le 60\text{ s}$ | Sin medición de tiempos de autoscaling HPA | **Pendiente** | `infrastructure/ansible/` | *(Pendiente)* |
| **AC4-E2** | Scalability | Escalado horizontal de pods en k3s | Despliegue de 1 a N pods sin bloqueo | Sin métricas de tiempos de escalado | **Pendiente** | `infrastructure/ansible/` | *(Pendiente)* |
| **AC4-E3** | Scalability | Particionado de topics Kafka bajo volumen | Balanceo equitativo entre particiones | Sin telemetría de particionado de eventos | **Pendiente** | `apps/kafka/` | *(Pendiente)* |
| **AC4-E4** | Scalability | Crecimiento de volumen de almacenamiento S3 | Almacenamiento elástico sin degradación | Sin saturación de volumen Garage S3 | **Pendiente** | `infrastructure/ansible/` | *(Pendiente)* |
| **AC4-E5** | Scalability | Conexiones concurrentes a PostgreSQL | Pool de conexiones $\le 80\%$ uso | Sin monitoreo del pool PgBouncer en pico | **Pendiente** | `infrastructure/ansible/` | *(Pendiente)* |
| **AC4-E6** | Scalability | Escalabilidad de caché Redis | Hit ratio $\ge 85\%$ bajo concurrencia | Sin telemetría de hit ratio de Redis | **Pendiente** | `apps/backend/services/catalog/` | *(Pendiente)* |
| **AC5-E1** | Reliability | Reintento automático de eventos fallidos | Dead Letter Queue (DLQ) tras 3 intentos | Sin prueba de mensajes envenenados | **Pendiente** | `apps/kafka/` | *(Pendiente)* |
| **AC5-E2** | Reliability | Consistencia eventual entre microservicios | Convergencia de estado $\le 5\text{ s}$ | Sin medición de sincronización temporal | **Pendiente** | `docs/architecture/SDD.md` | *(Pendiente)* |
| **AC5-E3** | Reliability | Integridad transaccional de estados | 0 estados inconsistentes en PostgreSQL | Sin auditoría masiva de integridad SQL | **Pendiente** | `apps/backend/services/service-request/` | *(Pendiente)* |
| **AC5-E4** | Reliability | Resiliencia ante desconexión de clientes | Reconexión automática $\le 5\text{ s}$ | Defecto SCRUM-606 abierto en mitigación | **Pendiente** | `docs/testing/registro-defectos-sprint4-sprint5.md` | *(Pendiente)* |
| **AC5-E5** | Reliability | Deduplicación e idempotencia de eventos | 0 efectos duplicados por `X-Event-Id` | **0 duplicados** en tabla `processed_events` | **Cumple** | `tests/e2e/evidencias/scrum-78-qa-2026-10-22.txt` | 22/10/2026 |
| **AC5-E6** | Reliability | Operación sin caídas durante suites E2E | 0 fallos en suite E2E programada | **100% PASS** en 291 aserciones de sistema | **Cumple** | `tests/e2e/evidencias/scrum-incremento-tecnico-qa-2026-10-22.txt` | 22/10/2026 |
| **AC6-E1** | Security | Cumplimiento estricto PCI-DSS en logs | 0 números PAN o CVV en DB o Loki | **0 tarjetas (PAN)** en 2,649 trazas Loki | **Cumple** | `tests/security/evidencias/pci-dss-loki-qa-2026-10-18.txt` | 18/10/2026 |
| **AC6-E2** | Security | Aislamiento lógico multi-tenant (RLS) | 0 fugas de datos; respuesta HTTP 404 | **5 de 5 (100%)** accesos ajenos $\to$ 404 | **Cumple** | `tests/e2e/evidencias/scrum-108-aprobacion-rechazo-qa-2026-10-22.txt` | 22/10/2026 |
| **AC6-E3** | Security | Control de acceso basado en roles (RBAC) | 100% accesos sin rol bloqueados | **6 de 6 (100%)** accesos no autorizados $\to$ 403 | **Cumple** | `tests/e2e/evidencias/scrum-56-registro-tecnico-qa-2026-10-22.txt` | 22/10/2026 |
| **AC6-E4** | Security | Token JWT comprometido o expirado | 100% tokens expirados rechazados | **4 de 4 (100%)** tokens inválidos $\to$ 401 | **Cumple** | `tests/e2e/evidencias/mvp-qa-sprint4-2026-10-18.txt` | 18/10/2026 |
| **AC6-E5** | Security | Reconstrucción inmutable de disputas | Trazabilidad con timestamp y actor | Sin auditoría forense de base de datos | **Pendiente** | `apps/backend/services/service-request/` | *(Pendiente)* |
| **AC6-E6** | Security | Registro de auditoría en pagos | Trazabilidad inmutable de cobros | Sin extracción formal de log de auditoría | **Pendiente** | `apps/backend/services/payments/` | *(Pendiente)* |
| **AC6-E7** | Security | No repudio de acciones críticas | Firma, usuario e IP en auditoría | Sin auditoría formal de `audit_logs` | **Pendiente** | `apps/backend/services/identity/` | *(Pendiente)* |
| **AC6-E8** | Security | Mitigación de fuerza bruta en login | Bloqueo temporal tras 5 fallos (423) | Sin corrida automatizada de fuerza bruta | **Pendiente** | `apps/backend/services/identity/` | *(Pendiente)* |
| **AC7-E1** | Maintainability | Pipeline de integración continua (CI) | CI ejecuta linters y pruebas en push | **1,032 pruebas CI** ejecutadas (100% pass) | **Cumple** | `tests/ci-results/` | 22/10/2026 |
| **AC7-E2** | Maintainability | Desacoplamiento modular y contratos | Spectral CLI y oasdiff sin breaking | **0 breaking changes**, **0 errores Spectral** | **Cumple** | `tests/contract/README.md` | 18/10/2026 |
| **AC7-E3** | Maintainability | Incorporación de nuevo microservicio | Alta de servicio sin alterar existentes | Sin prueba de extensión arquitectónica | **Pendiente** | `docs/architecture/SAD.md` §4 | *(Pendiente)* |
| **AC7-E4** | Maintainability | Diagnóstico de anomalías distribuido | Correlación por `correlationId` | Sin extracción cruzada entre 8 servicios | **Pendiente** | `docs/testing/TD.md` §10 | *(Pendiente)* |
| **AC7-E5** | Maintainability | Reutilización de librerías transversales | Componentes de seguridad compartidos | Sin medición cuantitativa de cobertura | **Pendiente** | `apps/backend/` | *(Pendiente)* |
| **AC7-E6** | Maintainability | Validación formal previa a producción | 100% suites E2E aprobadas antes de merge | **100% compuertas 2.1 a 2.6 aprobadas** | **Cumple** | `tests/e2e/evidencias/scrum-incremento-tecnico-qa-2026-10-22.txt` | 22/10/2026 |
| **AC8-E1** | Flexibility | Alta de nuevo tenant en la plataforma | Provisión sin parada ni reinicio | Sin medición cronometrada de provisión | **Pendiente** | `infrastructure/ansible/` | *(Pendiente)* |
| **AC8-E2** | Flexibility | Escalado horizontal independiente | Microservicios escalables sin acople | Sin prueba de desacople de escalabilidad | **Pendiente** | `infrastructure/ansible/` | *(Pendiente)* |
| **AC8-E3** | Flexibility | Soporte de múltiples canales cliente | Segregación por `X-Channel-Id` | Sin suite de pruebas multicanal en QA | **Pendiente** | `apps/api-gateway/` | *(Pendiente)* |
| **AC8-E4** | Flexibility | Adaptador de geocodificación extensible | Conmutación de geocodificador sin caída | Sin prueba de conmutación de proveedor | **Pendiente** | `apps/backend/services/service-request/` | *(Pendiente)* |
| **AC8-E5** | Flexibility | Despliegue automatizado con Ansible | Aprovisionamiento probado de 7 VMs | Sin medición cronometrada del playbook | **Pendiente** | `infrastructure/ansible/playbooks/` | *(Pendiente)* |
| **AC9-E1** | Safety | Transiciones atómicas y seguras | Bloqueo de saltos inválidos (409) | **4 de 4 (100%)** transiciones inválidas $\to$ 409 | **Cumple** | `tests/e2e/evidencias/scrum-84-seguimiento-estado-qa-2026-10-22.txt` | 22/10/2026 |
| **AC9-E2** | Safety | Alerta de técnico con bajas calificaciones | Bloqueo preventivo de asignaciones | Servicio Ranking en esqueleto (sin regla) | **Pendiente** | `apps/backend/services/ranking/` | *(Pendiente)* |
| **AC9-E3** | Safety | Detección de órdenes estancadas ($> 4\text{ h}$) | Cierre y alerta automática de servicio | Sin prueba de inyección de orden estancada | **Pendiente** | `apps/backend/services/service-request/` | *(Pendiente)* |

---

## 3. Resumen Estadístico Consolidado

* **Total de Escenarios de Calidad del SAD:** **52 escenarios**.
* **Escenarios que Cumplen con Medición Cuantitativa y Evidencia:** **14 escenarios (26.9%)**.
* **Escenarios Pendientes de Medición Cuantitativa Formal:** **38 escenarios (73.1%)**.
* **Escenarios que No Cumplen (Fallos):** **0 escenarios (0.0%)**.

> **Nota Metodológica:** Los 14 escenarios marcados como **Cumple** cuentan con mediciones numéricas verificables (latencias, tasas de error, códigos de estado HTTP y conteos de trazas) registradas en archivos de evidencia del repositorio. Los 38 escenarios restantes corresponden a requerimientos arquitectónicos válidos cuya medición cuantitativa requiere instrumentos específicos (pruebas de usabilidad con usuarios, simulación de fallas de infraestructura o telemetría continua de producción) que se ejecutarán en las etapas correspondientes.
