# Dependencias desde el código — despues

Generado el 2026-11-11 con `python tools/arquitectura/generar.py --fase despues` sobre `origin/develop` de cada servicio. Método y decisión: [`tools/arquitectura/README.md`](../../../../tools/arquitectura/README.md). Reglas: SDD 10.3.2.

| Servicio | Commit | Tipos | Paquetes | Dep. entre tipos | Dep. entre paquetes | Ciclos paquetes | Ciclos tipos (mayor) | Violaciones | Tipos > 250 líneas | Fan-out máx. | Cohesión H prom. |
|---|---|---|---|---|---|---|---|---|---|---|---|
| [Identity](identity/README.md) | `abffadb` | 186 | 24 | 599 | 93 | 1 | 0 (0) | 11 | 2 | 80 | 0.81 |
| [Catalog](catalog/README.md) | `44373e3` | 43 | 14 | 84 | 26 | 0 | 0 (0) | 0 | 0 | 15 | 0.86 |
| [ServiceRequest](service-request/README.md) | `ebd07d8` | 217 | 31 | 618 | 111 | 0 | 0 (0) | 0 | 1 | 22 | 0.78 |
| [Matching](matching/README.md) | `8e6450c` | 49 | 14 | 123 | 36 | 0 | 0 (0) | 0 | 0 | 13 | 0.75 |
| [Ranking](ranking/README.md) | `19d7908` | 33 | 11 | 64 | 19 | 0 | 0 (0) | 0 | 0 | 10 | 0.81 |
| [Payments](payments/README.md) | `cf3af88` | 84 | 17 | 214 | 39 | 0 | 0 (0) | 0 | 0 | 12 | 0.78 |
| [Communication](communication/README.md) | `120623a` | 77 | 17 | 181 | 44 | 0 | 1 (2) | 0 | 0 | 10 | 0.83 |

1. Sin las raíces de composición (`Program` y `DependencyInjection`), que por diseño conocen todo el servicio.

Actors no se analiza: es un esqueleto sin lógica (solo `Program.cs`).
