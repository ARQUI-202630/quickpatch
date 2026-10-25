# Evaluación de Capacidad de Interacción y Usabilidad (SCRUM-569)

**Código del Documento:** `EVA-USAB-SP5-2026-10-25`  
**Versión:** `2.0 Final`  
**Fecha:** 25 de octubre de 2026  
**Responsable:** Katherine Bravo (`ka.bravo@javeriana.edu.co`) — QA Lead  
**Trazabilidad Jira:** Tarea `SCRUM-569` | SAD AC1 (Escenarios de Usabilidad) | Documento de Pruebas `TD.md` V3.0  
**Criterio de Evaluación:** Conforme a la directriz técnica de QA, un escenario de interacción solo se certifica en estado **Aprobado** si cuenta con su captura de pantalla correspondiente en el repositorio, la medición cronometrada del tiempo de compleción y la fecha exacta de registro. Todo escenario no medido empíricamente en frontend permanece como **Pendiente**.

---

## 1. Convenciones de Evaluación

* **Aprobado:** Escenario con evidencia fotográfica (captura de pantalla) en el repositorio, tiempo medido de interacción con usuario y fecha registrada.
* **Pendiente:** Escenario cuya métrica objetivo está definida pero cuya medición en interfaz gráfica (web o móvil) se encuentra pendiente de ejecución presencial o soporte de instrumentación en frontend.
* **Rechazado:** Escenario cuyo tiempo de interacción superó el umbral máximo de tolerancia especificado en el SAD.

---

## 2. Matriz de Escenarios de Capacidad de Interacción (SCRUM-569)

| ID Escenario | Canal / Interfaz | Acción de Usuario Evaluada | Umbral Máximo (SAD) | Tiempo Medido | Captura de Pantalla | Fecha | Estado | Observaciones |
|:---:|---|---|:---:|:---:|:---:|:---:|:---:|---|
| **INT-001** | Aplicación Móvil (Cliente) | Registro de nuevo cliente y verificación inicial | $\le 120\text{ s}$ | *(Pendiente)* | *(Sin captura)* | *(Pendiente)* | **Pendiente** | Pendiente de sesión de prueba presencial en emulador/dispositivo Android con medición cronometrada. |
| **INT-002** | Aplicación Móvil (Cliente) | Creación de solicitud de servicio y selección de dirección | $\le 60\text{ s}$ | *(Pendiente)* | *(Sin captura)* | *(Pendiente)* | **Pendiente** | Requiere prueba de interacción completa con mapa y geocodificación en frontend móvil. |
| **INT-003** | Aplicación Móvil (Cliente) | Visualización de estado en tiempo real (seguimiento) | $\le 5\text{ s}$ | *(Pendiente)* | *(Sin captura)* | *(Pendiente)* | **Pendiente** | En espera de certificación de latencia de renderizado reactivo del WebSocket en frontend. |
| **INT-004** | Aplicación Web (Admin) | Aprobación de técnico en panel administrativo | $\le 30\text{ s}$ | *(Pendiente)* | *(Sin captura)* | *(Pendiente)* | **Pendiente** | Especificado para panel web Angular; pendiente de captura y cronometraje con usuario administrador. |
| **INT-005** | Aplicación Web (Admin) | Suspensión de cuenta de técnico con motivo | $\le 30\text{ s}$ | *(Pendiente)* | *(Sin captura)* | *(Pendiente)* | **Pendiente** | Flujo administrativo dependiente de despliegue y validación final de interfaz web. |
| **INT-006** | Aplicación Web (Proveedor) | Alta de técnico en equipo de trabajo | $\le 45\text{ s}$ | *(Pendiente)* | *(Sin captura)* | *(Pendiente)* | **Pendiente** | Requiere sesión de medición en portal de proveedores. |

---

## 3. Resumen Consolidado de Capacidad de Interacción

* **Total de Escenarios de Interacción Evaluados:** **6 escenarios**.
* **Escenarios Aprobados con Captura y Medición:** **0 escenarios (0.0%)**.
* **Escenarios Pendientes de Medición en Frontend:** **6 escenarios (100.0%)**.
* **Escenarios Rechazados:** **0 escenarios (0.0%)**.

> **Dictamen de QA:** Conforme al principio de transparencia técnica, la capacidad de interacción permanece en estado **Pendiente** hasta tanto se disponga de las capturas de pantalla de la interfaz gráfica y los registros cronometrados de la prueba de usuarios, programados en conjunto con la ejecución de UAT (SCRUM-608).
