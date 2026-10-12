#!/usr/bin/env bash
# Valida la composición del multirepo (SCRUM-333): los 12 repositorios de la solución como
# submódulos del repositorio principal, y los contratos de cada consumidor en una versión etiquetada.
#   - Servicios: contracts/api-gateway (REST) y contracts/kafka (eventos).
#   - Web y mobile: contracts/api-gateway (REST).
set -euo pipefail

required=(
  apps/mobile
  apps/web
  apps/api-gateway
  apps/backend/services/identity
  apps/backend/services/actors
  apps/backend/services/catalog
  apps/backend/services/service-request
  apps/backend/services/matching
  apps/backend/services/ranking
  apps/backend/services/payments
  apps/backend/services/communication
  apps/kafka
)

for p in "${required[@]}"; do
  git config -f .gitmodules --get-regexp '^submodule\..*\.path$' | grep -Eq " $p\$" || {
    echo "Falta submódulo principal: $p"
    exit 1
  }
done

# Verifica que un consumidor tenga el submódulo de contratos indicado en una versión etiquetada.
verificar() {
  local consumidor=$1 ruta=$2
  git -C "$consumidor" config -f .gitmodules --get-regexp '^submodule\..*\.path$' | grep -Fq " $ruta" || {
    echo "Falta $ruta en $consumidor"
    exit 1
  }
  local tag
  tag=$(git -C "$consumidor/$ruta" describe --tags --exact-match 2>/dev/null || true)
  if [ -z "$tag" ]; then
    echo "$consumidor/$ruta no está en una versión etiquetada."
    exit 1
  fi
  echo "$consumidor -> $ruta $tag"
}

for p in apps/web apps/mobile; do
  verificar "$p" contracts/api-gateway
done

for p in apps/backend/services/*; do
  verificar "$p" contracts/api-gateway
  verificar "$p" contracts/kafka
done

git submodule status --recursive
