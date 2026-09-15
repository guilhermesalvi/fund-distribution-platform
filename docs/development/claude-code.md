# Claude Code neste repositório

Abra o repositório no Claude Code ou execute `claude` na raiz. As convenções comuns estão em [CLAUDE.md](../../CLAUDE.md); as regras do código de produção estão em `.claude/rules` e carregam quando um arquivo do padrão declarado entra na tarefa.

## Instruções e regras

O Claude Code carrega o `CLAUDE.md` do diretório de início e de todos os diretórios acima dele, do mais amplo ao mais específico. Iniciar na raiz ou em `src/Offering` carrega o mesmo guia geral; não há `CLAUDE.md` em subdiretórios. As regras de `.claude/rules` têm frontmatter `paths`: [production-projects.md](../../.claude/rules/production-projects.md) para qualquer arquivo em `src/`, [program-composition.md](../../.claude/rules/program-composition.md) para `Program.cs`, `*Extensions.cs`, `*Endpoint.cs` e `*Consumer.cs`, e [tracing.md](../../.claude/rules/tracing.md) para todo `.cs` de produção. Cada regra entra no contexto quando o Claude lê ou edita um arquivo que casa com o padrão, e as regras se acumulam quando os padrões coincidem. Por isso o guia geral manda abrir a regra da área ao revisar código sem lê-lo. Consulte a [documentação oficial de memória e regras](https://code.claude.com/docs/en/memory).

As instruções, descrições e exemplos narrativos das regras usam português do Brasil; identificadores, comandos e código permanecem em inglês.

O pedido define o escopo e a conclusão. Em execução autorizada, as etapas avançam sem aprovação ou commit intermediário obrigatório. Especificações ainda não commitadas podem ser usadas e verificadas, com identificação por hash de conteúdo. Um pedido apenas de planejamento termina na entrega do plano.

## Skills do plugin

As skills `prd` e `sdd` vêm do plugin [claude-skills](https://github.com/guilhermesalvi/claude-skills), de Guilherme Salvi, instalado na conta do Claude Code e não no repositório. Elas aparecem no menu `/` como `/claude-skills:prd` e `/claude-skills:sdd`, e o Claude Code também pode selecioná-las pela descrição, conforme a [documentação oficial de skills](https://code.claude.com/docs/en/skills). A revisão em uso é `183dd948aef712749f10bfac4832e4ea14ca46b6`. O plugin está em inglês e inclui o verificador de forma dos PRDs em `skills/prd/scripts/check_prd.py`, que pode ser executado a partir da pasta do plugin quando fizer sentido, fora deste repositório e fora da CI.

Instalação, em uma sessão do Claude Code:

```text
/plugin marketplace add guilhermesalvi/claude-skills
/plugin install claude-skills@claude-skills
```

Exemplos de pedidos:

```text
/claude-skills:prd Revise o PRD docs/prd/0001-offering-offer-lifecycle.md
/claude-skills:sdd Especifique o comportamento técnico da abertura de uma oferta
```

As duas skills declaram a mesma precedência: pedido da sessão, depois convenção do repositório, depois defaults da skill. O que este repositório fixa está no `CLAUDE.md` e prevalece: prosa em português com estrutura, rótulos, tags e palavras-chave EARS em inglês (Idioma); prefixo de requisito por PRD, e não por contexto (Estrutura da solução); aprovação de conteúdo separada da autorização de Git (Uso com Claude Code). Atualizar o plugin muda as skills em todos os projetos da conta; ao atualizar, registre aqui a nova revisão e confira que esses overrides continuam suficientes.

## Decisões de layout

| Decisão | Custo aceito |
| --- | --- |
| `CLAUDE.md` na raiz concentra as convenções do repositório; não há `CLAUDE.md` em subdiretórios nem `AGENTS.md` | Outras ferramentas de agente não leem o arquivo; manter um segundo arquivo de entrada duplicaria a fonte |
| Três regras em `.claude/rules` com frontmatter `paths`: convenções dos projetos de produção, composição e tracing, cada uma com o escopo que declara | A regra só entra no contexto quando um arquivo do padrão é lido ou editado; revisão sem leitura de arquivo exige abrir a regra pelo link do `CLAUDE.md` |
| Skills `prd` e `sdd` só no plugin, fora do repositório | O repositório depende de uma revisão que não controla e quem clona sem o plugin não tem as skills; os overrides do repositório precisam viver no `CLAUDE.md` |
| Sem scripts de verificação de estrutura, instruções ou documentos | Inventário do `.slnx`, links e contratos dos PRDs só são conferidos em revisão; a CI verifica apenas o código de produção |
| Exclusões de `CLAUDE.local.md`, `.claude/settings.local.json` e `.claude/worktrees/` no Git | Overrides e configurações locais ficam fora do versionamento e podem alterar as instruções da máquina |

Não há hooks, servidores MCP, agentes personalizados ou configuração de execução versionados. Não foi criado `.claude/settings.json`: fixar modelo, permissões ou variáveis compartilhadas substituiria escolhas do ambiente sem necessidade. Se o projeto vier a precisar de configuração própria, use o [formato oficial de settings](https://code.claude.com/docs/en/settings).

## Decisões da revisão das instruções

A revisão das instruções seguiu as [orientações de prompting do GPT-6 Astra](https://developers.openai.com/api/docs/guides/latest-model#prompting-best-practices) e o [guia de revisão de skills e prompts](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra). Elas orientam precedência clara, leituras pertinentes, conclusão do escopo autorizado e verificações proporcionais, princípios que não dependem da ferramenta.

| Alteração | Motivo | Custo aceito |
| --- | --- | --- |
| Português na prosa dos documentos; inglês nos contratos | Facilitar leitura e manutenção pelo time, preservando o form check das skills | A prosa não é verificada por ferramenta |
| Aprovação de conteúdo separada da autorização de Git | Permitir execução e verificação da versão atual conforme autorização | Relatórios precisam identificar a versão examinada |
| Regras de produção fora do guia geral, em `.claude/rules` | Reduzir detalhes de código no contexto de tarefas documentais | A regra precisa ser aberta pelo link quando a tarefa não lê arquivo do padrão |

## Validação

Os comandos abaixo partem da raiz e são os mesmos da CI em [ci.yml](../../.github/workflows/ci.yml):

```bash
dotnet build FundDistributionPlatform.slnx
dotnet test FundDistributionPlatform.slnx
```

Mudanças apenas em instruções e documentação usam a revisão dos exemplos e a conferência do `.slnx` descrita no `CLAUDE.md`; não há validador de estrutura nem de formato de documentos. Build e testes .NET são exigidos quando o código correspondente muda.

Depois de alterar instruções ou regras, confira a descoberta em sessões novas, uma na raiz e outra em `src/Offering`:

```bash
claude
```

Em cada sessão, execute `/context` e confira `CLAUDE.md` em Memory files; depois peça as regras aplicáveis a `src/Offering/Program.cs`, pedindo que o arquivo seja lido: devem aparecer as três regras, porque o arquivo casa com os três padrões. Confira também `/claude-skills:prd` e `/claude-skills:sdd` no menu `/`. Se não aparecerem, o plugin não está instalado ou habilitado na conta; siga Skills do plugin. Se houver duplicatas, verifique skills pessoais com o mesmo nome em `~/.claude/skills`; o repositório não altera instalações globais. Um `CLAUDE.local.md` ou uma exclusão em `claudeMdExcludes` local altera o contexto da máquina e deve ser considerado ao diagnosticar diferenças.
