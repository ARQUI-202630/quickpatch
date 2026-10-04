# ADR-011 — k3s para los clústeres QUICKPATCH

- **Estado:** Aceptado; ampliado por ADR-015
- **Restricción:** K10

## Decisión original
Usar k3s en VM3 para los ocho microservicios de producción.

## Enmienda por ADR-015
VM2 también utiliza k3s para QA. La infraestructura auxiliar usa los mecanismos definidos por `quickpatch-infrastructure`.

## Consecuencias
Rolling updates, probes y auto-healing por servicio. VM2 y VM3 continúan siendo clústeres de nodo único y sus límites de recursos se fijan con medición real.
