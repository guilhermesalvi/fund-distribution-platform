# Specify

**Objetivo:** capturar *o quê* construir como requisitos testáveis, rastreáveis e sem ambiguidade: um contrato que o Design refina, as Tasks decompõem e o Verify audita.

Leia até o fim antes de agir.

---

## 0. Layout de arquivos (spec-anchored)

A spec de uma **capability** é viva e sobrevive às mudanças; cada mudança é um **delta** que se funde nela no arquivamento (memory.md, Arquivar). Capability ≈ área funcional de um bounded context (`fixed-income/bookbuilding`, `reservation-book/reservation-lifecycle`). O `<feature-slug>` da mudança é o `<feature-slug>` do PRD, sem o `<domain-slug>`, que já está no path da capability: PRD `0002-reservation-book-reservation-lifecycle.md` → `reservation-book/reservation-lifecycle/changes/NNNN-reservation-lifecycle/`.

```
/docs/specs/<domain-slug>/<capability-slug>/
├── spec.md                          # spec viva: requisitos vigentes com IDs
└── changes/NNNN-<feature-slug>/
    ├── spec.md                      # delta: ADDED / MODIFIED / REMOVED (IDs são estáveis; não há RENAMED)
    ├── design.md                    # Large/Complex ou risco nomeado
    ├── tasks.md                     # Large/Complex ou >5 passos
    └── validation.md                # relatório do Verifier
/docs/adr/NNNN-<slug>.md             # uma ADR por decisão de projeto (memory.md, Decisões e ADRs)
/docs/project-memory.md              # índice das AD-NNN, handoff, histórico de ciclos
```

- **Slugs são identificadores:** inglês, kebab-case, espelhando o nome que o código usa (`PartialReservation` → `partial-reservation`). O texto segue a Precedência de idioma (SKILL.md); o path acompanha branch, classe e prefixo de ID. Termo que o código mantém em português fica como o código escreveu. A mesma regra vale para o slug do PRD, porque os dois coincidem.
- **Mudanças são numeradas:** `changes/NNNN-<feature-slug>/`, contador de 4 dígitos global em `/docs/specs/`, alocado com `seq.py next /docs/specs --slug <feature-slug>` antes de criar o diretório, nunca lendo o diretório. O número é ordem de chegada e referência curta; quem sobrescreve quem é dito pelo delta (`MODIFIED`/`REMOVED` apontando para o ID), nunca pelo número. Contador global colide em PR paralelo: renumere o branch que entra depois; `seq.py check` acusa a duplicata.
- A `spec.md` viva **não** é numerada (uma por capability) e **não é reescrita por geração**: o modelo escreve o delta; `apply_delta.py` funde a lista de Requisitos, a Data e o Histórico (regiões do script); Propósito, Glossário e Domain Events são do autor (memory.md, Arquivar).
- **Crie artefatos sob demanda.** Nunca scaffolde `design.md` ou `tasks.md` vazios; ausência é o estado correto de fase pulada, e o substituto de cada artefato dispensado está em modes.md. Arquivo vazio mente sobre o processo.
- Capability nova: delta todo `ADDED`; o arquivamento cria a spec viva. Refactor puro: `<!-- sdd: spec-delta | no-behavior-change -->`, sem requisito inventado: o Contexto declara o objetivo técnico e os IDs da spec viva que o refactor preserva (modes.md). Spike descartável: `spec-first` no comentário de máquina; não há arquivamento, e o fechamento é registrar no Contexto o que se aprendeu e o Status `Descartado` ou `Promovido a <mudança>`; diga ao usuário, porque é exceção. Modo código: o primeiro delta é a baseline (`changes/NNNN-baseline/`), todo `ADDED`, arquivado com `apply_delta.py apply --create`.
- Não versione por timestamp no nome; git é o controle de versão. A spec viva mantém `## Histórico de revisões` ao fim, uma linha por mudança, com todos os IDs afetados explícitos (`+RSV-07, +RSV-08, ~RSV-03, -RSV-05`); ID com `-` fica aposentado para sempre.
- Sem repositório: mesmo layout sob o diretório de saída que o ambiente indica (SKILL.md, Gates, Caminhos).

**Comentário de máquina**, primeira linha de cada artefato, antes do `#`, ASCII minúsculo independente do idioma, lido pelos linters para seções por tier e cadeia de proveniência:

```
<!-- sdd: spec-delta | tier: large | capability: reservation-book/reservation-lifecycle | prd: /docs/prd/0002-reservation-book-reservation-lifecycle.md | prd-rev: git:3f9c2a1b7d0e4c5a9b8d7e6f0a1b2c3d4e5f6a7b -->
<!-- sdd: design | tier: large | spec: ./spec.md -->
<!-- sdd: tasks | tier: large | design: ./design.md -->
<!-- sdd: validation | change: 0001-partial-reservation | tier: large -->
```

`tier` ∈ {`small`, `medium`, `large`, `complex`}. `prd:` é o path do PRD relativo à raiz do repositório (omitido sem PRD); `prd-rev:` é a revisão exata consumida, `git:<hash-do-blob>` (`git hash-object <prd.md>`) ou `sha256:<12 hex>` sem Git (`lint_spec.py --print-prd-rev`), porque data sozinha não distingue duas revisões do mesmo dia (modes.md, Proveniência); `spec:`/`design:` apontam para o artefato de origem; `change:` é a identidade da mudança (`NNNN-<slug>`).

**Header humano:** tabela de duas colunas logo abaixo do `#`, rótulos no idioma do artefato (Status, Autor, Data, Capability, Prefixo, Confiança quando não for Alta). Status do delta ∈ {Rascunho, Aprovado, Em andamento, Concluído, Descartado, Bloqueado} (modes.md, Estados); da spec viva, Vigente. Data em AAAA-MM-DD, data real; Autor real (placeholder é HARD); Prefixo igual ao de todos os IDs do delta. Mesma forma e mesma rubrica de Confiança do `prd-writer`. O linter casa cada heading por igualdade com os aliases PT/EN, ignorando o alias entre parênteses; seção duplicada é HARD.

---

## 1. Origem e modo

Decida a origem pelo sinal no pedido; cada modo muda o que é `[FATO]`:

| Sinal no pedido | Modo | O que é `[FATO]` | Cuidado específico |
|---|---|---|---|
| PRD existe em `/docs/prd/` (layout do repositório, `prd-writer`) | **A partir do PRD** | Tudo que o PRD marca `[FATO]`; os FRs e Critérios de Aceitação aprovados, como fatos sobre a intenção. `[PREMISSA]` do PRD continua `[PREMISSA]` aqui, mesmo com o PRD Aprovado | Regras abaixo. `[PREMISSA-CRÍTICA]` do PRD entra como restrição, com o "se falsa" preservado; Não-objetivos viram Fora de Escopo; Métricas com guardrail viram Critérios de Sucesso |
| Sem PRD, mas usuário-alvo + problema + comportamento observável estão no pedido | **A partir da ideia** | O que o usuário afirmou | Registre o contexto em 3–5 linhas na seção Contexto; se descobrir que falta usuário ou problema, pare e redirecione |
| Sem PRD e falta usuário-alvo ou problema (solution-first, "CRUD para X", "tela de Y") | **Redirecione** | — | "Isso precisa de PRD antes": ative `prd-writer` pelo nome; retome Specify com o PRD aprovado |
| Código existente sem spec ("documente a spec do módulo X") | **Modo código** | O que o código *faz* (comportamento observável, testes, docs) | Nunca confunda o que o código faz com o que deveria fazer. Intenção inferida é `[PREMISSA]`; comportamento sem justificativa de negócio é `[LACUNA]` (feature órfã). Divergências ganham seção própria. Estratégia de leitura: design.md, Análise da base |

**A partir do PRD, seis regras:**

- **O requisito EARS cita o ID do PRD com prefixo e nunca reescreve a regra.** A spec descreve o comportamento observável do sistema que realiza a regra (valor, status, evento, prazo); a regra em si continua no FR do PRD. A citação vai ao fim da linha, entre colchetes (`[BOOK-04]`), e a seção Rastreabilidade lista PRD → EARS. Regra reescrita passa a existir em dois lugares e diverge; o PRD deixa de ser fonte. Estado, evento e conceito usam o Identificador que o PRD fixa (coluna Identificador da tabela de estados; nome do evento no catálogo do PRD 0000); o Glossário da spec só tem termos de solution space e aponta o glossário do PRD para o resto.
- **Lacuna ou inconsistência no PRD se corrige no PRD primeiro.** Regra de negócio ausente, ambígua ou contraditória não vira `[PREMISSA]` na spec: pare, corrija o PRD com o `prd-writer`, peça o commit do PRD quando commits estiverem autorizados e cite o hash no Contexto da spec; sem commit, cite o campo Data do PRD. `[PREMISSA]` na spec fica para decisão de solution space (formato de erro, prazo técnico, ordem de processamento) que o PRD não governa. Resolver regra na spec decide problem space sem quem é dono dele.
- **O prefixo da spec é distinto de todo prefixo de PRD** (`RSV` para a capability, `BOOK` no PRD) e não confundível com ele (`OFR` ao lado de `OFF` convida a erro de leitura; prefira sigla de outra raiz). Os dois têm a forma `X-nn` e tasks e testes citam ambos; prefixo igual torna `BOOK-07` ambíguo. Declare no header (campo Prefixo), igual ao prefixo de todo ID ADDED/MODIFIED; `lint_spec.py` acusa colisão e divergência lendo `/docs/prd`, e citação com prefixo que nenhum PRD declara é HARD.
- **Maturidade do PRD.** Specify consome PRD com Status Aprovado (prd-writer, output.md, Header). PRD em Rascunho ou Em Revisão só entra com decisão explícita do usuário nesta sessão: registre no Contexto que a spec nasce de PRD não aprovado e quem autorizou, limite a Confiança a Média e liste em Perguntas em Aberto as `[LACUNA]` e `[PREMISSA-CRÍTICA]` do PRD que tocam o escopo, com dono. Mudança posterior no PRD re-deriva a spec (SKILL.md, refine o contexto).
- **PRD 0000 e NFRs.** Quando existe PRD 0000, leia o mapa de contextos, o catálogo de eventos (produtor, consumidores, gatilho, IDs) e as Decisões delegadas a ADR: evento que a capability produz ou consome vira requisito EARS citando o ID que o governa; decisão delegada a ADR entra em Premissas e Perguntas em Aberto com dono "Design/ADR" e não se resolve na spec. NFR do PRD com resultado observável por teste (prazo, atomicidade de uma operação, registro de auditoria) vira requisito EARS citando o `X-NFR-nn`; NFR que é atributo de qualidade sem teste direto (consistência entre consumidores, exatidão como propriedade) entra na Rastreabilidade como origem de critério de design (design.md, Critérios antes das abordagens) e na tabela de Dimensões Implícitas.
- **Critérios de Aceitação herdados.** Os cenários dos Critérios de Aceitação do PRD são a suíte mínima que o Execute reproduz (execute.md, Testes derivados da spec): a Rastreabilidade lista cada cenário pelo nome do caso, idêntico à primeira coluna da tabela do PRD, ou citando entre parênteses o ID do FR que exercita (Dado/Quando/Então), com os IDs EARS que o cobrem; linha sem nenhum dos dois é HARD. Cenário sem requisito EARS que o cubra é lacuna da spec, não do PRD; aceitar a entrada válida e rejeitar a inválida são cenários e requisitos distintos.

Em qualquer modo, carregue antes de escrever: decisões `AD-NNN` ativas em `project-memory.md` (restringem o que a spec pode pedir) e a `spec.md` viva da capability, se existir (o delta é relativo a ela).

---

## 2. Varredura de contexto e clarify

**Varredura leve primeiro** (cadeia de verificação, design.md, Pesquisa): antes de qualquer pergunta, leia código vizinho, padrões e features irmãs. Use o que encontrar para ancorar as perguntas na realidade, não para limitar a spec ao que existe. A spec captura o que é *necessário*, não só o que há.

**Você é par técnico, não entrevistador.** Comece aberto; siga a energia do usuário; desafie vagueza ("bom" é o quê? "usuários" são quem? "rápido" é quanto?). Torne o abstrato concreto: "me conduz por um uso disso".

**Clarify, orçamento e priorização** (tier Complex sempre; Large quando há área cinzenta; Medium/Small pulam):

1. Varredura interna de cobertura, marcando cada categoria como Clara / Parcial / Ausente: escopo funcional e papéis; modelo de domínio (entidades, identidade, transições de estado, volume); fluxo de interação (jornadas, estados de erro, vazio, carregamento); atributos não funcionais (latência, escala, disponibilidade, observabilidade, segurança, regulação); integrações e falhas externas; edge cases e conflitos; restrições e alternativas rejeitadas; terminologia; sinais de conclusão (testabilidade dos critérios).
2. Fila interna de perguntas candidatas. **Máximo 5 na rodada.** Priorize por impacto × incerteza; inclua só perguntas cuja resposta muda arquitetura, modelo de dados, decomposição, desenho de teste ou aceitação. Exclua o que já foi respondido, preferência estilística e o que o código responde. O orçamento limita a rodada de esclarecimento; decisão material que ficou de fora continua pendente em Perguntas em Aberto, bloqueando só o que depende dela (SKILL.md, Decisão, premissa ou bloqueio), nunca vira premissa por falta de orçamento.
3. Apresente **uma por vez**: interrogativa completa (nunca um rótulo), uma linha "por que importa", opções concretas com a recomendada primeiro e uma linha de racional. O usuário deve poder aceitar ou sobrescrever numa palavra. Ofereça "você decide" quando razoável: a resposta é delegação explícita e vira decisão (a) de SKILL.md, Decisão, premissa ou bloqueio, registrada como tal. Pergunta sem resposta não vira default: fica como (c), bloqueando só o que depende dela.
4. Codifique cada resposta na spec **imediatamente** (requisito, assumption ou fora de escopo), não ao fim.

**Guardrail de escopo.** A fronteira da mudança é fixa. Clarify esclarece *como* algo deve se comportar, nunca *se* uma nova capability entra. Sugestão de escopo novo → "isso é outra mudança; registro em Ideias Adiadas" e volte.

---

## 3. Varredura de dimensões implícitas

Requisitos que ninguém pede e todo sistema precisa. Ao fechar o entendimento, antes de apresentar:

| Dimensão | Cobrir |
|---|---|
| Validação de entrada e limites | Formatos, limites, sanitização |
| Falha e falha parcial | Timeout, gravação parcial, rollback, compensação |
| Idempotência, retry, duplicata | Retry seguro, dedup key, exactly-once vs at-least-once |
| Autorização e rate limit | Quem chama o quê; throttling |
| Concorrência e ordenação | Condição de corrida, garantia de ordem, lock otimista |
| Ciclo de vida dos dados | TTL, arquivamento, exclusão, retenção regulatória |
| Observabilidade | Log, métrica, trace, correlação |
| Falha de dependência externa | Circuit breaker, fallback, degradação |
| Integridade de transição de estado | Transições válidas, guardas, estado terminal |
| Consistência entre contextos | Evento publicado, contrato consumido, eventual vs forte |

Por tier: **Large/Complex** cobrem toda dimensão, cada uma vira requisito **ou** `N/A porque [razão]`; célula em branco não existe. **Medium** cobre só as dimensões presentes no domínio da feature e colapsa o resto em `demais dimensões N/A para este escopo`. **Small** pula. O `N/A porque` é obrigatório: impede inventar requisito para preencher lista. A varredura é limitada ao escopo desta mudança.

---

## 4. Histórias e prioridade

**P1 = MVP** (fatia vertical, demonstrável sozinha por API, consumer, job ou UI; "vertical" é atravessar as camadas que a capability tem, não exigir frontend), **P2** deveria, **P3** nice-to-have. Cada história é **independentemente testável**: dá para implementar e demonstrar só ela. História que só faz sentido junto com outra está mal cortada. Histórias organizam requisitos por valor; o contrato são os requisitos abaixo delas.

---

## 5. Requisitos em EARS

Todo requisito segue exatamente **um** padrão EARS (*Easy Approach to Requirements Syntax*). Um padrão por requisito torna cada um inequívoco e diretamente testável, e promove as dimensões implícitas a cidadãos de primeira classe.

| Padrão | Keyword | Template | Use para |
|---|---|---|---|
| Ubiquitous | — | The [system] SHALL [response] | Invariantes sempre válidas |
| Event-driven | WHEN | WHEN [trigger] THEN the [system] SHALL [response] | Resposta a um gatilho discreto |
| State-driven | WHILE | WHILE [state] the [system] SHALL [response] | Comportamento válido durante um estado |
| Optional-feature | WHERE | WHERE [feature is present] the [system] SHALL [response] | Comportamento atrás de flag ou capability opcional |
| Unwanted-behavior | IF / THEN | IF [undesired condition] THEN the [system] SHALL [response] | Erros, falhas, entrada inválida, timeout |
| Complex | combinação | WHILE [state], WHEN [trigger] the [system] SHALL [response] | Combinações das anteriores |

- **Um requisito = uma unidade comportamental verificável**: obrigações independentes (que podem falhar separadamente) vão em requisitos separados; condição conjunta (`WHILE A, WHEN B`) e efeito indivisível (gravar e publicar na mesma transação) ficam no mesmo requisito, porque fragmentá-los inventa estados intermediários que a spec não quer. O teste é: dá para escrever um teste que afirme exatamente este resultado?
- **Valores concretos**: status code, mensagem, limite, prazo. "Rapidamente", "graciosamente", "apropriado" não são requisitos.
- Todo requisito contém `SHALL` e é mensurável; o linter rejeita sem `SHALL` e avisa quando não reconhece padrão.
- Keywords em inglês mesmo em spec em português; o corpo pode ser em português: `WHEN o investidor confirma a reserva THEN the system SHALL registrar a reserva com status Pendente em até 2s [BOOK-01]`.
- Domain event relevante a outro contexto é requisito, não detalhe de implementação: `WHEN a reserva é confirmada THEN the system SHALL publicar ReservationConfirmed com [payload semântico]`.
- **IDs:** `[PREFIXO]-[NN]` (`RSV-01`, `SETTLE-07`). Prefixo por capability, distinto dos prefixos de PRD (seção 1), 2+ dígitos, nunca reutilizado: ID removido morre. Todo requisito tem ID desde o rascunho; é o que rastreia até task e teste.
- **Edge cases** são requisitos Unwanted-behavior ou de fronteira, com ID como os outros; não uma lista solta.

---

## 6. Modelo de delta (spec-anchored)

A `spec.md` viva tem os requisitos vigentes; a `changes/NNNN-<feature>/spec.md` é um **delta** relativo a ela:

| Seção | Conteúdo | Regra |
|---|---|---|
| `## ADDED Requirements` | Requisitos novos, com ID novo | — |
| `## MODIFIED Requirements` | Requisito existente com texto novo | Reproduza o ID e o **texto completo** novo (não diff); uma linha `Antes:` com o texto anterior |
| `## REMOVED Requirements` | ID + uma linha de razão | Requisito removido precisa de razão registrada; o ID fica aposentado e o teste correspondente é removido na task com a mesma razão |

IDs são estáveis: não existe RENAMED. Mudar o significado é `MODIFIED`; substituir o conceito é `REMOVED` + `ADDED` com ID novo. `MODIFIED`/`REMOVED` apontando para ID inexistente na spec viva, `Antes:` divergente do texto vigente e seção `RENAMED` são `HARD` no linter e no `apply_delta.py`.

---

## 7. Gate de fechamento (antes de apresentar)

A spec não é apresentável até que cada item esteja resolvido ou registrado como assumption. Large/Complex: gate completo. Medium: resolva ambiguidades óbvias, registre o resto. Small: pula.

1. **Inequivocidade e precisão.** Cada requisito tem uma única interpretação e um resultado esperado preciso. Falhou em um dos dois: resolva com o usuário, divida, ou registre como assumption com interpretação escolhida + racional.
2. **Fechamento de perguntas e assumptions.** Toda decisão não resolvida no clarify vira (a) resolvida ou (b) assumption com default + racional na tabela. Nada segue sem marca. Assumption é só de solution space; regra de negócio volta ao PRD (seção 1).
3. **Áreas cinzentas recusadas viram assumptions.** O que o usuário explicitamente não quis discutir ("decide você", "não importa") é registrado com o default do agente e o racional; nunca descartado em silêncio. Ausência de resposta não é recusa: a pergunta fica em Perguntas em Aberto, bloqueando só o que depende dela (SKILL.md, Decisão, premissa ou bloqueio).
4. **Gate de lacuna** e **`[PREMISSA-CRÍTICA]`** conforme SKILL.md, Convenção de confiança; as premissas críticas ficam listadas ao fim como blockers antes de Execute.

O gate é limitado às dimensões declaradas e ao comportamento real desta mudança, nunca a "tudo que se pode imaginar". Fora de Escopo é o contrapeso: o gate esclarece requisitos existentes, não cria novos.

Depois: `lint_spec.py` (SKILL.md, Gates). Apresente só com linter limpo e diga o que precisa de validação.

---

## Ponto de Maior Fragilidade

`spec.md` (tier ≥ Medium) e `design.md` terminam nomeando **uma** decisão de julgamento, a que um revisor cético atacaria primeiro. Mesma regra do `prd-writer` (writing.md, Ponto de Maior Fragilidade): não é `[PREMISSA-CRÍTICA]` nem `[LACUNA]`; forma decisão, vetor de ataque, convite ao desafio; calibrada ao custo do erro (Small/Medium: duas linhas); sem auto-crítica cosmética. Na spec, tipicamente corte de escopo, limite numérico ou padrão EARS que fixa comportamento ambíguo; no design, fronteira de componente, escolha de consistência, acoplamento aceito.

---

## Template: delta `changes/NNNN-<feature-slug>/spec.md`

Rótulos em PT; em spec em inglês, use os rótulos EN entre parênteses (o linter aceita ambos).

```markdown
<!-- sdd: spec-delta | tier: large | capability: reservation-book/reservation-lifecycle | prd: /docs/prd/0002-reservation-book-reservation-lifecycle.md | prd-rev: git:3f9c2a1b7d0e4c5a9b8d7e6f0a1b2c3d4e5f6a7b -->
# Reserva Parcial no Livro

| | |
|---|---|
| **Status** | Rascunho |
| **Autor** | [nome] |
| **Data** | 2026-09-05 |
| **Capability** | reservation-book/reservation-lifecycle |
| **Prefixo** | RSV |
| **Confiança** | Média — uma premissa-crítica em validação |

## Contexto (Context)

[3–5 linhas. A partir do PRD: link, Status do PRD e quem autorizou seguir se não Aprovado, resumo do problema e da capability; correções feitas no PRD durante esta spec, com o hash do commit ou, sem commit, a Data do PRD. A partir da ideia: usuário-alvo, problema, resultado esperado. Modo código: o que a base faz hoje e por que está sendo especificada.]

## Escopo e Fora de Escopo (Scope / Out of Scope)

**Em escopo:** [uma frase por história P1/P2]

| Fora de escopo | Razão |
|---|---|
| [item] | [por quê] |

## Premissas e Perguntas em Aberto (Assumptions & Open Questions)

| Premissa / decisão | Default escolhido | Racional | Confirmada? |
|---|---|---|---|
| [PREMISSA] [ambiguidade de solution space] | [o que faremos] | [por quê] | não |

**Premissas críticas:**
- [PREMISSA-CRÍTICA] [afirmação]. Se falsa, [consequência para a abordagem]. Validar com [quem/como] antes de Execute.

**Perguntas em aberto:**
- Blocker antes de Execute: a `[PREMISSA-CRÍTICA]` acima. Dono: produto; resolve com a validação indicada.
- [pergunta com impacto, dono e critério de resolução; "nenhuma" só quando não há pendência, e nenhuma pode estar no caminho]

## Histórias (User Stories)

### P1: [título] ⭐ MVP
**Como** [papel], **quero** [capacidade] **para** [benefício].
**Por que P1:** [razão]
**Teste independente:** [como demonstrar só esta história]

## ADDED Requirements

- **RSV-07** — WHEN o operador registra reserva com quantidade abaixo do investimento mínimo THEN the system SHALL rejeitar com `MIN_INVESTMENT_NOT_MET` e manter o livro inalterado [BOOK-03]  <!-- unwanted -->
- **RSV-08** — WHILE a oferta está `Open` the system SHALL aceitar reservas cuja posição do investidor não exceda o investimento máximo [BOOK-04]  <!-- state-driven -->
- **RSV-09** — WHEN a reserva é aceita THEN the system SHALL registrar instante e ordem de registro imutáveis em até 1s [BOOK-14]  <!-- event-driven -->
- **RSV-10** — IF o mesmo registro chega duas vezes com o mesmo `idempotencyKey` THEN the system SHALL devolver a reserva original sem duplicar  <!-- unwanted; dimensão implícita -->
- **RSV-11** — IF a posição do investidor com a nova reserva excede o investimento máximo THEN the system SHALL rejeitar com `POSITION_ABOVE_MAXIMUM` e manter o livro inalterado [BOOK-04]  <!-- unwanted -->
- **RSV-12** — IF dois registros concorrentes do mesmo investidor chegam com chaves distintas THEN the system SHALL aceitar no máximo o que cabe no investimento máximo, reavaliando a posição a cada aceite  <!-- unwanted; dimensão implícita -->

## MODIFIED Requirements

- **RSV-03** — WHEN a oferta fecha THEN the system SHALL congelar todas as reservas ativas, inclusive parciais [BOOK-15]
  Antes: WHEN a oferta fecha THEN the system SHALL congelar as reservas integrais

## REMOVED Requirements

- **RSV-05** — Razão: reserva sempre integral deixa de existir com RSV-08. *(ID precisa existir na spec viva)*

## Dimensões Implícitas (Implicit Dimensions)

| Dimensão | Requisito ou N/A porque |
|---|---|
| Validação de entrada | RSV-07, RSV-11 |
| Idempotência | RSV-10 |
| Concorrência | RSV-12 (idempotência de um registro não cobre dois registros distintos concorrentes) |
| … | … |

## Critérios de Sucesso (Success Criteria)

- [ ] [resultado mensurável, tecnologia-agnóstico; herda métricas e guardrails do PRD quando existe]

## Rastreabilidade (Requirement Traceability)

PRD → EARS. Cada FR do PRD em escopo aparece; `—` marca requisito sem origem no PRD (dimensão implícita, decisão de solution space).

| ID do PRD | IDs EARS |
|---|---|
| BOOK-03 | RSV-07 |
| BOOK-04 | RSV-08, RSV-11 |
| BOOK-14 | RSV-09 |
| BOOK-15 | RSV-03 |
| — (idempotência) | RSV-10 |
| — (concorrência) | RSV-12 |

Cenários herdados dos Critérios de Aceitação do PRD, pelo nome do caso ou pelo FR que exercitam (aceitar a entrada válida e rejeitar a inválida são cenários distintos):

| Cenário do PRD | IDs EARS |
|---|---|
| Segunda reserva dentro do máximo aceita (BOOK-04, Dado/Quando/Então) | RSV-08 |
| Terceira reserva acima do máximo rejeitada (BOOK-04, Dado/Quando/Então) | RSV-11 |

Status por requisito EARS (Pending → In Design → In Tasks → Implementing → Verified; modes.md, Estados):

| ID | História | Status |
|---|---|---|
| RSV-07 | P1 | Pending |
| RSV-08 | P1 | Pending |
| RSV-09 | P1 | Pending |
| RSV-10 | P1 | Pending |
| RSV-11 | P1 | Pending |
| RSV-12 | P1 | Pending |
| RSV-03 | P1 | Pending |

## Ponto de Maior Fragilidade (Weakest Point)

[A decisão; o vetor de ataque; o convite ao desafio.]
```

Modo código: o delta é a baseline (`changes/NNNN-baseline/spec.md`, todo ADDED, cada requisito com a evidência `file:line` do comportamento observado) e adiciona `## Divergências identificadas`: o que o código faz e parece não dever fazer, o que deveria fazer e não faz, dead code; cada item `[PREMISSA]` com a evidência (`file:line`). Arquiva-se com `apply_delta.py apply --create` (modes.md, Contrato por combinação, Modo código).

## Template: spec viva `<capability>/spec.md`

```markdown
<!-- sdd: spec | capability: reservation-book/reservation-lifecycle | prd: /docs/prd/0002-reservation-book-reservation-lifecycle.md | prd-rev: git:3f9c2a1b7d0e4c5a9b8d7e6f0a1b2c3d4e5f6a7b -->
# Reservation Lifecycle — Spec

| | |
|---|---|
| **Status** | Vigente |
| **Data** | 2026-09-05 (última mudança: 0001-partial-reservation) |
| **Capability** | reservation-book/reservation-lifecycle |
| **Prefixo** | RSV |

## Propósito (Purpose)

[2–4 linhas: para que existe esta capability, quem a usa, PRD de origem.]

## Requisitos (Requirements)

- **RSV-01** — WHEN a oferta é publicada THEN the system SHALL passar a aceitar reservas com os limites, período e opções publicados [BOOK-01]
- **RSV-03** — WHEN a oferta fecha THEN the system SHALL congelar todas as reservas ativas, inclusive parciais [BOOK-15]

## Domain Events

| Evento | Produtor | Consumidores | Payload semântico | Gatilho |
|---|---|---|---|---|

## Glossário

[Só termos de solution space; termo de domínio aponta o glossário do PRD.]

## Histórico de revisões

| Data | Mudança | IDs afetados |
|---|---|---|
| 2026-09-05 | 0001-partial-reservation | +RSV-07, +RSV-08, +RSV-09, +RSV-10, +RSV-11, +RSV-12, ~RSV-03, -RSV-05 |
```

---

## Critérios de qualidade (passada Tier 2)

- Cada requisito é um padrão EARS, com `SHALL`, valor concreto e ID único (seção 5). Se você não consegue escrever o teste, reescreva o requisito.
- Requisito derivado do PRD cita o ID e não reescreve a regra; nenhuma regra de negócio decidida por assumption; Status do PRD registrado; PRD 0000, NFRs e Critérios de Aceitação consumidos conforme as seis regras (seção 1).
- P1 é fatia vertical demonstrável, não "só backend" (seção 4).
- Dimensões implícitas cobertas ou `N/A porque`; nenhuma inventada (seção 3).
- Toda inferência marcada; modo código nunca promove inferência a `[FATO]` (seção 1).
- Gate de fechamento cumprido (seção 7); Fora de Escopo presente quando há risco de creep; Ideias Adiadas capturam o que foi cortado no clarify.
- Delta aponta só para IDs existentes; capability nova é toda ADDED (seção 6).
- Ponto de Maior Fragilidade presente em tier ≥ Medium (seção acima).
- A spec reduz improviso no Design: se o Design vai precisar decidir comportamento, a spec ficou incompleta.
