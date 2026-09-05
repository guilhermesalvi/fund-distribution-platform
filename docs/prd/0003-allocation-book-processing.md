<!-- prd-tier: complexa -->
# Processamento do Livro e Alocação

| | |
|---|---|
| **Status** | Rascunho |
| **Autor** | Guilherme Salvi |
| **Data** | 2026-09-04 |
| **Contexto Originário** | Allocation (primário); consome Offering e ReservationBook; devolve `BookProcessed` aos dois |
| **Confiança** | Média — uma premissa-crítica regulatória em validação; regra de sobras do rateio e alocação abaixo do mínimo por investidor em aberto |

## Resumo Executivo

Quando a oferta fecha, o livro precisa virar resultado: a oferta se formou ou não; quais reservas entram, depois da vedação a pessoas vinculadas; quantas cotas inteiras cada reserva recebe, por condicionamento em distribuição parcial ou por rateio em excesso de demanda. O contexto Allocation faz esse processamento uma vez por oferta, a partir do livro fechado e da definição da oferta, e devolve um único desfecho. Métrica primária: resultado determinístico, com soma alocada nunca acima da quantidade base e igual a ela em caso de excesso, e nenhuma reserva recebendo mais do que pediu.

## Alinhamento Estratégico

[FATO] O projeto é um modelo executável do comportamento regulado pela Resolução CVM 160 e pela Resolução CVM 175, reduzido ao mínimo viável, para o caso de uso de corretora distribuindo cotas a investidor final. A plataforma tem três contextos: Offering, ReservationBook e Allocation.

Allocation é o núcleo do domínio: é onde as regras da CVM 160 sobre distribuição parcial, condicionamento e pessoas vinculadas produzem efeito, e onde a plataforma entrega o que promete, o resultado da alocação. Os outros dois contextos existem para alimentar este. Por isso o rigor deste PRD está na precisão das regras e nos exemplos numéricos, e não em funcionalidade.

[FATO] Outros critérios de rateio, lote adicional, tranches e alocação discricionária estão fora do escopo por decisão do autor.

## Contexto e Problema

[FATO] CVM 160, art. 73: a oferta se mantém a partir do mínimo definido pelo ofertante; abaixo dele, tudo é restituído (§ 3º). Art. 74: em distribuição parcial, o investidor pode ter condicionado a adesão à colocação total ou ao mínimo; o parágrafo único define cotas efetivamente distribuídas como todas as objeto de reserva, inclusive as condicionadas.

[FATO] CVM 160, art. 56: é vedada a colocação para pessoas vinculadas quando o excesso de demanda supera um terço da quantidade inicialmente ofertada, salvo, entre outras exceções, quando a exclusão delas deixaria a demanda remanescente abaixo da quantidade ofertada (§ 1º, III).

[FATO] CVM 160, art. 49: os coordenadores elaboram o plano de distribuição. A norma não fixa critério de rateio; ele é definido nos documentos da oferta. [PREMISSA] O rateio proporcional às reservas é o critério padrão de mercado para o público de varejo e é o único da v1.

[FATO] A distinção entre receber a totalidade ou o proporcional em distribuição parcial vem da Instrução CVM 400, art. 31, § 1º (revogada), mantida pela prática de mercado.

Sem um processamento único e determinístico, cada leitura do livro produziria um resultado diferente, e nenhum contexto poderia confiar no desfecho. Sem regras precisas para vedação, formação, condicionamento e rateio, os exemplos de borda (exclusão que derruba a demanda abaixo da base, truncamento que deixa sobras, condição que cancela reservas depois da formação) ficam a critério de quem implementa.

[PREMISSA-CRÍTICA] A leitura do art. 74, parágrafo único, é que cotas efetivamente distribuídas são apuradas antes de aplicar o condicionamento e não são recalculadas depois: a formação e o denominador do proporcional consideram todas as reservas do livro, inclusive as que a condição de colocação total vai cancelar. Consequência aceita: a oferta pode se formar e ser alocada com soma final abaixo do montante mínimo. Se falsa — se a formação tiver de considerar só o que sobra após o condicionamento — o processamento vira iterativo (excluir condicionadas, reavaliar o mínimo, repetir até estabilizar), os resultados mudam e FR-09 a FR-13 são reescritos.

## Usuário-alvo / JTBD

Operador da corretora: quer que o fechamento produza um resultado correto, explicável reserva a reserva e reprodutível, sem intervenção manual. JTBD: fechar a oferta e ter o desfecho.

Investidor (indireto, via livro): quer saber quantas cotas recebeu e por quê.

Consumidores (tratados como usuários de plataforma): Offering, que muda de estado com o desfecho, e ReservationBook, que aplica o resultado por reserva.

## Solução Proposta

Processar o livro fechado uma única vez por oferta, em etapas ordenadas com regras fixas, produzindo um desfecho e um resultado por reserva:

1. **Consolidação**: demanda total é a soma das quantidades das reservas ativas do livro fechado.
2. **Vedação a pessoas vinculadas**: se a demanda total supera a quantidade base em mais de um terço, as reservas com declaração de vínculo são excluídas, salvo se a exclusão deixar a demanda remanescente abaixo da quantidade base, caso em que nenhuma é excluída. Resulta a demanda efetiva.
3. **Formação**: demanda efetiva abaixo do montante mínimo, a oferta não se forma; caso contrário, se forma, e as cotas efetivamente distribuídas são o menor valor entre a demanda efetiva e a quantidade base.
4. **Distribuição parcial** (demanda efetiva entre o mínimo e a base, exclusive a base): cada reserva recebe conforme sua opção de condicionamento; as cotas efetivamente distribuídas não são recalculadas depois.
5. **Colocação integral** (demanda efetiva igual à base): cada reserva recebe a quantidade reservada.
6. **Excesso de demanda** (demanda efetiva acima da base): rateio proporcional em cotas inteiras, com sobras distribuídas uma a uma; o condicionamento não se aplica.
7. **Desfecho**: `BookProcessed` com a oferta formada e alocada, ou não formada, mais o resultado por reserva.

Mecanismo de execução, forma de leitura do livro e transporte do resultado são downstream e fora deste documento.

## Glossário de Domínio

| Termo | Definição |
|---|---|
| Livro fechado | Reservas ativas de uma oferta no instante do fechamento. Entrada única do processamento. |
| Demanda total | Soma das quantidades reservadas do livro fechado. |
| Demanda efetiva | Demanda total após a vedação a pessoas vinculadas. Base da formação, do condicionamento e do rateio. |
| Excesso de demanda | Demanda efetiva acima da quantidade base. |
| Excesso superior a um terço | Demanda total maior que a quantidade base multiplicada por quatro terços. Gatilho da vedação do art. 56. |
| Formação | Demanda efetiva maior ou igual ao montante mínimo. Oferta formada segue para alocação; não formada é cancelada. |
| Cotas efetivamente distribuídas | Menor valor entre demanda efetiva e quantidade base, apurado antes do condicionamento (art. 74, parágrafo único). |
| Distribuição parcial | Demanda efetiva entre o montante mínimo e a quantidade base, exclusive esta. |
| Condicionamento | Regra por reserva em distribuição parcial: colocação total (cancela), mínimo com totalidade (integral), mínimo com proporcional (truncado). Definido no PRD do Offering. |
| Rateio proporcional | Em excesso, cada reserva recebe a parte inteira de quantidade reservada vezes quantidade base dividido pela demanda efetiva. |
| Sobras | Cotas da quantidade base não distribuídas pelo truncamento do rateio. Distribuídas uma a uma. |
| Quantidade alocada | Cotas inteiras atribuídas a uma reserva no resultado. Nunca maior que a reservada. |
| Desfecho | Resultado do processamento para a oferta: formada e alocada, ou não formada. |

## Functional Requirements

Regras de negócio; cada uma é uma condição verificável, não um fluxo de interface. Notação: `B` quantidade base, `M` montante mínimo, `D` demanda total, `D'` demanda efetiva, `E` cotas efetivamente distribuídas, `q` quantidade reservada de uma reserva.

### Gatilho e entrada

- **FR-01 (Must)** O processamento inicia com o fechamento da oferta e usa como entrada exclusiva a definição da oferta publicada e o livro fechado.
- **FR-02 (Must)** Cada oferta é processada uma única vez. Um segundo processamento da mesma oferta é rejeitado.
- **FR-03 (Must)** Se a oferta for revogada antes de o processamento concluir, ele é interrompido e nenhum resultado é emitido.
- **FR-04 (Must)** O processamento é determinístico: a mesma oferta e o mesmo livro fechado produzem exatamente o mesmo resultado.

### Consolidação e vedação

- **FR-05 (Must)** `D` é a soma de `q` de todas as reservas do livro fechado.
- **FR-06 (Must)** Se `D > B × 4/3`, as reservas com declaração de vínculo são excluídas, com quantidade alocada zero e motivo de exclusão por vinculação.
- **FR-07 (Must)** A exclusão de FR-06 não ocorre se a demanda remanescente após excluir todas as vinculadas ficar abaixo de `B`; nesse caso nenhuma reserva é excluída e as vinculadas participam normalmente.
- **FR-08 (Must)** `D'` é a soma de `q` das reservas não excluídas. As demais exceções do art. 56, § 1º (formadores de mercado, aplicação mínima obrigatória) não são modeladas.

### Formação

- **FR-09 (Must)** Se `D' < M`, a oferta não se forma: o desfecho é não formada, e toda reserva não excluída recebe quantidade alocada zero com motivo de oferta não formada.
- **FR-10 (Must)** Se `D' ≥ M`, a oferta se forma e `E = min(D', B)`. `E` é apurado uma vez e não é recalculado após o condicionamento.

### Distribuição parcial (`M ≤ D' < B`)

- **FR-11 (Must)** Reserva com opção de colocação total recebe zero, com motivo de não atendida por condicionamento.
- **FR-12 (Must)** Reserva com opção de mínimo recebendo a totalidade recebe `q`.
- **FR-13 (Must)** Reserva com opção de mínimo recebendo o proporcional recebe a parte inteira de `q × E / B`.
- **FR-14 (Must)** Em oferta que não admite distribuição parcial (`M = B`), este ramo não ocorre: `D' < B` implica `D' < M` e a oferta não se forma.

### Colocação integral (`D' = B`)

- **FR-15 (Must)** Cada reserva não excluída recebe `q`.

### Excesso de demanda (`D' > B`)

- **FR-16 (Must)** Cada reserva não excluída recebe a parte inteira de `q × B / D'`.
- **FR-17 (Must)** As sobras, `B` menos a soma de FR-16, são distribuídas uma cota por reserva, em ordem decrescente da parte fracionária de `q × B / D'`. [PREMISSA] Empate é desfeito pela ordem cronológica de registro da reserva, mais antiga primeiro.
- **FR-18 (Must)** Nenhuma reserva recebe mais que `q`; se a distribuição de sobras alcançar esse limite em uma reserva, a cota vai para a próxima na ordem.
- **FR-19 (Must)** A soma das quantidades alocadas em excesso de demanda é exatamente `B`.
- **FR-20 (Must)** O condicionamento não se aplica em excesso de demanda; a opção declarada é ignorada.

### Resultado

- **FR-21 (Must)** Toda quantidade alocada é inteira e maior ou igual a zero.
- **FR-22 (Must)** Em qualquer ramo, a soma das quantidades alocadas é menor ou igual a `B`.
- **FR-23 (Must)** [PREMISSA] Investimento mínimo e máximo por investidor valem para a reserva, não para a alocação: rateio e proporcional podem alocar abaixo do mínimo por investidor.
- **FR-24 (Must)** O resultado por reserva carrega quantidade alocada e um motivo entre: atendida integralmente, atendida parcialmente por proporcional, atendida parcialmente por rateio, não atendida por condicionamento, excluída por vinculação, oferta não formada.
- **FR-25 (Must)** O desfecho da oferta carrega `D`, `D'`, `E`, o ramo aplicado e a lista de resultados por reserva, e é emitido uma única vez como `BookProcessed`.

## Domain Events

| Evento | Produtor | Consumidores | Gatilho de negócio |
|---|---|---|---|
| `BookProcessed` | Allocation | Offering, ReservationBook | Processamento concluído; carrega desfecho (formada e alocada, ou não formada), `D`, `D'`, `E`, ramo e resultado por reserva |

Eventos consumidos:

| Evento | Produtor | Uso neste contexto |
|---|---|---|
| `OfferPublished` | Offering | Conhece a definição da oferta que será processada |
| `OfferClosed` | Offering | Inicia o processamento (FR-01) |
| `OfferRevoked` | Offering | Interrompe processamento em curso (FR-03) |

O livro fechado é lido do ReservationBook no início do processamento; a forma dessa leitura é candidata a ADR no PRD do ReservationBook.

## Non-functional Requirements

- **NFR-01** Aritmética exata: quantidades e razões são calculadas sem ponto flutuante; truncamento é sempre para baixo.
- **NFR-02** O processamento de um livro é atômico: ou emite `BookProcessed` completo, ou não emite nada.
- **NFR-03** O resultado é explicável: para cada reserva, o motivo e os valores `D`, `D'`, `E` e o ramo permitem recalcular a quantidade alocada manualmente.
- **NFR-04** O processamento é a única operação de domínio que abre span manual nesta plataforma; segue as regras de tracing do repositório.

## Considerações Regulatórias

[FATO] CVM 160, art. 56 e § 1º, III: vedação em excesso superior a um terço e exceção quando a exclusão derruba a demanda abaixo da quantidade ofertada. FR-06 e FR-07 modelam exatamente isso; o cálculo do excesso ignora lote adicional e suplementar, que não existem na v1.

[FATO] CVM 160, art. 73 e § 3º: mínimo e restituição integral quando não atingido. FR-09 modela o desfecho não formada.

[FATO] CVM 160, art. 74 e parágrafo único: opções de condicionamento e definição de efetivamente distribuídos incluindo as condicionadas. FR-10 fixa `E` antes do condicionamento; a leitura está na premissa-crítica.

[PREMISSA] Sob o art. 74, as opções de colocação total e de mínimo com totalidade são obrigatórias em oferta com distribuição parcial. Não afeta este contexto: ele aplica a opção declarada, seja qual for o conjunto aceito.

[FATO] CVM 160, art. 75: a seção de distribuição parcial não se aplica a ofertas exclusivas para investidores profissionais. Não modelado; a categoria declarada não altera o condicionamento na v1.

[FATO] CVM 160, art. 49: plano de distribuição pelos coordenadores. O critério de rateio da v1 (proporcional com sobras por maior resto) é uma escolha do modelo, não uma imposição da norma.

[LACUNA] Não está definido se o plano de distribuição do caso de uso prevê rateio com prioridade por lote mínimo ou tratamento especial de reservas pequenas, práticas existentes em ofertas de varejo. Se sim, FR-16 e FR-17 mudam.

## Não-objetivos

- Outros critérios de rateio (divisão igualitária e sucessiva, ordem cronológica) e critérios por tranche.
- Lote adicional e lote suplementar.
- Alocação discricionária e tranche institucional.
- Exceções à vedação do art. 56 para formadores de mercado e para aplicação mínima obrigatória.
- Efeito da categoria do investidor (bloqueio de condicionamento para profissional, elegibilidade a tranches).
- Reprocessamento manual ou ajuste do resultado pelo operador.
- Liquidação financeira, custódia e posição do cotista.

## Trade-offs Declarados

- **Processamento automático no fechamento, sem revisão do operador.** *Custo:* não há como corrigir um livro com erro (reserva indevida, declaração errada) entre o fechamento e o resultado; a saída é revogar a oferta. *Razão:* revisão manual abre espaço para alocação discricionária, que está fora do escopo; o determinismo é o valor do modelo. Ver Ponto de Maior Fragilidade.
- **Sobras por maior parte fracionária, desempate cronológico.** *Custo:* investidores com reservas grandes tendem a ficar com a sobra; o critério não está nos documentos típicos de oferta. *Razão:* é o arredondamento que minimiza o desvio total em relação ao proporcional exato; o desempate cronológico é determinístico e auditável.
- **Limites por investidor valem só para a reserva.** *Custo:* um investidor pode receber uma cota quando o investimento mínimo era dez. *Razão:* é o comportamento real do rateio; impor o mínimo na alocação exigiria excluir reservas pequenas, o que é critério de rateio distinto e fora do escopo.
- **Um único critério de rateio.** *Custo:* ofertas cujo plano de distribuição prevê outro critério não são representáveis. *Razão:* proporcional é o padrão de varejo; os demais estão na tabela de extensões.
- **Vedação aplicada antes da formação.** *Custo:* nenhum; pela exceção do § 1º, III, a exclusão nunca leva a demanda abaixo de `B`, então não altera a formação. *Razão:* segue a ordem lógica da norma e evita excluir reservas de uma oferta que não vai se formar.

## Métricas de Sucesso

Projeto sem uso em produção; as métricas são de correção e de contrato, verificáveis por teste e por inspeção.

**Leading:**
- Todos os cenários dos Critérios de Aceitação reproduzidos por teste, com igualdade exata dos valores — alvo: 100%.
- Processar o mesmo livro duas vezes em ambiente de teste produz resultados idênticos — alvo: 100% em amostra aleatória de livros gerados.
- Invariantes FR-18, FR-19, FR-21 e FR-22 verificadas em todo livro gerado aleatoriamente — alvo: zero violações.

**Lagging:**
- Offering e ReservationBook aplicam `BookProcessed` sem precisar de dado que não esteja em FR-24 e FR-25 — verificado contra os PRDs do Offering e do ReservationBook.

**Guardrails:**
- Nenhuma reserva recebe mais do que reservou.
- Nenhuma quantidade alocada fracionária.
- Nenhuma alteração no livro fechado ou na definição da oferta por este contexto.

## Critérios de Aceitação

Em todos os cenários, `B = 1000` e `M = 600`, salvo indicação.

- **Dado** reservas A 500 (opção 3) e C 300 (opção 2), nenhuma vinculada, **quando** o livro é processado, **então** `D = D' = 800`, oferta formada em distribuição parcial, `E = 800`, A recebe 400 (parte inteira de 500 × 800 / 1000) e C recebe 300; desfecho formada e alocada, soma 700.
- **Dado** reservas A 100 (opção 1) e C 550 (opção 2), **quando** processado, **então** `D' = 650 ≥ 600`, formada, `E = 650`, A recebe 0 por condicionamento e C recebe 550; desfecho formada e alocada mesmo com soma 550 abaixo de `M`.
- **Dado** reservas somando 500, **quando** processado, **então** oferta não formada, todas com quantidade zero e motivo de oferta não formada; desfecho não formada.
- **Dado** reservas A 700, C 500 e V 300 (V vinculada), **quando** processado, **então** `D = 1500 > 1333,33`, V excluída, `D' = 1200 ≥ 1000`, rateio: A recebe 583 (583,33), C recebe 416 (416,67), sobra 1 vai para C (maior fração) → A 583, C 417, V 0 excluída; soma 1000.
- **Dado** reservas A 800 e V 600 (V vinculada), **quando** processado, **então** `D = 1400 > 1333,33`, mas excluir V deixaria 800 < 1000, logo V não é excluída; `D' = 1400`, rateio: A 571 (571,43), V 428 (428,57), sobra 1 vai para V → A 571, V 429; soma 1000.
- **Dado** reservas A 600 e C 400, **quando** processado, **então** `D' = 1000 = B`, colocação integral, A 600 e C 400, opções ignoradas.
- **Dado** reservas A 1000 e C 1000 registradas nessa ordem, **quando** processado, **então** rateio 500 e 500, sem sobras; se fossem A 1000 e C 999, A 500 (500,25), C 499 (499,75), sobra 1 vai para C (maior fração) → 500 e 500.
- **Dado** `M = B = 1000` e reservas somando 900, **quando** processado, **então** oferta não formada.
- **Dado** um processamento em curso, **quando** a oferta é revogada, **então** nenhum `BookProcessed` é emitido.
- **Dado** uma oferta já processada, **quando** um novo processamento é solicitado, **então** é rejeitado.

## Dependências e Riscos

| Item | Tipo | Impacto |
|---|---|---|
| Offering: definição da oferta, `OfferClosed`, `OfferRevoked`; consome `BookProcessed` | Acoplamento bidirecional | Alto — sem definição não há processamento; o desfecho muda o estado da oferta |
| ReservationBook: leitura do livro fechado com instante de registro; consome `BookProcessed` | Acoplamento bidirecional | Alto — o desempate cronológico exige instante estável por reserva (pergunta em aberto no PRD do ReservationBook) |
| Premissa-crítica sobre `E` fixado antes do condicionamento | Risco regulatório | Se cair, o algoritmo vira iterativo e os resultados mudam |
| Critério de sobras | Risco de desenho | Escolha do modelo, não da norma; pode divergir do plano de distribuição do caso de uso |
| Processamento sem revisão | Risco operacional | Erro no livro só se corrige por revogação |

## Perguntas em Aberto

- [ ] **Regra de sobras.** Critério decisivo: se o plano de distribuição do caso de uso fixa outro critério (por exemplo, ordem cronológica pura ou lote mínimo primeiro), FR-17 muda; se não fixa, maior fração fica.
- [ ] **Alocação abaixo do investimento mínimo por investidor é aceitável?** Critério decisivo: se os documentos do caso de uso garantem o mínimo ao investidor atendido, FR-23 cai e entra regra de exclusão de reservas pequenas no rateio.
- [ ] **Instante da reserva para desempate: registro original ou última alteração?** Critério decisivo: resposta do PRD do ReservationBook; afeta FR-17.
- [ ] **O operador precisa ver o resultado antes de ele valer?** Critério decisivo: se sim, entra um estado de resultado proposto e uma aprovação, e o processamento deixa de ser automático. Ver Ponto de Maior Fragilidade.
- [ ] **Candidato a ADR:** forma de leitura do livro fechado e garantia de que o Allocation processa exatamente o livro congelado no fechamento.

## Ponto de Maior Fragilidade

A decisão de **processar o livro automaticamente no fechamento e emitir o resultado sem revisão do operador**.

*Vetor de ataque:* um revisor cético aponta que, na vida real, o coordenador revisa o livro antes de divulgar a alocação, e que o modelo não tem nenhum ponto entre Fechada e Alocada para corrigir uma reserva indevida, uma declaração de vínculo errada ou um investidor que não deveria estar no livro. Com o processamento automático, a única correção é revogar a oferta inteira, o que pune todos os investidores por um erro de uma reserva. O custo de estar errado é alto: entra um estado de alocação proposta, uma aprovação explícita e a possibilidade de ajuste, e a máquina de estados do Offering ganha um passo.

*Desafie antes de aprovar:* o determinismo sem intervenção é o que o modelo quer demonstrar, ou é uma simplificação que vai cair no primeiro cenário de erro no livro? Se for o segundo, é mais barato colocar o passo de aprovação agora, sem ajuste discricionário, do que reabrir as três máquinas de estado depois.

## Referências

- [Resolução CVM 160 (texto consolidado)](https://conteudo.cvm.gov.br/export/sites/cvm/legislacao/resolucoes/anexos/100/resol160consolid.pdf) — arts. 49, 56, 73, 74 e 75.
- [Instrução CVM 400 (revogada)](https://conteudo.cvm.gov.br/export/sites/cvm/legislacao/instrucoes/anexos/400/inst400.pdf) — art. 31, § 1º, origem da distinção totalidade/proporcional.
- [PRD 0001 — Cadastro e Ciclo de Vida da Oferta](0001-offering-offer-lifecycle.md) — definição da oferta, estados e semântica das opções de condicionamento.
- [PRD 0002 — Livro de Reservas](0002-reservation-book-reservation-lifecycle.md) — livro fechado, declarações e status por reserva.
