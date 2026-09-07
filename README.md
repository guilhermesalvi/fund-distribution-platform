# Fund Distribution Platform

<!-- TODO: parágrafo sobre o domínio -->

Plataforma composta por três serviços, um por contexto de domínio, e um worker de migração de dados:

| Projeto | Tipo | Responsabilidade |
| --- | --- | --- |
| `Offering` | API | <!-- TODO --> |
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

```bash
dotnet build FundDistributionPlatform.slnx
```

```bash
dotnet test FundDistributionPlatform.slnx
```

## Estrutura do repositório

```text
.
├── .claude/
│   ├── rules/                        # regras por área: composição do Program.cs, tracing
│   └── skills/                       # skills de agente: prd-writer e spec-driven (ver Skills)
├── .github/
│   └── workflows/                    # CI: skills.yml valida skills, PRDs, specs e commits
├── docs/
│   ├── prd/                          # PRDs (prd-writer), um por contexto + 0000 overview
│   └── specs/                        # specs por capability (spec-driven): changes/NNNN-<slug>/
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
├── CLAUDE.md                         # convenções do repositório
├── Directory.Build.props             # propriedades comuns a todos os projetos
├── Directory.Packages.props          # versões de pacote (Central Package Management)
└── FundDistributionPlatform.slnx
```

Os serviços de API compilam com Native AOT (`PublishAot=true`) e globalização invariante.

## Convenções

As convenções de código, commits e estrutura estão em [CLAUDE.md](CLAUDE.md). Regras específicas por área (composição do `Program.cs`, módulos de feature, tracing) estão em [.claude/rules](.claude/rules).

## Skills

Duas skills de agente em `.claude/skills/` cobrem o caminho do problema ao código verificado; cada uma tem um `SKILL.md` (roteador), `references/` (regras por etapa) e `scripts/` (linters e testes).

| Skill | Quando usar | Produz |
| --- | --- | --- |
| [prd-writer](.claude/skills/prd-writer/SKILL.md) | Problema, usuário, capability, requisitos com ID, métricas e trade-offs de uma feature ou iniciativa | `docs/prd/NNNN-<domínio>-<feature>.md` |
| [spec-driven](.claude/skills/spec-driven/SKILL.md) | A partir de um PRD (ou pedido rico): spec técnica (EARS), design, tasks, implementação e verificação com evidência | `docs/specs/<contexto>/<capability>/changes/NNNN-<slug>/` (`spec.md`, `design.md`, `tasks.md`, `validation.md`) |

Pré-requisitos dos scripts: Python 3 (testado com 3.11 localmente e 3.12 na CI) e, para validar os diagramas Mermaid dos PRDs, Node 22 com o parser instalado uma vez por clone (único passo com acesso à rede):

```bash
python3 .claude/skills/prd-writer/scripts/lint_mermaid.py --setup
```

Validação completa, a mesma que a CI executa (`.github/workflows/skills.yml`):

```bash
python3 .claude/skills/prd-writer/scripts/lint_mermaid.py --self-test
python3 -m unittest discover -s .claude/skills/prd-writer/scripts/tests
python3 -m unittest discover -s .claude/skills/spec-driven/scripts/tests
python3 .claude/skills/prd-writer/scripts/seq.py check docs/prd
python3 .claude/skills/prd-writer/scripts/lint_prd.py docs/prd
python3 .claude/skills/spec-driven/scripts/seq.py check docs/specs
python3 .claude/skills/spec-driven/scripts/lint_spec.py docs/specs/<contexto>/<capability>/changes/<NNNN-slug>/spec.md
```

A CI ainda roda `apply_delta.py check` em cada delta cuja capability já tem spec viva e, em pull requests, valida cada mensagem de commit com o perfil de [CLAUDE.md](CLAUDE.md).

Semântica da saída dos linters: `HARD` bloqueia (exit 1) e precisa de correção antes de o artefato ser apresentado; `HARD INCOMPLETO` é validação que não pôde ser feita (parser Mermaid ausente, PRD ou spec viva não encontrados), nunca sucesso, e `lint_mermaid.py` sozinho sai com exit 3 nesse caso; `WARN` é heurística para julgamento e não afeta o exit; exit 2 é erro de uso (opção ou arquivo inválido). No Verify da spec-driven, o veredito `BLOCKED` marca verificação incompleta por ambiente e não fecha a mudança. Cada script imprime o que checa quando chamado sem argumentos.

A CI executa exatamente esses passos e, em pull requests, a validação das mensagens de commit. Ela não executa avaliação comportamental do agente (se a skill certa é acionada, se as autorizações são respeitadas): isso exige cenários com o modelo e ainda não está automatizado.
