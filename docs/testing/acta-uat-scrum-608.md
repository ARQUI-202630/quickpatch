# Acta de Aceptación UAT con la Product Owner — Sprint 5 (SCRUM-608)

**Código del Documento:** `ACTA-UAT-PO-SP5`  
**Responsable:** Katherine Bravo (`ka.bravo@javeriana.edu.co`) — QA Lead  
**Trazabilidad Jira:** Historia `SCRUM-605` | Especificación `SCRUM-606` | Ejecución `SCRUM-608`  
**Casos:** [`docs/testing/uat-product-owner.md`](uat-product-owner.md) (UAT-001 a UAT-008)  
**Escenarios de Capacidad de interacción previstos para la sesión:** AC4-E3, AC4-E4, AC4-E6 y AC4-E9 ([`docs/testing/capacidad-interaccion-scrum-569.md`](capacidad-interaccion-scrum-569.md))
**Aprobación de la Product Owner:** Informe UAT oficial del 5 de noviembre de 2026 ([`informe-uat-oficial-po-2026-11-05.xlsx`](informe-uat-oficial-po-2026-11-05.xlsx))

> **Cómo se hizo esta UAT.** No hubo sesión presencial con los 8 casos. La Product Owner revisó las evidencias de QA y registró su decisión en el Informe UAT oficial. Esta acta deja constancia de esa decisión. Lo que solo se podía medir con personas en la sesión queda como «No medido».

---

## 1. Datos de la sesión

| Campo | Valor |
|---|---|
| Fecha y hora | 5 de noviembre de 2026 (entrega del Informe UAT oficial) |
| Lugar o enlace | Revisión asíncrona de evidencias; decisión registrada en [`informe-uat-oficial-po-2026-11-05.xlsx`](informe-uat-oficial-po-2026-11-05.xlsx) |
| Product Owner | Angy Bautista |
| QA Lead | Katherine Bravo |
| Otros asistentes | No aplica (sin sesión presencial) |
| Ambiente | QA (`https://qa.quickpatch.internal`) |
| App móvil | APK `v0.5.5-qa` (versión de las evidencias del 4 y 5 de noviembre) |
| Panel web | `0.5.5` |

## 2. Preparación (antes de la sesión)

| # | Verificación | Responsable | Hecho |
|---|---|---|---|
| 1 | QA limpio para la UAT con `infrastructure/ansible/playbooks/limpiar-qa-uat.yml` (SCRUM-607) | DevOps | ☐ |
| 2 | Datos de demostración cargados (`tests/datos-demo/`) | DevOps | ☐ |
| 3 | APK `v0.5.4-qa` instalado en el celular de prueba | QA | ☐ |
| 4 | Panel web `0.5.5` abre con el administrador del tenant | QA | ☐ |
| 5 | Humo del flujo crítico en verde el mismo día (`tests/e2e/humo-flujo-critico.postman_collection.json`) | QA | ☐ |
| 6 | Cronómetro y planilla de la sección 4 a mano | QA | ☐ |

Las claves de las cuentas se reparten por el canal del equipo. No se escriben en esta acta.

**Nota del 5 de noviembre:** la preparación era para la sesión presencial, que no se hizo. Por eso las casillas quedan sin marcar. El humo del flujo crítico del 4 de noviembre pasó sin fallos (run 41935076005).

## 3. Resultado por caso

Dictamen posible: **Aprobado**, **Aprobado con observaciones** o **Rechazado**. Un caso rechazado debe tener su defecto en Jira.

| Caso | Qué valida | Dictamen | Evidencia (captura o archivo) | Observaciones de la PO | Defecto en Jira |
|---|---|---|---|---|---|
| UAT-001 | Registro y autenticación del cliente | Aprobado | quickpatch-mvp, run 41935076005 (4-nov): 61 aserciones y bloqueo tras intentos fallidos (423), 0 fallos | Aceptado con las evidencias de QA (RF-01, RF-03) | Ninguno |
| UAT-002 | Registro del técnico y aprobación del administrador | Aprobado | scrum-56-registro-tecnico y scrum-108-aprobacion-rechazo, run 41935076005 (4-nov), 0 fallos | Aceptado con las evidencias de QA (RF-02, RF-19). Queda abierta la pregunta P8 del SRS: si aplica también a proveedores | Ninguno |
| UAT-003 | Creación de la solicitud y asignación automática | Aprobado | scrum-458-geocodificacion-buzon, scrum-600-fuera-de-bogota y scrum-78-motor-matching, run 41935076005 (4-nov), 0 fallos | Aceptado con las evidencias de QA (RF-07, RF-09) | Ninguno |
| UAT-004 | Notificación, aceptación de la oferta y seguimiento de estados | Aprobado con observaciones | `tests/e2e/evidencias/rf-10-vencimiento-oferta-qa-2026-11-05.md` (PR #269); scrum-84-seguimiento-estado, run 41935076005 (4-nov) | RF-10 con observaciones: la oferta vence a los 179 s y pasa al siguiente técnico, pero no se probó el caso sin más técnicos. RF-11 aceptado | Ninguno |
| UAT-005 | Inicio del trabajo, foto de evidencia y finalización | Aprobado | scrum-96-evidencia y scrum-incremento-tecnico, run 41935076005 (4-nov), 0 fallos | Aceptado con las evidencias de QA (RF-14, RF-15) | Ninguno |
| UAT-006 | Pago con la pasarela simulada y comprobante | Aprobado | scrum-117-pago y scrum-495-comprobante, run 41935076005 (4-nov), 0 fallos | Aceptado con las evidencias de QA (RF-22, RF-24). Pasarela simulada (ADR-009); comprobante sin validez fiscal (DR-03) | Ninguno |
| UAT-007 | Cuenta corporativa, miembros y solicitud de empresa | Aprobado | scrum-68-cuenta-corporativa, scrum-75-solicitud-empresa y scrum-496-pago-empresa, run 41935076005 (4-nov), 0 fallos | Aceptado con las evidencias de QA (RF-06, RF-08, RF-23) | Ninguno |
| UAT-008 | Aislamiento entre tenants y permisos en el panel | Aprobado | scrum-65-roles-y-tenants y scrum-511-tenant-desactivado, run 41935076005 (4-nov); el tenant Beta recibe 404 en 7 colecciones | Aceptado con las evidencias de QA (RF-04, RF-05, RF-21) | Ninguno |

El dictamen de cada caso sale de la decisión de la Product Owner sobre los requisitos que cubre, en la hoja `Funcionalidades` del Informe UAT oficial. No se tomaron capturas de sesión: la evidencia son las corridas de QA citadas.

## 4. Mediciones de Capacidad de interacción
> **No medido.** Estas mediciones necesitan personas cronometradas en una sesión, que no se hizo. Las tablas quedan vacías a propósito. En el Informe UAT oficial, AC4-E3, AC4-E4 y AC4-E6 están en «No medido» y AC4-E9 en «Parcial».


### 4.1 AC4-E3: reconocer para qué sirve la app (meta: al menos 4 de 5 personas en menos de 30 s)

Se abre la app en la pantalla de inicio, sin explicación previa. Se pregunta: «¿Cómo pediría un técnico?». Se mide el tiempo hasta que la persona señala la acción correcta.

| Persona | Tiempo (s) | ¿Lo logró? |
|---|---|---|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |

### 4.2 AC4-E4: primer uso del técnico (meta: al menos 4 de 5 técnicos en menos de 10 min)

Sin capacitación previa, el técnico acepta la oferta, inicia el trabajo, sube la foto y finaliza (UAT-004 y UAT-005).

| Técnico | Tiempo (min) | ¿Lo logró? | Dónde se trabó |
|---|---|---|---|
| 1 | | | |
| 2 | | | |
| 3 | | | |
| 4 | | | |
| 5 | | | |

### 4.3 AC4-E9: el seguimiento se explica solo (meta: al menos 4 de 5 personas describen el estado sin ayuda)

Se muestra el detalle de una solicitud en cada estado y se pregunta: «¿Qué está pasando con su servicio?».

| Persona | ¿Describió el estado correctamente? | Comentario |
|---|---|---|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |

### 4.4 AC4-E6: calificación del servicio

Al terminar UAT-006, se observa si el cliente encuentra y usa la pantalla de calificación sin que se le indique.

| Persona | ¿Calificó sin ayuda? | Comentario |
|---|---|---|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |

La meta del escenario (al menos 60% de los servicios completados reciben calificación) se mide con uso real. Esta observación da una primera señal.

## 5. Resumen

| Concepto | Valor |
|---|---|
| Casos aprobados | 7 de 8 |
| Casos aprobados con observaciones | 1 de 8 (UAT-004, por RF-10) |
| Casos rechazados | 0 de 8 |
| Defectos abiertos en Jira | 0 bloqueantes. Abiertos de severidad baja: DEF-INT-02 y DEF-INT-03. En mitigación: DEF-S5-01 a DEF-S5-04 |
| AC4-E3 / AC4-E4 / AC4-E6 / AC4-E9 | No medido / No medido / No medido / Parcial |

## 6. Decisión de la Product Owner

☐ **Acepto** el incremento del Sprint 5 tal como está.  
☒ **Acepto con observaciones**, que quedan como HU o defectos en Jira (sección 3).  
☐ **No acepto.** Motivo:

Observaciones de la Product Owner, según el Informe UAT oficial:
1. RF-10 se acepta con observaciones (UAT-004).
2. AC4-E2 y AC9-E2 cuentan como Cumple por decisión de la Product Owner, todavía sin evidencia. AC9-E2 depende de SCRUM-642, que sigue en Backlog.
3. Las mediciones con personas de AC4-E3, AC4-E4, AC4-E6 y AC4-E9 no se hicieron.

Con esta decisión, el avance oficial del producto es 91.92%: 37 de 37 funcionalidades aceptadas y 73.08% de escenarios de calidad.

## 7. Firmas

| Rol | Nombre | Firma o aprobación | Fecha |
|---|---|---|---|
| Product Owner | Angy Bautista | Aprobación registrada en el Informe UAT oficial ([`informe-uat-oficial-po-2026-11-05.xlsx`](informe-uat-oficial-po-2026-11-05.xlsx)) | 05/11/2026 |
| QA Lead | Katherine Bravo | Registró el acta | 05/11/2026 |
