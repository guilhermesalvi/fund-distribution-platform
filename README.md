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
│   ├── AGENTS.md                     # instruções do código de produção
│   ├── AppHost/                      # Aspire AppHost; ponto de entrada local
│   ├── ServiceDefaults/              # defaults transversais dos serviços
│   ├── Offering/                     # API
│   ├── BookBuilding/                 # API
│   └── DataMigration/                # Worker
├── tests/
│   ├── AGENTS.md                     # instruções dos testes
│   ├── UnitTests/                    # xUnit: ServiceDefaults e, por contexto, o domínio
│   └── IntegrationTests/             # xUnit + Aspire.Hosting.Testing: sobe o AppHost
├── AGENTS.md                         # entrada das instruções e convenções do repositório
├── Directory.Build.props             # propriedades comuns a todos os projetos
├── Directory.Packages.props          # versões de pacote (Central Package Management)
├── global.json                       # versão do SDK .NET
└── FundDistributionPlatform.slnx
```

Os serviços de API compilam com Native AOT (`PublishAot=true`) e globalização invariante.

## Convenções

As convenções do repositório partem do [AGENTS.md](AGENTS.md). As regras de produção ficam em [src/AGENTS.md](src/AGENTS.md), e as de testes em [tests/AGENTS.md](tests/AGENTS.md).

## Trabalhar com Codex

Inicie a sessão na raiz do repositório: no aplicativo ou na extensão, abra este diretório como projeto; na CLI, execute `codex` a partir da raiz.

O Codex monta a cadeia de instruções ao iniciar. Primeiro lê as instruções do usuário em `~/.codex/AGENTS.override.md` ou `~/.codex/AGENTS.md`; depois percorre da raiz Git até o diretório inicial. Em cada diretório, `AGENTS.override.md` prevalece sobre `AGENTS.md`, e só um arquivo é carregado. As instruções mais próximas do diretório inicial prevalecem, com limite combinado padrão de 32 KiB. Uma sessão iniciada na raiz precisa ler explicitamente as instruções de `src` ou `tests` antes de atuar nessas áreas, como orienta o arquivo da raiz. Consulte o [carregamento de AGENTS.md](https://developers.openai.com/codex/guides/agents-md).

A skill `sdd` é distribuída pelo plugin `ai-skills`, instalado na conta e usado no aplicativo ou na CLI. A extensão IDE carrega as instruções do projeto, mas não oferece suporte a plugins. Na CLI:

```bash
codex plugin marketplace add guilhermesalvi/ai-skills
codex plugin add ai-skills@ai-skills
```

Para usar uma cópia local do repositório `ai-skills`, passe ao primeiro comando o caminho do diretório no lugar de `guilhermesalvi/ai-skills`. O nome do marketplace e o do plugin continuam `ai-skills`, e a instalação não depende de publicar o plugin no GitHub.

Confira `codex plugin list --marketplace ai-skills` e, em uma sessão nova, selecione `ai-skills:sdd` no menu de skills ou peça a tarefa pela descrição. Na CLI, `/skills` permite conferir as skills disponíveis. Evite cópias pessoais ou de projeto da mesma skill, que podem causar seleção ambígua. Skills específicas deste projeto, quando necessárias, ficam em `.agents/skills/<nome>/SKILL.md`; `sdd` continua no plugin. Consulte as orientações oficiais de [skills](https://developers.openai.com/codex/skills) e [plugins](https://developers.openai.com/codex/plugins).

O repositório não fixa modelo, esforço, permissões, hooks ou MCP; a conta e o ambiente determinam a disponibilidade e as permissões. Preferências pessoais ficam em `~/.codex/config.toml`. Uma configuração do projeto em `.codex/config.toml` só é carregada quando ele é confiável. `AGENTS.override.md` e o diretório `.codex/` ficam fora do Git para preservar ajustes locais. Se houver uma necessidade concreta de configuração compartilhada, revise a regra de ignore e versione apenas o arquivo necessário na mesma mudança. Consulte as [configurações do Codex](https://developers.openai.com/codex/config-basic).

### Conferir o carregamento

Após mudar instruções, inicie sessões novas na raiz, em `src/Offering`, em `tests` e em `docs/specs`; na CLI, execute `codex` a partir de cada diretório. Peça uma revisão sem edição e confira quais fontes foram usadas: regras de produção em `src`, de testes em `tests` e a skill `sdd` quando o pedido exigir seu fluxo. Uma correção mecânica de README segue as convenções gerais, sem a skill. Na raiz e em `docs/specs`, só as instruções gerais entram automaticamente; em `src/Offering` e `tests`, a cadeia também inclui o `AGENTS.md` da área. Verifique o comportamento, além da presença dos arquivos.

Se uma instrução não aparecer, confira o diretório inicial, `AGENTS.override.md` em cada nível, as instruções do usuário em `~/.codex/`, `project_doc_max_bytes` e `project_doc_fallback_filenames`. Se a skill não aparecer, confira o plugin em `codex plugin list --marketplace ai-skills`, se está habilitado nas configurações e possíveis cópias de mesmo nome no menu de skills. Abra uma sessão nova após corrigir o setup; não copie configurações pessoais para o repositório.
