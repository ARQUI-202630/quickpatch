# Revisión de la plantilla de presentaciones: redundancia y diagramas

Revisión de la presentación «QuickPatch Sprint 3 v4» (Canva, 47 láminas) para convertirla en una plantilla general de presentaciones. Es una recomendación: no cambia ningún diseño. Los datos propios del Sprint 3 (cifras, estados, evidencias de ese sprint) no se evaluaron; solo la estructura.

La numeración es la posición de la lámina en el diseño. No se vieron en imagen las láminas 1 a 3, 10 y 36 a 40 (portada, contenido, portadas de sección y capturas de evidencia). Todo lo demás se revisó con su texto y su miniatura.

## 1. Qué tipo de lámina es cada una

| Tipo | Láminas |
|---|---|
| Diagrama con texto de apoyo | 7 (BPMN), 16 (HLD), 17 (C4 Landscape), 18 (C4 Contexto), 19 (C4 Contenedores), 20 a 23 (C4 Componentes), 24 (C4 Código), 27 (Secuencia E2E), 30 (Deployment producción) |
| Tabla o matriz | 4, 6, 9, 11, 12, 13, 14, 15, 25, 26, 28, 29, 31, 32, 33, 41, 46 |
| Cadena de pasos | 42 (evidencia a decisión) |
| Cifras | 34 |
| Evidencia (capturas) | 35 a 39, 43 a 45 |
| Cierre | 47 |

## 2. Redundancia entre láminas

| Tema | Dónde se repite | Recomendación |
|---|---|---|
| Qué mejoró respecto al sprint anterior | 9 y 41 cumplen el mismo papel (ADR-021, ADR-022, Garage, atributos y escenarios, killers frente a fuera de alcance) | Dejar una sola lámina «antes y ahora» |
| Decisiones citadas dos o tres veces | ADR-021 en 9, 29 y 41; ADR-022 en 9, 29, 33 y 41 (y las 3 VM de QA en 31); Garage en 9, 28, 41 y 42 | Que cada ADR se explique en un solo lugar y los demás lo nombren sin volver a describirlo |
| Lista de documentos con versión | 11 y 46 (SRS, SAD, SDD, DD, Infraestructura, TD) | Una tabla con una columna de estado |
| Actores | 4 (necesidades), 6 (matriz), 16 (HLD), 17 y 18 (C4) | Dejar 4 y 6 como tablas; el dibujo de los actores lo da un solo diagrama |
| Canales web y móvil | 4 (columna Canal), 8, 16, 19, 22 y 23 | Borrar 8 (ya marcada «CREO QUE BORRAR»); queda dicho en 4 y en los diagramas |
| Cuatro niveles del mismo sistema | 16 (HLD), 17 (Landscape), 18 (Contexto), 19 (Contenedores) | Contexto está contenido en Landscape, y HLD y Contenedores muestran las mismas capas. Elegir el recorrido C4 y dejar el HLD solo si se necesita la vista por capas |
| Flujo de la solicitud | 7 (BPMN), 20, 21, 26 y 27 (nombres de eventos, «cotizaciones máx. 3», «técnico asignado») | El BPMN cuenta el negocio y la secuencia cuenta lo técnico; los nombres de eventos viven solo en 26 |
| Drivers, requisitos y calidad | 5, 12, 14 y 15 (D2 con RNF-06; D5 con RNF-10 y AC6; D8 con RNF-08) | Una sola cadena de trazabilidad en lugar de tres tablas |
| Killers y restricciones | 5, 13, 17, 41 y 47 (K9 sale en 13, 17 y 47) | Cada killer y restricción se define una vez; las otras láminas lo citan por código |
| Ambientes, compuertas y VMs | 13 (riesgos de las VMs), 30, 31, 32 y 33 | 31, 32 y 33 son un solo tema (ver la fila 5 del punto 3) |
| Aislamiento por tenant y outbox | RNF-10, AC6, AC6-E2, 25 y ADR-005; AC5-E4, AC5-E5, 24, ADR-007 | Mencionarlos con su código y mostrarlos una vez en un diagrama |
| Cifras de pruebas | 9, 11, 34 y 47 | Las cifras viven solo en la lámina de resultados |

Corrección a una revisión anterior: la lámina de estrategia de QA y compuertas es la 32, no la 33.

## 3. Láminas que se explicarían mejor con un diagrama

| # | Láminas actuales | Diagrama propuesto | Qué reemplaza | Prioridad |
|---|---|---|---|---|
| 1 | 14 y 15 | Árbol de utilidad: atributo, escenario, medida y validación | Dos tablas con las mismas siglas AC2, AC5 y AC6 | Alta |
| 2 | 26 | Mapa de eventos: productor, topic y consumidor | Las listas de eventos de 20, 21, 26 y 27 | Alta |
| 3 | 25 | Propiedad de datos: una base por servicio, referencias lógicas, outbox y eventos procesados | La tabla de tablas por servicio y la lista de reglas (el DD ya tiene la figura de base) | Alta |
| 4 | 31, 32 y 33 | Flujo de promoción entre ambientes: local, CI, QA y producción, con una compuerta entre cada par y las VM de cada ambiente | Tres tablas que se corresponden fila por fila | Alta |
| 5 | 13 | Los riesgos marcados sobre el diagrama de despliegue (VM1, VM3, VM4, VM6, vault) | La lista de «riesgos aceptados» | Media |
| 6 | 5, 29 y 42 | Cadena driver, escenario, ADR y trade-off generalizada (la lámina 42 ya la usa para un caso) | La tabla de ADR y la lista de drivers como texto suelto | Media |
| 7 | 9 y 41 | Antes y ahora en dos paneles: repositorios, ambiente de QA y almacenamiento | Dos tablas de mejoras | Media |
| 8 | 11 y 46 | Escalera de precedencia SRS, SAD, SDD, DD, Infraestructura y TD, con «qué responde» y el estado | Dos listas de documentos | Media |
| 9 | 28 | Barras de RAM y de tiempo de la prueba de concepto | La tabla de dos columnas | Baja |
| 10 | 12 | Árbol épica, requisito funcional e historia | La tabla (sirve tal como está) | Baja |

Láminas que no necesitan diagrama: 4 y 6 (son matrices), 34 (cifras), 35 a 39 y 43 a 45 (evidencia), 47 (cierre), y los diagramas que ya existen (7, 16 a 24, 27 y 30), a los que solo hay que quitar el texto repetido.

## 4. Reglas para la plantilla

1. Una lámina con diagrama lleva el título, una frase de qué mirar y nada más; el texto que repite lo que dibuja el diagrama se quita.
2. Cada concepto (ADR, RNF, killer, restricción, documento) se explica en una sola lámina; las demás lo nombran por su código.
3. Cinco tipos de lámina: diagrama, matriz o tabla, cadena de pasos, cifras y evidencia.
4. Los datos de un sprint concreto (cifras, estados, evidencias) van en un anexo, para que el cuerpo de la plantilla sirva en cualquier sprint.

## 5. Límites de esta revisión

- Es una lectura del texto y de miniaturas de baja resolución; no se leyó la letra pequeña de los diagramas.
- Se revisó el diseño tal como estaba el 20 de octubre de 2026; si la presentación cambió después, hay que repetir la revisión.
- Qué láminas conservar o fusionar lo decide el equipo; esto solo señala dónde hay repetición.
