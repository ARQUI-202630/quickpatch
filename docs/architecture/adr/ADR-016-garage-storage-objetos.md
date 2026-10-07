# ADR-016 — Garage como almacenamiento de objetos compatible con S3

- **Estado:** Aceptado
- **Fecha:** 3 de octubre de 2026
- **Decisión:** Garage v2.4.1 en un solo nodo, en VM7 para producción y con una instancia propia en VM2 para QA, en lugar de MinIO
- **Atributos priorizados:** AC6 Security (un solo puerto expuesto, llaves separadas por uso) y uso de recursos de VM7 (AC2)
- **Atributos sacrificados:** funciones avanzadas de S3 (versionado, bloqueo de objetos) y consola web
- **Driver y restricciones:** D7 (evidencia fotográfica), R5, R10
- **Implementación:** `quickpatch-infrastructure` (Ansible, llaves en Ansible Vault)

> **Actualización (ADR-021, 6 de octubre de 2026):** la instancia de Garage de QA pasa de VM2 a VM6; producción sigue en VM7.

## Contexto

Las evidencias fotográficas (D7, RF-15) y los respaldos diarios de PostgreSQL se guardan en un almacenamiento de objetos propio en VM7 (R5). La herramienta elegida era MinIO, pero al configurar las VMs (octubre de 2026) se encontró que dejó de distribuir su edición comunitaria: las imágenes de Docker no se actualizan y `dl.min.io` responde 410. Mientras se decidía, el almacenamiento quedó apagado y no había respaldo de la base de datos.

El reemplazo debía:

- ofrecer una API compatible con S3 (SDK de AWS en .NET y Java) con URLs prefirmadas;
- correr en un solo nodo en una VM compartida con Prometheus, Loki y Grafana (R10);
- tener una imagen de Docker mantenida;
- ser libre y sin costo (R5).

## Prueba de concepto

VM7, 3 de octubre de 2026, mismas pruebas y mismo puerto para los dos candidatos:

|Prueba|SeaweedFS 4.48|Garage v2.4.1|
|---|---|---|
|RAM en reposo / después de las pruebas (`docker stats`)|60 / 83 MiB|3 / 4 MiB|
|Subir y bajar 2 MB con el SDK de AWS, verificando el contenido|Correcto, 0,40 s|Correcto, 0,17 s|
|URL prefirmada de subida y de bajada|Correcto|Correcto|
|Acceso sin firma|Rechazado|Rechazado|
|`pg_dump` de `db_matching` (con PostGIS) desde VM4 y lectura con `pg_restore --list`|Correcto, 2 s|Correcto, 2 s|
|Puertos que abre hacia la red|4 (S3, master, volume, filer)|1 (S3); RPC y administración solo en localhost|

## Decisión

- Garage v2.4.1 en un solo nodo, en VM7 para producción y una instancia propia en VM2 para QA (ADR-015).
- En producción, la API S3 (`10.43.99.8:9000`) solo acepta conexiones de VM3 (servicios) y VM4 (respaldo).
- Dos buckets y una llave por uso: `servicios` solo accede a `evidencias` y `backups` solo a `backups-postgres`. Se comprobó el aislamiento en los dos sentidos.
- El respaldo diario sube un `pg_dump` de cada base a las 2:00 y conserva 7 días.
- Las llaves se guardan en Ansible Vault y la configuración completa es código de Ansible.
- ServiceRequest trata Garage como un adaptador de infraestructura detrás de un puerto de almacenamiento: el dominio no depende del proveedor.

## Alternativas descartadas

- **SeaweedFS:** cumple los requisitos y tiene licencia Apache 2.0, pero usa unas 20 veces más memoria en una VM compartida y abre cuatro puertos.
- **MinIO compilado desde el código:** obligaría a mantener una compilación propia sin actualizaciones de seguridad publicadas.
- **Ceph (RADOS Gateway):** pensado para clústeres de varios nodos; demasiado pesado para VM7.
- **Almacenamiento en la nube (Cloudflare R2, Amazon S3):** viola R5.

## Consecuencias

### Positivas
- Vuelve a haber respaldo diario de la base de datos.
- Garage casi no consume recursos de VM7 y expone un solo puerto.

### Costos
- Licencia AGPL v3 (sin obligaciones mientras no se modifique).
- No implementa versionado ni bloqueo de objetos (QUICKPATCH no los usa) y no trae consola web.
- Sigue siendo un solo nodo sin réplica, igual que el diseño con MinIO: si VM7 se pierde, se pierden las evidencias (limitación aceptada en el Documento de Infraestructura, sección 9.4).
- Hoy los servicios suben las evidencias; si en el futuro la app móvil las subiera directo con URLs prefirmadas, el gateway de VM1 tendría que publicar la API S3, porque los clientes no llegan a VM7.

## Trazabilidad

- SAD: driver D7, sección 5.5 (este archivo reemplaza el detalle de la antigua sección 5.5.1).
- Documento de Infraestructura: VM7, respaldos y sección 9.4.
- Relacionados: ADR-014 (respaldos de las bases), ADR-015 (instancia de QA).
