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

```bash
dotnet build FundDistributionPlatform.slnx
```

```bash
dotnet test FundDistributionPlatform.slnx
```

## Estrutura do repositório

```text
.
├── .agents/
│   └── skills/                       # skills locais do Codex (ver Skills)
├── .github/
│   ├── scripts/                      # check_commit.py (política de commit) e skills_gate.py (gate das skills)
│   └── workflows/                    # CI: skills.yml roda o gate das skills e valida commits de PR
├── docs/
│   ├── development/                  # regras por área: composição do Program.cs, tracing
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
├── AGENTS.md                         # entrada das instruções do Codex e convenções do repositório
├── Directory.Build.props             # propriedades comuns a todos os projetos
├── Directory.Packages.props          # versões de pacote (Central Package Management)
└── FundDistributionPlatform.slnx
```

Os serviços de API compilam com Native AOT (`PublishAot=true`) e globalização invariante.

## Convenções

As convenções de código, commits e estrutura estão em [AGENTS.md](AGENTS.md). Regras específicas por área (composição do `Program.cs`, módulos de feature, tracing) estão em [docs/development](docs/development).

## Desenvolvimento com Codex

Abra a pasta do repositório no aplicativo Codex ou inicie o [Codex CLI](https://developers.openai.com/codex/cli/) na raiz:

```bash
codex
```

O projeto usa `AGENTS.md` para instruções e `.agents/skills/` para as três skills locais. Não é necessário copiar as skills para a configuração pessoal. Em uma sessão nova, confira se `prd`, `sdd` e `ontology-from-transcript` aparecem no seletor de skills; no CLI, também podem ser invocadas pelo nome com `$`. As instruções da raiz direcionam a leitura das regras por área mesmo quando a tarefa começa em um subdiretório. Consulte a documentação oficial de [AGENTS.md](https://developers.openai.com/codex/guides/agents-md) e [skills](https://developers.openai.com/codex/skills).

Exemplos de pedidos na conversa:

```text
$prd escreva os requisitos de produto para a capability descrita abaixo: ...
$sdd especifique tecnicamente a capability descrita abaixo: ...
$ontology-from-transcript extraia os conceitos desta transcrição: ...
```

Modelo, autenticação e preferências pessoais ficam na instalação do Codex. Este repositório não precisa de `.codex/config.toml` para carregar suas instruções e skills.

Depois de mudar instruções ou skills, valide em sessões novas na raiz e em `src/Offering`: peça as convenções ativas e as regras aplicáveis a `Program.cs`, confirme a descoberta das três skills e experimente os pedidos acima com exemplos temporários. Um pedido de documentação geral não deve iniciar `prd` ou `sdd`; sem transcrição, a skill de ontologia não deve inventar conceitos. Essa verificação comportamental complementa o gate determinístico.

## Skills

Três skills de agente em `.agents/skills/`. Duas cobrem o caminho do problema ao código verificado, cada uma com `SKILL.md` (método), `references/` (regras por etapa) e `scripts/` (linters e testes); a terceira é um método isolado, só com `SKILL.md`.

| Skill | Quando usar | Produz |
| --- | --- | --- |
| [prd](.agents/skills/prd/SKILL.md) | Problema, usuário, capability, requisitos com ID, métricas e trade-offs de uma feature ou iniciativa | `docs/prd/NNNN-<domínio>-<feature>.md` |
| [ontology-from-transcript](.agents/skills/ontology-from-transcript/SKILL.md) | Transcrição de reunião com especialista de domínio: conceitos, relações, termos, atributos e restrições em oito passadas | Uma tabela por passada, como hipóteses a validar com o especialista |
| [sdd](.agents/skills/sdd/SKILL.md) | A partir de um PRD (ou pedido rico): spec técnica (EARS), design, tasks, implementação e verificação com evidência | `docs/specs/<contexto>/<capability>/spec.md` (viva) e `NNNN-<slug>/` (`design.md`, `tasks.md`) quando a mudança pede |

Os `SKILL.md` selecionam a entrada e as referências necessárias. Processo, formato e escrita têm fontes distintas dentro de cada pacote; uma correção localizada lê o trecho afetado, suas dependências e seus citadores. A leitura seletiva mantém as validações exigidas.

| Pacote | Processo e convenções | Escrita e exemplos |
| --- | --- | --- |
| PRD | [workflow.md](.agents/skills/prd/references/workflow.md): geração, checagem e revisão; [conventions.md](.agents/skills/prd/references/conventions.md): gravação e idioma | [prose.md](.agents/skills/prd/references/prose.md): política editorial local; [writing.md](.agents/skills/prd/references/writing.md): regras e formas por seção; [example.md](.agents/skills/prd/references/example.md): PRD completo e reescrita didática |
| SDD | [workflow.md](.agents/skills/sdd/references/workflow.md): pré-requisitos e autorizações; [validation.md](.agents/skills/sdd/references/validation.md): scripts, ciclos e rubricas | [prose.md](.agents/skills/sdd/references/prose.md): política editorial local; cada referência de entrada traz seu perfil de escrita e os exemplos pertinentes |

As políticas editoriais preservam IDs, tags, formatos, modalidades e significado. A revisão usa os ciclos existentes; exemplos parciais em blocos `text` ilustram a redação e não constituem evidência de execução. As referências de escrita dos dois pacotes são independentes.

Pré-requisitos dos scripts: Python 3 (testado com 3.14 localmente e 3.12 na CI) e, para validar os diagramas Mermaid dos PRDs e dos designs, Node 22 com o parser instalado uma vez por clone (único passo com acesso à rede). Cada skill é um pacote autocontido e traz o seu parser:

```bash
python3 .agents/skills/prd/scripts/lint_mermaid.py --setup
python3 .agents/skills/sdd/scripts/lint_mermaid.py --setup
```

Validação completa, a mesma que a CI executa (`.github/workflows/skills.yml`): o gate determinístico das skills, que roda suítes, self-test dos parsers, linters sobre `docs/`, independência entre skills, codificação e registro no `.slnx` e neste README, cada check com limite explícito. Toda mudança em `.agents/skills/**` passa por ele antes do commit; [GATE.md](.agents/skills/GATE.md) lista os checks e descreve a segunda etapa, a revisão cética com nota mínima, que o script não roda.

```bash
python3 .github/scripts/skills_gate.py
```

Scripts individuais, para validar um artefato durante o trabalho:

```bash
python3 .agents/skills/prd/scripts/lint_mermaid.py --self-test
python3 .agents/skills/sdd/scripts/lint_mermaid.py --self-test
python3 -m unittest discover -s .agents/skills/prd/scripts/tests
python3 -m unittest discover -s .agents/skills/sdd/scripts/tests
python3 .agents/skills/prd/scripts/seq.py check docs/prd
python3 .agents/skills/prd/scripts/lint_prd.py docs/prd
python3 .agents/skills/prd/scripts/lint_mermaid.py docs/prd
python3 .agents/skills/sdd/scripts/seq.py check docs/specs/<contexto>/<capability>
python3 .agents/skills/sdd/scripts/lint_spec.py docs/specs/<contexto>/<capability>/spec.md
python3 .agents/skills/sdd/scripts/lint_design.py docs/specs/<contexto>/<capability>/<NNNN-slug>/design.md --spec docs/specs/<contexto>/<capability>/spec.md
python3 .agents/skills/sdd/scripts/lint_tasks.py docs/specs/<contexto>/<capability>/<NNNN-slug>/tasks.md --spec docs/specs/<contexto>/<capability>/spec.md
python3 .agents/skills/sdd/scripts/lint_adr.py docs/adr
python3 .agents/skills/sdd/scripts/lint_mermaid.py docs/specs
```

A CI executa o gate em todo push e pull request e, em pull requests, valida cada mensagem de commit com `.github/scripts/check_commit.py` e o perfil de [AGENTS.md](AGENTS.md).

Semântica da saída dos linters: `HARD` retorna exit 1; sua correção, as exceções de forma por pedido/convenção e a apresentação com achados após o teto seguem [Checar da PRD](.agents/skills/prd/references/workflow.md#checar) ou [Scripts da SDD](.agents/skills/sdd/references/validation.md#scripts). Apresentar com achados não comprova validação nem aprovação. Nos dois `lint_mermaid.py`, `HARD INCOMPLETO` indica validação não realizada por parser ausente, nunca sucesso, com exit 3; a autorização de setup e a apresentação sem essa verificação seguem os mesmos ciclos. `WARN` é heurística e não afeta o exit; cada ciclo define seu tratamento. Exit 2 é erro de uso (opção ou arquivo inválido). Cada script imprime o que checa quando chamado sem argumentos. O gate do repositório mantém seu limite de zero HARD e bloqueia commit quando algum check falha.

A CI não executa avaliação comportamental do agente (se a skill certa é acionada, se as autorizações são respeitadas): isso exige cenários com o modelo e ainda não está automatizado.

Testes da reforma das skills, já descobertos pela suíte do gate em `.github/scripts/tests`:

```bash
python3 -m unittest discover -s .github/scripts/tests -p test_skill_snapshot.py
python3 -m unittest discover -s .github/scripts/tests -p test_skill_routing.py
python3 -m unittest discover -s .github/scripts/tests -p test_skill_editorial.py
```

`test_skill_snapshot.py` reproduz em Git temporário a diferença entre HEAD, índice e árvore de trabalho. `test_skill_routing.py` confere o contrato estrutural das entradas. `test_skill_editorial.py` verifica políticas locais, remissões, perfis e exemplos parciais, mantendo os templates completos sob as suítes dos linters. Os dois últimos não medem a decisão de um modelo nem a qualidade editorial do resultado; essas avaliações precisam de evidência própria.
