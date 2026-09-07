<!-- sdd: spec-delta | tier: complex | capability: allocation/book-processing | prd: /docs/prd/0003-allocation-book-processing.md | prd-rev: git:3ee73451033828d374b354840630c3b90ab0026e -->
# Processamento do Livro e Alocação

| | |
|---|---|
| **Status** | Rascunho |
| **Autor** | Guilherme Salvi |
| **Data** | 2026-09-06 |
| **Capability** | allocation/book-processing |
| **Prefixo** | PROC |
| **Confiança** | Média — PRD de origem em Rascunho |

## Contexto (Context)

Origem: [PRD 0003](../../../../prd/0003-allocation-book-processing.md), tier `complexa`, Status Rascunho em 2026-09-06; o usuário autorizou nesta sessão abrir a spec sobre o rascunho. Mapa de contextos e catálogo de eventos: [PRD 0000](../../../../prd/0000-platform-overview.md). A capability consome `OfferPublished`, `OfferClosed` e `OfferRevoked`, lê o livro fechado do ReservationBook (BOOK-16) e produz `BookProcessed`, consumido por Offering e ReservationBook. Notação do PRD: `B` quantidade base, `M` montante mínimo, `D` demanda total, `Dn` demanda das não vinculadas, `D'` demanda efetiva, `E` cotas efetivamente distribuídas, `q` quantidade reservada, `R` quantidade rateada, `Dr` demanda rateada.

Base lida: `src/Allocation` contém só a composição do serviço; testes são o esqueleto do xUnit. Convenções respeitadas: `.claude/rules/program-composition.md` e `.claude/rules/tracing.md` (o processamento é a única operação com span manual, ALLOC-NFR-04). Capability nova: delta todo ADDED. Identificadores dos motivos foram acrescentados ao PRD 0003 durante esta spec (sem commit; Data do PRD 2026-09-04, editado em 2026-09-06).

## Escopo e Fora de Escopo (Scope / Out of Scope)

**Em escopo:** gatilho e entrada do processamento, consolidação e vedação a vinculadas, formação, distribuição parcial, colocação integral, excesso de demanda com rateio e resto, colocação limitada, resultado e emissão única de `BookProcessed`.

| Fora de escopo | Razão |
|---|---|
| Outros critérios de rateio, lote adicional, sobras, alocação discricionária, revisão pelo operador | Não-objetivos do PRD 0003 |
| Aplicação do resultado às reservas e ao estado da oferta | Capabilities consumidoras (BOOK-17, OFF-09 a OFF-11) |
| Forma da leitura do livro fechado | Decisão delegada a ADR pelo PRD 0000, exigência BOOK-NFR-02; entra no Design |

## Premissas e Perguntas em Aberto (Assumptions & Open Questions)

| Premissa / decisão | Default escolhido | Racional | Confirmada? |
|---|---|---|---|
| [PREMISSA] Aritmética | Inteiros de 64 bits para quantidades; produto `q × R` calculado antes da divisão inteira; parte fracionária comparada como par (resto, `Dr`) sem ponto flutuante | ALLOC-NFR-01 proíbe ponto flutuante; `q × R` cabe em 64 bits para as quantidades do domínio | não |
| [PREMISSA] Processamento sem emitir | Falha antes da emissão deixa nenhum estado persistido além do registro da tentativa; a repetição é disparada pelo operador ou por retry do consumidor | ALLOC-02 admite repetição; ALLOC-NFR-02 exige tudo ou nada | não |
| [PREMISSA] Identificador do evento | `BookProcessed` carrega identificador único derivado da oferta, porque só existe um por oferta | ALLOC-02; permite dedup nos consumidores | não |
| [PREMISSA] Revogação durante o processamento | Verificada no início e imediatamente antes da emissão; entre os dois pontos o processamento é puro e sem efeito externo | ALLOC-03 e ALLOC-NFR-02: interromper sem emitir | não |

**Premissas críticas:**
- [PREMISSA-CRÍTICA] O livro fechado lido de BOOK-16 é idêntico ao congelado e não muda entre leituras (BOOK-NFR-02). Se falsa, ALLOC-04 (determinismo) não se sustenta e a repetição após falha pode produzir resultado diferente. Validar com a ADR de leitura do livro antes de Execute.

**Perguntas em aberto:**
- Leitura do livro fechado e transporte de `BookProcessed`. Dono: Design/ADR, conforme PRD 0000, Decisões delegadas a ADR. Fora do caminho da spec.
- Aprovação do PRD 0003. Dono: usuário. Bloqueia Design.

## Histórias (User Stories)

### P1: Processar o livro e emitir o desfecho ⭐ MVP
**Como** operador da corretora, **quero** que o fechamento produza um desfecho correto, explicável e reprodutível **para** que cada reserva saiba o que recebeu sem intervenção manual.
**Por que P1:** é a capability núcleo; tudo o mais a alimenta.
**Teste independente:** cada linha da tabela de Critérios de Aceitação do PRD 0003 reproduzida com igualdade exata.

### P2: Proteger a unicidade e a interrupção
**Como** consumidor do desfecho, **quero** que exista no máximo um `BookProcessed` por oferta e nenhum após revogação **para** aplicar o resultado sem reconciliação.
**Por que P2:** invariantes de borda, demonstráveis sem a aritmética.
**Teste independente:** segundo processamento rejeitado; revogação em curso interrompe sem emitir; repetição após falha emite o mesmo resultado.

## ADDED Requirements

### Gatilho e entrada

- **PROC-01** — WHEN `OfferClosed` é recebido THEN the system SHALL iniciar o processamento tendo como entrada exclusiva a definição publicada da oferta e o livro fechado lido do ReservationBook [ALLOC-01]
- **PROC-02** — IF um processamento é solicitado para oferta que já emitiu `BookProcessed` THEN the system SHALL rejeitar com `BOOK_ALREADY_PROCESSED` sem emitir [ALLOC-02]
- **PROC-03** — WHEN um processamento terminou sem emitir e é repetido THEN the system SHALL produzir e emitir o mesmo resultado que o original produziria [ALLOC-02]
- **PROC-04** — IF `OfferRevoked` é recebido antes da emissão THEN the system SHALL interromper o processamento sem emitir nem persistir resultado [ALLOC-03]
- **PROC-05** — IF `OfferRevoked` é recebido depois da emissão THEN the system SHALL manter o resultado emitido inalterado [ALLOC-03]
- **PROC-06** — The system SHALL produzir, para a mesma definição e o mesmo livro fechado, resultado idêntico em toda execução [ALLOC-04]

### Consolidação e vedação

- **PROC-07** — WHEN o processamento inicia THEN the system SHALL calcular `D` como a soma de `q` de todas as reservas e `Dn` como a soma de `q` das reservas com `IsRelatedParty = false` [ALLOC-05]
- **PROC-08** — IF `3 × D > 4 × B` e `Dn ≥ B` THEN the system SHALL excluir cada reserva com `IsRelatedParty = true`, com quantidade alocada 0 e motivo `ExcludedRelatedParty` [ALLOC-06]
- **PROC-09** — IF `3 × D > 4 × B` e `Dn < B` THEN the system SHALL não excluir reserva alguma e seguir em colocação limitada [ALLOC-07]
- **PROC-10** — WHEN a vedação é avaliada THEN the system SHALL calcular `D'` como a soma de `q` das reservas não excluídas [ALLOC-08]

### Formação

- **PROC-11** — IF `D' < M` THEN the system SHALL registrar desfecho `Lapsed` e atribuir a cada reserva não excluída quantidade alocada 0 com motivo `OfferLapsed` [ALLOC-09]
- **PROC-12** — IF `D' ≥ M` THEN the system SHALL registrar desfecho formada e calcular `E = min(D', B)` uma única vez, sem recálculo após o condicionamento [ALLOC-10]

### Distribuição parcial, colocação integral e excesso

- **PROC-13** — WHILE `M ≤ D' < B`, the system SHALL atribuir a cada reserva com opção 1 quantidade alocada 0 e motivo `CancelledByCondition` [ALLOC-11]
- **PROC-14** — WHILE `M ≤ D' < B`, the system SHALL atribuir a cada reserva com opção 2 quantidade alocada `q` e motivo `Filled` [ALLOC-12]
- **PROC-15** — WHILE `M ≤ D' < B`, the system SHALL atribuir a cada reserva com opção 3 quantidade alocada `⌊q × E / B⌋` e motivo `PartiallyFilledByCondition`, aceitando zero [ALLOC-13]
- **PROC-16** — WHILE `M = B`, the system SHALL classificar todo livro com `D' < B` como `D' < M`, nunca entrando em distribuição parcial [ALLOC-14]
- **PROC-17** — WHILE `D' = B`, the system SHALL atribuir a cada reserva não excluída quantidade alocada `q` e motivo `Filled`, ignorando a opção [ALLOC-15]
- **PROC-18** — WHILE `D' > B`, the system SHALL atribuir a cada reserva do conjunto rateado `⌊q × R / Dr⌋` com motivo `ScaledBack`, sendo no caso geral o conjunto rateado as reservas não excluídas, `R = B` e `Dr = D'` [ALLOC-16]
- **PROC-19** — WHEN o rateio é calculado THEN the system SHALL distribuir o resto `R − Σ⌊q × R / Dr⌋` uma cota por reserva do conjunto rateado, em ordem decrescente da parte fracionária de `q × R / Dr`, desempatando pela ordem de registro mais antiga [ALLOC-17]
- **PROC-20** — IF a distribuição do resto alcançaria `q` em uma reserva THEN the system SHALL não ultrapassar `q` e passar a cota à próxima reserva na ordem [ALLOC-18]
- **PROC-21** — WHILE `D' > B`, the system SHALL produzir soma das quantidades alocadas igual a `B` [ALLOC-19]
- **PROC-22** — WHILE `D' > B`, the system SHALL ignorar a opção de condicionamento de toda reserva [ALLOC-20]
- **PROC-23** — WHILE em colocação limitada, the system SHALL atribuir a cada reserva não vinculada `q` com motivo `Filled` e ratear entre as vinculadas com `R = B − Dn` e `Dr` igual à soma de `q` das vinculadas, aplicando PROC-18 a PROC-20 a esse conjunto [ALLOC-21]

### Resultado

- **PROC-24** — The system SHALL produzir toda quantidade alocada como inteiro maior ou igual a zero [ALLOC-22]
- **PROC-25** — The system SHALL produzir, em qualquer ramo, soma das quantidades alocadas menor ou igual a `B` [ALLOC-23]
- **PROC-26** — The system SHALL aplicar rateio e proporcional sem impor investimento mínimo por reserva nem máximo por posição, aceitando alocação abaixo do mínimo e zero [ALLOC-24]
- **PROC-27** — WHEN o resultado é produzido THEN the system SHALL carregar, por reserva, identificador, quantidade alocada e exatamente um motivo entre `Filled`, `PartiallyFilledByCondition`, `ScaledBack`, `CancelledByCondition`, `ExcludedRelatedParty`, `OfferLapsed` [ALLOC-25]
- **PROC-28** — WHEN o processamento conclui THEN the system SHALL emitir uma única vez `BookProcessed` com identificador da oferta, desfecho, `D`, `Dn`, `D'`, `E`, ramo aplicado (inclusive colocação limitada), lista de resultados por reserva e instante [ALLOC-26]
- **PROC-29** — WHEN o desfecho é `Lapsed` THEN the system SHALL emitir `BookProcessed` sem `E` e com a lista de resultados por reserva, vazia quando o livro não tem reservas [ALLOC-26]

### Consistência, explicabilidade e observabilidade

- **PROC-30** — The system SHALL calcular sem ponto flutuante, com truncamento para baixo em toda divisão [ALLOC-NFR-01]
- **PROC-31** — WHEN o processamento falha em qualquer ponto antes da emissão THEN the system SHALL deixar nenhum resultado persistido nem evento emitido [ALLOC-NFR-02]
- **PROC-32** — WHEN `BookProcessed` é consultado THEN the system SHALL permitir recalcular manualmente cada quantidade alocada a partir de motivo, `D`, `Dn`, `D'`, `E` e ramo [ALLOC-NFR-03]
- **PROC-33** — WHEN o processamento executa THEN the system SHALL abri-lo em um span manual `Allocation.ProcessBook` via `TraceAsync`, com tags `app.offer.id` e `app.allocation.branch`, sem dado de investidor [ALLOC-NFR-04]

## Dimensões Implícitas (Implicit Dimensions)

| Dimensão | Requisito ou N/A porque |
|---|---|
| Validação de entrada e limites | N/A porque a entrada é a definição publicada (validada por OFF-03) e o livro fechado (validado por BOOK-01 a BOOK-09); PROC-24 e PROC-25 são invariantes de saída |
| Falha e falha parcial | PROC-31 |
| Idempotência, retry, duplicata | PROC-02, PROC-03; `OfferClosed` reentregue após emissão cai em PROC-02 |
| Autorização e rate limit | N/A porque o processamento é disparado por evento, não por usuário |
| Concorrência e ordenação | PROC-02 cobre dois processamentos concorrentes: apenas um emite; ordem de registro é o desempate (PROC-19) |
| Ciclo de vida dos dados | N/A porque o resultado emitido é permanente (PROC-05) e não há retenção regulatória modelada |
| Observabilidade | PROC-33 |
| Falha de dependência externa | Leitura do livro fechado indisponível → processamento não inicia e pode ser repetido (PROC-03); a garantia de identidade é critério do Design (BOOK-NFR-02) |
| Integridade de transição de estado | PROC-02, PROC-04, PROC-05 |
| Consistência entre contextos | PROC-28, PROC-29; transporte é critério do Design (OFF-NFR-03) |

## Critérios de Sucesso (Success Criteria)

- [ ] Toda linha dos Critérios de Aceitação do PRD 0003 reproduzida por teste com igualdade exata.
- [ ] Em livros gerados aleatoriamente, processar duas vezes dá resultado idêntico e PROC-20, PROC-21, PROC-24 e PROC-25 nunca são violados; em colocação limitada toda não vinculada recebe `q`.
- [ ] Guardrails: nenhuma reserva recebe mais do que reservou; nenhuma quantidade fracionária; a capability não altera livro fechado nem definição da oferta.

## Rastreabilidade (Requirement Traceability)

| ID do PRD | IDs EARS |
|---|---|
| ALLOC-01 | PROC-01 |
| ALLOC-02 | PROC-02, PROC-03 |
| ALLOC-03 | PROC-04, PROC-05 |
| ALLOC-04 | PROC-06 |
| ALLOC-05 | PROC-07 |
| ALLOC-06 | PROC-08 |
| ALLOC-07 | PROC-09 |
| ALLOC-08 | PROC-10 |
| ALLOC-09 | PROC-11 |
| ALLOC-10 | PROC-12 |
| ALLOC-11 | PROC-13 |
| ALLOC-12 | PROC-14 |
| ALLOC-13 | PROC-15 |
| ALLOC-14 | PROC-16 |
| ALLOC-15 | PROC-17 |
| ALLOC-16 | PROC-18 |
| ALLOC-17 | PROC-19 |
| ALLOC-18 | PROC-20 |
| ALLOC-19 | PROC-21 |
| ALLOC-20 | PROC-22 |
| ALLOC-21 | PROC-23 |
| ALLOC-22 | PROC-24 |
| ALLOC-23 | PROC-25 |
| ALLOC-24 | PROC-26 |
| ALLOC-25 | PROC-27 |
| ALLOC-26 | PROC-28, PROC-29 |
| ALLOC-NFR-01 | PROC-30 |
| ALLOC-NFR-02 | PROC-31 |
| ALLOC-NFR-03 | PROC-32 |
| ALLOC-NFR-04 | PROC-33 |
| OFF-26, OFF-27, OFF-28 | Semântica aplicada por PROC-13 a PROC-15 |

Cenários herdados dos Critérios de Aceitação do PRD 0003, pelo nome do caso:

| Cenário do PRD | IDs EARS |
|---|---|
| Parcial com proporcional | PROC-12, PROC-14, PROC-15 |
| Parcial com colocação total | PROC-12, PROC-13, PROC-14 |
| Proporcional truncado a zero | PROC-15, PROC-24 |
| Duas reservas do mesmo investidor | PROC-13, PROC-14, PROC-27 |
| Não formada | PROC-11 |
| Não formada sem distribuição parcial | PROC-11, PROC-16 |
| Livro vazio | PROC-11, PROC-29 |
| Exclusão de vinculadas e rateio | PROC-08, PROC-18, PROC-19, PROC-21 |
| Colocação limitada | PROC-09, PROC-23 |
| Colocação limitada com resto | PROC-09, PROC-19, PROC-23 |
| Colocação integral | PROC-17, PROC-22 |
| Rateio sem resto | PROC-18, PROC-21 |
| Rateio com resto | PROC-18, PROC-19 |
| Empate na fração | PROC-19 |
| Empate no instante de registro | PROC-19 |
| Revogação em curso: nada emitido (ALLOC-03, Dado/Quando/Então) | PROC-04 |
| Novo processamento após emissão rejeitado (ALLOC-02, Dado/Quando/Então) | PROC-02 |
| Repetição após falha emite o mesmo resultado (ALLOC-02, ALLOC-04, Dado/Quando/Então) | PROC-03, PROC-06 |

Status por requisito EARS (Pending → In Design → In Tasks → Implementing → Verified):

| ID | História | Status |
|---|---|---|
| PROC-01 | P1 Processar | Pending |
| PROC-02 | P2 Unicidade | Pending |
| PROC-03 | P2 Unicidade | Pending |
| PROC-04 | P2 Unicidade | Pending |
| PROC-05 | P2 Unicidade | Pending |
| PROC-06 | P1 Processar | Pending |
| PROC-07 | P1 Processar | Pending |
| PROC-08 | P1 Processar | Pending |
| PROC-09 | P1 Processar | Pending |
| PROC-10 | P1 Processar | Pending |
| PROC-11 | P1 Processar | Pending |
| PROC-12 | P1 Processar | Pending |
| PROC-13 | P1 Processar | Pending |
| PROC-14 | P1 Processar | Pending |
| PROC-15 | P1 Processar | Pending |
| PROC-16 | P1 Processar | Pending |
| PROC-17 | P1 Processar | Pending |
| PROC-18 | P1 Processar | Pending |
| PROC-19 | P1 Processar | Pending |
| PROC-20 | P1 Processar | Pending |
| PROC-21 | P1 Processar | Pending |
| PROC-22 | P1 Processar | Pending |
| PROC-23 | P1 Processar | Pending |
| PROC-24 | P1 Processar | Pending |
| PROC-25 | P1 Processar | Pending |
| PROC-26 | P1 Processar | Pending |
| PROC-27 | P1 Processar | Pending |
| PROC-28 | P1 Processar | Pending |
| PROC-29 | P1 Processar | Pending |
| PROC-30 | P1 Processar | Pending |
| PROC-31 | P2 Unicidade | Pending |
| PROC-32 | P1 Processar | Pending |
| PROC-33 | P1 Processar | Pending |

## Ponto de Maior Fragilidade (Weakest Point)

A decisão de **verificar a revogação só no início e imediatamente antes da emissão (PROC-04, Premissas)**, tratando o processamento como função pura entre esses dois pontos.

*Vetor de ataque:* `OfferRevoked` que chega entre a verificação final e a emissão produz um `BookProcessed` sobre oferta revogada. O modelo tolera isso porque OFF-11 descarta o desfecho e BOOK-18 torna as reservas sem efeito, mas o resultado emitido continua existindo e explicável (PROC-32) para uma oferta que não existe mais; auditoria e consumidores precisam saber que "emitido" não implica "aplicado".

*Desafie antes de aprovar:* a emissão deve ser condicionada ao estado da oferta na mesma transação (exige transporte com leitura consistente, ADR pendente) ou a janela residual é aceita porque os consumidores já a tratam? Aceitar é mais simples e é o que o PRD 0000 descreve; condicionar muda a natureza da ADR de transporte.
