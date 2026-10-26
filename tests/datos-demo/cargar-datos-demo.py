#!/usr/bin/env python3
"""Carga idempotente del juego de datos de demostración en QA o en producción (SCRUM-632 y SCRUM-634).

Usa solo la API pública (el mismo camino de la app y del panel), así que respeta RLS y los roles de cada servicio.
Un registro que ya existe responde 409 y se deja como está: se puede repetir sin duplicar nada.

Sin credenciales en el repositorio: se leen del entorno.
  QP_ADMIN_EMAIL, QP_ADMIN_PASSWORD   administrador de la plataforma del ambiente (vault_identity_admins)
  QP_DEMO_PASSWORD                    contraseña de las cuentas de demostración (entre 8 y 128 caracteres)

  python3 cargar-datos-demo.py --ambiente qa --simular        muestra el plan y no escribe nada
  python3 cargar-datos-demo.py --ambiente qa                  carga
  python3 cargar-datos-demo.py --ambiente produccion --confirmar-produccion

Las solicitudes de ejemplo llevan la descripción «[DEMO] ...». Limpiar los datos de las pruebas de carga
(`playbooks/limpiar-carga-qa.yml`) filtra por «Solicitud de carga k6 %» y «Estrés pico 150 VU%», así que no las toca.
"""
import argparse
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

AMBIENTES = {
    "qa": {"ip": "10.43.100.168", "host": "qa.quickpatch.internal"},
    "produccion": {"ip": "10.43.100.168", "host": "quickpatch.internal"},
}
CANAL = "quickpatch-mobile"


class Api:
    def __init__(self, base, host):
        self.base, self.host = base.rstrip("/"), host
        self.ctx = ssl.create_default_context()
        self.ctx.check_hostname = False  # certificado autofirmado de VM1 (INFRASTRUCTURE.md 10.1)
        self.ctx.verify_mode = ssl.CERT_NONE

    def llamar(self, metodo, ruta, cuerpo=None, token=None):
        req = urllib.request.Request(f"{self.base}/api{ruta}", method=metodo,
                                     data=json.dumps(cuerpo).encode() if cuerpo is not None else None)
        req.add_header("Host", self.host)
        req.add_header("Content-Type", "application/json")
        req.add_header("X-Channel-Id", CANAL)
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        try:
            with urllib.request.urlopen(req, context=self.ctx, timeout=25) as r:
                texto = r.read()
                return r.status, (json.loads(texto) if texto else None)
        except urllib.error.HTTPError as e:
            texto = e.read()
            try:
                return e.code, json.loads(texto)
            except ValueError:
                return e.code, texto.decode(errors="replace")[:160]

    def login(self, email, clave):
        st, r = self.llamar("POST", "/v1/auth/login", {"email": email, "password": clave})
        return st, (r.get("accessToken") if isinstance(r, dict) else None)


def lista(r):
    return r if isinstance(r, list) else (r or {}).get("items", []) if isinstance(r, dict) else []


class Resumen:
    def __init__(self):
        self.cuenta = {}

    def anotar(self, tipo, estado, detalle=""):
        self.cuenta.setdefault(tipo, {"creado": 0, "ya existía": 0, "aplicado": 0, "error": 0})[estado] += 1
        print(f"  {tipo}: {detalle} -> {estado}")


def registrar(api, resumen, tipo, nombre, ruta, cuerpo):
    st, r = api.llamar("POST", ruta, cuerpo)
    if st == 201:
        resumen.anotar(tipo, "creado", nombre)
    elif st == 409:
        resumen.anotar(tipo, "ya existía", nombre)
    else:
        resumen.anotar(tipo, "error", f"{nombre} (HTTP {st}: {str(r)[:120]})")
    return st, r


def buscar_tecnico(api, token, email):
    """Busca el técnico por correo en todas las páginas de GET /v1/admin/technicians (máximo 100 por página)."""
    pagina = 1
    while True:
        st, r = api.llamar("GET", f"/v1/admin/technicians?page={pagina}&size=100", token=token)
        if st != 200 or not isinstance(r, dict):
            return None
        items = lista(r)
        for u in items:
            if u.get("email") == email:
                return u
        if not items or pagina * 100 >= r.get("totalItems", 0):
            return None
        pagina += 1


def cargar(api, juego, clave, admin, resumen, disponibles):
    st, tok = api.login(*admin)
    if st != 200:
        sys.exit(f"Inicio de sesión del administrador: HTTP {st}. No se cambió nada.")

    st, cats = api.llamar("GET", "/v1/catalog/categories", token=tok)
    categorias = {c["name"]: c["id"] for c in lista(cats)}
    pedidas = {t["categoria"] for t in juego["tecnicos"]} | {s["categoria"] for s in juego["solicitudes"]}
    if pedidas - categorias.keys():
        sys.exit(f"Categorías que no existen en el catálogo: {sorted(pedidas - categorias.keys())}. "
                 f"Existen: {sorted(categorias)}. No se cambió nada.")

    print("Clientes")
    for c in juego["clientes"]:
        registrar(api, resumen, "cliente", c["email"], "/v1/auth/register/client",
                  {"email": c["email"], "password": clave, "fullName": c["nombre"], "phone": c["telefono"]})

    print("Empresas")
    for e in juego["empresas"]:
        u = e["usuario"]
        registrar(api, resumen, "empresa", e["razonSocial"], "/v1/auth/register/company", {
            "company": {"legalName": e["razonSocial"], "nit": e["nit"], "contactEmail": u["email"], "contactPhone": u["telefono"]},
            "user": {"email": u["email"], "password": clave, "fullName": u["nombre"], "phone": u["telefono"]}})

    print("Técnicos")
    for t in juego["tecnicos"]:
        st, r = registrar(api, resumen, "técnico", t["email"], "/v1/auth/register/technician", {
            "email": t["email"], "password": clave, "fullName": t["nombre"], "phone": t["telefono"],
            "documentId": t["documento"], "specialtyId": categorias[t["categoria"]], "role": "tecnico"})
        if st == 201 and isinstance(r, dict) and r.get("id"):
            uid, estado = r["id"], "pendiente"
        else:
            u = buscar_tecnico(api, tok, t["email"]) or {}
            uid, estado = u.get("userId"), u.get("verificationStatus")
        if not uid:
            resumen.anotar("técnico (aprobación)", "error", f"{t['email']}: no aparece en el listado de Identity")
            continue
        if estado == "aprobado":
            resumen.anotar("técnico (aprobación)", "ya existía", t["email"])
        else:
            st_a, r_a = api.llamar("POST", f"/v1/admin/technicians/{uid}/approve", token=tok)
            if st_a != 200:
                resumen.anotar("técnico (aprobación)", "error", f"{t['email']} (HTTP {st_a}: {str(r_a)[:120]})")
                continue
            resumen.anotar("técnico (aprobación)", "aplicado", t["email"])
        st, ttok = api.login(t["email"], clave)
        if not ttok:
            resumen.anotar("técnico (cobertura)", "error", f"{t['email']}: no inicia sesión (HTTP {st})")
            continue
        for _ in range(12):  # Matching conoce al técnico unos segundos después de aprobarlo
            st, _r = api.llamar("PUT", "/v1/technicians/me/coverage", {"localityCodes": juego["cobertura"]}, ttok)
            if st == 200:
                break
            time.sleep(3)
        resumen.anotar("técnico (cobertura)", "aplicado" if st == 200 else "error",
                       t["email"] if st == 200 else f"{t['email']} (HTTP {st})")
        if disponibles:
            st, _r = api.llamar("PUT", "/v1/technicians/me/availability", {"status": "disponible"}, ttok)
            resumen.anotar("técnico (disponibilidad)", "aplicado" if st == 200 else "error",
                           t["email"] if st == 200 else f"{t['email']} (HTTP {st})")

    print("Solicitudes de ejemplo")
    for s in juego["solicitudes"]:
        st, ctok = api.login(s["cliente"], clave)
        if not ctok:
            resumen.anotar("solicitud", "error", f"{s['descripcion'][:40]}: el cliente no inicia sesión (HTTP {st})")
            continue
        st, r = api.llamar("GET", "/v1/service-requests", token=ctok)
        if any(x.get("description") == s["descripcion"] for x in lista(r)):
            resumen.anotar("solicitud", "ya existía", s["descripcion"][:50])
            continue
        st, r = api.llamar("POST", "/v1/service-requests", {
            "categoryId": categorias[s["categoria"]], "description": s["descripcion"], "addressText": s["direccion"]}, ctok)
        resumen.anotar("solicitud", "creado" if st == 201 else "error", f"{s['descripcion'][:50]} (HTTP {st})" if st != 201 else s["descripcion"][:50])


def simular(juego):
    print("Plan (no se escribe nada):")
    print(f"  clientes: {len(juego['clientes'])}, empresas: {len(juego['empresas'])}, técnicos: {len(juego['tecnicos'])} "
          f"(cobertura en {len(juego['cobertura'])} localidades), solicitudes de ejemplo: {len(juego['solicitudes'])}")
    for grupo in ("clientes", "tecnicos"):
        for x in juego[grupo]:
            print(f"  {grupo[:-1]}: {x['email']}")
    for e in juego["empresas"]:
        print(f"  empresa: {e['razonSocial']} ({e['usuario']['email']})")
    for s in juego["solicitudes"]:
        print(f"  solicitud: {s['descripcion']} — {s['direccion']}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--ambiente", choices=AMBIENTES, required=True)
    ap.add_argument("--juego", default=str(Path(__file__).with_name("juego-datos.json")))
    ap.add_argument("--simular", action="store_true", help="muestra el plan y no llama a la API")
    ap.add_argument("--confirmar-produccion", action="store_true", help="obligatoria con --ambiente produccion")
    ap.add_argument("--base-url", help="solo para pruebas locales (por ejemplo http://127.0.0.1:8099)")
    a = ap.parse_args()

    juego = json.loads(Path(a.juego).read_text(encoding="utf-8"))
    if a.simular:
        simular(juego)
        return
    if a.ambiente == "produccion" and not a.confirmar_produccion:
        sys.exit("En producción hace falta --confirmar-produccion. No se cambió nada.")

    faltan = [v for v in ("QP_ADMIN_EMAIL", "QP_ADMIN_PASSWORD", "QP_DEMO_PASSWORD") if not os.environ.get(v)]
    if faltan:
        sys.exit(f"Faltan variables de entorno: {', '.join(faltan)}. No se cambió nada.")
    clave = os.environ["QP_DEMO_PASSWORD"]
    if not 8 <= len(clave) <= 128:
        sys.exit("QP_DEMO_PASSWORD debe tener entre 8 y 128 caracteres (política de Identity).")

    amb = AMBIENTES[a.ambiente]
    api = Api(a.base_url or f"https://{amb['ip']}", amb["host"])
    resumen = Resumen()
    disponibles = a.ambiente != "produccion"
    if not disponibles:
        print("Producción: los técnicos quedan aprobados y con cobertura, pero no se marcan disponibles "
              "(Matching podría ofrecerles trabajo de clientes reales).")
    cargar(api, juego, clave, (os.environ["QP_ADMIN_EMAIL"], os.environ["QP_ADMIN_PASSWORD"]), resumen, disponibles)

    print("\nConteo final")
    for tipo, c in resumen.cuenta.items():
        print(f"  {tipo}: {c['creado']} creados, {c['ya existía']} ya existían, {c['aplicado']} aplicados, {c['error']} con error")
    if any(c["error"] for c in resumen.cuenta.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
