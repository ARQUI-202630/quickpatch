# Protocolo de medición de AC8-E1, AC8-E4 y AC9-E8 (SCRUM-668)

**Código del Documento:** `PRT-QA-668-2026-11-13`  
**Versión:** `1.0 (protocolo; resultados pendientes de ejecución en QA)`  
**Fecha:** 13 de noviembre de 2026  
**Responsable:** Katherine Bravo (`ka.bravo@javeriana.edu.co`) — QA Lead  
**Trazabilidad Jira:** Subtarea `SCRUM-668` de la historia `SCRUM-663` | Escenarios `AC8-E1`, `AC8-E4` y `AC9-E8` de [`matriz-escenarios-calidad-52.md`](matriz-escenarios-calidad-52.md) (hoy los tres en Parcial)  
**Criterio de aceptación de SCRUM-668:** estado final con evidencia, o la razón por la que sigue en Parcial

---

## 1. Qué falta en cada escenario

| Escenario | Meta | Qué hay hoy | Qué falta |
|---|---|---|---|
| **AC8-E1** Alta de un tenant | Tenant funcional en menos de 1 hora, sin caída para los demás tenants | El alta del tenant Beta funcionó en QA el 15-oct (`tests/e2e/evidencias/tenant-beta-qa-2026-10-15.txt`, 8/8) | Cronometrar el alta completa, desde la creación hasta el primer inicio de sesión, con los demás tenants funcionando durante la prueba |
| **AC8-E4** Cambio de proveedor de geolocalización | El cambio no exige tocar otros servicios | Solo ServiceRequest geocodifica, detrás del puerto `IGeocoder` (`NominatimGeocoder`); 0 referencias en los otros 6 servicios (medición del 4-nov) | Hacer un cambio real de proveedor en QA y mostrar que solo cambian la configuración o el adaptador de ServiceRequest |
| **AC9-E8** Cambio de proveedor sin alterar la cobertura | El 100 % de los casos de regresión de cobertura da lo mismo antes y después del cambio | La cobertura por localidad se calcula con PostGIS, no con el proveedor | Correr la misma regresión de cobertura antes y después del cambio de AC8-E4 |

AC8-E4 y AC9-E8 se miden en la misma ventana, porque los dos necesitan el mismo cambio de proveedor.

---

## 2. AC8-E1: alta cronometrada de un tenant

**Quién:** QA ejecuta y cronometra. El administrador de plataforma crea el tenant. DevOps aplica la configuración del canal (`infrastructure/ansible/playbooks/habilitar-tenant-beta.yml` como base, con otro nombre de tenant). QA no cambia la configuración de las VM.

**Pasos:**

1. Antes de empezar, correr el humo del flujo crítico contra el tenant principal y guardar la salida:
   `node tests/e2e/correr-colecciones-qa.js humo-flujo-critico`
2. **T0:** el administrador de plataforma crea el tenant con `POST /v1/platform/tenants` (o desde el panel). Anotar la hora exacta y el id del tenant.
3. DevOps habilita el canal del tenant nuevo (host del Nginx y `Channel__Tenants__...` en la configuración de Identity y Catalog). Anotar la hora en que termina.
4. Mientras se hacen los pasos 2 y 3, repetir el humo del paso 1 cada 5 minutos. Si alguna corrida falla, anotar la hora y el error.
5. **T1:** un usuario nuevo se registra e inicia sesión por el host del tenant nuevo (las mismas 8 comprobaciones de `tenant-beta-qa-2026-10-15.txt`). Anotar la hora del primer inicio de sesión exitoso.
6. Repetir el humo una última vez.

**Cumple si** T1 − T0 es menor de 60 minutos **y** todas las corridas del humo pasaron durante el alta. Si el alta necesita una persona de DevOps, el tiempo cuenta igual: se reporta tal como se midió.

**Evidencia:** `tests/e2e/evidencias/ac8-e1-alta-tenant-qa-<fecha>.txt` con T0, T1, la duración, las horas del paso 3 y las salidas del humo.

---

## 3. AC8-E4 y AC9-E8: cambio de proveedor de geolocalización

**Quién:** Backend y DevOps hacen el cambio en QA; QA corre la regresión antes y después. La decisión de qué proveedor usar en la prueba es de Arquitectura (ADR-024 fija el Nominatim propio de la VM de datos).

**Opciones de cambio, de la más barata a la más completa:**

| Opción | Qué se cambia | Mide AC8-E4 | Mide AC9-E8 |
|---|---|---|---|
| A. Otro servidor compatible con Nominatim (por ejemplo, una segunda instancia con otro extracto de OpenStreetMap) | Solo `Geocoding__NominatimUrl` en la configuración de ServiceRequest | Sí, si el cambio queda en esa variable | Sí |
| B. Un adaptador nuevo para otro proveedor (otra clase que implemente `IGeocoder`) | Una clase nueva y su registro en `DependencyInjection.cs` de ServiceRequest | Sí, y es la prueba más fuerte: muestra que el cambio queda dentro del adaptador | Sí |

**Pasos:**

1. **Antes del cambio**, correr la regresión de cobertura contra QA y guardar la salida:
   `node tests/e2e/correr-colecciones-qa.js scrum-600-fuera-de-bogota scrum-458-geocodificacion-buzon`

   (`scrum-600-fuera-de-bogota` es la misma colección que dio la evidencia de SCRUM-636: puntos conocidos dentro y fuera de Bogotá y su localidad.)
2. Backend o DevOps hacen el cambio (opción A o B) y lo despliegan en QA. Guardar el enlace al PR o al cambio de configuración.
3. **Para AC8-E4:** listar los repositorios y archivos que tocó el cambio. Cumple si solo cambian la configuración o el adaptador de ServiceRequest, y ningún otro servicio.
4. **Después del cambio**, correr las mismas dos colecciones del paso 1.
5. **Para AC9-E8:** comparar caso por caso las dos corridas (localidad asignada, rechazo fuera de Bogotá y vista previa). Cumple si el 100 % de los casos da el mismo resultado. Si algún caso cambia, se anota cuál y por qué.
6. Volver al proveedor original, si así lo decide Arquitectura, y correr la regresión una vez más.

**Evidencia:** `tests/e2e/evidencias/ac8-e4-ac9-e8-cambio-geocodificador-qa-<fecha>.txt`, con el cambio hecho, los archivos que tocó, las dos corridas y la comparación caso por caso.

---

## 4. Registro de ejecución

| Escenario | Fecha | Quién ejecutó | Resultado medido | Estado propuesto | Evidencia |
|---|---|---|---|---|---|
| AC8-E1 | | | | | |
| AC8-E4 | | | | | |
| AC9-E8 | | | | | |

Si la prueba no se puede hacer antes del cierre (por ejemplo, porque no hay ventana de DevOps en QA), el escenario sigue en **Parcial** y en esta tabla queda la razón, que es lo que pide SCRUM-668.

---

## 5. Lo que no hace este protocolo

- No da resultados: todavía no se ha ejecutado. Ninguna cifra de la matriz cambia por este documento.
- QA no cambia la configuración de las VM ni el código de ServiceRequest; esos cambios los hacen DevOps y Backend.
