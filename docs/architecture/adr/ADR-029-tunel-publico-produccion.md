# ADR-029 — Acceso público al panel de producción por un Cloudflare Quick Tunnel

- **Estado:** Aceptado; aplicado en VM1 el 24 de noviembre de 2026. Resuelve, para el panel y su API, la opción (b) de la «Consecuencia de R9 sin resolver» del SAD (sección 1.2.2)
- **Fecha:** 24 de noviembre de 2026
- **Decisión:** un contenedor `cloudflared` en VM1 abre un Quick Tunnel de Cloudflare hacia la entrada TLS de VM1, siempre con el nombre de producción (`quickpatch.internal`). Desde Internet, el panel de producción y su `/api/` quedan en una URL `https://<aleatorio>.trycloudflare.com`
- **Atributos priorizados:** usabilidad de la demostración (el profesor y los usuarios de prueba entran desde fuera de la red del laboratorio, sin VPN ni archivo `hosts`) y AC4 Security en el tramo público (Cloudflare presenta un certificado de una autoridad pública)
- **Atributos sacrificados:** AC5 Reliability (sin SLA; la URL cambia cada vez que el contenedor se reinicia; VM1 sigue siendo punto único de falla) y AC4 Security (producción queda alcanzable desde Internet y Cloudflare termina el TLS público, así que ve el tráfico en claro)
- **Restricciones:** R9 (sin dominio público ni puertos de entrada), R5 (sin servicios con costo: el Quick Tunnel es gratuito y no pide cuenta) y R11 (una persona administra la infraestructura)

## Contexto

El profesor pidió que el panel web de producción quede expuesto en Internet con Cloudflare.

R9 dice que las 7 VMs viven en la red privada `10.43.x.x` del laboratorio y que no hay NAT ni un dominio público. Desde la VPN, solo pasa el puerto 443 de VM1. El SAD dejaba abierta esta decisión con tres opciones: (a) limitar la demostración a la red del campus, (b) un túnel gratuito evaluado contra R5 y (c) pedir a la universidad una IP pública.

Dos datos hacen viable la opción (b) sin cambiar nada del producto:

- El panel llama a la API con rutas relativas (`/api/`), así que basta con que el panel y la API salgan por el mismo nombre público.
- En producción, los canales `quickpatch-web` y `quickpatch-mobile` apuntan al mismo tenant. Entrar con otro `Origin` deja el canal en `quickpatch-mobile` y el tenant no cambia.

## Decisión

```
Navegador ─HTTPS→ Cloudflare (*.trycloudflare.com)
                     ↑ conexión de salida, TCP 7844 (http2)
VM1  cloudflared ─HTTPS, Host quickpatch.internal→ entrada Nginx 10.43.100.168:443 ─→ gateway de VM3 (panel y API)
```

- **Origen:** `cloudflared` va con `network_mode: host` y apunta a `https://10.43.100.168:443`. El origen fija `Host` y SNI en `quickpatch.internal`, así que el Nginx de VM1 elige siempre el servidor de producción. Las entradas de QA, Beta y Grafana no se alcanzan por el túnel.
- **TLS:** de Cloudflare al navegador, con el certificado de Cloudflare. Entre `cloudflared` y Nginx, dentro de VM1, con el certificado autofirmado (`--no-tls-verify`).
- **Protocolo:** `--protocol=http2`, por TCP. Así pasa aunque el firewall del laboratorio corte el UDP que usa QUIC.
- **URL:** se lee del endpoint local `127.0.0.1:20241/quicktunnel`; el playbook la imprime y comprueba que responde.
- **Encendido explícito:** el playbook exige `-e confirmar_publico=si`, y `-e estado=absent` lo apaga.
- **App móvil:** no cambia. Su certificado fijado es el de VM1, no el de Cloudflare.

## Alternativas descartadas

- **Túnel con nombre (Cloudflare Zero Trust):** da una URL fija, pero exige una cuenta y un dominio público agregado a Cloudflare. Queda como paso siguiente si el panel debe tener una dirección estable.
- **ngrok u otros túneles gratuitos:** el plan gratuito agrega una página intermedia, limita las conexiones y no es lo que pidió el profesor.
- **IP pública o NAT hacia VM1 (opción c):** depende de la universidad y no se resuelve dentro del cierre.

## Consecuencias

- Producción es alcanzable desde Internet. La protegen el login del panel y la autorización de cada servicio; la entrada no tiene `limit_req`, y todos los clientes llegan a Nginx con la IP de VM1, así que no se puede limitar por cliente.
- Sin cuenta ni dominio no hay URL fija: después de reiniciar VM1 o Docker, se vuelve a correr el playbook para leer la nueva URL.
- Los webhooks de la pasarela de pagos siguen sin resolverse: la URL cambia y ADR-009 los simula.

## Evidencia

**24 de noviembre de 2026, 23:36 UTC.** El playbook levantó el túnel en VM1 y Cloudflare asignó `exercises-martha-fewer-prime.trycloudflare.com`. Desde la URL pública:

- `GET /` responde HTTP 200 con el panel 0.7.1 (`<title>QUICKPATCH — Panel administrativo`).
- `POST /api/v1/auth/login` con cuerpo vacío responde HTTP 400 de Identity, así que la API de producción se alcanza por el mismo origen.

En esa primera corrida, el paso que lee la URL falló aunque el túnel estaba arriba: `/quicktunnel` responde con `text/plain` y Ansible no llenaba `json`. El playbook ahora lee el cuerpo.
