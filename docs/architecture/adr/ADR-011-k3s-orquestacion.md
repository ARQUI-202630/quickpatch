# ADR-011 — k3s como orquestador de los microservicios

- **Estado:** Aceptado; ampliado por ADR-015
- **Fecha:** agosto de 2026 (SAD 1.0); enmienda del 3 de octubre de 2026
- **Decisión:** Kubernetes en su distribución k3s, en un clúster de un solo nodo, para los 8 microservicios (VM3 en producción y VM2 en QA); Docker Compose para el resto de VMs
- **Atributo priorizado:** AC5 Reliability (rolling updates sin downtime y auto-healing de contenedores)
- **Atributo sacrificado:** costo y simplicidad operativa (curva de aprendizaje y administración de un clúster)
- **Restricciones:** R5 (sin presupuesto), R7 (sin operación 24/7), R10 (7 VMs fijas), R11 (un solo administrador de infraestructura)
- **Implementación:** `quickpatch-infrastructure` (playbooks de Ansible y manifiestos de k3s)

> **Actualización (ADR-021, 6 de octubre de 2026):** el k3s de QA pasa de VM2 a VM5; producción sigue en VM3. Ambos siguen siendo clústeres de un solo nodo.

## Contexto

Los 8 microservicios (ADR-003) se despliegan de forma independiente y deben poder actualizarse sin cortar el servicio, reiniciarse solos si fallan y exponer sus sondas de salud. Solo hay 7 VMs (R10) y una sola persona administra la infraestructura (R11), así que no hay VMs libres para un plano de control dedicado.

## Decisión

- **k3s** en un solo nodo: en VM3 para producción y, desde ADR-015, en VM2 para QA.
- Cada servicio es un `Deployment` con `requests`/`limits`, `livenessProbe` en `/health/live` y `readinessProbe` en `/health/ready` sobre el puerto 8080, y se actualiza con rolling update.
- El resto de VMs (gateway, PostgreSQL, Redis, Kafka, Garage y observabilidad) usa **Docker Compose**, porque cada una aloja un componente principal que no se beneficia de un orquestador.
- La configuración del clúster y de las VMs es código de Ansible (R11).

## Alternativas descartadas

- **Kubernetes multi-nodo con `kubeadm`:** requiere VMs adicionales para el plano de control; viola R10.
- **Docker Compose también para los microservicios:** más simple, pero sin rolling updates, sin reinicio por sondas y con un despliegue que afecta a los 8 servicios a la vez.
- **Kubernetes administrado en la nube (EKS, GKE, AKS):** viola R5.
- **Docker Swarm:** orquestación más simple, pero con un ecosistema y una comunidad en declive y sin la API estándar de Kubernetes que pide el curso.

## Consecuencias

### Positivas
- Rolling updates, reinicio automático y sondas por servicio (AC5-E1, AC5-E2).
- Manifiestos estándar de Kubernetes, iguales en QA y en producción.

### Costos
- Un clúster que operar sin guardia 24/7 (R7); el equipo asume esa complejidad.
- Un solo nodo: si VM3 cae, caen los 8 servicios; k3s protege frente a la caída de un contenedor, no de la VM.
- Los `limits` de memoria deben ajustarse con medición real (AC2-E5, en QA).

## Evidencia

- Imágenes de Identity, Catalog y ServiceRequest construidas en el CI con sondas `/health/live` y `/health/ready` en el puerto 8080.
- Clúster de QA de VM2 configurado con Ansible (ADR-015).

## Trazabilidad

- SAD: secciones 5.4 y 5.5; restricciones R5, R7, R10 y R11.
- Documento de Infraestructura: secciones de k3s y despliegue.
- Relacionados: ADR-003, ADR-013, ADR-015.
