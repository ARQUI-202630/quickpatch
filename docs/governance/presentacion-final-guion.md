# Guion de la presentación final de QUICKPATCH

**Tarea:** SCRUM-706 (historia SCRUM-705). El diseño se arma en Canva; este guion fija el orden, el mensaje de cada lámina y **las únicas cifras permitidas**, todas tomadas de `docs/architecture/cifras-canonicas.md` (SCRUM-691). Si una cifra no está ahí, no va en la presentación.

**Estructura pedida por el profesor:** necesidad → problema → objetivo → alcance → solución → arquitectura → implementación → QA y UAT → resultados → cierre. No se empieza por la arquitectura.

## Marcas de estado (SCRUM-707)

Cada servicio, sistema o elemento de un diagrama lleva una de estas marcas, con la misma leyenda y los mismos colores en todas las láminas:

| Marca | Significa | Elementos al 12 de noviembre |
|---|---|---|
| **IMPLEMENTADO** | Hay código en `develop` y corre en QA y en producción | Identity, Catalog, ServiceRequest, Matching, Ranking, Payments, Communication, API Gateway, panel web, app móvil |
| **PLANEADO** | Diseñado, sin código | Actors (esqueleto), receptor de webhooks del PSP, regla de 4 horas (AC9-E3) |
| **EXTERNO** | Sistema de un tercero | Pasarela de pagos PCI-DSS certificada (sin contratar), GitHub |
| **MOCK** | Reemplazo simulado de un externo | Pasarela simulada (`SimulatedPaymentProvider`, ADR-009 modificado) |

Fuente: `docs/architecture/matriz-modelado-vs-real.md` (SCRUM-697).

Los 27 diagramas C4 exportados (`docs/architecture/diagrams/c4/`) llevan las mismas marcas con su leyenda pegada a la imagen (SCRUM-707): IMPLEMENTADO con borde verde, PLANEADO con borde gris discontinuo, EXTERNO con fondo gris y MOCK con fondo naranja y borde de puntos. En las láminas se usan esos mismos colores.

## Láminas

| # | Lámina | Mensaje | Cifras y evidencia permitidas |
|---|---|---|---|
| 1 | Portada | QUICKPATCH: técnicos disponibles y cercanos para hogares y empresas en Bogotá | — |
| 2 | Necesidad | Conseguir un técnico confiable depende de conocidos y directorios; no hay precio previo, seguimiento ni prueba del trabajo | `docs/governance/cierre-proyecto.md` §1 |
| 3 | Problema | Además, las empresas que ofrecen técnicos no tienen dónde operar sin mezclar sus datos con los de otras | Cierre §1 |
| 4 | Objetivo | MVP multi-tenant con asignación automática, cotización previa, seguimiento, evidencia fotográfica obligatoria, pago con comprobante y calificación | SRS 2.2 (8 funciones) |
| 5 | Alcance | 6 roles (4 en la app y 2 en el panel), 33 RF y 14 RNF, Bogotá D.C., pago con pasarela simulada; lo que quedó fuera (FA1 a FA3, R1) | Cifras canónicas: «Producto y alcance» |
| 6 | Solución, recorrido del cliente | Solicitar → técnico asignado → acepta → chat → cotización → acepta → ejecución con evidencia → pago → comprobante → calificación → reputación | Humo del flujo crítico en QA (30-oct) |
| 7 | Contexto (C4 nivel 1) | Los 6 roles agrupados por canal y la pasarela como externo | Figura `C4-02-Contexto` (SCRUM-689) |
| 8 | Contenedores (C4 nivel 2) | 8 microservicios definidos, **7 IMPLEMENTADOS** y Actors **PLANEADO**; 20 eventos de Kafka; 8 bases lógicas | `C4-03a-Contenedores-Sincrono` y `C4-03b-Contenedores-Eventos` (una lámina cada una si hace falta); cifras canónicas |
| 9 | Arquitectura interna | Cuatro capas con reglas verificadas en el CI de cada servicio (SDD 10.3.2) | — |
| 10 | Refactor del cierre | Antes y después medidos con la misma herramienta (12-nov): de 3 servicios con ciclos entre paquetes a ninguno (Identity, Matching y Payments); fan-out máximo de ServiceRequest de 31 a 21. Mostrar también lo que empeoró (fan-out de Matching de 10 a 13) y lo pendiente (Identity: 11 violaciones, SCRUM-650) | `docs/architecture/codigo/README.md` |
| 11 | Diagrama de código | Generado desde el código, no dibujado a mano | `tools/arquitectura/`, SDD 7.3 |
| 12 | Dinámico: creación y asignación | Pasos numerados con origen, destino y evento: solicitud, búsqueda del técnico, oferta y aceptación | `C4-05-Dinamico-CreacionAsignacion` (23 pasos), SDD 8.3 (SCRUM-684) |
| 13 | Despliegue | QA y producción separados (7 VM, 2 ambientes). El panel se entrega desde el Nginx y se ejecuta en el navegador; la app corre en el dispositivo | `C4-06-*` (SCRUM-674) |
| 14 | QA → producción | A producción solo llega lo probado en QA; un token de QA es rechazado por producción (401) | `tests/e2e/evidencias/separacion-qa-produccion-2026-11-10.txt` |
| 15 | Escenarios de calidad | 52 escenarios: Cumple, Parcial, No cumple y No medido, con la cifra final de SCRUM-664; los que no cumplen, con su motivo | Matriz de 52 escenarios |
| 16 | Funcionalidades | Definidas, implementadas, verificadas en QA y aceptadas: las cuatro cifras de SCRUM-700. **No usar** «37/37», «94 %» ni «91,92 %» | SCRUM-700 |
| 17 | UAT | Escenarios por rol y resultado de la UAT de cierre | SCRUM-658 |
| 18 | Lo que no se construyó | Pasarela real, Actors y AC9-E3, cada uno con su motivo. Lo que sí se cerró al final: el código transversal compartido (AC7-E5, ADR-020) | Cierre §5 y §6 |
| 19 | Riesgos y restricciones | R3, R5, R9, R10 y R11; riesgos aceptados del SAD 6.2 | Cierre §7 |
| 20 | Cierre | Qué se logró y qué lo demuestra | Cierre §8, con la revisión de la PO (SCRUM-704) |

## Preguntas de control para el ensayo (SCRUM-708)

Todo el equipo debe responderlas igual, con estas respuestas:

| Pregunta | Respuesta |
|---|---|
| ¿Cuántos usuarios o roles hay? | 6: Cliente, Empresa, Técnico y Proveedor (app); Admin del tenant y Admin de plataforma (panel) |
| ¿Cuántas funcionalidades? | 33 requisitos funcionales en el SRS; avance según las cuatro cifras de SCRUM-700 |
| ¿Cuántos escenarios? | 52, con el estado final de SCRUM-664 |
| ¿Cuántos servicios? | 8 definidos; 7 implementados; Actors planeado |
| ¿Cuáles están en producción? | Los 7 con código, el panel y la app, desde el 4 de noviembre. QA va adelante en los 7 servicios y en el panel (refactor del Sprint 6 y código compartido de ADR-020); llegan a producción solo por `release/*` → `main` (matriz de lo modelado frente a lo real) |
| ¿Cuántos repositorios? | 14: 13 de componentes (el último, `quickpatch-shared-dotnet`, por ADR-020) y el principal |
| ¿Cuántos topics? | 20 |
| ¿Qué quedó pendiente? | Pasarela real, Actors y AC9-E3 |
| ¿Cuántos escenarios cumplen? | 35 Cumple, 8 Parcial, 3 No cumple y 6 No medido, hasta que SCRUM-664 publique la cifra final |
| ¿Cuántos diagramas C4 hay? | 27 vistas del modelo de Structurizr, todas con la leyenda de estados, más 2 diagramas de código (C4-07) |
| ¿Cuál fue el resultado? | El de la conclusión del documento de cierre, aprobada por la PO |
