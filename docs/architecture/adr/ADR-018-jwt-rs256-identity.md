# ADR-018 — Tokens JWT firmados con RS256 solo por Identity

- **Estado:** Aceptado
- **Fecha:** 5 de octubre de 2026 (SCRUM-63)
- **Decisión:** Identity es el único servicio que emite tokens y el único que tiene la llave privada; los demás servicios validan los tokens localmente con la llave pública
- **Atributo priorizado:** AC6 Security (Authenticity, Confidentiality)
- **Atributo sacrificado:** AC7 Maintainability (gestión y rotación de un par de llaves) y revocación inmediata de tokens
- **Drivers y killers:** D5 (multi-tenancy), K12 (protección de datos personales)
- **Implementación:** `quickpatch-identity` (emisor) y cada servicio que expone REST (validador)

## Contexto

Todos los servicios necesitan saber quién hace la petición, de qué tenant es y con qué rol (RBAC, DD 10.5). Si cada servicio consultara a Identity en cada petición, Identity quedaría en el camino crítico de todo el sistema (contra ADR-003). Si se firmara con una clave simétrica (HS256) compartida, cualquier servicio comprometido podría emitir tokens válidos para cualquier tenant y rol.

## Decisión

- **RS256**: Identity firma con la llave privada; los demás servicios reciben solo la llave pública (`Jwt__PublicKeyPem`) y validan firma, `iss`, `aud` y `exp` sin llamar a Identity.
- Claims: `sub` (usuario), `tenant_id`, `role`, `iss`, `aud`, `exp` y `jti`. El **tenant de toda operación sale del claim `tenant_id`**, nunca del cuerpo de la petición (ADR-005).
- Vida corta del token de acceso (`expiresIn` en la respuesta del login).
- Identity no arranca si falta la llave privada o es inválida (validación al inicio), en lugar de fallar en el primer login.
- Las llaves se entregan como secretos de Kubernetes desde Ansible Vault; ninguna llave real entra a los repositorios.

## Alternativas descartadas

- **HS256 con un secreto compartido:** más simple, pero cualquier servicio con el secreto puede falsificar tokens; viola el principio de mínimo privilegio.
- **Tokens opacos con introspección en Identity:** revocación inmediata, pero una llamada a Identity por cada petición (latencia y acoplamiento).
- **Proveedor de identidad externo (Auth0, Cognito, Keycloak administrado):** viola R5; un Keycloak propio agregaría otro componente pesado que operar (R10, R11).

## Consecuencias

### Positivas
- Un servicio comprometido no puede emitir tokens.
- La validación es local y no depende de que Identity esté arriba.
- La misma llave pública sirve para todos los servicios y para el gateway.

### Costos
- Un token emitido sigue siendo válido hasta que expira: por ejemplo, un tenant desactivado puede seguir operando con un token emitido antes de la desactivación (brecha registrada frente a RN-T1). Se mitiga con vida corta del token; si no basta, hará falta una lista de revocación o la verificación del estado del tenant por evento.
- La rotación de llaves exige distribuir la nueva llave pública antes de firmar con la nueva privada (pendiente: publicar las llaves con `kid`/JWKS).

## Evidencia

- Identity emite tokens RS256 y rechaza el arranque sin llave (PR #4 de `quickpatch-identity`).
- ServiceRequest y Catalog validan los tokens con la llave pública; las pruebas cubren petición sin token, token alterado, token expirado y token sin `tenant_id` (401).

## Trazabilidad

- DD: sección de claims del token y matriz de roles (10.5).
- Contratos: `openapi/identity.v1.yaml` (`/v1/auth/login`).
- Relacionados: ADR-003, ADR-005.
