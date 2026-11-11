#!/usr/bin/env python3
"""Compara dos fases de `generar.py` (por defecto antes y despues) y escribe la tabla en docs/architecture/codigo/.

Uso: python tools/arquitectura/comparar.py [--antes antes] [--despues despues]
"""
import argparse
import json
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
CODIGO = RAIZ / "docs" / "architecture" / "codigo"
SERVICIOS = ["identity", "catalog", "service-request", "matching", "ranking", "payments", "communication"]
METRICAS = [
    ("violaciones_de_capas", "Violaciones de SDD 10.3.2", "menos"),
    ("ciclos_entre_paquetes", "Ciclos entre paquetes", "menos"),
    ("ciclos_entre_tipos", "Ciclos entre tipos", "menos"),
    ("tipos_de_mas_de_250_lineas", "Tipos de más de 250 líneas", "menos"),
    ("fan_out_maximo", "Fan-out máximo¹", "menos"),
    ("dependencias_entre_paquetes", "Dependencias entre paquetes", "menos"),
    ("cohesion_relacional_promedio", "Cohesión relacional promedio (H)", "mas"),
    ("tipos", "Tipos", None),
]


def flecha(a, d, sentido):
    if a == d or sentido is None:
        return "="
    mejora = (d < a) if sentido == "menos" else (d > a)
    return "mejora" if mejora else "empeora"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--antes", default="antes")
    ap.add_argument("--despues", default="despues")
    a = ap.parse_args()
    l = [f"# Dependencias desde el código — {a.antes} y {a.despues} del refactor",
         "",
         f"Comparación generada el {date.today().isoformat()} con `python tools/arquitectura/comparar.py`, a partir de "
         f"[`{a.antes}/`]({a.antes}/README.md) y [`{a.despues}/`]({a.despues}/README.md). Las dos mediciones usan la misma "
         "herramienta y la misma configuración (`tools/arquitectura/generar.py`, SCRUM-681).",
         ""]
    filas_resumen = []
    for s in SERVICIOS:
        fa, fd = CODIGO / a.antes / s / "metricas.json", CODIGO / a.despues / s / "metricas.json"
        if not (fa.exists() and fd.exists()):
            continue
        ma, md = json.loads(fa.read_text(encoding="utf-8")), json.loads(fd.read_text(encoding="utf-8"))
        ra, rd = ma["resumen"], md["resumen"]
        mismo = ma.get("commit") == md.get("commit")
        filas_resumen.append((md["servicio"], ma.get("commit"), md.get("commit"), mismo, ra, rd))
    l += ["## Resumen", "",
          "| Servicio | Commit antes | Commit después | Violaciones | Ciclos paquetes | Tipos > 250 líneas | Fan-out máx.¹ | Cohesión H |",
          "|---|---|---|---|---|---|---|---|"]
    for n, ca, cd, mismo, ra, rd in filas_resumen:
        def c(k):
            return f"{ra[k]} → {rd[k]}"
        nota = " (sin refactor integrado)" if mismo else ""
        l.append(f"| {n}{nota} | `{ca}` | `{cd}` | {c('violaciones_de_capas')} | {c('ciclos_entre_paquetes')} | "
                 f"{c('tipos_de_mas_de_250_lineas')} | {c('fan_out_maximo')} | {c('cohesion_relacional_promedio')} |")
    l += ["", "1. Sin las raíces de composición (`Program` y `DependencyInjection`).", ""]
    for n, ca, cd, mismo, ra, rd in filas_resumen:
        l += [f"## {n}", ""]
        if mismo:
            l += ["Mismo commit en las dos mediciones: el refactor de este servicio todavía no está en `develop`.", ""]
            continue
        l += ["| Métrica | Antes | Después | Resultado |", "|---|---|---|---|"]
        for k, etiqueta, sentido in METRICAS:
            l.append(f"| {etiqueta} | {ra[k]} | {rd[k]} | {flecha(ra[k], rd[k], sentido)} |")
        l.append("")
    (CODIGO / "README.md").write_text("\n".join(l), encoding="utf-8")
    print((CODIGO / "README.md"))


if __name__ == "__main__":
    main()
