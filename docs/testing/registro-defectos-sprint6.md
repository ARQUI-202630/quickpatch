# Registro de defectos del Sprint 6

**Código del documento:** `DEF-QA-SP6-2026-11-22`
**Versión:** `1.0`
**Fecha:** 22 de noviembre de 2026
**Responsable:** Katherine Bravo (`ka.bravo@javeriana.edu.co`), QA Lead
**Trazabilidad Jira:** historia SCRUM-665 (ratificación de confiabilidad y diagnóstico en producción)
**Criterios de severidad:** los mismos de [`registro-defectos-sprint4-sprint5.md`](registro-defectos-sprint4-sprint5.md), sección 1.

El registro de los Sprints 4 y 5 queda cerrado con sus 20 defectos, porque de él salen las estadísticas del Sprint 5. Los defectos que aparecen desde el 13 de noviembre se anotan aquí.

---

## 1. Defectos

| ID | Severidad | Servicio | Detectado en (prueba) | Estado | Responsable | Evidencia |
|:---:|:---:|---|---|:---:|---|---|
| **DEF-S6-01** | Baja (propuesta) | `quickpatch-service-request` (geocodificador Nominatim) | Diagnóstico en producción de AC7-E4 (SCRUM-665, 20-nov): una dirección de Medellín terminó en tiempo de espera del geocodificador y no en el rechazo por el límite de Bogotá | **Abierto** | Backend | [`ac7-e4-diagnostico-prod-2026-11-20.txt`](../../tests/e2e/evidencias/ac7-e4-diagnostico-prod-2026-11-20.txt) |

## 2. Ficha

### DEF-S6-01: una dirección fuera de Bogotá se rechaza por tiempo de espera del geocodificador

* **Qué pasó:** el 20 de noviembre a las 16:46 (hora de Bogotá), en producción, un cliente creó una solicitud con una dirección de Medellín. `NominatimGeocoder` canceló la petición a los 3 s (`TaskCanceledException`) y la solicitud se rechazó por esa razón (correlationId `f955c066-9805-4e81-9b82-65645a63df88`).
* **Qué se esperaba:** que el geocodificador devolviera las coordenadas y que la solicitud se rechazara al compararlas con el límite de Bogotá (RF-07, ADR-024).
* **Impacto:** el usuario ve el mensaje correcto y no se crea la solicitud, así que el resultado para el usuario cumple RF-07. Lo que cambia es el camino: el rechazo tarda unos 3 s y el log lo registra como una falla del geocodificador, no como una dirección fuera de cobertura. Por eso la severidad propuesta es Baja.
* **Pregunta para Backend:** si el geocodificador de producción solo tiene datos de Bogotá (y por eso no responde con otras ciudades) o si estaba lento a esa hora.
* **Relación con la UAT de cierre:** el paso 4 de UAT-CLI-02 (dirección fuera de Bogotá) pide anotar si el rechazo es inmediato o tarda unos 3 s. Ese dato sirve para confirmar este defecto en QA.
* **Tarea en Jira:** pendiente de crear para Backend.

## 3. Resumen

| Estado | Cantidad |
|---|:---:|
| Abiertos (no bloqueantes) | 1 |
| **Total del Sprint 6** | **1** |

No hay defectos bloqueantes (S1) ni de severidad alta (S2) en el Sprint 6.
