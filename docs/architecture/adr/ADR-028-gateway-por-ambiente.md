# ADR-028 — Gateway propio en cada ambiente, con VM1 como entrada TLS compartida

- **Estado:** Aceptado; implementado el 25 de octubre de 2026 en QA (VM2) y en producción (VM3) (SCRUM-573). Precisa la regla 3 de ADR-022 y cambia dónde corren el gateway y el panel, que ADR-022 y la decisión del 12 de octubre ponían en el k3s de VM3 y en VM1
- **Fecha:** 25 de octubre de 2026
- **Decisión:** producción y QA tienen cada uno su propio gateway Nginx, dentro de su VM de aplicación (VM3 y VM2), que reenvía la API al Traefik de su k3s y sirve el panel Angular de su ambiente. VM1 sigue siendo la única entrada desde la VPN, pero solo termina el HTTPS y reenvía por nombre al gateway del ambiente
- **Atributos priorizados:** AC7 Maintainability (Modifiability y Testability: la configuración, el panel y el despliegue de un ambiente se cambian y se prueban sin tocar los del otro) y AC5 Reliability (una configuración o un panel defectuosos de QA ya no pueden dejar sin gateway a producción)
- **Atributos sacrificados:** AC5 Reliability en la entrada (VM1 sigue siendo el único camino y un punto único de falla de los dos ambientes), AC2 Performance Efficiency (un salto de Nginx más por petición) y simplicidad operativa (R11: dos Nginx más que operar)
- **Restricciones:** R9 (desde la VPN solo entra el 443 de VM1), R10 (7 VMs fijas), R11 (una persona administra la infraestructura), R9 también cubre el certificado: sin dominio público no hay CA pública, así que es autofirmado

## Contexto

En la retroalimentación del Sprint 4 (24 de octubre de 2026), el profesor observó que el diagrama de despliegue da a entender que QA y producción comparten API Gateway e infraestructura, que producción no aparece modelada con sus tres máquinas y que las herramientas no son parte del despliegue productivo.

Lo que había desplegado el 25 de octubre de 2026:

- Un solo contenedor Nginx en VM1 con un `nginx.conf` que servía los tres destinos: producción, QA (con el tenant Beta) y Grafana. Un error en el bloque de QA podía dejar sin entrada a producción, y los dos paneles estaban en carpetas de VM1.
- En los k3s de VM3 y VM2 solo había Traefik con los Ingress de cada servicio. No existía un API Gateway desplegado en ningún ambiente, a pesar de que ADR-022 planeaba moverlo, con el panel, al k3s de VM3.
- Producción tenía 4 de los 8 servicios y el panel provisional; QA tenía 6 servicios y el panel real.

Dos condiciones limitan la solución:

- **R9:** el firewall perimetral de la universidad deja pasar desde la VPN solo el 443 de VM1. Las VMs de aplicación no son alcanzables directamente. VM1, en cambio, sí llega a VM2 y a VM3 (ya lo hacía por el 30080 de Traefik y por el 6443 del runner).
- **Cliente móvil:** la app de QA entra por `https://10.43.100.168` con la cabecera `Host` de QA y fija la huella SHA-256 del certificado de VM1. Una conexión por IP no manda nombre de servidor (SNI), y cambiar el certificado exigiría recompilar el APK.

## Decisión

```
VPN ─443→ VM1  entrada: certificado, TLS, red del equipo, Grafana
              ├─ quickpatch.internal ────→ VM3:8080  Nginx de producción → Traefik :30080 (k3s)
              └─ qa.* / beta.qa.* ───────→ VM2:8080  Nginx de QA         → Traefik :30080 (k3s)
```

1. **Un Nginx de gateway por ambiente**, en la VM de aplicación (VM3 en producción, VM2 en QA), como contenedor de Docker con `network_mode: host`. Los dos salen de la misma plantilla (`gateway-ambiente-nginx.conf.j2`, en `quickpatch-api-gateway`) y cambian solo por la variable `entorno`. Cada uno:
   - escucha en HTTP por el puerto 8080, abierto por el firewall solo a VM1;
   - quita el prefijo `/api` y reenvía al Traefik de su propio k3s (`/api/v1/realtime` con los tiempos del WebSocket de ADR-023);
   - sirve el panel Angular de su carpeta `/opt/quickpatch/gateway/panel`, que el runner escribe por SSH desde el job de `quickpatch-web` (`release/*` en VM2, `main` en VM3);
   - fija `X-Channel-Id` (DD 10.3) y descarta el que mande el cliente o el que ponga VM1; el tenant Beta existe solo en el gateway de QA, por el nombre `beta.qa.quickpatch.internal`.
2. **VM1 queda como entrada TLS** (`entrada-nginx.conf.j2`): termina el HTTPS con el mismo certificado autofirmado, aplica la lista de redes del equipo a QA, Beta y Grafana, y reenvía por `Host`, sin cambiar `Host`, `Origin` ni `Referer`, al gateway del ambiente. Producción sigue siendo el servidor por defecto, así que la app móvil conserva su entrada por IP y su huella de certificado.
3. **Se cambia un ambiente a la vez.** `gateway_propio.qa` y `gateway_propio.produccion` (inventario de Ansible) valen `false` mientras VM1 atienda ese ambiente por sí misma, que es la forma anterior, y `true` cuando lo atiende su gateway. La entrada se niega a escribirse si el gateway de un ambiente en `true` no responde, y volver atrás es poner la bandera en `false` y aplicar de nuevo.
4. **Los tiempos del WebSocket (75 s) van en los dos saltos** (entrada y gateway): si uno usa el valor por defecto de 60 s, corta la conexión inactiva de Communication (ping cada 30 s).

## Alternativas descartadas

- **Solo documentar y redibujar (ADR de excepción, un Nginx compartido):** costo mínimo, pero deja la configuración, el panel y el despliegue de los dos ambientes en el mismo archivo. No separa nada, y el profesor pidió un gateway por ambiente.
- **Enrutador TCP por SNI en el 443 de VM1 y un Nginx con TLS en cada ambiente:** el certificado y su huella pasarían a ser uno por ambiente (recompilar el APK), y la app de QA, que entra por IP sin SNI, no tendría a dónde ir salvo un destino por defecto.
- **Dos Nginx en VM1 con puertos distintos:** independiza el proceso, no el nodo, y el firewall de la universidad solo deja pasar el 443 desde la VPN (R9): un segundo puerto no sería alcanzable.
- **API Gateway y panel en el k3s de cada ambiente (plan de ADR-022):** es lo más coherente con la orquestación, pero no existe imagen del gateway ni del panel, VM3 es la VM con más carga (presupuesto de RAM del Documento de Infraestructura, 5.6) y no cabe en el tiempo de la entrega. Queda como evolución posible; este ADR no la impide.
- **TLS en cada ambiente y VM1 como túnel TCP:** descartada por los mismos motivos del enrutador por SNI.

## Consecuencias

### Positivas

- Cada ambiente tiene su gateway, su configuración, su panel y su despliegue. Un cambio o un error en el Nginx de QA no toca el de producción, y el diagrama de despliegue puede mostrar cada ambiente con sus tres VMs y su gateway propio.
- No cambia nada para los usuarios ni para la app móvil: mismos nombres, misma IP de entrada, mismo certificado.
- El cambio es reversible por ambiente con una bandera, y se verifica con `verificar-gateway-ambiente.yml` (solo lectura) antes y después de cambiar la entrada.

### Costos y riesgos aceptados

- **VM1 sigue siendo la única entrada y el punto único de falla de los dos ambientes.** Es el límite de R9 y R10 (sin una octava VM ni otro camino desde la VPN). Un error en la configuración de la entrada todavía puede dejar sin acceso a ambos ambientes; por eso la entrada se valida con `nginx -t` antes de escribirse y es mucho más pequeña que antes (sin API, sin paneles, sin mapa de canal).
- **Dos Nginx más que operar** (R11), con SELinux en Enforcing en VM2 (Rocky): los volúmenes llevan la etiqueta `:z`.
- **Un salto más** por petición, y dos configuraciones de WebSocket que deben mantenerse iguales.
- **El canal del cliente solo se prueba de punta a punta** (`humo-frontends.yml`, `pruebas-sistema.yml`): un `proxy_set_header` dentro de una `location` haría que esa ruta dejara de heredar `X-Channel-Id`, como ya advertía la plantilla anterior.
- **La llave SSH del runner queda autorizada en VM3**, además de VM2, para publicar el panel de producción. El runner ya tiene el kubeconfig de producción, así que el alcance no crece de forma importante.
- **Producción sigue incompleta:** 4 de 8 servicios y el panel provisional. Este ADR mueve la estructura, no completa el despliegue.

## Implementación (SCRUM-573)

- `quickpatch-api-gateway` (PR #29): `gateway-ambiente-nginx.conf.j2` y `entrada-nginx.conf.j2` (antes `gateway-nginx.conf.j2`).
- `quickpatch` (PR #161): `deploy-gateway.yml` (gateway de cada ambiente, copia opcional del panel y entrada de VM1), `gateway_propio` y `gateway_puerto` en el inventario, regla de firewall del 8080 desde VM1 en VM2 y VM3, llave del runner en VM3 (`deploy-runner.yml --tags llave-runner`), `verificar-gateway-ambiente.yml` y la compuerta RNF-08 leyendo el panel de QA en VM2.
- `quickpatch-web` (PR #25): el job «Panel en qa / produccion» publica por SSH en VM2 o VM3.
- Orden aplicado el 25 de octubre: firewall del 8080, llave del runner, gateway de QA en VM2, verificación, cambio de la entrada para QA, gateway de producción en VM3, verificación y cambio de la entrada para producción.

## Evidencia (25 de octubre de 2026)

- `verificar-gateway-ambiente.yml` en VM1: QA, gateway 200, Traefik 200 y entrada 200, con el panel real; producción, gateway 401, Traefik 401 y entrada 401 (servicio vivo sin token), con el panel provisional. La entrada por IP con el `Host` de QA, como la app móvil, da lo mismo que por nombre.
- `https://qa.quickpatch.internal/api/v1/realtime`: `101 Switching Protocols` a través de los dos Nginx. El tenant Beta responde 404 en `/`.
- Compuerta RNF-08: desde VM1, la huella del panel de QA en VM2 por SSH coincide con la de la copia que se publicó.

## Trazabilidad

- SAD: secciones 4.1, 5.1 a 5.3 y 5.5; RNF-02; escenario AC7-E6.
- Documento de Infraestructura: secciones 2.1, 3.2, 3.3, 5.2, 6 y 10.
- Relacionados: ADR-015 (QA y entrada única), ADR-022 (regla 3, que este ADR precisa), ADR-023 (WebSocket y sus tiempos), ADR-011 (k3s sin cambios).
