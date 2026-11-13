#!/usr/bin/env python3
"""SCRUM-649: verifica que la medición de acoplamiento y cohesión compara lo que dice comparar.

Lee los commits «antes» y «después» de docs/architecture/codigo/<fase>/<servicio>/metricas.json
(salida de tools/arquitectura/generar.py) y, sobre el historial de `develop` de cada servicio:

1. «antes» es un ancestro de «después» (las dos fases miden la misma línea de develop);
2. ningún PR de refactor del cierre (SCRUM-647: SCRUM-650 a SCRUM-657) entró antes de «antes»
   (la línea base es anterior al primer PR de refactor);
3. lista los PR mezclados entre «antes» y «después», para ver qué explica el cambio
   (refactor, código compartido de ADR-020 u otras funcionalidades);
4. dice si «después» sigue siendo la punta de develop o si develop ya avanzó.

Uso (desde la raíz del superproyecto; solo lee):
    python tests/mantenibilidad/verificar_linea_base.py
    python tests/mantenibilidad/verificar_linea_base.py --repos /tmp/servicios --json

Sale con 1 si alguna línea base no cumple 1 o 2.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
CODIGO = RAIZ / "docs" / "architecture" / "codigo"
ORG = "https://github.com/ARQUI-202630"
SERVICIOS = ["identity", "catalog", "service-request", "matching", "ranking", "payments", "communication"]
# Subtareas de la historia SCRUM-647 (refactor interno) y SCRUM-657 (código transversal, ADR-020).
REFACTOR_CIERRE = {f"SCRUM-{n}" for n in range(650, 658)}
RE_MERGE = re.compile(r"^Merge pull request #(\d+) from [^/]+/(\S+)")
RE_SCRUM = re.compile(r"SCRUM-\d+", re.IGNORECASE)


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *args], check=check, capture_output=True, text=True)


def preparar(carpeta: Path, servicio: str) -> Path:
    repo = carpeta / f"{servicio}.git"
    if not repo.exists():
        subprocess.run(["git", "clone", "-q", "--bare", "--filter=blob:none",
                        f"{ORG}/quickpatch-{servicio}.git", str(repo)], check=True)
    return repo


def prs(repo: Path, rango: str) -> list[dict]:
    salida = git(repo, "log", rango, "--first-parent", "--merges", "--reverse",
                 "--format=%h%x1f%ad%x1f%s%x1f%b%x1e", "--date=short").stdout
    res = []
    for bloque in salida.split("\x1e"):
        bloque = bloque.strip()
        if not bloque:
            continue
        sha, fecha, asunto, cuerpo = (bloque.split("\x1f") + ["", "", "", ""])[:4]
        m = RE_MERGE.match(asunto)
        if not m:
            continue
        titulo = cuerpo.strip().splitlines()[0] if cuerpo.strip() else ""
        ids = {i.upper() for i in RE_SCRUM.findall(titulo + " " + m.group(2))}
        res.append({"sha": sha, "fecha": fecha, "pr": int(m.group(1)), "titulo": titulo,
                    "refactor_cierre": bool(ids & REFACTOR_CIERRE)})
    return res


def verificar(carpeta: Path) -> list[dict]:
    filas = []
    for s in SERVICIOS:
        antes = json.loads((CODIGO / "antes" / s / "metricas.json").read_text(encoding="utf-8"))["commit"]
        despues = json.loads((CODIGO / "despues" / s / "metricas.json").read_text(encoding="utf-8"))["commit"]
        repo = preparar(carpeta, s)
        es_ancestro = git(repo, "merge-base", "--is-ancestor", antes, despues, check=False).returncode == 0
        previos = [p for p in prs(repo, antes) if p["refactor_cierre"]]
        entre = prs(repo, f"{antes}..{despues}")
        despues_de = prs(repo, f"{despues}..develop")
        filas.append({
            "servicio": s, "antes": antes, "despues": despues,
            "fecha_antes": git(repo, "log", "-1", "--format=%ad", "--date=short", antes).stdout.strip(),
            "antes_es_ancestro_de_despues": es_ancestro,
            "refactors_antes_de_la_linea_base": previos,
            "prs_entre_antes_y_despues": entre,
            "prs_en_develop_despues_de_la_medicion": despues_de,
            "ok": es_ancestro and not previos,
        })
    return filas


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repos", help="carpeta con clones <servicio>.git (si no, usa una temporal)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.repos:
        Path(a.repos).mkdir(parents=True, exist_ok=True)
        filas = verificar(Path(a.repos))
    else:
        with tempfile.TemporaryDirectory() as tmp:
            filas = verificar(Path(tmp))

    if a.json:
        print(json.dumps(filas, ensure_ascii=False, indent=2))
    else:
        for f in filas:
            estado = "OK" if f["ok"] else "REVISAR"
            print(f"{f['servicio']:<16} antes {f['antes']} ({f['fecha_antes']}) -> después {f['despues']}: {estado}")
            for p in f["prs_entre_antes_y_despues"]:
                marca = "refactor" if p["refactor_cierre"] else "otro    "
                print(f"    {marca} #{p['pr']} {p['fecha']} {p['titulo']}")
            if f["prs_en_develop_despues_de_la_medicion"]:
                print(f"    develop avanzó {len(f['prs_en_develop_despues_de_la_medicion'])} PR después de la medición")
    return 0 if all(f["ok"] for f in filas) else 1


if __name__ == "__main__":
    sys.exit(main())
