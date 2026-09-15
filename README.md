# Fund Distribution Platform

Modelo executável do comportamento regulado pela Resolução CVM 160 (ofertas públicas) e pela Resolução CVM 175 (fundos), reduzido ao mínimo viável, para o caso de uso de corretora distribuindo cotas de fundo fechado a investidor final. Não há liquidação financeira nem integração externa; o investidor não acessa a plataforma, e o operador da corretora age em seu nome. O domínio está descrito nos PRDs de `docs/prd`, a partir da [visão geral](docs/prd/0000-platform-overview.md).

Plataforma composta por dois serviços, um por contexto de domínio, e um worker de migração de dados:

| Projeto | Tipo | Responsabilidade |
| --- | --- | --- |
| `Offering` | API | Definição imutável da oferta e sua máquina de estados ([PRD 0001](docs/prd/0001-offering-offer-lifecycle.md)) |
| `BookBuilding` | API | Reservas contra oferta Aberta, livro congelado no fechamento, processamento único do livro fechado (vedação a vinculadas, formação, condicionamento e rateio) e status por reserva ([PRD 0002](docs/prd/0002-book-building-bid-lifecycle.md), [PRD 0003](docs/prd/0003-book-building-book-processing.md)) |
| `DataMigration` | Worker | Migração de dados. Não expõe HTTP. |

## Pré-requisitos

- .NET SDK 10.0.400 ou feature band mais recente do .NET 10, conforme `global.json` (`rollForward: latestFeature`)
- Aspire CLI 13.5 (`aspire --version`)

## Como rodar

```bash
aspire run --apphost src/AppHost/AppHost.csproj
```

O comando compila a solução, sobe os três projetos e abre o dashboard do Aspire em `https://localhost:17150`. O dashboard mostra logs, traces e métricas de todos os serviços.

Portas dos serviços em desenvolvimento:

| Serviço | URL |
| --- | --- |
| Offering | `http://localhost:5084` |
| BookBuilding | `http://localhost:5129` |

Cada API expõe, apenas em ambiente `Development`:

- `/health` — todos os health checks precisam passar.
- `/alive` — só os checks marcados como `live`.
- `/openapi/v1.json` — documento OpenAPI.

## Build e testes

```bash
dotnet build FundDistributionPlatform.slnx
dotnet test FundDistributionPlatform.slnx
```

A CI ([ci.yml](.github/workflows/ci.yml)) executa os mesmos comandos no `ubuntu-latest` em push e pull request na `main`, com o SDK do `global.json`.

## Estrutura do repositório

```text
.
├── .claude/
│   └── rules/                        # regras do código de produção: projetos, composição e tracing
├── .github/workflows/                # CI: build e testes
├── docs/
│   ├── development/                  # uso do Claude Code e do plugin de skills
│   └── prd/                          # PRDs (prd): 0000 overview, 0001 Offering, 0002 e 0003 BookBuilding
├── src/
│   ├── AppHost/                      # Aspire AppHost; ponto de entrada local
│   ├── ServiceDefaults/              # OpenTelemetry, service discovery, resiliência, health checks,
│   │                                 # versionamento, ProblemDetails, OpenAPI
│   ├── Offering/                     # API
│   ├── BookBuilding/                 # API
│   └── DataMigration/                # Worker
├── tests/
│   ├── UnitTests/                    # xUnit
│   └── IntegrationTests/             # xUnit
├── CLAUDE.md                         # entrada das instruções do Claude Code e convenções do repositório
├── Directory.Build.props             # propriedades comuns a todos os projetos
├── Directory.Packages.props          # versões de pacote (Central Package Management)
├── global.json                       # versão do SDK .NET
└── FundDistributionPlatform.slnx
```

Os serviços de API compilam com Native AOT (`PublishAot=true`) e globalização invariante.

## Convenções

As convenções de código, commits e estrutura estão em [CLAUDE.md](CLAUDE.md). As regras do código de produção (convenções dos projetos, composição do `Program.cs`, módulos de feature e tracing) estão em `.claude/rules`, com escopo por padrão de arquivo. As skills PRD e SDD vêm do plugin `claude-skills`, instalado na conta do Claude Code; o [guia do Claude Code](docs/development/claude-code.md) descreve a instalação, as decisões de layout e a validação.
