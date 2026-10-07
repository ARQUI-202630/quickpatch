# Pruebas E2E y de Sistema (API) — QUICKPATCH

Este directorio contiene las colecciones y scripts de pruebas automatizadas de extremo a extremo (E2E) y de integración del sistema contra el API Gateway de QUICKPATCH.

Las colecciones aquí ubicadas se ejecutan automáticamente en el runner de integración de QA (VM1) a través del flujo de GitHub Actions `.github/workflows/pruebas-sistema.yml`.

---

## 1. Alcance y Casos Cubiertos

### Colección: `scrum-65-roles-y-tenants.postman_collection.json`

Esta suite valida los mecanismos de control de acceso por roles (RBAC) y las restricciones de ciclo de vida de los tenants según las especificaciones del SAD, DD y el Documento de Pruebas (TD V1):

| Tarea Jira | Caso TD | Método y Endpoint | Rol / Condición | Resultado Esperado | Criterio de Aceptación / Requisito |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **SCRUM-65** | `IDN-001` | `POST /api/v1/auth/login` | `admin_tenant` | **HTTP 200 OK** | Semilla: Obtención de token RS256 con rol verificado `admin_tenant`. |
| **SCRUM-65** | `CAT-001` | `POST /api/v1/catalog/admin/categories` | `admin_tenant` | **HTTP 201 Created** | Control positivo: Administrador crea categoría de servicio en el catálogo. |
| **SCRUM-65** | `IDN-002` | `POST /api/v1/auth/register/client` | Anónimo | **HTTP 201 Created** | Registro de usuario final con rol `cliente`. |
| **SCRUM-65** | `IDN-003` | `POST /api/v1/auth/login` | `cliente` | **HTTP 200 OK** | Semilla: Autenticación de cliente y obtención de token RS256. |
| **SCRUM-65** | `IDN-012` | `POST /api/v1/service-requests` | `admin_tenant` | **HTTP 403 Forbidden** | RF-07, IDN-012: Creación de solicitudes reservada exclusivamente al rol `cliente`. Retorna `problems/no-autorizado`. |
| **SCRUM-65** | `CAT-010` | `POST /api/v1/catalog/admin/categories` | `cliente` | **HTTP 403 Forbidden** | AC6-E3, CAT-010: Mutación de catálogo restringida exclusivamente a administradores. Retorna `problems/no-autorizado`. |
| **SCRUM-65** | `IDN-017` | `POST /api/v1/service-requests` | Anónimo (sin token) | **HTTP 401 Unauthorized** | AC6-E4, IDN-017: Rechazo inmediato de peticiones no autenticadas en el API Gateway. Retorna `problems/no-autenticado`. |
| **SCRUM-114** | `IDN-019` | `POST /api/v1/auth/login` | Tenant Inactivo | **HTTP 403 Forbidden** | RF-21, RN-T1: Bloqueo de inicio de sesión para credenciales de tenant suspendido/desactivado. |
| **SCRUM-114** | `TEN-001` | `POST /api/v1/service-requests` | Tenant Activo (`cliente`) | **HTTP 201 Created** | Control: Solicitudes de tenants activos son procesadas con normalidad (`buscando_tecnico`). |

---

## 2. Ejecución de las Pruebas

### Opción A: Ejecución Local Automatizada (con Mock Gateway)
Para validar la suite en un entorno de desarrollo local sin requerir la infraestructura de VM2 levantada:

```bash
node tests/e2e/run-e2e.js
```

El script iniciará automáticamente un servidor HTTP ligero en el puerto 8080 que emula las reglas del Gateway y ejecutará Newman sobre la colección.

### Opción B: Ejecución con Newman apuntando a QA (VM2)
Para ejecutar directamente contra el ambiente desplegado en QA:

```bash
npx --yes newman run tests/e2e/scrum-65-roles-y-tenants.postman_collection.json \
  --env-var "baseUrl=https://qa.quickpatch.internal" \
  --insecure \
  --reporters cli
```

O utilizando el runner:

```bash
node tests/e2e/run-e2e.js --remote
```

---

## 3. Integración en CI/CD

El pipeline `.github/workflows/pruebas-sistema.yml` detecta automáticamente cualquier archivo `tests/e2e/*.postman_collection.json` y lo ejecuta con el contenedor oficial de Newman dentro de la red del laboratorio:

```yaml
- name: Newman (colecciones de API)
  run: |
    for c in tests/e2e/*.postman_collection.json; do
      docker run --rm --add-host "$QA_HOST:$QA_IP" -v "$PWD/tests/e2e:/etc/newman" \
        postman/newman:6-alpine run "$(basename "$c")" --insecure --env-var "baseUrl=$BASE_URL"
    done
```
