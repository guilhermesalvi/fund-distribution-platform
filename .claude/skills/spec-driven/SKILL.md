---
name: spec-driven
description: 'Spec-Driven Development em cinco entradas (Specify, Design, Tasks, Execute, Verify): de requisitos técnicos testáveis (EARS, IDs rastreáveis, deltas por capability) a design orientado a risco, tasks com teste co-locado e verificação com evidência. Cobre Design e Implementação; Intenção é o prd-writer. TRIGGER: "tech spec", "especificação técnica", "spec" de requisitos técnicos ou de comportamento do sistema, "SDD", "design da solução", "quebre em tasks", "implemente a spec", "verifique a implementação", "retome" uma mudança SDD existente, "documente a spec do módulo X"; também ao implementar feature não trivial sem citar spec. NÃO acionar para PRD/discovery (prd-writer), ADR isolada, code review sem spec, refactor mecânico.'
---

# Spec-Driven Development

Este arquivo é o roteador: posicionamento, roteamento, tiers, as invariantes que valem em toda entrada e onde vive cada regra. Regra detalhada vive em `references/`, em um único lugar; os demais lugares citam.

## Posicionamento

Esta skill implementa as ênfases **Design** e **Implementação** do framework *Três Ênfases* (EximiaCo). A ênfase **Intenção** é o `prd-writer`; esta skill começa onde o PRD termina.

| Ênfase | Pergunta | Artefato | Skill |
|---|---|---|---|
| Intenção | Que problema, para quem, por quê? | `/docs/prd/…` | `prd-writer` |
| Design | O que o sistema deve fazer (spec) e como será estruturado (design)? | `spec.md`, `design.md`, `tasks.md` | esta: Specify, Design, Tasks |
| Implementação | Como transformar o design em código verificado? | código, `validation.md`, `project-memory.md` | esta: Execute, Verify |

Princípios que valem em toda entrada:

- As ênfases são cíclicas e a catraca só sobe: complexidade descoberta no meio da tarefa promove o tier (pare, diga, suba); nada rebaixa tier no meio.
- **Refine o contexto, não o erro.** Artefato downstream errado (teste que não deveria passar, código que contradiz o design, task impossível) não se remenda: diagnostique o artefato upstream (PRD, spec, design, tasks) que carregava a causa, corrija a fonte e re-derive. Procedimento no Execute: execute.md, Implementar.
- **Fatos você procura; decisões você pergunta.** O que é descobrível no ambiente (código, config, docs, histórico do repositório) você resolve pela cadeia de verificação (design.md, Pesquisa), com script quando precisa de baseline (design.md, Análise da base). Pergunta fica para decisão do usuário: escopo, prioridade, comportamento de produto, trade-off.
- **Precedência.** Quando pedido, convenção e defaults discordam sobre layout, formato de commit, idioma, forma de ADR ou comandos, vale nesta ordem: primeiro o que o usuário pediu nesta sessão; depois a convenção do projeto (CLAUDE.md do repositório, rules, CONTRIBUTING, docs); depois as instruções pessoais do usuário (CLAUDE.md global); por último os defaults desta skill. A skill preenche só o que ninguém fixou e avisa quando substituiu um default.
- **Aprovações e autorizações** (fonte canônica; os demais lugares citam). São quatro atos distintos. (1) **Aprovação de conteúdo** é o gate entre artefatos: o usuário revisa e aprova cada artefato antes do seguinte, e apresentar um artefato e começar o próximo no mesmo fôlego pula o gate. (2) **Autorização para implementar** permite editar arquivos da mudança na árvore de trabalho. (3) **Autorização para commit** local. (4) **Autorização para operação externa** cobre push, deploy, banco compartilhado e qualquer efeito remoto ou destrutivo, e é dada sempre por ação. Pedido explícito ("implementa a spec", "faz a T3") concede (2); "commita" concede (3); (4) nunca é implícita. Autorização concedida vale para a sessão ou para a mudança e não é pedida de novo. Silêncio nunca é aprovação nem autorização. Aprovação refere-se à revisão aprovada: alteração material no artefato (comportamento, escopo, contrato) invalida a aprovação dele e dos dependentes que a citam; correção editorial não reabre nada (modes.md, Estados).
- **Decisão, premissa ou bloqueio.** Toda dúvida cai em uma de três categorias. (a) Decisão ordinária dentro da autonomia já concedida: decida, registre onde o artefato manda (assumption, decisão técnica, memória) e siga, sem nova confirmação. (b) `[PREMISSA]` explícita com default e racional: permite avançar e fica revisável. (c) Decisão material do usuário (escopo, regra de negócio, trade-off, operação externa): pergunte e bloqueie só o trabalho que depende dela, continuando o resto. Delegação explícita ("decide você") vira (a). Sem resposta, o item dependente fica bloqueado e registrado; nada é adotado "por default". O orçamento de perguntas (specify.md, Clarify) limita a rodada e não converte decisão material pendente em premissa. Vale em Specify, Design, Execute e Verify.
- **Falha é entregável.** Linter com HARD que você não consegue resolver, dependência indisponível, fonte ausente ou verificação bloqueada se apresentam como relatório de falha ou de validação incompleta, com o que falta. Nunca se apresentam como artefato aprovável, e nunca se esconde a falha para "não apresentar HARD".

## Roteamento de origem

PRD vive no problem space; spec e design no solution space. Antes de Specify, decida a origem pelo sinal no pedido (PRD, ideia rica, código existente, ou redirecionar ao `prd-writer`): specify.md, Origem e modo. "Precisa de PRD?" é sobre maturidade do problem space; "quanto artefato de SDD?" é sobre tamanho e risco (Tiers). São ortogonais.

## Entradas

Cada entrada lê o artefato anterior; se houver mais de um candidato, liste e diga qual usou. Leia a referência inteira antes de agir. Scripts em `scripts/` no diretório desta skill: `python3 <skill-dir>/scripts/<nome>.py`, nunca a partir da raiz do projeto.

| Pedido | Entrada | Referência | Pré-requisito |
|---|---|---|---|
| Especificar, requisitos, "como deve se comportar" | Specify | [specify.md](references/specify.md) | PRD ou pedido rico |
| Design, arquitetura, comparar abordagens | Design | [design.md](references/design.md) | spec aprovada |
| Quebrar em tasks, plano de implementação | Tasks | [tasks.md](references/tasks.md) | design aprovado (ou spec, se Design foi pulado) |
| Implementar, "faz a T3" | Execute | [execute.md](references/execute.md) | tasks (ou plano inline) aprovadas + Analyze sem CRITICAL nem HIGH pendente (verify.md) |
| Validar, verificar, UAT | Verify | [verify.md](references/verify.md) | última task fechada (com ou sem commit) |
| Pausar, retomar, registrar decisão, arquivar | Memória | [memory.md](references/memory.md) | — |

O contrato completo por modo e tier (pré-requisitos, fonte de requisitos e estrutura, onde ficam passos, gates, evidências, status e desvios, aprovações, Verify, fechamento, pausa, retomada, arquivamento) e as transições de estado de cada artefato estão em [modes.md](references/modes.md); é a fonte canônica quando um artefato é dispensado.

## Tiers

Dois eixos: **tamanho** (arquivos, componentes, tasks) e **risco** (Fairbanks: o que pode falhar caro; integração externa, estado e concorrência, dinheiro, dado regulado, contrato público, novo deployável ou biblioteca compartilhada). O tier é o maior dos dois.

| Tier | Critério | Specify | Design | Tasks | Execute | Verify |
|---|---|---|---|---|---|---|
| **Small** | ≤3 arquivos, um componente, sem risco nomeado | Inline: 1–3 requisitos EARS com ID no plano inline do Execute | Pula: estrutura em uma linha do plano inline | Pula: passos inline no Execute | Implementa e verifica inline | Passada *fresh-eyes* própria |
| **Medium** | Feature clara, <10 tasks, risco baixo | `spec.md` breve com IDs | Uma ou duas linhas no plano inline, salvo risco nomeado | Pula se ≤5 passos óbvios sem dependência não trivial; senão `tasks.md` | Por task, commit atômico quando autorizado | Verifier com independência declarada |
| **Large** | Multi-componente, integração, estado | `spec.md` completa + dimensões implícitas | `design.md`: componentes, interfaces, riscos | `tasks.md` completo com fases | Por task, commit atômico | Verifier + sensor de discriminação |
| **Complex** | Ambiguidade, domínio novo, regulado, dinheiro, contrato público | Completa + clarify | 2–3 abordagens + design completo | Completo + plano por fase | Por task, sub-agentes opcionais | Verifier + sensor + UAT se user-facing |

- Specify e Execute nunca são pulados: sempre se sabe o quê antes de fazer.
- `design.md` pula quando não há decisão arquitetural, padrão novo nem interação entre componentes a planejar **e** nenhum risco nomeado; a estrutura escolhida aparece então em uma ou duas linhas do plano inline do Execute (execute.md, Passos inline), que é o que passa pelo gate. Risco nomeado exige `design.md` mesmo em Medium (duas seções curtas atacando o risco, não o template inteiro). Unidade de deploy nova é sempre risco nomeado (design.md, Unidade de deploy). PRD de tier `complexa` (regulação, dinheiro, multi-ator) carrega risco nomeado: a mudança é no mínimo Large.
- Artefato pulado tem substituto declarado: Small leva requisitos EARS com ID, estrutura, gate e passos ao plano inline do Execute; Medium sem `tasks.md` mantém `spec.md` e leva o resto ao plano inline. Analyze e Verify leem o que existe (verify.md); comandos de gate vêm do plano inline quando não há `tasks.md`.
- Válvula de segurança: Execute sem `tasks.md` começa listando passos inline. Quando a lista passa de 5 passos, revela dependência não trivial ou revela risco nomeado, pare, declare o tier novo e crie o artefato que faltou (execute.md, Passos inline).
- Na dúvida entre dois tiers, declare o maior: subdimensionar produz spec cega; superdimensionar custa seções omitíveis.
- O tier vai no comentário de máquina de cada artefato (specify.md, Layout) e é consumido pelos linters.

## Convenção de confiança

Mesmas tags do `prd-writer`, com o que conta como fato nesta skill:

- `[FATO]`: confirmado pelo PRD, pelo usuário, pelo código existente ou por documentação.
- `[PREMISSA]`: inferido pela skill; vira assumption com default escolhido + racional na spec.
- `[PREMISSA-CRÍTICA]`: load-bearing; se falsa, invalida a abordagem. Máximo 1–3 por artefato, cada uma com "se falsa…", validada antes de Execute.
- `[LACUNA]`: informação insuficiente para decidir com segurança. Nunca preencha com especulação sem tag.

**Gate de lacuna.** `[LACUNA]` no caminho (toca requisito, componente ou interface em escopo) bloqueia o avanço de ênfase. Resolva com o usuário ou converta explicitamente em `[PREMISSA]` com default e racional. Lacuna de regra de negócio se resolve no PRD, não na spec (specify.md, Origem e modo). `[LACUNA]` fora do caminho vai para Perguntas em Aberto com dono e critério de resolução. Lacuna que sobreviveu ao design é tratada antes da primeira task pela regra Decisão, premissa ou bloqueio (execute.md, Antes da primeira task); sem resposta do usuário, a lacuna continua lacuna.

## Contrato de execução

Invariantes de todo Execute; execute.md descreve o procedimento e cita estes itens.

1. **Testes derivam da spec**, nunca da implementação: cada teste afirma o resultado que a spec define.
2. **O gate decide, não a auto-avaliação.** Task pronta é comando de gate (runner, build, lint) com exit 0.
3. **Um commit atômico por task**, quando commits estão autorizados, no formato que o repositório convenciona (Conventional Commits por default), com `tasks.md` e rastreabilidade atualizados no mesmo commit. Mensagem planejada (campo Commit), commit autorizado e commit executado são estados distintos. Sem autorização de commit a task fecha do mesmo jeito: gate verde, `tasks.md` marcado e rastreabilidade atualizada na árvore de trabalho, e o registro diz "sem commit" onde pediria hash. Nunca agrupe tasks. Nunca enfraqueça, pule ou apague teste para passar; remoção de teste só acompanha requisito REMOVED, com a razão.
4. **Verificação independente** após a última task (tier Medium ou maior): o Verifier re-deriva a cobertura sem herdar o trabalho do autor, com evidência ou zero (verify.md). O grau de independência depende do harness (sub-agente fresco, ou passada *fresh-eyes* do próprio autor) e é declarado no `validation.md`; o que não é opcional é a passada e a evidência. O Verifier devolve o relatório; o orquestrador persiste `validation.md` e atualiza spec e tasks.
5. **Blast radius.** Escopo de escrita de uma task: seus arquivos de implementação, teste, configuração indispensável e os artefatos de acompanhamento (`tasks.md`, rastreabilidade); arquivo indispensável descoberto durante a task entra em `Onde` com nota, sem aumento material de escopo. Quem autoriza o quê: Posicionamento, Aprovações e autorizações.
6. **Segurança.** Pacote novo é sugestão até validação humana da procedência no registro oficial; nunca instale sem sinalizar. Segredo, connection string ou dado de produção encontrado na base nunca entra no output; sinalize como risco.

## Gates determinísticos

Os scripts checam o que a auto-revisão da LLM faz mal: conformidade mecânica que sofre drift. O que cada um checa está no docstring (`python <skill-dir>/scripts/<nome>.py` sem argumentos; use `python3` onde `python` não existir). `HARD` exige correção e nova rodada; artefato com HARD pendente não é aprovável. HARD com prefixo `INCOMPLETO` é validação incompleta (fonte ausente, git ou parser indisponível): relate como tal, nunca como sucesso (Posicionamento, Falha é entregável). `WARN` é heurística: julgue. Linter verde é esqueleto conforme, não artefato bom; as passadas de julgamento (Revise) continuam obrigatórias. Sem ferramenta de execução de código, faça as mesmas checagens lendo o artefato e diga que foi manual.

Caminhos: `<skill-dir>` é o diretório desta skill; `/docs/...` na documentação é caminho relativo à raiz do repositório, nunca raiz do sistema de arquivos; ao chamar um script, passe o caminho real. Sem repositório, o diretório de saída é o que o ambiente indica (pergunte ou anuncie), não um path fixo.

| Momento | Comando |
|---|---|
| Ao abrir uma mudança e antes de arquivar | `seq.py check /docs/specs`; `seq.py check /docs/adr` |
| Antes de apresentar a spec | `lint_spec.py <spec.md> [--living <spec-viva.md>]` (IDs do PRD citados resolvem em `/docs/prd`; prefixo da spec distinto dos prefixos de PRD e igual ao dos IDs; PRD ausente é HARD `INCOMPLETO`; `prd-rev` divergente é HARD, ausente é WARN; `Antes:` de MODIFIED diferente do texto vigente na spec viva é HARD; link Markdown para arquivo local que não resolve é HARD; `--print-prd-rev <prd.md>` imprime a revisão) |
| Antes de apresentar as tasks | `lint_tasks.py <tasks.md> --spec <spec.md> [--commit-max-len N] [--commit-no-scope] [--commit-no-bang] [--commit-single-line] [--commit-lowercase]` (`--spec` obrigatório; delta de refactor `no-behavior-change` serve de fonte pelos invariantes citados; as opções com prefixo `commit-` repassam a política de commit do repositório) |
| Em cada commit | `check_commit.py --message "<msg>" [--max-len N] [--no-scope] [--no-bang] [--single-line] [--lowercase]` (ou `--file` como hook `commit-msg`): confere a forma Conventional Commits; a regra mais estrita do repositório entra pelas opções, lidas de onde a política está escrita (CLAUDE.md, CONTRIBUTING), e são as mesmas que `lint_tasks.py` recebe com prefixo `commit-` |
| No sensor de discriminação (verify.md, 2.4) | `sensor_scratch.py create <dir> [--repo <path>] [--path <p>]`, `sensor_scratch.py reset <dir>`, `sensor_scratch.py remove <dir>`: worktree com snapshot da versão verificada (HEAD + alterações pendentes, commitadas no scratch); `reset` volta ao snapshot e falha se o scratch não ficar limpo; a árvore real, o index e os branches nunca mudam |
| Antes de declarar a mudança pronta | `lint_validation.py <validation.md> --spec <spec.md> [--uat] [--evidence-of-run <log>]` (`--uat`, ou a flag `uat` no comentário de máquina, exige a seção UAT): veredito PASS, FAIL ou BLOCKED consistente com o conteúdo |
| Ao arquivar | `apply_delta.py apply <delta-spec.md> [--living <spec.md>] [--create] [--date AAAA-MM-DD] [--dry-run]`: única escrita nas regiões do script da spec viva (lista de Requisitos, Data, Histórico); Propósito, Glossário e Domain Events são do autor (memory.md, Arquivar) |
| Depois do merge e em CI | `apply_delta.py check <delta-spec.md>`: delta mais recente é conferido por texto; delta já superado por mudanças posteriores é auditado só pela linha do histórico e pelos REMOVED, e nunca se reaplica delta antigo |
| Ao abrir Design sobre base existente | `hotspots.py <repo>`: indício do repositório, não gate nem prova; saída inconclusiva (exit 2) não é evidência |

## Redação

- Idioma do artefato pela Precedência (pedido na sessão, convenção do projeto, instruções pessoais, e só então o idioma do input, default PT); o idioma da conversa não muda o do artefato. Ficam em inglês: keywords EARS (`WHEN`, `WHILE`, `WHERE`, `IF`, `SHALL`), IDs (`RSV-03`), código, identificadores, paths e slugs, mensagens de commit, e todo termo técnico ou de domínio consagrado em inglês (domain event, outbox, idempotency key, retry, timeout, circuit breaker, aggregate, value object, port/adapter, handler, gate, rollback, feature flag, bookbuilding). Não traduza nem invente forma em português; termo que o time já usa em português (liquidação, oferta, reserva, lote) fica em português.
- Voz declarativa e decidida: "o sistema rejeita", "faremos". Hedging só para incerteza real, marcada com a tag.
- Sem meta-narração; produza o artefato, não anuncie a fase. Commits, resumos e relatórios: veredito primeiro, frases curtas, sem filler.
- Um conceito por parágrafo. Preserve o contexto de decisão (racional de trade-off, "se falsa", mitigação de risco): é sinal para humanos e para o próximo agente.
- Sem placeholder em artefato aprovável: "TBD", "TODO", "adicionar validação" são falhas, não conteúdo (lista por artefato em `scripts/_common.py`).

## Revise

Revisão é parte da entrega em toda entrada: a passada mecânica (Gates) e três de julgamento. Falha em qualquer uma leva a ajuste antes de apresentar.

- **Tier 1, conformidade que o linter não alcança:** tier coerente com tamanho e risco; toda inferência marcada (não a grafia, mas se uma frase sem tag deveria ser `[PREMISSA]`); idioma; densidade.
- **Tier 2:** critérios de qualidade da referência da entrada.
- **Tier 3, adversarial:** produza o Ponto de Maior Fragilidade (specify.md; vale para spec e design) ou, no Verify, assuma o papel de quem quer provar que a mudança não atende à spec.

## Workflows

- **Nova mudança:** primeiro o roteamento de origem e o tier; depois Specify, Design e Tasks, sendo Design e Tasks opcionais conforme o tier; depois Analyze (verify.md), Execute, Verify e o arquivamento (memory.md). Há gate de aprovação entre cada artefato; o que cada modo dispensa e o substituto estão em modes.md.
- **Retomar:** memory.md, Retomar; a evidência do git vence o snapshot, e `git status` é indício de progresso, não prova de conclusão.
- **Capability sem spec:** Specify em modo código escreve o delta de baseline e o arquiva com `apply_delta.py apply --create` (modes.md, Contrato por combinação, Modo código); só depois abra uma mudança.
- **Output no chat:** faça o trabalho, não narre a máquina. Depois de apresentar, aponte o Ponto de Maior Fragilidade, as `[PREMISSA-CRÍTICA]` a validar antes de Execute, as `[LACUNA]` no caminho e o gate seguinte.
