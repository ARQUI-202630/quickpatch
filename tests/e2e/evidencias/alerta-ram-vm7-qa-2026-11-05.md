# Disparo de prueba de la alerta de RAM en VM7 de QA (AC9-E6, RF-28)

Escenario AC9-E6: alerta emitida en menos de 15 minutos desde que se cumple la condición (RAM por encima del 85 %). La regla es `qp-ram-alta` de Grafana (`infrastructure/ansible/files/grafana/alerting/rules.yml`): RAM usada mayor a 85 % durante 5 minutos, evaluada cada minuto, con 30 segundos de espera de grupo y un correo como punto de contacto.

## Qué se hizo

El 5 de noviembre de 2026 se subió la RAM de **VM7** (QA, Kafka y Garage; 11,9 GiB) por encima del 85 % con un proceso de Python que reserva memoria real, con `oom_score_adj` en 1000 (si el kernel debe matar algo, es ese proceso) y un freno que lo libera si quedan menos de 700 MiB disponibles. No se probó en producción. Kafka y Garage siguieron arriba durante toda la prueba.

## Línea de tiempo (UTC)

| Hora | Hecho | Fuente |
|---|---|---|
| 01:46:03 | Inicio de la prueba, RAM al 30,5 % | registro de la VM (`alerta-ram-vm7-qa-2026-11-05.txt`) |
| **01:46:24** | **La RAM cruza el 85 %** (85,55 %) | registro de la VM |
| 01:46:25 | Objetivo alcanzado: 89,40 % usada, 1.263 MiB disponibles | registro de la VM |
| **01:52:20** | **La alerta pasa a «Firing»** (RAM al 89 % en vm7; valor 89,42) | correo de Grafana: «Observed 34s before this notification was delivered, at 01:52:20 UTC» |
| **01:52:54** | **Llega el correo «[FIRING:1] RAM alta en una VM vm7»** | fecha del mensaje |
| 01:57:11 | Última muestra sostenida (87,28 %) | registro de la VM |
| 01:57:30 | La memoria se libera: 30,3 % | registro de la VM |
| 01:58:20 | La alerta se resuelve (RAM al 29 %) | correo de Grafana |
| 02:02:54 | Llega el correo «[RESOLVED] RAM alta en una VM vm7» | fecha del mensaje |

## Resultado

| Medida | Valor | Meta |
|---|---|---|
| Del cruce del 85 % a la alerta en «Firing» | 5 min 56 s | menos de 15 min |
| Del cruce del 85 % al correo recibido | 6 min 30 s | menos de 15 min |

Se cumple la meta con mucho margen. Los 5 minutos de la regla explican casi todo el tiempo; el resto es el intervalo de evaluación, el scrape de Prometheus y la espera de grupo.

## Límites

- Es QA (VM7), no la VM que nombra el escenario (RAM de VM3, disco de VM4 o VM6, todas de producción). La regla es la misma para todas las VM (`vm` es una etiqueta), pero no se disparó en esas VM.
- Solo se probó la regla de RAM. La de disco (`qp-disco-lleno`, 10 minutos de espera, estimado de 11 a 12 minutos hasta el correo) no se probó.
- Las horas del cruce salen del reloj de VM7; las de la alerta y el correo, de Grafana y de Gmail, todas en UTC.
