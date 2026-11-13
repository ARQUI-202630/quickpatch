#!/usr/bin/env python3
"""Calcula las cifras de QA de QUICKPATCH desde sus fuentes únicas (SCRUM-700, SCRUM-664).

Fuentes:
  - docs/testing/indicadores-funcionales.md   -> cuatro indicadores funcionales (33 RF) y extensiones
  - docs/testing/matriz-escenarios-calidad-52.md -> estado de los 52 escenarios de calidad

Uso:
  python scripts/calcular_indicadores_qa.py              # imprime las cifras
  python scripts/calcular_indicadores_qa.py --json       # las imprime en JSON
  python scripts/calcular_indicadores_qa.py --verificar  # además busca cifras retiradas en docs/testing

No hay cifras escritas a mano: si cambia una fila de las fuentes, cambia el resultado.
"""
import json
import os
import re
import sys
from collections import Counter, OrderedDict

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDICADORES = os.path.join(RAIZ, 'docs', 'testing', 'indicadores-funcionales.md')
MATRIZ_52 = os.path.join(RAIZ, 'docs', 'testing', 'matriz-escenarios-calidad-52.md')
DOCS_TESTING = os.path.join(RAIZ, 'docs', 'testing')

PESO_FUNCIONAL = 0.7
PESO_CALIDAD = 0.3
PUNTAJE = {'Cumple': 1.0, 'Parcial': 0.5, 'No cumple': 0.0, 'No medido': 0.0}
ESTADOS = ['Cumple', 'Parcial', 'No cumple', 'No medido']


def _celdas(linea):
    return [c.strip() for c in linea.strip().strip('|').split('|')]


def _bloque(texto, inicio, fin):
    i = texto.index(inicio)
    j = texto.index(fin, i)
    return texto[i:j]


def leer_rf():
    texto = open(INDICADORES, encoding='utf-8').read()
    rf, ext = [], []
    for linea in _bloque(texto, '<!-- tabla-rf', '<!-- fin-tabla-rf').splitlines():
        if linea.startswith('| RF-'):
            c = _celdas(linea)
            rf.append({'id': c[0], 'prioridad': c[2], 'definida': c[3] == 'Sí',
                       'implementada': c[4] == 'Sí', 'verificada': c[5] == 'Sí',
                       'aceptada': c[6] == 'Sí', 'observacion': c[8]})
    for linea in _bloque(texto, '<!-- tabla-ext', '<!-- fin-tabla-ext').splitlines():
        if linea.startswith('| EXT-'):
            c = _celdas(linea)
            ext.append({'id': c[0], 'implementada': c[3] == 'Sí',
                        'verificada': c[4] == 'Sí', 'aceptada': c[5] == 'Sí'})
    return rf, ext


def leer_escenarios():
    texto = open(MATRIZ_52, encoding='utf-8').read()
    seccion = texto.split('## 2.')[1].split('## 3.')[0]
    escenarios = []
    for linea in seccion.splitlines():
        if re.match(r'\|\s*\*\*AC\d-E\d', linea):
            c = _celdas(linea)
            escenarios.append({'id': c[0].strip('*'), 'estado': c[6].strip('*').strip()})
    return escenarios


def calcular():
    rf, ext = leer_rf()
    esc = leer_escenarios()
    total_rf = sum(1 for r in rf if r['definida'])
    ind = OrderedDict((k, sum(1 for r in rf if r[k]))
                      for k in ('definida', 'implementada', 'verificada', 'aceptada'))
    estados = Counter(e['estado'] for e in esc)
    desconocidos = set(estados) - set(PUNTAJE)
    if desconocidos:
        raise SystemExit(f'Estado de escenario desconocido: {desconocidos}')
    por_atributo = OrderedDict()
    for e in esc:
        por_atributo.setdefault(e['id'][:3], Counter())[e['estado']] += 1
    pct_esc = sum(PUNTAJE[e['estado']] for e in esc) / len(esc) * 100
    pct_func = ind['aceptada'] / total_rf * 100
    avance = PESO_FUNCIONAL * pct_func + PESO_CALIDAD * pct_esc
    return OrderedDict([
        ('rf_total', total_rf),
        ('rf_alta', sum(1 for r in rf if r['prioridad'] == 'Alta')),
        ('rf_alta_aceptadas', sum(1 for r in rf if r['prioridad'] == 'Alta' and r['aceptada'])),
        ('indicadores', ind),
        ('rf_con_observacion', [r['id'] for r in rf if r['observacion'] not in ('', '—')]),
        ('extensiones', OrderedDict([('total', len(ext)),
                                     ('aceptadas', sum(1 for e in ext if e['aceptada']))])),
        ('escenarios_total', len(esc)),
        ('escenarios', OrderedDict((s, estados.get(s, 0)) for s in ESTADOS)),
        ('escenarios_por_atributo', OrderedDict(
            (a, OrderedDict((s, c.get(s, 0)) for s in ESTADOS)) for a, c in por_atributo.items())),
        ('pct_escenarios', round(pct_esc, 2)),
        ('pct_funcional_aceptado', round(pct_func, 2)),
        ('avance_producto', round(avance, 2)),
    ])


# Cifras que ya no se usan. Una línea que las cite debe decir que es histórica.
CIFRAS_RETIRADAS = [r'37 de 37', r'37 funcionalidades', r'91[.,]92', r'73[.,]08', r'94[.,]52',
                    r'81[.,]73', r'\b34 Cumple', r'\b39 Cumple', r'\b4 No cumple', r'36 aceptadas']
MARCAS_HISTORICAS = ['histór', 'Histór', 'Era ', 'era ', 'etirad', 'o usar', 'antes', 'Antes',
                     'sube de', 'pasa de', 'corte del 5', 'primera versión', 'segunda versión']
# Documentos que son registro histórico por definición.
EXCLUIDOS = {'acta-uat-scrum-608.md', 'conciliacion-cifras-qa-2026-11-12.md',
             'indicadores-funcionales.md', 'informe-pruebas-sprint3.md', 'informe-pruebas-sprint4.md'}


def verificar():
    hallazgos = []
    patron = re.compile('|'.join(CIFRAS_RETIRADAS))
    for nombre in sorted(os.listdir(DOCS_TESTING)):
        if not nombre.endswith('.md') or nombre in EXCLUIDOS:
            continue
        for n, linea in enumerate(open(os.path.join(DOCS_TESTING, nombre), encoding='utf-8'), 1):
            if patron.search(linea) and not any(m in linea for m in MARCAS_HISTORICAS):
                hallazgos.append(f'docs/testing/{nombre}:{n}: {patron.search(linea).group(0)}')
    return hallazgos


def _pct(x):
    return f'{x:.2f} %'.replace('.', ',')


def main():
    r = calcular()
    if '--json' in sys.argv:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        i = r['indicadores']
        print(f"Requisitos funcionales (SRS v5.6): {r['rf_total']}")
        print(f"  Definidas {i['definida']} | Implementadas {i['implementada']} | "
              f"Verificadas en QA {i['verificada']} | Aceptadas {i['aceptada']}")
        print(f"  Prioridad Alta aceptadas: {r['rf_alta_aceptadas']} de {r['rf_alta']}")
        print(f"  Con observaciones: {', '.join(r['rf_con_observacion'])}")
        print(f"Extensiones fuera del SRS: {r['extensiones']['total']} "
              f"({r['extensiones']['aceptadas']} aceptadas, no entran al denominador)")
        e = r['escenarios']
        print(f"Escenarios de calidad: {r['escenarios_total']} -> " +
              ', '.join(f'{v} {k}' for k, v in e.items()) + f" = {_pct(r['pct_escenarios'])}")
        for a, c in r['escenarios_por_atributo'].items():
            print(f"  {a}: " + ', '.join(f'{v} {k}' for k, v in c.items()))
        print(f"Avance del producto: {PESO_FUNCIONAL} x {_pct(r['pct_funcional_aceptado'])} + "
              f"{PESO_CALIDAD} x {_pct(r['pct_escenarios'])} = {_pct(r['avance_producto'])}")
    if '--verificar' in sys.argv:
        hallazgos = verificar()
        if hallazgos:
            print('\nCifras retiradas sin marca de histórico:')
            print('\n'.join(hallazgos))
            sys.exit(1)
        print('\nVerificación: 0 cifras retiradas en docs/testing.')


if __name__ == '__main__':
    main()
