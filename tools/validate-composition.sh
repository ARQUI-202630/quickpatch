#!/usr/bin/env bash
set -euo pipefail

required=(
  apps/web
  apps/mobile
  apps/backend/services/identity
  apps/backend/services/actors
  apps/backend/services/catalog
  apps/backend/services/service-request
  apps/backend/services/matching
  apps/backend/services/ranking
  apps/backend/services/payments
  apps/backend/services/communication
  contracts
  infrastructure
)

for p in "${required[@]}"; do

  git config -f .gitmodules \
    --get-regexp '^submodule\..*\.path$' \
    | grep -Fq " $p" || {
      echo "Falta submódulo principal: $p"
      exit 1
    }

done

consumers=(
  apps/web
  apps/mobile
  apps/backend/services/*
)

for p in "${consumers[@]}"; do

  if [ ! -f "$p/.gitmodules" ]; then
    echo "Falta contracts/ en $p"
    exit 1
  fi

  git -C "$p" config \
    -f .gitmodules \
    --get-regexp '^submodule\..*\.path$' \
    | grep -Fq ' contracts' || {
      echo "Falta contracts/ en $p"
      exit 1
    }

  tag=$(
    git -C "$p/contracts" \
      describe --tags --exact-match \
      2>/dev/null || true
  )

  if [ -z "$tag" ]; then
    echo "$p/contracts no está en una versión etiquetada."
    exit 1
  fi

  echo "$p -> contracts $tag"

done

git submodule status --recursive
