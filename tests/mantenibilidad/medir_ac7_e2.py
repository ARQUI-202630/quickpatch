#!/usr/bin/env python3
"""AC7-E2 (acoplamiento entre módulos): qué parte de los cambios toca un solo servicio.

Meta de la matriz de 52 escenarios: el 80 % o más de los cambios afectan un solo servicio.

Método (el mismo de tests/e2e/evidencias/ac7-mantenibilidad-e2-e3-e5-medicion-2026-11-05.md):
- Fuente: los PR mezclados en `develop` de los repositorios de servicios, leídos de los
  commits de merge («Merge pull request #N from ...») del historial de primer padre.
- Un «cambio» es un número de SCRUM, tomado del título, el cuerpo o la rama del PR.
- Se excluyen las promociones (`main`/`release/*` que vuelven a develop), los back-merge
  y los PR sin número de SCRUM.
- Se cuenta en cuántos repositorios de servicios tiene PR mezclados cada cambio.

Uso (desde la raíz del superproyecto; solo lee, no modifica ningún repositorio):
    python tests/mantenibilidad/medir_ac7_e2.py --desde 2026-10-24
    python tests/mantenibilidad/medir_ac7_e2.py --desde 2026-10-24 --por-historia
    python tests/mantenibilidad/medir_ac7_e2.py --desde 2026-11-06 --json

Clona el historial (sin archivos) de cada servicio en una carpeta temporal, o usa
--repos <carpeta> con clones `<servicio>.git` ya hechos.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

ORG = "https://github.com/ARQUI-202630"
SERVICIOS = ["identity", "actors", "catalog", "service-request", "matching", "ranking", "payments", "communication"]

RE_MERGE = re.compile(r"^Merge pull request #(\d+) from [^/]+/(\S+)")
RE_SCRUM = re.compile(r"SCRUM-(\d+)", re.IGNORECASE)
RE_TIPO = re.compile(r"^(\w+)(\([^)]*\))?!?:")
# Promociones y back-merge: no son cambios nuevos.
RE_PROMOCION = re.compile(r"^(main|release/.*|chore/main-a-develop.*)$")
RE_TEXTO_PROMOCION = re.compile(r"main vuelve a develop|back-?merge", re.IGNORECASE)


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout


def preparar(carpeta: Path, servicio: str) -> Path:
    repo = carpeta / f"{servicio}.git"
    if not repo.exists():
        subprocess.run(["git", "clone", "-q", "--bare", "--filter=blob:none",
                        f"{ORG}/quickpatch-{servicio}.git", str(repo)], check=True)
    return repo


def prs(repo: Path, desde: str, hasta: str | None):
    args = ["log", "develop", "--first-parent", "--merges", f"--since={desde}T00:00:00-05:00",
            "--format=%H%x1f%ad%x1f%s%x1f%b%x1e", "--date=short"]
    if hasta:
        args.insert(4, f"--until={hasta}T23:59:59-05:00")
    for bloque in git(repo, *args).split("\x1e"):
        bloque = bloque.strip()
        if not bloque:
            continue
        sha, fecha, asunto, cuerpo = (bloque.split("\x1f") + ["", "", "", ""])[:4]
        m = RE_MERGE.match(asunto)
        if not m:
            continue
        rama = m.group(2)
        titulo = cuerpo.strip().splitlines()[0] if cuerpo.strip() else ""
        yield {"sha": sha[:7], "fecha": fecha, "pr": int(m.group(1)), "rama": rama, "titulo": titulo}


def medir(carpeta: Path, desde: str, hasta: str | None, historias: dict[str, str] | None = None) -> dict:
    historias = historias or {}
    cambios: dict[str, dict] = defaultdict(lambda: {"servicios": set(), "tipos": set(), "prs": []})
    excluidos = {"promociones": 0, "sin_scrum": 0}
    for servicio in SERVICIOS:
        repo = preparar(carpeta, servicio)
        for pr in prs(repo, desde, hasta):
            if RE_PROMOCION.match(pr["rama"]) or RE_TEXTO_PROMOCION.search(pr["titulo"]):
                excluidos["promociones"] += 1
                continue
            ids = sorted(set(RE_SCRUM.findall(pr["titulo"] + " " + pr["rama"])), key=int)
            if not ids:
                excluidos["sin_scrum"] += 1
                continue
            tipo = RE_TIPO.match(pr["titulo"])
            tipo = tipo.group(1).lower() if tipo else "otro"
            alcance = RE_TIPO.match(pr["titulo"]).group(2) if RE_TIPO.match(pr["titulo"]) else ""
            for clave in sorted({historias.get(f"SCRUM-{i}", f"SCRUM-{i}") for i in ids}):
                c = cambios[clave]
                c["servicios"].add(servicio)
                c["tipos"].add("chore-contracts" if tipo == "chore" and alcance and "contracts" in alcance else tipo)
                c["prs"].append(f"{servicio}#{pr['pr']} ({pr['fecha']}) {pr['titulo']}")

    def resumen(filtro) -> dict:
        sel = {k: v for k, v in cambios.items() if filtro(v)}
        n = len(sel)
        uno = sum(1 for v in sel.values() if len(v["servicios"]) == 1)
        dos = sum(1 for v in sel.values() if len(v["servicios"]) == 2)
        return {"cambios": n, "un_servicio": uno, "dos": dos, "tres_o_mas": n - uno - dos,
                "pct_un_servicio": round(100 * uno / n, 1) if n else None}

    definiciones = {
        "todos": resumen(lambda v: True),
        "sin_subida_de_contratos": resumen(lambda v: v["tipos"] != {"chore-contracts"}),
        "solo_feat_y_fix": resumen(lambda v: v["tipos"] <= {"feat", "fix"}),
    }
    detalle = {k: {"servicios": sorted(v["servicios"]), "tipos": sorted(v["tipos"]), "prs": v["prs"]}
               for k, v in sorted(cambios.items(), key=lambda kv: int(kv[0].split("-")[1]))}
    return {"desde": desde, "hasta": hasta, "agrupado_por_historia": bool(historias),
            "meta_pct": 80.0, "excluidos": excluidos,
            "definiciones": definiciones, "cambios": detalle}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--desde", required=True, help="fecha inicial AAAA-MM-DD (hora de Bogotá)")
    ap.add_argument("--hasta", help="fecha final AAAA-MM-DD (incluida)")
    ap.add_argument("--repos", help="carpeta con clones <servicio>.git (si no, usa una temporal)")
    ap.add_argument("--por-historia", action="store_true",
                    help="agrupa las subtareas en su historia con tests/mantenibilidad/ac7-e2-historias.json")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    historias = None
    if a.por_historia:
        historias = {k: v for k, v in json.loads((Path(__file__).parent / "ac7-e2-historias.json")
                                                 .read_text(encoding="utf-8")).items() if not k.startswith("_")}
    if a.repos:
        carpeta = Path(a.repos)
        carpeta.mkdir(parents=True, exist_ok=True)
        r = medir(carpeta, a.desde, a.hasta, historias)
    else:
        with tempfile.TemporaryDirectory() as tmp:
            r = medir(Path(tmp), a.desde, a.hasta, historias)

    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0
    unidad = "historia" if r["agrupado_por_historia"] else "número de SCRUM del PR"
    print(f"AC7-E2 por {unidad}, desde {r['desde']} hasta {r['hasta'] or 'hoy'} (meta: {r['meta_pct']:.0f} % en un solo servicio)")
    print(f"Excluidos: {r['excluidos']['promociones']} promociones o back-merge, {r['excluidos']['sin_scrum']} PR sin SCRUM")
    for nombre, d in r["definiciones"].items():
        print(f"  {nombre:<24} {d['cambios']:>3} cambios: {d['un_servicio']} en un servicio "
              f"({d['pct_un_servicio']} %), {d['dos']} en dos, {d['tres_o_mas']} en tres o más")
    print("Cambios en más de un servicio:")
    for k, v in r["cambios"].items():
        if len(v["servicios"]) > 1:
            print(f"  {k}: {', '.join(v['servicios'])} [{', '.join(v['tipos'])}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
