# Registro de discrepancias de cifras de QA (SCRUM-664, SCRUM-695, SCRUM-701)

**Fecha:** 12 de noviembre de 2026, sobre `develop` (`ed3310d`)
**Responsable:** Katherine Bravo (`ka.bravo@javeriana.edu.co`), QA Lead
**Fuentes únicas:**
- [`indicadores-funcionales.md`](indicadores-funcionales.md) (SCRUM-700): 33 RF y los cuatro indicadores.
- [`matriz-escenarios-calidad-52.md`](matriz-escenarios-calidad-52.md) (SCRUM-664): 52 escenarios.
- [`cifras-canonicas.md`](../architecture/cifras-canonicas.md) (SCRUM-691): el resto de cifras del proyecto.

**Verificación:** `python scripts/calcular_indicadores_qa.py --verificar` busca en `docs/testing` las cifras retiradas. Si alguna aparece sin decir que es histórica, falla. Con este PR da 0 hallazgos.

## 1. Cifras vigentes

| Dato | Valor al 12-nov-2026 | Fuente |
|---|---|---|
| Requisitos funcionales definidos | 33 | SRS v5.6; `indicadores-funcionales.md` |
| RF implementados, verificados en QA y aceptados | 33, 33 y 33 (100 %). RF-10 con observaciones, y RF-22 y RF-23 con la pasarela simulada | `indicadores-funcionales.md` |
| Extensiones fuera del SRS | 4 (EXT-01 a EXT-04), todas aceptadas, fuera del denominador | `indicadores-funcionales.md`, sección 4 |
| Escenarios de calidad | 52: 35 Cumple, 8 Parcial, 3 No cumple y 6 No medido, para un 75,00 % | `matriz-escenarios-calidad-52.md` |
| Avance del producto | 92,50 % (0,7 × 100 % + 0,3 × 75,00 %) | `indicadores-funcionales.md`, sección 5 |
| k6 con 150 VU (run 41940280403) | p95 de 1.183 ms, métrica del umbral `test_type` | `tests/performance/evidencias/k6-stress-150vu-qa-2026-11-04-run-41940280403.json` |
| k6 con 50 VU (run 41940280403) | p95 de 88 ms al crear solicitud y de 32 ms en catálogo | `tests/performance/evidencias/k6-load-50vu-qa-2026-11-04-run-41940280403.json` |

## 2. Discrepancias corregidas en este PR

| # | Documento | Dato | Valor encontrado | Valor corregido | Motivo |
|---|---|---|---|---|---|
| 1 | `informe-pruebas-sprint5.md`, secciones 1.1 y 1.3 | Funcionalidades | 37 de 37 | 33 de 33 RF, más 4 extensiones aparte | El 37 eran los 33 RF más EXT-01 a EXT-04 (SCRUM-700) |
| 2 | `informe-pruebas-sprint5.md`, sección 1.3 | Escenarios | 73,08 % (34, 8, 4 y 6) | 75,00 % (35, 8, 3 y 6) | AC7-E5 cumple desde el 11-nov (SCRUM-657, PR #296) |
| 3 | `informe-pruebas-sprint5.md`, sección 1.3 | Avance | 91,92 % | 92,50 % | Sale de la fila 2 |
| 4 | `informe-pruebas-sprint5.md`, dictamen y recomendaciones 3 y 5 | Acta de UAT | Pendiente de firma | Firmada y en `develop` (PR #272) | El PR #272 se fusionó el 11-nov |
| 5 | `estadisticas-pruebas-sprint5.md`, sección 5, y `scripts/generar_estadisticas_qa.py` | Avance, funcionalidades y escenarios | 91,92 %, 37 de 37 y 73,08 %, escritos a mano en el script | Calculados con `calcular_indicadores_qa.py` | El documento decía «cero cifras escritas a mano», pero estas tres sí lo estaban |
| 6 | `estadisticas-pruebas-sprint5.md`, sección 3 | p95 de k6 | 79,66 ms con 50 VU y 1.105,96 ms con 150 VU | 88,16 ms y 1.183,24 ms | El script usaba el p95 de todas las peticiones. El informe y el Documento de Infraestructura usan la métrica del umbral, que ahora usa también el script |
| 7 | `matriz-escenarios-calidad-52.md`, AC1-E2 | Valor medido | «Verificado en 28 RFs de 33» y «Falta firmar el acta» | 24 de 24 RF Alta aceptados, 33 de 33 verificados, acta en el PR #272 | Estado al 12-nov (SCRUM-700) |
| 8 | `matriz-escenarios-calidad-52.md`, sección 3 | Cambios del 11-nov | No estaban registrados | Párrafo nuevo: AC7-E5 pasa a Cumple, y el porcentaje va de 73,08 % a 75,00 % | Trazabilidad del cambio |
| 9 | `matriz-funcionalidades-srs-v5.md` (versión 3.0, 26-oct) | Estado de los RF | 26 aprobados, 3 con observaciones y 4 sin probar (RF-12, RF-17, RF-21 y RF-25) | 33 verificados, RF-10 con observaciones | Evidencias del 4 y 5 de noviembre (versión 4.0) |
| 10 | `matriz-funcionalidades-srs-v5.md` | Extensiones y pasarela | Faltaba EXT-04; RF-23 no estaba marcado como simulado | Se agrega EXT-04 y RF-23 queda como «Implementado (mock)» | Igual que el Informe UAT de la PO |
| 11 | `matriz-funcionalidades-srs-v5.md`, RF-26 | Pruebas de CI | 1.032 pruebas | 1.525 pruebas (SCRUM-602) | Es la misma cifra del informe y de las estadísticas |
| 12 | `TD.md`, título y sección 1 | Versión | «TD V3.0», con la tabla en 3.2 | TD V3.3 | El título y la tabla no coincidían |
| 13 | `TD.md`, alcance | Repositorios | 12 de componentes más el principal | 13 de componentes más el principal (14) | `cifras-canonicas.md` (ADR-020, del 11-nov) |
| 14 | `TD.md`, sección 7.1.2 | Escenarios automatizados | 38; AC9-E2 y AC9-E7 «pendientes de diseño» | 42 (se suman AC4-E5, AC4-E7, AC9-E2 y AC9-E7), con el estado medido de la matriz | Hay colecciones y pruebas que ya los miden |
| 15 | `TD.md`, sección 10.1 | RF y escenarios | 32 RF (SRS v3.3) y 37 escenarios | Queda marcada como corte histórico del Sprint 3 | Era la cifra vigente el 3-oct |
| 16 | `avance-real-sprint5.md`, `inventario-funcionalidades-por-usuario.md` y `guion-demostracion-sprint5.md` | Avance | 65,4 % de 78 funcionalidades | Quedan marcados como corte histórico del 27-oct | Las 78 se quedan como desglose por rol (SCRUM-700) |

## 3. Cifras retiradas

| Cifra | Dónde apareció | Por qué se retira |
|---|---|---|
| 94,52 % de avance, 81,73 % de escenarios y «39 escenarios aprobados» (39, 7, 4 y 2) | Segunda versión del Excel de la PO (5-nov) y presentación del Sprint 5 | Contaba como Cumple AC4-E3, AC4-E4, AC4-E6, AC4-E8 y AC4-E9 sin medición ni evidencia. La matriz solo acepta Cumple con medición, fecha y evidencia |
| 91,92 %, 73,08 % y «37 de 37» | Informe 1.2, estadísticas 2.2, acta de UAT | Son el corte del 5-nov. El acta firmada (PR #272) se conserva como registro histórico y **no se modifica** |
| «36 aceptadas» y 94 % | Presentación del Sprint 5 | No corresponden a ninguna fuente (`cifras-canonicas.md`) |

## 4. Pendientes fuera de este PR

| # | Qué | Valor | Quién |
|---|---|---|---|
| 1 | Defectos: el informe y las estadísticas cuentan 19, y la hoja Defectos del Informe UAT de la PO cuenta 24 | Faltan HAL-S5-01, HAL-S5-02 y DEF-INT-01 a DEF-INT-03 en `registro-defectos-sprint4-sprint5.md` y en `Matriz_UAT_Avance_QuickPatch.xlsx`. DEF-INT-02 debería quedar Resuelto con quickpatch-mobile#58 | QA (Katherine), en un PR aparte |
| 2 | `cifras-canonicas.md` todavía dice «unidad por decidir (SCRUM-700)» y «la fuente única la cierra SCRUM-664» | Apuntar a `indicadores-funcionales.md` y a la matriz de 52: 33 RF, 33/33/33/33 y 75,00 % | Arquitectura (Juan Diego, SCRUM-691) |
| 3 | `docs/governance/cierre-proyecto.md` y `presentacion-final-guion.md` esperan las cifras de SCRUM-700 y SCRUM-664 | 33/33/33/33, 92,50 % y 35/8/3/6 | Juan Diego (SCRUM-703 y SCRUM-706) |
| 4 | Las gráficas PNG de `docs/testing/img/` no se regeneran en este PR | Solo las tocan las fuentes del sistema; las cifras no cambian | — |
