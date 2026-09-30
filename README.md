# Fund Distribution Platform

Modelo executável do comportamento regulado pela Resolução CVM 160 (ofertas públicas) e pela Resolução CVM 175 (fundos), reduzido ao mínimo viável, para o caso de uso de corretora distribuindo cotas de classe fechada a investidor final. Não há liquidação financeira nem integração externa; o investidor não acessa a plataforma, e o operador da corretora age em seu nome. O domínio está descrito em `docs/specs`, uma spec por capability; cada spec registra suas regras, suas decisões, com custo e motivo, e as fontes regulatórias.

Plataforma composta por dois serviços, um por contexto de domínio, e um worker de migração de dados. Cada contexto mantém sua persistência, e os dois se comunicam por eventos: o Offering é upstream, e o BookBuilding consome a definição e o estado da oferta e devolve o desfecho do livro. O comportamento de negócio ainda não está implementado: os serviços são o esqueleto de composição (`Program.cs` com `ServiceDefaults`), sem endpoints nem regras de domínio, e o worker é o modelo do template. O que cada projeto fará está nas specs:

| Projeto | Tipo | Responsabilidade prevista |
| --- | --- | --- |
| `Offering` | API | [Ciclo de Vida da Oferta](docs/specs/offer-lifecycle/spec.md) |
| `BookBuilding` | API | [Livro de Reservas](docs/specs/bid-book/spec.md) e [Processamento do Livro](docs/specs/book-processing/spec.md) |
| `DataMigration` | Worker | Migração de dados. Não expõe HTTP. |

O que já existe e roda: AppHost do Aspire com os três projetos, `ServiceDefaults` (OpenTelemetry, service discovery, resiliência HTTP, health checks, versionamento de API, ProblemDetails e OpenAPI) e os endpoints de diagnóstico listados abaixo.

## Pré-requisitos

- .NET SDK 10.0.400 ou feature band mais recente do .NET 10, conforme `global.json` (`rollForward: latestFeature`)
- Aspire CLI 13.5.3 (`aspire --version`); o AppHost usa o bundle da CLI, inclusive nos testes de integração

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

A CI ([ci.yml](.github/workflows/ci.yml)) executa os mesmos comandos no `ubuntu-latest` em push e pull request na `main`, com o SDK do `global.json` e a Aspire CLI instalada pelo script oficial. Um segundo job publica `Offering` e `BookBuilding` com Native AOT para `linux-x64`:

```bash
dotnet publish src/Offering/Offering.csproj -c Release -r linux-x64
```

No Windows, use `-r win-x64` com o Build Tools do Visual Studio instalado.

## Estrutura do repositório

```text
.
├── .github/workflows/                # CI: build, testes e publicação AOT
├── docs/
│   ├── adr/                          # decisões que valem para mais de uma capability
│   └── specs/                        # uma spec por capability
├── src/
│   ├── CLAUDE.md                     # instruções do código de produção
│   ├── AppHost/                      # Aspire AppHost; ponto de entrada local
│   ├── ServiceDefaults/              # defaults transversais dos serviços
│   ├── Offering/                     # API
│   ├── BookBuilding/                 # API
│   └── DataMigration/                # Worker
├── tests/
│   ├── CLAUDE.md                     # instruções dos testes
│   ├── UnitTests/                    # xUnit: ServiceDefaults e, por contexto, o domínio
│   └── IntegrationTests/             # xUnit + Aspire.Hosting.Testing: sobe o AppHost
├── CLAUDE.md                         # entrada das instruções e convenções do repositório
├── Directory.Build.props             # propriedades comuns a todos os projetos
├── Directory.Packages.props          # versões de pacote (Central Package Management)
├── global.json                       # versão do SDK .NET
└── FundDistributionPlatform.slnx
```

Os serviços de API compilam com Native AOT (`PublishAot=true`) e globalização invariante.

## Convenções

As convenções do repositório e as instruções do Claude Code partem do [CLAUDE.md](CLAUDE.md).

Para trabalhar com Claude Code, inicie a sessão na raiz do repositório. O repositório não fixa modelo, esforço, permissões, hooks ou MCP; a conta e o ambiente determinam a disponibilidade e as permissões.

A skill `sdd` vem do plugin `ai-skills`, instalado uma vez no escopo do usuário:

```bash
claude plugin marketplace add guilhermesalvi/ai-skills
claude plugin install ai-skills@ai-skills
```
