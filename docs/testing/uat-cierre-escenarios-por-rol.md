# Escenarios de la UAT de cierre por rol (SCRUM-659)

**Código del documento:** `SPEC-UAT-CIERRE-2026-11-12`
**Versión:** 1.0, borrador para revisión de la Product Owner
**Fecha:** 12 de noviembre de 2026
**Responsable:** Katherine Bravo (`ka.bravo@javeriana.edu.co`), QA Lead
**Trazabilidad Jira:** historia SCRUM-658 (UAT de cierre con todos los roles). Subtareas: SCRUM-659 (este documento), SCRUM-660 (ejecución del flujo crítico), SCRUM-661 (ejecución de los roles corporativos y administrativos) y SCRUM-662 (revisión y firma de la PO).
**Ambiente:** QA (`https://qa.quickpatch.internal`): app móvil con el APK `-qa` vigente y panel web. Nunca producción (ADR-015).
**Fuentes:** SRS v5.6, sección 5 (33 RF); [`indicadores-funcionales.md`](indicadores-funcionales.md); [`matriz-escenarios-calidad-52.md`](matriz-escenarios-calidad-52.md), escenarios AC4.

---

## 1. Alcance

La UAT del Sprint 5 (SCRUM-608) se cerró sin sesión: la PO aceptó con las evidencias de QA. La UAT de cierre la ejecutan personas en la app y en el panel de QA, con los **6 roles** del producto. Tiene dos objetivos:

1. Recorrer el **flujo crítico completo** (cliente → técnico → pago → calificación) y los **flujos administrativos**, con un resultado real y evidencia en cada paso.
2. Medir con personas los escenarios de calidad que siguen sin medición: **AC4-E3, AC4-E4, AC4-E6 y AC4-E9**.

Este documento reemplaza la especificación de 8 casos de [`uat-product-owner.md`](uat-product-owner.md) para el cierre. Esa especificación citaba RF que ya no corresponden, como RF-30 y RF-31, que están retirados, o RF-06 y RF-07 para pagos.

**Cobertura:** los 33 RF del SRS y las extensiones EXT-01, EXT-02 y EXT-04 tienen al menos un escenario (sección 6).

## 2. Plantilla de registro

Cada escenario se registra con estos campos. Los primeros seis vienen en este documento. **Resultado real**, **PASS/FAIL** y **Evidencia** los llena quien ejecuta, en SCRUM-660 o SCRUM-661, en el registro de ejecución de la sección 5.

| Campo | Qué va |
|---|---|
| ID | `UAT-<rol>-<n>` |
| Escenario | Qué se prueba, en palabras de negocio |
| Requisitos | RF, extensión o escenario de calidad |
| Usuario | Rol y cuenta de prueba (sección 3) |
| Precondición | Estado necesario antes de empezar |
| Pasos | Lo que hace la persona en la app o en el panel |
| Resultado esperado | Lo que debe pasar para que sea PASS |
| Resultado real | Lo que pasó, con hora |
| PASS / FAIL | PASS solo si se cumple todo el resultado esperado |
| Evidencia | Captura o video en `tests/e2e/evidencias/uat-cierre-<fecha>/`, nombrado con el ID |

Un FAIL se registra como defecto en Jira y en [`registro-defectos-sprint4-sprint5.md`](registro-defectos-sprint4-sprint5.md), con el ID del escenario.

## 3. Datos y cuentas de prueba

- Se usan los dos tenants de QA: **Alfa**, donde se hace la prueba, y **Beta**, para el aislamiento. Las cuentas se crean el día de la sesión con correos `@quickpatch.test`. Las contraseñas no se escriben en este documento ni en la evidencia.
- Pagos con las tarjetas de prueba de la pasarela simulada (ADR-009). Nunca se usa una tarjeta real.
- Direcciones de Bogotá para el flujo normal, y una de fuera de Bogotá para el caso de rechazo.
- Al terminar, los datos de la sesión se limpian de QA y la limpieza se registra.

## 4. Escenarios

### 4.1 Cliente (app móvil): flujo crítico (SCRUM-660)

| ID | Escenario | Requisitos | Precondición | Pasos | Resultado esperado |
|---|---|---|---|---|---|
| UAT-CLI-01 | Descargar la app, crear la cuenta y entrar | EXT-03, RF-01, RF-03, EXT-01 | Sin cuenta en Alfa | 1. Descargar el APK desde la landing. 2. Crear la cuenta con correo y contraseña de 8 o más caracteres. 3. Probar una contraseña de menos de 8. 4. Iniciar sesión. 5. Editar nombre y teléfono en el perfil | La descarga funciona. La contraseña corta se rechaza con un mensaje que dice qué corregir. La cuenta se crea y se entra. El perfil guarda los cambios, y el correo y el rol no se pueden editar |
| UAT-CLI-02 | Crear una solicitud en pocos pasos | RF-07, AC4-E1, AC4-E5 | UAT-CLI-01 hecho | 1. Desde el inicio, crear una solicitud con categoría, descripción y dirección en Bogotá. 2. Repetir con un campo obligatorio vacío. 3. Repetir con una dirección fuera de Bogotá | La solicitud queda creada en máximo 3 pasos y en estado de búsqueda de técnico. El campo vacío y la dirección fuera de Bogotá no se aceptan, y la app dice qué campo corregir |
| UAT-CLI-03 | Seguir el estado de la solicitud en tiempo real | RF-11, AC4-E9 | Solicitud de UAT-CLI-02 | 1. Abrir la solicitud y dejar la pantalla abierta mientras el técnico avanza. 2. En cada estado, la persona dice qué está pasando y qué sigue, sin ayuda | La pantalla cambia sola en cada uno de los 4 estados o más. Cada estado tiene un texto que explica qué ocurre. Para AC4-E9 se anota si la persona lo describió bien (sección 4.7) |
| UAT-CLI-04 | Revisar y aceptar la cotización, y conversar con el técnico | RF-35, RF-37 | Cotización emitida en UAT-TEC-02 | 1. Abrir la cotización y revisar mano de obra y materiales. 2. Rechazarla una vez. 3. Aceptar la segunda. 4. Escribir en el chat de la solicitud | El rechazo deja pedir otra cotización (máximo 3). La aceptación avanza la solicitud. El técnico recibe el mensaje en tiempo real |
| UAT-CLI-05 | Pagar el servicio y recibir el comprobante | RF-22, RF-24 | Servicio completado en UAT-TEC-03 | 1. Pagar con la tarjeta de prueba. 2. Abrir el comprobante | El pago queda aprobado y la solicitud pasa a «Pagado». El comprobante tiene el desglose y la fecha. La app no muestra el número completo de la tarjeta |
| UAT-CLI-06 | Calificar el servicio una sola vez | RF-12, AC4-E6 | Solicitud en «Pagado» | 1. Calificar de 1 a 5, con un comentario. 2. Intentar calificar otra vez | La calificación queda guardada. El segundo intento no se permite. Para AC4-E6 se cuenta si la persona calificó sin que se le pidiera (sección 4.7) |
| UAT-CLI-07 | Cancelar una solicitud antes de que empiece | RF-36 | Solicitud nueva, sin iniciar | 1. Cancelar indicando el motivo. 2. Intentar cancelar una solicitud ya en progreso | La primera queda cancelada con su motivo. La segunda no se puede cancelar |

### 4.2 Técnico (app móvil): flujo crítico (SCRUM-660)

| ID | Escenario | Requisitos | Precondición | Pasos | Resultado esperado |
|---|---|---|---|---|---|
| UAT-TEC-01 | Registrarse con documentos y quedar pendiente | RF-02 | Sin cuenta | 1. Registrarse como técnico con documento y especialidad. 2. Esperar una solicitud de su especialidad | Queda «Pendiente de verificación» y no recibe ofertas mientras no lo aprueben |
| UAT-TEC-02 | Recibir la oferta, aceptarla y cotizar | RF-09, RF-10, RF-14, RF-34 | Técnico aprobado (UAT-ADT-01), disponible y con cobertura en la localidad | 1. Recibir la oferta de UAT-CLI-02. 2. Aceptarla antes de 3 minutos. 3. Abrir el detalle. 4. Emitir la cotización con mano de obra y materiales | La oferta llega solo a un técnico de la especialidad. Al aceptar, la solicitud queda asignada. El detalle muestra categoría, dirección y teléfono. El cliente recibe la cotización |
| UAT-TEC-03 | Iniciar y completar el trabajo con foto | RF-15 | Cotización aceptada | 1. Iniciar el trabajo. 2. Intentar completarlo sin foto. 3. Completarlo con foto | Sin foto no se puede completar. Con foto queda completado y el cliente puede pagar |
| UAT-TEC-04 | Dejar vencer una oferta | RF-10 | Otro técnico candidato disponible | 1. Recibir una oferta y no responder durante 3 minutos | La oferta vence y pasa al siguiente técnico. El primero no puede aceptarla después |
| UAT-TEC-05 | Cambiar la disponibilidad y la zona de cobertura | RF-13 | Técnico aprobado | 1. Pasar a no disponible. 2. Cambiar las localidades de cobertura. 3. Volver a disponible | Mientras está no disponible no recibe ofertas. Después solo las recibe de sus localidades |
| UAT-TEC-06 | Ver el historial y los pagos recibidos | RF-17, RF-25 | Servicio pagado en UAT-CLI-05 | 1. Abrir el historial. 2. Abrir «Mis pagos» | El historial muestra el servicio con su fecha, estado y calificación. Los pagos muestran el monto recibido |

### 4.3 Empresa, usuario autorizado de la cuenta corporativa (SCRUM-661)

| ID | Escenario | Requisitos | Precondición | Pasos | Resultado esperado |
|---|---|---|---|---|---|
| UAT-EMP-01 | Registrar la cuenta corporativa y sumar un usuario autorizado | RF-06 | Sin cuenta corporativa | 1. Registrar la empresa con razón social, NIT y contacto. 2. Agregar un segundo usuario autorizado. 3. Ese usuario activa su acceso e inicia sesión | La cuenta queda con 2 usuarios autorizados y los dos entran a la app |
| UAT-EMP-02 | Pedir un servicio para una sede a nombre de la empresa | RF-08 | UAT-EMP-01 hecho | 1. Crear la solicitud eligiendo la sede | La solicitud queda a nombre de la cuenta corporativa y con la sede |
| UAT-EMP-03 | Pagar a nombre de la cuenta corporativa | RF-23, RF-24 | Servicio de UAT-EMP-02 completado | 1. El otro usuario autorizado paga con la tarjeta de prueba | El pago y el comprobante quedan a nombre de la empresa |

### 4.4 Proveedor (app móvil) (SCRUM-661)

| ID | Escenario | Requisitos | Precondición | Pasos | Resultado esperado |
|---|---|---|---|---|---|
| UAT-PRO-01 | Registrarse como proveedor con documentos | RF-02 | Sin cuenta | 1. Registrarse como proveedor | Queda «Pendiente de verificación» hasta que el Admin del tenant decida |
| UAT-PRO-02 | Administrar su equipo de técnicos | RF-16 | Proveedor aprobado | 1. Dar de alta un técnico del equipo. 2. Verlo en el listado. 3. Intentar darlo de alta otra vez con el mismo documento | El técnico queda en el equipo, en el tenant del proveedor. El duplicado se rechaza con un mensaje claro |
| UAT-PRO-03 | Ver los pagos recibidos | RF-25 | Un servicio pagado de un técnico de su equipo | 1. Abrir «Mis pagos» | Aparece el pago del servicio |

### 4.5 Admin del tenant (panel web) (SCRUM-661)

| ID | Escenario | Requisitos | Precondición | Pasos | Resultado esperado |
|---|---|---|---|---|---|
| UAT-ADT-01 | Aprobar y rechazar técnicos y proveedores con motivo | RF-19 | UAT-TEC-01 y UAT-PRO-01 pendientes | 1. Aprobar al técnico. 2. Rechazar un registro escribiendo el motivo. 3. Intentar rechazar sin motivo | Solo el aprobado recibe ofertas. El rechazo queda con su motivo. Sin motivo no se permite. Antes de cada acción el panel pide confirmación |
| UAT-ADT-02 | Ver las solicitudes activas por estado | RF-18 | Solicitudes del flujo crítico en curso | 1. Abrir el panel de solicitudes y filtrar por estado | Aparecen solo las solicitudes de su tenant, con su estado actual |
| UAT-ADT-03 | Suspender a un técnico | RF-20 | Técnico aprobado sin servicio en curso | 1. Suspenderlo indicando el motivo. 2. Crear una solicitud de su especialidad | Queda suspendido con la fecha y el responsable, y no recibe la oferta |
| UAT-ADT-04 | Ver los técnicos con reputación baja | AC9-E2 | Técnico con promedio menor a 3,0 y 5 calificaciones o más | 1. Abrir el listado de técnicos | El técnico aparece señalado con «Reputación baja» y sigue aprobado |
| UAT-ADT-05 | Generar el enlace de recuperación de contraseña | EXT-04 | Usuario que olvidó la contraseña y la pidió con su correo | 1. Generar el enlace. 2. El usuario define una contraseña nueva. 3. Usar el enlace otra vez | El usuario entra con la contraseña nueva. El enlace no sirve una segunda vez |

### 4.6 Admin de plataforma (panel web) (SCRUM-661)

| ID | Escenario | Requisitos | Precondición | Pasos | Resultado esperado |
|---|---|---|---|---|---|
| UAT-ADP-01 | Ver las solicitudes de todos los tenants | RF-18 | Solicitudes en Alfa y en Beta | 1. Abrir el panel de solicitudes. 2. Filtrar por tenant | Ve las de los dos tenants, y el filtro funciona |
| UAT-ADP-02 | Desactivar y volver a activar un tenant | RF-21 | Tenant de prueba con un usuario | 1. Desactivarlo y confirmar. 2. El usuario intenta iniciar sesión. 3. Activarlo otra vez | Pide confirmación. Con el tenant desactivado el usuario no puede iniciar sesión, y el cambio queda en la auditoría. Al activarlo, el usuario entra de nuevo |

### 4.7 Transversales: aislamiento, canal y operación

| ID | Escenario | Requisitos | Usuario | Pasos | Resultado esperado |
|---|---|---|---|---|---|
| UAT-X-01 | Aislamiento entre tenants desde la interfaz | RF-04, AC6-E2 | Admin del tenant Alfa y cliente de Beta | 1. El admin de Alfa busca solicitudes y técnicos de Beta. 2. El cliente de Beta busca una solicitud de Alfa | Ninguno ve datos del otro tenant |
| UAT-X-02 | Cada rol entra por su canal | RF-05 | Cliente, técnico y Admin del tenant | 1. El cliente intenta entrar al panel web. 2. El admin intenta usar la app móvil | Los dos se rechazan, y cada uno entra solo por su canal |
| UAT-X-03 | Volver atrás en todas las pantallas | EXT-02 | Cliente y técnico | 1. Durante el flujo crítico, usar el botón atrás de Android en cada pantalla | Se vuelve a la pantalla anterior sin perder lo que ya se guardó |
| UAT-X-04 | Pipeline, prueba E2E, cifrado y logs | RF-26, RF-27, RF-28, RF-29 | QA Lead (observación) | 1. Mostrar la última corrida en verde de `pruebas-sistema.yml`, con el humo del flujo crítico. 2. Mostrar que la app y el panel usan HTTPS. 3. Buscar en Loki una petición de la sesión por su correlation-id | La corrida está en verde y llega hasta la calificación. La conexión es HTTPS. La petición aparece en Loki con su correlation-id. Estos 4 RF son técnicos: la PO los acepta por observación |

### 4.8 Mediciones con personas (AC4)

Se hacen en la misma sesión, con **5 participantes** que no son del equipo de desarrollo. El cronómetro empieza cuando la persona recibe el teléfono, y no se le ayuda.

| ID | Escenario de calidad | Qué hace la persona | Meta | Se registra |
|---|---|---|---|---|
| UAT-M-01 | AC4-E3: reconocer para qué sirve la app | Ve la pantalla de inicio por primera vez y señala cómo pediría un servicio | Al menos 4 de 5 lo identifican en menos de 30 s | Tiempo y acierto por participante |
| UAT-M-02 | AC4-E4: primer uso del técnico | Con una cuenta de técnico aprobada, acepta la oferta, cotiza y completa con foto (UAT-TEC-02 y UAT-TEC-03) | Al menos 4 de 5 terminan sin ayuda en menos de 10 min | Tiempo, si terminó y si pidió ayuda |
| UAT-M-03 | AC4-E9: el seguimiento se explica solo | En UAT-CLI-03, dice con sus palabras qué pasa y qué sigue en cada estado | Al menos 4 de 5 describen bien el estado | Respuesta por estado y participante |
| UAT-M-04 | AC4-E6: motivación para calificar | Al terminar el pago (UAT-CLI-05), se observa si califica sin que se le pida | 60 % o más de los servicios completados reciben calificación | Servicios completados y calificados en la sesión |

Con estos resultados se actualizan los 4 escenarios en la matriz de 52 (SCRUM-664) y las cifras se recalculan con `scripts/calcular_indicadores_qa.py`. Si no se llega a la meta, el escenario queda como Parcial o No cumple con el valor medido. Nunca se marca Cumple sin medición.

## 5. Registro de ejecución

Lo llena quien ejecuta (SCRUM-660 y SCRUM-661). Una fila por escenario.

| ID | Fecha y hora | Ejecutó | Resultado real | PASS / FAIL | Evidencia | Defecto |
|---|---|---|---|---|---|---|
| UAT-CLI-01 | | | | | | |
| UAT-CLI-02 | | | | | | |
| UAT-CLI-03 | | | | | | |
| UAT-CLI-04 | | | | | | |
| UAT-CLI-05 | | | | | | |
| UAT-CLI-06 | | | | | | |
| UAT-CLI-07 | | | | | | |
| UAT-TEC-01 | | | | | | |
| UAT-TEC-02 | | | | | | |
| UAT-TEC-03 | | | | | | |
| UAT-TEC-04 | | | | | | |
| UAT-TEC-05 | | | | | | |
| UAT-TEC-06 | | | | | | |
| UAT-EMP-01 | | | | | | |
| UAT-EMP-02 | | | | | | |
| UAT-EMP-03 | | | | | | |
| UAT-PRO-01 | | | | | | |
| UAT-PRO-02 | | | | | | |
| UAT-PRO-03 | | | | | | |
| UAT-ADT-01 | | | | | | |
| UAT-ADT-02 | | | | | | |
| UAT-ADT-03 | | | | | | |
| UAT-ADT-04 | | | | | | |
| UAT-ADT-05 | | | | | | |
| UAT-ADP-01 | | | | | | |
| UAT-ADP-02 | | | | | | |
| UAT-X-01 | | | | | | |
| UAT-X-02 | | | | | | |
| UAT-X-03 | | | | | | |
| UAT-X-04 | | | | | | |
| UAT-M-01 | | | | | | |
| UAT-M-02 | | | | | | |
| UAT-M-03 | | | | | | |
| UAT-M-04 | | | | | | |

## 6. Cobertura de requisitos

| Requisito | Escenarios |
|---|---|
| RF-01, RF-03 | UAT-CLI-01 |
| RF-02 | UAT-TEC-01, UAT-PRO-01 |
| RF-04 | UAT-X-01 |
| RF-05 | UAT-X-02 |
| RF-06 | UAT-EMP-01 |
| RF-07 | UAT-CLI-02 |
| RF-08 | UAT-EMP-02 |
| RF-09, RF-14, RF-34 | UAT-TEC-02 |
| RF-10 | UAT-TEC-02, UAT-TEC-04 |
| RF-11 | UAT-CLI-03 |
| RF-12 | UAT-CLI-06 |
| RF-13 | UAT-TEC-05 |
| RF-15 | UAT-TEC-03 |
| RF-16 | UAT-PRO-02 |
| RF-17 | UAT-TEC-06 |
| RF-18 | UAT-ADT-02, UAT-ADP-01 |
| RF-19 | UAT-ADT-01 |
| RF-20 | UAT-ADT-03 |
| RF-21 | UAT-ADP-02 |
| RF-22 | UAT-CLI-05 |
| RF-23 | UAT-EMP-03 |
| RF-24 | UAT-CLI-05, UAT-EMP-03 |
| RF-25 | UAT-TEC-06, UAT-PRO-03 |
| RF-26, RF-27, RF-28, RF-29 | UAT-X-04 |
| RF-35, RF-37 | UAT-CLI-04 |
| RF-36 | UAT-CLI-07 |
| EXT-01, EXT-03 | UAT-CLI-01 |
| EXT-02 | UAT-X-03 |
| EXT-04 | UAT-ADT-05 |
| AC4-E3, AC4-E4, AC4-E6, AC4-E9 | UAT-M-01 a UAT-M-04 |
| AC9-E2 | UAT-ADT-04 |

Son 33 de 33 RF, 4 de 4 extensiones y los 4 escenarios AC4 pendientes.

## 7. Revisión de la Product Owner

| Rol | Nombre | Decisión | Fecha |
|---|---|---|---|
| Product Owner | Angy Bautista | Pendiente de revisión (SCRUM-659 y SCRUM-662) | — |
| QA Lead | Katherine Bravo | Propone los escenarios | 12/11/2026 |
