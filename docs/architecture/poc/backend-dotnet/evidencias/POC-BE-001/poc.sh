#!/usr/bin/env bash
# POC-BE-001: ServiceRequest (.NET 10) -> Kafka -> Matching (Spring Boot 4.1.1)
set -u
S="$(cd "$(dirname "$0")" && pwd)"
SR=http://localhost:8081
b64url() { openssl base64 -A | tr '+/' '-_' | tr -d '='; }
sqlsr() { docker exec poc-pg psql -U postgres -d db_service_request -tAc "$1"; }
sqlmt() { docker exec poc-pg psql -U postgres -d db_matching -tAc "$1"; }
produce() { printf '%s|%s\n' "$2" "$3" | docker exec -i poc-kafka kafka-console-producer --bootstrap-server localhost:29092 --topic "$1" --property parse.key=true --property key.separator='|' 2>/dev/null; }
uuid() { python -c "import uuid;print(uuid.uuid4())"; }
wait_for() { local i; for i in $(seq 1 "$2"); do [ "$(eval "$1")" = "$3" ] && return 0; sleep 1; done; return 1; }

TENANT=$(uuid); CLIENT=$(uuid); CATEGORY=$(uuid)
now=$(date +%s)
header=$(printf '{"alg":"RS256","typ":"JWT"}' | b64url)
payload=$(printf '{"sub":"%s","tenant_id":"%s","role":"cliente","iss":"quickpatch-identity","aud":"quickpatch","iat":%d,"exp":%d,"jti":"%s"}' "$CLIENT" "$TENANT" "$now" $((now+3600)) "$(uuid)" | b64url)
sig=$(printf '%s.%s' "$header" "$payload" | openssl dgst -sha256 -sign "$S/priv.pem" | b64url)
TOKEN="$header.$payload.$sig"

echo "== Preparación: categoría publicada por Catalog (catalog.category-changed) =="
produce catalog.category-changed "$CATEGORY" "{\"eventId\":\"$(uuid)\",\"eventType\":\"catalog.category-changed\",\"eventVersion\":1,\"occurredAt\":\"2026-10-06T20:00:00Z\",\"correlationId\":\"$(uuid)\",\"tenantId\":\"$TENANT\",\"producer\":\"catalog-service\",\"data\":{\"categoryId\":\"$CATEGORY\",\"name\":\"Plomería\",\"active\":true,\"updatedAt\":\"2026-10-06T20:00:00Z\"}}"
wait_for "sqlsr \"select count(*) from service_request_categories where category_id='$CATEGORY'\"" 60 1 && echo "réplica de la categoría creada en ServiceRequest"

crear() {
  curl -s -o "$S/resp.json" -w "%{http_code}" -X POST "$SR/v1/service-requests" -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" -H "X-Correlation-Id: $1" \
    -d "{\"categoryId\":\"$CATEGORY\",\"description\":\"$2\",\"location\":{\"latitude\":4.6533,\"longitude\":-74.0836},\"addressText\":\"Calle 45 # 13-20, apto 301\"}"
}

echo; echo "== C1 Interoperabilidad, tenant y correlationId =="
CORR1=$(uuid); t0=$(date +%s%3N)
code=$(crear "$CORR1" "Fuga de agua debajo del lavaplatos"); SR1=$(grep -o '"id":"[^"]*"' "$S/resp.json" | head -1 | cut -d'"' -f4)
echo "POST /v1/service-requests -> $code, id=$SR1"
EV1=$(sqlsr "select id from outbox_events where aggregate_id='$SR1'")
wait_for "sqlmt \"select count(*) from processed_events where event_id='$EV1'\"" 30 1 && t1=$(date +%s%3N)
echo "eventId (outbox ServiceRequest) = $EV1"
echo "processed_events en Matching: $(sqlmt "select event_id||' tenant='||tenant_id||' tipo='||event_type from processed_events where event_id='$EV1'")"
echo "tenant del token = $TENANT"
echo "latencia POST -> registrado en Matching: $((t1-t0)) ms"
echo "log de Matching con el mismo correlationId: $(grep -c "$CORR1" "$S/matching.log") línea(s)"

echo; echo "== C3 Duplicado por eventId =="
P1=$(sqlsr "select payload::text from outbox_events where id='$EV1'")
produce service-request.created "$SR1" "$P1"
sleep 4
echo "processed_events con $EV1: $(sqlmt "select count(*) from processed_events where event_id='$EV1'")"
echo "Matching registró DUPLICATE: $(grep -c "$EV1: DUPLICATE" "$S/matching.log")"

echo; echo "== C6 Contrato inválido =="
produce service-request.created "x" "esto no es json"
produce service-request.created "y" "{\"eventId\":\"$(uuid)\",\"eventType\":\"service-request.created\",\"eventVersion\":1,\"occurredAt\":\"2026-10-06T20:00:00Z\",\"correlationId\":\"$(uuid)\",\"tenantId\":\"$TENANT\",\"producer\":\"service-request-service\",\"data\":{\"serviceRequestId\":\"$(uuid)\"}}"
sleep 4
echo "mensajes descartados por Matching: $(grep -c "descartado" "$S/matching.log")"

echo; echo "== C4/C5 Kafka caído y recuperación =="
docker stop poc-kafka >/dev/null; echo "Kafka detenido"
CORR2=$(uuid); code=$(crear "$CORR2" "Cambio de chapa de la puerta principal"); SR2=$(grep -o '"id":"[^"]*"' "$S/resp.json" | head -1 | cut -d'"' -f4)
echo "POST con Kafka caído -> $code, id=$SR2"
sleep 8
EV2=$(sqlsr "select id from outbox_events where aggregate_id='$SR2'")
echo "outbox con Kafka caído: $(sqlsr "select 'published_at='||coalesce(published_at::text,'NULL')||' attempts='||attempts from outbox_events where id='$EV2'")"
docker start poc-kafka >/dev/null; t0=$(date +%s); echo "Kafka iniciado de nuevo"
wait_for "sqlmt \"select count(*) from processed_events where event_id='$EV2'\"" 120 1 && t1=$(date +%s)
echo "outbox después: $(sqlsr "select 'published_at='||coalesce(published_at::text,'NULL')||' attempts='||attempts from outbox_events where id='$EV2'")"
echo "Matching registró $EV2: $(sqlmt "select count(*) from processed_events where event_id='$EV2'") (recuperación en $((t1-t0)) s desde que Kafka volvió)"
echo "eventos perdidos: $(sqlsr "select count(*) from outbox_events where published_at is null")"
