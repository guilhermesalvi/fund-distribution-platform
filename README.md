# Fund Distribution Platform

Modelo executável do comportamento regulado pela Resolução CVM 160 (ofertas públicas) e pela Resolução CVM 175 (fundos), reduzido ao mínimo viável, para o caso de uso de corretora distribuindo cotas de fundo fechado a investidor final. Não há liquidação financeira nem integração externa; o investidor não acessa a plataforma, e o operador da corretora age em seu nome. O domínio está descrito nos PRDs de `docs/prd`, a partir da [visão geral](docs/prd/0000-platform-overview.md).

Plataforma composta por três serviços, um por contexto de domínio, e um worker de migração de dados:

| Projeto | Tipo | Responsabilidade |
| --- | --- | --- |
| `Offering` | API | Definição imutável da oferta e sua máquina de estados ([PRD 0001](docs/prd/0001-offering-offer-lifecycle.md)) |
| `ReservationBook` | API | Reservas contra oferta Aberta; livro congelado no fechamento; status por reserva ([PRD 0002](docs/prd/0002-reservation-book-reservation-lifecycle.md)) |
| `Allocation` | API | Processamento único do livro fechado: vedação a vinculadas, formação, condicionamento e rateio ([PRD 0003](docs/prd/0003-allocation-book-processing.md)) |
| `DataMigration` | Worker | Migração de dados. Não expõe HTTP. |

## Pré-requisitos

- .NET SDK 10 (desenvolvido com 10.0.400)
- Aspire CLI 13.5 (`aspire --version`)

## Como rodar

```bash
aspire run --apphost src/AppHost/AppHost.csproj
```

O comando compila a solução, sobe os quatro projetos e abre o dashboard do Aspire em `https://localhost:17150`. O dashboard mostra logs, traces e métricas de todos os serviços.

Portas dos serviços em desenvolvimento:

| Serviço | URL |
| --- | --- |
| Offering | `http://localhost:5084` |
| ReservationBook | `http://localhost:5129` |
| Allocation | `http://localhost:5288` |

Cada API expõe, apenas em ambiente `Development`:

- `/health` — todos os health checks precisam passar.
- `/alive` — só os checks marcados como `live`.
- `/openapi/v1.json` — documento OpenAPI.

## Build e testes

Os comandos de build e teste, e o momento de rodá-los, estão em [CLAUDE.md](CLAUDE.md), seção Build e testes.

## Estrutura do repositório

```text
.
├── .claude/
│   ├── rules/                        # regras por área: composição do Program.cs, tracing
│   └── skills/                       # skills do Claude Code (ver Skills)
├── docs/
│   └── prd/                          # PRDs (prd), um por contexto + 0000 overview
├── src/
│   ├── AppHost/                      # Aspire AppHost; ponto de entrada local
│   ├── ServiceDefaults/              # OpenTelemetry, service discovery, resiliência, health checks,
│   │                                 # versionamento, ProblemDetails, OpenAPI
│   ├── Offering/                     # API
│   ├── ReservationBook/              # API
│   ├── Allocation/                   # API
│   └── DataMigration/                # Worker
├── tests/
│   ├── UnitTests/                    # xUnit
│   └── IntegrationTests/             # xUnit
├── CLAUDE.md                         # entrada das instruções do Claude Code e convenções do repositório
├── Directory.Build.props             # propriedades comuns a todos os projetos
├── Directory.Packages.props          # versões de pacote (Central Package Management)
└── FundDistributionPlatform.slnx
```

Os serviços de API compilam com Native AOT (`PublishAot=true`) e globalização invariante.

## Convenções

As convenções de código, commits e estrutura estão em [CLAUDE.md](CLAUDE.md). Regras específicas por área (composição do `Program.cs`, módulos de feature, tracing) estão em [.claude/rules](.claude/rules) e carregam sozinhas quando um arquivo do padrão delas entra na tarefa.

## Desenvolvimento com Claude Code

Abra a pasta do repositório no aplicativo Claude Code ou inicie o [Claude Code](https://docs.claude.com/en/docs/claude-code/overview) na raiz. O projeto usa `CLAUDE.md` para instruções, `.claude/rules/` para as regras por área e `.claude/skills/` para as duas skills locais; nada precisa ser copiado para a configuração pessoal. Em uma sessão nova, `/prd` e `/sdd` aparecem no menu `/`, e o Claude Code também aciona a skill sozinho quando o pedido se enquadra na descrição dela. Consulte a documentação oficial de [CLAUDE.md](https://docs.claude.com/en/docs/claude-code/memory) e [skills](https://docs.claude.com/en/docs/claude-code/skills).

Exemplos de pedidos na conversa:

```text
/prd escreva os requisitos de produto para a capability descrita abaixo: ...
/sdd especifique tecnicamente a capability descrita abaixo: ...
```

Modelo, autenticação e preferências pessoais ficam na instalação do Claude Code e em `.claude/settings.local.json`, que não é versionado.

Depois de mudar instruções ou skills, valide em sessões novas na raiz e em `src/Offering`: peça as convenções ativas e as regras aplicáveis a `Program.cs`, confirme as duas skills no menu `/` e experimente os pedidos acima com exemplos temporários. Um pedido de documentação geral não deve iniciar `prd` ou `sdd`.

## Skills

Duas skills de agente em `.claude/skills/` cobrem o caminho do problema ao código verificado, cada uma com `SKILL.md` (método) e `references/` (regras por etapa).

| Skill | Quando usar | Produz |
| --- | --- | --- |
| [prd](.claude/skills/prd/SKILL.md) | Problema, usuário, capability, requisitos com ID, métricas e trade-offs de uma feature ou iniciativa | `docs/prd/NNNN-<domínio>-<feature>.md` |
| [sdd](.claude/skills/sdd/SKILL.md) | A partir de um PRD (ou pedido rico): spec técnica (EARS), design, tasks, implementação e verificação com evidência | `docs/specs/<contexto>/<capability>/spec.md` (viva) e `NNNN-<slug>/` (`design.md`, `tasks.md`) quando a mudança pede |

Os `SKILL.md` selecionam a entrada e as referências necessárias. Processo, formato e escrita têm fontes distintas dentro de cada pacote; uma correção localizada lê o trecho afetado, suas dependências e seus citadores. A leitura seletiva mantém as validações exigidas.

| Pacote | Processo e convenções | Escrita e exemplos |
| --- | --- | --- |
| PRD | [workflow.md](.claude/skills/prd/references/workflow.md): geração, checagem e revisão; [conventions.md](.claude/skills/prd/references/conventions.md): gravação e idioma | [prose.md](.claude/skills/prd/references/prose.md): política editorial local; [writing.md](.claude/skills/prd/references/writing.md): regras e formas por seção; [example.md](.claude/skills/prd/references/example.md): PRD completo e reescrita didática |
| SDD | [workflow.md](.claude/skills/sdd/references/workflow.md): pré-requisitos e autorizações; [validation.md](.claude/skills/sdd/references/validation.md): checagem de forma, ciclos e rubricas | [prose.md](.claude/skills/sdd/references/prose.md): política editorial local; cada referência de entrada traz seu perfil de escrita e os exemplos pertinentes |

As políticas editoriais preservam IDs, tags, formatos, modalidades e significado. A revisão usa os ciclos existentes; exemplos parciais em blocos `text` ilustram a redação e não constituem evidência de execução. As referências de escrita dos dois pacotes são independentes.

As skills não trazem scripts: toda checagem de forma é feita lendo o artefato, item a item, conforme a referência de validação de cada pacote. Scripts voltam a entrar quando uma verificação repetível justificar o custo de mantê-los.
