# Dependencias desde el código — antes y despues del refactor

Comparación generada el 2026-11-12 con `python tools/arquitectura/comparar.py`, a partir de [`antes/`](antes/README.md) y [`despues/`](despues/README.md). Las dos mediciones usan la misma herramienta y la misma configuración (`tools/arquitectura/generar.py`, SCRUM-681).

## Resumen

| Servicio | Commit antes | Commit después | Violaciones | Ciclos paquetes | Tipos > 250 líneas | Fan-out máx.¹ | Cohesión H |
|---|---|---|---|---|---|---|---|
| Identity (sin refactor integrado) | `abffadb` | `fe22c14` | 11 → 11 | 1 → 0 | 2 → 2 | 80 → 79 | 0.81 → 0.79 |
| Catalog | `b7c38cb` | `6345700` | 0 → 0 | 0 → 0 | 0 → 0 | 15 → 14 | 0.85 → 0.86 |
| ServiceRequest | `394a1e8` | `45c0653` | 0 → 0 | 0 → 0 | 2 → 1 | 31 → 21 | 0.79 → 0.77 |
| Matching | `3fade78` | `8e6450c` | 0 → 0 | 1 → 0 | 0 → 0 | 10 → 13 | 0.85 → 0.75 |
| Ranking | `867716d` | `1679652` | 0 → 0 | 0 → 0 | 0 → 0 | 10 → 10 | 0.79 → 0.89 |
| Payments | `4435eac` | `6a2b893` | 0 → 0 | 1 → 0 | 0 → 0 | 12 → 11 | 0.78 → 0.77 |
| Communication (sin refactor integrado) | `120623a` | `fe01c13` | 0 → 0 | 0 → 0 | 0 → 0 | 10 → 10 | 0.83 → 0.83 |

1. Sin las raíces de composición (`Program` y `DependencyInjection`).

## Identity

Sin el refactor de SCRUM-650 (pendiente). El cambio sale de adoptar `quickpatch-shared-dotnet` (ADR-020, SCRUM-657): el Outbox y el consumo de Kafka salen del servicio y desaparece el ciclo entre `Infrastructure.Messaging` e `Infrastructure.Persistence`. Las 11 violaciones siguen.

| Métrica | Antes | Después | Resultado |
|---|---|---|---|
| Violaciones de SDD 10.3.2 | 11 | 11 | = |
| Ciclos entre paquetes | 1 | 0 | mejora |
| Ciclos entre tipos | 0 | 0 | = |
| Tipos de más de 250 líneas | 2 | 2 | = |
| Fan-out máximo¹ | 80 | 79 | mejora |
| Dependencias entre paquetes | 93 | 91 | mejora |
| Cohesión relacional promedio (H) | 0.81 | 0.79 | empeora |
| Tipos | 186 | 182 | = |

## Catalog

| Métrica | Antes | Después | Resultado |
|---|---|---|---|
| Violaciones de SDD 10.3.2 | 0 | 0 | = |
| Ciclos entre paquetes | 0 | 0 | = |
| Ciclos entre tipos | 0 | 0 | = |
| Tipos de más de 250 líneas | 0 | 0 | = |
| Fan-out máximo¹ | 15 | 14 | mejora |
| Dependencias entre paquetes | 26 | 22 | mejora |
| Cohesión relacional promedio (H) | 0.85 | 0.86 | mejora |
| Tipos | 42 | 38 | = |

## ServiceRequest

| Métrica | Antes | Después | Resultado |
|---|---|---|---|
| Violaciones de SDD 10.3.2 | 0 | 0 | = |
| Ciclos entre paquetes | 0 | 0 | = |
| Ciclos entre tipos | 0 | 0 | = |
| Tipos de más de 250 líneas | 2 | 1 | mejora |
| Fan-out máximo¹ | 31 | 21 | mejora |
| Dependencias entre paquetes | 111 | 109 | mejora |
| Cohesión relacional promedio (H) | 0.79 | 0.77 | empeora |
| Tipos | 211 | 211 | = |

## Matching

| Métrica | Antes | Después | Resultado |
|---|---|---|---|
| Violaciones de SDD 10.3.2 | 0 | 0 | = |
| Ciclos entre paquetes | 1 | 0 | mejora |
| Ciclos entre tipos | 0 | 0 | = |
| Tipos de más de 250 líneas | 0 | 0 | = |
| Fan-out máximo¹ | 10 | 13 | empeora |
| Dependencias entre paquetes | 34 | 36 | empeora |
| Cohesión relacional promedio (H) | 0.85 | 0.75 | empeora |
| Tipos | 45 | 49 | = |

## Ranking

| Métrica | Antes | Después | Resultado |
|---|---|---|---|
| Violaciones de SDD 10.3.2 | 0 | 0 | = |
| Ciclos entre paquetes | 0 | 0 | = |
| Ciclos entre tipos | 0 | 0 | = |
| Tipos de más de 250 líneas | 0 | 0 | = |
| Fan-out máximo¹ | 10 | 10 | = |
| Dependencias entre paquetes | 19 | 17 | mejora |
| Cohesión relacional promedio (H) | 0.79 | 0.89 | mejora |
| Tipos | 32 | 28 | = |

## Payments

| Métrica | Antes | Después | Resultado |
|---|---|---|---|
| Violaciones de SDD 10.3.2 | 0 | 0 | = |
| Ciclos entre paquetes | 1 | 0 | mejora |
| Ciclos entre tipos | 0 | 0 | = |
| Tipos de más de 250 líneas | 0 | 0 | = |
| Fan-out máximo¹ | 12 | 11 | mejora |
| Dependencias entre paquetes | 41 | 37 | mejora |
| Cohesión relacional promedio (H) | 0.78 | 0.77 | empeora |
| Tipos | 84 | 77 | = |

## Communication

Sin el refactor de SCRUM-656 (pendiente). El cambio sale de adoptar `quickpatch-shared-dotnet` (ADR-020, SCRUM-657): 2 tipos transversales menos; el resto de las métricas no se mueve.

| Métrica | Antes | Después | Resultado |
|---|---|---|---|
| Violaciones de SDD 10.3.2 | 0 | 0 | = |
| Ciclos entre paquetes | 0 | 0 | = |
| Ciclos entre tipos | 1 | 1 | = |
| Tipos de más de 250 líneas | 0 | 0 | = |
| Fan-out máximo¹ | 10 | 10 | = |
| Dependencias entre paquetes | 44 | 44 | = |
| Cohesión relacional promedio (H) | 0.83 | 0.83 | = |
| Tipos | 77 | 75 | = |
