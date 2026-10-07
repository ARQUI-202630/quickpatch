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

## Imágenes (23)

En el repositorio están en `docs/architecture/diagrams/c4/<clave>.png`, sin el prefijo `structurizr-` que pone Structurizr al exportar. Se exportan con metadatos y sin recortar (opciones por defecto del botón de exportar).

| Clave | Tipo C4 | Sección del SDD |
|---|---|---|
| `C4-01-Landscape` | System Landscape | 3 |
| `C4-02-Contexto` | System Context | 4 |
| `C4-03-Contenedores` | Container | 5.1 |
| `C4-04-Componentes-Web` | Component | 6.2 |
| `C4-04-Componentes-Mobile` | Component | 6.2 |
| `C4-04-Componentes-Identity` | Component | 6.4 |
| `C4-04-Componentes-Actors` | Component | 6.5 |
| `C4-04-Componentes-Catalog` | Component | 6.6 |
| `C4-04-Componentes-ServiceRequest` | Component | 6.7 |
| `C4-04-Componentes-Matching` | Component | 6.8 |
| `C4-04-Componentes-Ranking` | Component | 6.9 |
| `C4-04-Componentes-Payments` | Component | 6.10 |
| `C4-04-Componentes-Communication` | Component | 6.11 |
| `C4-07-Codigo-OutboxIdempotencia` | Code (PlantUML) | 7.1 |
| `C4-07-Codigo-AislamientoTenant` | Code (PlantUML) | 7.2 |
| `C4-05-Dinamico-CrearSolicitud` | Dynamic | 8.3 |
| `C4-05-Dinamico-Pago` | Dynamic | 8.4 |
| `C4-05-Dinamico-InicioSesion` | Dynamic | 8.5 |
| `C4-05-Dinamico-ReplicaCategorias` | Dynamic | 8.5 |
| `C4-05-Dinamico-Calificacion` | Dynamic | 8.5 |
| `C4-05-Dinamico-GestionTenants` | Dynamic | 8.5 |
| `C4-06-Despliegue-Produccion` | Deployment | 9.1 |
| `C4-06-Despliegue-QA` | Deployment | 9.1 |

## Convenciones

- Cada vista fija su `autoLayout` (dirección y separación) para que el PNG quede apaisado y sin solapamientos; si un cambio del modelo desordena una vista, se ajusta ahí y no en la imagen.
- Las vistas donde los grupos estorban la distribución los ocultan con la propiedad `structurizr.groups false`.

- Los elementos y relaciones con la etiqueta `Planeado` están diseñados pero no existen en `develop`; se dibujan punteados.
- Un cambio de arquitectura se hace en el DSL o en el `.puml` y se vuelve a exportar; las imágenes no se editan a mano.
