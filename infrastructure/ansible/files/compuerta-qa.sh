#!/usr/bin/env bash
# Compuerta de producción (RNF-08, SAD 2.2; SCRUM-415). La instala deploy-runner.yml en VM1 como
# /usr/local/bin/compuerta-qa y la llama el job `desplegar` de cada repositorio antes de tocar producción.
#
# Producción solo recibe una versión que:
#   1. está desplegada hoy en QA (la misma imagen, o el mismo build del panel), y
#   2. pasó las pruebas de sistema contra QA: la última ejecución de pruebas-sistema.yml del repositorio
#      quickpatch terminó en éxito y empezó DESPUÉS de que esa versión llegó a QA.
#
# Uso:
#   compuerta-qa servicio <deployment> <imagen>      p. ej. compuerta-qa servicio catalog ghcr.io/...:t-abc
#   compuerta-qa panel <carpeta-del-build>           compara con el panel que sirve el gateway de QA (VM2:/opt/quickpatch/gateway/panel)
#
# Variables:
#   GH_TOKEN                token de Actions para leer las ejecuciones (el repositorio quickpatch es público)
#   COMPUERTA_EXCEPCION     si trae texto, deja pasar con un aviso: excepción registrada al RNF-08 (por ejemplo,
#                           "release 0.2.0: QA sin datos, aprobada por el equipo el 7 de octubre"). Vacía, bloquea.
#   KUBECONFIG_QA           por omisión ~/.kube/config-qa (lo deja deploy-runner.yml)
#   PANEL_QA_SSH            usuario@host de la VM que sirve el panel de QA (por omisión quickpatch@VM2, con la llave del runner).
#                           Vacío: la carpeta PANEL_QA es de este mismo equipo.
set -euo pipefail

REPO_PRUEBAS="${REPO_PRUEBAS:-ARQUI-202630/quickpatch}"
WORKFLOW_PRUEBAS="${WORKFLOW_PRUEBAS:-pruebas-sistema.yml}"
KUBECONFIG_QA="${KUBECONFIG_QA:-$HOME/.kube/config-qa}"
PANEL_QA="${PANEL_QA:-/opt/quickpatch/gateway/panel}"
PANEL_QA_SSH="${PANEL_QA_SSH-quickpatch@10.43.98.15}"
NS="${NS:-quickpatch}"

falla() {
  if [ -n "${COMPUERTA_EXCEPCION:-}" ]; then
    echo "::warning::Compuerta RNF-08 omitida por excepción registrada: ${COMPUERTA_EXCEPCION}. Motivo del bloqueo: $1"
    exit 0
  fi
  echo "::error::Compuerta RNF-08: $1"
  exit 1
}

modo="${1:-}"
case "$modo" in
  servicio)
    deployment="${2:?falta el Deployment}"
    imagen="${3:?falta la imagen}"
    actual=$(kubectl --kubeconfig "$KUBECONFIG_QA" -n "$NS" get deployment "$deployment" \
      -o jsonpath='{.spec.template.spec.containers[0].image}') \
      || falla "no se pudo leer el Deployment '$deployment' en QA."
    [ "$actual" = "$imagen" ] \
      || falla "QA corre $actual y a producción va $imagen: esta versión no está desplegada en QA."
    revision=$(kubectl --kubeconfig "$KUBECONFIG_QA" -n "$NS" get deployment "$deployment" \
      -o jsonpath='{.metadata.annotations.deployment\.kubernetes\.io/revision}')
    # El ReplicaSet de la revisión actual dice desde cuándo corre esta imagen en QA.
    en_qa_desde=$(kubectl --kubeconfig "$KUBECONFIG_QA" -n "$NS" get replicasets -o json | jq -r \
      --arg d "$deployment" --arg r "$revision" \
      '.items[] | select(any(.metadata.ownerReferences[]?; .name == $d) and .metadata.annotations["deployment.kubernetes.io/revision"] == $r) | .metadata.creationTimestamp' \
      | head -n 1)
    [ -n "$en_qa_desde" ] || falla "no se encontró el ReplicaSet de la revisión $revision de '$deployment' en QA."
    ;;
  panel)
    build="${2:?falta la carpeta del build}"
    huella_cmd="find . -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum | cut -d' ' -f1"
    # El panel de QA lo sirve el gateway de QA en VM2 (SCRUM-573): se lee por SSH con la llave del runner.
    en_qa() { if [ -n "$PANEL_QA_SSH" ]; then ssh -o BatchMode=yes -o ConnectTimeout=10 "$PANEL_QA_SSH" "$1"; else bash -c "$1"; fi; }
    huella_build=$(cd "$build" && bash -c "$huella_cmd")
    huella_qa=$(en_qa "cd '$PANEL_QA' && $huella_cmd") || falla "no se pudo leer $PANEL_QA en ${PANEL_QA_SSH:-este equipo}."
    [ "$huella_build" = "$huella_qa" ] \
      || falla "el panel de QA no es este build: publícalo primero en QA (release/*)."
    ultimo=$(en_qa "find '$PANEL_QA' -type f -printf '%T@\\n'" | sort -n | tail -n 1) || falla "no se pudo leer la fecha del panel de QA."
    en_qa_desde=$(date -u -d "@$ultimo" +%Y-%m-%dT%H:%M:%SZ)
    ;;
  *)
    echo "Uso: compuerta-qa servicio <deployment> <imagen> | compuerta-qa panel <carpeta-del-build>" >&2
    exit 2
    ;;
esac

# Última ejecución terminada de las pruebas de sistema contra QA.
ejecucion=$(curl -fsS -H "Authorization: Bearer ${GH_TOKEN:?falta GH_TOKEN}" -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/${REPO_PRUEBAS}/actions/workflows/${WORKFLOW_PRUEBAS}/runs?status=completed&per_page=1") \
  || falla "no se pudo consultar ${WORKFLOW_PRUEBAS} en ${REPO_PRUEBAS}."
conclusion=$(jq -r '.workflow_runs[0].conclusion // "ninguna"' <<<"$ejecucion")
inicio=$(jq -r '.workflow_runs[0].run_started_at // ""' <<<"$ejecucion")
url=$(jq -r '.workflow_runs[0].html_url // ""' <<<"$ejecucion")

[ "$conclusion" = "success" ] \
  || falla "la última ejecución de las pruebas de sistema contra QA terminó en '$conclusion' ($url)."
# Fechas ISO 8601 en UTC: se comparan como texto.
if [ -z "$inicio" ] || [[ ! "$inicio" > "$en_qa_desde" ]]; then
  falla "las pruebas de sistema ($inicio, $url) son anteriores a la llegada de esta versión a QA ($en_qa_desde): hay que correrlas de nuevo."
fi

echo "::notice::Compuerta RNF-08 superada: la versión está en QA desde $en_qa_desde y las pruebas de sistema pasaron después ($inicio, $url)."
