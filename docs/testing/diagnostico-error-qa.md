# Protocolo y Validación de Diagnóstico de Errores en QA (SCRUM-325)

**Fecha:** 7 de octubre de 2026  
**Responsable:** Katherine Bravo (`ka.bravo@javeriana.edu.co`) — QA Lead  
**Trazabilidad Jira:** Subtarea `SCRUM-325` | Historia `SCRUM-307` | Escenarios SAD §4.3 (`AC7-E4`, `AC6-E3`)  
**Ambiente:** QA (VM2 `10.43.98.15`) y Observabilidad Central (VM1 `10.43.100.168`)

---

## 1. Objetivo

Demostrar de forma práctica y controlada la capacidad de diagnóstico de fallos en el ambiente de QA mediante el stack centralizado de observabilidad (Loki y Grafana en VM1), verificando que:
1. Cualquier error originado en los microservicios de QA retorna un identificador único de correlación (`X-Correlation-Id`) junto con una estructura estandarizada **RFC 9457 Problem Details**.
2. La causa raíz del fallo puede ser identificada, analizada y aislada en los logs agregados de **Loki** mediante consultas **LogQL**, **sin requerir acceso interactivo por SSH** a las máquinas virtuales ni a los contenedores de Kubernetes (k3s).
3. Se cumple con el escenario de calidad **AC7-E4** (localización de causa raíz en menos de 1 hora) y la política de seguridad **PAY-002** (ausencia estricta de números de tarjeta PAN o códigos CVV en los logs).

---

## 2. Arquitectura de Observabilidad y Cadena de Logs

Conforme a lo establecido en **ADR-022** e **INFRASTRUCTURE §7**, el flujo de telemetría de errores sigue una ruta unidireccional desacoplada:

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
                                                   [ VM1: Grafana :3000 / Web ]
```

### Componentes y Roles
- **Servicios ASP.NET Core & Spring Boot (VM2):** Emiten eventos estructurados a la salida estándar (`stdout`) formateados en JSON mediante `Microsoft.Extensions.Logging` / Serilog o SLF4J.
- **Promtail (VM2):** Demonio local que recolecta las líneas de log de `/var/log/pods/quickpatch_*`, inyecta etiquetas contextuales (`vm="vm2"`, `entorno="qa"`, `namespace="quickpatch"`, `service="<microservicio>"`) y las transmite de manera continua al puerto 3100 de VM1.
- **Loki (VM1):** Motor de indexación y almacenamiento persistente de logs de las 7 VMs.
- **Grafana (VM1):** Interfaz web unificada (`https://grafana.quickpatch.internal`) para consulta de métricas y logs con sintaxis LogQL.

---

## 3. Escenarios de Error Controlados

Para validar la trazabilidad completa, se seleccionaron dos escenarios representativos de negocio y seguridad:

| Escenario | Endpoint | Error Provocado | Regla / Requisito | Código HTTP |
|---|---|---|---|---|
| **1. Geo-espacial (Negocio)** | `POST /api/v1/service-requests` | Coordenadas fuera del polígono metropolitano de Bogotá (`4.1500, -73.0500`) | RF-07, AC7-E4, RN-S1 | `422 Unprocessable Entity` |
| **2. Control de Acceso (Seguridad)** | `POST /api/v1/catalog/admin/categories` | Cliente intentando crear una categoría sin permisos administrativos | RNF-04, AC6-E3, CAT-010 | `403 Forbidden` |

---

## 4. Paso a Paso de Reproducción y Diagnóstico

### Escenario 1: Solicitud de Servicio fuera de Cobertura (422)

#### Paso 1.1: Provocación del error desde el cliente
Se emite una solicitud con coordenadas correspondientes al municipio de Villavicencio (fuera del perímetro operativo de Bogotá) inyectando un identificador de auditoría:

```bash
curl -k -X POST "https://qa.quickpatch.internal/api/v1/service-requests" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN_CLIENTE>" \
  -H "X-Correlation-Id: cid-diag-qa-geo-muyeapd7" \
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
El API Gateway y el servicio `service-request` devuelven inmediatamente:
- **HTTP Status:** `422 Unprocessable Entity`
- **Header:** `X-Correlation-Id: cid-diag-qa-geo-muyeapd7`
- **Cuerpo (Problem Details):**
```json
{
  "type": "https://quickpatch.internal/problems/fuera-de-cobertura",
  "title": "Ubicación fuera de zona de cobertura",
  "status": 422,
  "detail": "Las coordenadas proporcionadas (4.15, -73.05) se encuentran fuera del área metropolitana de Bogotá.",
  "instance": "/api/v1/service-requests",
  "correlationId": "cid-diag-qa-geo-muyeapd7",
  "timestamp": "2026-10-07T17:42:24.258Z",
  "invalidParams": [
    {
      "name": "location",
      "reason": "Punto geográfico fuera de los límites de Bogotá D.C."
    }
  ]
}
```

#### Paso 1.3: Localización de la causa raíz en Loki (VM1)
El ingeniero o auditor accede a Grafana en `https://grafana.quickpatch.internal` (o consulta directamente la API de Loki en `http://10.43.100.168:3100`) y ejecuta la consulta **LogQL**:

```logql
{entorno="qa", service="service-request"} |= "cid-diag-qa-geo-muyeapd7"
```

#### Paso 1.4: Registro estructurado encontrado
Loki retorna de forma instantánea el registro estructurado emitido por el pod en VM2:

```json
{
  "@t": "2026-10-07T17:42:24.259Z",
  "@mt": "Validación de cobertura fallida para solicitud de servicio: punto ({Latitude}, {Longitude}) fuera de Bogotá",
  "@l": "Warning",
  "CorrelationId": "cid-diag-qa-geo-muyeapd7",
  "Service": "service-request",
  "Environment": "qa",
  "TenantId": "a1a1a1a1-bbbb-cccc-dddd-eeeeeeeeeeee",
  "UserId": "usr-client-01",
  "Action": "CreateServiceRequest",
  "StatusCode": 422,
  "ErrorCode": "ERR_LOCATION_OUT_OF_BOUNDS",
  "Latitude": 4.15,
  "Longitude": -73.05,
  "Detail": "Punto espacial no intercepta el polígono PostGIS de cobertura metropolitana de Bogotá"
}
```

**Diagnóstico obtenido:**
- **Causa raíz:** La función `ST_Within(point, polygon)` de PostGIS retornó `false` al evaluar las coordenadas `(4.1500, -73.0500)` contra la tabla `coverage_zones`.
- **Tiempo de diagnóstico:** Menor a **15 segundos** desde la ocurrencia del error.
- **Acceso:** Realizado 100% mediante consulta LogQL, sin abrir ninguna sesión SSH a VM2 ni a los pods.

---

### Escenario 2: Acceso Denegado por Rol no Autorizado (403 - RNF-04)

#### Paso 2.1: Provocación del error
Un usuario autenticado con rol `cliente` intenta invocar un endpoint administrativo reservado para el rol `admin_tenant`:

```bash
curl -k -X POST "https://qa.quickpatch.internal/api/v1/catalog/admin/categories" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN_CLIENTE>" \
  -H "X-Correlation-Id: cid-diag-qa-sec-muyeape1" \
  -d '{"name": "Cerrajería Maliciosa"}'
```

#### Paso 2.2: Respuesta del sistema (RFC 9457)
- **HTTP Status:** `403 Forbidden`
- **Header:** `X-Correlation-Id: cid-diag-qa-sec-muyeape1`
- **Cuerpo:**
```json
{
  "type": "https://quickpatch.internal/problems/no-autorizado",
  "title": "Acceso Denegado",
  "status": 403,
  "detail": "El usuario autenticado con rol 'cliente' no cuenta con permisos administrativos para gestionar categorías.",
  "instance": "/api/v1/catalog/admin/categories",
  "correlationId": "cid-diag-qa-sec-muyeape1",
  "timestamp": "2026-10-07T17:42:24.264Z"
}
```

#### Paso 2.3: Consulta en Loki (VM1)
```logql
{entorno="qa", service="catalog"} |= "cid-diag-qa-sec-muyeape1"
```

#### Paso 2.4: Registro estructurado de auditoría en Loki
```json
{
  "@t": "2026-10-07T17:42:24.265Z",
  "@mt": "Acceso denegado (403): usuario con rol '{Role}' intentó acceder a '{Path}'",
  "@l": "Warning",
  "CorrelationId": "cid-diag-qa-sec-muyeape1",
  "Service": "catalog",
  "Environment": "qa",
  "TenantId": "a1a1a1a1-bbbb-cccc-dddd-eeeeeeeeeeee",
  "UserId": "usr-client-01",
  "Role": "cliente",
  "Path": "/api/v1/catalog/admin/categories",
  "Method": "POST",
  "StatusCode": 403,
  "ErrorCode": "ERR_FORBIDDEN_ACCESS",
  "Rule": "RNF-04 / CAT-010"
}
```

**Diagnóstico obtenido:**
- **Causa raíz:** Violación de política de autorización RBAC en el middleware de `Catalog`. El usuario `usr-client-01` carece del rol `admin_tenant`.
- **Cumplimiento normativo:** Queda verificado el cumplimiento estricto de **RNF-04** (todo evento 403 queda auditado con método, ruta, usuario y rol en Loki).

---

## 5. Automatización y Evidencia Ejecutable

Se implementó el script de verificación automatizada:
[`tests/e2e/validar-diagnostico-error-qa.js`](file:///c:/Users/kathe/OneDrive/Escritorio/ARQUI/Arquitectura/quickpatch/tests/e2e/validar-diagnostico-error-qa.js)

### Ejecución Local
```bash
node tests/e2e/validar-diagnostico-error-qa.js
```

### Ejecución contra el Ambiente Real de QA (VM2 & VM1)
```bash
node tests/e2e/validar-diagnostico-error-qa.js --remote
```

### Evidencia Registrada
El archivo de evidencia [`tests/e2e/evidencias/scrum-325-diagnostico-error-qa-2026-10-07.txt`](file:///c:/Users/kathe/OneDrive/Escritorio/ARQUI/Arquitectura/quickpatch/tests/e2e/evidencias/scrum-325-diagnostico-error-qa-2026-10-07.txt) contiene la corrida completa demostrando la inyección, respuesta Problem Details y extracción de trazas en Loki con **0 fallos**.

---

## 6. Conclusiones y Cumplimiento de Criterios

| Criterio Evaluado | Meta de Arquitectura | Resultado Obtenido | Estado |
|---|---|---|:---:|
| **Trazabilidad E2E** | X-Correlation-Id presente en cliente y backend | Correlación exacta 1:1 verificada en ambos casos | ✅ Aprobado |
| **Aislamiento de SSH** | Cero acceso interactivo a contenedores | Diagnóstico 100% realizado desde Loki/Grafana | ✅ Aprobado |
| **SLA de Diagnóstico (AC7-E4)** | Causa identificada en $\le 1$ hora | Localización en $< 15$ segundos vía LogQL | ✅ Aprobado |
| **Auditoría RNF-04** | Registro obligatorio de todo 403 | Log persistido con rol, usuario y endpoint | ✅ Aprobado |
| **Seguridad PCI-DSS (PAY-002)** | Cero datos de pago (PAN / CVV) en logs | Verificado: 0 números de tarjeta en trazas | ✅ Aprobado |
