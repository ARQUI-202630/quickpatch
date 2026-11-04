# Escaneo PCI-DSS sobre los logs de QA, Sprint 5 (SCRUM-527)

Fecha: 2026-11-04. Responsable: Katherine Bravo (QA). Historia: SCRUM-524.

## 1. Qué se revisa

El paso «Escáner PCI-DSS sobre los logs de QA (Loki)» del workflow «Pruebas de sistema» consulta Loki con `query_range` sobre `{vm="vm2"}`. Eso cubre todos los logs del clúster k3s de QA, incluido Payments, de las últimas 24 horas, con un límite de 5000 líneas.

En esas líneas busca:
- números de tarjeta Visa, Mastercard, Amex y Discover con dígito de Luhn válido;
- CVV o CVC seguidos de 3 o 4 dígitos.

## 2. Resultados del Sprint 5

| Corrida | Rama | Fecha (UTC) | Resultado del paso | Salida |
|---|---|---|---|---|
| 41168063519 | `feature/qa/humo-flujo-critico` | 2026-10-31 04:28 | success | «Líneas revisadas: 5000. Hallazgos: 0.» |
| 41515531669 | `develop` | 2026-11-02 20:02 | success | «Líneas revisadas: 5000. Hallazgos: 0.» |
| 41522853302 | `develop` | 2026-11-02 20:50 | success | «Líneas revisadas: 5000. Hallazgos: 0.» |
| 41794907667 | `develop` | 2026-11-04 07:49 | success | «Líneas revisadas: 5000. Hallazgos: 0.» |

- https://github.com/ARQUI-202630/quickpatch/actions/runs/41794907667
- La corrida del 30 de octubre (hora de Bogotá) tiene el log copiado sin cambios en `tests/security/evidencias/zap-pci-ci-qa-2026-10-30-run-41168063519.txt`.

## 3. Conclusión

En las cuatro corridas del Sprint 5 no aparece ningún número de tarjeta ni ningún código de seguridad en los logs de QA. El último reporte anterior es `tests/security/evidencias/pci-dss-loki-qa-2026-10-18.txt`, del Sprint 4.
