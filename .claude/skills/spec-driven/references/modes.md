# Modos, tiers e estados

Fonte canônica do que cada combinação de modo e tier exige e dispensa, e das transições de estado de cada artefato. As referências das entradas descrevem o procedimento e citam este arquivo; quando um artefato é dispensado, é aqui que está o substituto.

Leia até o fim antes de agir.

---

## 1. Contrato por combinação

Colunas: de onde vêm requisitos, estrutura e decisões; onde ficam passos, gates, evidências, status e desvios; aprovações (SKILL.md, Aprovações e autorizações); Verify; fechamento, pausa e retomada; arquivamento e spec viva.

| Combinação | Pré-requisitos | Requisitos, estrutura, decisões | Passos, gates, evidências, status, desvios | Aprovações | Verify | Fechamento, pausa, retomada | Arquivamento e spec viva |
|---|---|---|---|---|---|---|---|
| **Small, tudo inline** | Pedido rico ou PRD; nenhum requisito da spec viva muda (senão é Medium) | Requisitos EARS com ID e a estrutura em uma linha, no plano inline (execute.md, Passos inline); decisão de solution space registrada no próprio plano | Passos do plano; gate = comando do repositório declarado no plano; evidência = tabela de adequação dos testes no chat; status = passos marcados no plano; desvio = nota no plano | Aprovar o plano inline (conteúdo); implementar e commit conforme autorização | Passada *fresh-eyes* própria, com tabela de evidência, no chat; sem `validation.md` | Fecha quando o último passo passa no gate; pausa/retomada registram o plano no Handoff | Sem delta e sem arquivamento; spec viva intocada |
| **Medium, spec + plano inline** | PRD ou pedido rico; `spec.md` (delta) aprovada | Requisitos: delta; estrutura: uma ou duas linhas no plano inline; decisões locais na tabela de Premissas do delta | Passos e gates no plano inline; evidência no chat e no `validation.md`; status na Rastreabilidade do delta; desvios: `## Desvios` no delta (não há `tasks.md`) | Aprovar delta e plano | Verifier (independência declarada); `validation.md` na pasta da mudança | Fecha com Verify PASS; Handoff aponta o passo | `apply_delta.py apply`; spec viva atualizada |
| **Medium, spec + tasks, sem design.md** | Delta e `tasks.md` aprovados | Requisitos: delta; estrutura mínima: seção `## Estrutura` no `tasks.md` (arquivos, componentes, o que reusa, em até dez linhas); decisões locais no delta | `tasks.md` inteiro (Matriz, Comandos de Gate, tasks, Desvios); evidência por task e no `validation.md`; status na Rastreabilidade | Aprovar delta e tasks | Verifier; aderência ao design compara com `## Estrutura` do `tasks.md` | Por task; Handoff com a última task | `apply_delta.py apply` |
| **Large/Complex, todos os artefatos** | Delta, `design.md`, `tasks.md` aprovados; Analyze sem CRITICAL nem HIGH pendente | Requisitos: delta; estrutura e decisões: `design.md`; decisões de projeto → ADR | `tasks.md`; evidência por task e `validation.md` com sensor; status na Rastreabilidade; desvios em `tasks.md` | Aprovar cada artefato; abordagem escolhida confirmada antes dos componentes | Verifier + sensor; UAT se user-facing (Complex) | Por task; Handoff | `apply_delta.py apply`; ADRs registradas |
| **Sem commits autorizados** (qualquer tier) | Igual ao tier | Igual ao tier | Igual ao tier; onde pediria hash, "sem commit"; progresso = artefatos atualizados na árvore de trabalho | Autorização de commit ausente não bloqueia implementar | Escopo do Verifier = `git diff <base>` + untracked sobre a árvore de trabalho | Handoff registra o estado dos arquivos; retomada reconcilia com `git status` (indício, não prova) | Igual ao tier; o arquivamento não exige commit |
| **Refactor `no-behavior-change`** | Spec viva existente; delta com o flag e sem ADDED/MODIFIED/REMOVED | Requisitos: os da spec viva que o refactor preserva, listados no Contexto do delta como invariantes; objetivo técnico declarado (o que melhora e por quê); tasks citam esses IDs em `Requisito` | Tasks e gates normais; testes existentes são a evidência (characterization); evidência = testes que continuam passando sobre o mesmo comportamento | Aprovar delta (invariantes e objetivo) e tasks | Verifier: eixo 1 prova que os invariantes citados continuam cobertos; sensor conforme o tier (o `lint_validation.py` o exige em Large/Complex; opcional em Medium sem risco nomeado) | Normal | `apply_delta.py apply` registra só a linha de histórico, uma vez |
| **Spike `spec-first`** | Delta com `spec-first` no comentário de máquina; usuário ciente de que é descartável | Requisitos no delta (podem ser poucos); estrutura inline | Plano inline ou tasks; evidência mínima declarada no delta | Aprovar delta | Passada própria; sem `validation.md` obrigatório | Fecha com o resultado do spike registrado no Contexto (o que se aprendeu); Handoff normal | Sem `apply_delta`; a pasta `changes/` fica como histórico com Status `Descartado` ou `Promovido a <mudança>` |
| **Modo código** (documentar comportamento existente) | Código, testes e docs existentes; nenhuma spec viva | Requisitos derivados do que o código faz, `[PREMISSA]` para intenção; divergências em seção própria (specify.md, Origem e modo) | Não há implementação: o artefato é o delta de baseline `changes/NNNN-baseline/spec.md`, todo ADDED | Aprovar o delta de baseline | Sem Verifier; a evidência é `file:line` do comportamento observado em cada requisito | Fecha ao arquivar | `apply_delta.py apply --create` cria a spec viva a partir do delta: o script continua sendo o único a escrever a lista de Requisitos |
| **Capability nova** (a partir de PRD ou ideia) | PRD Aprovado ou pedido rico | Delta todo ADDED; estrutura e decisões conforme o tier | Conforme o tier | Conforme o tier | Conforme o tier | Conforme o tier | `apply_delta.py apply --create` no arquivamento |
| **Sem repositório Git** | Diretório de saída indicado pelo ambiente | Igual ao tier | Igual ao tier; sem hash; sem `hotspots.py`; proveniência por `sha256` do conteúdo (seção 3) | Igual ao tier | Verifier sobre o conjunto de arquivos da mudança; sensor em cópia do diretório | Handoff registra paths e datas | Igual ao tier |

Regras transversais:

- Consumidor de artefato opcional lê o substituto desta tabela; nenhuma entrada exige `tasks.md`, `design.md`, "último commit" ou diretório de mudança em rota que os dispensa.
- Small que descobre que muda um requisito da spec viva, ou que ganha risco nomeado, sobe de tier (catraca) e passa a ter delta.
- Não invente requisito para preencher template: seção sem conteúdo real diz "N/A porque".

---

## 2. Estados e transições

| Artefato | Caminho normal | Saídas |
|---|---|---|
| **PRD** (prd-writer, output.md, Header) | Rascunho → Em Revisão → Aprovado → Substituído por NNNN | — |
| **Delta, design, tasks** | Rascunho → Aprovado → Em andamento → Concluído | Rascunho → Descartado ou Promovido a <mudança> (spike) ou Bloqueado (decisão material pendente, com o item que bloqueia) |
| **Rastreabilidade por requisito** | Pending → In Design → In Tasks → Implementing → Verified | qualquer estado → Removed (REMOVED, com razão) ou Blocked (depende de decisão pendente) |

Só o usuário aprova. Alteração material em PRD Aprovado (regra, escopo, contrato) volta a Em Revisão e invalida a aprovação das specs que citam os IDs tocados; correção editorial não muda Status. A revisão consumida pela spec é registrada em `prd-rev` (seção 3).

Alteração material em delta, design ou tasks Aprovado volta o artefato a Rascunho, e os artefatos a jusante que dependem do trecho alterado voltam a Rascunho também; correção editorial mantém o Status. Verified só pelo Verifier.

**Analyze** (verify.md, seção 1), severidade e efeito:

| Severidade | Critério | Efeito |
|---|---|---|
| CRITICAL | Viola decisão ativa; requisito P1 sem cobertura; `[PREMISSA-CRÍTICA]` não validada; contradição entre artefatos | Bloqueia Execute até correção no artefato-fonte |
| HIGH | Requisito duplicado ou conflitante; atributo de segurança ou performance ambíguo; critério não testável; task sem requisito | Bloqueia Execute até correção, ou aceite explícito do usuário registrado no relatório |
| MEDIUM | Drift de terminologia; edge case subespecificado; dimensão N/A contradita por task | Execute segue; item vira task de correção ou registro de aceite |
| LOW | Estilo | Nota |

"Analyze limpo" significa: nenhum CRITICAL, nenhum HIGH sem aceite registrado.

**Verify** (verify.md): PASS, FAIL ou BLOCKED (verificação incompleta: dependência indisponível, gate não executável, sensor impossível), com o motivo. PASS exige conformidade sem gap, gate verde, sensor sem sobrevivente quando obrigatório e UAT sem Bloqueante/Maior quando houver. FAIL gera tasks de correção (máximo 3 iterações). BLOCKED é entregável e não fecha a mudança.

**Arquivamento** (memory.md, seção 5): só após Verify PASS, desvios resolvidos (seção 4) e aprovação de conteúdo do fechamento pelo usuário (SKILL.md, Aprovações e autorizações); delta, design e tasks passam a Concluído; spec viva atualizada pelo script; histórico com uma linha por mudança.

Os relatórios preservam quatro distinções: **documento válido** (linter sem HARD) é diferente de **documento aprovável** (válido, revisado, sem `[LACUNA]` no caminho, Ponto de Maior Fragilidade nomeado), que é diferente de **implementação conforme** (Verify PASS), que é diferente de **verificação incompleta ou bloqueada** (BLOCKED, com motivo).

---

## 3. Proveniência

- Cada artefato cita a revisão exata do que consumiu: o delta declara `prd:` e `prd-rev:` no comentário de máquina; design cita `spec:`; tasks citam `design:` (ou `spec:` sem design); `validation.md` cita a base do diff. `prd-rev` é `git:<hash-do-blob>` (`git hash-object <arquivo>`) quando há Git, ou `sha256:<12 hex>` do conteúdo (`lint_spec.py --print-prd-rev`) quando não há. Data de calendário sozinha não identifica duas revisões do mesmo dia.
- `apply_delta.py apply --create` copia `prd` e `prd-rev` para a spec viva; mudanças posteriores registram no histórico a revisão do PRD que consumiram.
- Referência a versão antiga (PRD substituído, ID Removed) resolve para o documento histórico, marcada como histórica; nunca é recriada nem reciclada.
- Aprovação não converte premissa em fato: `[PREMISSA]` do PRD Aprovado continua `[PREMISSA]` na spec, com o plano de validação; só `[FATO]` do PRD é `[FATO]` na spec.
- Cenários de aceitação herdados chegam a requisitos e a evidências: cada cenário tem ID EARS que o cobre e, no Verify, `file:line`. Exigir aceitação de entrada válida não cobre a rejeição da inválida: os dois são requisitos distintos.
- Decisão técnica declara se é **restrição de produto ou contrato público** (API, evento, formato persistido, exposto a terceiros: muda com versionamento e aviso) ou **decisão interna** de implementação (muda sem aviso): coluna Tipo na tabela de Decisões técnicas do design.

---

## 4. Desvios e fechamento

- `SPEC_DEVIATION` que muda comportamento não sobrevive ao Verify: volta ao artefato de origem (PRD, spec, design), o artefato é reaprovado, a implementação é reverificada, e só então o delta correspondente é aplicado. O arquivamento nunca ajusta a spec ao código depois da verificação, e "registrado na memória como exclusão" não é prova de conformidade.
- Desvio que não muda comportamento (estrutura, nome interno) fica em `## Desvios` com justificativa e é julgado no eixo 2 do Verify.
- Problema adjacente encontrado durante a task (bug vizinho, dívida, dead code) é reportado, não corrigido; vira task ou mudança separada se o usuário quiser.
