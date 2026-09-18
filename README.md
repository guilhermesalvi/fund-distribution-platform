# Fund Distribution Platform

Modelo executável do comportamento regulado pela Resolução CVM 160 (ofertas públicas) e pela Resolução CVM 175 (fundos), reduzido ao mínimo viável, para o caso de uso de corretora distribuindo cotas de classe fechada a investidor final. Não há liquidação financeira nem integração externa; o investidor não acessa a plataforma, e o operador da corretora age em seu nome. O domínio está descrito nos PRDs de `docs/prd`, a partir da [visão geral](docs/prd/0000-platform-overview.md); cada PRD registra suas decisões, com custo e motivo, e as fontes regulatórias.

Plataforma composta por dois serviços, um por contexto de domínio, e um worker de migração de dados. O comportamento de negócio ainda não está implementado: os serviços são o esqueleto de composição (`Program.cs` com `ServiceDefaults`), sem endpoints nem regras de domínio, e o worker é o modelo do template. O que cada projeto fará está nos PRDs:

| Projeto | Tipo | Responsabilidade prevista |
| --- | --- | --- |
| `Offering` | API | Definição e ciclo de vida da oferta ([PRD 0001](docs/prd/0001-offering-offer-lifecycle.md)) |
| `BookBuilding` | API | Reservas, fechamento e processamento do livro ([PRD 0002](docs/prd/0002-book-building-bid-lifecycle.md), [PRD 0003](docs/prd/0003-book-building-book-processing.md)) |
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
├── .claude/
│   └── agents/                       # subagentes planner e worker
├── .github/workflows/                # CI: build, testes e publicação AOT
├── docs/
│   └── prd/                          # CLAUDE.md, overview e PRDs das capabilities
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

## Desenvolvimento com Claude Code

Abra o projeto no aplicativo Claude Code ou execute `claude` na raiz do repositório: a sessão carrega o `CLAUDE.md` da raiz e os subagentes de `.claude/agents/`. Permissões, autenticação, hooks e MCP continuam sob controle do ambiente do usuário.

Instale o plugin de skills uma vez no seu ambiente, a partir da raiz do checkout local do plugin:

```bash
claude plugin marketplace add .
claude plugin install ai-skills@ai-skills
```

Use `/ai-skills:prd` para requisitos de produto e `/ai-skills:sdd` para trabalho técnico; Claude também seleciona as skills pela descrição do pedido. Rode `/reload-plugins` ou inicie uma nova sessão após instalar ou atualizar o plugin. As skills são mantidas no plugin; suas cópias não ficam neste repositório.

Os papéis de subagentes estão configurados para distribuir o esforço conforme a tarefa:

| Papel | Modelo | Esforço | Uso |
| --- | --- | --- | --- |
| [planner](.claude/agents/planner.md) | `opus` | `high` | Planejamento e revisão complexos, sem editar arquivos |
| [worker](.claude/agents/worker.md) | `sonnet` | `medium` | Execução delimitada e verificação |

Delegue com `@agent-planner` e `@agent-worker` ou descrevendo a subtarefa. O modelo da sessão principal é escolhido no cliente. A disponibilidade dos modelos depende da conta e do cliente; o guia do repositório orienta como lidar com uma capacidade ausente.

Após alterar instruções ou agentes, confira o carregamento em uma nova sessão, pelos Memory files de `/context`, na raiz e nas áreas `src/Offering`, `tests` e `docs/prd`. A sessão iniciada na raiz deve ler explicitamente o guia da área antes de atuar nela. Confira também as skills disponíveis no menu `/` e o plugin em `/plugin`.

Referências oficiais: [instruções com CLAUDE.md](https://code.claude.com/docs/en/memory) e [subagentes](https://code.claude.com/docs/en/sub-agents).
