# Fund Distribution Platform

<!-- TODO: parágrafo sobre o domínio -->

Plataforma composta por quatro serviços, um por contexto de domínio, e um worker de migração de dados:

| Projeto | Tipo | Responsabilidade |
| --- | --- | --- |
| `Offering` | API | <!-- TODO --> |
| `DemandConsolidation` | API | <!-- TODO --> |
| `ReservationBook` | API | <!-- TODO --> |
| `Allocation` | API | <!-- TODO --> |
| `DataMigration` | Worker | Migração de dados. Não expõe HTTP. |

## Pré-requisitos

- .NET SDK 10 (desenvolvido com 10.0.400)
- Aspire CLI 13.5 (`aspire --version`)

## Como rodar

```bash
aspire run --apphost src/AppHost/AppHost.csproj
```

O comando compila a solução, sobe os cinco projetos e abre o dashboard do Aspire em `https://localhost:17150`. O dashboard mostra logs, traces e métricas de todos os serviços.

Portas dos serviços em desenvolvimento:

| Serviço | URL |
| --- | --- |
| Offering | `http://localhost:5084` |
| DemandConsolidation | `http://localhost:5268` |
| ReservationBook | `http://localhost:5129` |
| Allocation | `http://localhost:5288` |

Cada API expõe, apenas em ambiente `Development`:

- `/health` — todos os health checks precisam passar.
- `/alive` — só os checks marcados como `live`.
- `/openapi/v1.json` — documento OpenAPI.

## Build e testes

```bash
dotnet build FundDistributionPlatform.slnx
```

```bash
dotnet test FundDistributionPlatform.slnx
```

## Estrutura do repositório

```
src/AppHost               Aspire AppHost; ponto de entrada local
src/ServiceDefaults       OpenTelemetry, service discovery, resiliência, health checks, versionamento, ProblemDetails, OpenAPI
src/Offering              API
src/DemandConsolidation   API
src/ReservationBook       API
src/Allocation            API
src/DataMigration         Worker
tests/UnitTests           xUnit
tests/IntegrationTests    xUnit
```

Os serviços de API compilam com Native AOT (`PublishAot=true`) e globalização invariante.

## Convenções

As convenções de código, commits e estrutura estão em [CLAUDE.md](CLAUDE.md). Regras específicas por área (composição do `Program.cs`, módulos de feature, tracing) estão em [.claude/rules](.claude/rules).
