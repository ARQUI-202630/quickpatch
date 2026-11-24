"""Acoplamiento y cohesión ENTRE los microservicios de QUICKPATCH (SCRUM-709).

`generar.py` mide cada servicio por dentro (paquetes y clases). Este script mide el sistema: qué servicio depende de
cuál, por qué medio y con qué fuerza, y si cada servicio es dueño de lo suyo.

Fuentes, todas regenerables:
- el catálogo de topics del contrato (`quickpatch-kafka`, `topics/topics.yaml` de la última etiqueta), contrastado con
  el código: cada servicio que nombra un topic en su `src/` debe figurar en el catálogo como su productor o como uno
  de sus consumidores, y al revés;
- las llamadas HTTP entre servicios, buscadas en el código (`/internal/v1/...` y clientes con `BaseAddress`);
- las referencias de código entre repositorios (`ProjectReference` y dependencias de Maven);
- la base de datos de cada servicio (sus manifiestos de `deploy/`);
- la cohesión interna que ya midió `generar.py` (`docs/architecture/codigo/despues/<servicio>/metricas.json`).

Uso (desde la raíz del superproyecto): python tools/arquitectura/servicios.py
Salida: docs/architecture/codigo/servicios/README.md
"""
import json
import re
import subprocess
from collections import defaultdict
from datetime import date
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[2]
SERVICIOS_DIR = RAIZ / "apps" / "backend" / "services"
KAFKA = RAIZ / "apps" / "kafka"
SALIDA = RAIZ / "docs" / "architecture" / "codigo" / "servicios"
CODIGO = RAIZ / "docs" / "architecture" / "codigo" / "despues"

# Nombre en el catálogo de topics -> carpeta del repositorio.
REPOS = {"identity-service": "identity", "actors-service": "actors", "catalog-service": "catalog",
         "service-request-service": "service-request", "matching-service": "matching", "ranking-service": "ranking",
         "payments-service": "payments", "communication-service": "communication"}
NOMBRE = {v: k.removesuffix("-service") for k, v in REPOS.items()}
# Dueño de cada endpoint interno: el servicio que lo expone en su capa Api.
ENDPOINTS_INTERNOS = {"internal/v1/users": "identity"}
# Consumidores que el catálogo lista como previstos y la documentación declara fuera del alcance actual.
PREVISTOS = {("catalog.category-changed", "matching"): "DD 9 y SAD 4.2.2: Matching aún no replica los nombres de las categorías"}


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, encoding="utf-8", check=True).stdout


def fuentes(repo: str):
    base = SERVICIOS_DIR / repo / ("src/main/java" if repo == "matching" else "src")
    for f in base.rglob("*"):
        p = f.as_posix()
        if f.suffix in (".cs", ".java", ".json", ".yml", ".yaml") and "/obj/" not in p and "/bin/" not in p and "/test/" not in p:
            yield f


def main() -> None:
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    git(KAFKA, "fetch", "-q", "--tags", "origin")
    etiqueta = git(KAFKA, "tag", "--sort=-v:refname").split()[0]
    catalogo = yaml.safe_load(git(KAFKA, "show", f"{etiqueta}:topics/topics.yaml"))["topics"]
    commits = {r: git(SERVICIOS_DIR / r, "rev-parse", "--short", "HEAD").strip() for r in NOMBRE}
    textos = {r: "\n".join(f.read_text(encoding="utf-8", errors="ignore") for f in fuentes(r)) for r in NOMBRE}

    # 1. Eventos: catálogo contra código.
    asincronas = defaultdict(set)      # (productor, consumidor) -> topics
    producidos, consumidos = defaultdict(list), defaultdict(list)
    diferencias, previstos = [], []
    for t in catalogo:
        productor = REPOS[t["producer"]]
        consumidores = [REPOS[c] for c in t.get("consumers") or []]
        producidos[productor].append(t["name"])
        for c in consumidores:
            consumidos[c].append(t["name"])
            asincronas[(productor, c)].add(t["name"])
        en_catalogo = {productor, *consumidores}
        en_codigo = {r for r, txt in textos.items() if f'"{t["name"]}"' in txt}
        for r in sorted(en_codigo - en_catalogo):
            diferencias.append(f"`{NOMBRE[r]}` nombra `{t['name']}` en su código, pero el catálogo no lo lista")
        for r in sorted(en_catalogo - en_codigo):
            if (t["name"], r) in PREVISTOS:
                previstos.append(f"`{NOMBRE[r]}` en `{t['name']}`: previsto, no implementado ({PREVISTOS[(t['name'], r)]})")
                continue
            diferencias.append(f"el catálogo lista a `{NOMBRE[r]}` en `{t['name']}`, pero su código no lo nombra")

    # 2. Llamadas síncronas entre servicios.
    sincronas = defaultdict(set)
    for r, txt in textos.items():
        for ruta, dueno in ENDPOINTS_INTERNOS.items():
            if dueno != r and ruta in txt:
                sincronas[(r, dueno)].add(f"GET /{ruta}")

    # 3. Referencias de código entre repositorios.
    referencias = []
    for r in NOMBRE:
        for f in (SERVICIOS_DIR / r).rglob("*.csproj"):
            for ref in re.findall(r'ProjectReference Include="([^"]+)"', f.read_text(encoding="utf-8")):
                otro = next((o for o in NOMBRE if o != r and f"QuickPatch.{o.replace('-', '').lower()}" in ref.lower().replace("-", "")), None)
                if otro and "shared" not in ref:
                    referencias.append(f"{NOMBRE[r]} -> {NOMBRE[otro]} ({ref})")
    pom = (SERVICIOS_DIR / "matching" / "pom.xml").read_text(encoding="utf-8")
    referencias += [f"matching -> {a}" for a in re.findall(r"<artifactId>(quickpatch-[^<]+)</artifactId>", pom)]

    # 4. Base de datos de cada servicio.
    bases = {}
    for r in NOMBRE:
        txt = "\n".join(f.read_text(encoding="utf-8", errors="ignore") for f in (SERVICIOS_DIR / r / "deploy").rglob("*") if f.is_file())
        txt += textos[r]
        bases[r] = sorted(set(re.findall(r"\bdb_[a-z_]+\b", txt)))

    # 5. Métricas por servicio.
    filas, aristas = [], set()
    for (a, b) in list(asincronas) + list(sincronas):
        aristas.add((b, a) if (a, b) in asincronas else (a, b))  # dependencia: consumidor -> productor; llamador -> llamado
    for r in NOMBRE:
        ce = {b for a, b in aristas if a == r}
        ca = {a for a, b in aristas if b == r}
        ce_sinc = {b for a, b in sincronas if a == r}
        m = json.loads((CODIGO / r / "metricas.json").read_text(encoding="utf-8"))["resumen"]
        filas.append({"s": r, "ce": len(ce), "ca": len(ca), "ce_sinc": len(ce_sinc),
                      "i": round(len(ce) / (len(ce) + len(ca)), 2) if ce or ca else 0.0,
                      "prod": len(producidos[r]), "cons": len(consumidos[r]),
                      "h": m["cohesion_relacional_promedio"], "ciclos": m["ciclos_entre_paquetes"],
                      "viol": m["violaciones_de_capas"], "bases": bases[r]})

    # Ciclos de llamadas síncronas (los únicos que acoplan la disponibilidad de dos servicios).
    def ciclo_sincrono():
        g = defaultdict(set)
        for a, b in sincronas:
            g[a].add(b)
        for a in list(g):
            pila, vistos = [a], set()
            while pila:
                n = pila.pop()
                for m2 in g[n]:
                    if m2 == a:
                        return True
                    if m2 not in vistos:
                        vistos.add(m2)
                        pila.append(m2)
        return False

    unico_productor = all(isinstance(t["producer"], str) for t in catalogo)
    bases_compartidas = {b: [NOMBRE[r] for r in NOMBRE if b in bases[r]] for r in NOMBRE for b in bases[r]}
    bases_compartidas = {b: rs for b, rs in bases_compartidas.items() if len(rs) > 1}

    # ---------------------------------------------------------------- salida
    SALIDA.mkdir(parents=True, exist_ok=True)
    l = ["# Acoplamiento y cohesión entre los microservicios", "",
         f"Generado el {date.today().isoformat()} con `python tools/arquitectura/servicios.py` (SCRUM-709) sobre los repositorios en "
         f"`develop` ({', '.join(f'{NOMBRE[r]} `{c}`' for r, c in commits.items())}) y el catálogo de topics `quickpatch-kafka` {etiqueta}. "
         "La medición de cada servicio por dentro está en [`../despues/`](../despues/README.md).", "",
         "## Resultado", ""]
    criterios = [
        ("Ningún servicio usa el código de otro", not referencias,
         "solo comparten `quickpatch-shared-dotnet`, que es código transversal (ADR-020)" if not referencias else "; ".join(referencias)),
        ("Cada servicio tiene su propia base de datos", not bases_compartidas,
         "una base por servicio (ADR-014)" if not bases_compartidas else str(bases_compartidas)),
        ("Cada evento tiene un solo productor, que es dueño de ese dato", unico_productor, f"{len(catalogo)} topics, un productor cada uno (ADR-006)"),
        ("El catálogo de eventos coincide con el código", not diferencias, "sin diferencias" if not diferencias else f"{len(diferencias)} diferencias, abajo"),
        ("Las llamadas síncronas entre servicios son mínimas y sin ciclos", len(sincronas) <= 1 and not ciclo_sincrono(),
         f"{len(sincronas)} relación síncrona: " + "; ".join(f"{NOMBRE[a]} → {NOMBRE[b]} ({', '.join(sorted(v))})" for (a, b), v in sincronas.items())),
        ("Cada servicio es cohesivo por dentro", all(f["ciclos"] == 0 and f["viol"] == 0 and f["h"] >= 0.7 for f in filas),
         "0 ciclos entre paquetes, 0 violaciones de capas y cohesión relacional promedio de "
         f"{min(f['h'] for f in filas)} a {max(f['h'] for f in filas)}"),
    ]
    l += ["| Criterio | Cumple | Detalle |", "|---|---|---|"]
    l += [f"| {c} | {'Sí' if ok else '**No**'} | {d} |" for c, ok, d in criterios]
    l += ["", "## Por servicio", "",
          "Ce: servicios de los que depende (le publican eventos que consume o los llama). Ca: servicios que dependen de él. "
          "I = Ce / (Ca + Ce): cerca de 0, estable (muchos dependen de él); cerca de 1, dependiente. H: cohesión relacional promedio de sus "
          "paquetes (`generar.py`).", "",
          "| Servicio | Ce | de ellas síncronas | Ca | I | Eventos que publica | Eventos que consume | H | Ciclos entre paquetes | Violaciones | Base |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for f in filas:
        l.append(f"| {NOMBRE[f['s']]} | {f['ce']} | {f['ce_sinc']} | {f['ca']} | {f['i']} | {f['prod']} | {f['cons']} | {f['h']} | "
                 f"{f['ciclos']} | {f['viol']} | {', '.join('`' + b + '`' for b in f['bases']) or '—'} |")
    l += ["", "## Dependencias entre servicios", "",
          "Una flecha va del servicio que depende al que provee: el consumidor de un evento depende de su productor, y el que llama, del "
          "llamado. Las continuas son síncronas (HTTP); las punteadas, eventos de Kafka.", "", "```mermaid", "flowchart LR"]
    for r in NOMBRE:
        l.append(f"  {r.replace('-', '_')}[{NOMBRE[r]}]")
    for (a, b), v in sorted(sincronas.items()):
        l.append(f"  {a.replace('-', '_')} -->|{', '.join(sorted(v))}| {b.replace('-', '_')}")
    for (p, c), v in sorted(asincronas.items()):
        l.append(f"  {c.replace('-', '_')} -.->|{len(v)} evento{'s' if len(v) > 1 else ''}| {p.replace('-', '_')}")
    l += ["```", "", "## Eventos (catálogo contrastado con el código)", "", "| Topic | Productor | Consumidores |", "|---|---|---|"]
    for t in catalogo:
        l.append(f"| `{t['name']}` | {REPOS[t['producer']] and NOMBRE[REPOS[t['producer']]]} | "
                 f"{', '.join(NOMBRE[REPOS[c]] for c in t.get('consumers') or []) or '— (sin consumidores hoy)'} |")
    l += ["", "**Diferencias entre el catálogo y el código:** " + ("ninguna." if not diferencias else ""), *[f"- {d}" for d in diferencias], "",
          "**Consumidores previstos** (en el catálogo, documentados como fuera del alcance actual): " + ("ninguno." if not previstos else ""), *[f"- {d}" for d in previstos], "",
          "## Cómo leerlo", "",
          "- **Bajo acoplamiento** entre microservicios no es «cero dependencias»: un flujo de negocio cruza varios servicios. Lo que importa "
          "es el medio y la dirección. Los eventos (ADR-006, ADR-007) desacoplan en el tiempo: el productor no conoce a sus consumidores ni "
          "espera que estén arriba. Una llamada síncrona sí acopla la disponibilidad, por eso se mide aparte y debe ser la excepción.",
          "- **Ciclos.** Entre servicios, los ciclos de eventos son coreografía normal (ServiceRequest publica `service-request.created`, "
          "Matching responde con `matching.technician-assigned`); lo que no puede haber es un ciclo de llamadas síncronas, que encadenaría "
          "las caídas.",
          "- **Alta cohesión** de un servicio: es dueño de sus datos (su base, ADR-014), es el único productor de los eventos de su "
          "agregado, y por dentro sus clases trabajan juntas (cohesión relacional, sin ciclos ni violaciones de capas).", ""]
    (SALIDA / "README.md").write_text("\n".join(l), encoding="utf-8")
    for c, ok, d in criterios:
        print(("OK " if ok else "NO ") + c + ": " + d)
    for d in diferencias:
        print("  -", d)


if __name__ == "__main__":
    main()
