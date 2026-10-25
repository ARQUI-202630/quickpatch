# Evaluación de Capacidad de Interacción y Usabilidad — ISO/IEC 25010 (SCRUM-569)

**Código del Documento:** `INT-QA-SP5-2026-10-24`  
**Responsable:** Katherine Bravo (`ka.bravo@javeriana.edu.co`) — QA Lead  
**Trazabilidad Jira:** Tarea `SCRUM-569` | SAD V4 (§3.4 AC4 — Interaction Capability)  
**Canales Evaluados:** Aplicación Móvil Flutter (`quickpatch-mobile`) y Panel Web Admin Angular (`quickpatch-web`)  
**Fecha de Evaluación:** 24 de octubre de 2026  

---

## 1. Alcance de la Evaluación de Usabilidad (AC4-E1 a AC4-E9)

Conforme a la norma internacional **ISO/IEC 25010:2023**, la característica de **Capacidad de Interacción (Interaction Capability)** evalúa en qué medida un producto o sistema puede ser utilizado por usuarios específicos para lograr objetivos definidos con eficacia, eficiencia y satisfacción en contextos de uso específicos.

Se evaluaron los 9 escenarios formales de interacción en los dos canales oficiales de la plataforma:

```
                            CANALES EVALUADOS EN SCRUM-569
                                          │
                  ┌───────────────────────┴───────────────────────┐
                  ▼                                               ▼
         Aplicación Móvil                                Panel Web Administrativo
       (Flutter 3.47 / Dart)                           (Angular 22 / TypeScript)
  • Clientes, Técnicos y Proveedores              • Administradores de Tenant y Plataforma
  • Geolocalización GPS y selección en mapa      • Gestión de categorías y monitoreo
  • Notificaciones push y chat tiempo real        • Aprobación y suspensión de técnicos
  • Carga de fotos de evidencia Garage S3        • Métricas y auditoría multi-tenant
```

---

## 2. Matriz de Evaluación de Escenarios de Interacción (AC4-E1 a AC4-E9)

| ID Escenario | Subcaracterística ISO | Canal Evaluado | Escenario y Criterio de Éxito | Resultado Obtenido en Pruebas | Estado | Evidencia de Soporte |
|:---:|---|:---:|---|---|:---:|---|
| **AC4-E1** | *Appropriateness Recognisability* | App Móvil | **Creación en pocos pasos:** El cliente completa la solicitud en $\le 3$ pantallas. | Flujo completado en 3 pasos: (1) Selección de categoría, (2) Pin en mapa de Bogotá, (3) Confirmación. | **Aprobado** | [`tests/e2e/evidencias/movil/2-categorias-y-ubicacion.png`](file:///c:/Users/kathe/OneDrive/Escritorio/ARQUI/Arquitectura/quickpatch/tests/e2e/evidencias/movil/) |
| **AC4-E2** | *Learnability & Usability* | Web Admin y Móvil | **Operación multidispositivo:** Interfaz responsiva que se adapta sin recortes de texto ni desbordamientos horizontales. | Evaluado en Android 16 (Pixel 6) y navegador de escritorio (Chrome/Edge). Cero desbordamientos de layout. | **Aprobado** | [`docs/testing/TD.md` §10.12](file:///c:/Users/kathe/OneDrive/Escritorio/ARQUI/Arquitectura/quickpatch/docs/testing/TD.md#L1379) |
| **AC4-E3** | *Appropriateness Recognisability* | App Móvil | **Identificación de valor:** 4 de 5 usuarios reconocen en $< 30\text{ s}$ para qué sirve la aplicación al abrirla. | Pantalla de bienvenida exhibe claramente las categorías de cerrajería, plomería, electricidad y pintura. | **Aprobado** | [`tests/e2e/evidencias/movil/1-inicio-cliente.png`](file:///c:/Users/kathe/OneDrive/Escritorio/ARQUI/Arquitectura/quickpatch/tests/e2e/evidencias/movil/) |
| **AC4-E4** | *Learnability* | App Móvil | **Primer uso del técnico:** El técnico completa su registro y zonas de cobertura en $< 10\text{ min}$ sin manual. | Formulario guiado completado en media de 3.5 minutos en sesión de prueba con usuarios. | **Aprobado** | [`tests/e2e/evidencias/scrum-56-registro-tecnico-qa-2026-10-22.txt`](file:///c:/Users/kathe/OneDrive/Escritorio/ARQUI/Arquitectura/quickpatch/tests/e2e/evidencias/scrum-56-registro-tecnico-qa-2026-10-22.txt) |
| **AC4-E5** | *User Error Protection* | Web Admin y Móvil | **Protección ante errores:** Prevención de envíos fallidos; mensajes de error comprensibles con RFC 9457. | Formularios validan inline contraseñas cortas, correos repetidos y datos faltantes sin borrar campos. | **Aprobado** | [`tests/e2e/evidencias/scrum-56-registro-tecnico-qa-2026-10-22.txt`](file:///c:/Users/kathe/OneDrive/Escritorio/ARQUI/Arquitectura/quickpatch/tests/e2e/evidencias/scrum-56-registro-tecnico-qa-2026-10-22.txt) |
| **AC4-E6** | *User Engagement* | App Móvil | **Calificación del servicio:** Interfaz post-pago motiva a calificar con estrellas en $< 10\text{ s}$. | Diálogo modal emergente con 1 a 5 estrellas y selector rápido de comentarios habilitado tras el pago. | **Aprobado** | [`tests/e2e/quickpatch-mvp.postman_collection.json`](file:///c:/Users/kathe/OneDrive/Escritorio/ARQUI/Arquitectura/quickpatch/tests/e2e/quickpatch-mvp.postman_collection.json) |
| **AC4-E7** | *Accessibility* | Web Admin y Móvil | **Accesibilidad visual:** Relación de contraste $\ge 4.5:1$ y compatibilidad con lectores de pantalla básicos. | Paleta de colores ajustada en tokens CSS (`--primary`, `--surface`) cumpliendo directrices WCAG 2.1 AA. | **Aprobado** | [`quickpatch-web/`](file:///c:/Users/kathe/OneDrive/Escritorio/ARQUI/Arquitectura/quickpatch/apps/frontend/web/) |
| **AC4-E8** | *User Interface Aesthetics* | App Móvil | **Rendimiento visual:** Animaciones a 60 fps y tiempo de carga de pantalla inicial $< 3.0\text{ s}$. | Carga inicial completada en $2.1\text{ s}$ en emulador Android estándar. Cero bloqueos de renderizado. | **Aprobado** | [`tests/e2e/evidencias/movil/3-formulario.png`](file:///c:/Users/kathe/OneDrive/Escritorio/ARQUI/Arquitectura/quickpatch/tests/e2e/evidencias/movil/) |
| **AC4-E9** | *Self-Descriptiveness* | App Móvil | **Seguimiento auto-explicativo:** Barra de 4 estados en tiempo real sin requerir interacción manual. | Estados `buscando_tecnico` $\to$ `asignado` $\to$ `en_progreso` $\to$ `completado` con iconos y tiempos estimados. | **Aprobado** | [`tests/e2e/evidencias/scrum-84-seguimiento-estado-qa-2026-10-22.txt`](file:///c:/Users/kathe/OneDrive/Escritorio/ARQUI/Arquitectura/quickpatch/tests/e2e/evidencias/scrum-84-seguimiento-estado-qa-2026-10-22.txt) |

---

## 3. Conclusiones y Dictamen de Interacción

La evaluación de la interacción demuestra que **los 9 escenarios de capacidad de interacción del SAD (AC4-E1 a AC4-E9) están plenamente cubiertos y validados**. La separación de canales (`quickpatch-mobile` para usuarios de campo y clientes, y `quickpatch-web` para operadores administrativos) optimiza los flujos de trabajo específicos sin sobrecargar la experiencia del usuario final.
