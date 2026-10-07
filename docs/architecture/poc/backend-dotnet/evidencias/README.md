# Evidencias POC-BE-001

Guardar únicamente resultados reales: logs, estados controlados de Outbox/processed_events, versiones y comandos de reproducción. No guardar secretos ni datos sensibles.

## POC-BE-001 (6 de octubre de 2026)

- `POC-BE-001/poc.sh`: script de los casos C1 a C6. Requiere los dos servicios corriendo (ServiceRequest en `:8081`, Matching en `:8082`), los contenedores `poc-pg` y `poc-kafka`, y un par de llaves RSA de prueba (`priv.pem`, `pub.pem`) generado con `openssl genrsa` junto al script. Las llaves no se versionan.
- `POC-BE-001/resultado.txt`: salida de la ejecución. Los UUID son aleatorios de esa corrida; no hay datos personales.
