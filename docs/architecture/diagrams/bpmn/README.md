# Flujos de negocio de QUICKPATCH en BPMN Sketch Miner

Fuentes de texto para https://www.bpmn-sketch-miner.ai: se pega el contenido de cada `.txt` y la herramienta dibuja el BPMN. Cubren SCRUM-285 (flujos principales) y SCRUM-289 (lógica de negocio crítica) del SDD.

## Cómo están escritos

- **Son flujos de negocio, no de la aplicación.** Los carriles son los participantes del negocio: las personas (Cliente, Empresa cliente, Técnico, Proveedor, Admin del tenant, Admin de plataforma), **Quickpatch** como un solo participante y la **Pasarela de pagos** como socio externo. No aparecen microservicios, eventos, tokens, bases de datos ni el inicio de sesión (es un mecanismo técnico, no una actividad del negocio): cómo los implementa el sistema está en los diagramas C4 del SDD (sección 8, Dynamic).
- Cada línea es `Carril: actividad`. Una línea entre paréntesis, como `Cliente: (Solicitud registrada)`, es un evento: el primero de cada historia es el de inicio y el último el de fin.
- Cada caso alternativo es otra historia, separada con una línea vacía. Sketch Miner une las historias y pone una compuerta donde se separan. Las actividades repetidas se escriben igual en todas las historias para que se unan.
- Las reglas de negocio vienen del DD (RN-*) y los requisitos del SRS (RF-*).

## Flujos

| Archivo | Flujo | Requisitos y reglas |
|---|---|---|
| `00-flujo-punta-a-punta` | Vista general: solicitud, asignación, cotización, servicio, pago y calificación | RF-07, RF-09, RF-34, RF-15, RF-22, RF-12 |
| `01-registro-de-cliente` | Alta de un cliente hogar y rechazo de uno ya registrado | RF-01, RN-U1 |
| `02-registro-y-verificacion-de-tecnicos` | Registro del técnico, aprobación, rechazo y suspensión | RF-02, RF-19, RF-20 |
| `03-registro-de-empresa-cliente` | Cuenta corporativa | RF-06, DEP-13. **Pendiente:** SCRUM-26; aún no está en el contrato de la API |
| `04-gestion-de-tenants` | Activar o desactivar tenants con auditoría | RF-21, RN-U6 |
| `05-gestion-del-catalogo` | Categorías de servicio del tenant | RN-SR10 |
| `06-disponibilidad-y-cobertura-del-tecnico` | Disponibilidad y zona de cobertura | RF-13, RN-M6 |
| `07-creacion-de-solicitud` | Solicitud con validación de cobertura y tipo de servicio | RF-07, RN-SR1, RN-SR9 a RN-SR11 |
| `08-asignacion-de-tecnico` | Ofrecer el servicio al técnico más cercano, rechazo o falta de respuesta y sin técnicos | RF-09, RF-10, RN-M1 a RN-M7 |
| `09-cotizacion` | Aceptación, rechazo, tercera cotización rechazada y vencimiento | RF-34, RF-35, RN-Q1 a RN-Q7 |
| `10-ejecucion-del-servicio` | Inicio, evidencia fotográfica y cierre | RF-14, RF-15, RN-SR3, RN-SR6, RN-E1 a RN-E3 |
| `11-pago-y-facturacion` | Pago con tarjeta, rechazo con reintento y comprobante | RF-22, RF-24, RN-P1 a RN-P5, RN-SR4, RN-SR5 |
| `12-calificacion-y-reputacion` | Calificación única y recálculo de reputación | RF-12, RN-R1 a RN-R3 |
| `13-cancelacion-de-solicitud` | Cancelación por cliente o admin antes de iniciar | RF-36, RN-SR7, RN-SR8, RN-Q5, RN-M5 |
| `14-gestion-del-equipo-del-proveedor` | Técnicos del proveedor y sus pagos | RF-16, RF-25 |

## Imágenes

Exportar cada diagrama en PNG desde Sketch Miner con el mismo nombre del `.txt` (por ejemplo `09-cotizacion.png`). En el repositorio van en `docs/architecture/diagrams/bpmn/` y se enlazan desde el SDD.
