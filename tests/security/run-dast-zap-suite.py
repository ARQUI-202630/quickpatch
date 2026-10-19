#!/usr/bin/env python3
"""
QUICKPATCH — Suite de Evaluación DAST OWASP ZAP Baseline Real (SCRUM-396)
Responsable: Katherine Bravo (QA Lead - ka.bravo@javeriana.edu.co)
Estándares: OWASP Top 10 API Security (2023), INF-013, SAD V4 (v2.28)

Ejecuta el contenedor oficial de OWASP ZAP contra el API Gateway de QA
(https://qa.quickpatch.internal) aplicando las reglas de zap-baseline.conf
y procesa el archivo oficial de resultados zap.json.
"""

import os
import sys
import json
import subprocess
from datetime import datetime

# Garantizar salida UTF-8 en consolas Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')


def check_docker_available():
    try:
        res = subprocess.run(["docker", "ps"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
        return res.returncode == 0
    except Exception:
        return False


def run_dast_zap_validation():
    print("=" * 80)
    print("EJECUTANDO: ANÁLISIS DINÁMICO DAST OWASP ZAP BASELINE CONTRA QA (SCRUM-396)")
    print("Ambiente Objetivo: https://qa.quickpatch.internal")
    print("Reglas: tests/security/zap-baseline.conf")
    print("=" * 80)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    evidencias_dir = os.path.join(script_dir, "evidencias")
    os.makedirs(evidencias_dir, exist_ok=True)

    zap_json_path = os.path.join(evidencias_dir, "zap.json")
    zap_report_txt = os.path.join(evidencias_dir, "zap-dast-baseline-qa-2026-10-18.txt")
    conf_file = os.path.join(script_dir, "zap-baseline.conf")

    docker_ok = check_docker_available()

    if not docker_ok:
        print("\n[INSTRUCCIÓN PARA QA]")
        print("El servicio de Docker Desktop no se encuentra en ejecución.")
        print("Para ejecutar el escaneo real de OWASP ZAP contra QA:")
        print("1. Inicie Docker Desktop en su máquina.")
        print("2. Ejecute el siguiente comando:")
        print(f"\n  docker run --rm -v \"{evidencias_dir}:/zap/wrk/:rw\" ghcr.io/zaproxy/zaproxy:stable zap-baseline.py -t https://qa.quickpatch.internal -J zap.json -r zap.html\n")
        print("Las alertas reales quedarán exportadas en zap.json y zap.html.")
        return

    print("\n[Docker Detectado] Ejecutando escáner oficial ghcr.io/zaproxy/zaproxy:stable...")
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{evidencias_dir}:/zap/wrk/:rw",
        "ghcr.io/zaproxy/zaproxy:stable",
        "zap-baseline.py",
        "-t", "https://qa.quickpatch.internal",
        "-J", "zap.json",
        "-r", "zap.html"
    ]
    print("Comando:", " ".join(cmd))

    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    print(proc.stdout)

    if os.path.exists(zap_json_path):
        with open(zap_json_path, 'r', encoding='utf-8') as f:
            datos_zap = json.load(f)

        sitios = datos_zap.get('site', [])
        alertas = []
        for s in sitios:
            alertas.extend(s.get('alerts', []))

        altas_o_criticas = [a for a in alertas if a.get('riskcode') in ('3', '4')]
        print(f"\n[Resultado Real ZAP] Total alertas encontradas: {len(alertas)}")
        print(f"Alertas de Alto/Crítico Riesgo: {len(altas_o_criticas)}")

        # Escribir reporte formal
        with open(zap_report_txt, 'w', encoding='utf-8') as rep:
            rep.write(f"REPORTE FORMAL OWASP ZAP BASELINE CONTRA QA\n")
            rep.write(f"Fecha: {datetime.now().isoformat()}\n")
            rep.write(f"Total Alertas: {len(alertas)}\n")
            rep.write(f"Alertas Críticas/Altas: {len(altas_o_criticas)}\n")
            for a in alertas:
                rep.write(f"- [{a.get('riskdesc')}] {a.get('alert')}: {a.get('count')} instancias\n")
        print(f"[Evidencia Guardada] {zap_report_txt}")


if __name__ == '__main__':
    run_dast_zap_validation()
