# Guion de la demostración del incremento — Sprint 5

**Historia:** SCRUM-556 (presentación de la entrega del Sprint 5). **Tarea:** SCRUM-557.
**Estado del guion:** borrador del 27 de octubre de 2026, escrito sobre lo que hoy funciona en QA. Antes del ensayo se revisa contra el estado final del sprint: los pasos marcados **[si llega]** solo se muestran si su historia está en Finalizado y tiene evidencia en QA.

## Reglas de la demostración

1. **Solo se muestra lo que corre en QA**, con la app instalada desde el APK publicado y el panel de `qa.quickpatch.internal`. Nada en local ni con datos simulados en la app.
2. **Datos:** las cuentas de demostración de `tests/datos-demo/` (dominio `demo.quickpatch.test`). Se cargan con `cargar-datos-demo.py --ambiente qa` el día anterior. Las contraseñas no se muestran en pantalla ni en las diapositivas.
3. **Lo simulado se dice en voz alta:** el pago usa la pasarela simulada (ADR-009 modificado) con las tarjetas de prueba, no un proveedor certificado.
4. **Plan B:** si la VPN o QA fallan, se muestran los videos grabados en el ensayo y las evidencias de `tests/e2e/evidencias/`. No se improvisa en otro ambiente.

## Preparación (el día anterior)

| Paso | Responsable | Cómo se verifica |
|---|---|---|
| Cargar los datos de demostración en QA | DevOps | Al repetir el script, todo sale como "ya existía" |
| Instalar el APK del último release en dos teléfonos o emuladores (cliente y técnico) | Frontend | La pantalla de inicio de sesión abre contra QA |
| Poner disponibles a los técnicos de demostración | DevOps | `disponible` en el panel |
| Revisar que QA tenga las versiones del cierre del sprint | DevOps | Releases y job de despliegue en verde |
| Grabar el video de respaldo de cada bloque | QA | Archivos en la carpeta compartida del equipo |

## Bloques y tiempos (unos 20 minutos)

### Bloque 1. Qué cambió desde el Sprint 4 (2 min) — Juan Diego
- Lo que observó el profesor el 24 de octubre y qué se hizo con cada punto: el gateway por ambiente (ADR-028), los diagramas C4 por componente y los dinámicos con escenario, la restricción geográfica (SRS 2.3.1), el mapa arquitectónico y la matriz de funcionalidades.
- El avance real, con su fórmula y su fecha de corte (SCRUM-562, `docs/testing/avance-real-sprint5.md`). Al 27 de octubre: **65.4%** de las 78 funcionalidades verificadas en QA y 82.1% implementadas. Se muestra con la tabla por tipo de usuario y se explica qué falta para subirlo; se actualiza con el corte final antes de presentar.

### Bloque 2. Entrada al producto (2 min)
1. Abrir `qa.quickpatch.internal`: la página de presentación (SCRUM-491).
2. Mostrar el botón de descarga del APK (SCRUM-628).

### Bloque 3. Flujo del cliente y del técnico (8 min)
Dos teléfonos en pantalla: `demo.cliente1` y `demo.tecnico1`.

1. **Cliente:** crea una solicitud de plomería con una dirección de Bogotá (RF-07). Si sobra tiempo, se muestra que una dirección fuera de Bogotá se rechaza (RN-SR9).
2. **Técnico:** recibe la oferta y la acepta (RF-09, RF-10). El cliente ve el cambio de estado sin refrescar (RF-11, ADR-023).
3. **Técnico:** emite la cotización (RF-34). **Cliente:** la acepta (RF-35).
4. **Chat:** un mensaje de ida y vuelta (RF-37, ADR-026).
5. **Técnico:** inicia, sube la foto de evidencia y completa (RF-15).
6. **Cliente:** paga con la tarjeta de prueba aprobada (RF-22, pasarela simulada) y abre el comprobante (RF-24). La solicitud pasa a `pagado`.
7. **[si llega]** El cliente califica el servicio (RF-12, ADR-027) y la reputación del técnico se actualiza. El backend ya está en `develop` (SCRUM-85 y SCRUM-498, 27 de octubre); para mostrarlo faltan la pantalla de la app (SCRUM-86), el despliegue de Ranking en QA (SCRUM-512) y la colección de QA (SCRUM-87). Si no llegan, se muestra el diagrama dinámico de la calificación (SDD, figura 27).
8. **Técnico:** su historial de servicios (RF-17; hoy sin evidencia en QA, SCRUM-102). **[si llega]** Sus pagos recibidos (RF-25).

### Bloque 4. Empresa (2 min)
1. Con la cuenta de la empresa de demostración: sus usuarios autorizados (RF-06).
2. El pago de una solicitud de la empresa hecho por otro usuario de la empresa (RF-23, RN-P6). Si no da el tiempo, se muestra la evidencia `scrum-496-pago-empresa-qa-2026-10-27.txt` (59/59).

### Bloque 5. Panel web (3 min)
1. **Administrador del tenant:** el tablero y las solicitudes activas por estado (RF-18); la aprobación o el rechazo de un técnico con motivo (RF-19); la suspensión (RF-20).
2. **Administrador de plataforma:** el alta y la desactivación de un tenant (RF-21), y las solicitudes de todos los tenants.

### Bloque 6. Calidad y operación (3 min)
- Estadísticas de pruebas y defectos del sprint (SCRUM-601) y la matriz de los 52 escenarios (SCRUM-563).
- Grafana con los logs de la corrida de la demostración, filtrados por `correlationId` (RF-28).
- Lo que todavía no está en producción (Documento de Infraestructura, 4.3) y su plan (SCRUM-518).

## Preguntas que conviene tener preparadas

| Pregunta probable | Respuesta corta y su fuente |
|---|---|
| ¿Por qué el pago es simulado? | ADR-009 modificado: el MVP usa un puerto `IPaymentProvider` y la pasarela certificada entra sin cambiar el contrato |
| ¿Qué pasa si se cae Ranking? | La calificación se guarda igual y la reputación se pone al día al volver (ADR-027, AC5-E3) |
| ¿Producción es igual a QA? | Todavía no: le faltan Payments, Communication y los topics del incremento (Infraestructura 4.3, SCRUM-518), y Ranking no está desplegado en ningún ambiente (SCRUM-512) |
| ¿Cómo se calculó el avance? | Matriz de funcionalidades por usuario (`docs/testing/inventario-funcionalidades-por-usuario.md`), con la fórmula de SCRUM-562 |
| ¿Por qué solo Bogotá? | Regla de negocio y restricción de arquitectura (SRS 2.3.1, SAD R6); Sumapaz queda pendiente (P10) |

## Ensayo

El criterio de la tarea es un ensayo completo antes de la presentación. Se registra aquí:

| Fecha | Asistentes | Duración real | Qué falló | Ajuste |
|---|---|---|---|---|
| | | | | |
