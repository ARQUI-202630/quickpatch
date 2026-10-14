#!/usr/bin/env bash
# Genera el extracto de OpenStreetMap solo con Bogotá que importa Nominatim (SCRUM-454, ADR-024).
# Descarga Colombia de Geofabrik y lo recorta al rectángulo de cobertura del MVP (RN-SR9 del DD: latitud 4,45 a 4,85 y longitud
# -74,25 a -73,98) con osmium. Las VMs no hacen este paso: el playbook deploy-nominatim.yml copia el resultado.
#
#   tools/nominatim-extracto.sh [carpeta-de-trabajo]     (por defecto ./.cache-nominatim; con Docker Desktop debe estar en /mnt/c)
#
# Deja bogota.osm.pbf y bogota.osm.pbf.sha256 en la carpeta de trabajo. Cópialos a infrastructure/ansible/files/nominatim/.
set -euo pipefail
TRABAJO="${1:-$PWD/.cache-nominatim}"
BBOX="-74.25,4.45,-73.98,4.85"      # lon_min,lat_min,lon_max,lat_max
URL="https://download.geofabrik.de/south-america/colombia-latest.osm.pbf"
mkdir -p "$TRABAJO"
if [ ! -f "$TRABAJO/colombia-latest.osm.pbf" ]; then
  curl -L --fail -A "quickpatch-infra (sebastiansanchez3004@gmail.com)" -o "$TRABAJO/colombia-latest.osm.pbf" "$URL"
fi
docker run --rm -v "$TRABAJO":/datos ubuntu:24.04 bash -c "
  set -e
  apt-get update -qq && apt-get install -y -qq osmium-tool >/dev/null
  osmium extract --bbox $BBOX --strategy complete_ways --overwrite -o /datos/bogota.osm.pbf /datos/colombia-latest.osm.pbf
  osmium fileinfo /datos/bogota.osm.pbf | grep -E 'Bounding box|Number of nodes|Number of ways|Number of relations|File size|Timestamps' || true
"
( cd "$TRABAJO" && sha256sum bogota.osm.pbf | tee bogota.osm.pbf.sha256 )
echo "Extracto: $TRABAJO/bogota.osm.pbf ($(du -h "$TRABAJO/bogota.osm.pbf" | cut -f1))"
