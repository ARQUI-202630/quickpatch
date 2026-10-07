# Rol IA — DevOps

## Área

- `infrastructure/**`
- `.github/workflows/**`

## Stack a desplegar

Reparto aprobado en ADR-022 (1 + 3 + 3), migración en curso (SCRUM-334):

- VM7, herramientas: Garage de producción, Prometheus, Loki y Grafana.
- Producción: VM1 entrada (Nginx, API Gateway, panel Angular, runner y k6), VM3 k3s con los 8 servicios, VM4 PostgreSQL/PostGIS, Redis y Kafka.
- QA, misma forma: VM2 entrada, VM5 k3s, VM6 datos, Kafka y Garage de QA.
- Recursos por servicio (base, usuario de Redis, llave de Garage): `docs/infrastructure/INFRASTRUCTURE.md`, sección 3.4.

## Toolchains

CI debe contemplar:
- .NET SDK / `dotnet`;
- JDK + Maven/Gradle para Matching;
- Node/Angular CLI para build web;
- Flutter SDK para mobile.

## Regla de recursos

No reutilizar automáticamente los límites históricos de NestJS como límites .NET.

Requests/limits definitivos deben medirse y cumplir el presupuesto/atributos de calidad de VM3.

## No modificar por defecto

Lógica de negocio, endpoints funcionales o modelos de dominio.
