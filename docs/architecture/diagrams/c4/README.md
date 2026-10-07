# Diagramas C4 de QUICKPATCH

Fuente única de los diagramas C4 del SDD (sección 2.2). En el repositorio viven en `docs/architecture/diagrams/c4/`.

| Archivo | Contenido |
|---|---|
| `quickpatch.dsl` | Modelo y vistas en Structurizr DSL: System Landscape, System Context, Container, 10 Component, 6 Dynamic y 2 Deployment (21 vistas) |
| `C4-07-Codigo-OutboxIdempotencia.puml` | Nivel de código (UML de clases, PlantUML): Outbox e idempotencia de `service-request.created` |
| `C4-07-Codigo-AislamientoTenant.puml` | Nivel de código (UML de clases, PlantUML): aislamiento entre tenants en Identity |

## Exportar las vistas de Structurizr

Con Structurizr Lite (Docker), desde esta carpeta:

```bash
docker run -it --rm -p 8080:8080 -v "$PWD:/usr/local/structurizr" structurizr/lite
```

Abrir `http://localhost:8080`, entrar a cada vista y exportarla en PNG (botón de exportar → PNG). Structurizr nombra el archivo `structurizr-<clave>.png`; también sirve pegar el DSL en https://structurizr.com/dsl.

Para validar el DSL sin abrir el navegador:

```bash
docker run --rm -v "$PWD:/w" structurizr/structurizr validate -workspace /w/quickpatch.dsl
```

## Generar los diagramas de código

```bash
docker run --rm -i plantuml/plantuml -tpng -pipe < C4-07-Codigo-OutboxIdempotencia.puml > C4-07-Codigo-OutboxIdempotencia.png
docker run --rm -i plantuml/plantuml -tpng -pipe < C4-07-Codigo-AislamientoTenant.puml > C4-07-Codigo-AislamientoTenant.png
```

También se pueden pegar en https://www.plantuml.com/plantuml.

## Imágenes esperadas (23)

Se dejan en `C:\Users\juand\Documents\8_Semestre\Arquitectura\Diagramas`. En el repositorio quedan como `docs/architecture/diagrams/c4/<clave>.png`, sin el prefijo `structurizr-`.

| Clave | Tipo C4 | Sección del SDD |
|---|---|---|
| `C4-01-Landscape` | System Landscape | 3.1.0 |
| `C4-02-Contexto` | System Context | 3.1.0 |
| `C4-03-Contenedores` | Container | 3.1.4 |
| `C4-04-Componentes-Web` | Component | 3.1.5 |
| `C4-04-Componentes-Mobile` | Component | 3.1.5 |
| `C4-04-Componentes-Identity` | Component | 3.2.2 |
| `C4-04-Componentes-Actors` | Component | 3.2.3 |
| `C4-04-Componentes-Catalog` | Component | 3.2.4 |
| `C4-04-Componentes-ServiceRequest` | Component | 3.2.5 |
| `C4-04-Componentes-Matching` | Component | 3.2.6 |
| `C4-04-Componentes-Ranking` | Component | 3.2.7 |
| `C4-04-Componentes-Payments` | Component | 3.2.8 |
| `C4-04-Componentes-Communication` | Component | 3.2.9 |
| `C4-07-Codigo-OutboxIdempotencia` | Code (PlantUML) | 4.5.1 |
| `C4-07-Codigo-AislamientoTenant` | Code (PlantUML) | 4.5.2 |
| `C4-05-Dinamico-CrearSolicitud` | Dynamic | 5.3 |
| `C4-05-Dinamico-Pago` | Dynamic | 5.4 |
| `C4-05-Dinamico-InicioSesion` | Dynamic | 5.12 |
| `C4-05-Dinamico-ReplicaCategorias` | Dynamic | 5.12 |
| `C4-05-Dinamico-Calificacion` | Dynamic | 5.12 |
| `C4-05-Dinamico-GestionTenants` | Dynamic | 5.12 |
| `C4-06-Despliegue-Produccion` | Deployment | 7.1 |
| `C4-06-Despliegue-QA` | Deployment | 7.1 |

## Convenciones

- Los elementos y relaciones con la etiqueta `Planeado` están diseñados pero no existen en `develop`; se dibujan punteados.
- Un cambio de arquitectura se hace en el DSL o en el `.puml` y se vuelve a exportar; las imágenes no se editan a mano.
