# Dependencias desde el código — despues

Generado el 2026-11-23 con `python tools/arquitectura/generar.py --fase despues` sobre `origin/develop` de cada servicio. Método y decisión: [`tools/arquitectura/README.md`](../../../../tools/arquitectura/README.md). Reglas: SDD 10.3.2.

| Servicio | Commit | Tipos | Paquetes | Dep. entre tipos | Dep. entre paquetes | Ciclos paquetes | Ciclos tipos (mayor) | Violaciones | Tipos > 250 líneas | Fan-out máx. | Cohesión H prom. |
|---|---|---|---|---|---|---|---|---|---|---|---|
| [Identity](identity/README.md) | `6631e7f` | 195 | 24 | 637 | 89 | 0 | 0 (0) | 0 | 0 | 29 | 0.79 |
| [Actors](actors/README.md) | `2759bd6` | 34 | 13 | 77 | 26 | 0 | 0 (0) | 0 | 0 | 11 | 0.88 |
| [Catalog](catalog/README.md) | `9c574e0` | 38 | 13 | 73 | 22 | 0 | 0 (0) | 0 | 0 | 14 | 0.86 |
| [ServiceRequest](service-request/README.md) | `04391e4` | 212 | 31 | 604 | 109 | 0 | 0 (0) | 0 | 1 | 21 | 0.77 |
| [Matching](matching/README.md) | `2816723` | 49 | 14 | 123 | 36 | 0 | 0 (0) | 0 | 0 | 13 | 0.75 |
| [Ranking](ranking/README.md) | `9e4b500` | 28 | 11 | 54 | 17 | 0 | 0 (0) | 0 | 0 | 10 | 0.89 |
| [Payments](payments/README.md) | `a665f4f` | 77 | 17 | 198 | 37 | 0 | 0 (0) | 0 | 0 | 11 | 0.77 |
| [Communication](communication/README.md) | `92f11ed` | 78 | 17 | 180 | 44 | 0 | 0 (0) | 0 | 0 | 10 | 0.83 |

1. Sin las raíces de composición (`Program` y `DependencyInjection`), que por diseño conocen todo el servicio.

Actors se analiza desde SCRUM-640; antes era un esqueleto sin lógica (solo `Program.cs`), así que no tiene línea base.
