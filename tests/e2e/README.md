# e2e

Pruebas de sistema de QUICKPATCH contra el ambiente de QA. Las corre `.github/workflows/pruebas-sistema.yml` desde el runner de VM1 en cada `release/*` (compuerta 2 del Documento de Pruebas).

## Colección del MVP de Sprint 3

`quickpatch-mvp.postman_collection.json` recorre el flujo de punta a punta (SCRUM-27):

1. **Administrador del tenant:** inicia sesión y crea una categoría. Catalog publica `catalog.category-changed`.
2. **Cliente:** se registra, inicia sesión y ve la categoría nueva.
3. **Solicitud:** crea la solicitud. ServiceRequest valida la categoría en su réplica (si todavía no llegó, reintenta hasta 10 veces cada 2 s), la guarda en `buscando_tecnico` y publica `service-request.created`, que consume Matching. Después consulta el detalle.
4. **Casos negativos:** sin token (401), administrador creando una solicitud (403), cliente administrando categorías (403), ubicación fuera de Bogotá (422) y descripción corta (400 con el error por campo), con Problem Details y `correlationId`.

La colección se genera con `python tests/e2e/generar-coleccion.py`: se edita el script y se regenera el JSON.

### Variables

|Variable|Valor|
|---|---|
|`baseUrl`|`https://qa.quickpatch.internal` (sin `/api`; la colección lo agrega)|
|`adminEmail`, `adminPassword`|Administrador inicial de QA: el mismo `admin-email`/`admin-password` del Secret `identity-secretos`. En GitHub, secretos `QA_ADMIN_EMAIL` y `QA_ADMIN_PASSWORD` del repositorio. Nunca en la colección|

```bash
docker run --rm -v "$PWD/tests/e2e:/etc/newman" postman/newman:6-alpine run quickpatch-mvp.postman_collection.json \
  --insecure --env-var baseUrl=https://qa.quickpatch.internal --env-var adminEmail=... --env-var adminPassword=...
```

### Evidencia

`evidencias/mvp-local-2026-10-07.txt`: corrida local con los cuatro servicios reales (Identity, Catalog, ServiceRequest y Matching), PostgreSQL+PostGIS, Kafka y un Nginx con las mismas rutas del gateway. Resultado: 13 peticiones y 18 aserciones sin fallos. Se verificó además en la base que el Outbox publicó `service-request.created` y que Matching lo registró en `processed_events`.

## Orden del despliegue del MVP en QA

1. Infraestructura de QA (Ansible): bases `db_<servicio>` con su `_migrator` y su `_app`, PostGIS en `db_service_request` y `db_matching`, Redis, Kafka con los topics de `quickpatch-kafka/topics/topics.yaml` y Garage.
2. Secretos de Kubernetes de cada servicio (`deploy/k8s/README.md` de Identity, Catalog, ServiceRequest y Matching). Un solo par de llaves RSA: la privada para Identity y la pública para los demás.
3. `kubectl apply -f deploy/k8s/<servicio>.yaml` en cada repositorio.
4. Rama `release/*` en cada servicio: el pipeline publica la imagen y la despliega en QA; los init containers aplican las migraciones.
5. Solo la primera vez: `db/roles.sql` de cada servicio, el alta del tenant (`identity/db/seed-tenant.example.sql`) y `kubectl -n quickpatch rollout restart deployment` para que Identity cree el administrador inicial.
6. Rama `release/*` en este repositorio: corre esta colección contra QA.
7. App móvil: `config/qa.json` con la huella del certificado de VM1 (`quickpatch-mobile`, README).
