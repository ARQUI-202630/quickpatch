# Diagramas Dinámicos: Cotización, Pago, Cancelación — SCRUM-591

**Documento:** SCRUM-591  
**Versión:** 1.0  
**Fecha:** 2026-10-31  
**Scope:** Flujos transaccionales de cotización, pago y cancelación

---

## 1. Flujo de Cotización (Quote)

Técnico propone mano de obra + materiales; cliente acepta o rechaza.

```mermaid
sequenceDiagram
    participant Tech as Técnico/App
    participant SR as ServiceRequest
    participant Kafka as Kafka
    participant Comm as Communication
    participant Client as Cliente/App
    
    Note over SR: Estado: asignado
    
    Tech->>SR: POST /v1/service-requests/{id}/quote<br/>(labor, materials, total)
    SR->>SR: INSERT quotes<br/>estado: propuesta
    SR->>Kafka: service-request.quoted
    
    Kafka->>Comm: Consume quoted
    Comm->>Client: Notifica: "Técnico propone $X"
    
    alt Cliente acepta
        Client->>SR: POST /v1/service-requests/{id}/quote/{qid}/accept
        SR->>SR: UPDATE quotes<br/>estado: aceptada
        SR->>Kafka: service-request.quote-accepted
        
        Kafka->>Comm: Consume quote-accepted
        Comm->>Tech: Notifica: "Cliente aceptó cotización"
        
        Note over SR: Ahora cliente puede pagar<br/>Técnico puede iniciar servicio
        
    else Cliente rechaza
        Client->>SR: POST /v1/service-requests/{id}/quote/{qid}/reject
        SR->>SR: UPDATE quotes<br/>estado: rechazada
        SR->>Kafka: service-request.quote-rejected
        
        Kafka->>Comm: Consume quote-rejected
        Comm->>Tech: Notifica: "Cliente rechazó oferta"
        
        Note over SR: Vuelve a estado asignado<br/>Técnico puede hacer nueva cotización
    end
```

---

## 2. Flujo de Pago (Payment)

Cliente paga con token; pasarela (simulada) aprueba o rechaza.

```mermaid
sequenceDiagram
    participant Client as Cliente/App
    participant Gateway as Pasarela (simulada)
    participant Payments as Payments Service
    participant Kafka as Kafka
    participant SR as ServiceRequest
    participant Conc as Conciliación (scheduler)
    
    Note over Client: Cotización aceptada, listo para pagar
    
    Client->>Gateway: Genera token (dispositivo)<br/>tok_sim_*
    Client->>Payments: POST /v1/service-requests/{id}/payment<br/>(paymentToken, billing)
    
    Payments->>Payments: INSERT payments<br/>status: pendiente
    Payments->>Payments: Responde paymentId<br/>Cliente muestra "Procesando..."
    
    Payments->>Payments: Envía token a pasarela (async)<br/>UPDATE status: procesando
    
    loop Cliente consulta (polling)
        Client->>Payments: GET /v1/service-requests/{id}/payment
        Payments->>Client: {status: procesando}
    end
    
    par Conciliación: cada N minutos
        Conc->>Gateway: Consulta resultado<br/>(paymentId, token)
        
        alt Pasarela responde APROBADO
            Conc->>Payments: UPDATE status: aprobado
            Conc->>Kafka: payment.approved
            Kafka->>SR: Consume approved
            SR->>SR: UPDATE status: pagado
            SR->>Kafka: service-request.status-changed
        else Pasarela responde RECHAZADO
            Conc->>Payments: UPDATE status: rechazado
            Conc->>Kafka: payment.rejected
        else Pasarela sin respuesta (timeout)
            Note over Conc: Reintenta después
        end
    end
    
    Client->>Payments: GET /v1/service-requests/{id}/payment
    Payments->>Client: {status: aprobado, invoiceId}
    
    Note over Client: Pago completado, solicitud en estado pagado
```

---

## 3. Flujo de Cancelación

Cliente cancela antes de iniciar el servicio; técnico se libera.

```mermaid
sequenceDiagram
    participant Client as Cliente/App
    participant SR as ServiceRequest
    participant Kafka as Kafka
    participant Match as Matching
    participant Tech as Técnico/App
    participant TA as technician_availability
    
    Note over SR: Estado: asignado, en_espera, o buscando_tecnico
    
    Client->>SR: POST /v1/service-requests/{id}/cancel<br/>(reason)
    
    SR->>SR: Valida RN-SR7: no cancelar desde<br/>en_progreso, completado, pagado, cancelado
    
    alt Validación OK
        SR->>SR: UPDATE status: cancelado<br/>UPDATE cancelledAt
        SR->>Kafka: service-request.cancelled
        
        alt Si hay técnico asignado
            Kafka->>Match: Consume cancelled
            Match->>TA: UPDATE technician_id=X<br/>status: disponible (libera técnico)
            Match->>Kafka: matching.technician-assigned (invalidado)
            
            Kafka->>Tech: Notifica: "Solicitud cancelada"
        else Sin técnico (en buscando_tecnico)
            Note over Kafka: Matching descarta búsqueda<br/>no hay acción
        end
        
        SR->>Kafka: service-request.status-changed → cancelado
        Kafka->>Communication: Notifica cliente
        
    else Validación falla (RN-SR7)
        SR->>Client: 409 transicion-invalida
        Note over Client: No se permite cancelación desde este estado
    end
```

---

## 4. Máquina de Estados Completa

Estados y transiciones permitidas según RN-SR1 a RN-SR8.

```mermaid
graph TD
    A["buscando_tecnico"] -->|Cliente cancela| B["❌ cancelado"]
    A -->|Matching asigna| C["en_espera o asignado"]
    
    C -->|Cliente cancela| B
    C -->|No hay técnico| D["en_espera"]
    C -->|Técnico asignado| E["asignado"]
    
    E -->|Técnico inicia| F["en_progreso"]
    
    F -->|Técnico completa| G["completado"]
    
    G -->|Cliente paga| H["pagado ✅"]
    
    G -->|Cliente califica| I["completado + calificado"]
    I -->|Cliente paga| H
    
    B -->|Terminal| J["Fin"]
    H -->|Terminal| J
    
    style A fill:#fff3cd
    style B fill:#f8d7da
    style D fill:#fff3cd
    style E fill:#d1ecf1
    style F fill:#ffeaa7
    style G fill:#c3e6cb
    style H fill:#90ee90
    style J fill:#e2e3e5
```

---

## 5. Transaccionalidad: Outbox Pattern

Cuando ocurren cambios de estado críticos, se insertan en `outbox_events` y se publican a Kafka.

```mermaid
graph LR
    A["Cambio de estado<br/>(cancelación, pago, etc.)"] -->|Insert| B["outbox_events<br/>(misma transacción)"]
    B -->|Commit| C["Evento persiste"]
    
    C -->|Publicador<br/>asíncrono| D["Kafka"]
    D -->|Consumer 1<br/>idempotente| E["Matching"]
    D -->|Consumer 2<br/>idempotente| F["Communication"]
    
    E -->|processed_events| G["Marca leído"]
    F -->|processed_events| G
    
    Note over B,C: Garantía: evento no se pierde<br/>aunque falle publicación inmediata
    Note over E,F: Garantía: idempotencia<br/>Si se reintenta, no cambia estado
```

---

## 6. Casos de Error

### Cancelación desde estado no permitido
```mermaid
graph LR
    A["en_progreso, completado,<br/>pagado, o ya cancelado"] -->|POST /cancel| B["409 transicion-invalida"]
    B --> C["Cliente ve: 'No se puede<br/>cancelar desde este estado'"]
    style B fill:#ffcdd2
```

### Pago sin cotización aceptada
```mermaid
graph LR
    A["Cotización no aceptada"] -->|POST /payment| B["422 pago-no-disponible"]
    B --> C["Cliente ve: 'Acepte la<br/>cotización primero'"]
    style B fill:#ffcdd2
```

### Calificación duplicada
```mermaid
graph LR
    A["Servicio ya calificado"] -->|POST /rating| B["409 ya-calificada"]
    B --> C["Cliente ve: calificación existente<br/>(read-only)"]
    style B fill:#ffcdd2
```

---

## 7. Notas de Implementación

1. **Cotización múltiple:** Técnico puede proponer varias cotizaciones; cliente acepta una (RN-Q3).

2. **Cancelación y reembolso:** Cancelación NO implementa reembolsos automáticos en el MVP (ADR-009, ADR-024).

3. **Conciliación:** Payments ejecuta cada N minutos para verificar pagos en `procesando`; no es time-critical.

4. **Polling vs. Webhook:** Cliente hace polling `GET /payment` porque la pasarela es simulada; en prod usaría webhook.

5. **Idempotencia:** `payment.approved` y `payment.rejected` son idempotentes; si se publican dos veces, el UPDATE es el mismo.

6. **Regla RN-SR4:** ServiceRequest solo pasa a `pagado` cuando `payment.approved` llega. No hay pase automático.

---

**Referencias:**
- RF-34, RF-35 (Cotización)
- RF-22, RF-23 (Pago)
- RF-36 (Cancelación)
- RN-SR1 a RN-SR8, RN-Q1 a RN-Q7, RN-P1 a RN-P6 (Reglas)
- DD 8.3.5 (Cancelación), 8.3.6-8.3.9 (Cotización), 8.3.12 (Pago)
- ADR-007 (Outbox), ADR-009 (Pasarela), ADR-024 (Fuera MVP)

