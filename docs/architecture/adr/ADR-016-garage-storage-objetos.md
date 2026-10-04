# ADR-016 — Garage como almacenamiento de objetos S3-compatible

- **Estado:** Aceptado
- **Fecha:** 2026-10-03
- **Driver:** D7

## Contexto
Las evidencias fotográficas y respaldos requieren object storage self-hosted. La alternativa vigente dejó de ser MinIO durante la configuración de infraestructura.

## Decisión
Usar Garage en VM7 y en el ambiente QA de VM2, conservando API S3-compatible y URLs prefirmadas.

## Consecuencias
Los datos permanecen dentro de las 7 VMs. Evidencias y backups usan buckets/credenciales separados. ServiceRequest trata Garage como adaptador de infraestructura.

## Relación
ADR-015, SAD, SDD, DD e Infraestructura.
