# Processamento do Livro

| | |
| --- | --- |
| **Requirement Prefix** | `ALLOC` |
| **Affected Capabilities** | [Ciclo de Vida da Oferta](../offer-lifecycle/spec.md), [Livro de Reservas](../bid-book/spec.md) |

## Context

O processamento do livro determina o desfecho da oferta e a quantidade e o motivo do resultado de cada reserva. O fechamento do livro dispara um cálculo determinístico que consolida a demanda, aplica a vedação a pessoas vinculadas, apura a formação e calcula a alocação. O mesmo livro fechado precisa produzir o mesmo resultado, com no máximo um desfecho emitido por oferta.

O operador da corretora fecha o livro e precisa de um desfecho correto, explicável reserva a reserva e reprodutível, sem intervenção manual. O investidor, indiretamente pelo [Livro de Reservas](../bid-book/spec.md), quer saber quantas cotas recebeu e por quê. O [Ciclo de Vida da Oferta](../offer-lifecycle/spec.md) consome o desfecho e o assume como estado final da oferta.

As regras definem os casos de borda: demanda das não vinculadas abaixo da base, truncamento com resto e condicionamento que reduz a alocação depois da formação.

A entrada vem de duas capabilities: a definição publicada da oferta, do [Ciclo de Vida da Oferta](../offer-lifecycle/spec.md), e o livro fechado, do [Livro de Reservas](../bid-book/spec.md). O processamento acontece dentro do BookBuilding, com código em `src/BookBuilding`, e o resultado de cada reserva é aplicado pelo Livro de Reservas (BID-22).

O contrato consolida as decisões de produto do autor e a leitura das normas listadas em References.

## Scope

Entram o disparo pelo fechamento, a retentativa automática, a consolidação da demanda, a vedação a pessoas vinculadas, a apuração da formação, a alocação em cada ramo, o resultado por reserva, a emissão de `BookProcessed` e a interrupção pela revogação da oferta.

Ficam fora:

- outros critérios de rateio (igualitário e sucessivo, cronológico puro, prioridade por lote mínimo, exclusão de reservas pequenas) e critérios por tranche;
- garantia do investimento mínimo por investidor na alocação;
- lote adicional e suplementar, sobras de subscrição e direito de preferência, alocação discricionária e tranche institucional;
- as exceções do art. 56, § 1º, da CVM 160 para formadores de mercado e aplicação mínima obrigatória;
- efeito da categoria do investidor (art. 75), reprocessamento manual, aprovação ou ajuste pelo operador, liquidação, custódia e posição do cotista.

## Assumptions

- **Os identificadores em inglês do Glossary são propostas, exceto os desfechos e `ScaledBack`, justificados em Trade-offs.** Nenhum tipo de domínio em `src/BookBuilding` os fixa, e a convenção do projeto pede o identificador canônico antes de o nome entrar no código. Choice: os identificadores da tabela. If false: o identificador rejeitado muda sem custo de migração enquanto nenhum tipo o usar. Confirmed? y (Autor, 2026-09-30)

## Glossary

Oferta, quantidade base, montante mínimo e opções aceitas são definidos no [Ciclo de Vida da Oferta](../offer-lifecycle/spec.md). Investidor, reserva, quantidade reservada, opção declarada e ordem de registro são definidos no [Livro de Reservas](../bid-book/spec.md). Os símbolos entre parênteses são a notação dos requisitos e dos cenários.

| Term | Identifier | Definition |
| --- | --- | --- |
| Quantidade base (`B`) | `BaseQuantity` | Definida em OFF-08 |
| Montante mínimo (`M`) | `MinimumQuantity` | Definido em OFF-12 |
| Quantidade reservada (`q`) | `Quantity` | Cotas pedidas na reserva (BID-03) |
| Livro fechado | — | Reservas ativas no fechamento (BID-20, BID-21), uma linha por reserva |
| Situação do processamento | `ProcessingStatus` | `Pending`, `Completed` ou `Interrupted`; tabela em Requirements |
| Demanda total (`D`) | `TotalDemand` | Soma dos pedidos do livro fechado (ALLOC-08) |
| Demanda das não vinculadas (`Dn`) | `NonRelatedDemand` | Parcela da demanda sem declaração de vínculo (ALLOC-08); decide entre ALLOC-09 e ALLOC-10 |
| Demanda efetiva (`D'`) | `EffectiveDemand` | Demanda depois das exclusões (ALLOC-11); base da formação, do condicionamento e do rateio; em colocação limitada é igual a `D` |
| Excesso superior a um terço | — | `D > B × 4/3`; fronteira da vedação em ALLOC-09 e ALLOC-10 |
| Colocação limitada | `LimitedPlacement` | Exceção do art. 56, §§ 1º, III, e 3º (ALLOC-10), executada por ALLOC-23 |
| Formação | — | Apuração do desfecho (ALLOC-12, ALLOC-13) |
| Desfecho | `Outcome` | Formada ou não formada; identificadores na tabela de desfechos |
| Cotas efetivamente distribuídas (`E`) | `DistributedQuantity` | Quantidade apurada em ALLOC-13; numerador do proporcional de ALLOC-16, com denominador `B`; não é necessariamente a soma final alocada |
| Distribuição parcial | `PartialDistribution` | Ramo em que `M ≤ D' < B` (ALLOC-14 a ALLOC-16) |
| Excesso de demanda | — | `D' > B`; ramos de ALLOC-18 a ALLOC-23 |
| Opção de condicionamento | `ConditionOption` | Opção declarada na reserva (BID-08) entre as aceitas pela oferta (OFF-14); efeito e motivo em ALLOC-14 a ALLOC-16 |
| Rateio proporcional | — | Divisão definida em ALLOC-18 |
| Quantidade rateada (`R`) | `ScaleBackQuantity` | Cotas divididas pelo rateio (ALLOC-18, ALLOC-23) |
| Demanda rateada (`Dr`) | `ScaleBackDemand` | Soma de `q` do conjunto rateado (ALLOC-18, ALLOC-23) |
| Resto do arredondamento | `RoundingRemainder` | Diferença distribuída por ALLOC-19; espelho descritivo, sem termo específico de mercado nas fontes consultadas. Não designa sobras de subscrição (CVM 160, art. 65, § 2º, I) |
| Quantidade alocada | `AllocatedQuantity` | Cotas atribuídas à reserva, sujeitas a ALLOC-20 e ALLOC-24 |
| Resultado da reserva | `BidResult` | Quantidade alocada e motivo de uma reserva (ALLOC-27) |

## Requirements

O fechamento do livro (BID-18, BID-20) dispara o processamento dentro do BookBuilding. A situação do processamento acompanha as tentativas até a conclusão ou a interrupção.

```mermaid
stateDiagram-v2
    [*] --> Pending: fechamento do livro (ALLOC-01)
    Pending --> Pending: tentativa falha (ALLOC-03)
    Pending --> Completed: conclusão (ALLOC-30)
    Pending --> Interrupted: OfferRevoked (ALLOC-05)
```

| State | Identifier | Meaning |
| --- | --- | --- |
| Pendente | `Pending` | Livro fechado, sem desfecho registrado (ALLOC-01, ALLOC-03) |
| Concluído | `Completed` | Resultados aplicados e `BookProcessed` registrado (ALLOC-30) |
| Interrompido | `Interrupted` | `OfferRevoked` recebido antes da conclusão (ALLOC-05) |

```mermaid
flowchart TD
    startNode["Livro fechado"] -->|ALLOC-08| demandNode{"D > 4B/3?"}
    demandNode -->|"não: ALLOC-11"| effectiveNode["Demanda efetiva"]
    demandNode -->|"sim: ALLOC-09, ALLOC-10"| relatedNode{"Dn ≥ B?"}
    relatedNode -->|"sim: ALLOC-09"| excludeNode["Exclusão de vinculadas"]
    relatedNode -->|"não: ALLOC-10"| limitedNode["Colocação limitada"]
    excludeNode -->|ALLOC-11| effectiveNode
    limitedNode -->|ALLOC-11| effectiveNode
    effectiveNode -->|ALLOC-12, ALLOC-13| formationNode{"D' < M?"}
    formationNode -->|"sim: ALLOC-12"| lapseNode["Não formada"]
    formationNode -->|"não: ALLOC-13"| formedNode["Formação e apuração de E"]
    formedNode -->|ALLOC-14, ALLOC-17, ALLOC-18| branchNode{"D' versus B"}
    branchNode -->|"menor: ALLOC-14 a ALLOC-16"| partialNode["Condicionamento"]
    branchNode -->|"igual: ALLOC-17"| fullNode["Colocação integral"]
    branchNode -->|"maior: ALLOC-18, ALLOC-23"| limitCheck{"Ramo de ALLOC-10?"}
    limitCheck -->|"sim: ALLOC-23"| limitedAllocation["Atendimento integral das não vinculadas e rateio das vinculadas"]
    limitCheck -->|"não: ALLOC-18 a ALLOC-22"| scaleNode["Rateio geral"]
    lapseNode -->|ALLOC-28| resultNode["BookProcessed"]
    partialNode -->|ALLOC-28| resultNode
    fullNode -->|ALLOC-28| resultNode
    limitedAllocation -->|ALLOC-28| resultNode
    scaleNode -->|ALLOC-28| resultNode
```

### Gatilho, entrada e execução

- **ALLOC-01** — O fechamento do livro (BID-18, BID-20) cria o processamento da oferta em `Pending` na mesma operação atômica.
- **ALLOC-02** — A entrada exclusiva do processamento é a definição publicada da oferta, recebida em `OfferPublished`, e o livro fechado (BID-21).
- **ALLOC-03** — Enquanto o processamento está em `Pending`, uma tentativa que falha é repetida automaticamente, sem ação do operador, até a conclusão (ALLOC-30) ou a interrupção (ALLOC-05).
- **ALLOC-04** — Cada oferta produz no máximo um `BookProcessed`.
- **ALLOC-05** — Se o BookBuilding receber `OfferRevoked` com o processamento em `Pending`, o processamento passa a `Interrupted` na mesma operação atômica em que as reservas passam a `Void` (BID-23), e nenhum resultado é aplicado nem evento registrado.
- **ALLOC-06** — `OfferRevoked` recebido depois de `Completed` não altera o desfecho emitido.
- **ALLOC-07** — O processamento é determinístico: a mesma oferta e o mesmo livro fechado produzem exatamente o mesmo resultado, em qualquer tentativa.

### Consolidação e vedação

- **ALLOC-08** — `D` é a soma de `q` de todas as reservas do livro fechado; `Dn` é a soma de `q` das reservas sem declaração de vínculo.
- **ALLOC-09** — Se `D > B × 4/3` e `Dn ≥ B`, as reservas com declaração de vínculo são excluídas: quantidade alocada zero, motivo `ExcludedRelatedParty`.
- **ALLOC-10** — Se `D > B × 4/3` e `Dn < B`, nenhuma reserva é excluída, e o processamento segue em colocação limitada (ALLOC-23).
- **ALLOC-11** — `D'` é a soma de `q` das reservas não excluídas.

### Formação

- **ALLOC-12** — Se `D' < M`, a oferta não se forma: desfecho `Lapsed`, e toda reserva recebe zero com motivo `Void`.
- **ALLOC-13** — Se `D' ≥ M`, a oferta se forma (desfecho `Unconditional`) e `E = min(D', B)`. `E` é apurado uma vez e não é recalculado depois do condicionamento.

### Distribuição parcial (`M ≤ D' < B`)

Em oferta que não admite distribuição parcial (`M = B`, OFF-13), este ramo não ocorre, porque `D' < B` implica `D' < M`.

- **ALLOC-14** — Opção 1, condicionada à colocação total da quantidade base: a reserva não é atendida, recebe zero e motivo `CancelledByCondition`.
- **ALLOC-15** — Opção 2, condicionada ao montante mínimo com recebimento da totalidade: a reserva recebe `q`, motivo `Filled`.
- **ALLOC-16** — Opção 3, condicionada ao montante mínimo com recebimento proporcional: a reserva recebe `⌊q × E / B⌋`, truncado para baixo, motivo `PartiallyFilledByCondition`. Zero é resultado válido e mantém esse motivo.

### Colocação integral (`D' = B`)

- **ALLOC-17** — Cada reserva não excluída recebe `q`, motivo `Filled`; a opção de condicionamento é ignorada.

### Excesso de demanda (`D' > B`)

- **ALLOC-18** — Cada reserva do conjunto rateado recebe `⌊q × R / Dr⌋`, com `Dr` a soma de `q` do conjunto rateado. No caso geral o conjunto é o das reservas não excluídas, `R = B` e `Dr = D'`. O motivo é `ScaledBack`, mesmo quando ALLOC-19 leva a quantidade a `q`.
- **ALLOC-19** — O resto do arredondamento, `R` menos a soma de ALLOC-18, é distribuído uma cota por reserva do conjunto rateado, em ordem decrescente da parte fracionária de `q × R / Dr`. O empate é desfeito pela ordem de registro, mais antiga primeiro (BID-17).
- **ALLOC-20** — Nenhuma reserva recebe mais que `q`.
- **ALLOC-21** — Em excesso de demanda, a soma das quantidades alocadas é exatamente `B`.
- **ALLOC-22** — O condicionamento não se aplica em excesso de demanda; a opção declarada é ignorada.
- **ALLOC-23** — Em colocação limitada (ALLOC-10), cada reserva não vinculada recebe `q` com motivo `Filled`; o conjunto rateado é o das vinculadas, `R = B − Dn`, `Dr` é a soma de `q` das vinculadas, e ALLOC-18 a ALLOC-20 se aplicam a esse conjunto. ALLOC-21 vale para o total.

### Resultado

- **ALLOC-24** — Toda quantidade alocada é inteira e maior ou igual a zero.
- **ALLOC-25** — Em qualquer ramo, a soma das quantidades alocadas é menor ou igual a `B`.
- **ALLOC-26** — Investimento mínimo por reserva e máximo por posição valem no registro (BID-03, BID-04), não na alocação: rateio e proporcional podem alocar abaixo do mínimo, inclusive zero. O motivo é a regra aplicada, não a quantidade.
- **ALLOC-27** — O resultado por reserva carrega a quantidade alocada e um motivo da tabela de motivos.
- **ALLOC-28** — O `BookProcessed` identifica a oferta e o instante da conclusão e carrega o desfecho, `D`, `Dn`, `D'`, `E`, o ramo aplicado e a lista identificável de resultados por reserva (ALLOC-27). `E` só é apurado em ALLOC-13; na não formação é não aplicável.

| Outcome | Identifier | Meaning |
| --- | --- | --- |
| Formada | `Unconditional` | `D' ≥ M` (ALLOC-13) |
| Não formada | `Lapsed` | `D' < M` (ALLOC-12) |

| Reason | Identifier | Meaning |
| --- | --- | --- |
| Atendida integralmente | `Filled` | Recebe `q` (ALLOC-15, ALLOC-17, ALLOC-23) |
| Atendida parcialmente por proporcional | `PartiallyFilledByCondition` | Opção 3 em distribuição parcial (ALLOC-16) |
| Atendida parcialmente por rateio | `ScaledBack` | Integra o conjunto rateado (ALLOC-18, ALLOC-23) |
| Não atendida por condicionamento | `CancelledByCondition` | Opção 1 em distribuição parcial (ALLOC-14) |
| Excluída por vinculação | `ExcludedRelatedParty` | Vedação a pessoas vinculadas (ALLOC-09) |
| Oferta não formada | `Void` | Não formação (ALLOC-12) |

| Branch | Identifier | Meaning |
| --- | --- | --- |
| Não formação | `NonFormation` | ALLOC-12 |
| Distribuição parcial | `PartialDistribution` | ALLOC-14 a ALLOC-16 |
| Colocação integral | `FullPlacement` | ALLOC-17, inclusive depois da exclusão de ALLOC-09 |
| Rateio geral | `GeneralScaleBack` | ALLOC-18 a ALLOC-22, inclusive depois da exclusão de ALLOC-09 |
| Colocação limitada | `LimitedPlacement` | ALLOC-23 |

Os identificadores dos ramos e dos motivos compostos são nomes descritivos do modelo, sem enumeração equivalente nas fontes consultadas; `ScaledBack`, `Unconditional` e `Lapsed` usam termos de mercado justificados em Trade-offs.

### Integridade e rastreabilidade

- **ALLOC-29** — A aritmética é exata: nenhum valor intermediário é arredondado, e todo truncamento é para baixo.
- **ALLOC-30** — A conclusão é uma operação atômica: a aplicação dos resultados às reservas (BID-22), a passagem a `Completed` e o registro de `BookProcessed` ocorrem juntos, ou nenhum ocorre.
- **ALLOC-31** — O `BookProcessed` registrado é entregue ao Offering ao menos uma vez, inclusive depois de falha do BookBuilding ou do transporte.
- **ALLOC-32** — Cada quantidade alocada é recalculável pelas fórmulas do ramo informado, a partir do livro fechado (BID-21), da quantidade base e do montante mínimo da definição publicada e dos valores de ALLOC-28.
- **ALLOC-33** — O processamento, cada tentativa e o registro de `BookProcessed` levam o identificador da oferta aos rastros de execução; a tentativa que falha registra também a falha.

## Domain Events

| Event | Trigger | Content | Consumers |
| --- | --- | --- | --- |
| `BookProcessed` | Conclusão do processamento (ALLOC-30), no máximo uma vez por oferta (ALLOC-04) | O conteúdo de ALLOC-28 | [Ciclo de Vida da Oferta](../offer-lifecycle/spec.md), que assume o desfecho como estado da oferta (OFF-23 a OFF-25). A entrega é ao menos uma vez (ALLOC-31): o evento pode chegar repetido ou depois da revogação da oferta, e a oferta descarta os dois casos (OFF-25) |

O processamento consome `OfferPublished` (ALLOC-02) e `OfferRevoked` (ALLOC-05, ALLOC-06), definidos no [Ciclo de Vida da Oferta](../offer-lifecycle/spec.md).

## Acceptance Scenarios

`B = 1000` e `M = 600`, com reservas não vinculadas, salvo indicação. `V` marca reserva vinculada; a ordem de listagem é a ordem de registro; `(n)` é a opção de condicionamento, e a reserva sem `(n)` declara a opção 2, salvo em oferta que não admite distribuição parcial, em que não declara opção. A condição traz `D`, `Dn`, `D'` e `E`, nessa ordem, e o ramo emitido; o traço em `E` significa não aplicável (ALLOC-28). Valores entre parênteses aproximam `q × R / Dr` só para leitura; os cálculos são exatos.

| Scenario | Input | Condition | Requirements | Result |
| --- | --- | --- | --- | --- |
| Parcial com proporcional | A 500 (3), C 300 (2) | 800, 800, 800, 800; `PartialDistribution` | ALLOC-13, ALLOC-15, ALLOC-16 | A 400 = ⌊500 × 800 / 1000⌋ proporcional; C 300 integral; soma 700 |
| Parcial com colocação total | A 100 (1), C 550 (2) | 650, 650, 650, 650; `PartialDistribution` | ALLOC-13 a ALLOC-15 | A 0 por condicionamento; C 550; formada mesmo com soma 550 abaixo de `M` |
| Proporcional truncado a zero | A 1 (3), C 699 (2) | 700, 700, 700, 700; `PartialDistribution` | ALLOC-13, ALLOC-15, ALLOC-16 | A 0 = ⌊1 × 700 / 1000⌋, motivo proporcional; C 699 |
| Proporcional truncado acima de zero | A 15 (1), C 15 (2), F 15 (3), G 655 (2) | 700, 700, 700, 700; `PartialDistribution` | ALLOC-13 a ALLOC-16 | A 0 por condicionamento; C 15 integral; F 10 = ⌊15 × 700 / 1000⌋ proporcional; G 655 integral; soma 680 |
| Duas reservas do mesmo investidor | A1 300 (1) e A2 200 (2) do mesmo investidor; C 200 (2) | 700, 700, 700, 700; `PartialDistribution` | ALLOC-13 a ALLOC-15 | A1 0 por condicionamento; A2 200; C 200; resultado por reserva |
| Não formada | Reservas somando 500 | 500, 500, 500, —; `NonFormation` | ALLOC-12 | Desfecho `Lapsed`; todas 0, motivo `Void` |
| Não formada sem distribuição parcial | `M = B = 1000`; reservas somando 900 | 900, 900, 900, —; `NonFormation` | ALLOC-12 | Desfecho `Lapsed`; todas 0, motivo `Void` |
| Livro vazio | Livro sem reservas | 0, 0, 0, —; `NonFormation` | ALLOC-12 | Desfecho `Lapsed` sem resultados por reserva |
| Fronteira de um terço | `B = 999`; A 600, C 400, V 332 | 1332, 1000, 1332, 999; `GeneralScaleBack` | ALLOC-09, ALLOC-18 | `D = B × 4/3`, sem vedação; A 450, C 300, V 249 por rateio, sem resto; soma 999 |
| Exclusão com demanda não vinculada igual à base | A 600, C 400, V 400 | 1400, 1000, 1000, 1000; `FullPlacement` | ALLOC-09, ALLOC-17 | V 0 excluída, porque `Dn = B`; A 600 e C 400 integrais; soma 1000 |
| Exclusão de vinculadas e rateio | A 700, C 500, V 300 | 1500, 1200, 1200, 1000; `GeneralScaleBack` | ALLOC-09, ALLOC-18 a ALLOC-21 | V 0 excluída; A 583 (583,33), C 416 (416,67); resto 1 → C; A 583, C 417; soma 1000 |
| Colocação limitada | A 800, V 600 | 1400, 800, 1400, 1000; `LimitedPlacement` | ALLOC-10, ALLOC-23 | A 800 integral; V rateia 200 e recebe 200 por rateio; soma 1000 |
| Colocação limitada com resto | A 800, V1 400, V2 200 | 1400, 800, 1400, 1000; `LimitedPlacement` | ALLOC-10, ALLOC-23 | A 800; `R = 200`, `Dr = 600`: V1 133 (133,33), V2 66 (66,67); resto 1 → V2; V1 133, V2 67; soma 1000 |
| Colocação integral | A 600 (1), C 400 (3) | 1000, 1000, 1000, 1000; `FullPlacement` | ALLOC-17 | A 600 e C 400, ambas integrais; opções ignoradas |
| Rateio sem resto | A 1000 (1), C 1000 (3) | 2000, 2000, 2000, 1000; `GeneralScaleBack` | ALLOC-18 a ALLOC-22 | 500 e 500 por rateio, sem resto; opções ignoradas |
| Rateio com resto | A 1000, C 999 | 1999, 1999, 1999, 1000; `GeneralScaleBack` | ALLOC-18 a ALLOC-21 | A 500 (500,25), C 499 (499,75); resto 1 → C; 500 e 500 |
| Empate na fração | A 500, C 500; `B = 999` | 1000, 1000, 1000, 999; `GeneralScaleBack` | ALLOC-18 a ALLOC-21 | 499 (499,5) cada; frações iguais; resto 1 → A pela ordem de registro; A 500, C 499 |
| Empate no instante de registro | Idem, aceitas no mesmo instante, A anterior na ordem de registro | 1000, 1000, 1000, 999; `GeneralScaleBack` | ALLOC-18 a ALLOC-21 | A 500, C 499 |
| Revogação durante o processamento | `OfferRevoked` recebido | Processamento `Pending` | ALLOC-05 | `Interrupted` e reservas `Void` na mesma operação; nenhum `BookProcessed` registrado |
| Revogação após conclusão | `OfferRevoked` recebido | Processamento `Completed` | ALLOC-06 | Desfecho emitido inalterado |
| Falha no cálculo | Tentativa falha antes da conclusão | Processamento `Pending` | ALLOC-03, ALLOC-07, ALLOC-33 | Falha registrada; continua `Pending`; a nova tentativa automática registra o `BookProcessed` que a original produziria |
| Falha na conclusão | Falha durante a aplicação dos resultados | Processamento `Pending` | ALLOC-30 | Nenhuma reserva com resultado e nenhum `BookProcessed` registrado; continua `Pending` |
| Entrega após falha | BookBuilding falha logo depois da conclusão | `BookProcessed` registrado e ainda não entregue | ALLOC-31 | `BookProcessed` entregue ao Offering depois da recuperação |

## Observable Decisions

| Surface or dimension | Landing |
| --- | --- |
| Evento `BookProcessed` | ALLOC-28 e Domain Events |
| Consulta do resultado, do desfecho e da situação do processamento | Pelo [Livro de Reservas](../bid-book/spec.md) (BID-22, BID-26, BID-27) |
| Validation and limits | ALLOC-20 e ALLOC-24 a ALLOC-26 |
| State transitions | Diagrama da situação do processamento; ALLOC-01, ALLOC-03, ALLOC-05 e ALLOC-30 |
| Failure and partial failure | ALLOC-03, ALLOC-30 e ALLOC-31 |
| Idempotency and duplication | ALLOC-04 e ALLOC-07; o Offering descarta `BookProcessed` repetido (OFF-25) |
| Concurrency and ordering | Revogação durante o processamento, aplicada junto com a revogação das reservas (ALLOC-05) |
| Cross-capability consistency | Entrada exclusiva (ALLOC-02); conclusão atômica (ALLOC-30); entrega ao menos uma vez (ALLOC-31) |
| Observability | ALLOC-32 e ALLOC-33 |
| Data lifecycle | O resultado fica nas reservas (BID-22) e, depois de revogação, no histórico delas (BID-23) |
| `n/a` | Authorization: o processamento não expõe operação a nenhum chamador; Rate limiting: o processamento roda uma vez por livro fechado, sem chamada que o dispare de fora; External dependency failure: sem integração externa |

## Trade-offs

| Decision | Cost | Reason |
| --- | --- | --- |
| Processamento automático no fechamento, sem revisão do operador (ALLOC-01) | O operador não corrige o livro fechado: uma declaração errada pode exigir revogar a oferta inteira; corrigir depois do fechamento exigiria uma etapa de revisão, com permissões e efeito sobre o resultado | O recorte demonstra a alocação automática pelas regras publicadas; as validações ocorrem antes do fechamento, o histórico é preservado e o processamento é determinístico |
| Retentativa automática até a conclusão ou a interrupção (ALLOC-03) | Uma falha persistente, como um defeito no cálculo, mantém o processamento `Pending` sem limite; a saída é corrigir o defeito ou revogar a oferta (ALLOC-05) | O cálculo é determinístico (ALLOC-07) e a conclusão é atômica (ALLOC-30), então repetir é seguro; não exige operação nova nem decisão do operador, e o reprocessamento manual está fora do Scope |
| Aplicação dos resultados e registro do desfecho numa só operação (ALLOC-30) | O Offering só recebe o desfecho depois de os resultados estarem aplicados, e a entrega é assíncrona (ALLOC-31): a oferta continua `Open` até recebê-lo | Elimina o estado em que o Offering assume um desfecho que as reservas não refletem; emitir antes e aplicar depois exigiria reconciliação |
| `E` apurado antes do condicionamento, sem recálculo (ALLOC-13) | A oferta pode se formar com soma final alocada abaixo do montante mínimo | O modelo adota a leitura do art. 74, parágrafo único, da CVM 160: as condicionadas integram os efetivamente distribuídos, e a base do proporcional é fixada antes das condições |
| Um único critério de rateio, proporcional (ALLOC-18) | Ofertas com outro critério não são representáveis | Decisão do autor; nenhuma fonte registrada sustenta que seja o critério usual de ofertas de varejo |
| Resto por maior parte fracionária, desempate pela ordem de registro (ALLOC-19) | Reservas grandes tendem a ficar com o resto; fracionar aumenta as chances; nenhuma fonte registrada mostra esse critério em planos de distribuição, que podem adotar outro | Minimiza o desvio do proporcional exato, atende ao art. 49, III, e é determinístico e auditável |
| Limites por investidor só no registro (ALLOC-26) | O investidor pode receber uma cota ou nenhuma com investimento mínimo de dez | O rateio proporcional (ALLOC-18) não tem piso por investidor; garantir o mínimo seria outro critério de rateio, fora do Scope |
| `ScaledBack` como identificador do rateio (ALLOC-27) | Atendida parcialmente vira dois status, `ScaledBack` e `PartiallyFilledByCondition`, e o operador precisa dos dois para explicar o resultado | Termo de comunicados de oferta ("scale-back of oversubscriptions on a pro rata basis", Euro Manganese, em References); `ProRata` colidiria com a opção 3 |
| `Unconditional` e `Lapsed` como identificadores do desfecho (ALLOC-28) | `Unconditional` convive com as opções de condicionamento da reserva | Termos do Takeover Code e de prospectos listados em References, em vez da tradução literal `Formed` e `NotFormed`; a escolha é terminológica e não importa as regras dessas ofertas |

## References

- [Resolução CVM 160](https://conteudo.cvm.gov.br/export/sites/cvm/legislacao/resolucoes/anexos/100/resol160consolid.pdf), lida em 2026-09-05. Art. 56, caput, § 1º, III, e § 3º: vedação a pessoas vinculadas em excesso superior a um terço, exceção quando a exclusão derruba a demanda abaixo da quantidade ofertada e colocação limitada ao necessário, preservada a integral das não vinculadas (ALLOC-09, ALLOC-10, ALLOC-23); o excesso ignora lotes adicional e suplementar. Art. 73, §§ 3º e 4º: restituição abaixo do mínimo, inclusive a quem condicionou à totalidade (ALLOC-12, ALLOC-14). Art. 70: suspensão e cancelamento são atos da CVM por irregularidade (ALLOC-12); por isso o desfecho é não formada, e não cancelada. Art. 74 e parágrafo único: opção do investidor entre a totalidade e o mínimo, e as condicionadas integram os efetivamente distribuídos (ALLOC-13, ALLOC-16). Art. 49, III: o plano fixa o rateio com tratamento equitativo, sem impor critério (ALLOC-18, ALLOC-19). Arts. 65 e 75 delimitam o Glossary e o Scope.
- [Instrução CVM 400](https://conteudo.cvm.gov.br/export/sites/cvm/legislacao/instrucoes/anexos/400/inst400.pdf), revogada, lida em 2026-09-05. Art. 31, § 1º: origem da distinção entre totalidade e proporcional (ALLOC-16); referência histórica.
- [Euro Manganese](https://www.newsfilecorp.com/release/252189/Completion-of-A1.5M-Security-Purchase-Plan), lido em 2026-09-06: comunicado com uso de scale-back; referência terminológica para `ScaledBack`, sem valor normativo.
- [The Takeover Code, regra 31.2](https://code.thetakeoverpanel.org.uk/tp/rules/rule-31/rule-31-2.html?date=2023-12-11&timeline=True), 14ª edição, versão de 2023-12-11, consultada em 2026-09-16: usa `unconditional` e `lapses` como desfechos de oferta; referência terminológica para `Unconditional` e `Lapsed`, sem valor normativo.
- [Prospecto da Shanghai FourSemi Semiconductor Co., Ltd., publicado na HKEX](https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0323/2026032300023.pdf), datado de 2026-03-23, seção "Structure of the Global Offering — Conditions of the Global Offering", pp. 287–288 da numeração impressa, consultado em 2026-09-16: usa `unconditional` e `lapse` nas condições da oferta; referência terminológica para `Unconditional` e `Lapsed`, sem valor normativo.
