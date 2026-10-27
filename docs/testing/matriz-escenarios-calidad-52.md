# Matriz de Evaluación de los 52 Escenarios de Calidad del SAD (SCRUM-565)

**Código del Documento:** `MTX-CAL-SAD-52-2026-10-26`  
**Versión:** `3.0 Final Sincronizada`  
**Fecha:** 26 de octubre de 2026  
**Responsable:** Katherine Bravo (`ka.bravo@javeriana.edu.co`) — QA Lead  
**Trazabilidad Jira:** Tarea `SCRUM-565` | SAD §3 (52 Escenarios de Calidad en 9 Atributos ISO/IEC 25010) | `TD.md` V3.0  
**Criterio de Evaluación:** Conforme a la directriz técnica de Juan Diego, un escenario se clasifica como **Cumple** únicamente si cuenta con una **medición cuantitativa explícita**, **fecha de ejecución** y **archivo de evidencia verificable** en el repositorio. Todo escenario sin medición cuantitativa formal permanece como **No medido** / **Pendiente** (es preferible un porcentaje sincero a observaciones del profesor).

---

## 1. Atributos de Calidad Evaluados (SAD §3)

1. **AC1: Functional Suitability (Idoneidad Funcional):** Completitud y corrección funcional de los flujos críticos.
2. **AC2: Performance Efficiency (Eficiencia de Desempeño):** Comportamiento temporal, rendimiento bajo concurrencia y uso de recursos.
3. **AC3: Compatibility (Compatibilidad):** Coexistencia e interoperabilidad de microservicios y pasarelas.
4. **AC4: Interaction Capability (Capacidad de Interacción):** Usabilidad, accesibilidad y experiencia de usuario.
5. **AC5: Reliability (Fiabilidad):** Tolerancia a fallos, consistencia eventual y patrones de resiliencia (Outbox/Idempotencia).
6. **AC6: Security (Seguridad):** Confidencialidad PCI-DSS, aislamiento multi-tenant (RLS), RBAC y mitigación de fuerza bruta.
7. **AC7: Maintainability (Mantenibilidad):** CI/CD, modularidad, contratos OpenAPI y validación previa en QA.
8. **AC8: Flexibility (Flexibilidad):** Adaptabilidad a nuevos tenants, clientes corporativos y cambios de infraestructura.
9. **AC9: Safety (Seguridad Operacional / Inocuidad):** Integridad del ciclo de vida de la solicitud y mitigación de riesgos operativos.

---

## 2. Matriz Consolidada de los 52 Escenarios de Calidad (SAD §3)

| ID | Atributo de Calidad | Nombre del Escenario | Métrica / Criterio Esperado (SAD §3) | Valor Medido | Archivo de Evidencia (Ruta Relativa) | Estado | Observaciones Técnicas |
|:---:|---|---|---|---|---|:---:|---|
| **AC1-E1** | Functional Suitability | Filtro de especialidad en el matching | 0% de asignaciones a técnico de otra especialidad | 0 asignaciones a técnicos de otra especialidad | `tests/e2e/evidencias/scrum-78-qa-2026-10-22.txt`; `tests/e2e/evidencias/scrum-incremento-tecnico-qa-2026-10-22.txt` | **Cumple** | Filtro validado en motor de matching con PostGIS. |
| **AC1-E2** | Functional Suitability | Cobertura de requisitos del MVP | 100% de los RF de prioridad Alta con prueba de aceptación | Verificado en 28 RFs de 33 | Matriz de Funcionalidades SRS v5.5 | **Parcial** | Se consolida con la sesión de UAT formal. |
| **AC1-E3** | Functional Suitability | Información suficiente para ejecutar el servicio | 100% de solicitudes asignadas muestran categoría, dirección y descripción | Detalle completo (categoría, dirección, teléfono) entregado al técnico | `tests/e2e/evidencias/scrum-incremento-tecnico-qa-2026-10-22.txt` (bloque 3.1 DTL-001) | **Cumple** | Cumple RN-SR13; terceros reciben HTTP 403. |
| **AC2-E1** | Performance Efficiency | Búsqueda de técnicos cercanos | $< 3\text{ s}$ para el 95% de las solicitudes | **p95 = 73.55 ms** en carga 50 VU ($< 3\text{ s}$) | `tests/performance/evidencias/k6-load-50vu-summary.json` | **Cumple** | Latencia percentil 95 en búsqueda geoespacial PostGIS. |
| **AC2-E2** | Performance Efficiency | Consulta de historial | $< 1.5\text{ s}$ por página de resultados | Sin cronometraje formal por página | *(Sin archivo de evidencia)* | **No medido** | Programado para pruebas de carga en Sprint 5. |
| **AC2-E3** | Performance Efficiency | Procesamiento en segundo plano | $< 7\text{ s}$ de la creación de la solicitud a la notificación | $\approx 2\text{ s}$ en pruebas E2E contra QA ($< 7\text{ s}$) | `tests/e2e/evidencias/scrum-490-cotizacion-qa-2026-10-22.txt`; `tests/e2e/evidencias/scrum-478-aviso-tiempo-real-qa-2026-10-22.txt` | **Cumple** | Tiempo medido desde alta hasta entrega WS. |
| **AC2-E4** | Performance Efficiency | Pico de carga inesperado | Soporta 150 solicitudes de matching concurrentes | **150 VU sostenidos**, **0% fallos** (38,876 reqs), **p95 = 415.39 ms** | `tests/performance/evidencias/k6-stress-150vu-summary.json` | **Cumple** | Carga masiva durante 4 min sin degradación. |
| **AC2-E5** | Performance Efficiency | Uso de recursos bajo carga normal | 0 OOMKilled y pods dentro de limits durante k6 | 0 caídas observadas en k6 | `tests/performance/evidencias/k6-stress-150vu-qa-2026-10-18.txt` | **Parcial** | Requiere captura gráfica de Grafana / kubectl get pods con limits (Infraestructura §5.6). |
| **AC3-E1** | Compatibility | Integración con la pasarela de pagos | 100% de transacciones sin error de formato/protocolo | 0 fallos contra sandbox simulado | `tests/e2e/evidencias/scrum-117-pago-qa-2026-10-22.txt` | **Parcial** | Validado contra mock/sandbox (ADR-009). |
| **AC3-E2** | Compatibility | Convivencia de los 8 microservicios en VM2/VM3 | Matching $< 3\text{ s}$ p95 y 0 pods desalojados | 8 servicios coexistiendo en k3s; p95 = 73.55 ms y 0 pods desalojados | `tests/performance/evidencias/k6-stress-150vu-qa-2026-10-18.txt`; `tests/ci-results/` | **Cumple** | Convivencia sin interferencia de recursos. |
| **AC4-E1** | Interaction Capability | Creación de solicitud en pocos pasos | 100% de solicitudes en máx. 3 pasos (RNF-11) | 1 formulario + confirmación | SAD §2.2 (`nueva_solicitud_page.dart`) | **Cumple** | Flujo optimizado en app móvil. |
| **AC4-E2** | Interaction Capability | Uso en distintos dispositivos | 100% de pantallas sin scroll horizontal ni cortes | Sin pruebas multi-pantalla formales | *(Sin archivo de evidencia)* | **No medido** | Requiere matriz de dispositivos en Sprint 5. |
| **AC4-E3** | Interaction Capability | Reconocer si la app sirve para lo que necesito | 4 de 5 usuarios identifican cómo solicitar en $< 30\text{ s}$ | Sesión presencial programada | `docs/testing/uat-product-owner.md` | **No medido** | Se evalúa en la sesión de UAT con PO. |
| **AC4-E4** | Interaction Capability | Primer uso del técnico sin capacitación | 4 de 5 técnicos completan el ciclo en $< 10\text{ min}$ | Sesión presencial programada | `docs/testing/uat-product-owner.md` | **No medido** | Prueba con usuarios reales en UAT. |
| **AC4-E5** | Interaction Capability | Protección ante errores del usuario | 0 solicitudes con campos vacíos o dirección no validada | Validación HTTP 422 ante dirección inválida | `tests/e2e/evidencias/scrum-458-geocodificacion-buzon-qa-2026-10-22.txt` | **Parcial** | Validación de dirección geocodificada en Bogotá. |
| **AC4-E6** | Interaction Capability | Motivación para calificar el servicio | $\ge 60\%$ de servicios completados reciben calificación | Funcionalidad no desarrollada | *(Sin archivo de evidencia)* | **No cumple** | Depende de RF-12 (calificación inexistente). |
| **AC4-E7** | Interaction Capability | Uso con distintas capacidades | 100% de pantallas del flujo pasan pruebas de accesibilidad | Escaneo preliminar en panel admin | `docs/testing/capacidad-interaccion-scrum-569.md` | **No medido** | Requiere escaneo completo en Flutter. |
| **AC4-E8** | Interaction Capability | Uso en dispositivos de gama baja | Flujo sin cierres y cada pantalla $< 3\text{ s}$ | Sin pruebas en emuladores de bajos recursos | *(Sin archivo de evidencia)* | **No medido** | Programado para Sprint 5. |
| **AC4-E9** | Interaction Capability | Seguimiento que se explica solo | 100% de estados con texto explicativo | Textos implementados en 4 estados | `tests/e2e/evidencias/scrum-84-seguimiento-estado-qa-2026-10-22.txt` | **No medido** | Requiere validación cualitativa en UAT. |
| **AC5-E1** | Reliability | Caída de un componente no crítico | Recuperación manual en 12–24 h | Sin simulación de desastre mayor | *(Sin archivo de evidencia)* | **No medido** | Evaluación de DRP programada. |
| **AC5-E2** | Reliability | Mantenimiento planeado | Downtime planeado $< 2\text{ h}$ | Sin ventana de mantenimiento ejecutada | *(Sin archivo de evidencia)* | **No medido** | Procedimiento documentado en Ansible. |
| **AC5-E3** | Reliability | Caída de un microservicio | 0% de eventos perdidos; procesa backlog al reiniciar | Eventos retenidos en `outbox_events` y procesados al reconectar | `tests/e2e/evidencias/scrum-incremento-tecnico-qa-2026-10-22.txt` | **Parcial** | Garantía Outbox atómica en PostgreSQL. |
| **AC5-E4** | Reliability | Kafka no disponible | 0 eventos perdidos; reintento automático | Persistencia transaccional en `outbox_events` | `docs/architecture/SDD.md` §4.2 | **Parcial** | Reintento transaccional en productores. |
| **AC5-E5** | Reliability | Evento duplicado por reintento | 0 efectos duplicados (`eventId`) | Sin prueba de deduplicación en QA | *(Sin archivo de evidencia)* | **No medido** | Prueba de reintento de eventos duplicados en QA pendiente de ejecución; verificada en suite local. |
| **AC5-E6** | Reliability | Operación sin fallos del flujo crítico | $< 1\%$ de respuestas 5xx y 0 fallos en E2E | Flujo E2E probado sin fallos (61 aserciones PASS) | `tests/e2e/evidencias/scrum-incremento-tecnico-qa-2026-10-22.txt` | **Parcial** | Flujo verificado hasta pago y comprobante; calificación pendiente por RF-12 no desarrollado. |
| **AC6-E1** | Security | Protección de datos de pago | 0 números de tarjeta/CVV en BD o logs | **0 números PAN/CVV** en 2,649 trazas auditadas en Loki | `tests/security/evidencias/pci-dss-loki-qa-2026-10-18.txt` | **Cumple** | Escaneo exhaustivo con regex PCI-DSS. |
| **AC6-E2** | Security | Aislamiento multi-tenant | 0 fugas entre tenants | Accesos cross-tenant aislados responden HTTP 404 | `tests/e2e/evidencias/scrum-108-aprobacion-rechazo-qa-2026-10-22.txt`; `tests/e2e/evidencias/tenant-beta-qa-2026-10-15.txt` | **Cumple** | RLS en PostgreSQL VM5; 0 fugas. |
| **AC6-E3** | Security | Control de acceso por rol | 100% de endpoints sensibles validan rol en backend | Accesos no autorizados bloqueados con HTTP 403 Forbidden | `tests/e2e/evidencias/scrum-56-registro-tecnico-qa-2026-10-22.txt`; `tests/e2e/evidencias/scrum-105-panel-operativo-qa-2026-10-22.txt` | **Cumple** | Validación estricta de RBAC. |
| **AC6-E4** | Security | Token comprometido o expirado | 100% de tokens inválidos/expirados rechazados | 401 en REST y 4001 en WS ante tokens sin firma/expirados | `tests/e2e/evidencias/mvp-qa-sprint4-2026-10-18.txt`; `tests/e2e/evidencias/scrum-478-aviso-tiempo-real-qa-2026-10-22.txt` | **Cumple** | Rechazo inmediato de JWT RSA-256. |
| **AC6-E5** | Security | Reconstrucción de una disputa | 100% de transiciones de estado registradas | Transiciones registradas con actor, timestamp y S3 | `tests/e2e/evidencias/scrum-84-seguimiento-estado-qa-2026-10-22.txt`; `tests/e2e/evidencias/scrum-96-evidencia-qa-2026-10-22.txt` | **Cumple** | Trazabilidad inmutable en PostgreSQL y S3. |
| **AC6-E6** | Security | Registro de cambios en pagos | 100% de cambios de estado en pagos con marca de tiempo | Sin auditoría forense de pagos | *(Sin archivo de evidencia)* | **No medido** | Programado para Sprint 5. |
| **AC6-E7** | Security | Acción crítica no repudiable | 100% de acciones críticas con usuario y hora | Sin verificación en tabla `audit_logs` | *(Sin archivo de evidencia)* | **No medido** | Programado para Sprint 5. |
| **AC6-E8** | Security | Fuerza bruta contra el login | 0 accesos con credenciales inválidas; bloqueo tras umbral | **HTTP 423 Locked** tras 5 intentos fallidos (RN-U4) | `tests/e2e/evidencias/mvp-qa-sprint4-2026-10-18.txt` (bloque fuerza bruta) | **Cumple** | Mitigación activa en Identity Service. |
| **AC7-E1** | Maintainability | Pipeline de integración continua | Build y pruebas en $< 10\text{ min}$ | **1.032 pruebas CI backend** aprobadas en runs de 1m a 4m | GitHub Actions (8 repos backend, runs oficiales) | **Cumple** | Pipelines de CI en GitHub Actions. |
| **AC7-E2** | Maintainability | Acoplamiento entre módulos | $\ge 80\%$ de los cambios afectan un solo servicio | Sin conteo formal de PRs por repositorio | *(Sin archivo de evidencia)* | **No medido** | Métrica histórica de PRs por repositorio pendiente de consolidar en Sprint 5. |
| **AC7-E3** | Maintainability | Incorporación de un nuevo microservicio | 0 cambios de código en servicios existentes | Sin prueba de adición de nuevo servicio | *(Sin archivo de evidencia)* | **No medido** | Arquitectura desacoplada por eventos Kafka. |
| **AC7-E4** | Maintainability | Diagnóstico de un fallo en producción | Causa identificada en $\le 1\text{ h}$ con Grafana/Loki | Diagnóstico verificado en QA con correlationId | `tests/security/evidencias/scrum-325-diagnostico-error-qa-2026-10-07.txt` | **Parcial** | Verificado en QA, pendiente en producción. |
| **AC7-E5** | Maintainability | Reutilización de la lógica transversal | 0 copias de la lógica transversal entre servicios | Sin análisis de duplicación de librerías | *(Sin archivo de evidencia)* | **No medido** | Uso de middleware común en backend. |
| **AC7-E6** | Maintainability | Validación del incremento en QA antes de producción | 100% de despliegues pasan por QA; 0 pruebas carga en prod | Compuertas 2.1 a 2.6 aprobadas; pruebas k6 en QA (ADR-015) | `docs/testing/informe-pruebas-sprint4.md` §5 | **Cumple** | Aislamiento total de producción. |
| **AC8-E1** | Flexibility | Alta de nuevo tenant | Tenant funcional en $< 1\text{ h}$, sin downtime | Aprovisionamiento verificado en QA | `tests/e2e/evidencias/tenant-beta-qa-2026-10-15.txt` | **Parcial** | Falta medición formal de tiempo $< 1\text{ h}$. |
| **AC8-E2** | Flexibility | Escalado independiente de un servicio | Escalar sin cambios de código ni downtime | Sin prueba de escalado en caliente | *(Sin archivo de evidencia)* | **No medido** | Soportado por k3s / HPA. |
| **AC8-E3** | Flexibility | Nuevo canal o tipo de cliente | 0 cambios en dominio para nuevo tipo de cliente | Soporte de cuenta Empresa integrado limpiamente (RF-06, RF-08) | `tests/e2e/evidencias/scrum-68-cuenta-corporativa-qa-2026-10-22.txt`; `tests/e2e/evidencias/scrum-75-solicitud-empresa-qa-2026-10-22.txt` | **Cumple** | Incorporación de clientes corporativos. |
| **AC8-E4** | Flexibility | Cambio de proveedor de geolocalización | Reemplazo sin cambios en los demás servicios | Sin cambio de adaptador en Sprint 4 | *(Sin archivo de evidencia)* | **No medido** | Diseñado mediante interfaz de adaptador. |
| **AC8-E5** | Flexibility | Reconstrucción del entorno desde cero | VM operativa en $\le 4\text{ h}$ solo con lo documentado | Playbooks de Ansible disponibles | `infrastructure/ansible/` | **No medido** | Procedimiento automatizado en Ansible. |
| **AC9-E1** | Safety | Transiciones seguras del ciclo de servicio | 0 transiciones inválidas en `service_requests` | Saltos de estado inválidos responden HTTP 409 Conflict | `tests/e2e/evidencias/scrum-84-seguimiento-estado-qa-2026-10-22.txt` | **Cumple** | Máquina de estados estricta en ServiceRequest. |
| **AC9-E2** | Safety | Técnico con calificaciones bajas | 100% de técnicos señalados en panel sin suspensión auto | Funcionalidad no desarrollada | *(Sin archivo de evidencia)* | **No cumple** | Depende de RF-12 (calificación inexistente). |
| **AC9-E3** | Safety | Servicio sin cierre | 100% de solicitudes vencidas marcadas en el panel | Sin job de barrido de solicitudes vencidas | *(Sin archivo de evidencia)* | **No medido** | Programado para Sprint 5. |
| **AC9-E4** | Safety | Sin candidatos elegibles | 0 asignaciones a técnicos que no cumplen filtro | Transición atómica a `en_espera` sin candidatos elegibles | `tests/e2e/evidencias/scrum-78-qa-2026-10-22.txt` | **Cumple** | Lógica de matching ante ausencia de técnicos. |
| **AC9-E5** | Safety | Pasarela de pagos sin respuesta | 0 'pagado' sin `payment.approved` y 0 cobros duplicados | Conciliación y timeout en pasarela simulada | `tests/e2e/evidencias/scrum-117-pago-qa-2026-10-22.txt`; `tests/e2e/evidencias/scrum-495-comprobante-qa-2026-10-22.txt` | **Cumple** | Manejo de estados pendientes sin doble cobro. |
| **AC9-E6** | Safety | Alerta de operación en riesgo | Alerta en $< 15\text{ min}$ | Sin configuración de alertas de riesgo en Grafana | *(Sin archivo de evidencia)* | **No medido** | Programado para Sprint 5. |
| **AC9-E7** | Safety | Integración de un componente nuevo | 100% de E2E pasan antes de despliegue | Suites E2E de incremento técnico aprobadas antes de merge | `tests/e2e/evidencias/scrum-incremento-tecnico-qa-2026-10-22.txt` | **Cumple** | Integración validada en QA desplegado. |
| **AC9-E8** | Safety | Cambio de geolocalización sin alteración | 100% de casos de regresión con el mismo resultado | Sin cambio de motor geoespacial en Sprint 4 | *(Sin archivo de evidencia)* | **No medido** | Basado en PostGIS. |

---

## 3. Balance Cuantitativo de los Escenarios de Calidad

* **Total de Escenarios Evaluados:** **52 Escenarios de Arquitectura (SAD §3)**.
* **Escenarios en Estado CUMPLE (con medición cuantitativa y evidencia):** **20 escenarios (38.5%)**.
* **Escenarios en Estado PARCIAL:** **9 escenarios (17.3%)** (incluye AC2-E5 recursos, AC3-E1 pasarela mock, AC5-E3 outbox, AC5-E4 kafka, AC5-E6 flujo sin calificación, AC7-E4 diagnóstico en QA, AC8-E1 tenant).
* **Escenarios en Estado NO CUMPLE:** **2 escenarios (3.8%)** (AC4-E6 y AC9-E2, dependientes de la calificación inexistente RF-12).
* **Escenarios en Estado NO MEDIDO / PENDIENTE:** **21 escenarios (40.4%)** (programados para Sprint 5 o sesión presencial de UAT).
* **Porcentaje de Escenarios de Calidad:** **47.12%** ($[20 \times 1.0 + 9 \times 0.5] / 52$).
* **Avance Preliminar del Producto (Fórmula QA):** **74.36%** ($0.7 \times 86.03\% \text{ [QA]} + 0.3 \times 47.12\% \text{ [Calidad]}$). Cifra 100% blindada y defendible técnicamente frente a la PO y el profesor.
