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
│   └── skills/                       # skills de agente (ver Skills)
├── .github/
│   ├── scripts/                      # check_commit.py: política de commit do CLAUDE.md
│   └── workflows/                    # CI: skills.yml valida skills, PRDs, specs e commits
├── docs/
│   ├── prd/                          # PRDs (prd), um por contexto + 0000 overview
│   └── specs/                        # spec viva por capability (sdd): <contexto>/<capability>/spec.md
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

Três skills de agente em `.claude/skills/`. Duas cobrem o caminho do problema ao código verificado, cada uma com `SKILL.md` (método), `references/` (regras por etapa) e `scripts/` (linters e testes); a terceira é um método isolado, só com `SKILL.md`.

| Skill | Quando usar | Produz |
| --- | --- | --- |
| [prd](.claude/skills/prd/SKILL.md) | Problema, usuário, capability, requisitos com ID, métricas e trade-offs de uma feature ou iniciativa | `docs/prd/NNNN-<domínio>-<feature>.md` |
| [ontology-from-transcript](.claude/skills/ontology-from-transcript/SKILL.md) | Transcrição de reunião com especialista de domínio: conceitos, relações, termos, atributos e restrições em oito passadas | Uma tabela por passada, como hipóteses a validar com o especialista |
| [sdd](.claude/skills/sdd/SKILL.md) | A partir de um PRD (ou pedido rico): spec técnica (EARS), design, tasks, implementação e verificação com evidência | `docs/specs/<contexto>/<capability>/spec.md` (viva) e `NNNN-<slug>/` (`design.md`, `tasks.md`) quando a mudança pede |

Pré-requisitos dos scripts: Python 3 (testado com 3.11 localmente e 3.12 na CI) e, para validar os diagramas Mermaid dos PRDs e dos designs, Node 22 com o parser instalado uma vez por clone (único passo com acesso à rede). Cada skill é um pacote autocontido e traz o seu parser:

```bash
python3 .claude/skills/prd/scripts/lint_mermaid.py --setup
python3 .claude/skills/sdd/scripts/lint_mermaid.py --setup
```

Validação completa, a mesma que a CI executa (`.github/workflows/skills.yml`): o gate determinístico das skills, que roda suítes, self-test dos parsers, linters sobre `docs/`, independência entre skills, codificação e registro no `.slnx` e neste README, cada check com limite explícito. Toda mudança em `.claude/skills/**` passa por ele antes do commit; [GATE.md](.claude/skills/GATE.md) lista os checks e descreve a segunda etapa, a revisão cética com nota mínima, que o script não roda.

```bash
python3 .github/scripts/skills_gate.py
```

Scripts individuais, para validar um artefato durante o trabalho:

```bash
python3 .claude/skills/prd/scripts/lint_mermaid.py --self-test
python3 .claude/skills/sdd/scripts/lint_mermaid.py --self-test
python3 -m unittest discover -s .claude/skills/prd/scripts/tests
python3 -m unittest discover -s .claude/skills/sdd/scripts/tests
python3 .claude/skills/prd/scripts/seq.py check docs/prd
python3 .claude/skills/prd/scripts/lint_prd.py docs/prd
python3 .claude/skills/prd/scripts/lint_mermaid.py docs/prd
python3 .claude/skills/sdd/scripts/seq.py check docs/specs/<contexto>/<capability>
python3 .claude/skills/sdd/scripts/lint_spec.py docs/specs/<contexto>/<capability>/spec.md
python3 .claude/skills/sdd/scripts/lint_design.py docs/specs/<contexto>/<capability>/<NNNN-slug>/design.md --spec docs/specs/<contexto>/<capability>/spec.md
python3 .claude/skills/sdd/scripts/lint_tasks.py docs/specs/<contexto>/<capability>/<NNNN-slug>/tasks.md --spec docs/specs/<contexto>/<capability>/spec.md
python3 .claude/skills/sdd/scripts/lint_adr.py docs/adr
python3 .claude/skills/sdd/scripts/lint_mermaid.py docs/specs
```

Em pull requests, a CI valida cada mensagem de commit com `.github/scripts/check_commit.py` e o perfil de [CLAUDE.md](CLAUDE.md), e confere que nenhuma skill cita a outra pelo nome.

Semântica da saída dos linters: `HARD` bloqueia (exit 1) e precisa de correção antes de o artefato ser apresentado; nos dois `lint_mermaid.py`, `HARD INCOMPLETO` é validação que não pôde ser feita (parser Mermaid ausente), nunca sucesso, com exit 3 (nenhum dos outros linters chama o parser); `WARN` é heurística para julgamento e não afeta o exit; exit 2 é erro de uso (opção ou arquivo inválido). Cada script imprime o que checa quando chamado sem argumentos.

A CI executa o gate e, em pull requests, a validação das mensagens de commit. Ela não executa avaliação comportamental do agente (se a skill certa é acionada, se as autorizações são respeitadas): isso exige cenários com o modelo e ainda não está automatizado.
