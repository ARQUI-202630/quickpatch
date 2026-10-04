# QUICKPATCH — Toolchain fijado

| Tecnología | Versión |
|---|---:|
| .NET SDK | 10.0.401 |
| ASP.NET Core | 10 |
| EF Core | 10.x |
| Java | 25 LTS |
| Spring Boot | 4.1.1 |
| Node.js | 24.21.0 LTS |
| Angular | 22.1.x |
| TypeScript | 6.0.x |
| Flutter | 3.47.5 |
| Dart | 3.13.4 |

## Fuente de verdad

Servicios .NET:
`global.json`

Matching:
`.java-version` + Maven Wrapper/pom.xml

Web:
`.nvmrc` + package.json + package-lock.json

Mobile:
`.flutter-version` + pubspec.lock

Contracts:
`.nvmrc`

CI:
quickpatch-infrastructure/.github/workflows/

No usar preview, RC, beta o nightly en el scaffold base.
