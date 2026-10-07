# ADR-015 — Ambiente de QA en VM2 y acceso a través del gateway de VM1

- **Estado:** Aceptado (3 de octubre de 2026); la parte de QA en una sola VM la reemplaza el ADR-021
- **Fecha:** 2026-10-03
- **Decisión:** VM2 deja de servir el panel web y aloja un ambiente de QA permanente. El panel pasa al Nginx de VM1, que además es la única entrada desde la VPN a producción, a QA y a Grafana, y elige el destino según el nombre pedido.
- **Implementación:** rama `feature/devops/ansible-base` de `quickpatch-infrastructure`

> **Actualización (ADR-021, 6 de octubre de 2026):** QA deja de ser una sola VM: la entrada (Nginx y panel de QA) sigue en VM2, k3s pasa a VM5 y los datos a VM6. La entrada única por VM1 y el acceso por nombre siguen vigentes.

## Contexto

### Ambiente de QA

Hasta ahora QA no ocupaba ninguna VM (Documento de Infraestructura, sección 4.1). Las pruebas funcionales, de aceptación y de seguridad corrían en un runner de GitHub Actions que levantaba `docker-compose.staging.yml` y lo destruía al terminar. La prueba de carga corría contra VM3 de producción, después del despliegue y con reversión si fallaba (SRS, RNF-07 y RNF-08). La razón era R10: el laboratorio asigna 7 VMs fijas y no da una octava.

Ese modelo funciona, pero deja tres problemas:

1. No existe un QA al que se pueda entrar entre una prueba y otra, para revisar un error o hacer una demostración.
2. El despliegue real (k3s, manifiestos y rolling update) solo se ejecuta en producción. Un manifiesto mal escrito se descubre en producción.
3. La prueba de carga corre contra producción. Si el umbral falla, la versión ya está desplegada y hay que revertirla.

Mientras tanto, VM2 solo servía el panel Angular, que son archivos estáticos.

### Acceso desde la VPN

Al configurar las VMs (3 de octubre de 2026) se encontró que el firewall perimetral de la universidad, que el equipo no controla (R9), solo deja pasar algunos puertos desde la VPN. Pasan el 443 de VM1, el 8080 de VM6 (Kafka UI) y el 22 de todas las VMs. No pasan el 3000 (Grafana) ni el 9090 (Prometheus) de VM7, ni el 443 de VM2. Desde dentro del laboratorio, por ejemplo desde VM1, los tres responden.

Sin una solución, el equipo no puede ver Grafana ni QA desde la VPN, que es como trabaja.

## Decisión

### 1. VM2 pasa a ser el ambiente de QA

| Antes | Después |
|---|---|
| VM1: Nginx y API Gateway | VM1: Nginx, API Gateway **y panel Angular** (archivos estáticos), runner de GitHub y k6 |
| VM2: panel Angular | VM2: **QA completo** |

QA en VM2 replica la forma de producción en una sola máquina:

- k3s de un nodo, con la misma versión y los mismos rangos de red que VM3, para probar los manifiestos y el rolling update antes de producción.
- PostgreSQL + PostGIS con una base por servicio, Redis y Kafka en Docker Compose.
- Nginx propio, que sirve el panel y envía `/api/` a k3s.
- Secretos propios: ninguna contraseña de QA es igual a la de producción.

**QA no puede llegar a producción.** PostgreSQL, Redis y Kafka de producción solo aceptan conexiones desde VM3 (Documento de Infraestructura, sección 10.2). Se comprobó que VM2 no puede abrir conexión con VM4:5432.

**La prueba de carga (k6) corre contra QA**, desde el runner de VM1. Así una versión que no cumple el umbral se detecta antes de llegar a producción.

### 2. VM1 es la entrada única y elige el destino por nombre

El Nginx de VM1 escucha en el 443, el único puerto que el firewall perimetral deja pasar, y reenvía cada petición según el nombre pedido:

| Nombre | Destino | Quién puede entrar |
|---|---|---|
| `quickpatch.internal` (o la IP de VM1) | Producción: panel y `/api/` hacia VM3 | Cualquiera que alcance VM1 |
| `qa.quickpatch.internal` | QA en VM2 | Solo `10.0.0.0/8` (red de la universidad y VPN) |
| `grafana.quickpatch.internal` | Grafana en VM7 | Solo `10.0.0.0/8`, con el login de Grafana |

- No hay DNS (R9). Cada persona agrega una línea a su archivo `hosts` con los tres nombres apuntando a VM1, como ya preveía la sección 11.2 del Documento de Infraestructura para `quickpatch.internal`.
- El certificado autofirmado de VM1 incluye los tres nombres.
- Prometheus no se publica. Sus datos se consultan desde Grafana, que lo alcanza dentro del laboratorio, y Prometheus no tiene login.

## Justificación

### Por qué VM2 y no otra VM

| VM | Por qué no se usó para QA |
|---|---|
| VM3 | Es la más cargada y ya es punto único de falla (SAD, sección 5.2). QA competiría por CPU y memoria con los 8 microservicios de producción. |
| VM4 | El SAD deja la base de datos sola en su VM. Compartirla con QA mezcla datos de prueba y reales en la misma máquina. |
| VM5 y VM6 | Redis y Kafka se separaron a propósito para aislar sus fallas. |
| VM7 | Ya combina almacenamiento y observabilidad. |
| **VM2** | Su único trabajo eran archivos estáticos, que el Nginx de VM1 puede servir sin costo apreciable. Es la única VM que se libera sin juntar dos cargas pesadas. |

### Por qué por nombre y no por ruta

La alternativa era publicar todo en la IP de VM1 bajo rutas: `/grafana/` y `/qa/`. Funciona para Grafana con dos variables de configuración, pero no para QA. El panel Angular espera vivir en `/` y pedir la API en `/api/`. Para servirlo bajo `/qa/` habría que compilarlo con otra ruta base, y entonces QA probaría un build distinto del que llega a producción, que es justo lo que QA debe evitar.

Con nombres, cada destino vive en su propia raíz y QA usa exactamente el mismo build que producción. El costo es una línea en el archivo `hosts` de cada persona, que se agrega una vez.

### Por qué un proxy en VM1 y no otra forma de acceso

- **Pedir al laboratorio que abra los puertos:** depende de un tercero sin fecha de respuesta, y cada puerto nuevo requeriría otra solicitud. El equipo lo consideró innecesario si VM1 resuelve el acceso.
- **Túneles SSH:** funcionan porque el 22 sí pasa, pero cada persona tiene que abrir su propio túnel cada vez. Sirven como respaldo, no como forma normal de trabajo.

## Consecuencias

### Positivas

- QA existe siempre, con datos y secretos propios, y se puede abrir para depurar o hacer una demostración.
- El despliegue con k3s se prueba en QA antes de producción.
- La prueba de carga deja de correr contra producción.
- RNF-07 ("staging separado de producción") se cumple con un servidor real.
- Grafana y QA quedan accesibles desde la VPN sin depender del laboratorio.

### Costos

- **Una VM más que mantener para una sola persona (R11).** Se mitiga con un playbook propio (`deploy-qa.yml`) y el mismo inventario de Ansible.
- **La prueba de carga en QA es una aproximación.** En QA todo corre en una VM; en producción, en siete. Un resultado aceptable en QA no garantiza el mismo resultado en producción, pero un resultado malo en QA sí indica un problema. Las métricas de producción en Grafana siguen siendo la validación final.
- **Recursos de VM2.** Con QA levantado y sin microservicios todavía, VM2 usa 3,3 GB de 11 GiB (medido el 3 de octubre de 2026). El consumo con los 8 servicios está por medirse.
- **Una línea en el archivo `hosts` por persona** para entrar a QA y a Grafana.

### Riesgo aceptado: VM1 concentra la entrada

VM1 ya era la única entrada a producción. Con esta decisión también es la única entrada desde la VPN a QA y a Grafana, y además sirve el panel y aloja el runner y k6. Esto tiene dos efectos:

1. **Si VM1 se cae, se pierde el acceso desde la VPN a producción, a QA y a Grafana a la vez.** Para producción no cambia nada, porque ya dependía de VM1. Lo grave es Grafana: es lo que se abriría para diagnosticar la caída, y deja de estar disponible justo en ese momento.
   - **Mitigación:** el SSH sí pasa el perímetro hacia todas las VMs, así que Grafana se puede abrir con un túnel directo a VM7, sin pasar por VM1: `ssh -L 3000:10.43.99.8:3000 estudiante@10.43.99.8`. El procedimiento queda en el README de Ansible.
2. **k6 compite con el gateway de producción.** Cuando el runner genera carga contra QA, consume CPU de VM1, la misma que atiende las peticiones de producción.
   - **Mitigación:** las pruebas de carga se ejecutan en una ventana sin usuarios activos, como ya exigía RNF-07, y se vigila la CPU de VM1 en Grafana durante la prueba.

Se acepta porque la alternativa, repartir la entrada entre varias VMs, no es posible: el perímetro solo deja pasar el 443 de VM1.

### Limitación: la restricción por red es amplia

QA y Grafana solo aceptan `10.0.0.0/8`, pero ese rango incluye toda la red de la universidad y a cualquier usuario de su VPN, no solo al equipo. Para Grafana la protección real es su login. El panel de QA todavía no tiene login, así que cualquiera dentro de la red de la universidad que conozca el nombre puede abrirlo. Es aceptable mientras QA solo tenga datos de prueba.

## Decisiones descartadas

### Mantener QA efímero en GitHub Actions

Se descartó porque no resuelve ninguno de los tres problemas del contexto. Sigue siendo válido para las pruebas automáticas de cada Pull Request, que no necesitan un servidor permanente.

### QA como namespace dentro del k3s de VM3

Se descartó porque QA competiría por recursos con producción en la VM más cargada, y una prueba de carga en QA degradaría producción.

### Pedir una octava VM

Se descartó porque el laboratorio no la asigna (R10).

### Publicar QA y Grafana por ruta en la IP de VM1

Se descartó porque obliga a compilar el panel de QA distinto del de producción (ver Justificación).

### Pedir al laboratorio que abra los puertos de VM7 y VM2

Se descartó por depender de un tercero, cuando VM1 resuelve el acceso con los puertos que ya pasan.

## Pendientes

- Decidir si QA usa el sandbox de la pasarela de pagos o un simulador. Se recomienda el simulador, porque QA tampoco puede recibir webhooks desde fuera del laboratorio (R9).
- ~~Definir el reemplazo de MinIO~~: resuelto en el ADR-016 (Garage, en producción y en QA).
- Medir el consumo de VM2 con los 8 microservicios desplegados.
- Agregar login al panel de QA o restringir `team_networks` a los rangos de la VPN del equipo, si el laboratorio los asigna fijos.
- Revisar Kafka UI en VM6:8080. El perímetro sí deja pasar ese puerto y hoy no tiene login.
- Actualizar los documentos:
  - ~~SAD, sección 5.1: tabla de VMs~~: hecho en el SAD V2.13.
  - SRS: RNF-07 y RNF-08, que hoy describen la prueba de carga contra producción.
  - Documento de Infraestructura:
    - secciones 2 y 3.2: rol de VM2, y VM2 y VM5 con Rocky Linux, no Ubuntu;
    - sección 4: ambientes;
    - sección 5.2: `deploy-frontend` se integra en `deploy-gateway` y se agrega `deploy-qa`;
    - sección 6: despliegue a QA;
    - secciones 10.2 y 11: puertos y los tres nombres;
    - sección 13: el riesgo aceptado de VM1.
  - SDD, sección 7: diagrama de producción y diagrama nuevo de QA.
  - Documento de Políticas: QA como servidor de la rama `release/*`.

## Trazabilidad

Resumen en el SAD, sección 5.5 (tabla de ADR de infraestructura).

Esta decisión se refleja en `quickpatch-infrastructure`:

- `ansible/inventory/group_vars/all/main.yml` (`gateway_hosts`)
- `ansible/inventory/group_vars/all/firewall.yml` (reglas de VM2)
- `ansible/playbooks/deploy-qa.yml` y `ansible/playbooks/deploy-gateway.yml`
- `ansible/templates/gateway-nginx.conf.j2` y `ansible/templates/observabilidad.compose.yml.j2`
- `ansible/README.md` (sección "Entrar a producción, QA y Grafana")
