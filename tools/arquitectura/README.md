# Ingeniería inversa de los microservicios (SCRUM-680)

Genera, **desde el código compilado de `develop`**, los diagramas de paquetes y de clases y las métricas de acoplamiento y cohesión de los 8 servicios con código (Actors desde SCRUM-640). Responde a la observación final del profesor: el nivel de código de C4 no se dibuja a mano, sale del código y se puede regenerar.

```bash
# Desde la raíz del superproyecto. Requiere git, .NET SDK 10, JDK 17+ (jdeps) y Maven.
python tools/arquitectura/generar.py --fase antes                         # los 7 servicios
python tools/arquitectura/generar.py --fase despues --servicios catalog   # solo algunos
python tools/arquitectura/generar.py --fase antes --ref v1.2.0            # otra referencia git
```

La salida va a `docs/architecture/codigo/<fase>/`: un `README.md` comparativo y, por servicio, `README.md` (métricas y tablas), `metricas.json`, `paquetes.puml`, `paquetes.mmd` (Mermaid, se ve directamente en GitHub) y `clases-centrales.puml`. No toca las copias de trabajo: cada servicio se exporta con `git archive` a una carpeta temporal y se compila ahí.

## Decisión de herramienta (SCRUM-681)

**Criterios**, tomados de SCRUM-680: que se pueda volver a ejecutar con un comando; que muestre paquetes, clases principales y dependencias; que sirva para detectar acoplamiento (ciclos, clases sobreconectadas, baja cohesión); que funcione con C# y Java; y que la salida sea PlantUML, Mermaid, Graphviz, D2 o Structurizr.

| Opción | C# | Java | Dependencias entre tipos | Métricas | Regenerable sin licencia | Resultado |
|---|---|---|---|---|---|---|
| NDepend | Sí | No | Sí | Sí | No (licencia de pago, solo Windows) | Descartada |
| PlantUmlClassDiagramGenerator (`puml-gen`) | Sí | No | Solo herencia y asociaciones por campos, desde el texto fuente; no ve las llamadas dentro de los métodos | No | Sí | Descartada: dibuja clases, pero no mide acoplamiento. No se probó, porque en el entorno del equipo no se instalan herramientas de terceros sin revisión |
| DependenSee | Sí | No | Solo entre proyectos y paquetes NuGet | No | Sí | Descartada: no llega a clases ni paquetes |
| NetArchTest / ArchUnit | Sí / Sí | — | Verifican reglas | No | Sí | Se usan para las **pruebas de arquitectura** (SDD 10.3.2), no para diagramar |
| Diagramas del IDE (Rider, IntelliJ, Visual Studio) | Sí | Sí | Sí | Parcial | No (se generan a mano) | Descartada: no se regenera en CI |
| Structurizr | — | — | — | — | Sí | No modela el nivel de código (SDD 7) |
| **`jdeps` (JDK)** | No | **Sí** | **Sí**, del bytecode | Con el script | **Sí**: viene con el JDK | **Adoptada para Java** |
| **`System.Reflection.Metadata` (runtime .NET) + extractor propio** | **Sí** | No | **Sí**, del IL: herencia, campos, firmas, variables locales y cada tipo, método o campo que el código usa | Con el script | **Sí**: viene con el SDK, sin paquetes externos | **Adoptada para .NET** |

**Por qué del binario y no del texto fuente:** el compilador ya resolvió los nombres. Una dependencia que aparece solo dentro de un método (por ejemplo, `new ChannelOptions()` en un endpoint) se ve en el IL o en el bytecode, pero no en los `using` ni en los campos. Así medimos lo que el código hace, no lo que declara.

**Salida:** PlantUML (`!pragma layout smetana`, no requiere Graphviz) y Mermaid. Las mismas métricas para los dos lenguajes salen de `generar.py`.

## Qué mide

| Métrica | Definición |
|---|---|
| Tipos | Clases, interfaces, records y enums propios. Los tipos que genera el compilador (closures, máquinas de estado async) se atribuyen al tipo que los declara. Se excluyen las migraciones de EF Core, que son código generado. |
| Paquete | Espacio de nombres en .NET (`QuickPatch.Identity.Application.Companies`) o paquete en Java. |
| Dependencia entre tipos | A usa B al menos una vez: herencia, interfaz, campo, firma, variable local o referencia en el cuerpo de un método. |
| Fan-out / fan-in de un tipo | Cuántos tipos propios distintos usa y cuántos lo usan (acoplamiento eferente y aferente). |
| Ciclo entre paquetes o tipos | Componente fuertemente conexo de más de un nodo (algoritmo de Tarjan). |
| Inestabilidad del paquete | I = Ce / (Ca + Ce), con los paquetes que usa (Ce) y los que lo usan (Ca). |
| Cohesión relacional (H) | (R + 1) / N, con R las dependencias entre tipos dentro del paquete y N sus tipos. Cuanto más alta, más trabajan juntos los tipos del paquete. |
| Violaciones | Dependencias que prohíbe la matriz del SDD 10.3.2: entre capas (por ejemplo, `Api → Infrastructure` fuera de `Program`) y hacia tecnologías (por ejemplo, `Domain → Microsoft.EntityFrameworkCore`). |
| Líneas | .NET: rango de líneas con código del tipo según el PDB. Java: líneas no vacías del archivo. |

Las raíces de composición (`Program`, las clases `DependencyInjection` y `MatchingApplication`) quedan fuera de los rankings de fan-out: por diseño registran todo el servicio.

## Limitaciones

- Las líneas no son comparables entre .NET y Java porque se miden distinto. En los dos lenguajes, los tipos anidados se cuentan dentro del tipo que los declara.
- La capa sale del ensamblado (.NET) o del primer segmento del paquete (Java); un tipo mal ubicado se cuenta en la capa donde está, que es justo lo que se quiere detectar.
- No mide llamadas por reflexión ni configuración (por ejemplo, el registro de consumidores de Spring por anotaciones).
- Actors solo tiene medición «después»: en la línea base era un esqueleto (solo `Program.cs`). `comparar.py` omite los servicios sin las dos fases.
