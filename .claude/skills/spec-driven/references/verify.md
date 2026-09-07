# Verify

Duas verificações em momentos diferentes:

1. **Analyze** — antes de implementar: consistência entre spec, design e tasks. Read-only.
2. **Verifier** — depois da última task: a implementação atende à spec (eixo 1) e ao design (eixo 2)? Independente, com evidência.

Leia até o fim antes de agir.

---

## 1. Analyze (pré-implementação)

Passada read-only sobre os artefatos que a mudança tem: `spec.md`, `design.md` e `tasks.md` quando existem; o plano inline do Execute quando Tasks ou Design foram pulados, com os requisitos inline em Small (execute.md, Passos inline). Roda depois das tasks (ou do plano) aprovadas e antes da primeira linha de código. Não edita artefatos; produz relatório e recomendação. Sem `design.md`, as passadas de aderência e inconsistência comparam spec com plano; em Small, a passada cabe em poucas linhas.

| Passada | O que procura |
|---|---|
| **Duplicação** | Dois requisitos que dizem o mesmo com palavras diferentes |
| **Ambiguidade** | Adjetivo sem número ("rápido", "robusto"), requisito lido de duas formas, resultado sem valor |
| **Subespecificação** | Requisito citado em task sem resultado preciso; edge case sem requisito; dimensão implícita marcada N/A que a task contradiz |
| **Aderência a decisões** | Design ou task que viola `AD-NNN` ativa sem entrada no Rastreamento de complexidade |
| **Cobertura** | Requisito sem task (o linter já pega); task sem requisito; requisito da spec viva afetado pelo delta sem task |
| **Inconsistência** | Terminologia divergente entre artefatos; interface no design ≠ `Produz` da task; `Depende de` ≠ mapa de execução |

Severidade e efeito: tabela em modes.md, Estados (CRITICAL e HIGH bloqueiam Execute; HIGH admite aceite explícito do usuário registrado no relatório; MEDIUM segue com task de correção ou aceite; LOW é nota).

Saída: tabela `ID | Categoria | Severidade | Localização | Resumo | Recomendação`, cobertura (% de requisitos com no mínimo uma task) e veredito: "Analyze limpo" é nenhum CRITICAL e nenhum HIGH sem aceite; a correção é sempre no artefato-fonte (SKILL.md, refine o contexto).

---

## 2. Verifier (pós-implementação)

**Autor e verificador são pessoas (ou agentes) distintos, na medida do harness.** Com sub-agente disponível, o orquestrador dispara um Verifier **fresco** com este arquivo, a spec, o design (ou o plano inline), o `tasks.md` e o intervalo de diff — sem o histórico da implementação. Sem sub-agente, o autor faz uma passada *fresh-eyes* própria depois da última task, começando por re-derivar a cobertura do zero, sem consultar as tabelas de evidência que produziu. Nesse caso a independência é parcial e o `validation.md` diz isso no campo Verificador. O que não muda entre os dois: evidência ou zero, dois eixos, relatório.

O Verifier é **read-only** sobre a árvore real: devolve o relatório ao orquestrador, que persiste `validation.md`, roda o linter e atualiza spec e tasks; o Verifier não grava nada na mudança. Mutações do sensor acontecem em scratch (worktree temporário ou cópia), nunca na árvore de trabalho.

**Escopo e snapshot:** registre a base (`git merge-base` ou o commit de partida), os commits da mudança e as alterações preexistentes na árvore (staged, unstaged e untracked, `git status --porcelain` no início), e diga quais entram no escopo; o relatório se refere a esse estado exato. Arquivos do diff: `git diff <base>..HEAD --name-only` + staged + unstaged + untracked pertinentes (sem commits, `git diff <base> --name-only` + untracked). Alterações do usuário fora da mudança e o estado do index são preservados: o Verifier não faz `add`, `stash`, `checkout` nem "restaura" nada na árvore real. Evidência fora do diff é válida quando um arquivo pré-existente foi modificado; note quando um check depende de arquivo fora do diff — pode indicar base errada.

### 2.1 Tasks concluídas

Todas marcadas em `tasks.md` (ou no plano inline)? Alguma parcial ou bloqueada? `## Desvios` (no `tasks.md`, no delta ou no plano, conforme modes.md) lista tudo o que o código marca?

### 2.2 Eixo 1 — conformidade à spec (evidência ou zero)

Para **cada requisito** no delta (ADDED e MODIFIED) e cada edge case:

| Requisito | Resultado definido pela spec | `file:line` + assertion | Resultado |
|---|---|---|---|
| RSV-07 | rejeita com `MIN_LOT_NOT_MET`, book inalterado | `tests/…/PartialReservationTests.cs:41` — `result.Error.Should().Be(ReservationError.MinLotNotMet)` | ✅ PASS / ❌ GAP / ⚠️ lacuna de precisão |

Regras:

- Onde a spec define resultado preciso, a assertion tem de mirar **exatamente** esse resultado — não basta existir assertion.
- Onde a spec **não** define resultado preciso, o resultado é lacuna de precisão, reportada com a marca de ressalva; nunca aprovada em silêncio.
- **Evidência ou zero:** sem `file:line`, o requisito conta como não coberto. Procure antes de declarar ausência; mostre a busca.
- Requisitos REMOVED: confirme que o comportamento removido não existe mais (teste antigo removido com justificativa; nenhum caminho vivo).

### 2.3 Gate Build

Rode o gate Build de `tasks.md` (ou do plano inline). Exit diferente de 0 é **FAIL**: pare. Gate não executável (SDK ausente, dependência indisponível) é **BLOCKED** com motivo, não FAIL. Registre comando, total, passados, falhos, pulados (cada skip justificado, em linha `Pulados:`) e exit. Teste pulado ou não executado não é evidência; PASS com zero testes executados não existe. Compare a contagem de testes com a de antes da mudança: se diminuiu, investigue (só REMOVED com razão justifica). Assertion enfraquecida é regressão potencial.

### 2.4 Sensor de discriminação (tier ≥ Large; Medium quando há risco nomeado)

Prova empírica de que os testes detectam regressão. Em scratch, nunca na árvore real; o isolamento vem da construção (diretório separado), não de "restaurar" depois:

1. **Scratch com a versão verificada.** `sensor_scratch.py create <tmp> [--path <p>]` (SKILL.md, Gates) cria um worktree destacado em HEAD, aplica sobre ele o que ainda não está commitado (`git diff HEAD`, staged e unstaged, mais os untracked não ignorados) e commita o resultado no scratch como **snapshot**, com hash: essa é a versão exatamente verificada. `--path` restringe as alterações pendentes ao escopo da mudança e deixa de fora alteração preexistente do usuário. HEAD sozinho não contém implementação não commitada; e diff contra a base (`git diff <base>`) não serve para montar o scratch, porque inclui commits que HEAD já tem e o patch não aplica. O scratch nasce sem arquivos ignorados (dependências, saída de build): o gate precisa se bastar (restore, build). Sem Git: cópia integral do diretório do projeto e uma segunda cópia intocada como snapshot. Copiar só os arquivos modificados não produz ambiente executável.
2. **Baseline verde no scratch.** Rode o gate da mudança no scratch antes de mutar. Se falhou, o sensor é **BLOCKED** (ambiente), não "sobrevivente".
3. **Injete uma falha de comportamento por vez** no código novo, proporcional ao risco: inverta condição (troque `>` por `>=`), troque retorno (status errado, zero em vez de calculado), off-by-one, remova efeito colateral exigido pela spec (publicação de evento, gravação).
4. **Rode os testes** que cobrem o código mutado (gate Quick/Full) no scratch.
5. **Classifique:** *morto* (testes falham por assertion), *sobrevivente* (todos passam), *inválido* (não compila ou falha por erro de ambiente: não conta como morto, escolha outra mutação), *falha de infraestrutura* (runner não executa: BLOCKED).
6. **Restaure o snapshot entre rodadas** com `sensor_scratch.py reset <tmp>`: volta ao commit de snapshot, remove arquivo que a mutação criou e falha se `git status --porcelain` não ficar vazio no scratch. Esse status vazio é a prova de que a próxima mutação parte da versão verificada. `git checkout -- .` não faz isso: restaura o index, que no worktree recém-criado é HEAD, não a versão verificada. Sem Git: recopie a partir da cópia-snapshot.
7. **Descarte o scratch** (`sensor_scratch.py remove <tmp>` / apague as cópias). A árvore real, o index e os branches nunca foram tocados; não há nada a restaurar neles. **Proibido:** `git stash push`, `checkout` ou `reset` na árvore real.
8. **Mutante sobrevivente** significa que os testes não discriminam aquele comportamento e gera task de correção; PASS não é possível com sobrevivente.

Profundidade: default 1–3 mutações no código de maior risco. Caminho crítico (dinheiro, liquidação, auth, integridade) exige no mínimo 5 mutações cobrindo ramificações, ou tooling de mutação da linguagem quando disponível (Stryker.NET, mutmut, cargo-mutants). Registre o hash do snapshot e o resultado por mutação com a classificação acima.

### 2.5 Eixo 2 — aderência ao design

O eixo 1 prova que a spec foi atendida; não prova que a estrutura é a projetada. Organização é ter lugar definido para as coisas (o design); bagunça é coisa fora do lugar combinado — e só existe dívida técnica onde existe lugar definido, senão é improviso. Este eixo detecta a bagunça enquanto é pequena. Checklist, com observação obrigatória nos itens com ressalva ou não atendidos:

| Item | Status | Observação |
|---|---|---|
| Estrutura segue o design (arquivos, componentes, localização) | ✅ / ⚠️ / ❌ | |
| Responsabilidades respeitadas (componente faz o que o design diz, e só isso) | | |
| Interfaces batem com as assinaturas do design | | |
| Sem dependência fora do planejado (pacote, módulo, serviço) | | |
| Nenhum deployável ou biblioteca compartilhada criada sem entrada no Rastreamento de complexidade (justificativa, dono) | | |
| Sem ciclo entre módulos; módulos consumidos só pela interface pública (nenhuma instância de classe interna de outro módulo) | | |
| Domain events com contrato do design (payload, chave, entrega) | | |
| Riscos do design mitigados como prometido | | |
| Lacunas do design resolvidas explicitamente e registradas | | |
| Desvios (`SPEC_DEVIATION`) justificados e listados | | |

Na tabela, a marca de ressalva (`⚠️`) significa desvio justificado e a marca de reprovado (`❌`) significa item não atendido. As duas exigem observação. Item não atendido vira gap.

### 2.6 Qualidade de código (por arquivo do diff)

Nada além do pedido; sem abstração de uso único; sem flexibilidade não solicitada; só arquivos da task tocados; código adjacente não "melhorado"; estilo existente seguido; guias de teste do projeto seguidos (cite o arquivo, ou "default forte"); todo teste no escopo mapeia para requisito, edge case ou "pronto quando" (sem teste órfão). "Um sênior aprovaria?"

### 2.7 UAT interativo (Complex, user-facing)

Só quando há comportamento user-facing em que julgamento humano importa (fluxo de UI, interação, visual). Backend e infra: checks automatizados bastam.

Um teste por vez: `Teste N: [nome] — Esperado: [observável] — Funciona? Descreva o que vê.` Interprete a resposta pela tabela:

| Resposta | Marca |
|---|---|
| "sim", "passa", "próximo" | ✅ |
| "pula", "não dá para testar" | ⏭️ |
| qualquer outra coisa | ❌, com o texto verbatim |

A severidade é inferida, nunca perguntada: crash, erro ou quebrado é Bloqueante; não funciona, errado ou falta é Maior; lento, estranho ou pequeno é Menor; cor, fonte ou alinhamento é Cosmético; incerto é Maior.

### 2.8 Relatório e ciclo de correção

Produza o relatório no formato de `validation.md` (template abaixo) e devolva-o ao orquestrador com o resumo compacto. Veredito é uma palavra: **PASS**, **FAIL** ou **BLOCKED** (verificação incompleta: gate não executável, dependência indisponível, sensor impossível), com `**Motivo do bloqueio:**` quando BLOCKED; modes.md, Estados. Gaps viram **tasks de correção** `TCn` no formato do `tasks.md` (tasks.md, Task atômica), em `## Tasks de correção` do `tasks.md` ou, sem ele, do plano inline, executadas pelo ciclo do Execute, seguidas de re-verificação. **Máximo 3 iterações** de corrigir e re-verificar; persistindo, escale ao usuário em vez de continuar o loop. Mesmo limite para diagnóstico de uma issue de UAT.

O orquestrador persiste `changes/NNNN-<feature>/validation.md` e roda `lint_validation.py <validation.md> --spec <spec.md>` (`--uat` em Complex user-facing; `--evidence-of-run <log>` quando o log do gate foi capturado). Com exit diferente de 0, a mudança não fecha: HARD corrige o relatório; FAIL roteia os gaps; BLOCKED escala o bloqueio. O linter confere a consistência do relatório, não prova que os comandos rodaram: quem rodou é quem responde por isso.

Depois do PASS e com os desvios resolvidos (modes.md, Desvios): o orquestrador atualiza `Status` da Rastreabilidade para `Verified` e segue para o arquivamento ([memory.md](memory.md)).

---

## Template: `changes/NNNN-<feature-slug>/validation.md`

```markdown
<!-- sdd: validation | change: 0001-partial-reservation | tier: large -->
# Reserva Parcial — Validação

**Veredito:** PASS ✅
<!-- uma palavra: PASS | FAIL | BLOCKED -->
**Motivo do bloqueio:** <!-- só quando BLOCKED -->
**Verificador:** sub-agente fresco (independente) | passada fresh-eyes do autor (independência parcial)
**Diff:** `<base>..<head>` — N arquivos; alterações preexistentes: nenhuma | listadas
**Data:** AAAA-MM-DD

## Conformidade à spec

| Requisito | Resultado da spec | `file:line` + assertion | Resultado |
|---|---|---|---|

N/N requisitos com evidência · M lacunas de precisão · K gaps

## Gate Build
Comando: … · Total N · Passou N · Falhou 0 · Pulou 0 · exit 0 · Contagem antes/depois: N → M
Pulados: nenhum

## Sensor de discriminação

Baseline no scratch: verde (snapshot `<hash>`).

| Mutação | Arquivo:linha | Testes rodados | Resultado |
|---|---|---|---|
| `>` → `>=` no investimento mínimo | `…:57` | Quick | morto ✅ |

## Aderência ao design

| Item | Status | Observação |
|---|---|---|

## Qualidade de código
[por arquivo, só o que falhou ou merece nota]

## UAT
<!-- quando aplicável -->

## Gaps (ordenados por severidade)

1. [severidade] [descrição] → task de correção TC1

## Iteração
1 de 3
```

**Resumo compacto no chat:** veredito na primeira linha; N/N requisitos com evidência; gate; sensor (mortos/sobreviventes); aderência (itens com ressalva ou não atendidos); gaps ordenados; próximo passo.

---

## Critérios de qualidade

- Analyze roda antes da primeira linha de código, sobre os artefatos que existem, e não edita artefato.
- Verifier re-deriva a cobertura sem herdar a tabela do autor e declara o grau de independência.
- Toda linha de evidência tem `file:line` e a expressão da assertion.
- Lacuna de precisão reportada, nunca aprovada.
- Sensor em scratch com snapshot da versão verificada (hash registrado), baseline verde antes de mutar, uma mutação por vez a partir do snapshot restaurado, classificação por mutação registrada.
- Dois eixos, sempre: spec e design (ou `## Estrutura` do `tasks.md`, ou o plano inline, quando o design foi pulado).
- Veredito uma palavra, consistente com conformidade, gate, sensor, gaps e UAT; BLOCKED com motivo.
- Loop de correção limitado a 3; escala em vez de girar.
- Relatório lidera com o veredito.
