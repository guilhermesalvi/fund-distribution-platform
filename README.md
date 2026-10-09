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

As convenções do repositório e as instruções do Claude Code partem do [CLAUDE.md](CLAUDE.md). As regras de produção ficam em [src/CLAUDE.md](src/CLAUDE.md), e as de testes em [tests/CLAUDE.md](tests/CLAUDE.md).

## Trabalhar com Claude Code

Inicie a sessão na raiz do repositório: no aplicativo ou na extensão, abra este diretório como projeto; na CLI, execute `claude` a partir da raiz.

O Claude Code carrega as instruções do usuário e, ao iniciar, os arquivos `CLAUDE.md` e `CLAUDE.local.md` do diretório inicial e dos ancestrais. O `CLAUDE.md` de um subdiretório abaixo do inicial entra no contexto só quando Claude lê, escreve ou edita um arquivo ali; uma sessão iniciada na raiz lê as instruções de `src` ou `tests` antes de atuar nessas áreas, como orienta o arquivo da raiz. A documentação recomenda menos de 200 linhas por `CLAUDE.md`. Consulte o [carregamento de CLAUDE.md](https://code.claude.com/docs/en/memory#how-claude-md-files-load).

A skill `sdd` é distribuída pelo plugin `ai-skills`, instalado no escopo do usuário, que é o padrão dos comandos:

```bash
claude plugin marketplace add guilhermesalvi/ai-skills
claude plugin install ai-skills@ai-skills
```

Para usar uma cópia local do repositório `ai-skills`, passe ao primeiro comando o caminho do diretório no lugar de `guilhermesalvi/ai-skills`. O nome do marketplace e o do plugin continuam `ai-skills`, e a instalação não depende de publicar o plugin no GitHub.

Confira `claude plugin list` e, em uma sessão nova, invoque `/ai-skills:sdd` ou peça a tarefa pela descrição; `/skills` lista as skills disponíveis. Não crie cópias pessoais ou de projeto com o mesmo nome: elas carregam junto com a do plugin, que continua em `/ai-skills:sdd`, e passam a responder por `/sdd`. Skills específicas deste projeto, quando necessárias, ficam em `.claude/skills/<nome>/SKILL.md`; `sdd` continua no plugin. Consulte as orientações oficiais de [skills](https://code.claude.com/docs/en/skills) e da [CLI de plugins](https://code.claude.com/docs/en/plugins/cli-reference).

O repositório não fixa modelo, esforço, permissões, hooks ou MCP; a conta e o ambiente determinam a disponibilidade e as permissões. Preferências pessoais ficam em `~/.claude/settings.json`, e as pessoais deste projeto, em `.claude/settings.local.json`. Um `.claude/settings.json` compartilhado só deve ser criado por uma necessidade concreta do projeto. `CLAUDE.local.md`, `.claude/settings.local.json` e os worktrees em `.claude/worktrees/` são locais e ficam fora do Git. Consulte as [configurações do Claude Code](https://code.claude.com/docs/en/settings).

### Conferir o carregamento

Após mudar instruções, inicie sessões novas na raiz, em `src/Offering`, em `tests` e em `docs/specs`; na CLI, execute `claude` a partir de cada diretório. Peça uma revisão sem edição e confira quais fontes foram usadas: regras de produção em `src`, de testes em `tests` e a skill `sdd` quando o pedido exigir seu fluxo. Uma correção mecânica de README segue as convenções gerais, sem a skill. Em `/context`, a lista Memory files mostra os `CLAUDE.md` carregados; o de um subdiretório só aparece depois de carregado. Verifique o comportamento, além da presença dos arquivos.

Se uma instrução não aparecer, confira o diretório inicial, `CLAUDE.local.md`, as instruções do usuário em `~/.claude/CLAUDE.md` e `claudeMdExcludes` nas configurações. Se a skill não aparecer, confira o plugin em `claude plugin list` e possíveis cópias de mesmo nome em `/skills`. Abra uma sessão nova após corrigir o setup; não copie configurações pessoais para o repositório. Para diagnosticar, um hook [`InstructionsLoaded`](https://code.claude.com/docs/en/hooks#instructionsloaded) nas configurações pessoais informa cada `CLAUDE.md` carregado e o motivo do carregamento.
