<!-- sdd: spec-delta | tier: complex | capability: offering/offer-lifecycle | prd: /docs/prd/0001-offering-offer-lifecycle.md | prd-rev: git:1be799f82eb57fec0bffe47d6dbb4935e8177233 -->
# Cadastro e Ciclo de Vida da Oferta

| | |
|---|---|
| **Status** | Rascunho |
| **Autor** | Guilherme Salvi |
| **Data** | 2026-09-06 |
| **Capability** | offering/offer-lifecycle |
| **Prefixo** | OLC |
| **Confiança** | Média — PRD de origem em Rascunho; uma pergunta de regra de negócio devolvida ao PRD |

## Contexto (Context)

Origem: [PRD 0001](../../../../prd/0001-offering-offer-lifecycle.md), tier `complexa`, Status Rascunho em 2026-09-06; o usuário autorizou nesta sessão abrir a spec sobre o rascunho, por isso a Confiança fica em Média até a aprovação do PRD. Mapa de contextos, catálogo de eventos e decisões delegadas a ADR vêm do [PRD 0000](../../../../prd/0000-platform-overview.md). A capability é upstream: ReservationBook e Allocation leem a definição publicada e o estado corrente; o Allocation devolve `BookProcessed`, único gatilho de `Unconditional` e `Lapsed`.

Base lida: `src/Offering` contém só a composição do serviço (`Program.cs` com `AddServiceDefaults`/`AddApiDefaults`), sem domínio; `tests/UnitTests` e `tests/IntegrationTests` têm o esqueleto do xUnit. Convenções que a spec respeita: `.claude/rules/program-composition.md` (módulo de feature, endpoints versionados, `JsonSerializerContext` por feature) e `.claude/rules/tracing.md` (sem span manual em handler; tags `app.*`). Capability nova: delta todo ADDED; o arquivamento cria a spec viva.

Correção feita no PRD durante esta spec (sem commit; Data do PRD 2026-09-04, editado em 2026-09-06): Perguntas em Aberto do PRD 0001 passou a registrar a pergunta sobre conjunto de opções informado em oferta sem distribuição parcial (OFF-20), porque a spec não decide problem space.

## Escopo e Fora de Escopo (Scope / Out of Scope)

**Em escopo:** cadastro de Draft, publicação com validação completa, imutabilidade da definição, máquina de estados com transições explícitas, eventos produzidos (`OfferPublished`, `OfferClosed`, `OfferRevoked`), consumo de `BookProcessed`, consulta por outros contextos.

| Fora de escopo | Razão |
|---|---|
| Semântica das opções de condicionamento aplicada ao livro (OFF-26 a OFF-28) | Definida no PRD 0001, aplicada pela capability `allocation/book-processing`; aqui só o conjunto aceito é exposto |
| Verificação de que a reserva escolhe opção do conjunto aceito (OFF-29) | É BOOK-08, capability `reservation-book/reservation-lifecycle` |
| Séries, tranches, lote adicional, modificação de oferta, suspensão, liquidação, cadastro de fundo e investidor | Não-objetivos do PRD 0001 |
| Transporte dos eventos entre contextos | Decisão delegada a ADR pelo PRD 0000, exigência OFF-NFR-03; entra no Design |
| Autenticação e autorização do operador | Não modeladas no MVP (Premissas) |

## Premissas e Perguntas em Aberto (Assumptions & Open Questions)

| Premissa / decisão | Default escolhido | Racional | Confirmada? |
|---|---|---|---|
| [PREMISSA] Forma da rejeição de publicação e de transição | ProblemDetails com `status` 422 para violação de publicação e 409 para transição inválida; corpo com `violations[]`, cada item `attribute` e `rule` (`OFF-nn`); código estável em `type` | `AddApiDefaults()` já usa ProblemDetails; OFF-04 exige atributo e regra por violação | não |
| [PREMISSA] Identificador da oferta | GUID gerado na criação do Draft, imutável | Nome não é chave (OFF-15); consumidores citam a oferta pelo identificador | não |
| [PREMISSA] Instante corrente | Relógio do serviço em UTC, injetado (`TimeProvider`) para teste determinístico | OFF-07, OFF-08 e OFF-24 comparam instantes; teste precisa controlar o relógio | não |
| [PREMISSA] Descarte de Draft | Remoção lógica: a oferta deixa de existir para consulta e transição; nenhum evento | OFF-02 e o diagrama (`Draft --> [*]`); nenhum consumidor conhece Drafts (OFF-14) | não |
| [PREMISSA] Sem autenticação no MVP | "Quem disparou" (OFF-NFR-02) é o identificador de operador informado na requisição ou o nome do contexto produtor do evento | PRD 0002 fixa que o investidor não tem identidade; o PRD 0001 não pede autenticação | não |
| [PREMISSA] Concorrência entre transições | Lock otimista por versão da oferta; a segunda transição concorrente é reavaliada contra o estado resultante | OFF-NFR-01 exige atomicidade; sem fila de comandos no MVP | não |

**Premissas críticas:**
- [PREMISSA-CRÍTICA] Os consumidores obtêm a definição completa pelo evento `OfferPublished` e usam a consulta (OLC-38) só para reconciliação. Se falsa, a consulta vira contrato síncrono no caminho crítico das reservas e o ADR de transporte muda de natureza (leitura consistente em vez de entrega de evento). Validar com o autor ao aprovar o PRD 0001, antes de Execute.

**Perguntas em aberto:**
- Oferta sem distribuição parcial publicada com conjunto de opções informado: rejeitar ou ignorar? Regra de negócio; registrada em Perguntas em Aberto do PRD 0001 (OFF-20). Dono: autor do PRD. Bloqueia só o requisito de validação correspondente (OLC-23 cobre apenas o caso de conjunto vazio); as demais tasks seguem.
- Transporte dos eventos e garantia de OFF-NFR-03 (definição e estado iguais para todos os consumidores). Dono: Design/ADR, conforme PRD 0000, Decisões delegadas a ADR. Fora do caminho da spec.
- Aprovação do PRD 0001 (Status Rascunho). Dono: usuário. Bloqueia Design.

## Histórias (User Stories)

### P1: Publicar uma oferta válida ⭐ MVP
**Como** operador de distribuição, **quero** cadastrar a oferta em Draft e publicá-la com validação completa **para** que os demais contextos passem a ver uma definição estável e o estado `Open`.
**Por que P1:** sem oferta publicada nenhuma reserva existe; é a raiz de dependência da plataforma.
**Teste independente:** criar Draft, publicar, consultar como outro contexto e obter definição idêntica com estado `Open`; publicar Draft inválido e receber todas as violações.

### P1: Conduzir a oferta pela máquina de estados
**Como** operador de distribuição, **quero** fechar, revogar e encerrar a oferta, e ver o estado avançar com o desfecho do livro, **para** que o ciclo tenha um estado inequívoco em cada instante.
**Por que P1:** o fechamento é o gatilho do processamento do livro; sem ele o Allocation não inicia.
**Teste independente:** oferta `Open` → fechar → `Closed` → desfecho formada → `Unconditional` → encerrar → `Completed`; transições fora do diagrama rejeitadas; desfecho fora de `Closed` descartado e registrado.

### P2: Consultar a oferta como contexto consumidor
**Como** ReservationBook ou Allocation, **quero** consultar a definição publicada e o estado corrente pelo identificador **para** reconciliar o que recebi por evento.
**Por que P2:** o caminho principal é o evento (Premissas críticas); a consulta é reconciliação.
**Teste independente:** consultar oferta `Open` e receber definição e estado; consultar Draft e receber `OFFER_NOT_FOUND`.

## ADDED Requirements

### Ciclo de vida

- **OLC-01** — WHEN o operador cria uma oferta THEN the system SHALL registrá-la em `Draft` com identificador único e os atributos informados, sem validar nenhum deles [OFF-01]
- **OLC-02** — WHILE a oferta está `Draft` the system SHALL aceitar edição de qualquer atributo, inclusive para valor ausente ou inconsistente [OFF-02]
- **OLC-03** — WHEN o operador descarta uma oferta `Draft` THEN the system SHALL removê-la de consulta e de qualquer transição posterior, respondendo `OFFER_NOT_FOUND` a acessos seguintes [OFF-02]
- **OLC-04** — WHEN o operador publica uma oferta `Draft` sem violação de OLC-17 a OLC-28 THEN the system SHALL passar a oferta a `Open` em uma única operação [OFF-03]
- **OLC-05** — IF a publicação viola uma ou mais regras THEN the system SHALL manter a oferta em `Draft` e responder com a lista completa de violações, cada uma com o atributo e o ID da regra do PRD [OFF-04]
- **OLC-06** — WHILE a oferta está em estado diferente de `Draft` the system SHALL rejeitar qualquer alteração de atributo com `OFFER_IMMUTABLE`, mantendo a definição publicada byte a byte [OFF-05]
- **OLC-07** — IF uma transição fora do diagrama do PRD é solicitada THEN the system SHALL rejeitar com `INVALID_TRANSITION`, informando estado corrente e transição tentada, sem alterar a oferta [OFF-06]
- **OLC-08** — WHILE a oferta está `Open` e o instante corrente é maior ou igual ao início do período de reserva, WHEN o operador fecha THEN the system SHALL passar a oferta a `Closed` [OFF-07]
- **OLC-09** — IF o operador fecha uma oferta `Open` antes do início do período de reserva THEN the system SHALL rejeitar com `RESERVATION_PERIOD_NOT_STARTED` e manter `Open` [OFF-07]
- **OLC-10** — WHILE a oferta está `Open` e o instante corrente é posterior ao fim do período de reserva the system SHALL expor `acceptingReservations = false` na consulta, sem mudar o estado [OFF-08]
- **OLC-11** — WHILE a oferta está `Closed`, WHEN `BookProcessed` informa desfecho não formada THEN the system SHALL passar a oferta a `Lapsed` [OFF-09]
- **OLC-12** — WHILE a oferta está `Closed`, WHEN `BookProcessed` informa desfecho formada com alocação concluída THEN the system SHALL passar a oferta a `Unconditional` [OFF-10]
- **OLC-13** — IF `BookProcessed` chega com a oferta em estado diferente de `Closed` THEN the system SHALL manter estado e definição, registrar o desfecho como descartado com estado corrente, identificador do evento e instante, e não emitir evento [OFF-11]
- **OLC-14** — WHILE a oferta está `Open`, `Closed` ou `Unconditional`, WHEN o operador revoga THEN the system SHALL passar a oferta a `Revoked` [OFF-12]
- **OLC-15** — WHILE a oferta está `Unconditional`, WHEN o operador encerra THEN the system SHALL passar a oferta a `Completed` [OFF-13]
- **OLC-16** — The system SHALL expor a outros contextos somente ofertas em estado diferente de `Draft`, cada uma com a definição publicada e o estado corrente [OFF-14]

### Validação na publicação

- **OLC-17** — IF o nome está ausente ou vazio após remoção de espaços nas bordas THEN the system SHALL registrar a violação `NAME_REQUIRED` com regra OFF-15 [OFF-15]
- **OLC-18** — IF fundo, classe ou número da emissão está ausente THEN the system SHALL registrar a violação `SHARE_IDENTIFICATION_INCOMPLETE` com regra OFF-16 [OFF-16]
- **OLC-19** — WHEN a oferta é publicada THEN the system SHALL armazenar fundo, classe e subclasse sem espaços nas bordas e compará-los sem distinção de caixa, sem consultar cadastro nem verificar unicidade [OFF-16]
- **OLC-20** — IF o preço por cota é menor ou igual a zero ou tem mais de 8 casas decimais THEN the system SHALL registrar a violação `UNIT_PRICE_INVALID` com regra OFF-17 [OFF-17]
- **OLC-21** — IF a quantidade base não é inteira ou é menor que 1 THEN the system SHALL registrar a violação `BASE_QUANTITY_INVALID` com regra OFF-18 [OFF-18]
- **OLC-22** — IF o montante mínimo está ausente, não é inteiro, é menor que 1 ou é maior que a quantidade base THEN the system SHALL registrar a violação `MINIMUM_AMOUNT_INVALID` com regra OFF-19 [OFF-19]
- **OLC-23** — WHEN o montante mínimo é igual à quantidade base e o conjunto de opções está vazio THEN the system SHALL publicar a oferta com `partialDistribution = false` e conjunto de opções vazio [OFF-20]
- **OLC-24** — IF o investimento mínimo por investidor não é inteiro, é menor que 1 ou é maior que o máximo THEN the system SHALL registrar a violação `MIN_INVESTMENT_INVALID` com regra OFF-21 [OFF-21]
- **OLC-25** — IF o investimento máximo por investidor não é inteiro ou é maior que a quantidade base THEN the system SHALL registrar a violação `MAX_INVESTMENT_INVALID` com regra OFF-22 [OFF-22]
- **OLC-26** — IF o período de reserva não tem início ou fim, ou o fim não é posterior ao início THEN the system SHALL registrar a violação `RESERVATION_PERIOD_INVALID` com regra OFF-23 [OFF-23]
- **OLC-27** — IF o instante da publicação é posterior ao fim do período de reserva THEN the system SHALL registrar a violação `RESERVATION_PERIOD_ENDED` com regra OFF-24 [OFF-24]
- **OLC-28** — IF o montante mínimo é menor que a quantidade base e o conjunto de opções não contém as opções 1 e 2 THEN the system SHALL registrar a violação `CONDITIONING_OPTIONS_INVALID` com regra OFF-25 [OFF-25]
- **OLC-29** — WHEN uma oferta com distribuição parcial é publicada THEN the system SHALL expor `acceptedConditioningOptions` exatamente como informado, com a opção 3 presente só quando informada [OFF-25]

### Domain events

- **OLC-30** — WHEN a oferta passa a `Open` THEN the system SHALL publicar `OfferPublished` com identificador da oferta, definição completa, estado `Open` e instante [OFF-03]
- **OLC-31** — WHEN a oferta passa a `Closed` THEN the system SHALL publicar `OfferClosed` com identificador da oferta, estado `Closed` e instante [OFF-07]
- **OLC-32** — WHEN a oferta passa a `Revoked` THEN the system SHALL publicar `OfferRevoked` com identificador da oferta, estado anterior, estado `Revoked` e instante [OFF-12]
- **OLC-33** — WHEN a oferta passa a `Unconditional`, `Lapsed` ou `Completed` THEN the system SHALL não publicar evento, porque nenhum contexto os consome na v1 [OFF-09]

### Consistência, auditoria e consulta

- **OLC-34** — WHEN uma publicação ou transição falha em qualquer ponto THEN the system SHALL deixar estado, definição e eventos pendentes exatamente como antes da operação [OFF-NFR-01]
- **OLC-35** — WHEN uma transição é aplicada THEN the system SHALL registrar quem ou qual contexto a disparou e o instante, consultável por oferta em ordem cronológica [OFF-NFR-02]
- **OLC-36** — The system SHALL armazenar e devolver o preço por cota como decimal exato, de modo que o valor consultado seja igual ao publicado em todas as casas [OFF-NFR-04]
- **OLC-37** — IF duas transições concorrentes chegam para a mesma oferta THEN the system SHALL aplicar exatamente uma delas e rejeitar a outra com `INVALID_TRANSITION` avaliada contra o estado resultante [OFF-06]
- **OLC-38** — WHEN um contexto consulta uma oferta pelo identificador THEN the system SHALL responder com definição publicada, estado corrente e `acceptingReservations`, ou `OFFER_NOT_FOUND` quando a oferta é `Draft` ou não existe [OFF-14]
- **OLC-39** — WHEN o operador consulta uma oferta `Draft` pelo identificador THEN the system SHALL responder com os atributos informados até então e o estado `Draft` [OFF-02]
- **OLC-40** — WHEN uma transição é aplicada ou um desfecho é descartado THEN the system SHALL registrar no trace corrente as tags `app.offer.id` e `app.offer.status`, sem dado pessoal [OFF-NFR-02]

## Dimensões Implícitas (Implicit Dimensions)

| Dimensão | Requisito ou N/A porque |
|---|---|
| Validação de entrada e limites | OLC-17 a OLC-28 |
| Falha e falha parcial | OLC-34 |
| Idempotência, retry, duplicata | N/A porque `BookProcessed` reentregue encontra a oferta fora de `Closed` e é descartado por OLC-13; segunda tentativa de uma transição já aplicada cai em OLC-07 |
| Autorização e rate limit | N/A porque o MVP não modela identidade do operador (Premissas); origem da ação registrada por OLC-35 |
| Concorrência e ordenação | OLC-37 |
| Ciclo de vida dos dados | N/A porque nenhuma retenção regulatória é modelada (Não-objetivos do PRD 0001: documentos e registro na CVM fora); Draft descartado segue OLC-03 |
| Observabilidade | OLC-40, sobre a instrumentação automática do `ServiceDefaults` |
| Falha de dependência externa | N/A porque a capability não chama serviço externo; `BookProcessed` é consumido de forma assíncrona e tratado por OLC-11 a OLC-13 |
| Integridade de transição de estado | OLC-07, OLC-37 |
| Consistência entre contextos | OLC-30 a OLC-33; a propriedade "definição e estado iguais para todos os consumidores" (OFF-NFR-03) é critério do Design e da ADR de transporte |

## Critérios de Sucesso (Success Criteria)

- [ ] Toda combinação inválida de OFF-15 a OFF-25 é rejeitada com a lista completa de violações: um caso por regra e um combinando duas (métrica leading do PRD 0001).
- [ ] Toda transição fora do diagrama é rejeitada e todo desfecho fora de `Closed` é descartado e registrado.
- [ ] Nenhuma alteração de atributo é aceita após a publicação; a definição consultada é idêntica à publicada, inclusive o preço com 8 casas.
- [ ] Guardrails: Draft continua aceitando estado incompleto; nenhum consumidor mantém estado de oferta próprio (verificável nas specs das outras capabilities).

## Rastreabilidade (Requirement Traceability)

PRD → EARS. Cada FR do PRD em escopo aparece; `—` marca requisito sem origem no PRD.

| ID do PRD | IDs EARS |
|---|---|
| OFF-01 | OLC-01 |
| OFF-02 | OLC-02, OLC-03, OLC-39 |
| OFF-03 | OLC-04, OLC-30 |
| OFF-04 | OLC-05 |
| OFF-05 | OLC-06 |
| OFF-06 | OLC-07, OLC-37 |
| OFF-07 | OLC-08, OLC-09, OLC-31 |
| OFF-08 | OLC-10 |
| OFF-09 | OLC-11, OLC-33 |
| OFF-10 | OLC-12 |
| OFF-11 | OLC-13 |
| OFF-12 | OLC-14, OLC-32 |
| OFF-13 | OLC-15 |
| OFF-14 | OLC-16, OLC-38 |
| OFF-15 | OLC-17 |
| OFF-16 | OLC-18, OLC-19 |
| OFF-17 | OLC-20 |
| OFF-18 | OLC-21 |
| OFF-19 | OLC-22 |
| OFF-20 | OLC-23 (conjunto vazio); conjunto informado aguarda o PRD (Perguntas em aberto) |
| OFF-21 | OLC-24 |
| OFF-22 | OLC-25 |
| OFF-23 | OLC-26 |
| OFF-24 | OLC-27 |
| OFF-25 | OLC-28, OLC-29 |
| OFF-26, OFF-27, OFF-28 | Fora desta capability: aplicados em `allocation/book-processing` |
| OFF-29 | Fora desta capability: verificado em `reservation-book/reservation-lifecycle` (BOOK-08) |
| OFF-NFR-01 | OLC-34 |
| OFF-NFR-02 | OLC-35, OLC-40, OLC-13 (desfecho descartado) |
| OFF-NFR-03 | Critério de design: ADR de transporte (PRD 0000, Decisões delegadas a ADR) |
| OFF-NFR-04 | OLC-36 |

Cenários herdados dos Critérios de Aceitação do PRD 0001, pelo FR que exercitam:

| Cenário do PRD | IDs EARS |
|---|---|
| Publicação válida com opções {1, 2, 3}; segundo Draft com o mesmo nome também publicado (OFF-03, OFF-15) | OLC-04, OLC-17, OLC-30 |
| Draft sem emissão, mínimo 500 e máximo 10, montante mínimo maior que a base: três violações (OFF-04) | OLC-05, OLC-18, OLC-22, OLC-24 |
| Período começou ontem e termina amanhã: aceito; terminou ontem: OFF-24 | OLC-04, OLC-27 |
| Preço 96,53420001 consultado com exatamente esse valor (OFF-17) | OLC-20, OLC-36 |
| Alteração de atributo fora de Draft rejeitada; definição idêntica (OFF-05) | OLC-06 |
| Draft não aparece para outro contexto (OFF-14) | OLC-16, OLC-38 |
| Fechada com demanda efetiva 500 e mínimo 600 → Não formada; 700 e alocação concluída → Formada (OFF-09, OFF-10) | OLC-11, OLC-12 |
| Desfecho em Revogada: permanece e registrado como descartado (OFF-11) | OLC-13 |
| Formada: revogar → Revogada; encerrar → Encerrada (OFF-12, OFF-13) | OLC-14, OLC-15, OLC-32 |
| Terminais e Draft rejeitam transições (OFF-06) | OLC-07 |
| Mínimo igual à base com conjunto vazio: aceita, sem distribuição parcial (OFF-20) | OLC-23 |
| Mínimo menor que a base com conjunto vazio ou {1, 3}: rejeitado; {1, 2}: aceito (OFF-25) | OLC-28, OLC-29 |
| Opção 3 recebe ⌊15 × 700 / 1000⌋ = 10 (OFF-28) | Fora desta capability: `allocation/book-processing` |

Status por requisito EARS (Pending → In Design → In Tasks → Implementing → Verified):

| ID | História | Status |
|---|---|---|
| OLC-01 | P1 Publicar | Pending |
| OLC-02 | P1 Publicar | Pending |
| OLC-03 | P1 Publicar | Pending |
| OLC-04 | P1 Publicar | Pending |
| OLC-05 | P1 Publicar | Pending |
| OLC-06 | P1 Publicar | Pending |
| OLC-07 | P1 Máquina de estados | Pending |
| OLC-08 | P1 Máquina de estados | Pending |
| OLC-09 | P1 Máquina de estados | Pending |
| OLC-10 | P2 Consulta | Pending |
| OLC-11 | P1 Máquina de estados | Pending |
| OLC-12 | P1 Máquina de estados | Pending |
| OLC-13 | P1 Máquina de estados | Pending |
| OLC-14 | P1 Máquina de estados | Pending |
| OLC-15 | P1 Máquina de estados | Pending |
| OLC-16 | P2 Consulta | Pending |
| OLC-17 | P1 Publicar | Pending |
| OLC-18 | P1 Publicar | Pending |
| OLC-19 | P1 Publicar | Pending |
| OLC-20 | P1 Publicar | Pending |
| OLC-21 | P1 Publicar | Pending |
| OLC-22 | P1 Publicar | Pending |
| OLC-23 | P1 Publicar | Pending |
| OLC-24 | P1 Publicar | Pending |
| OLC-25 | P1 Publicar | Pending |
| OLC-26 | P1 Publicar | Pending |
| OLC-27 | P1 Publicar | Pending |
| OLC-28 | P1 Publicar | Pending |
| OLC-29 | P1 Publicar | Pending |
| OLC-30 | P1 Publicar | Pending |
| OLC-31 | P1 Máquina de estados | Pending |
| OLC-32 | P1 Máquina de estados | Pending |
| OLC-33 | P1 Máquina de estados | Pending |
| OLC-34 | P1 Máquina de estados | Pending |
| OLC-35 | P1 Máquina de estados | Pending |
| OLC-36 | P1 Publicar | Pending |
| OLC-37 | P1 Máquina de estados | Pending |
| OLC-38 | P2 Consulta | Pending |
| OLC-39 | P1 Publicar | Pending |
| OLC-40 | P1 Máquina de estados | Pending |

## Ponto de Maior Fragilidade (Weakest Point)

A decisão de **tratar a segunda transição concorrente como `INVALID_TRANSITION` avaliada contra o estado resultante (OLC-37)**, em vez de um erro próprio de conflito.

*Vetor de ataque:* o operador que pediu "fechar" um milissegundo depois de outro pedido válido recebe "transição inválida de `Closed` para `Closed`", que descreve o estado final e não o que aconteceu; a auditoria (OLC-35) registra uma rejeição por regra de negócio onde houve corrida. Se um consumidor automatizar retry por código de erro, `INVALID_TRANSITION` o fará desistir de operações que deveriam ser reavaliadas.

*Desafie antes de aprovar:* um código distinto (`CONCURRENT_MODIFICATION`, 409 com estado corrente) custa um ramo a mais no tratamento de erro e separa "regra violada" de "chegou tarde". Se o operador é humano e único no MVP, a corrida é rara e o código único basta; se qualquer automação disparar transições, o código distinto entra antes de Execute.
