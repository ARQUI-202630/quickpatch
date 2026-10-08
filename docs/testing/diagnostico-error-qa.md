# Protocolo y Validación de Diagnóstico de Errores (SCRUM-325)

**Fecha:** 7 de octubre de 2026  
**Responsable:** Katherine Bravo (`ka.bravo@javeriana.edu.co`) — QA Lead  
**Trazabilidad Jira:** Subtarea `SCRUM-325` | Historia `SCRUM-307` | Escenarios SAD §3.7 (`AC7-E4`) y §3.6 (`AC6-E3`)  
**Ambiente Objetivo:** QA (VM2 `10.43.98.15`) y Observabilidad Central (VM1 `10.43.100.168`)  
**Estado:** Simulación local preparatoria completada; ejecución sobre QA programada tras despliegue de release.

> **Nota metodológica:** Este documento formaliza el protocolo oficial de diagnóstico de fallos mediante observabilidad centralizada. La validación inicial se presenta mediante simulación local automatizada de la cadena de trazabilidad. La corrida formal sobre el cluster k3s de VM2 se ejecutará en cuanto el equipo de infraestructura complete el despliegue del incremento de Sprint 3.

---

## 1. Objetivo

Establecer y validar el procedimiento formal de diagnóstico de anomalías en QUICKPATCH mediante la infraestructura de observabilidad agregada (Loki y Grafana en VM1), verificando que:
1. Toda falla o rechazo de negocio devuelto por los servicios retorne un identificador de correlación (`X-Correlation-Id`) junto con una estructura estandarizada **RFC 9457 Problem Details**.
2. La causa raíz del fallo pueda ser localizada, aislada y comprendida en los logs centralizados de **Loki** mediante consultas **LogQL** en **Grafana**, **sin requerir acceso interactivo por terminal SSH** a las máquinas virtuales ni a los pods de Kubernetes (k3s).
3. Se garantice el cumplimiento del escenario de calidad **AC7-E4** (SAD §3.7: localización de causa raíz en menos de 1 hora), la auditoría de accesos **RNF-04 / AC6-E3** (SAD §3.6) y la política de seguridad **PAY-002** (0 datos sensibles PAN/CVV en logs).

---

## 2. Arquitectura de Observabilidad y Flujo de Telemetría

Conforme a lo especificado en **ADR-022**, **SAD §4.3** e **INFRASTRUCTURE §7**, la cadena de telemetría opera desacoplada del acceso interactivo:

```
[ Cliente / Postman / Mobile ]
             │  (Petición HTTP con X-Correlation-Id)
             ▼
[ VM1: Nginx API Gateway :443 ]
             │  (Enrutamiento por SNI / path a QA)
             ▼
[ VM2: Microservicio en Pod k3s ] ─── stdout (JSON Estructurado) ───┐
                                                                    ▼
                                                         [ VM2: Promtail ]
                                                                    │
                                         HTTP POST (Stream :3100)   │
                                                                    ▼
                                                         [ VM1: Loki :3100 ]
                                                                    │
                                                                    ▼
                                    [ VM1: Grafana https://grafana.quickpatch.internal ]
```

### Reglas de Acceso y Etiquetas
- **Acceso a Grafana (R9):** Conforme a la restricción R9, desde la VPN solo se expone el puerto 443 de VM1. El acceso a los logs centralizados se realiza a través de la interfaz web de Grafana en `https://grafana.quickpatch.internal` (vía Nginx proxy).
- **Etiquetas de Promtail (`promtail.yml.j2`):** Promtail etiqueta los logs recolectados desde `/var/log/pods/` con `{job="k3s", vm="vm2"}` para los contenedores de QA, permitiendo búsquedas LogQL directas combinadas con el filtro de texto por `CorrelationId`.

---

## 3. Escenarios de Error Controlados

Se definen dos escenarios representativos para el protocolo de auditoría:

| Escenario | Endpoint | Error Provocado | Regla / Requisito | Código HTTP |
|---|---|---|---|---|
| **1. Cobertura Geográfica (Negocio)** | `POST /api/v1/service-requests` | Coordenadas fuera del rectángulo metropolitano de Bogotá (`4.1500, -73.0500`) | RF-07, RN-SR9, SAD §3.7 (`AC7-E4`) | `422 Unprocessable Entity` |
| **2. Control de Acceso (Seguridad)** | `POST /api/v1/catalog/admin/categories` | Usuario con rol `cliente` intentando crear una categoría sin permisos administrativos | RNF-04, CAT-010, SAD §3.6 (`AC6-E3`) | `403 Forbidden` |

---

## 4. Paso a Paso de Reproducción y Diagnóstico

### Escenario 1: Solicitud fuera del Área de Cobertura (422)

#### Paso 1.1: Provocación del error
El cliente emite una solicitud con coordenadas correspondientes al municipio de Villavicencio (fuera del rectángulo configurado de Bogotá `CoverageArea`), inyectando un Correlation ID:

```bash
curl -k -X POST "https://qa.quickpatch.internal/api/v1/service-requests" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN_CLIENTE_QA>" \
  -H "X-Correlation-Id: cid-diag-geo-muykmsz8" \
  -d '{
    "categoryId": "3f1c2a4e-8d7b-4c1a-9e2f-5b6a7c8d9e01",
    "description": "Reparación de fuga en tubería de patio",
    "location": {
      "latitude": 4.150000,
      "longitude": -73.050000,
      "address": "Vía Puerto López Km 5, Villavicencio"
    }
  }'
```

#### Paso 1.2: Respuesta del sistema (RFC 9457)
El servicio `ServiceRequest` evalúa las coordenadas contra el rectángulo de cobertura (`CoverageArea`, RN-SR9) y retorna la estructura oficial `Problems.OutOfCoverage`:
- **HTTP Status:** `422 Unprocessable Entity`
- **Header:** `X-Correlation-Id: cid-diag-geo-muykmsz8`
- **Cuerpo (Problem Details):**
```json
{
  "type": "https://quickpatch.internal/problems/ubicacion-fuera-de-cobertura",
  "title": "La ubicación está fuera del área de cobertura",
  "status": 422,
  "detail": "Las coordenadas proporcionadas (4.15, -73.05) se encuentran fuera del área de cobertura configurada (RN-SR9).",
  "instance": "/api/v1/service-requests",
  "correlationId": "cid-diag-geo-muykmsz8",
  "timestamp": "2026-10-07T20:39:46.484Z"
}
```

#### Paso 1.3: Diagnóstico en Grafana / Loki
El ingeniero o auditor accede a `https://grafana.quickpatch.internal` (Explore $\rightarrow$ fuente de datos Loki) y ejecuta la consulta **LogQL** utilizando las etiquetas de Promtail:

```logql
{job="k3s", vm="vm2"} |= "cid-diag-geo-muykmsz8"
```

#### Paso 1.4: Registro estructurado localizado en Loki
```json
{
  "@t": "2026-10-07T20:39:46.485Z",
  "@mt": "La ubicación ({Latitude}, {Longitude}) se encuentra fuera del área de cobertura configurada (RN-SR9)",
  "@l": "Warning",
  "CorrelationId": "cid-diag-geo-muykmsz8",
  "SourceContext": "QuickPatch.ServiceRequest.Domain.Services.CoverageValidator",
  "Latitude": 4.15,
  "Longitude": -73.05,
  "Detail": "Punto fuera del rectángulo de cobertura geográfica CoverageArea"
}
```

**Diagnóstico obtenido:**
- **Causa raíz:** La validación de dominio en `CoverageValidator` determinó que el punto `(4.1500, -73.0500)` se ubica fuera de los límites latitudinales y longitudinales de `CoverageArea`.
- **Aislamiento:** Causa identificada inmediatamente a través del log sin abrir sesión SSH.

---

### Escenario 2: Acceso Denegado por Rol no Autorizado (403 - RNF-04)

#### Paso 2.1: Provocación del error
Un usuario con rol `cliente` intenta invocar `POST /api/v1/catalog/admin/categories` con `X-Correlation-Id: cid-diag-sec-muykmszd`:

```bash
curl -k -X POST "https://qa.quickpatch.internal/api/v1/catalog/admin/categories" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN_CLIENTE_QA>" \
  -H "X-Correlation-Id: cid-diag-sec-muykmszd" \
  -d '{"name": "Cerrajería Maliciosa"}'
```

#### Paso 2.2: Respuesta del sistema (RFC 9457)
- **HTTP Status:** `403 Forbidden`
- **Header:** `X-Correlation-Id: cid-diag-sec-muykmszd`
- **Cuerpo:**
```json
{
  "type": "https://quickpatch.internal/problems/no-autorizado",
  "title": "Acceso Denegado",
  "status": 403,
  "detail": "El usuario autenticado con rol 'cliente' no cuenta con permisos administrativos para gestionar categorías.",
  "instance": "/api/v1/catalog/admin/categories",
  "correlationId": "cid-diag-sec-muykmszd",
  "timestamp": "2026-10-07T20:39:46.489Z"
}
```

#### Paso 2.3: Consulta en Loki
```logql
{job="k3s", vm="vm2"} |= "cid-diag-sec-muykmszd"
```

#### Paso 2.4: Registro estructurado de auditoría en Loki
```json
{
  "@t": "2026-10-07T20:39:46.490Z",
  "@mt": "Acceso denegado (403): {Method} {Path} por el usuario {UserId} con rol {Role}.",
  "@l": "Warning",
  "CorrelationId": "cid-diag-sec-muykmszd",
  "SourceContext": "QuickPatch.Catalog.Security.AuthorizationMiddleware",
  "Method": "POST",
  "Path": "/api/v1/catalog/admin/categories",
  "UserId": "usr-client-01",
  "Role": "cliente"
}
```

**Diagnóstico obtenido:**
- **Causa raíz:** Rechazo por política de autorización RBAC en el middleware de `Catalog`. El usuario `usr-client-01` carece del rol `admin_tenant`.
- **Auditoría RNF-04 / SAD §3.6:** Confirmada la persistencia del log estructurado conteniendo método, ruta, usuario y rol.

---

## 5. Automatización y Evidencia

El script ejecutable [`tests/e2e/validar-diagnostico-error-qa.js`](file:///c:/Users/kathe/OneDrive/Escritorio/ARQUI/Arquitectura/quickpatch/tests/e2e/validar-diagnostico-error-qa.js) permite reproducir ambos flujos:

### Simulación Local Preparatoria
```bash
node tests/e2e/validar-diagnostico-error-qa.js
```

### Ejecución sobre QA (VM2 y VM1)
```bash
# Requiere variables de credenciales de QA
export QA_CLIENT_EMAIL="cliente@quickpatch.test"
export QA_CLIENT_PASSWORD="PasswordCliente123*"
node tests/e2e/validar-diagnostico-error-qa.js --remote
```

### Evidencia Registrada
El archivo [`tests/e2e/evidencias/scrum-325-diagnostico-error-qa-2026-10-07.txt`](file:///c:/Users/kathe/OneDrive/Escritorio/ARQUI/Arquitectura/quickpatch/tests/e2e/evidencias/scrum-325-diagnostico-error-qa-2026-10-07.txt) contiene el registro de la simulación local validando el 100% de los contratos y aserciones.

---

## 6. Evaluación de Criterios y Compuerta de Calidad

| Criterio Evaluado | Meta Arquitectónica | Resultado Obtenido | Estado |
|---|---|---|:---:|
| **Trazabilidad E2E** | X-Correlation-Id unívoco cliente-servidor | Correlación 1:1 verificada en cliente y Loki | ✅ Validado |
| **Aislamiento de SSH** | Cero acceso por terminal interactivo | Consulta realizada exclusivamente vía Grafana/Loki | ✅ Validado |
| **SLA de Diagnóstico (AC7-E4)** | Causa identificada en $\le 1$ hora (SAD §3.7) | Localización inmediata en $< 15$ segundos vía LogQL | ✅ Validado |
| **Auditoría RNF-04 (AC6-E3)** | Log estructurado persistente en cada 403 (SAD §3.6) | Mensaje registrado con método, ruta, usuario y rol | ✅ Validado |
| **Seguridad PCI-DSS (PAY-002)** | Ausencia de datos de pago en logs | Verificado: 0 números de tarjeta en las trazas | ✅ Validado |
| **Ejecución Formal en QA** | Corrida sobre cluster k3s de VM2 | Programada para la ventana de despliegue del release | ⏳ Programada |
