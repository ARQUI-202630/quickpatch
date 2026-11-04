# Capturas de la recuperación de contraseña en QA (SCRUM-623, REC-023 a REC-025)

Tomadas el 4 de noviembre de 2026 contra QA (`qa.quickpatch.internal`):
- **App:** APK `v0.5.4-qa` de GitHub Releases, en un emulador Android, con capturas por `adb`.
- **Panel:** `release/0.5.5`, con Edge controlado por Playwright y el administrador del tenant principal.

La cuenta es un cliente creado solo para estas capturas (`rec.capturas.31416@quickpatch.test`). Su clave inicial y la nueva se generaron al vuelo y no se guardaron. El enlace que se ve en `panel-2` ya se usó, así que no sirve.

## App (REC-023)

| Archivo | Qué muestra |
|---|---|
| `app-1-inicio-sesion.png` | Inicio de sesión con «¿Olvidaste tu contraseña?». |
| `app-2-formulario.png` | Formulario «Recupera tu contraseña». |
| `app-3-correo-existente.png` | Pedido con el correo de la cuenta: «Recibimos tu solicitud». |
| `app-4-correo-inexistente.png` | Pedido con un correo que no existe: el mismo mensaje, para no revelar quién está registrado. |
| `app-5-entra-clave-nueva.png` | Después del paso 5 del panel, el cliente entra a la app con la clave nueva. |

## Panel (REC-024 y REC-025)

| Archivo | Qué muestra |
|---|---|
| `panel-1-bandeja.png` | «Recuperar contraseñas» del administrador, con la solicitud del cliente. |
| `panel-2-enlace-generado.png` | Enlace de un solo uso que vence en 1 hora, con «Copiar enlace». |
| `panel-3-pagina-enlace.png` | Página del enlace: «Define tu contraseña nueva». |
| `panel-4-clave-corta.png` | Validación de la longitud: «Usa entre 8 y 128 caracteres». |
| `panel-5-clave-actualizada.png` | «Tu contraseña quedó actualizada», que remite a la app. |
| `panel-6-enlace-usado.png` | El mismo enlace por segunda vez: «Este enlace ya no sirve» (REC-014 en pantalla). |

Después del paso 5, la solicitud ya no aparece en la bandeja (REC-019).
