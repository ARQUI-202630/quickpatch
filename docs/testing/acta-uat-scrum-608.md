# Acta de Aceptación UAT con la Product Owner — Sprint 5 (SCRUM-608)

**Código del Documento:** `ACTA-UAT-PO-SP5`  
**Responsable:** Katherine Bravo (`ka.bravo@javeriana.edu.co`) — QA Lead  
**Trazabilidad Jira:** Historia `SCRUM-605` | Especificación `SCRUM-606` | Ejecución `SCRUM-608`  
**Casos:** [`docs/testing/uat-product-owner.md`](uat-product-owner.md) (UAT-001 a UAT-008)  
**Escenarios de Capacidad de interacción medidos en la sesión:** AC4-E3, AC4-E4, AC4-E6 y AC4-E9 ([`docs/testing/capacidad-interaccion-scrum-569.md`](capacidad-interaccion-scrum-569.md))

---

## 1. Datos de la sesión

| Campo | Valor |
|---|---|
| Fecha y hora | |
| Lugar o enlace | |
| Product Owner | |
| QA Lead | Katherine Bravo |
| Otros asistentes | |
| Ambiente | QA (`https://qa.quickpatch.internal`) |
| App móvil | APK `v0.5.4-qa` |
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

## 3. Resultado por caso

Dictamen posible: **Aprobado**, **Aprobado con observaciones** o **Rechazado**. Un caso rechazado debe tener su defecto en Jira.

| Caso | Qué valida | Dictamen | Evidencia (captura o archivo) | Observaciones de la PO | Defecto en Jira |
|---|---|---|---|---|---|
| UAT-001 | Registro y autenticación del cliente | | | | |
| UAT-002 | Registro del técnico y aprobación del administrador | | | | |
| UAT-003 | Creación de la solicitud y asignación automática | | | | |
| UAT-004 | Notificación, aceptación de la oferta y seguimiento de estados | | | | |
| UAT-005 | Inicio del trabajo, foto de evidencia y finalización | | | | |
| UAT-006 | Pago con la pasarela simulada y comprobante | | | | |
| UAT-007 | Cuenta corporativa, miembros y solicitud de empresa | | | | |
| UAT-008 | Aislamiento entre tenants y permisos en el panel | | | | |

Las capturas se guardan en `tests/e2e/evidencias/uat-<fecha>/`, con el número del caso en el nombre.

## 4. Mediciones de Capacidad de interacción

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
| Casos aprobados | __ de 8 |
| Casos aprobados con observaciones | __ de 8 |
| Casos rechazados | __ de 8 |
| Defectos abiertos en Jira | |
| AC4-E3 / AC4-E4 / AC4-E6 / AC4-E9 | Cumple / No cumple (según las tablas de la sección 4) |

## 6. Decisión de la Product Owner

☐ **Acepto** el incremento del Sprint 5 tal como está.  
☐ **Acepto con observaciones**, que quedan como HU o defectos en Jira (sección 3).  
☐ **No acepto.** Motivo:

## 7. Firmas

| Rol | Nombre | Firma o aprobación | Fecha |
|---|---|---|---|
| Product Owner | | | |
| QA Lead | Katherine Bravo | | |
