SCRUM-448: prueba de humo de punta a punta del panel y la app contra QA, 19 de octubre de 2026
===============================================================================================
Versiones en QA: panel quickpatch-web release/0.4.0, app quickpatch-mobile develop (release/0.4.0 + huella corregida,
quickpatch-mobile#29), ServiceRequest 0.4.0, Matching 0.5.0, Identity 0.4.0, Catalog, Communication 0.2.0.

1. Panel web (tests/e2e/humo/humo-panel.spec.ts, Playwright 1.48.2, Chromium)
   Workflow «Humo de los frontends en QA» en el runner de VM1 con los secretos QA_ADMIN_* y QA_PLATFORM_ADMIN_*:
   https://github.com/ARQUI-202630/quickpatch/actions/runs/39328587806 (3 de 3 pasan, 19,0 s)

   PASA  Administrador de la plataforma: inicia sesión, llega a /tenants y ve la tabla      3771 ms   1-tenants-plataforma.png
   PASA  Administrador del tenant: inicia sesión, ve los conteos y la lista de solicitudes,   8345 ms   2-solicitudes-tenant.png
         cancela con motivo la solicitud de un cliente nuevo de la corrida y la fila queda             3-dialogo-cancelacion.png
         «Cancelado» (SCRUM-477)                                                                       4-solicitud-cancelada.png
   PASA  Un cliente no entra al panel: aviso de que use la app móvil                         5161 ms

2. App móvil (quickpatch-mobile integration_test/humo_qa_test.dart, emulador Android 16, AVD quickpatch)
   flutter test integration_test/humo_qa_test.dart --dart-define-from-file=config/qa.json → All tests passed (15 s)

   PASA  Pantalla de inicio de sesión                                1089 ms
   PASA  Inicio de sesión del cliente (Identity)                     1418 ms
   PASA  Formulario con las categorías de Catalog                     207 ms
   PASA  «¿Es aquí?» con la dirección ubicada (Nominatim de QA)       314 ms
   PASA  Solicitud creada y detalle abierto (Buscando técnico)        339 ms
   PASA  Diálogo de cancelación                                       260 ms
   PASA  Solicitud cancelada con su motivo                            489 ms

Fallos encontrados y su causa
-----------------------------
- App: el APK de QA no se conectaba a nada (HandshakeException). VM1 regeneró su certificado el 16 de octubre y
  config/qa.json seguía fijando la huella anterior. Corregido en quickpatch-mobile#29; hay que sacar release/0.4.1 para
  que el APK descargable funcione.
- Datos de QA: el tenant principal tiene 195.939 solicitudes (172.196 en espera, 85.544 creadas el 19 de octubre). Las
  crea el job «Carga (k6)» de pruebas-sistema.yml: stress-test-150vu.js crea ~40.000 por corrida y load-test-50vu.js
  ~2.800. Las de hoy salen de dos corridas de ese workflow lanzadas para la SCRUM-478. Se identifican por la descripción
  («Estrés pico 150 VU…», «Solicitud de carga k6…»). Pendiente: limpiarlas en QA y que k6 no cree solicitudes en el
  tenant compartido.
- Aviso en tiempo real: el canal de Communication en QA autentica pero no entrega avisos (en diagnóstico con DevOps).
  No afecta esta prueba: la app consulta el detalle cada 30 s cuando el canal no envía nada.
