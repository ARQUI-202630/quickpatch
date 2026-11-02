# Catálogo de Eventos Kafka — QUICKPATCH

**Documento:** SCRUM-593/594  
**Versión:** 1.0  
**Fecha:** 2026-10-31  
**Autor:** Backend (API Contracts)

---

## Propósito

Índice centralizado de todos los eventos Kafka de QUICKPATCH: propósito, productor, consumidores, campos, flujos.

Referencia: `quickpatch-kafka/events/` + `topics/topics.yaml`.

---

## 1. Eventos de Registro y Verificación

### `technician.registered` (v1.0)
- **Productor:** identity-service
- **Consumidores:** matching-service, communication-service
- **Cuándo:** Técnico o proveedor se registra (RF-02)
- **Campos clave:** technicianId, specialtyId, verificationStatus (pendiente), providerId (opcional), updatedAt
- **Propósito:** Matching crea proyección local (specialty, verification status) sin consultar Identity en cada búsqueda (P-01, ADR-017)
- **Referencia:** RF-02, DD 5.3, ADR-006, ADR-017, v4

### `technician.verification-changed` (v1.0)
- **Productor:** identity-service
- **Consumidores:** matching-service, communication-service
- **Cuándo:** Admin del tenant aprueba/rechaza/suspende técnico (RF-19, RF-20)
- **Campos clave:** technicianId, verificationStatus (aprobado|rechazado|suspendido), changedAt
- **Propósito:** Matching actualiza disponibilidad; Communication notifica al técnico
- **Referencia:** RF-19, RF-20, DD 8.3.13, SCRUM-39/40

---

## 2. Eventos de Solicitud de Servicio

### `service-request.created` (v1.0)
- **Productor:** service-request-service
- **Consumidores:** matching-service, communication-service
- **Cuándo:** Cliente crea una solicitud (RF-07, RF-08)
- **Campos clave:** serviceRequestId, clientId, categoryId, location (lat/lon), description, createdAt, clientType (hogar|empresa), companyId (opcional)
- **Propósito:** Matching inicia búsqueda de técnico; Communication notifica al cliente
- **Referencia:** RF-07, RF-08, DD 8.3.2, SCRUM-73

### `service-request.status-changed` (v1.0)
- **Productor:** service-request-service
- **Consumidores:** communication-service
- **Cuándo:** Cualquier cambio de estado de la solicitud
- **Campos clave:** serviceRequestId, status (buscando_tecnico|en_espera|asignado|cotizado|cotizacion_aceptada|en_progreso|completado|pagado|cancelado), clientId, technicianId (opcional), changedAt
- **Propósito:** Communication notifica en tiempo real a cliente y técnico; genera buzón y aviso en chat (ADR-023, SCRUM-456). Se publica en la misma transacción del cambio, solo si se aplicó (Outbox, ADR-007)
- **Referencia:** RF-17, DD 8.3.3, DD 8.3.4, SCRUM-466, RN-SR7, v5.1

### `service-request.cancelled` (v1.0)
- **Productor:** service-request-service
- **Consumidores:** matching-service
- **Cuándo:** Cliente cancela antes de iniciar servicio (RF-36)
- **Campos clave:** serviceRequestId, clientId, technicianId, reason, cancelledAt
- **Propósito:** Matching retira oferta y libera técnico (RN-M6)
- **Referencia:** RF-36, DD 8.3.5, SCRUM-472

### `service-request.completed` (v1.0)
- **Productor:** service-request-service
- **Consumidores:** matching-service, payments-service
- **Cuándo:** Técnico marca servicio completado (RF-15)
- **Campos clave:** serviceRequestId, technicianId, totalAmount (de cotización aceptada), completedAt
- **Propósito:** Matching libera técnico (RN-M6); Payments crea pago pendiente (RN-P4)
- **Referencia:** RF-15, DD 8.3.11, SCRUM-94

### `service-request.rated` (v1.0) ⭐ NUEVO SCRUM-497
- **Productor:** service-request-service
- **Consumidores:** ranking-service, communication-service
- **Cuándo:** Cliente califica servicio EN ESTADO PAGADO (RF-12, RN-R3)
- **Campos clave:** serviceRequestId, technicianId, score (1-5, RN-R1), ratedAt
- **Propósito:** Ranking calcula reputación (5+ calificaciones y promedio < 3.0 = lowReputation). Communication notifica (futuro)
- **Referencia:** RF-12, DD 8.3.12, RN-R1/R2/R3, ADR-027, SCRUM-497

---

## 3. Eventos de Cotización

### `service-request.quoted` (v1.0)
- **Productor:** service-request-service
- **Consumidores:** communication-service
- **Cuándo:** Técnico propone cotización (RF-34)
- **Campos clave:** serviceRequestId, technicianId, quotes (array con id, total, materials, labor), quotedAt
- **Propósito:** Communication notifica cotización al cliente
- **Referencia:** RF-34, DD 8.3.6, SCRUM-487

### `service-request.quote-accepted` (v1.0)
- **Productor:** service-request-service
- **Consumidores:** communication-service
- **Cuándo:** Cliente acepta cotización
- **Campos clave:** serviceRequestId, quoteId, acceptedAt
- **Propósito:** Communication notifica aceptación al técnico
- **Referencia:** RF-34, DD 8.3.8, SCRUM-487

### `service-request.quote-rejected` (v1.0)
- **Productor:** service-request-service
- **Consumidores:** communication-service
- **Cuándo:** Cliente rechaza cotización
- **Campos clave:** serviceRequestId, quoteId, rejectedAt
- **Propósito:** Communication notifica rechazo; técnico puede hacer otra oferta
- **Referencia:** RF-34, DD 8.3.9, SCRUM-487

### `service-request.started` (v1.0)
- **Productor:** service-request-service
- **Consumidores:** (ninguno por ahora; futuro para Communication)
- **Cuándo:** Técnico inicia el servicio (RF-14)
- **Campos clave:** serviceRequestId, technicianId, startedAt
- **Propósito:** Reservado para Communication en futuro
- **Referencia:** RF-14, DD 8.3.10, SCRUM-94

---

## 4. Eventos de Matching

### `matching.offer-created` (v1.0)
- **Productor:** matching-service
- **Consumidores:** communication-service
- **Cuándo:** Matching genera oferta para un técnico (búsqueda activa, RN-M9)
- **Campos clave:** serviceRequestId, attemptId (FK → matching_attempts), technicianId, expiresAt (3 minutos, RN-M8)
- **Propósito:** Communication notifica al técnico que tiene una oferta pendiente. No lleva dirección ni datos del cliente (RN-SR13)
- **Referencia:** RF-10, DD 8.3.4, RN-M8/M9, SCRUM-30, v4

### `matching.technician-assigned` (v1.0)
- **Productor:** matching-service
- **Consumidores:** service-request-service
- **Cuándo:** Técnico acepta oferta (RF-10)
- **Campos clave:** serviceRequestId, technicianId, assignedAt
- **Propósito:** ServiceRequest actualiza estado a `asignado`
- **Referencia:** RF-10, DD 8.3.7, SCRUM-35

### `matching.no-technician-available` (v1.0)
- **Productor:** matching-service
- **Consumidores:** service-request-service
- **Cuándo:** Ningún técnico disponible en cobertura (RN-M4)
- **Campos clave:** serviceRequestId, searchId, noAvailableAt
- **Propósito:** ServiceRequest pasa a `en_espera` (RN-SR6)
- **Referencia:** RF-11, DD 8.3.4, SCRUM-35

### `matching.search-resumed` (v1.0)
- **Productor:** matching-service
- **Consumidores:** service-request-service
- **Cuándo:** Solicitud en espera vuelve a tener candidatos (RN-M10: técnico aprobado, disponible, nueva cobertura, etc)
- **Campos clave:** serviceRequestId, clientId, trigger (disponibilidad|cobertura|aprobacion|liberacion|barrido), resumedAt
- **Propósito:** ServiceRequest vuelve de `en_espera` a `buscando_tecnico`; Matching reintenta con candidatos más nuevos
- **Referencia:** RF-10, RN-M10, DD 8.3.4, SCRUM-35, v4

---

## 5. Eventos de Pago

### `payment.approved` (v1.0)
- **Productor:** payments-service
- **Consumidores:** service-request-service
- **Cuándo:** Pasarela (simulada) aprueba pago (RF-23)
- **Campos clave:** paymentId, serviceRequestId, amount, approvedAt, invoiceId
- **Propósito:** ServiceRequest pasa a `pagado` (RN-SR4)
- **Referencia:** RF-23, DD 8.3.12, SCRUM-42

### `payment.rejected` (v1.0)
- **Productor:** payments-service
- **Consumidores:** service-request-service
- **Cuándo:** Pasarela rechaza pago (RF-23)
- **Campos clave:** paymentId, serviceRequestId, reason, rejectedAt
- **Propósito:** ServiceRequest no cambia estado; cliente puede reintentar
- **Referencia:** RF-23, DD 8.3.12, SCRUM-42

---

## 6. Eventos de Reputación

### `ranking.technician-reputation-changed` (v1.0) ⭐ NUEVO SCRUM-497
- **Productor:** ranking-service
- **Consumidores:** identity-service
- **Cuándo:** Reputación del técnico cambió (por calificación nueva)
- **Campos clave:** technicianId, averageRating (0-5, 0.1 precision), ratingCount, lowReputation, changedAt
- **Propósito:** Identity actualiza perfil técnico con reputación (promedio, conteo, flag bajo)
- **Referencia:** RF-16, ADR-027, SCRUM-497

---

## 7. Eventos de Catálogo

### `catalog.category-changed` (v1.0)
- **Productor:** catalog-service
- **Consumidores:** service-request-service, matching-service
- **Cuándo:** Categoría cambia nombre, descripción o estado (ADR-025)
- **Campos clave:** categoryId, name, description (opcional desde v1.0), status, changedAt
- **Propósito:** ServiceRequest y Matching mantienen caché actualizado
- **Referencia:** RF-05, ADR-025, SCRUM-331

---

## 8. Eventos de Tenant ⭐ NUEVO SCRUM-508

### `tenant.status-changed` (v1.0)
- **Productor:** identity-service
- **Consumidores:** service-request-service
- **Cuándo:** Estado del tenant cambió (activo ↔ inactivo)
- **Campos clave:** tenantId, status (activo|inactivo), updatedAt
- **Propósito:** ServiceRequest valida que el tenant esté activo al crear solicitudes (RN-T1). Tenant inactivo bloquea creación (RN-T1) e inicio de sesión
- **Referencia:** SCRUM-508, RN-T1, ADR-028, v5.15

---

## 9. Flujos de Extremo a Extremo

### Flujo de Creación y Matching
```
Cliente crea solicitud
    ↓
service-request.created (ServiceRequest → buscando_tecnico)
    ↓
Matching busca candidatos (RN-M9: aprobado, disponible, misma categoría, cobertura)
    ↓
matching.offer-created (3 min TTL, RN-M8) → Communication notifica técnico
    ↓ (técnico acepta)
matching.technician-assigned → service-request.status-changed a "asignado"
    ↓
    ├─ (técnico rechaza u oferta expira)
    └─ matching.no-technician-available → service-request.status-changed a "en_espera"
       → matching.search-resumed (RN-M10: cuando aparece candidato)
```

### Flujo de Cotización y Ejecución
```
Solicitud en estado "asignado"
    ↓
Técnico propone cotización
    ↓
service-request.quoted (status → cotizado) → Communication notifica cliente
    ↓ (cliente acepta)
service-request.quote-accepted (status → cotizacion_aceptada)
    ↓
Técnico inicia servicio
    ↓
service-request.started (status → en_progreso) → Communication notifica cliente
    ↓
Técnico completa con evidencia
    ↓
service-request.completed → Matching libera técnico (RN-M6), Payments crea pago (RN-P4)
```

### Flujo de Pago
```
Solicitud en "completado"
    ↓
Cliente paga
    ↓
payment.approved → service-request.status-changed a "pagado"
    ↓ (o payment.rejected → solicitud permanece en "completado", cliente puede reintentar)
```

### Flujo de Calificación y Reputación
```
Solicitud EN ESTADO PAGADO
    ↓
Cliente califica (score 1-5, RN-R1)
    ↓
service-request.rated → Ranking recibe calificación
    ↓
Ranking calcula: (5+ calificaciones AND promedio < 3.0) = lowReputation
    ↓
ranking.technician-reputation-changed (averageRating, ratingCount, lowReputation, updatedAt)
    ↓
Identity actualiza technician_profiles.average_rating (proyección local para filtros, ADR-017)
```

---

## 10. Transaccionalidad y Confiabilidad

Todos los eventos se publican con **Transactional Outbox Pattern** (ADR-007):
- Insert en tabla `outbox_events` en la misma transacción que el cambio de negocio.
- Publicador asíncrono consume y publica a Kafka.
- Consumer idempotencia vía `processed_events` (RN-EV1).

**Garantía:** At-least-once delivery. No se pierden eventos, pero pueden duplicarse; consumidores son idempotentes.

---

## 11. Referencias Cruzadas

| Área | Documento |
|------|-----------|
| Definiciones | DD (secciones 5, 8) |
| Arquitectura | SAD (sección 8, ADR-006, ADR-007) |
| Flujos | SDD (sección 11) |
| Decisiones | ADR-006 (Kafka), ADR-007 (Outbox), ADR-017 (particiones), ADR-027 (calificación) |

---

**Historial:**

| Versión | Fecha | Cambio | SCRUM |
|---------|-------|--------|-------|
| 1.0 | 2026-10-31 | Creación: 20 eventos, flujos, transaccionalidad | SCRUM-593/594 |

