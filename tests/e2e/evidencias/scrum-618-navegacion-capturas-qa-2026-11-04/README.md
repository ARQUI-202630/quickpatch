# Recorrido de navegación de la app en QA (SCRUM-618, historia SCRUM-615)

Tomadas el 4 de noviembre de 2026 contra QA (`qa.quickpatch.internal`):
- **App:** APK `v0.5.5-qa` de GitHub Releases, en un emulador Android, con capturas por `adb`.
- **Regla:** `docs/navegacion.md` de `quickpatch-mobile`, de la SCRUM-616 (PR #43 y #52) y aplicada en la SCRUM-617 (PR #44).

Las cuentas se crearon solo para este recorrido, con claves aleatorias que no se guardaron:
- un cliente, `nav.capturas.47132@quickpatch.test`;
- un técnico aprobado por el administrador del tenant, `nav.tecnico.*@quickpatch.test`.

La solicitud de la captura 16 se canceló al terminar. Al técnico no se le guardaron localidades, así que no recibe ofertas.

«Atrás» es el botón atrás de Android, y «flecha» es la flecha de la AppBar.

## Sin sesión

| Archivo | Qué muestra | Regla |
|---|---|---|
| `01-login.png` | Inicio de sesión, sin flecha. | Pantalla raíz; atrás sale de la app. |
| `02-registro-con-flecha.png` | Crear cuenta, con flecha. | Se abre con `push`; la flecha vuelve al login. |
| `03-registro-confirmar-salida.png` | Con el nombre escrito, la flecha pregunta «¿Salir sin guardar?». «Salir» vuelve al login. | Confirmación en formularios. |
| `04-registro-tecnico-con-flecha.png` | Registro de técnico o proveedor, con flecha. Atrás volvió al login. | Secundaria. |
| `05-activar-cuenta-con-flecha.png` | Activa tu cuenta, con flecha. Atrás volvió al login. | Secundaria. |
| `06-recuperar-con-flecha.png` | Recupera tu contraseña, con flecha. Atrás volvió al login. | Secundaria. |

## Cliente

| Archivo | Qué muestra | Regla |
|---|---|---|
| `07-inicio-sin-flecha.png` | Pestaña Inicio, sin flecha. | Raíz. |
| `08-solicitudes-sin-flecha.png` | Pestaña Solicitudes, sin flecha. | Raíz. |
| `09-atras-vuelve-a-inicio.png` | Atrás desde Solicitudes lleva a Inicio, sin salir de la app. | Decisión 2 del inventario. |
| `10-nueva-solicitud-con-flecha.png` | Nueva solicitud, con flecha. | Secundaria. |
| `11-nueva-solicitud-confirmar-salida.png` | Con la descripción escrita, atrás pregunta «¿Salir sin guardar?». | Confirmación en formularios. |
| `12-cuenta-sin-flecha.png` | Pestaña Cuenta, sin flecha. | Raíz. |
| `13-editar-perfil-con-flecha.png` | Editar perfil, con flecha. | Secundaria. |
| `14-editar-perfil-confirmar-salida.png` | Con el nombre cambiado, la flecha pregunta antes de descartarlo. | Confirmación en formularios. |
| `15-notificaciones-con-flecha.png` | Notificaciones, con flecha. Atrás volvió a Cuenta. | Secundaria. |
| `16-solicitud-creada-con-flecha.png` | Detalle de la solicitud recién creada (abierto con `go`), con flecha. | Acción terminal. |
| `17-atras-va-a-mis-solicitudes.png` | Atrás desde la solicitud recién creada lleva a Solicitudes, no al formulario: la solicitud no se crea dos veces. | Decisión 1 del inventario. |

## Técnico

| Archivo | Qué muestra | Regla |
|---|---|---|
| `18-tecnico-inicio-sin-flecha.png` | Inicio del técnico, sin flecha. | Raíz. |
| `19-disponibilidad-con-flecha.png` | Disponibilidad y cobertura, con flecha. | Secundaria. |
| `20-disponibilidad-confirmar-salida.png` | Con una localidad marcada sin guardar, atrás pregunta. «Salir» descartó el cambio. | Confirmación en formularios. |
| `21-pagos-recibidos-con-flecha.png` | Mis pagos (desde «Pagos recibidos» de Inicio), con flecha. | Secundaria. |
| `22-historial-con-flecha.png` | Historial (desde Cuenta), con flecha. La flecha volvió a Cuenta. | Secundaria. |
| `23-tecnico-servicios-sin-flecha.png` | Pestaña Servicios, sin flecha. Atrás llevó a Inicio. | Raíz; decisión 2. |

## Fuera de este recorrido

Estas pantallas necesitan un servicio asignado o un rol que no se armó, y las cubren las 66 pruebas de widget de `test/app/navegacion_atras_test.dart`:
- el chat, el pago, el comprobante y el servicio asignado del técnico;
- las pantallas de empresa (Usuarios de la empresa, Agregar usuario);
- las del proveedor (Equipo, Agregar técnico).

El pago aprobado que no se repite al volver también lo cubren las pruebas de widget y la colección `scrum-117-pago`.
