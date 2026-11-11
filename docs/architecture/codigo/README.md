# Dependencias desde el código — antes y despues del refactor

Comparación generada el 2026-11-11 con `python tools/arquitectura/comparar.py`, a partir de [`antes/`](antes/README.md) y [`despues/`](despues/README.md). Las dos mediciones usan la misma herramienta y la misma configuración (`tools/arquitectura/generar.py`, SCRUM-681).

## Resumen

| Servicio | Commit antes | Commit después | Violaciones | Ciclos paquetes | Tipos > 250 líneas | Fan-out máx.¹ | Cohesión H |
|---|---|---|---|---|---|---|---|
| Identity (sin refactor integrado) | `abffadb` | `abffadb` | 11 → 11 | 1 → 1 | 2 → 2 | 80 → 80 | 0.81 → 0.81 |
| Catalog | `b7c38cb` | `44373e3` | 0 → 0 | 0 → 0 | 0 → 0 | 15 → 15 | 0.85 → 0.86 |
| ServiceRequest | `394a1e8` | `ebd07d8` | 0 → 0 | 0 → 0 | 2 → 1 | 31 → 22 | 0.79 → 0.78 |
| Matching | `3fade78` | `8e6450c` | 0 → 0 | 1 → 0 | 0 → 0 | 10 → 13 | 0.85 → 0.75 |
| Ranking | `867716d` | `19d7908` | 0 → 0 | 0 → 0 | 0 → 0 | 10 → 10 | 0.79 → 0.81 |
| Payments | `4435eac` | `cf3af88` | 0 → 0 | 1 → 0 | 0 → 0 | 12 → 12 | 0.78 → 0.78 |
| Communication (sin refactor integrado) | `120623a` | `120623a` | 0 → 0 | 0 → 0 | 0 → 0 | 10 → 10 | 0.83 → 0.83 |

1. Sin las raíces de composición (`Program` y `DependencyInjection`).

## Identity

Mismo commit en las dos mediciones: el refactor de este servicio todavía no está en `develop`.

## Catalog

| Métrica | Antes | Después | Resultado |
|---|---|---|---|
| Violaciones de SDD 10.3.2 | 0 | 0 | = |
| Ciclos entre paquetes | 0 | 0 | = |
| Ciclos entre tipos | 0 | 0 | = |
| Tipos de más de 250 líneas | 0 | 0 | = |
| Fan-out máximo¹ | 15 | 15 | = |
| Dependencias entre paquetes | 26 | 26 | = |
| Cohesión relacional promedio (H) | 0.85 | 0.86 | mejora |
| Tipos | 42 | 43 | = |

## ServiceRequest

| Métrica | Antes | Después | Resultado |
|---|---|---|---|
| Violaciones de SDD 10.3.2 | 0 | 0 | = |
| Ciclos entre paquetes | 0 | 0 | = |
| Ciclos entre tipos | 0 | 0 | = |
| Tipos de más de 250 líneas | 2 | 1 | mejora |
| Fan-out máximo¹ | 31 | 22 | mejora |
| Dependencias entre paquetes | 111 | 111 | = |
| Cohesión relacional promedio (H) | 0.79 | 0.78 | empeora |
| Tipos | 211 | 217 | = |

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
| Dependencias entre paquetes | 19 | 19 | = |
| Cohesión relacional promedio (H) | 0.79 | 0.81 | mejora |
| Tipos | 32 | 33 | = |

## Payments

| Métrica | Antes | Después | Resultado |
|---|---|---|---|
| Violaciones de SDD 10.3.2 | 0 | 0 | = |
| Ciclos entre paquetes | 1 | 0 | mejora |
| Ciclos entre tipos | 0 | 0 | = |
| Tipos de más de 250 líneas | 0 | 0 | = |
| Fan-out máximo¹ | 12 | 12 | = |
| Dependencias entre paquetes | 41 | 39 | mejora |
| Cohesión relacional promedio (H) | 0.78 | 0.78 | = |
| Tipos | 84 | 84 | = |

## Communication

Mismo commit en las dos mediciones: el refactor de este servicio todavía no está en `develop`.
