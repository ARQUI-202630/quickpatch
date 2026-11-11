# Dependencias desde el código — antes

Generado el 2026-11-10 con `python tools/arquitectura/generar.py --fase antes` sobre `origin/develop` de cada servicio. Método y decisión: [`tools/arquitectura/README.md`](../../../../tools/arquitectura/README.md). Reglas: SDD 10.3.2.

| Servicio | Commit | Tipos | Paquetes | Dep. entre tipos | Dep. entre paquetes | Ciclos paquetes | Ciclos tipos (mayor) | Violaciones | Tipos > 250 líneas | Fan-out máx. | Cohesión H prom. |
|---|---|---|---|---|---|---|---|---|---|---|---|
| [Identity](identity/README.md) | `abffadb` | 186 | 24 | 599 | 93 | 1 | 0 (0) | 11 | 2 | 80 | 0.81 |
| [Catalog](catalog/README.md) | `b7c38cb` | 42 | 14 | 81 | 26 | 0 | 0 (0) | 0 | 0 | 15 | 0.85 |
| [ServiceRequest](service-request/README.md) | `394a1e8` | 211 | 31 | 596 | 111 | 0 | 0 (0) | 0 | 2 | 31 | 0.79 |
| [Matching](matching/README.md) | `3fade78` | 45 | 13 | 111 | 34 | 1 | 0 (0) | 0 | 0 | 10 | 0.85 |
| [Ranking](ranking/README.md) | `867716d` | 32 | 11 | 61 | 19 | 0 | 0 (0) | 0 | 0 | 10 | 0.79 |
| [Payments](payments/README.md) | `4435eac` | 84 | 17 | 214 | 41 | 1 | 0 (0) | 0 | 0 | 12 | 0.78 |
| [Communication](communication/README.md) | `120623a` | 77 | 17 | 181 | 44 | 0 | 1 (2) | 0 | 0 | 10 | 0.83 |

1. Sin las raíces de composición (`Program` y `DependencyInjection`), que por diseño conocen todo el servicio.

Actors no se analiza: es un esqueleto sin lógica (solo `Program.cs`).
