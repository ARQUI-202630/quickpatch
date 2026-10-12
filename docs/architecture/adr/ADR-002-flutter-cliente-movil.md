# ADR-002 — Flutter como cliente móvil único

- **Estado:** Aceptado
- **Fecha:** agosto de 2026 (SAD 1.0)
- **Decisión:** Una sola aplicación Flutter para clientes, empresas cliente, técnicos y proveedores en Android e iOS
- **Atributo priorizado:** AC7 Maintainability
- **Atributo sacrificado:** AC2 Performance Efficiency (rendimiento y APIs nativas óptimas por plataforma)
- **Restricción que la motiva:** R3 (tiempo académico de unos 3 meses)
- **Implementación:** `quickpatch-mobile` (Flutter 3.47.5, Dart 3.13.4)

## Contexto

QUICKPATCH tiene dos canales (SAD, sección 4.2.1): un panel web para los administradores y una aplicación móvil para quienes piden y prestan los servicios. Los usuarios de la app usan tanto Android como iOS, y la app tiene flujos con cámara (evidencia fotográfica, D7), ubicación (D1), notificaciones y seguimiento en tiempo real (D2).

El equipo tiene una sola persona dedicada a mobile y un calendario de unos tres meses (R3). Mantener dos aplicaciones nativas duplicaría el desarrollo, las pruebas y la corrección de defectos de cada pantalla.

## Decisión

Construir **una sola aplicación Flutter** para todos los roles móviles. La app:

- consume únicamente los contratos REST de `quickpatch-api-gateway`, fijados con el submódulo `contracts/api-gateway/` (ADR-021);
- organiza el código por capacidad (`lib/features/<capacidad>/{data,domain,presentation}`) y separa lo transversal en `lib/core/`;
- muestra solo las opciones permitidas para el rol del token (SCRUM-25).

## Alternativas descartadas

- **Apps nativas (Kotlin y Swift):** mejor rendimiento y acceso directo a las APIs de cada plataforma, pero dos bases de código, dos conjuntos de pruebas y conocimiento de dos plataformas en un equipo pequeño. No cabe en R3.
- **React Native:** una sola base de código, pero el equipo trabaja con Angular y TypeScript en web y con Flutter ya tenía experiencia; React Native no reduce el costo frente a Flutter y agrega un tercer ecosistema de UI.
- **Aplicación web progresiva (PWA):** se reutilizaría el panel Angular, pero el acceso a cámara, ubicación en segundo plano y notificaciones en iOS es limitado, y el seguimiento en tiempo real del técnico en campo depende de esas capacidades.

## Consecuencias

### Positivas
- Una sola base de código, una sola suite de pruebas (`flutter test`, cobertura mínima del 80% en el CI) y un solo APK por versión.
- La misma lógica de sesión, errores y roles para todos los usuarios móviles.

### Costos
- Se renuncia a optimizaciones nativas por plataforma; si alguna funcionalidad lo exige (por ejemplo, ubicación continua en segundo plano), se resuelve con un plugin o con código nativo puntual.
- Dependencia de la madurez de los plugins de Flutter para cámara, almacenamiento seguro y notificaciones.
- Hoy el CI compila solo Android: compilar iOS requiere macOS.

## Evidencia

- Estructura base y autenticación de la app en `quickpatch-mobile` (PR #3 y #4), con análisis estático sin hallazgos y 43 pruebas.
- Sin PoC de rendimiento: el rendimiento en dispositivos de gama baja se medirá con el escenario AC4-E8.

## Trazabilidad

- SAD: secciones 4.2.1 y 6; restricción R3; escenarios AC4-E1, AC4-E2, AC4-E8.
- SDD: componentes de apps cliente (C4 nivel 3).
- Relacionados: ADR-012 (stack), ADR-013 (repositorios).
