# Medición de acoplamiento y cohesión antes y después del refactor (SCRUM-649)

**Código del Documento:** `MET-QA-ACOPL-2026-11-13`  
**Versión:** `1.0`  
**Fecha:** 13 de noviembre de 2026  
**Responsable:** Katherine Bravo (`ka.bravo@javeriana.edu.co`) — QA Lead  
**Trazabilidad Jira:** Subtarea `SCRUM-649` de la historia `SCRUM-647` (refactor interno de los microservicios) | Escenarios `AC7-E2` y `AC7-E5` de la matriz de 52  
**Fuentes:** `docs/architecture/codigo/` (medición de Arquitectura con `tools/arquitectura/generar.py`, SCRUM-680 a SCRUM-683) y el historial de `develop` de los repositorios de servicios

---

## 1. Qué pide la tarea y en qué estado queda

| Criterio de aceptación de SCRUM-649 | Estado | Dónde se ve |
|---|---|---|
| Línea base «antes» tomada sobre `develop` antes del primer PR de refactor | **Cumple.** En los 7 servicios el commit «antes» es el último de `develop` antes del primer PR de refactor, y ningún PR de refactor del cierre entró antes | Sección 2 |
| Medición «después» con la misma herramienta y el mismo procedimiento | **Cumple.** Las dos fases salen de `generar.py` con la misma configuración, y `comparar.py` vuelve a producir la misma tabla | Secciones 3 y 5 |
| Tabla comparativa por servicio en `docs/testing` | **Cumple** con este documento | Sección 3 |
| El procedimiento se puede repetir con un comando | **Cumple.** Un comando por paso, en la sección 5 | Sección 5 |
| Volver a medir AC7-E2 y AC7-E5 después del refactor | **Hecho.** AC7-E5 sigue en Cumple (11-nov). AC7-E2 sigue en No cumple con todas las definiciones del periodo completo | Sección 4 |

La herramienta, las métricas y sus límites están en [`tools/arquitectura/README.md`](../../tools/arquitectura/README.md). QA no cambió la herramienta ni sus resultados: este documento verifica cómo se tomaron las dos mediciones y resume lo que muestran.

---

## 2. Verificación de la línea base

Comando: `python tests/mantenibilidad/verificar_linea_base.py`. Lee los commits de cada `metricas.json` y los compara con el historial de `develop` de cada servicio. Salida del 13-nov:

| Servicio | «Antes» | «Después» | PR entre las dos mediciones | Resultado |
|---|---|---|---|---|
| Identity | `abffadb` (5-nov) | `fe22c14` | #38 (funcionalidad SCRUM-642), #39 y #40 (código compartido, SCRUM-657). **No tiene su refactor (SCRUM-650)** | OK |
| Catalog | `b7c38cb` (4-nov) | `6345700` | #19 (refactor, SCRUM-651), #20 y #21 (SCRUM-657) | OK |
| ServiceRequest | `394a1e8` (4-nov) | `45c0653` | #44 (refactor, SCRUM-652), #45 y #46 (SCRUM-657) | OK |
| Matching | `3fade78` (4-nov) | `8e6450c` | #24 (refactor, SCRUM-653) | OK |
| Ranking | `867716d` (4-nov) | `1679652` | #13 (refactor, SCRUM-654), #14 y #15 (SCRUM-657) | OK |
| Payments | `4435eac` (4-nov) | `6a2b893` | #19 (refactor, SCRUM-655), #20 y #21 (SCRUM-657) | OK |
| Communication | `120623a` (4-nov) | `fe01c13` | #25 y #26 (SCRUM-657). **No tiene su refactor (SCRUM-656)** | OK |

En los 7 servicios, «antes» es ancestro de «después» y ningún PR de SCRUM-650 a SCRUM-657 entró antes de «antes». «Después» sigue siendo la punta de `develop`: no hay PR nuevos después de la medición. Identity es el único con un cambio de funcionalidad entre las dos fases (#38).

---

## 3. Tabla comparativa por servicio

Valores de `docs/architecture/codigo/antes/` y `docs/architecture/codigo/despues/`. La tabla completa, con todas las métricas, está en [`docs/architecture/codigo/README.md`](../architecture/codigo/README.md).

| Servicio | Violaciones de SDD 10.3.2 | Ciclos entre paquetes | Tipos de más de 250 líneas | Fan-out máximo¹ | Dependencias entre paquetes | Cohesión H |
|---|---|---|---|---|---|---|
| Identity² | 11 → 11 | 1 → **0** | 2 → 2 | 80 → 79 | 93 → 91 | 0.81 → 0.79 |
| Catalog | 0 → 0 | 0 → 0 | 0 → 0 | 15 → 14 | 26 → 22 | 0.85 → 0.86 |
| ServiceRequest | 0 → 0 | 0 → 0 | 2 → **1** | 31 → **21** | 111 → 109 | 0.79 → 0.77 |
| Matching | 0 → 0 | 1 → **0** | 0 → 0 | 10 → 13 | 34 → 36 | 0.85 → 0.75 |
| Ranking | 0 → 0 | 0 → 0 | 0 → 0 | 10 → 10 | 19 → 17 | 0.79 → **0.89** |
| Payments | 0 → 0 | 1 → **0** | 0 → 0 | 12 → 11 | 41 → 37 | 0.78 → 0.77 |
| Communication² | 0 → 0 | 0 → 0 | 0 → 0 | 10 → 10 | 44 → 44 | 0.83 → 0.83 |

1. Sin las raíces de composición (`Program` y `DependencyInjection`).
2. Sin su refactor integrado. El cambio sale de adoptar `quickpatch-shared-dotnet` (ADR-020).

**Lectura de QA:**

- **Mejora:** desaparecen los 3 ciclos entre paquetes (Identity, Matching y Payments). El fan-out máximo de ServiceRequest baja de 31 a 21 y queda un tipo grande menos. Las dependencias entre paquetes bajan en 5 de 7 servicios.
- **Empeora:** la cohesión H baja en Identity, ServiceRequest, Matching y Payments. En Matching también sube el fan-out máximo (10 → 13) y las dependencias entre paquetes (34 → 36): al separar los puertos por responsabilidad hay más tipos pequeños que se usan entre sí.
- **Sigue igual:** las 11 violaciones de capas de Identity, porque su refactor (SCRUM-650) no está integrado. Ninguno de los otros 6 servicios tiene violaciones antes ni después.

---

## 4. Escenarios AC7-E2 y AC7-E5 después del refactor

### 4.1 AC7-E5: reutilización de la lógica transversal

Sigue en **Cumple**. La medición del 11-nov ([`ac7-e5-remedicion-2026-11-11.md`](../../tests/e2e/evidencias/ac7-e5-remedicion-2026-11-11.md)) muestra 0 copias en .NET con `quickpatch-shared-dotnet` v0.2.1. Desde esa fecha no entró ningún PR nuevo en los servicios (sección 2), así que la medición sigue vigente.

### 4.2 AC7-E2: acoplamiento entre módulos (meta: el 80 % o más de los cambios toca un solo servicio)

Comando: `python tests/mantenibilidad/medir_ac7_e2.py --desde 2026-10-24` (y `--por-historia`). Usa el método de la medición del 5-nov ([`ac7-mantenibilidad-e2-e3-e5-medicion-2026-11-05.md`](../../tests/e2e/evidencias/ac7-mantenibilidad-e2-e3-e5-medicion-2026-11-05.md)): cuenta en cuántos repositorios de servicios tiene PR mezclados en `develop` cada cambio, sin las promociones ni los back-merge. El 5-nov la definición de «cambio» la debía fijar Arquitectura, y no quedó registrada en SCRUM-669. Por eso el script mide con las dos unidades posibles.

**Unidad: número de SCRUM del PR (normalmente la subtarea)**

| Periodo | Cambios | Un servicio | Dos | Tres o más | Sin la subida de contratos | Solo `feat` y `fix` |
|---|---|---|---|---|---|---|
| 24-oct a 5-nov (antes del refactor) | 19 | 14 (73,7 %) | 3 | 2 | 77,8 % (18) | 84,6 % (13) |
| 6-nov a 13-nov (refactor) | 8 | 7 (87,5 %) | 0 | 1 | 87,5 % (8) | 100 % (1) |
| **24-oct a 13-nov (todo)** | **27** | **21 (77,8 %)** | 3 | 3 | **80,8 %** (26) | **85,7 %** (14) |

**Unidad: historia de Jira (las subtareas se agrupan en su historia, con `tests/mantenibilidad/ac7-e2-historias.json`)**

| Periodo | Cambios | Un servicio | Dos | Tres o más | Sin la subida de contratos | Solo `feat` y `fix` |
|---|---|---|---|---|---|---|
| 24-oct a 5-nov | 13 | 7 (53,8 %) | 2 | 4 | 58,3 % (12) | 75,0 % (8) |
| 6-nov a 13-nov | 3 | 2 (66,7 %) | 0 | 1 | 66,7 % (3) | 100 % (1) |
| **24-oct a 13-nov (todo)** | **16** | **9 (56,2 %)** | 2 | 5 | **60,0 %** (15) | **77,8 %** (9) |

Los cambios que tocan más de un servicio en todo el periodo son SCRUM-547 (subida mecánica del submódulo de contratos, 6 servicios), SCRUM-588 (convención de paquetes, 3), SCRUM-657 (código compartido de ADR-020, 6), SCRUM-515 (sondas, 2), SCRUM-118 (pago de la empresa, 2) y SCRUM-498 (reputación en Identity y Ranking, 2). Al agrupar por historia se juntan además SCRUM-32 (calificación: Identity, Ranking y ServiceRequest), SCRUM-348 (tenant inactivo: Identity y ServiceRequest) y SCRUM-512 (despliegue del Sprint 5: 3 servicios).

**Resultado: AC7-E2 sigue en No cumple.** Con la unidad más favorable (subtarea, sin la subida de contratos) llega al 80,8 %, pero con la unidad «todos los cambios» queda en 77,8 % y por historia en 56,2 %. No se cambia el estado de la matriz mientras Arquitectura no fije la unidad. Los números del periodo del refactor (87,5 %) no prueban menos acoplamiento: cada subtarea de refactor es de un solo servicio por diseño, y la muestra es de 8 cambios.

**Diferencia con la medición del 5-nov:** ese día se contaron 17 cambios a mano (64,7 %). El script cuenta 19 en el mismo periodo por subtarea, o 13 por historia, porque el conteo del 5-nov agrupó algunas subtareas en su historia (SCRUM-32 y SCRUM-348) y otras no. El script deja la regla escrita y aplica una sola a la vez.

---

## 5. Cómo se repite

Desde la raíz del superproyecto:

```bash
# 1. Medición de Arquitectura (requiere .NET SDK 10, JDK 17+ con jdeps y Maven)
python tools/arquitectura/generar.py --fase antes --ref <commit antes> --servicios <servicio>
python tools/arquitectura/generar.py --fase despues --servicios <servicio>
python tools/arquitectura/comparar.py          # vuelve a escribir docs/architecture/codigo/README.md

# 2. Verificación de QA (solo git y Python; solo lee)
python tests/mantenibilidad/verificar_linea_base.py
python tests/mantenibilidad/medir_ac7_e2.py --desde 2026-10-24
python tests/mantenibilidad/medir_ac7_e2.py --desde 2026-10-24 --por-historia
```

**Qué verificó QA el 13-nov:**

- `comparar.py` sobre los `metricas.json` del repositorio da la misma tabla de `docs/architecture/codigo/README.md`; solo cambia la fecha de generación.
- `verificar_linea_base.py` da OK en los 7 servicios (sección 2).
- Los 14 commits de los `metricas.json` existen en los repositorios de servicios.
- **Falta volver a correr `generar.py` desde cero en una máquina de QA.** El 13-nov se intentó en dos equipos y no se pudo compilar: en uno no hay .NET SDK 10 ni Maven, y en el otro Maven no encontró las dependencias de Spring Security que usa Matching. Ninguna cifra de la sección 3 sale de esos intentos. Cuando haya un equipo con las herramientas, se corre el paso 1 en una carpeta aparte (`--salida`) y se compara el bloque `resumen` de cada `metricas.json`.

---

## 6. Pendientes

| # | Qué | Quién |
|---|---|---|
| 1 | Refactor de Identity (SCRUM-650) y de Communication (SCRUM-656). Cuando se integren, se repite la fase «después» de esos dos servicios y este documento | Backend; QA repite la verificación |
| 2 | Definir la unidad de «cambio» de AC7-E2 (subtarea o historia, con o sin la subida de contratos) | Arquitectura (Juan Diego) |
| 3 | Bajar las 11 violaciones de capas de Identity | Backend (SCRUM-650) |
| 4 | Volver a correr `generar.py` desde cero en un equipo con .NET SDK 10 y Maven, y comparar con los `metricas.json` del repositorio | QA, con el equipo que tenga las herramientas |
