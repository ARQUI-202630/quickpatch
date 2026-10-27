# Especificación de Casos de Prueba de Aceptación de Usuario (UAT) — Sprint 5 (SCRUM-606)

**Código del Documento:** `SPEC-UAT-PO-SP5-2026-10-25`  
**Versión:** `2.0 Especificación`  
**Fecha de Publicación:** 25 de octubre de 2026  
**Responsable:** Katherine Bravo (`ka.bravo@javeriana.edu.co`) — QA Lead  
**Trazabilidad Jira:** Tarea `SCRUM-606` | Ejecución UAT `SCRUM-608` | Documento de Pruebas `TD.md` V3.0  
**Ambiente Destino:** QA Desplegado (`https://qa.quickpatch.internal` / Aplicaciones Web y Móvil)  

---

## 1. Alcance y Metodología de las Pruebas de Aceptación

El presente documento constituye la **especificación formal de los 8 casos de prueba de aceptación de usuario (UAT)** diseñados para validar los flujos de valor centrales de la plataforma QuickPatch desde la perspectiva de negocio y usuario final.

> **Nota de Gobernanza y Alcance (SCRUM-606 vs SCRUM-608):**  
> Este documento contiene exclusivamente la **especificación técnica de diseño de los casos de prueba** (actores, precondiciones, pasos, datos de entrada y resultados esperados).  
> La **sesión presencial de ejecución** y la firma del **Acta Formal de Aceptación con el Product Owner** corresponden a la tarea **`SCRUM-608`**, la cual se programará y ejecutará una vez la coordinación del proyecto designe formalmente a la persona que actuará como Product Owner y se coordine la fecha de la sesión.

---

## 2. Especificación de los 8 Casos de Prueba UAT

### UAT-001: Registro, Validación de Seguridad y Autenticación de Cliente Individual
* **ID Caso:** `UAT-001`
* **Actor / Rol:** Cliente Residencial (Nuevo Usuario)
* **Historias / Requisitos:** `SCRUM-21` / `RF-01`, `RF-02`, `RF-03` / `IDN-001`, `IDN-002`
* **Precondición:** El cliente no se encuentra registrado en el sistema. El servicio `Identity` está operativo en QA.
* **Pasos de Ejecución:**
  1. Abrir la aplicación cliente e ingresar a la pantalla de "Crear Cuenta".
  2. Diligenciar los campos obligatorios: Nombre completo, Correo electrónico, Teléfono y Contraseña.
  3. Probar una contraseña débil ($< 8$ caracteres o sin mayúscula/número) y verificar mensaje de rechazo RFC 9457.
  4. Ingresar una contraseña válida conforme a la política de seguridad y confirmar el formulario.
  5. Iniciar sesión con las credenciales registradas.
  6. Consultar la sección "Mi Perfil" (`GET /api/v1/users/me`).
* **Datos de Prueba:**
  - Correo: `cliente.uat.sp5@quickpatch.test`
  - Teléfono: `3001234567`
  - Contraseña Débil: `clave` (Debe ser rechazada)
  - Contraseña Válida: `QuickPatch2026*!`
* **Resultado Esperado:**
  - Creación exitosa de la cuenta con código HTTP `201 Created`.
  - Autenticación exitosa retornando token JWT con claims válidos de rol `client`.
  - Visualización correcta del perfil con nombre, correo y estado activo.

---

### UAT-002: Registro de Técnico, Especialidad y Validación de Aprobación Administrativa
* **ID Caso:** `UAT-002`
* **Actor / Rol:** Técnico Independiente y Administrador de Plataforma
* **Historias / Requisitos:** `SCRUM-22`, `SCRUM-39` / `RF-13`, `RF-19` / `IDN-010`
* **Precondición:** Catálogo de especialidades disponible en `Catalog`.
* **Pasos de Ejecución:**
  1. Ingresar por el portal de técnicos y seleccionar "Registro de Técnico Independiente".
  2. Diligenciar documento de identidad, especialidad (ej. Plomería) y datos de contacto.
  3. Enviar solicitud de registro y constatar estado inicial devuelto `pendiente_verificacion`.
  4. Intentar recibir asignaciones automáticas de trabajo (verificar que no es elegible en matching).
  5. Iniciar sesión como `admin_plataforma` en el panel administrativo web.
  6. Localizar al técnico en la lista de solicitudes pendientes y ejecutar la acción "Aprobar Técnico".
* **Datos de Prueba:**
  - Técnico: `Carlos Mendoza`
  - Correo: `carlos.tecnico.uat@quickpatch.test`
  - Documento: `CC-1098765432`
  - Especialidad: Plomería (`specialtyId: 0192d6e0-...`)
* **Resultado Esperado:**
  - Registro inicial en estado `pendiente_verificacion`.
  - El sistema no asigna órdenes al técnico mientras permanezca pendiente.
  - Aprobación administrativa exitosa (HTTP `200 OK`) con evento Outbox `technician.verification-changed` emitido y estado actualizado a `aprobado`.

---

### UAT-003: Creación de Solicitud de Servicio y Asignación Automática Geoespacial (Matching)
* **ID Caso:** `UAT-003`
* **Actor / Rol:** Cliente y Motor de Matching
* **Historias / Requisitos:** `SCRUM-28`, `SCRUM-29` / `RF-05`, `RF-09` / `MAT-001`, `SAD AC2-E1`
* **Precondición:** Existe un técnico en estado `aprobado`, con disponibilidad operativa activa y cobertura sobre la zona del servicio (Bogotá urbana).
* **Pasos de Ejecución:**
  1. El cliente inicia sesión y selecciona la categoría del servicio requerido.
  2. Ingresa la dirección del servicio (con validación de geocodificación en Bogotá) y descripción del problema.
  3. Confirma la solicitud y verifica que la orden se crea en estado `buscando_tecnico`.
  4. El motor de matching procesa la solicitud mediante búsqueda por PostGIS dentro del radio de cobertura.
  5. Verificar que el sistema genera y envía la oferta de asignación al técnico idóneo más cercano en menos de 60 segundos.
* **Datos de Prueba:**
  - Categoría: Fontanería / Reparación de Fuga
  - Dirección: `Calle 72 # 10-34, Bogotá`
  - Coordenadas: `lat: 4.6558, lng: -74.0583`
* **Resultado Esperado:**
  - Orden creada con ID único y estado `buscando_tecnico`.
  - Evento de matching procesado sin duplicidad (idempotencia garantizada por `processed_events`).
  - Oferta emitida hacia el técnico candidato en tiempo inferior a 60 segundos (percentil 95 cumplido).

---

### UAT-004: Notificación en Vivo, Aceptación de Oferta y Seguimiento de Estados
* **ID Caso:** `UAT-004`
* **Actor / Rol:** Técnico Asignado y Cliente
* **Historias / Requisitos:** `SCRUM-29`, `SCRUM-31`, `SCRUM-478` / `RF-10`, `RF-11`, `RF-32`
* **Precondición:** Oferta de asignación enviada al técnico. Conexión WebSocket establecida.
* **Pasos de Ejecución:**
  1. El técnico recibe la notificación de la oferta con el detalle preliminar del servicio y tarifa base.
  2. El técnico presiona el botón "Aceptar Oferta".
  3. Verificar que el estado de la solicitud transiciona atómicamente a `asignado`.
  4. En la pantalla del cliente, constatar que la vista de seguimiento se actualiza en tiempo real mostrando el nombre y especialidad del técnico asignado.
  5. El cliente intenta consultar la solicitud desde otra sesión sin permisos (verificar control de acceso).
* **Datos de Prueba:**
  - Oferta: ID generado en UAT-003
  - Acción: Aceptar dentro de la ventana de vigencia (30 segundos)
* **Resultado Esperado:**
  - Transición atómica a `asignado` (HTTP `200 OK`).
  - Notificación push / WebSocket entregada inmediatamente a la aplicación del cliente.
  - El cliente visualiza los datos del técnico asignado; accesos de terceros ajenos son bloqueados con HTTP 403 / 404.

---

### UAT-005: Inicio del Trabajo, Carga de Evidencia Fotográfica y Finalización del Servicio
* **ID Caso:** `UAT-005`
* **Actor / Rol:** Técnico Asignado
* **Historias / Requisitos:** `SCRUM-31`, `SCRUM-35`, `SCRUM-96` / `RF-11`, `RF-24`
* **Precondición:** Solicitud en estado `asignado`. Almacenamiento de objetos Garage S3 operativo en VM7.
* **Pasos de Ejecución:**
  1. El técnico llega al lugar y marca "Iniciar Trabajo" (`POST /api/v1/service-requests/{id}/start`).
  2. Verificar que la orden transiciona a `en_progreso`.
  3. El técnico intenta marcar "Finalizar Trabajo" sin subir evidencia fotográfica (verificar que el sistema lo rechaza con 400 Bad Request conforme a regla de negocio).
  4. El técnico sube la fotografía del trabajo culminado a Garage S3 vía URL prefirmada.
  5. El técnico reintenta "Finalizar Trabajo" adjuntando la URI de la evidencia.
* **Datos de Prueba:**
  - Archivo: Fotografía de prueba JPEG (`evidencia-reparacion-uat.jpg`)
  - Tamaño: $< 5\text{ MB}$
* **Resultado Esperado:**
  - Paso a `en_progreso` registrado con timestamp.
  - Bloqueo de finalización sin evidencia fotográfica previa.
  - Carga exitosa en bucket S3 y cierre de la orden en estado `completado`.

---

### UAT-006: Liquidación de Servicio, Simulación de Pasarela de Pagos y Comprobante
* **ID Caso:** `UAT-006`
* **Actor / Rol:** Cliente
* **Historias / Requisitos:** `SCRUM-43`, `SCRUM-45`, `SCRUM-495` / `RF-06`, `RF-07`
* **Precondición:** Solicitud en estado `completado`. Microservicio `Payments` en modo sandbox/mock.
* **Pasos de Ejecución:**
  1. El cliente visualiza la liquidación final del servicio con el detalle de mano de obra y tarifa base.
  2. Presiona "Pagar Servicio" y selecciona medio de pago simulado (tarjeta de crédito sandbox).
  3. Se procesa la transacción contra el adaptador mock de la pasarela.
  4. Verificar que el pago se registra como aprobado con su respectivo código de transacción.
  5. El cliente visualiza y descarga el comprobante digital de pago.
* **Datos de Prueba:**
  - Tarjeta Sandbox: Número de prueba de pasarela (sin números reales para cumplir PCI-DSS)
  - Monto: Tarifa base cotizada
* **Resultado Esperado:**
  - Transacción aprobada por el mock de pagos (HTTP `200 OK`).
  - Emisión del comprobante de pago con ID de transacción, correlationId y fecha.
  - Cero números de tarjeta reales registrados en base de datos ni en logs.

---

### UAT-007: Registro de Cuenta Corporativa, Gestión de Miembros y Solicitud Empresarial
* **ID Caso:** `UAT-007`
* **Actor / Rol:** Administrador de Empresa Corporativa y Empleado Autorizado
* **Historias / Requisitos:** `SCRUM-66`, `SCRUM-73` / `RF-22`, `RF-23`
* **Precondición:** Servicio de soporte para cuentas corporativas disponible en `Identity` y `ServiceRequest`.
* **Pasos de Ejecución:**
  1. Registrar una nueva empresa corporativa en la plataforma con NIT y razón social.
  2. El administrador de la empresa invita a un colaborador mediante su correo electrónico institucional.
  3. El colaborador acepta la invitación, establece su contraseña e inicia sesión.
  4. El colaborador solicita un servicio de mantenimiento locativo institucional indicando el centro de costos.
  5. Verificar que la orden se factura y asocia al tenant de la empresa y no a la cuenta personal del empleado.
* **Datos de Prueba:**
  - Empresa: `Soluciones Inmobiliarias S.A.S.`
  - NIT: `900.123.456-7`
  - Empleado: `operaciones@inmobiliaria.test`
  - Centro de Costos: `CC-SEDE-NORTE`
* **Resultado Esperado:**
  - Aprovisionamiento del tenant corporativo con aislamiento lógico RLS.
  - Vinculación exitosa del colaborador al tenant corporativo.
  - Solicitud de servicio radicada con imputación directa al centro de costos empresarial.

---

### UAT-008: Verificación de Aislamiento Multi-Tenant y Seguridad RBAC en Panel Web Admin
* **ID Caso:** `UAT-008`
* **Actor / Rol:** Administrador de Tenant A y Administrador de Tenant B
* **Historias / Requisitos:** `SCRUM-24`, `SCRUM-39`, `SCRUM-108` / `RF-19`, `RF-30`, `RF-31` / `SAD AC6-E2`
* **Precondición:** Existen dos tenants independientes (Tenant Alfa y Tenant Beta) con órdenes y técnicos registrados en cada uno.
* **Pasos de Ejecución:**
  1. Iniciar sesión como `admin_tenant` del Tenant Alfa.
  2. Consultar el listado de técnicos y solicitudes en el panel de control web.
  3. Intentar consultar directamente por API una orden perteneciente al Tenant Beta (`GET /api/v1/service-requests/{id-beta}`).
  4. Intentar modificar el estado o suspender un técnico perteneciente al Tenant Beta.
  5. Intentar acceder a rutas exclusivas de `admin_plataforma` con token de `admin_tenant`.
* **Datos de Prueba:**
  - Tenant Alfa: `tenant-alfa-id`
  - Tenant Beta: `tenant-beta-id`
  - Recurso Ajeno: ID de orden y técnico de Tenant Beta
* **Resultado Esperado:**
  - El administrador del Tenant Alfa visualiza únicamente los recursos de su propio tenant.
  - La consulta de recursos del Tenant Beta retorna HTTP `404 Not Found` estricto (RLS impide revelar la existencia del registro).
  - Intentos de alteración cross-tenant son rechazados con 404 / 403.
  - Invocación de endpoints de superadministrador bloqueada con HTTP `403 Forbidden`.

---

## 3. Protocolo de Ejecución para la Sesión con Product Owner (SCRUM-608)

1. **Convocatoria y Asignación:** La coordinación confirmará la persona designada como Product Owner y la fecha de la sesión presencial / remota.
2. **Ambiente Preparado:** La sesión se llevará a cabo sobre el ambiente desplegado de QA (`https://qa.quickpatch.internal`), con datos limpios de prueba sembrados específicamente para la sesión.
3. **Rol del Evaluador:** La Product Owner operará directamente las aplicaciones web y móvil ejecutando los pasos de la especificación anterior.
4. **Criterio de Dictamen:** Cada caso se calificará como *Aprobado*, *Aprobado con Observaciones* o *Rechazado*.
5. **Cierre Formal:** La sesión concluirá con el diligenciamiento y firma del Acta de Aceptación UAT correspondiente a la tarea **`SCRUM-608`**.
