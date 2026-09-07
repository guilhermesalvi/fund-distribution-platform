# Memória do projeto, pausa/retomada e arquivamento

`/docs/project-memory.md` é a memória entre ciclos: decisões que o código não expressa, padrões a seguir, handoff para retomar. Não é log de sessão nem cópia do código.

Leia até o fim antes de agir.

---

## 1. `project-memory.md`

Três seções. As duas primeiras são **índices mutáveis**; a terceira é **append-only**.

```markdown
# Project Memory

_Decisões, padrões e contexto que o próximo ciclo precisa saber. Entradas de ciclo são imutáveis: atualização cria entrada nova, nunca edita a anterior._

## Decisões arquiteturais

| ID | Decisão | Status | ADR | Origem | Data |
|---|---|---|---|---|---|
| AD-001 | Eventos de domínio saem por outbox transacional; nunca publish direto no handler | Ativa | [0001](adr/0001-outbox-for-domain-events.md) | changes/0001-partial-reservation/design.md | 2026-09-04 |
| AD-002 | … | Substituída por AD-005 | [0002](adr/0002-….md) | … | … |

## Handoff

_Snapshot da última pausa. Reconciliado contra git na retomada; evidência vence snapshot._

- **Mudança:** fixed-income/bookbuilding/changes/0001-partial-reservation
- **Branch:** feat/partial-reservation
- **Última task concluída:** T3 (commit a1b2c3d; ou "sem commit" quando commits não estão autorizados)
- **Próxima:** T4 — depende de T3 ✅
- **Bloqueios:** [PREMISSA-CRÍTICA] sobre lote mínimo ainda não validada com produto
- **Data:** 2026-09-04 18:40

## Histórico de ciclos

### [2026-09-04 18:40] — Reserva Parcial: domínio e regras de lote

**Ciclo:** execute | **Artefato:** changes/0001-partial-reservation/tasks.md | **Tasks:** T1–T3

#### Decisões tomadas
<!-- não óbvias no código, com justificativa; decisão de projeto ganha AD-NNN e entra no índice -->

#### Padrões adotados
<!-- convenções que os próximos ciclos devem seguir -->

#### Lacunas resolvidas
<!-- o que estava em aberto e como foi decidido -->

#### Exclusões deliberadas
<!-- o que foi deixado de fora e por quê -->

#### Contexto adicional
<!-- o que o código não expressa -->
```

**O que entra** (rubrica): só o que o próximo ciclo precisa saber e não está no código nem nos artefatos. Decisão não óbvia com racional; padrão a seguir; lacuna resolvida e como; exclusão deliberada e por quê; premissa validada ou refutada. **O que não entra:** o que o `tasks.md` já diz; o que o diff mostra; narrativa de sessão.

**Imutabilidade.** Entradas do Histórico nunca são editadas ou apagadas; correção é entrada nova referenciando a anterior. Os índices (Decisões, Handoff) são atualizados no lugar.

**Quando escrever.** Ao fim de cada ciclo com sinal (design aprovado, fase de tasks concluída, verificação, arquivamento) e em toda pausa. Ciclo sem sinal não gera entrada — ruído degrada a memória.

---

## 2. Decisões e ADRs

Uma decisão é de **projeto** (ganha `AD-NNN`) quando fixa convenção, restrição ou padrão que features futuras devem seguir. Decisão local à feature fica na tabela de decisões do `design.md`.

Cada `AD-NNN` é um arquivo `docs/adr/NNNN-<slug>.md` com o mesmo número (alocado por `seq.py next /docs/adr --kind adr --slug <slug>`); a tabela de `project-memory.md` é o índice, com o link. Projeto que já registra decisões em outro layout ou formato (ADR em outro diretório, seção de decisões com custo e razão em PRD ou CLAUDE.md) mantém o seu: o índice aponta para a decisão canônica existente e a skill não cria formato paralelo (SKILL.md, Precedência). O registro exige alternativas consideradas e consequências, não só a decisão: sem elas a IA re-propõe caminhos já descartados e o time re-litiga o que já foi pago. Os participantes entram porque decisão de arquitetura raramente é de uma pessoa, e nome na ADR é o que responde "por que fizemos assim?" depois do turnover. A ADR é a documentação de arquitetura que sobrevive: código e diagrama mostram o que é; só ela guarda o porquê.

```markdown
# ADR 0007: Eventos de domínio saem por outbox transacional

| | |
|---|---|
| **Status** | Proposta / Ativa / Substituída por AD-NNN / Obsoleta |
| **Data** | 2026-09-05 |
| **Participantes** | quem decidiu; quem foi consultado |
| **Origem** | changes/0001-partial-reservation/design.md |

## Contexto
[Situação e restrições que forçaram a decisão; o que estava em jogo.]

## Decisão
[Uma frase: o que faremos.]

## Alternativas consideradas
| Alternativa | Por que rejeitada |
|---|---|

## Consequências
- Positivas: …
- Negativas: … (o custo aceito; toda decisão tem um lado ruim, e ADR sem consequência negativa é decisão não examinada)

## Regras derivadas
[Regra em CLAUDE.md, rules ou linter que existe por causa desta ADR, com o path. É o vínculo regra → princípio que a limpeza do arquivamento verifica.]
```

- **Registrar:** próximo número; status `Ativa`; linha no índice com link e origem; racional resumido na entrada de ciclo correspondente.
- **Conformar:** todo Design lê as ativas antes de projetar. Decisão ativa é restrição.
- **Superseder:** nova ADR com o racional; a antiga muda o status para `Substituída por AD-NNN`. Nunca apague, nunca edite a antiga além do status.
- **Regra nova cita a decisão:** regra de projeto que a mudança cria ou altera (CLAUDE.md, rules, linter custom) cita a ADR ou o princípio que a justifica. Regra sem porquê é seguida cegamente ou ignorada; as duas coisas custam. Regra existente sem porquê não é apagada por isso: é reportada como trabalho separado (seção 5).
- Gatilho explícito: "registre essa decisão", "isso é decisão de projeto", "daqui em diante sempre…".

---

## 3. Pausar

Ao pedido ("pausa", "vou parar", "encerra a sessão") ou quando o contexto está perto do limite:

1. Termine a task em andamento se faltam minutos; senão, **não commite parcial** — registre no Handoff o que está incompleto e o estado dos arquivos.
2. Atualize `## Handoff`: mudança, branch, última task concluída com hash (ou "sem commit" e o estado dos arquivos), próxima task e dependências, bloqueios (`[PREMISSA-CRÍTICA]` pendente, lacuna, gate falhando), data/hora.
3. Escreva a entrada de ciclo no Histórico se houve sinal.
4. Confirme em uma linha o que foi registrado.

---

## 4. Retomar

Ao pedido ("retoma", "continua de onde paramos", "onde estávamos"):

1. Leia `## Handoff` e `## Decisões arquiteturais`.
2. **Reconcilie contra a evidência** — o snapshot pode estar velho:
   - `git branch --show-current` bate com o Handoff?
   - `git status --porcelain`: mudanças não commitadas que o Handoff não menciona?
   - `git log --oneline -10`: commits depois do hash registrado?
   - `tasks.md`: tasks marcadas concluídas coincidem com os commits? Sem commits autorizados, coincidem com o `git status --porcelain`?
3. Divergência → a evidência vence; diga o que difere e proponha a reconciliação. `git status` e commits são indício de progresso, não prova de conclusão: task só conta como concluída com gate verde registrado (tasks.md marcado ou plano inline) e evidência.
4. Proponha o próximo passo (task, gate pendente, premissa a validar) **antes** de escrever código. Espere confirmação.

Nunca retome executando por cima de estado desconhecido.

---

## 5. Arquivar a mudança (spec-anchored)

Depois do Verifier em PASS, dos desvios resolvidos (modes.md, Desvios) e da aprovação de conteúdo do fechamento pelo usuário (SKILL.md, Aprovações e autorizações):

1. **Fundir o delta na spec viva** com `apply_delta.py apply <changes/NNNN-slug/spec.md>` (SKILL.md, Gates; `--create` para capability nova ou baseline de modo código). O script é o único que escreve nas suas regiões: lista de `## Requisitos`, campo Data e tabela de `## Histórico de revisões` (uma linha por mudança, identidade `NNNN-<slug>`, todos os IDs afetados explícitos); ele valida tudo antes de escrever, recusa `Antes:` divergente do texto vigente (alteração concorrente) e não reaplica delta já registrado.

   Fica com você, depois do merge, nas regiões do autor: **Propósito** (o `--create` copia o Contexto do delta — reescreva no escopo da capability), **Glossário** e a tabela **Domain Events**, que exige payload semântico e consumidores. O script avisa quando um requisito publica evento; não inventa a linha.
2. **Rastreabilidade** do delta: todos os IDs em `Verified`; Status do delta, do design e das tasks → `Concluído`.
3. **Desvios:** já resolvidos antes do PASS final: desvio que muda comportamento voltou ao artefato de origem, foi reaprovado e reverificado, e só então entra no delta aplicado; desvio sem mudança de comportamento ficou em `## Desvios` com justificativa. O arquivamento não ajusta a spec ao código, e exclusão registrada na memória não é prova de conformidade. Nenhum desvio sobrevive sem destino.
4. **Memória:** entrada de ciclo `archive`; decisões de projeto que nasceram no design promovidas a `AD-NNN` se ainda não foram.
5. Rode `apply_delta.py check <delta>` e depois `lint_spec.py` na spec viva, que precisa passar como spec, não só o delta (SKILL.md, Gates). Sobre delta já superado por mudanças posteriores, `check` audita só a linha do histórico e os REMOVED; nunca reaplique delta antigo para "corrigir" divergência causada por evolução legítima.
6. **Instruções tocadas pela mudança.** Se a mudança criou, alterou ou invalidou instrução versionada (CLAUDE.md, rules, prompts, docs de convenção), deixe uma regra só por assunto e com o porquê (seção 2), porque a IA segue ora uma, ora outra. Conflito ou regra sem justificativa fora do que a mudança tocou é reportado como trabalho separado, com o path; não se apaga regra por falta de ADR nem se revisa o repositório inteiro no arquivamento.
7. A pasta `changes/NNNN-<feature>/` permanece como histórico, com o prefixo, que mantém a ordem legível depois que o delta se fundiu; não apague.

Spike `spec-first` não passa por aqui: seu fechamento é o registro do que se aprendeu no Contexto do delta e o Status `Descartado` ou `Promovido a <mudança>` (modes.md); a pasta fica como histórico.

---

## Critérios de qualidade

- Memória contém só o que o próximo ciclo precisa e o código não diz.
- Histórico append-only; índices atualizados no lugar.
- Toda decisão de projeto tem ADR com alternativas, consequências e participantes, no formato do projeto quando ele já tem um, indexada com status e origem; superseder nunca apaga.
- Arquivamento deixa coerentes as instruções que a mudança tocou e reporta o resto como trabalho separado.
- Handoff reconciliado com git na retomada; evidência vence.
- Arquivamento deixa a spec viva coerente e lintável, sem desvio órfão.
