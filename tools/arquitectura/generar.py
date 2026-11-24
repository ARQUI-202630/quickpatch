#!/usr/bin/env python3
"""Ingeniería inversa de los microservicios de QUICKPATCH (SCRUM-680/681/682/683).

Para cada servicio exporta la rama pedida (por defecto origin/develop) con `git archive`,
la compila y extrae las dependencias entre tipos desde el código compilado:

- .NET: `extractor-dotnet` (System.Reflection.Metadata sobre los .dll y .pdb).
- Java (Matching): `jdeps -verbose:class -filter:none` sobre target/classes.

Después calcula métricas (ciclos, fan-in/fan-out, inestabilidad, cohesión relacional,
violaciones de las reglas de dependencia del SDD 10.3.2) y escribe los diagramas de
paquetes y de clases centrales en PlantUML y Mermaid.

Uso (desde la raíz del superproyecto):
    python tools/arquitectura/generar.py --fase antes
    python tools/arquitectura/generar.py --fase despues --servicios catalog ranking

Requisitos: git, .NET SDK 10, JDK 17+ con jdeps y Maven.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from collections import defaultdict
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
SERVICIOS_DIR = RAIZ / "apps" / "backend" / "services"
DOTNET = {"identity": "Identity", "actors": "Actors", "catalog": "Catalog", "service-request": "ServiceRequest",
          "ranking": "Ranking", "payments": "Payments", "communication": "Communication"}
JAVA = {"matching": "Matching"}
TODOS = ["identity", "actors", "catalog", "service-request", "matching", "ranking", "payments", "communication"]
CAPAS = ["Api", "Application", "Domain", "Infrastructure"]

# Reglas del SDD 10.3.2: (capa origen, capa destino) prohibidas entre tipos propios.
PROHIBIDAS = {("Domain", "Application"), ("Domain", "Infrastructure"), ("Domain", "Api"),
              ("Application", "Infrastructure"), ("Application", "Api"),
              ("Infrastructure", "Api"), ("Api", "Infrastructure")}
# Raíces de composición: el único punto del API que puede conocer Infrastructure.
# Caso de uso principal de cada servicio para su diagrama de clases (C4 · Code, SCRUM-715): clase de entrada, caso de
# uso y por qué. El resto del servicio repite el patrón y está en su diagrama de componentes (C4-04).
CASOS = {
    "identity": ("AuthEndpoints", "LoginHandler", "inicio de sesión (RF-03, RN-U4, ADR-018)"),
    "actors": ("TechnicianEventsConsumer", "TechnicianEventsHandler", "proyección de technician.registered y .verification-changed (SCRUM-640)"),
    "catalog": ("CategoryEndpoints", "CreateCategoryHandler", "alta de una categoría (ADR-007, ADR-025)"),
    "service-request": ("ServiceRequestEndpoints", "CreateServiceRequestHandler", "creación de la solicitud (RF-07, RN-SR1, RN-SR9, RN-T1)"),
    "matching": ("ServiceRequestCreatedListener", "ServiceRequestCreatedHandler", "inicio del matching al crearse la solicitud (RN-M1 a RN-M10, RN-EV1)"),
    "ranking": ("ServiceRequestRatedConsumer", "ServiceRequestRatedHandler", "reputación del técnico desde la calificación (ADR-027)"),
    "payments": ("PaymentEndpoints", "PayHandler", "pago con la pasarela simulada (RF-22, ADR-009 modificado)"),
    "communication": ("ChatEndpoints", "SendChatMessageHandler", "envío de un mensaje del chat (RF-37, ADR-026)"),
}

RAICES_COMPOSICION = {"Program", "co.quickpatch.matching.MatchingApplication"}
# Tecnologías prohibidas por capa.
TECNOLOGIA = {
    "csharp": {"Domain": ["Microsoft.EntityFrameworkCore", "Npgsql", "Confluent.Kafka", "Microsoft.AspNetCore"],
               "Application": ["Microsoft.EntityFrameworkCore", "Npgsql", "Confluent.Kafka", "Microsoft.AspNetCore"],
               "Infrastructure": ["Microsoft.AspNetCore"]},
    "java": {"Domain": ["org.springframework"],
             "Application": ["org.springframework.jdbc", "org.springframework.kafka", "org.springframework.web"]},
}


def sh(cmd: list[str], cwd: Path | None = None, salida_binaria: bool = False) -> str | bytes:
    r = subprocess.run(cmd, cwd=cwd, capture_output=True)
    if r.returncode != 0:
        sys.exit(f"Falló: {' '.join(cmd)}\n{r.stdout.decode(errors='replace')[-3000:]}\n{r.stderr.decode(errors='replace')[-3000:]}")
    return r.stdout if salida_binaria else r.stdout.decode("utf-8", errors="replace")


def exportar(repo: Path, ref: str, destino: Path) -> str:
    sha = sh(["git", "-C", str(repo), "rev-parse", "--short", ref]).strip()
    tar = sh(["git", "-C", str(repo), "archive", "--format=tar", ref], salida_binaria=True)
    with tarfile.open(fileobj=io.BytesIO(tar)) as t:
        t.extractall(destino, filter="data")
    # git archive no incluye los submódulos. Desde ADR-020 los servicios .NET compilan
    # shared/dotnet (quickpatch-shared-dotnet), así que se exporta el commit que fija la referencia.
    for linea in sh(["git", "-C", str(repo), "ls-tree", "-r", ref]).splitlines():
        meta, _, ruta = linea.partition("\t")
        modo, tipo, commit = meta.split()
        if tipo != "commit":
            continue
        sub = repo / ruta
        if not (sub / ".git").exists():
            sh(["git", "-C", str(repo), "submodule", "update", "--init", "--", ruta])
        if subprocess.run(["git", "-C", str(sub), "cat-file", "-e", commit], capture_output=True).returncode != 0:
            sh(["git", "-C", str(sub), "fetch", "-q", "origin"])
        tar = sh(["git", "-C", str(sub), "archive", "--format=tar", commit], salida_binaria=True)
        with tarfile.open(fileobj=io.BytesIO(tar)) as t:
            t.extractall(destino / ruta, filter="data")
    return sha


# ---------------------------------------------------------------- extracción

def extraer_dotnet(fuente: Path, nombre: str, trabajo: Path, extractor: Path) -> dict:
    binario = trabajo / "bin"
    sh(["dotnet", "build", str(fuente / "src" / f"QuickPatch.{nombre}.Api"), "-c", "Release",
        "-o", str(binario), "-nologo", "-v", "q"])
    salida = trabajo / "extraccion.json"
    sh(["dotnet", str(extractor), str(binario), nombre, str(salida)])
    d = json.loads(salida.read_text(encoding="utf-8"))
    tipos = [{"id": t["Id"], "paquete": t["Paquete"], "capa": t["Capa"], "clase": t["Clase"],
              "lineas": t["Lineas"], "archivo": t.get("Archivo"),
              "implementa": t.get("Implementa", []), "inyecta": t.get("Inyecta", [])} for t in d["tipos"]]
    for t in tipos:
        if t["archivo"]:
            t["archivo"] = relativo(t["archivo"], fuente)
    return {"tipos": tipos, "dependencias": d["dependencias"], "externas": d["externas"]}


def relativo(ruta: str, fuente: Path) -> str:
    # Ruta dentro del repositorio del servicio: la carpeta temporal también se llama "src".
    r = ruta.replace("\\", "/")
    i = r.find("/src/QuickPatch.")
    return r[i + 1:] if i >= 0 else Path(r).name


def extraer_java(fuente: Path) -> dict:
    mvn = shutil.which("mvn") or shutil.which("mvn.cmd")
    sh([mvn, "-q", "-DskipTests", "compile"], cwd=fuente)
    jdeps = shutil.which("jdeps") or "jdeps"
    texto = sh([jdeps, "-verbose:class", "-filter:none", str(fuente / "target" / "classes")])
    base = "co.quickpatch.matching."
    tipos: dict[str, dict] = {}
    deps, externas = set(), set()

    def raiz(n: str) -> str:
        return n.split("$")[0]

    for linea in texto.splitlines():
        m = re.match(r"\s+(\S+)\s+->\s+(\S+)\s+(.*)$", linea)
        if not m:
            continue
        de, a = raiz(m.group(1)), raiz(m.group(2))
        if not de.startswith(base) or de.endswith("package-info"):
            continue
        tipos.setdefault(de, {})
        if a.startswith(base):
            if not a.endswith("package-info"):
                tipos.setdefault(a, {})
                if a != de:
                    deps.add((de, a))
        elif not a.startswith("java."):
            p = a.split(".")[:-1]
            externas.add((de, ".".join(p[:3] if p and p[0] in ("org", "com", "io") else p[:2])))

    lista = []
    for t in sorted(tipos):
        resto = t[len(base):]
        capa = {"api": "Api", "application": "Application", "domain": "Domain",
                "infrastructure": "Infrastructure"}.get(resto.split(".")[0], "Api")
        archivo = Path("src/main/java") / (t.replace(".", "/") + ".java")
        texto_fuente = (fuente / archivo).read_text(encoding="utf-8") if (fuente / archivo).exists() else ""
        simple = t.rsplit(".", 1)[-1]
        mk = re.search(rf"\b(interface|record|enum|class)\s+{re.escape(simple)}\b", texto_fuente)
        clase = {"interface": "interface", "enum": "enum"}.get(mk.group(1) if mk else "", "class")
        if mk and re.search(rf"abstract\s+class\s+{re.escape(simple)}\b", texto_fuente):
            clase = "abstract"
        lineas = sum(1 for l in texto_fuente.splitlines() if l.strip())
        lista.append({"id": t, "paquete": t.rsplit(".", 1)[0], "capa": capa, "clase": clase,
                      "lineas": lineas, "archivo": str(archivo).replace("\\", "/"), "fuente": texto_fuente})
    # Interfaces que implementa y parámetros del constructor, leídos del fuente y resueltos por nombre simple.
    # Los puertos anidados (MatchingPorts.RequestStore) se cuentan en su tipo raíz, igual que en jdeps.
    por_simple = {x["id"].rsplit(".", 1)[-1]: x["id"] for x in lista}
    resolver = lambda n: por_simple.get(n.strip().split("<")[0].split(".")[0].strip())
    for x in lista:
        simple = x["id"].rsplit(".", 1)[-1]
        fuente_x = x.pop("fuente")
        mi = re.search(rf"\b(?:class|record)\s+{re.escape(simple)}\b[^{{]*?\bimplements\s+([^{{]+)\{{", fuente_x, re.S)
        x["implementa"] = sorted({r for r in (resolver(n) for n in (mi.group(1).split(",") if mi else [])) if r})
        mc = re.search(rf"public\s+{re.escape(simple)}\s*\(([^)]*)\)", fuente_x, re.S)
        x["inyecta"] = []
        for par in (mc.group(1).split(",") if mc and mc.group(1).strip() else []):
            tipo_par = re.sub(r"@\w+(\([^)]*\))?\s*", "", par).strip().rsplit(" ", 1)[0].strip()
            x["inyecta"].append(resolver(tipo_par) or tipo_par.split("<")[0].split(".")[-1])
    return {"tipos": lista,
            "dependencias": [{"de": a, "a": b} for a, b in sorted(deps)],
            "externas": [{"de": a, "ns": b} for a, b in sorted(externas)]}


# ---------------------------------------------------------------- análisis

def tarjan(nodos: list[str], aristas: dict[str, set[str]]) -> list[list[str]]:
    indice, bajo, pila, en_pila, comps, c = {}, {}, [], set(), [], [0]
    sys.setrecursionlimit(10000)

    def visitar(v: str) -> None:
        indice[v] = bajo[v] = c[0]; c[0] += 1
        pila.append(v); en_pila.add(v)
        for w in aristas.get(v, ()):
            if w not in indice:
                visitar(w); bajo[v] = min(bajo[v], bajo[w])
            elif w in en_pila:
                bajo[v] = min(bajo[v], indice[w])
        if bajo[v] == indice[v]:
            comp = []
            while True:
                w = pila.pop(); en_pila.discard(w); comp.append(w)
                if w == v:
                    break
            if len(comp) > 1:
                comps.append(sorted(comp))

    for n in nodos:
        if n not in indice:
            visitar(n)
    return sorted(comps, key=len, reverse=True)


def es_composicion(tipo: str) -> bool:
    return tipo in RAICES_COMPOSICION or tipo.endswith(".DependencyInjection")


def analizar(servicio: str, lenguaje: str, datos: dict) -> dict:
    # El código generado por EF Core (migraciones y snapshot) no se diseña a mano: se excluye.
    tipos = {t["id"]: t for t in datos["tipos"] if ".Migrations" not in t["paquete"]}
    deps = [(d["de"], d["a"]) for d in datos["dependencias"] if d["de"] in tipos and d["a"] in tipos]
    sale, entra = defaultdict(set), defaultdict(set)
    for a, b in deps:
        sale[a].add(b); entra[b].add(a)

    paquetes = defaultdict(list)
    for t in tipos.values():
        paquetes[t["paquete"]].append(t["id"])
    pk_sale, pk_entra, pk_peso, internas = defaultdict(set), defaultdict(set), defaultdict(int), defaultdict(int)
    for a, b in deps:
        pa, pb = tipos[a]["paquete"], tipos[b]["paquete"]
        if pa == pb:
            internas[pa] += 1
        else:
            pk_sale[pa].add(pb); pk_entra[pb].add(pa); pk_peso[(pa, pb)] += 1

    ciclos_paquetes = tarjan(sorted(paquetes), pk_sale)
    ciclos_tipos = tarjan(sorted(tipos), sale)

    capas = defaultdict(int)
    violaciones = []
    for a, b in deps:
        ca, cb = tipos[a]["capa"], tipos[b]["capa"]
        if ca != cb:
            capas[f"{ca}->{cb}"] += 1
        if (ca, cb) in PROHIBIDAS and a not in RAICES_COMPOSICION:
            violaciones.append({"regla": f"{ca} no depende de {cb}", "de": a, "a": b})
    for e in datos["externas"]:
        t = tipos.get(e["de"])
        if not t:
            continue
        for prefijo in TECNOLOGIA[lenguaje].get(t["capa"], []):
            if e["ns"] == prefijo or e["ns"].startswith(prefijo + "."):
                violaciones.append({"regla": f"{t['capa']} no depende de {prefijo}", "de": e["de"], "a": e["ns"]})

    por_tipo = []
    for t in tipos.values():
        por_tipo.append({"tipo": t["id"], "capa": t["capa"], "clase": t["clase"], "lineas": t["lineas"],
                         "fan_out": len(sale[t["id"]]), "fan_in": len(entra[t["id"]]), "archivo": t["archivo"]})
    por_paquete = []
    for p, ids in sorted(paquetes.items()):
        ce, ca = len(pk_sale[p]), len(pk_entra[p])
        por_paquete.append({"paquete": p, "tipos": len(ids), "fan_out": ce, "fan_in": ca,
                            "inestabilidad": round(ce / (ca + ce), 2) if ca + ce else 0.0,
                            "cohesion_relacional": round((internas[p] + 1) / len(ids), 2)})

    def top(clave: str, n: int = 10) -> list[dict]:
        # Las raíces de composición (Program y DependencyInjection) registran todo el servicio:
        # su fan-out alto es esperado y no indica acoplamiento de diseño.
        candidatos = [x for x in por_tipo if not es_composicion(x["tipo"])]
        return sorted(candidatos, key=lambda x: (-x[clave], x["tipo"]))[:n]

    lineas = [t["lineas"] for t in tipos.values()]
    return {
        "servicio": servicio, "lenguaje": lenguaje,
        "resumen": {
            "tipos": len(tipos), "paquetes": len(paquetes), "dependencias_entre_tipos": len(deps),
            "dependencias_entre_paquetes": len(pk_peso),
            "ciclos_entre_paquetes": len(ciclos_paquetes),
            "paquetes_en_ciclos": sum(len(c) for c in ciclos_paquetes),
            "ciclos_entre_tipos": len(ciclos_tipos),
            "mayor_ciclo_de_tipos": max((len(c) for c in ciclos_tipos), default=0),
            "violaciones_de_capas": len(violaciones),
            "tipos_de_mas_de_250_lineas": sum(1 for x in lineas if x > 250),
            "fan_out_maximo": max((x["fan_out"] for x in por_tipo if not es_composicion(x["tipo"])), default=0),
            "fan_out_promedio": round(sum(x["fan_out"] for x in por_tipo) / max(1, len(por_tipo)), 2),
            "cohesion_relacional_promedio": round(sum(x["cohesion_relacional"] for x in por_paquete) / max(1, len(por_paquete)), 2),
        },
        "dependencias_entre_capas": dict(sorted(capas.items())),
        "violaciones": violaciones,
        "ciclos_entre_paquetes": ciclos_paquetes,
        "ciclos_entre_tipos": ciclos_tipos,
        "mayor_fan_out": top("fan_out"), "mayor_fan_in": top("fan_in"), "mas_grandes": top("lineas"),
        "paquetes": por_paquete,
        "aristas_paquetes": [{"de": a, "a": b, "n": n} for (a, b), n in sorted(pk_peso.items())],
        "aristas_tipos": [{"de": a, "a": b} for a, b in sorted(deps)],
    }


# ---------------------------------------------------------------- diagramas

def corto(nombre: str, servicio_ns: str) -> str:
    return nombre[len(servicio_ns) + 1:] if nombre.startswith(servicio_ns + ".") else nombre


def alias(n: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "_", n)


def diagramas(m: dict, ns: str, destino: Path, fase: str, sha: str) -> None:
    en_ciclo = {p for c in m["ciclos_entre_paquetes"] for p in c}
    malas = {(v["de"], v["a"]) for v in m["violaciones"]}
    capa_de = {}
    for p in m["paquetes"]:
        resto = corto(p["paquete"], ns)
        capa_de[p["paquete"]] = next((c for c in CAPAS if resto.lower().startswith(c.lower())), "Api")
    viol_paquetes = set()
    for v in m["violaciones"]:
        pa = v["de"].rsplit(".", 1)[0] if "." in v["de"] else "(global)"
        pb = v["a"].rsplit(".", 1)[0] if "." in v["a"] else v["a"]
        viol_paquetes.add((pa, pb))

    titulo = f"{m['servicio']} — paquetes ({fase}, {sha})"
    puml = ["@startuml", "!pragma layout smetana", f"title {titulo}", "skinparam packageStyle rectangle",
            "skinparam shadowing false", "left to right direction"]
    for capa in CAPAS:
        miembros = [p for p in m["paquetes"] if capa_de[p["paquete"]] == capa]
        if not miembros:
            continue
        puml.append(f'package "{capa}" {{')
        for p in miembros:
            color = " #FFCDD2" if p["paquete"] in en_ciclo else ""
            puml.append(f'  component "{corto(p["paquete"], ns) or p["paquete"]}\\n{p["tipos"]} tipos" as {alias(p["paquete"])}{color}')
        puml.append("}")
    mmd = ["flowchart LR"]
    for capa in CAPAS:
        miembros = [p for p in m["paquetes"] if capa_de[p["paquete"]] == capa]
        if not miembros:
            continue
        mmd.append(f"  subgraph {capa}")
        for p in miembros:
            mmd.append(f'    {alias(p["paquete"])}["{corto(p["paquete"], ns) or p["paquete"]} ({p["tipos"]})"]')
        mmd.append("  end")
    estilos = []
    for i, e in enumerate(m["aristas_paquetes"]):
        mala = (e["de"], e["a"]) in viol_paquetes
        ciclo = e["de"] in en_ciclo and e["a"] in en_ciclo
        color = "#C62828" if mala else ("#EF6C00" if ciclo else "#607D8B")
        puml.append(f'{alias(e["de"])} --> {alias(e["a"])} {color} : {e["n"]}')
        mmd.append(f'  {alias(e["de"])} -->|{e["n"]}| {alias(e["a"])}')
        if mala or ciclo:
            estilos.append(f"  linkStyle {i} stroke:{color},stroke-width:2px")
    for p in en_ciclo:
        mmd.append(f"  style {alias(p)} fill:#FFCDD2")
    puml += ["legend right", "Rojo: viola SDD 10.3.2 · Naranja: ciclo entre paquetes", "Número: dependencias entre tipos", "endlegend", "@enduml"]
    (destino / "paquetes.puml").write_text("\n".join(puml) + "\n", encoding="utf-8")
    (destino / "paquetes.mmd").write_text("\n".join(mmd + estilos) + "\n", encoding="utf-8")

    # Clases centrales: las 12 con más dependencias (entrada + salida) y sus relaciones entre ellas.
    centrales = sorted({**{x["tipo"]: x for x in m["mayor_fan_out"]}, **{x["tipo"]: x for x in m["mayor_fan_in"]}}.values(),
                       key=lambda x: -(x["fan_in"] + x["fan_out"]))[:12]
    ids = {x["tipo"] for x in centrales}
    c = ["@startuml", "!pragma layout smetana", f"title {m['servicio']} — clases más conectadas ({fase}, {sha})",
         "hide empty members", "skinparam shadowing false"]
    for x in centrales:
        estereotipo = {"interface": "interface", "enum": "enum", "abstract": "abstract class"}.get(x["clase"], "class")
        c.append(f'{estereotipo} "{corto(x["tipo"], ns)}" as {alias(x["tipo"])} <<{x["capa"]}>> {{\n  {x["lineas"]} líneas · entra {x["fan_in"]} · sale {x["fan_out"]}\n}}')
    for e in m["aristas_tipos"]:
        if e["de"] in ids and e["a"] in ids:
            color = " #C62828" if (e["de"], e["a"]) in malas else ""
            c.append(f'{alias(e["de"])} ..>{color} {alias(e["a"])}')
    c.append("@enduml")
    (destino / "clases-centrales.puml").write_text("\n".join(c) + "\n", encoding="utf-8")


def caso_de_uso(servicio: str, datos: dict, ns: str, destino: Path, fase: str, sha: str) -> None:
    """Diagrama de clases del caso de uso principal (C4 · Code): entrada -> caso de uso -> puertos <- adaptadores."""
    if servicio not in CASOS:
        return
    entrada_s, caso_s, motivo = CASOS[servicio]
    tipos = {t["id"]: t for t in datos["tipos"] if ".Migrations" not in t["paquete"]}
    sale = defaultdict(set)
    for d in datos["dependencias"]:
        if d["de"] in tipos and d["a"] in tipos:
            sale[d["de"]].add(d["a"])
    por_simple = defaultdict(list)
    for i in tipos:
        por_simple[i.rsplit(".", 1)[-1]].append(i)
    entrada, caso = por_simple[entrada_s][0], por_simple[caso_s][0]

    nodos, rel, externas = [entrada, caso], [(entrada, caso, "-->", "invoca")], set()
    pendientes, vistos = [caso], set()
    while pendientes:
        actual = pendientes.pop(0)
        if actual in vistos:
            continue
        vistos.add(actual)
        for dep in tipos[actual].get("inyecta", []):
            if dep not in tipos:
                externas.add(dep.rsplit(".", 1)[-1])
                continue
            nodos.append(dep)
            rel.append((actual, dep, "-->", "usa"))
            # Un puerto es lo que alguien implementa; en Java, también la clase que agrupa interfaces anidadas (MatchingPorts).
            impls = [i for i, x in tipos.items() if dep in x.get("implementa", []) and x["capa"] in ("Infrastructure", "Application")]
            if impls or tipos[dep]["clase"] in ("interface", "abstract"):
                for impl in impls:
                    nodos.append(impl)
                    rel.append((impl, dep, "..|>", "implementa"))
                    if tipos[impl]["capa"] == "Application":
                        pendientes.append(impl)
            elif tipos[dep]["capa"] == "Application" and not dep.endswith("Handler"):
                pendientes.append(dep)
    # Tipos del dominio que usan el caso de uso y sus colaboradores de Application (del IL o del bytecode).
    for origen in [v for v in vistos if tipos[v]["capa"] == "Application"]:
        for dom in sorted(d for d in sale[origen] if tipos[d]["capa"] == "Domain" and tipos[d]["clase"] not in ("interface", "static")):
            nodos.append(dom)
            rel.append((origen, dom, "..>", "crea o usa"))
    nodos = list(dict.fromkeys(nodos))

    l = ["classDiagram", "    direction LR"]
    for capa in CAPAS:
        miembros = [n for n in nodos if tipos[n]["capa"] == capa]
        if not miembros:
            continue
        l.append(f"    namespace {capa} {{")
        for n in miembros:
            est = {"interface": "<<interface>>", "abstract": "<<abstract>>", "enum": "<<enumeration>>"}.get(tipos[n]["clase"])
            nombre = alias(corto(n, ns).rsplit(".", 1)[-1])
            l += [f"        class {nombre} {{", f"            {est}", "        }"] if est else [f"        class {nombre}"]
        l.append("    }")
    vistas = set()
    for a, b, flecha, etiqueta in rel:
        if (a, b) not in vistas:
            vistas.add((a, b))
            l.append(f"    {alias(corto(a, ns).rsplit('.', 1)[-1])} {flecha} {alias(corto(b, ns).rsplit('.', 1)[-1])} : {etiqueta}")
    mmd = "\n".join(l) + "\n"
    (destino / "caso-de-uso.mmd").write_text(mmd, encoding="utf-8")

    tabla = [f"| `{corto(n, ns)}` | {tipos[n]['capa']} | `{tipos[n].get('archivo') or ''}` |" for n in nodos]
    md = [f"# {datos.get('nombre', servicio)} — código del caso de uso principal ({fase})", "",
          f"Nivel 4 del modelo C4 ([c4model.com/diagrams](https://c4model.com/diagrams)): las clases del caso de uso principal, **{motivo}**, "
          "desde su clase de entrada hasta los adaptadores, con un bloque por capa (SDD 10.3.1 y 10.3.2). El resto del servicio repite el patrón "
          "y está en su diagrama de componentes (C4-04) y en [`paquetes.mmd`](paquetes.mmd).", "",
          f"Generado desde el código compilado de `origin/develop` (`{sha}`) el {date.today().isoformat()} con `tools/arquitectura/generar.py` "
          "(SCRUM-715). No se edita a mano.", "",
          "```mermaid", mmd.rstrip(), "```", "",
          "**Cómo leerlo.** `-->` es una dependencia inyectada por el constructor; `..|>`, una clase que implementa un puerto "
          "(un adaptador de Infrastructure o un colaborador de Application); `..>`, un tipo del dominio que el caso de uso o sus colaboradores usan, "
          "según el IL (.NET) o el bytecode (Java). No se dibujan las dependencias transversales: "
          + (", ".join(f"`{e}`" for e in sorted(externas)) or "ninguna") + ".", "",
          "| Clase | Capa | Archivo |", "|---|---|---|", *tabla, ""]
    (destino / "caso-de-uso.md").write_text("\n".join(md), encoding="utf-8")


def resumen_md(m: dict, ns: str, sha: str, fase: str) -> str:
    r = m["resumen"]
    l = [f"# {m['servicio']} — {fase}", "",
         f"Código de `origin/develop` en `{sha}`, generado el {date.today().isoformat()} con `tools/arquitectura/generar.py`.", "",
         "| Métrica | Valor |", "|---|---|"]
    etiquetas = {"tipos": "Tipos (sin migraciones)", "paquetes": "Paquetes", "dependencias_entre_tipos": "Dependencias entre tipos",
                 "dependencias_entre_paquetes": "Dependencias entre paquetes", "ciclos_entre_paquetes": "Ciclos entre paquetes",
                 "paquetes_en_ciclos": "Paquetes dentro de ciclos", "ciclos_entre_tipos": "Ciclos entre tipos",
                 "mayor_ciclo_de_tipos": "Tipos en el mayor ciclo", "violaciones_de_capas": "Violaciones de SDD 10.3.2",
                 "tipos_de_mas_de_250_lineas": "Tipos de más de 250 líneas", "fan_out_maximo": "Fan-out máximo (sin raíces de composición)",
                 "fan_out_promedio": "Fan-out promedio", "cohesion_relacional_promedio": "Cohesión relacional promedio (H)"}
    l += [f"| {etiquetas[k]} | {v} |" for k, v in r.items()]
    l += ["", "## Dependencias entre capas", "", "| Desde → hacia | Dependencias |", "|---|---|"]
    l += [f"| {k.replace('->', ' → ')} | {v} |" for k, v in m["dependencias_entre_capas"].items()]
    l += ["", "## Clases con más dependencias de salida (fan-out)", "", "| Tipo | Capa | Líneas | Sale | Entra |", "|---|---|---|---|---|"]
    l += [f"| `{corto(x['tipo'], ns)}` | {x['capa']} | {x['lineas']} | {x['fan_out']} | {x['fan_in']} |" for x in m["mayor_fan_out"]]
    l += ["", "## Clases más usadas (fan-in)", "", "| Tipo | Capa | Entra | Sale |", "|---|---|---|---|"]
    l += [f"| `{corto(x['tipo'], ns)}` | {x['capa']} | {x['fan_in']} | {x['fan_out']} |" for x in m["mayor_fan_in"]]
    l += ["", "## Clases más grandes", "", "| Tipo | Capa | Líneas | Archivo |", "|---|---|---|---|"]
    l += [f"| `{corto(x['tipo'], ns)}` | {x['capa']} | {x['lineas']} | `{x['archivo']}` |" for x in m["mas_grandes"]]
    l += ["", "## Ciclos entre paquetes", ""]
    l += [f"- {', '.join('`' + corto(p, ns) + '`' for p in c)}" for c in m["ciclos_entre_paquetes"]] or ["Ninguno."]
    l += ["", "## Violaciones de las reglas de dependencia (SDD 10.3.2)", ""]
    if m["violaciones"]:
        l += ["| Regla | Desde | Hacia |", "|---|---|---|"]
        l += [f"| {v['regla']} | `{corto(v['de'], ns)}` | `{corto(v['a'], ns)}` |" for v in m["violaciones"]]
    else:
        l.append("Ninguna.")
    l += ["", "## Paquetes", "", "| Paquete | Tipos | Fan-in | Fan-out | Inestabilidad | Cohesión H |", "|---|---|---|---|---|---|"]
    l += [f"| `{corto(p['paquete'], ns) or p['paquete']}` | {p['tipos']} | {p['fan_in']} | {p['fan_out']} | {p['inestabilidad']} | {p['cohesion_relacional']} |" for p in m["paquetes"]]
    l += ["", "## Diagrama de paquetes", "", "Fuente: [`paquetes.puml`](paquetes.puml) (PlantUML) y [`paquetes.mmd`](paquetes.mmd). Clases más conectadas: [`clases-centrales.puml`](clases-centrales.puml). "
          "Clases del caso de uso principal (C4 · Code): [`caso-de-uso.md`](caso-de-uso.md).", "",
          "```mermaid", (Path(DESTINO_ACTUAL) / "paquetes.mmd").read_text(encoding="utf-8").rstrip(), "```", ""]
    return "\n".join(l)


DESTINO_ACTUAL = ""


def main() -> None:
    global DESTINO_ACTUAL
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fase", required=True, help="antes | despues (nombre de la carpeta de salida)")
    ap.add_argument("--ref", default="origin/develop", help="referencia git a analizar en cada servicio")
    ap.add_argument("--servicios", nargs="*", default=TODOS)
    ap.add_argument("--salida", default=str(RAIZ / "docs" / "architecture" / "codigo"))
    ap.add_argument("--sin-fetch", action="store_true", help="no ejecutar git fetch antes de exportar")
    a = ap.parse_args()

    salida = Path(a.salida) / a.fase
    trabajo = Path(tempfile.mkdtemp(prefix="qp-arq-"))
    extractor = trabajo / "extractor" / "extractor-dotnet.dll"
    if any(s in DOTNET for s in a.servicios):
        sh(["dotnet", "build", str(Path(__file__).parent / "extractor-dotnet"), "-c", "Release",
            "-o", str(extractor.parent), "-nologo", "-v", "q"])
    filas = []
    for s in a.servicios:
        repo = SERVICIOS_DIR / s
        if not a.sin_fetch:
            sh(["git", "-C", str(repo), "fetch", "-q", "origin"])
        fuente = trabajo / s / "src"
        fuente.mkdir(parents=True)
        sha = exportar(repo, a.ref, fuente)
        if s in DOTNET:
            datos, lenguaje, ns = extraer_dotnet(fuente, DOTNET[s], trabajo / s, extractor), "csharp", f"QuickPatch.{DOTNET[s]}"
        else:
            datos, lenguaje, ns = extraer_java(fuente), "java", "co.quickpatch.matching"
        nombre = DOTNET.get(s) or JAVA[s]
        m = analizar(nombre, lenguaje, datos)
        m["commit"] = sha
        destino = salida / s
        destino.mkdir(parents=True, exist_ok=True)
        DESTINO_ACTUAL = str(destino)
        (destino / "metricas.json").write_text(json.dumps(m, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        diagramas(m, ns, destino, a.fase, sha)
        datos["nombre"] = nombre
        caso_de_uso(s, datos, ns, destino, a.fase, sha)
        (destino / "README.md").write_text(resumen_md(m, ns, sha, a.fase), encoding="utf-8")
        filas.append((s, nombre, sha, m["resumen"]))
        print(f"{nombre}: {m['resumen']}")

    if set(a.servicios) == set(TODOS):
        l = [f"# Dependencias desde el código — {a.fase}", "",
             f"Generado el {date.today().isoformat()} con `python tools/arquitectura/generar.py --fase {a.fase}` sobre `{a.ref}` de cada servicio. "
             "Método y decisión: [`tools/arquitectura/README.md`](../../../../tools/arquitectura/README.md). Reglas: SDD 10.3.2.", "",
             "| Servicio | Commit | Tipos | Paquetes | Dep. entre tipos | Dep. entre paquetes | Ciclos paquetes | Ciclos tipos (mayor) | Violaciones | Tipos > 250 líneas | Fan-out máx. | Cohesión H prom. |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for s, n, sha, r in filas:
            l.append(f"| [{n}]({s}/README.md) | `{sha}` | {r['tipos']} | {r['paquetes']} | {r['dependencias_entre_tipos']} | {r['dependencias_entre_paquetes']} | "
                     f"{r['ciclos_entre_paquetes']} | {r['ciclos_entre_tipos']} ({r['mayor_ciclo_de_tipos']}) | {r['violaciones_de_capas']} | "
                     f"{r['tipos_de_mas_de_250_lineas']} | {r['fan_out_maximo']} | {r['cohesion_relacional_promedio']} |")
        l += ["", "1. Sin las raíces de composición (`Program` y `DependencyInjection`), que por diseño conocen todo el servicio.", "",
              "Actors se analiza desde SCRUM-640; antes era un esqueleto sin lógica (solo `Program.cs`), así que no tiene línea base.", ""]
        (salida / "README.md").write_text("\n".join(l), encoding="utf-8")
    shutil.rmtree(trabajo, ignore_errors=True)


if __name__ == "__main__":
    main()
