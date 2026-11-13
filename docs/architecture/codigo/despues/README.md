# Dependencias desde el código — despues

Generado el 2026-11-12 con `python tools/arquitectura/generar.py --fase despues` sobre `origin/develop` de cada servicio. Método y decisión: [`tools/arquitectura/README.md`](../../../../tools/arquitectura/README.md). Reglas: SDD 10.3.2.

| Servicio | Commit | Tipos | Paquetes | Dep. entre tipos | Dep. entre paquetes | Ciclos paquetes | Ciclos tipos (mayor) | Violaciones | Tipos > 250 líneas | Fan-out máx. | Cohesión H prom. |
|---|---|---|---|---|---|---|---|---|---|---|---|
| [Identity](identity/README.md) | `fe22c14` | 182 | 24 | 589 | 91 | 0 | 0 (0) | 11 | 2 | 79 | 0.79 |
| [Catalog](catalog/README.md) | `6345700` | 38 | 13 | 73 | 22 | 0 | 0 (0) | 0 | 0 | 14 | 0.86 |
| [ServiceRequest](service-request/README.md) | `45c0653` | 211 | 31 | 601 | 109 | 0 | 0 (0) | 0 | 1 | 21 | 0.77 |
| [Matching](matching/README.md) | `8e6450c` | 49 | 14 | 123 | 36 | 0 | 0 (0) | 0 | 0 | 13 | 0.75 |
| [Ranking](ranking/README.md) | `1679652` | 28 | 11 | 54 | 17 | 0 | 0 (0) | 0 | 0 | 10 | 0.89 |
| [Payments](payments/README.md) | `6a2b893` | 77 | 17 | 198 | 37 | 0 | 0 (0) | 0 | 0 | 11 | 0.77 |
| [Communication](communication/README.md) | `fe01c13` | 75 | 17 | 176 | 44 | 0 | 1 (2) | 0 | 0 | 10 | 0.83 |

1. Sin las raíces de composición (`Program` y `DependencyInjection`), que por diseño conocen todo el servicio.

Actors no se analiza: es un esqueleto sin lógica (solo `Program.cs`).
