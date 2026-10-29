# Guía de Estados de Componentes UI — QUICKPATCH

**Documento:** SCRUM-620  
**Versión:** 1.0  
**Fecha:** 2026-10-28  
**Audience:** Frontend (Flutter mobile, Angular web)

---

## Propósito

Esta guía documenta los estados visibles y transiciones de los componentes UI principales de QUICKPATCH, alineados con los estados de negocio del DD (sección 5) y los flujos del SDD.

Los componentes reflejan el estado real del backend: no anticipan transiciones, no cachean estados desactualizados.

---

## 1. Solicitud de Servicio (`ServiceRequest`)

**Estados principales:** `buscando_tecnico`, `en_espera`, `asignado`, `en_progreso`, `completado`, `cancelado`, `pagado`.

### Estados y transiciones

| Estado | Visible | Quién puede ver | Acciones disponibles | Icono/Color |
|--------|---------|-----------------|----------------------|------------|
| **buscando_tecnico** | Cliente | Cliente, admin | Cancelar | 🔍 Gris (progreso) |
| **en_espera** | Cliente | Cliente, admin | Cancelar | ⏳ Amarillo (pausa) |
| **asignado** | Cliente + técnico | Dueño (cliente/empresa, técnico) | Cliente: aceptar/rechazar cotización; Técnico: iniciar | 👨‍🔧 Azul |
| **en_progreso** | Cliente + técnico | Dueño | Cliente: ver avance; Técnico: completar | ⚙️ Naranja (activo) |
| **completado** | Cliente + técnico | Dueño | Cliente: calificar; Técnico: ver calificación | ✅ Verde |
| **pagado** | Cliente + técnico | Cliente (pago), técnico (reputación) | Cerrado | 💳 Verde oscuro |
| **cancelado** | Cliente + técnico | Dueño | No hay acciones | ❌ Rojo |

### Transiciones no permitidas

- No se puede volver de `completado` a `en_progreso`.
- No se puede cancelar desde `en_progreso` o después.
- No se puede pagar dos veces (`pagado` es terminal).

### Información visible por rol

- **Cliente propietario:** todo lo anterior, más dirección, ubicación, datos del técnico, cotización.
- **Empresa_contacto:** lo mismo que cliente si la solicitud es de la empresa.
- **Técnico asignado:** solo desde `asignado` en adelante; no ve dirección ni datos de cliente (RN-SR13) hasta `en_progreso`.
- **Admin_tenant:** todo, filtrable por estado.

---

## 2. Cotización (`Quote`)

Aparece cuando el técnico asignado propone un total a cobrar por mano de obra + materiales.

| Estado | Quién ve | Qué hace |
|--------|----------|----------|
| **En revisión** | Cliente | Acepta o rechaza. Si rechaza, vuelve a `asignado` y el técnico puede hacer otra oferta. |
| **Aceptada** | Ambos | Se cierra. El técnico puede iniciar el servicio. Cliente puede pagar desde aquí. |
| **Rechazada** | Ambos | Se cierra. No hay acción. |

---

## 3. Pago (`Payment`)

| Estado | Visible para | Acciones | Notas |
|--------|---------------|---------|----|
| **pendiente** | Cliente, admin | Pagar | Se crea cuando la cotización es aceptada. |
| **procesando** | Igual | Esperando respuesta de pasarela (simulada). App consulta periódicamente. | El estado es temporal. |
| **aprobado** | Igual | Cerrado. Solicitud pasa a `pagado`. | Técnico ve el pago en su historial. |
| **rechazado** | Igual | Reintentar pago | Se puede crear otro pago. |

---

## 4. Calificación (`Rating`)

Aparece después de `completado` y solo el cliente propietario puede calificar (una sola vez).

| Estado | Visible | Acciones |
|--------|---------|----------|
| **No calificada** | Cliente (solo en `completado`) | Calificar (1-5 estrellas + comentario opcional) |
| **Calificada** | Cliente + Técnico | Ver calificación. Técnico ve su reputación actualizada. |

---

## 5. Carritos y Caché

### Regla General

**No cachear estados de negocio.** Siempre consultar el servidor cuando el usuario abre una pantalla.

- **GET /v1/service-requests/{id}:** obtén el estado actual antes de mostrar.
- **GET /v1/service-requests?status=&page=&size=:** lista actualizada.
- **GET /v1/technicians/me/service-requests:** historial técnico con score/ratedAt si aplica.

### Optimización: Polling

Si un estado está en transición (`procesando`, `buscando_tecnico`), la app puede hacer polling cada 5 segundos para evitar que el usuario espere. Detener cuando el estado cambie.

---

## 6. WebSocket / Tiempo Real (Futuro)

La guía actual es para REST. Cuando Communication agregue WebSocket (RF-37, SCRUM-479), los cambios de estado llegarán en tiempo real vía `chat.message` en `realtime.v1.yaml`.

---

## 7. Errores Comunes en UI

| Error | Causa | Acción usuario |
|-------|-------|-----------------|
| `404 no-encontrado` | Solicitud no existe o no tiene permiso. | Reload. Si persiste, contactar soporte. |
| `409 transicion-invalida` | Acción no permitida desde este estado. | Reload para ver el estado actual. |
| `409 ya-calificada` | Ya calificó esta solicitud. | Mostrar la calificación existente (read-only). |
| `423 cuenta-bloqueada` | Login: 5 intentos fallidos. | Esperar 15 minutos. Mostrar `Retry-After`. |

---

## 8. Referencias

- **DD:** secciones 5 (Diccionario de Datos), 7 (Reglas de Negocio), 8.3 (Contratos).
- **SAD:** sección 7.4 (ciclo de vida de la solicitud).
- **SDD:** sección 11 (flujos de negocio).
- **RN-SR1 a RN-SR16:** reglas de solicitud de servicio.

---

**Historial:**

| Versión | Fecha | Cambio | SCRUM |
|---------|-------|--------|-------|
| 1.0 | 2026-10-28 | Creación inicial. Estados principales, transiciones, permisos. | SCRUM-620 |
