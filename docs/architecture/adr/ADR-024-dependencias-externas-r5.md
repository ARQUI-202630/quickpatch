# ADR-024 — Dependencias externas frente a R5: geocodificación propia (Nominatim, Bogotá) y notificaciones dentro de la app

- **Estado:** Aceptado el 12 de octubre de 2026 por el equipo (SCRUM-413 y SCRUM-405; SAD V4 y SRS V5). Resuelve la decisión pendiente P1 del SRS (sección 7.4)
- **Fecha:** 12 de octubre de 2026
- **Decisión:** R5 se mantiene sin cambios: la única dependencia externa de producción sigue siendo la pasarela de pagos (K2). La geocodificación (RIE-02) se resuelve dentro de las 7 VMs con un Nominatim propio que solo tiene el mapa de Bogotá (R6). Las notificaciones (RIE-03) del MVP se entregan dentro de la app: el canal de ADR-023 y un buzón de notificaciones en Communication Service. El correo y las notificaciones push con la app cerrada quedan fuera del MVP
- **Atributos priorizados:** AC6 Security (los datos personales —direcciones, correos y tokens de dispositivo— no salen de la infraestructura del laboratorio, K12) y AC5 Reliability (ninguna función del MVP depende de que un tercero responda, salvo el pago)
- **Atributos sacrificados:** AC7 Maintainability (un componente más que instalar, importar y actualizar en cada ambiente, con una sola persona de DevOps, R11), AC2 Performance Efficiency (RAM y disco de la VM de datos) y AC4 Interaction Capability (sin avisos con la app cerrada ni por correo)
- **Restricciones:** R5 (sin presupuesto, sin dependencias externas de producción salvo la pasarela), R6 (operación limitada a Bogotá), R9 (red privada), R10 (7 VMs fijas de 11 GiB), R11 (una persona administra la infraestructura), K12 (Ley 1581, datos personales)

## Contexto

El SRS pide dos interfaces externas que contradicen R5 del SAD (SRS 7.4, P1; SCRUM-405):

- **RIE-02 Geocodificación:** convertir en coordenadas la dirección escrita por el cliente cuando no comparte la ubicación de su teléfono. La cercanía con los técnicos ya la calcula PostGIS (ADR-004); lo que falta es pasar de texto a punto.
- **RIE-03 Notificaciones:** confirmar el registro, la asignación del técnico, la cotización y los cambios de estado, "por correo electrónico y/o notificación push".

R5 dice que el cómputo y los datos que atienden usuarios en producción no corren fuera de las 7 VMs, y que la única dependencia externa de producción es la pasarela de pagos. Un geocodificador en la nube recibiría las direcciones de los clientes; un proveedor de correo recibiría sus correos, y el push en Android y iOS solo se entrega por Firebase Cloud Messaging o APNs. Todos son terceros que reciben datos personales (K12).

Desde ADR-023, los cambios de estado ya llegan a la app por un canal propio (WebSocket hacia Communication Service), sin servicios externos: lo que RIE-03 agrega sobre eso es avisar con la app cerrada y por correo.

## Decisión

### Geocodificación (RIE-02): Nominatim propio con el mapa de Bogotá

1. **Componente:** [Nominatim](https://nominatim.org/) (geocodificador de OpenStreetMap, software libre) en un contenedor de Docker Compose en la **VM de datos de cada ambiente**: VM4 en producción y VM5 en QA (ADR-022, regla 1: mismos componentes en los dos ambientes; ADR-011: Docker Compose fuera del k3s).
2. **Datos:** solo **Bogotá D.C.** (R6). El extracto se obtiene del mapa de Colombia de OpenStreetMap recortado al límite de Bogotá; así la importación y la base caben con holgura en la VM de datos (11 GiB de RAM, R10). La descarga del mapa es un paso de aprovisionamiento, como bajar una imagen: no es una dependencia en tiempo de ejecución.
3. **Base de datos:** Nominatim trae su propio PostgreSQL dentro del contenedor y no usa la instancia de los servicios. Es una **excepción explícita a ADR-014**: esa base solo guarda datos públicos del mapa, no datos de los usuarios, y aislarla evita que una importación compita con las bases de los servicios.
4. **Acceso:** solo desde el k3s del mismo ambiente (VM3 → VM4, VM2 → VM5), por la red interna y con regla de firewall propia (ADR-022, regla 2). No se publica por VM1.
5. **Quién lo usa:** ServiceRequest Service, del lado del servidor. Si una solicitud llega con la dirección y **sin coordenadas**, la geocodifica dentro de Bogotá antes de guardarla; si no encuentra la dirección o Nominatim no responde, rechaza la solicitud con un error que le pide al cliente compartir su ubicación. Las coordenadas del GPS siguen siendo la primera opción. La app ya no geocodifica: la sección 4.1 del SAD deja de ubicar ese paso en Flutter Mobile.
6. **Actualización del mapa:** manual y poco frecuente (por ejemplo, una vez por sprint), reimportando el extracto con el playbook. El MVP no necesita cambios de calles en tiempo real.

### Notificaciones (RIE-03): dentro de la app en el MVP

1. **Avisos en vivo:** el canal de estado en tiempo real de ADR-023.
2. **Buzón:** Communication Service guarda cada notificación por usuario y tenant (su base, `db_communication`) y la app las muestra en una lista (registro confirmado, técnico asignado, cotización recibida, cambio de estado). Así el usuario ve lo que pasó aunque no tuviera la app abierta.
3. **Fuera del MVP:** el correo electrónico y las notificaciones push con la app cerrada. Para incorporarlos habría que revisar R5 (un proveedor de correo o Firebase y APNs) en una decisión nueva.

## Alternativas descartadas

- **Ampliar R5 para servicios externos gratuitos que no guarden datos (SRS, P1 opción a):** resolvía las dos interfaces con poco trabajo, pero un geocodificador o un proveedor de correo en la nube sí recibe datos personales mientras procesa la petición, y el equipo prefirió no abrir la restricción.
- **Geocodificar con la localidad de Bogotá (centroide del catálogo `localities`, P-04):** sin componente nuevo, pero el punto queda a varios kilómetros de la dirección real y el matching por cercanía (D1) pierde precisión justo para quien no comparte la ubicación.
- **Geocodificador del sistema operativo del teléfono:** no agrega componentes al backend, pero la dirección del cliente sale a Google o a Apple desde el dispositivo (K12), y el resultado depende de cada teléfono.
- **Nominatim con el mapa de Colombia completo:** cubre más ciudades de las que el MVP atiende (R6) a cambio de varias veces más RAM, disco y tiempo de importación.
- **Correo con un servidor propio o con la cuenta de Gmail de las alertas:** un servidor propio no entrega correo hacia Internet desde la red del laboratorio de forma confiable (R9); la cuenta de Gmail de Grafana es para avisar al equipo, no para escribirles a los usuarios (sus correos saldrían a Google).
- **Push con Firebase Cloud Messaging:** es la única forma práctica de avisar con la app cerrada en Android, pero es un servicio externo que recibe los tokens de los dispositivos (R5, K12).

## Consecuencias

### Positivas

- La restricción R5 se cumple tal como está escrita y P1 del SRS queda resuelta.
- Ningún dato personal sale de las 7 VMs para geocodificar ni para notificar (K12).
- La geocodificación no tiene cuotas ni límites de uso de un tercero, y funciona igual en QA y en producción.
- Las notificaciones del MVP reutilizan Communication Service y el canal de ADR-023.

### Costos

- Un componente más en VM4 y VM5, con su importación inicial (minutos con el extracto de Bogotá) y su actualización manual (R11).
- Excepción a ADR-014: hay una segunda base PostgreSQL en la VM de datos, dentro del contenedor de Nominatim.
- La precisión depende de cómo esté cargado el mapa de OpenStreetMap en Bogotá; las direcciones con nomenclatura poco común pueden no encontrarse, y entonces se le pide al cliente compartir su ubicación.
- Sin correo ni push, un usuario con la app cerrada no se entera de un cambio hasta que la abre (el buzón le muestra lo que pasó).

## Trabajo que se desprende

- **Infraestructura (DevOps):** playbook de Nominatim para VM4 y VM5 con el extracto de Bogotá, regla de firewall desde el k3s del ambiente, presupuesto de memoria de la VM de datos y documento de infraestructura.
- **Contratos y DD V4 (SCRUM-416, SCRUM-418):** en `CreateServiceRequest`, las coordenadas pasan a ser opcionales cuando llega la dirección, con el error de dirección no encontrada; endpoint del buzón de notificaciones de Communication.
- **Backend:** geocodificación en ServiceRequest (cliente HTTP hacia Nominatim con tiempo de espera y restringido a Bogotá) y buzón en Communication.
- **App:** permitir crear la solicitud sin ubicación (con la dirección) y mostrar el buzón.
- **Documentos:** SRS (RIE-02, RIE-03 y P1, hecho en esta versión), SAD 4.1 (diagrama de contexto, hecho), SDD 5.1 y el modelo de Structurizr (SCRUM-425).

## Trazabilidad

- SRS: RIE-02, RIE-03, RF-07, RF-11; sección 7.4 (P1, resuelta).
- SAD: R5, R6, R9, R10, R11, K12; D1, D2; secciones 1.2, 4.1 y 5.5.
- Relacionados: ADR-004 (PostGIS), ADR-011 (Docker Compose fuera del k3s), ADR-014 (excepción), ADR-022 (VMs de datos y aislamiento entre ambientes), ADR-023 (canal en tiempo real).

## Implementación en QA (14 de octubre de 2026, SCRUM-454)

Desplegado en VM5 con `deploy-nominatim.yml` (detalle y mediciones en el Documento de Infraestructura, sección 5.9). Dos precisiones frente a lo decidido arriba:

- **Red.** El contenedor de Nominatim no usa la red del host (su PostgreSQL interno choca con el 5432 de la VM): publica su API solo en `127.0.0.1:8081` y un Nginx en la red del host la expone en el puerto 8088, con la regla de firewall de la VM (VM2 hacia VM5) y el mismo `allow` en el Nginx. Producción (VM4, desde VM3) queda pendiente.
- **Límite de la geocodificación.** El mapa resuelve nombres de vía y lugares, pero **no el número de casa ni la calle transversal** de la nomenclatura de Bogotá ("Carrera 7 # 72-41" devolvió una Carrera 7 en otra localidad). Con la dirección escrita la coordenada puede quedar en otra localidad; el GPS sigue siendo la primera opción y conviene que la app muestre el punto encontrado para que el Cliente lo confirme. Pendiente de decisión del equipo de ServiceRequest y de la app.
