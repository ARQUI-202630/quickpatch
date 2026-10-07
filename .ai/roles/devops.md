# Rol IA — DevOps

## Área

- `infrastructure/**`
- `.github/workflows/**`

## Stack a desplegar

Distribución aprobada en ADR-022 (3 + 3 + 1), migración en curso (SCRUM-334):

- VM1, herramientas: proxy de entrada :443, runner de GitHub, k6, Prometheus, Loki y Grafana.
- Producción: VM3 k3s (8 servicios, API Gateway y panel Angular), VM4 PostgreSQL/PostGIS y Redis, VM6 Kafka y Garage.
- QA, misma forma: VM2 k3s, VM5 datos, VM7 Kafka y Garage.
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
