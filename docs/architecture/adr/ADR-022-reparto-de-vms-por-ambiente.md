# ADR-022 — Reparto de las 7 VMs en tres ambientes: herramientas, QA y producción

- **Estado:** Aceptado (6 de octubre de 2026)
- **Fecha:** 2026-10-06
- **Decisión:** Las 7 VMs se reparten en tres ambientes: 1 de herramientas (VM7), 3 de producción (VM1, VM3 y VM4) y 3 de QA (VM2, VM5 y VM6). Producción y QA tienen la misma forma: una VM de entrada (App e Ingress), una de servicios (k3s) y una de datos (PostgreSQL, Redis y Kafka).
- **Reemplaza:** la parte del ADR-015 que dejaba todo QA en VM2. La entrada única por VM1 y el acceso por nombre del ADR-015 siguen vigentes.
- **Atributo priorizado:** AC7 Maintainability (Testability: QA con la misma forma que producción)
- **Atributo sacrificado:** AC5 Reliability (en producción, PostgreSQL, Redis y Kafka comparten VM4 y caen juntos)
- **Implementación:** pendiente en `quickpatch-infrastructure` (Ansible)

## Contexto

Hasta ahora el reparto era el del SAD 5.1: VM1 gateway, panel y runner; VM2 QA completo (ADR-015); VM3 k3s con los 8 microservicios; VM4 PostgreSQL; VM5 Redis; VM6 Kafka; y VM7 Garage con observabilidad.

El 6 de octubre de 2026, al reorganizar las máquinas del laboratorio, el profesor propuso separar App, servicios y base de datos: una VM de herramientas (monitoreo, DevOps y QA), 2 VMs de QA ("App + Ingress" y "BD + Servicios") y 4 de producción (BD, Ingress + Servicios, Servicios y App). Son las mismas 7 VMs, solo reorganizadas. El equipo prefiere 3 de QA y 3 de producción.

Dos problemas del reparto anterior:

1. **QA no tiene la forma de producción.** QA corre todo en una VM, y producción en cuatro roles distintos. El ADR-015 ya lo reconocía como costo: "un resultado aceptable en QA no garantiza el mismo resultado en producción". La prueba de carga se trasladó a QA (SRS 3.3), así que ese límite pesa más.
2. **QA tampoco prueba las conexiones por red entre servicios y datos**, que en producción siempre cruzan VMs.

Restricciones que no cambian:

- El perímetro de la universidad solo deja pasar desde la VPN el 443 de VM1, el 8080 de VM6 y el 22 de todas las VMs (R9). VM1 tiene que seguir siendo la entrada.
- Hardware fijo de 7 VMs (R10) y una sola persona que las administra (R11).

Ventana de oportunidad: no hay servicios ni datos todavía (el último uso medido, del 3 de octubre, es sin microservicios), así que reorganizar solo cuesta reescribir los playbooks de Ansible. Después de que lleguen los primeros servicios costaría migrar datos.

## Decisión

### 1. Reparto

| Ambiente | Rol | VM | Qué corre |
|---|---|---|---|
| Herramientas | Observabilidad | VM7 | Garage de producción, Prometheus, Loki y Grafana (sin cambios) |
| Producción | Entrada | VM1 | Nginx, panel Angular, runner de GitHub y k6 (sin cambios) |
| Producción | Servicios | VM3 | k3s con los 8 microservicios (sin cambios) |
| Producción | Datos | VM4 | PostgreSQL + PostGIS (una base por servicio, ADR-014), **Redis y Kafka con su UI** |
| QA | Entrada | VM2 | Nginx de QA y panel de QA |
| QA | Servicios | VM5 | k3s de QA con los 8 microservicios |
| QA | Datos | VM6 | PostgreSQL + PostGIS, Redis, Kafka y Garage de QA |

### 2. Qué se mueve

- **Producción:** Redis (de VM5) y Kafka (de VM6) pasan a VM4. VM1, VM3 y el PostgreSQL de VM4 no cambian.
- **QA:** VM2 conserva solo Nginx y el panel; su k3s y sus datos salen. k3s de QA nace en VM5 y los datos de QA en VM6.
- **VM7** no cambia.

### 3. Reglas que se mantienen

- VM1 sigue siendo la única entrada desde la VPN a producción, a QA y a Grafana. `qa.quickpatch.internal` sigue apuntando a VM2, cuyo Nginx reenvía `/api/` al k3s de VM5.
- QA no puede llegar a producción: los datos de producción solo aceptan a VM3, y los de QA solo a VM5.
- Cada ambiente conserva secretos propios.

### 4. Kafka UI

El perímetro solo deja pasar el 8080 de VM6, y Kafka de producción pasa a VM4. Kafka UI queda accesible por túnel SSH (`ssh -L 8080:10.43.98.209:8080 estudiante@10.43.98.209`). Publicarlo por VM1 con login queda pendiente.

### 5. Orden de la migración

Producción primero. VM5 y VM6 son hoy producción (Redis y Kafka), así que se mueven a VM4 antes de reconvertirse en QA. Después se reconstruye QA y se vacía VM2.

## Justificación

- **Por qué estas VMs.** VM1, VM3 y VM4 ya tienen el rol que necesitan, y VM7 no cambia. Son los menos movimientos posibles para llegar a 3 y 3.
- **Por qué QA con la misma forma.** Cada ambiente tiene entrada, servicios y datos en VMs distintas, así que QA prueba también las conexiones entre ellas y la prueba de carga se parece más a producción.
- **Por qué VM2 queda como entrada de QA.** El pipeline ya publica el panel de QA en VM2 por SSH (`deploy-panel.yml`) y el runner tiene su llave: los workflows no cambian.
- **Por qué juntar datos en VM4.** Tres VMs de producción no alcanzan para separar entrada, servicios, PostgreSQL, Redis y Kafka. Estimación a partir de lo medido el 3 de octubre: VM4 sola usa 2,4 GiB, Kafka y su UI suman 1,2 GiB (medido en VM6) y Redis casi nada (VM5 usa 2,3 GiB de base). Son unos 3,6 GiB sin carga, de 11 GiB.

## Consecuencias

### Positivas

- QA y producción tienen la misma forma.
- La prueba de carga en QA representa mejor a producción (SRS 3.3).
- Las conexiones por red entre servicios y datos se prueban en QA antes de producción.
- Migrar cuesta poco ahora: no hay datos.

### Costos y riesgos

- **Rompe dos principios del SAD 5.2:** "base de datos sola en su VM" y "Kafka aislado de lo síncrono, Redis separado de Kafka". Se acepta como excepción. Las ráfagas de Kafka pueden competir con PostgreSQL por CPU y memoria, y si VM4 cae se pierden a la vez bases, caché y bus. **Mitigación:** topes de memoria donde ya existen (heap de Kafka de 1 a 2 GB y `maxmemory` de Redis, que baja de 6 GB a 1 GB para esta VM), alerta de RAM al 85% y medición con los servicios reales (pendiente). La memoria de PostgreSQL queda con su valor por defecto hasta que se mida.
- **k3s sigue de un solo nodo** en producción (VM3) y en QA (VM5): sigue siendo punto único de falla. Un clúster de varios nodos exigiría quitar VMs a otros roles.
- **Kafka UI deja de estar accesible desde la VPN** y queda con túnel SSH.
- **QA estará caído durante la migración**, porque se reconstruye.
- **VM1 sigue concentrando la entrada**, con los riesgos aceptados en el ADR-015, y k6 sigue compitiendo con el gateway.

## Decisiones descartadas

- **2 VMs de QA y 4 de producción** (propuesta del profesor). Separa App y Servicios en producción y permitiría un k3s de dos nodos. Se descartó porque QA con 2 VMs no tiene la forma de producción y el equipo prefiere 3 y 3. Si el profesor la exige, esta decisión se reabre.
- **Dejar QA completo en VM2.** No representa a producción.
- **Mantener Redis y Kafka en VMs propias en producción.** No cabe en 3 VMs.
- **k3s de varios nodos.** Cada ambiente tiene una sola VM de servicios.

## Pendientes

- Implementar el reparto en Ansible: inventario, reglas de firewall, `deploy-qa.yml`, Nginx de QA, kubeconfig de QA del runner, etiqueta `entorno` de Promtail y objetivos de Prometheus.
- Actualizar el Documento de Infraestructura, el SDD (despliegue y ambientes) y el diagrama ilustrado.
- Medir VM4 con PostgreSQL, Redis y Kafka juntos y con los 8 microservicios en marcha.
- Agregar login a Kafka UI y publicarlo por VM1.

## Trazabilidad

Resumen en el SAD, sección 5.5 (tabla de ADR de infraestructura) y 6.1 (matriz de trade-offs). Modifica las secciones 5.1, 5.2 y 5.3 del SAD.

Se reflejará en `quickpatch-infrastructure`:

- `ansible/inventory/hosts.yml` y `ansible/inventory/group_vars/all/firewall.yml`
- `ansible/playbooks/deploy-qa.yml`, `deploy-db.yml`, `deploy-cache.yml`, `deploy-kafka.yml` y `deploy-runner.yml`
- `ansible/templates/qa-nginx.conf.j2` y `ansible/templates/promtail.yml.j2`
