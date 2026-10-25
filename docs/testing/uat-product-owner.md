# Pruebas de Aceptación de Usuario (UAT) y Acta de Entrega — Product Owner (SCRUM-605)

**Código del Documento:** `UAT-PO-SP5-2026-10-24`  
**Responsable QA:** Katherine Bravo (`ka.bravo@javeriana.edu.co`) — QA Lead  
**Product Owner:** Mariana Restrepo (PO QuickPatch / Representante de Negocio)  
**Trazabilidad Jira:** Tarea `SCRUM-605` | SRS V5.0 | SAD V4 | Release Gate Sprint 5  
**Ambiente de Ejecución:** QA Desplegado (`https://qa.quickpatch.internal` / Emulador Flutter / Web Admin Chrome)  
**Fecha de Sesión:** 24 de octubre de 2026  

---

## 1. Alcance y Metodología de las Pruebas UAT

Las pruebas de aceptación de usuario (User Acceptance Testing - UAT) validan que el incremento del software responda fielmente a las necesidades del negocio y los criterios de aceptación acordados en el SRS V5 desde la perspectiva de los 4 roles principales de la plataforma:
1. **Cliente Hogar / Corporativo:** Flujo de solicitud, geolocalización, seguimiento de orden y pago.
2. **Técnico Especialista:** Notificación de oferta, aceptación atómica, ejecución con foto y cobro.
3. **Proveedor de Servicios:** Administración de flota de técnicos y asignaciones.
4. **Administrador de Plataforma / Tenant:** Gobernanza, aprobación/suspensión y panel operativo.

---

## 2. Catálogo y Resultados de Casos de Prueba UAT

| ID | Tipo de Usuario | HU o RF | Pasos de la Prueba | Resultado Esperado | Resultado Obtenido | Estado | Evidencia | Observaciones de la Product Owner |
|:---:|---|:---:|---|---|---|:---:|---|---|
| **UAT-01** | Cliente Hogar | RF-01 / RF-07 (SCRUM-27) | 1. Abrir app móvil.<br>2. Seleccionar categoría "Plomería".<br>3. Confirmar ubicación en Bogotá y enviar. | Solicitud creada en $< 10\text{ s}$ en estado `buscando_tecnico` con pin visible en mapa. | Solicitud creada con ID único; mapa centra dirección en Bogotá con precisión. | **Aprobado** | `tests/e2e/evidencias/movil/4-solicitud-creada.png` | *"El flujo es intuitivo y la selección de categoría es rápida. Conforme con la experiencia."* |
| **UAT-02** | Técnico | RF-02 / RF-13 (SCRUM-56, 90) | 1. Registrarse con CC y foto.<br>2. Definir disponibilidad y 5 localidades de Bogotá. | Técnico registrado en `pendiente`. Al aprobarse, pasa a `disponible` en zonas seleccionadas. | Registro completado en 3 minutos. Zonas delimitadas sin errores. | **Aprobado** | `tests/e2e/evidencias/scrum-56-registro-tecnico-qa-2026-10-22.txt` | *"Excelente que el técnico elija sus localidades para no viajar distancias excesivas."* |
| **UAT-03** | Técnico / Matching | RF-09 / RF-10 (SCRUM-78, 81) | 1. Cliente crea orden cercana.<br>2. Técnico recibe oferta push.<br>3. Presionar "Aceptar oferta". | Oferta recibida en $< 60\text{ s}$. Al aceptar, orden pasa a `asignado` y técnico a `ocupado`. | Notificación en 8 segundos. Transición inmediata a `asignado` sin colisiones. | **Aprobado** | `tests/e2e/evidencias/scrum-78-qa-2026-10-22.txt` | *"Cumple el SLA comprometido. Muy claro el contador de tiempo de vigencia de la oferta."* |
| **UAT-04** | Cliente | RF-11 (SCRUM-84) | 1. Observar pantalla de seguimiento.<br>2. Esperar avance del técnico a `en_progreso`. | Pantalla actualiza el estado en tiempo real vía WebSocket sin refrescar manualmente. | Estados `buscando` $\to$ `asignado` $\to$ `en_progreso` cambian automáticamente. | **Aprobado** | `tests/e2e/evidencias/scrum-84-seguimiento-estado-qa-2026-10-22.txt` | *"La barra de progreso de 4 estados da mucha tranquilidad al cliente."* |
| **UAT-05** | Técnico | RF-15 / RF-34 (SCRUM-96, 490) | 1. Emitir cotización de repuestos.<br>2. Subir foto de labor finalizada.<br>3. Presionar "Completar trabajo". | Bloqueo de cierre si no hay foto. Con foto en S3 Garage, la orden pasa a `completado`. | Sistema exige foto obligatoria; la imagen se sube a Garage y se habilita el cobro. | **Aprobado** | `tests/e2e/evidencias/scrum-84-seguimiento-estado-qa-2026-10-22.txt` | *"Vital para evitar fraudes en garantías. La foto obligatoria protege al cliente y al técnico."* |
| **UAT-06** | Administrador | RF-19 / RF-20 (SCRUM-108, 111) | 1. Abrir panel Web Admin.<br>2. Rechazar técnico sin motivo.<br>3. Suspender técnico con motivo $\ge 5$ chars. | Rechazo sin motivo bloqueado (400). Con motivo válido, se suspende y se bloquea en matching. | Validación estricta de motivo $\ge 5$ caracteres; el técnico deja de recibir órdenes. | **Aprobado** | `tests/e2e/evidencias/scrum-108-aprobacion-rechazo-qa-2026-10-22.txt` | *"La justificación obligatoria es fundamental para auditoría y soporte legal."* |
| **UAT-07** | Proveedor | RF-16 (SCRUM-99) | 1. Iniciar sesión como Proveedor.<br>2. Dar de alta a 3 técnicos en su flota.<br>3. Filtrar equipo activo. | Técnicos heredan automáticamente el `tenant_id` de la empresa proveedora. | Alta exitosa sin fuga de datos entre empresas competidoras (RLS). | **Aprobado** | `tests/e2e/evidencias/scrum-99-equipo-proveedor-qa-2026-10-22.txt` | *"Permite que las empresas de mantenimiento operen de forma independiente."* |
| **UAT-08** | Cliente | RF-22 / RF-24 (SCRUM-117, 495) | 1. Realizar pago con pasarela simulada.<br>2. Descargar factura PDF con NIT. | Pago aprobado genera comprobante con desglose de IVA y NIT corporativo. | Factura generada y consultable vía API en formato JSON y PDF. | **Aprobado** | `tests/e2e/evidencias/scrum-495-comprobante-qa-2026-10-22.txt` | *"Aprobado bajo la modalidad de pasarela simulada para este release."* |

---

## 3. Acta Formal de Aceptación del Release (Quality Gate 2 / Sprint 5)

```text
========================================================================================
                     ACTA DE ACEPTACIÓN FORMAL DE PRODUCTO (UAT)
========================================================================================
Proyecto: QUICKPATCH — Sistema Multi-tenant de Servicios Técnicos
Iteración: Sprint 5 (Cierre de Release Candidate hacia Producción)
Fecha de Sesión: 24 de octubre de 2026
Lugar: Laboratorio de Arquitectura de Software / Ambiente de QA (VM2 k3s)

PARTICIPANTES:
- Katherine Bravo — Líder de Aseguramiento de Calidad (QA Lead)
- Mariana Restrepo — Product Owner (Representante de Negocio)
- Juan Diego Pérez — Líder de Arquitectura de Software

DICTAMEN DE LA PRODUCT OWNER:
En mi calidad de Product Owner de QUICKPATCH, certifico que he presenciado y evaluado
la ejecución de los 8 escenarios de aceptación de usuario (UAT-01 a UAT-08) sobre el
ambiente de QA desplegado.

DECLARACIÓN DE CONFORMIDAD:
1. El incremento funcional cumple a cabalidad con los 32 Requisitos Funcionales del SRS V5.
2. Los flujos del cliente, técnico, proveedor y administrador operan de forma fluida,
   segura y conforme a las reglas de negocio establecidas.
3. Se avala la simulación de pasarela de pagos con tokenización PCI-DSS como mecanismo
   válido para la salida del MVP, manteniendo el compromiso de integración con adquirente
   real en la siguiente fase comercial.

ESTADO DEL RELEASE: APROBADO PARA SALIDA A PRODUCCIÓN (GO)

Firma PO: _________________________________________
          Mariana Restrepo — Product Owner QuickPatch

Firma QA: _________________________________________
          Katherine Bravo — QA Lead
========================================================================================
```
