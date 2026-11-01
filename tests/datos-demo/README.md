# Datos de demostración de QA y producción

Script idempotente que carga en QA o en producción un juego de datos de demostración (**SCRUM-632**, definición formal de datos en **SCRUM-633**). Usa exclusivamente la API pública —el mismo camino que transitan la aplicación móvil y el panel web administrativo— garantizando el cumplimiento de RLS, los roles RBAC y el aislamiento por tenant.

| Archivo | Qué es |
|---|---|
| `cargar-datos-demo.py` | Script de carga idempotente (Python 3, biblioteca estándar, sin dependencias externas) |
| `juego-datos.json` | Definición formal del juego de datos semilla: categorías base, clientes hogar, empresas clientes corporativas, técnicos con cobertura en Bogotá, proveedores con equipo, segundo tenant y solicitudes de demostración. Sin credenciales |

## Qué carga (Definición SCRUM-633)

El juego de datos formalizado en `juego-datos.json` cubre todos los tipos de usuario y perfiles de uso contemplados en el sistema (SRS v5.5, TD §8.2):

1. **6 Categorías Base de Catálogo:**
   - Si no existen en el ambiente, el script las siembra automáticamente (`POST /v1/catalog/admin/categories`):
     - *Aire acondicionado* (Instalación, mantenimiento y recarga de gas)
     - *Cerrajería* (Aperturas, cambio de guardas y chapas)
     - *Eléctrico* (Instalaciones, tomas, breakers y cortos)
     - *Electrodomésticos* (Reparación de lavadoras, neveras y estufas)
     - *Pintura* (Pintura de interiores y exteriores)
     - *Plomería* (Fugas, grifería, tuberías y destapes)
   - Una categoría que ya existe inactiva no se reactiva sola: esa decisión corresponde al administrador del tenant.

2. **3 Clientes Hogar (Personas Naturales):**
   - `demo.cliente1@demo.quickpatch.test` (Carolina Gómez Restrepo, Tel: `3001230001`)
   - `demo.cliente2@demo.quickpatch.test` (Andrés Felipe Morales, Tel: `3001230002`)
   - `demo.cliente3@demo.quickpatch.test` (Mariana Lucía Torres, Tel: `3001230003`)

3. **2 Empresas Clientes (Personas Jurídicas / Cuentas Corporativas):**
   - *Inmobiliaria & Coworking Bogotá S.A.S.* (NIT `900123456-7`), Contacto: `demo.empresa1@demo.quickpatch.test` (Santiago Ramírez, Tel: `3001230011`)
   - *Restaurantes y Cafés Andinos S.A.S.* (NIT `901987654-3`), Contacto: `demo.empresa2@demo.quickpatch.test` (Valeria Jaramillo, Tel: `3001230012`)

4. **1 Proveedor con Equipo de Técnicos (RF-16 / SCRUM-99):**
   - *Red de Servicios Técnicos Bogotá S.A.S.* (NIT `901234567-8`), Contacto: `demo.proveedor1@demo.quickpatch.test` (Héctor Fabio Proveedor, Tel: `3004560001`).
   - Técnico de su equipo: `demo.tecnico.proveedor1@demo.quickpatch.test` (Néstor Raúl Cárdenas, CC: `1000000031`, Especialidad: Plomería).
   - Valida la gestión delegada de nómina técnica (`/v1/providers/me/technicians`) y el aislamiento intra-tenant (RN-TP4).

5. **4 Técnicos Profesionales Independientes:**
   - `demo.tecnico1@demo.quickpatch.test` (Carlos Alberto Pérez, CC: `1000000021`, Especialidad: Plomería)
   - `demo.tecnico2@demo.quickpatch.test` (Jorge Enrique Duarte, CC: `1000000022`, Especialidad: Plomería)
   - `demo.tecnico3@demo.quickpatch.test` (Mauricio Silva Peña, CC: `1000000023`, Especialidad: Cerrajería)
   - `demo.tecnico4@demo.quickpatch.test` (Héctor Fabio Ospina, CC: `1000000024`, Especialidad: Eléctrico)
   - Todos quedan aprobados por el administrador de tenant y con cobertura configurada en las **20 localidades de Bogotá** (`01` a `20`).
   - En **QA**, los técnicos se configuran con estado `disponible` inmediatamente.
   - En **producción no se marcan disponibles** (permanecen en `no_disponible`): marcarlos haría que el motor de Matching les asigne solicitudes de clientes reales o reintente órdenes en cola (RN-M10). Para una demostración en producción se activan bajo demanda y se desactivan al finalizar.

6. **Segundo Tenant para Demostración de Aislamiento Multi-Tenant (RLS / AC6-E2):**
   - Tenant Beta: *Tenant Beta Soluciones* (`tenant-beta`).
   - Cuenta con su propio cliente (`demo.beta.cliente@demo.quickpatch.test`) y técnico (`demo.beta.tecnico@demo.quickpatch.test`).
   - Permite verificar en demostraciones y pruebas que las consultas cruzadas entre tenants retornan HTTP 404/403 y que no existen fugas de solicitudes ni de perfiles entre tenants.

7. **5 Solicitudes de Demostración (`[DEMO]`):**
   - Todas ubicadas en direcciones verificables dentro del perímetro urbano de Bogotá (geocodificación Nominatim RIE-02 / RN-SR9):
     - `demo.cliente1`: `[DEMO] Fuga de agua continua en grifería del lavamanos principal` (Calle 72 # 10-34, Chapinero).
     - `demo.cliente2`: `[DEMO] Cambio de cerradura de seguridad y copia de llaves` (Carrera 15 # 85-30, Usaquén).
     - `demo.cliente3`: `[DEMO] Cortocircuito en panel de interruptores de cocina` (Calle 53 # 13-25, Teusaquillo).
     - `demo.empresa1`: `[DEMO] Mantenimiento preventivo de batería de baños piso 3 oficinas` (Avenida Carrera 68 # 24-30, Salitre / Fontibón).
     - `demo.empresa2`: `[DEMO] Revisión de acometida y tomas de corriente en barra comercial` (Calle 134 # 9-51, Usaquén).

## Cobertura de Administradores y Seguridad

Conforme a la arquitectura del sistema (SAD §2.3 y DD §8.3):

1. **Cómo quedan cubiertos los Administradores:**
   - **Administrador de Plataforma (`admin_plataforma`):** No se crea por este script ni se expone en datos demo. Se provisiona a nivel de infraestructura/IaC mediante Ansible (`vault_identity_admins`) y administra la creación y estado de los tenants (`/v1/platform/tenants`, RN-U6).
   - **Administrador del Tenant (`admin_tenant`):** Es quien ejecuta las labores de gobierno en cada tenant (creación de categorías en el catálogo, aprobación y suspensión de técnicos mediante `/v1/admin/technicians/{id}/approve`). Sus credenciales se suministran de forma segura por variables de entorno (`QP_ADMIN_EMAIL`, `QP_ADMIN_PASSWORD`), evitando quemar contraseñas administrativas en archivos o repositorios.

2. **Gestión de Credenciales en Demostración:**
   - En estricto cumplimiento con **RF-29**, **RNF-01** y **K2**:
     - **Ninguna credencial se almacena en el repositorio ni en archivos de configuración.**
     - La contraseña uniforme de las cuentas de demostración se provee en tiempo de ejecución mediante `QP_DEMO_PASSWORD` (longitud entre 8 y 128 caracteres, validada por Identity).

| Variable | Descripción |
|---|---|
| `QP_ADMIN_EMAIL`, `QP_ADMIN_PASSWORD` | Administrador **del tenant** del ambiente, rol `admin_tenant` (`vault_identity_admins` del vault de Ansible). La aprobación de técnicos está restringida a este rol |
| `QP_DEMO_PASSWORD` | Contraseña asignada a todas las cuentas semilla del juego de datos de demostración |

## Ejecución del Script

```bash
# 1. Simulación sin escrituras (inspección de plan)
python3 tests/datos-demo/cargar-datos-demo.py --ambiente qa --simular

# 2. Carga sobre ambiente QA (requiere VPN y variables de entorno)
python3 tests/datos-demo/cargar-datos-demo.py --ambiente qa

# 3. Carga sobre ambiente Producción (con confirmación de seguridad)
python3 tests/datos-demo/cargar-datos-demo.py --ambiente produccion --confirmar-produccion
```

El script es estrictamente **idempotente**: si un usuario, empresa o solicitud ya existe (código HTTP 409), el registro existente se respeta sin duplicar entidades ni generar inconsistencias.

## Procedimiento de Limpieza y Convivencia

- **Aislamiento frente a pruebas de carga:** El playbook de Ansible `infrastructure/ansible/playbooks/limpiar-carga-qa.yml` purga exclusivamente solicitudes cuyo patrón coincida con `Solicitud de carga k6 %` o `Estrés pico 150 VU%`, preservando intactos los registros que inician con el prefijo `[DEMO] …`.
- **Depuración de datos de demostración:** Dado que la API pública no expone eliminación física de usuarios ni solicitudes, si se requiere retirar el juego de demostración se realiza a nivel de base de datos previa copia de seguridad, filtrando por el dominio `@demo.quickpatch.test` y la descripción `[DEMO]`.
