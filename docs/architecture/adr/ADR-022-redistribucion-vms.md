# ADR-022 — Redistribución de las 7 VMs: 3 de producción, 3 de QA y 1 de herramientas

- **Estado:** Aceptado; implementación en curso (SCRUM-334). Modifica a ADR-015 y actualiza la ubicación de los componentes de ADR-011, ADR-014 y ADR-016
- **Fecha:** 6 de octubre de 2026
- **Decisión:** VM1 es la VM de herramientas y la única entrada desde la VPN. Producción ocupa VM3 (aplicación), VM4 (datos) y VM6 (mensajería y almacenamiento). QA es una copia de producción en VM2, VM5 y VM7
- **Atributos priorizados:** AC7 Maintainability (Testability: QA reproduce la topología de producción, incluida la red entre VMs) y AC5 Reliability (las pruebas de QA ya no compiten por una sola VM)
- **Atributos sacrificados:** AC5 Reliability en producción (pasa de 6 VMs a 3: más componentes por VM) y AC2 (Kafka y Garage, y PostgreSQL y Redis, comparten VM)
- **Restricciones:** R9 (desde la VPN solo entra el 443 de VM1), R10 (7 VMs fijas), R11 (una persona administra la infraestructura)

## Contexto

Con ADR-015, producción usaba seis VMs (VM1 y VM3 a VM7) y QA una sola (VM2), con todo junto: k3s, PostgreSQL, Redis, Kafka, Garage y Nginx. Eso tenía dos problemas:

- QA no reproducía la red de producción: en QA todo se comunicaba dentro de una máquina, así que un error de firewall, de nombres o de latencia entre VMs solo aparecía en producción. La prueba de carga en QA era solo una aproximación, porque la base de datos, Kafka y los servicios competían por la misma VM (Documento de Infraestructura, sección 6.2).
- Las herramientas del equipo (runner de CI, k6, observabilidad) estaban repartidas entre la VM de entrada (VM1) y la de almacenamiento (VM7).

En la revisión de octubre de 2026, el profesor pidió repartir las 7 VMs en **3 para QA, 3 para producción y 1 para herramientas**.

Dos condiciones limitan el mapeo:

- **R9:** el firewall de la universidad solo deja pasar el 443 de VM1 desde la VPN. Si VM1 fuera de producción, QA y Grafana dependerían de la VM de producción para ser alcanzables.
- **Medición del 3 de octubre de 2026:** con toda la infraestructura desplegada y sin microservicios, ninguna VM pasa del 32% de la RAM (11 GiB por VM, de los cuales unos 2,3 GiB son del software del laboratorio).

## Decisión

|VM|Ambiente|Rol|Qué corre|
|---|---|---|---|
|VM1|Herramientas|Entrada y herramientas|Proxy Nginx :443 que elige destino por nombre (`quickpatch.internal` → producción, `qa.quickpatch.internal` → QA, `grafana.quickpatch.internal` → Grafana); runner de GitHub con kubectl y k6; Prometheus, Loki y Grafana para los dos ambientes|
|VM3|Producción|Aplicación|k3s de un nodo: los 8 microservicios, el API Gateway (`quickpatch-api-gateway`) y el panel Angular|
|VM4|Producción|Datos|PostgreSQL + PostGIS (una base por servicio, ADR-014) y Redis|
|VM6|Producción|Mensajería y almacenamiento|Kafka y Kafka UI (`quickpatch-kafka`) y Garage (evidencias y respaldos de PostgreSQL, ADR-016)|
|VM2|QA|Aplicación|Igual que VM3|
|VM5|QA|Datos|Igual que VM4|
|VM7|QA|Mensajería y almacenamiento|Igual que VM6|

Reglas:

1. **Mismos componentes y versiones en los dos ambientes**, aprovisionados con los mismos playbooks de Ansible parametrizados por ambiente (SCRUM-346).
2. **Aislamiento entre ambientes:** las VMs de QA no pueden conectarse a las de producción, ni al revés. Solo VM1 llega a las dos.
3. **TLS termina en VM1**, que reenvía al gateway del ambiente (Traefik en el k3s de VM3 o VM2). Dentro de cada ambiente, el gateway enruta `/api/<servicio>` al servicio.
4. **Recursos por servicio:** cada servicio tiene su base de datos con roles propios (ADR-014, ADR-019), su usuario de Redis restringido a sus claves (`<servicio>:*`) si usa caché, y su llave de Garage limitada a sus buckets si guarda archivos. El detalle está en el Documento de Infraestructura.
5. **Respaldo:** el `pg_dump` diario de producción va de VM4 al Garage de VM6. QA no tiene respaldo: sus datos son de prueba.
6. **Observabilidad:** las 7 VMs envían métricas y logs a VM1, con la etiqueta de su ambiente.

## Alternativas descartadas

- **VM1 como gateway de producción y otra VM como herramientas:** QA y Grafana dependerían de la VM de producción para ser alcanzables desde la VPN (R9), y una carga de prueba hacia QA pasaría por la entrada de producción.
- **QA en una sola VM y producción en cinco (ADR-015):** no cumple la indicación del profesor y QA no reproduce la red de producción.
- **Base de datos sola en su VM y Redis con Kafka:** Redis es caché de baja latencia para los servicios y Kafka recibe ráfagas; juntar Redis con PostgreSQL mantiene el almacenamiento de estado en una VM y la mensajería y los archivos en otra.
- **Kubernetes en las tres VMs de cada ambiente (clúster de tres nodos):** daría alta disponibilidad a los servicios, pero obligaría a mover PostgreSQL, Kafka y Garage dentro del clúster y a operar dos clústeres de tres nodos con una sola persona (R11).

## Consecuencias

### Positivas

- QA tiene la misma topología que producción: firewall, nombres, latencia y despliegue se prueban antes de producción (AC7-E6), y la prueba de carga de QA es representativa (AC2-E5).
- Las herramientas quedan en una VM que no es de ningún ambiente: el runner y la observabilidad no compiten con producción.
- Se mantiene una sola entrada desde la VPN.

### Costos

- Producción pasa de seis VMs a tres: si VM4 cae, se pierden PostgreSQL y Redis a la vez; si VM6 cae, Kafka y Garage. La limitación de un solo nodo por componente ya existía (SAD, sección 5.2).
- VM1 concentra la entrada, el CI y la observabilidad: si cae, no hay acceso desde la VPN ni monitoreo (riesgo ya aceptado en ADR-015). La prueba de carga se lanza desde VM1, que también recibe las métricas: hay que medir que k6 no afecte a Prometheus y Loki.
- La migración mueve servicios con datos (Redis de VM5 a VM4; Garage y observabilidad desde VM7) y cambia las reglas de firewall de casi todas las VMs.
- Los presupuestos de memoria de VM4 y VM6 deben medirse de nuevo con los servicios desplegados (SCRUM-347).

## Plan de migración (SCRUM-343 a SCRUM-347, DevOps)

1. VM1: instalar Prometheus, Loki y Grafana y redirigir las métricas y los logs de las 7 VMs; después apagar la observabilidad de VM7.
2. Producción: mover Redis de VM5 a VM4 y Garage de VM7 a VM6 (copiando los buckets y respaldos), y desplegar el API Gateway y el panel en el k3s de VM3. Después cambiar el proxy de VM1.
3. QA: repartir el QA todo en uno de VM2 en VM2 (k3s), VM5 (PostgreSQL y Redis) y VM7 (Kafka y Garage).
4. Firewall por VM según la tabla de reglas del Documento de Infraestructura.
5. Verificación: medición de RAM y disco, pruebas de humo y reglas de firewall en los dos ambientes.

## Trazabilidad

- SAD: secciones 5.1 a 5.5; escenarios AC2-E5, AC5-E1, AC7-E6.
- Documento de Infraestructura: distribución objetivo y recursos por servicio.
- Relacionados: ADR-011 (k3s en VM3 y VM2, sin cambios), ADR-014 (PostgreSQL en VM4; QA en VM5), ADR-015 (QA y entrada única, modificado), ADR-016 (Garage en VM6; QA en VM7), ADR-021.
