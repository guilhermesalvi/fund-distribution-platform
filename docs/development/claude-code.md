# Claude Code neste repositório

Abra o repositório no Claude Code ou execute `claude` na raiz. As convenções comuns estão em [CLAUDE.md](../../CLAUDE.md); as regras do código de produção estão em `.claude/rules` e carregam quando um arquivo do padrão declarado entra na tarefa.

## Instruções, regras e skills

O Claude Code carrega o `CLAUDE.md` do diretório de início e de todos os diretórios acima dele, do mais amplo ao mais específico. Iniciar na raiz ou em `src/Offering` carrega o mesmo guia geral; não há `CLAUDE.md` em subdiretórios. As regras de `.claude/rules` têm frontmatter `paths`: [production-projects.md](../../.claude/rules/production-projects.md) para qualquer arquivo em `src/`, [program-composition.md](../../.claude/rules/program-composition.md) para `Program.cs`, `*Extensions.cs`, `*Endpoint.cs` e `*Consumer.cs`, e [tracing.md](../../.claude/rules/tracing.md) para todo `.cs` de produção. Cada regra entra no contexto quando o Claude lê ou edita um arquivo que casa com o padrão, e as regras se acumulam quando os padrões coincidem. Por isso o guia geral manda abrir a regra da área ao revisar código sem lê-lo. Consulte a [documentação oficial de memória e regras](https://code.claude.com/docs/en/memory).

As skills [prd](../../.claude/skills/prd/SKILL.md) e [sdd](../../.claude/skills/sdd/SKILL.md) estão incluídas no clone em `.claude/skills`, com suas referências e scripts. Não há instalação global nem acesso à rede necessário para descobri-las. Elas aparecem no menu `/` como `/prd` e `/sdd`, em sessões iniciadas na raiz ou em qualquer subdiretório do projeto, e o Claude Code também pode selecioná-las pela descrição, conforme a [documentação oficial de skills](https://code.claude.com/docs/en/skills).

Exemplos de pedidos:

```text
/prd Revise o PRD docs/prd/0001-offering-offer-lifecycle.md
/sdd Especifique o comportamento técnico da abertura de uma oferta
```

As instruções, descrições, referências e exemplos narrativos das regras e das skills usam português do Brasil. Os contratos de artefatos permanecem em inglês: títulos fixos, campos, tags, palavras-chave EARS, IDs e valores de gates. As listas de exceções estão em [conventions.md da prd](../../.claude/skills/prd/references/conventions.md) e [workflow.md da sdd](../../.claude/skills/sdd/references/workflow.md). Comentários e docstrings do verificador PRD estão em português; seus diagnósticos de linha de comando preservam o inglês por compatibilidade.

O pedido define o escopo e a conclusão. Em execução autorizada, as etapas avançam sem aprovação ou commit intermediário obrigatório. Especificações ainda não commitadas podem ser usadas e verificadas, com identificação por hash de conteúdo. Um pedido apenas de planejamento termina na entrega do plano.

## Decisões de layout

| Decisão | Custo aceito |
| --- | --- |
| `CLAUDE.md` na raiz concentra as convenções do repositório; não há `CLAUDE.md` em subdiretórios nem `AGENTS.md` | Outras ferramentas de agente não leem o arquivo; manter um segundo arquivo de entrada duplicaria a fonte |
| Três regras em `.claude/rules` com frontmatter `paths`: convenções dos projetos de produção, composição e tracing, cada uma com o escopo que declara | A regra só entra no contexto quando um arquivo do padrão é lido ou editado; revisão sem leitura de arquivo exige abrir a regra pelo link do `CLAUDE.md` |
| Skills `prd` e `sdd` versionadas em `.claude/skills` | A origem [claude-skills](https://github.com/guilhermesalvi/claude-skills) continua em inglês e exige comparação semântica ao atualizar |
| Invocação por `/prd` e `/sdd` | O plugin `claude-skills`, se instalado na máquina, expõe `/claude-skills:prd` e `/claude-skills:sdd` em paralelo, e o projeto usa as versões locais |
| Exclusões de `CLAUDE.local.md`, `.claude/settings.local.json` e `.claude/worktrees/` no Git | Overrides e configurações locais ficam fora do versionamento e podem alterar as instruções da máquina |
| Orçamento de 32 KiB em `check_repository.py` para a cadeia de `CLAUDE.md` mais todas as regras, no pior caso em que todos os padrões casam | O Claude Code não impõe esse limite; ele é uma disciplina do repositório, e a orientação oficial é manter cada arquivo abaixo de 200 linhas |

Não há hooks, servidores MCP, agentes personalizados ou configuração de execução versionados. Não foi criado `.claude/settings.json`: fixar modelo, permissões ou variáveis compartilhadas substituiria escolhas do ambiente sem necessidade. Se o projeto vier a precisar de configuração própria, use o [formato oficial de settings](https://code.claude.com/docs/en/settings).

## Origem e atualização das skills

As duas skills vieram de [guilhermesalvi/claude-skills](https://github.com/guilhermesalvi/claude-skills), de Guilherme Salvi, na revisão `183dd948aef712749f10bfac4832e4ea14ca46b6`. Foram importados todos os 19 arquivos de `skills/prd` e `skills/sdd`. A skill `transcript-fix` não era dependência deste projeto.

Adaptações locais: caminhos e hierarquia migrados para o repositório; tradução para português; descrições e entradas reduzidas; referências reorganizadas por necessidade; autonomia, conclusão, evidência e validação proporcionais à mudança. O exemplo de PRD foi substituído por um cenário fictício menor e verificável, sem afirmações regulatórias que possam ser confundidas com pesquisa desta revisão. O verificador `check_prd.py` mantém regras, diagnósticos e códigos de saída; comentários e docstrings foram traduzidos e os arquivos lidos são fechados explicitamente. A origem não contém arquivo de licença; nenhum foi acrescentado ou presumido nesta cópia.

Para atualizar, compare `.claude/skills/prd` e `.claude/skills/sdd` com uma revisão específica da origem, revise o significado das alterações e preserve as adaptações acima. A tradução exige comparação semântica, pois o diff de texto sozinho não identifica equivalência. Registre aqui a nova revisão e atualize o `.slnx` para arquivos criados ou removidos. A cópia versionada evita alterações silenciosas por atualização do plugin.

## Decisões da revisão das instruções

A revisão das instruções e das skills seguiu as [orientações de prompting do GPT-6 Astra](https://developers.openai.com/api/docs/guides/latest-model#prompting-best-practices) e o [guia de revisão de skills e prompts](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra). Elas orientam precedência clara, leituras pertinentes, conclusão do escopo autorizado e verificações proporcionais, princípios que não dependem da ferramenta.

| Alteração | Motivo | Custo aceito |
| --- | --- | --- |
| Português na prosa; inglês nos contratos | Facilitar leitura e manutenção pelo time, preservando consumidores | Atualizações da origem exigem revisão semântica |
| Aprovação separada de commit | Permitir execução e verificação da versão atual conforme autorização | Relatórios precisam identificar a versão examinada |
| Revisão por achados; persistência por progresso | Corrigir problemas reais sem notas artificiais ou paradas por quota | Exige julgamento explícito sobre dependências e novas hipóteses |
| Gates escolhidos por risco e critérios | Evitar repetir suites por posição da tarefa | O plano precisa justificar verificação e evidência vigente |
| Mutation testing por decisão fundamentada ou pedido | Concentrar o esforço nas regras cujo risco o justifica | Dispensa exige justificativa; o risco financeiro ou de concorrência continua sendo avaliado |
| Regras de produção fora do guia geral, em `.claude/rules` | Reduzir detalhes de código no contexto de tarefas documentais | A regra precisa ser aberta pelo link quando a tarefa não lê arquivo do padrão |

## Validação

Pré-requisitos das verificações: Git no PATH e Python 3.10 ou superior, somente biblioteca padrão. Os comandos abaixo partem da raiz:

```bash
python scripts/check_repository.py
python scripts/test_repository_checks.py
python .claude/skills/prd/scripts/check_prd.py docs/prd
dotnet build FundDistributionPlatform.slnx
dotnet test FundDistributionPlatform.slnx
```

`check_repository.py` confere inventário da solução, destinos dos links locais fora de exemplos, estrutura das skills, frontmatter `paths` das regras, orçamento de 32 KiB para a cadeia de `CLAUDE.md` mais as regras, e contratos de gates em tarefas e exemplos completos. Ele inclui arquivos novos não ignorados e desconsidera removidos, permitindo uso antes do commit. `test_repository_checks.py` exercita os gates e extrai o exemplo completo de PRD para verificá-lo, incluindo uma citação inválida de controle. São checks estruturais, sem prova de qualidade ou comportamento do modelo.

Mudanças apenas em instruções e documentação usam os validadores e a revisão dos exemplos. Build e testes .NET são exigidos quando o código correspondente muda. Para validar metadados com o verificador do `skill-creator` no Windows, use `python -X utf8 <caminho-do-skill-creator>/scripts/quick_validate.py <pasta-da-skill>`; isso evita depender da página de código do sistema para ler português em UTF-8.

Depois de alterar instruções, regras ou skills, confira a descoberta em sessões novas, uma na raiz e outra em `src/Offering`:

```bash
claude
```

Em cada sessão, execute `/context` e confira `CLAUDE.md` em Memory files; depois peça as regras aplicáveis a `src/Offering/Program.cs`, pedindo que o arquivo seja lido: devem aparecer as três regras, porque o arquivo casa com os três padrões. Confira também `/prd` e `/sdd` no menu `/`. Se uma skill não aparecer, reinicie a sessão. Se houver duplicatas, verifique o plugin `claude-skills` ou skills pessoais com o mesmo nome em `~/.claude/skills`; o repositório não altera instalações globais. Um `CLAUDE.local.md` ou uma exclusão em `claudeMdExcludes` local altera o contexto da máquina e deve ser considerado ao diagnosticar diferenças.
