<!-- prd-tier: complexa -->
# Processamento do Livro e Alocação

| | |
|---|---|
| **Status** | Rascunho |
| **Autor** | Guilherme Salvi |
| **Data** | 2026-09-04 |
| **Contexto Originário** | Allocation (primário); consome Offering e ReservationBook; devolve `BookProcessed` aos dois |

## Resumo Executivo

Quando a oferta fecha, o livro precisa virar resultado: a oferta se formou ou não; quais reservas entram, depois da vedação a pessoas vinculadas; quantas cotas inteiras cada reserva recebe, por condicionamento em distribuição parcial ou por rateio em excesso de demanda. O contexto Allocation faz esse processamento uma vez por oferta, a partir do livro fechado e da definição da oferta, e devolve um único desfecho. Métrica primária: resultado determinístico, com soma alocada nunca acima da quantidade base e igual a ela em caso de excesso, e nenhuma reserva recebendo mais do que pediu.

## Alinhamento Estratégico

[FATO] O projeto é um modelo executável do comportamento regulado pela Resolução CVM 160 e pela Resolução CVM 175, reduzido ao mínimo viável, para o caso de uso de corretora distribuindo cotas a investidor final. A plataforma tem três contextos: Offering, ReservationBook e Allocation.

Allocation é o núcleo do domínio: é onde as regras da CVM 160 sobre distribuição parcial, condicionamento e pessoas vinculadas produzem efeito, e onde a plataforma entrega o que promete, o resultado da alocação. Os outros dois contextos existem para alimentar este. Por isso o rigor deste PRD está na precisão das regras e nos exemplos numéricos, e não em funcionalidade.

[FATO] Outros critérios de rateio, lote adicional, tranches e alocação discricionária estão fora do escopo por decisão do autor.

## Contexto e Problema

[FATO] CVM 160, art. 73: a oferta se mantém a partir do mínimo definido pelo ofertante; abaixo dele, tudo é restituído (§ 3º), inclusive a quem condicionou a adesão à distribuição total (§ 4º). Art. 74: em distribuição parcial, o investidor pode ter condicionado a adesão à colocação total ou ao mínimo; o parágrafo único define valores efetivamente distribuídos como todos os objeto de subscrição, "inclusive aqueles sujeitos às condições previstas nos incisos I e II".

[FATO] CVM 160, art. 56: é vedada a colocação para pessoas vinculadas quando o excesso de demanda supera um terço da quantidade inicialmente ofertada. A vedação não se aplica quando, sem a colocação para vinculadas, a demanda remanescente fica abaixo da quantidade ofertada (§ 1º, III); nessa hipótese, a colocação para vinculadas fica limitada ao necessário para perfazer a quantidade ofertada, preservada a colocação integral do que as não vinculadas demandaram (§ 3º).

[FATO] CVM 160, art. 49, III: em oferta ao público em geral com possibilidade de rateio, o plano de distribuição deve estabelecer regras que garantam tratamento equitativo, e pode fixar limite máximo por pedido de reserva. A norma não fixa critério de rateio. [FATO] Por decisão do autor, o rateio proporcional às reservas, com resto do arredondamento por maior fração, é o único critério da v1.

[FATO] A distinção entre receber a totalidade ou o proporcional em distribuição parcial vem da Instrução CVM 400, art. 31, § 1º (revogada), mantida pela prática de mercado.

Sem um processamento único e determinístico, cada leitura do livro produziria um resultado diferente, e nenhum contexto poderia confiar no desfecho. Sem regras precisas para vedação, formação, condicionamento e rateio, os exemplos de borda (exclusão que derruba a demanda abaixo da base, truncamento que deixa resto, condição que cancela reservas depois da formação) ficam a critério de quem implementa.

[FATO] As cotas efetivamente distribuídas são apuradas antes de aplicar o condicionamento e não são recalculadas depois: a formação e o numerador do proporcional consideram todas as reservas do livro fechado, inclusive as que a condição de colocação total vai cancelar. É a leitura literal do art. 74, parágrafo único, e a única que o texto admite: o parágrafo existe para quebrar a circularidade entre "quanto foi distribuído" e "quais condições se cumprem". Consequência aceita: a oferta pode se formar e ser alocada com soma final abaixo do montante mínimo, e os investidores da opção 1 são restituídos (art. 73, § 4º).

## Usuário-alvo / JTBD

Operador da corretora: quer que o fechamento produza um resultado correto, explicável reserva a reserva e reprodutível, sem intervenção manual. JTBD: fechar a oferta e ter o desfecho.

Investidor (indireto, via livro): quer saber quantas cotas recebeu e por quê.

Consumidores (tratados como usuários de plataforma): Offering, que muda de estado com o desfecho, e ReservationBook, que aplica o resultado por reserva.

## Solução Proposta

Processar o livro fechado uma única vez por oferta, em etapas ordenadas com regras fixas, produzindo um desfecho e um resultado por reserva:

1. **Consolidação**: demanda total é a soma das quantidades das reservas ativas do livro fechado.
2. **Vedação a pessoas vinculadas**: se a demanda total supera a quantidade base em mais de um terço, as reservas com declaração de vínculo são excluídas, salvo se a demanda das não vinculadas ficar abaixo da quantidade base. Nesse caso nenhuma é excluída, mas a colocação para vinculadas fica limitada ao que falta para completar a base depois de atender integralmente as não vinculadas. Resulta a demanda efetiva.
3. **Formação**: demanda efetiva abaixo do montante mínimo, a oferta não se forma; caso contrário, se forma, e as cotas efetivamente distribuídas são o menor valor entre a demanda efetiva e a quantidade base.
4. **Distribuição parcial** (demanda efetiva entre o mínimo e a base, exclusive a base): cada reserva recebe conforme sua opção de condicionamento; as cotas efetivamente distribuídas não são recalculadas depois.
5. **Colocação integral** (demanda efetiva igual à base): cada reserva recebe a quantidade reservada.
6. **Excesso de demanda** (demanda efetiva acima da base): rateio proporcional em cotas inteiras, com o resto do arredondamento distribuído uma cota por reserva; em colocação limitada, o rateio se aplica só às vinculadas sobre o que falta para a base; o condicionamento não se aplica.
7. **Desfecho**: `BookProcessed` com a oferta formada e alocada, ou não formada, mais o resultado por reserva.

Mecanismo de execução, forma de leitura do livro e transporte do resultado são downstream e fora deste documento.

## Glossário de Domínio

| Termo | Definição |
|---|---|
| Livro fechado | Reservas ativas de uma oferta no instante do fechamento. Entrada única do processamento. Um investidor pode ter mais de uma reserva; cada reserva é uma linha. |
| Demanda total | Soma das quantidades reservadas do livro fechado. |
| Demanda das não vinculadas | Soma das quantidades reservadas das reservas sem declaração de vínculo. Decide entre exclusão e colocação limitada. |
| Demanda efetiva | Demanda total após a vedação a pessoas vinculadas. Base da formação, do condicionamento e do rateio; o condicionamento não a altera. Em colocação limitada, é igual à demanda total. |
| Excesso de demanda | Demanda efetiva acima da quantidade base. |
| Excesso superior a um terço | Demanda total maior que a quantidade base multiplicada por quatro terços. Gatilho da vedação do art. 56. |
| Colocação limitada | Hipótese do art. 56, §§ 1º, III, e 3º: não vinculadas recebem o que demandaram; vinculadas dividem o que falta para completar a quantidade base. |
| Formação | Demanda efetiva maior ou igual ao montante mínimo. Oferta formada segue para alocação; não formada não aloca nada e os valores são restituídos. |
| Cotas efetivamente distribuídas | Menor valor entre demanda efetiva e quantidade base, apurado antes do condicionamento (art. 74, parágrafo único). |
| Distribuição parcial | Demanda efetiva entre o montante mínimo e a quantidade base, exclusive esta. |
| Condicionamento | Regra por reserva em distribuição parcial: colocação total (cancela), mínimo com totalidade (integral), mínimo com proporcional (truncado). Definido no PRD do Offering. |
| Rateio proporcional | Em excesso, cada reserva recebe a parte inteira de quantidade reservada vezes quantidade rateada dividido pela demanda rateada. No caso geral, quantidade rateada é a base e demanda rateada é a demanda efetiva. |
| Resto do arredondamento | Cotas da quantidade rateada não distribuídas pelo truncamento. Distribuídas uma a uma por maior parte fracionária. Em inglês, `RoundingRemainder`. Não confundir com "sobras" de subscrição (art. 65, § 2º, I), que são valores não subscritos na primeira rodada e estão fora do escopo. |
| Quantidade alocada | Cotas inteiras atribuídas a uma reserva no resultado. Nunca maior que a reservada; zero é válido. |
| Desfecho | Resultado do processamento para a oferta: formada e alocada, ou não formada. |

## Functional Requirements

Regras de negócio; cada uma é uma condição verificável, não um fluxo de interface. Notação: `B` quantidade base, `M` montante mínimo, `D` demanda total, `Dn` demanda das não vinculadas, `D'` demanda efetiva, `E` cotas efetivamente distribuídas, `q` quantidade reservada de uma reserva.

### Gatilho e entrada

- **FR-01 (Must)** O processamento inicia com o fechamento da oferta e usa como entrada exclusiva a definição da oferta publicada e o livro fechado.
- **FR-02 (Must)** Cada oferta produz no máximo um `BookProcessed`. Depois de emitido, novo processamento da mesma oferta é rejeitado. Um processamento que terminou sem emitir resultado (NFR-02) pode ser repetido e, por FR-04, produz o resultado que o original produziria.
- **FR-03 (Must)** Se a oferta for revogada antes de o processamento concluir, ele é interrompido e nenhum resultado é emitido. Revogação depois da emissão não altera o resultado emitido; seu efeito sobre as reservas é do PRD 0002 (FR-18).
- **FR-04 (Must)** O processamento é determinístico: a mesma oferta e o mesmo livro fechado produzem exatamente o mesmo resultado.

### Consolidação e vedação

- **FR-05 (Must)** `D` é a soma de `q` de todas as reservas do livro fechado; `Dn` é a soma de `q` das reservas sem declaração de vínculo.
- **FR-06 (Must)** Se `D > B × 4/3` e `Dn ≥ B`, as reservas com declaração de vínculo são excluídas, com quantidade alocada zero e motivo de exclusão por vinculação.
- **FR-07 (Must)** Se `D > B × 4/3` e `Dn < B`, nenhuma reserva é excluída e o processamento segue em colocação limitada: cada reserva não vinculada recebe `q`, e as reservas vinculadas rateiam entre si `B − Dn` conforme FR-21.
- **FR-08 (Must)** `D'` é a soma de `q` das reservas não excluídas. As demais exceções do art. 56, § 1º (formadores de mercado, aplicação mínima obrigatória) não são modeladas.

### Formação

- **FR-09 (Must)** Se `D' < M`, a oferta não se forma: o desfecho é não formada, e toda reserva não excluída recebe quantidade alocada zero com motivo de oferta não formada.
- **FR-10 (Must)** Se `D' ≥ M`, a oferta se forma e `E = min(D', B)`. `E` é apurado uma vez e não é recalculado após o condicionamento.

### Distribuição parcial (`M ≤ D' < B`)

- **FR-11 (Must)** Reserva com opção de colocação total recebe zero, com motivo de não atendida por condicionamento.
- **FR-12 (Must)** Reserva com opção de mínimo recebendo a totalidade recebe `q`, com motivo de atendida integralmente.
- **FR-13 (Must)** Reserva com opção de mínimo recebendo o proporcional recebe a parte inteira de `q × E / B`. Zero é resultado válido.
- **FR-14 (Must)** Em oferta que não admite distribuição parcial (`M = B`), este ramo não ocorre: `D' < B` implica `D' < M` e a oferta não se forma.

### Colocação integral (`D' = B`)

- **FR-15 (Must)** Cada reserva não excluída recebe `q`, com motivo de atendida integralmente; a opção de condicionamento é ignorada.

### Excesso de demanda (`D' > B`)

- **FR-16 (Must)** Cada reserva do conjunto rateado recebe a parte inteira de `q × R / Dr`, onde `R` é a quantidade rateada e `Dr` a soma de `q` do conjunto rateado. No caso geral, o conjunto rateado é o das reservas não excluídas, `R = B` e `Dr = D'`. O motivo é atendida parcialmente por rateio, mesmo quando FR-17 leva a quantidade a `q` (FR-24).
- **FR-17 (Must)** O resto do arredondamento, `R` menos a soma de FR-16, é distribuído uma cota por reserva do conjunto rateado, em ordem decrescente da parte fracionária de `q × R / Dr`. Empate é desfeito pela ordem de registro da reserva, mais antiga primeiro; a ordem é total e imutável, e distingue reservas aceitas no mesmo instante (PRD 0002, FR-14).
- **FR-18 (Must)** Nenhuma reserva recebe mais que `q`; se a distribuição do resto alcançar esse limite em uma reserva, a cota vai para a próxima na ordem.
- **FR-19 (Must)** A soma das quantidades alocadas em excesso de demanda é exatamente `B`.
- **FR-20 (Must)** O condicionamento não se aplica em excesso de demanda; a opção declarada é ignorada.
- **FR-21 (Must)** Em colocação limitada (FR-07), o conjunto rateado é o das reservas vinculadas, `R = B − Dn` e `Dr` é a soma de `q` das vinculadas; FR-16 a FR-18 se aplicam a esse conjunto, e as não vinculadas recebem `q` com motivo de atendida integralmente. FR-19 vale para o total.

### Resultado

- **FR-22 (Must)** Toda quantidade alocada é inteira e maior ou igual a zero.
- **FR-23 (Must)** Em qualquer ramo, a soma das quantidades alocadas é menor ou igual a `B`.
- **FR-24 (Must)** Investimento mínimo por reserva e máximo por posição do investidor valem no registro (PRD 0002, FR-03 e FR-04), não na alocação: rateio e proporcional podem alocar abaixo do mínimo por investidor, inclusive zero. O motivo do resultado é a regra aplicada, não a quantidade.
- **FR-25 (Must)** O resultado por reserva carrega quantidade alocada e um motivo entre: atendida integralmente, atendida parcialmente por proporcional, atendida parcialmente por rateio, não atendida por condicionamento, excluída por vinculação, oferta não formada.
- **FR-26 (Must)** O desfecho da oferta carrega `D`, `Dn`, `D'`, `E`, o ramo aplicado (inclusive colocação limitada) e a lista de resultados por reserva, e é emitido uma única vez como `BookProcessed`.

## Domain Events

| Evento | Produtor | Consumidores | Gatilho de negócio |
|---|---|---|---|
| `BookProcessed` | Allocation | Offering, ReservationBook | Processamento concluído; carrega desfecho (formada e alocada, ou não formada), `D`, `Dn`, `D'`, `E`, ramo e resultado por reserva |

Eventos consumidos:

| Evento | Produtor | Uso neste contexto |
|---|---|---|
| `OfferPublished` | Offering | Conhece a definição da oferta que será processada |
| `OfferClosed` | Offering | Inicia o processamento (FR-01) |
| `OfferRevoked` | Offering | Interrompe processamento em curso (FR-03) |

O livro fechado é lido do ReservationBook no início do processamento; a forma dessa leitura é delegada a ADR, e o PRD 0002 (NFR-02) fixa a exigência: o livro lido é idêntico ao congelado.

## Non-functional Requirements

- **NFR-01** Aritmética exata: quantidades e razões são calculadas sem ponto flutuante; truncamento é sempre para baixo.
- **NFR-02** O processamento de um livro é atômico: ou emite `BookProcessed` completo, ou não emite nada.
- **NFR-03** O resultado é explicável: para cada reserva, o motivo e os valores `D`, `Dn`, `D'`, `E` e o ramo permitem recalcular a quantidade alocada manualmente.
- **NFR-04** O processamento é a única operação de domínio que abre span manual nesta plataforma; segue as regras de tracing do repositório.

## Considerações Regulatórias

Texto consolidado da Resolução CVM 160 lido em 2026-09-05; artigos citados conferidos contra o texto.

[FATO] CVM 160, art. 56, caput e § 1º, III: vedação em excesso superior a um terço e exceção quando a exclusão derruba a demanda abaixo da quantidade ofertada. § 3º: na exceção, a colocação para vinculadas "fica limitada ao necessário para perfazer a quantidade de valores mobiliários inicialmente ofertada, desde que preservada a colocação integral junto a pessoas não vinculadas dos valores mobiliários por elas demandados". FR-06, FR-07 e FR-21 modelam os três dispositivos; o cálculo do excesso ignora lote adicional e suplementar, que não existem na v1.

[FATO] CVM 160, art. 73, §§ 3º e 4º: mínimo, restituição integral quando não atingido, e restituição a quem condicionou à distribuição total. FR-09 modela o desfecho não formada; FR-11 modela o § 4º em distribuição parcial.

[FATO] CVM 160, art. 74 e parágrafo único: opções de condicionamento e definição de efetivamente distribuídos incluindo as condicionadas. FR-10 fixa `E` antes do condicionamento.

[FATO] CVM 160, art. 74, I e II: as opções de colocação total e de mínimo são obrigatórias em oferta com distribuição parcial (PRD 0001, FR-25). Não afeta este contexto: ele aplica a opção declarada.

[FATO] CVM 160, art. 75: a seção de distribuição parcial não se aplica a ofertas exclusivas para investidores profissionais. Não modelado; a categoria declarada não altera o condicionamento na v1.

[FATO] CVM 160, art. 49, III: o plano de distribuição fixa as regras de rateio, com tratamento equitativo. O critério da v1 (proporcional com resto por maior fração e desempate pela ordem de registro) é uma escolha do modelo, não uma imposição da norma. Prioridade por lote mínimo, tratamento especial de reservas pequenas e outros critérios do plano são não-objetivos.

## Não-objetivos

- Outros critérios de rateio (divisão igualitária e sucessiva, ordem cronológica pura, prioridade por lote mínimo, exclusão de reservas pequenas) e critérios por tranche.
- Garantia do investimento mínimo por investidor na alocação.
- Lote adicional e lote suplementar.
- Sobras de subscrição e direito de preferência.
- Alocação discricionária e tranche institucional.
- Exceções à vedação do art. 56 para formadores de mercado e para aplicação mínima obrigatória.
- Efeito da categoria do investidor (bloqueio de condicionamento para profissional, elegibilidade a tranches).
- Reprocessamento manual, aprovação prévia ou ajuste do resultado pelo operador.
- Liquidação financeira, custódia e posição do cotista.

## Trade-offs Declarados

- **Processamento automático no fechamento, sem revisão do operador.** *Custo:* não há como corrigir um livro com erro (reserva indevida, declaração errada) entre o fechamento e o resultado; a saída é revogar a oferta. *Razão:* revisão manual abre espaço para alocação discricionária, que está fora do escopo; uma aprovação sem poder de ajuste equivale a "Formada, depois revogar", que o PRD 0001 (FR-12) já permite, e custaria um estado a mais sem capacidade nova. Ver Ponto de Maior Fragilidade.
- **Resto do arredondamento por maior parte fracionária, desempate pela ordem de registro.** *Custo:* reservas grandes tendem a ficar com o resto; um investidor que fraciona a posição em várias reservas aumenta suas chances, porque o resto vai uma cota por reserva; o critério não está nos documentos típicos de oferta. *Razão:* é o arredondamento que minimiza o desvio total em relação ao proporcional exato (método dos maiores restos), atende o tratamento equitativo do art. 49, III, e o desempate pela ordem de registro é determinístico e auditável.
- **Limites por investidor valem só para a reserva.** *Custo:* um investidor pode receber uma cota, ou nenhuma, quando o investimento mínimo era dez. *Razão:* é o comportamento real do rateio; impor o mínimo na alocação exigiria excluir reservas pequenas, o que é critério de rateio distinto e fora do escopo.
- **Um único critério de rateio.** *Custo:* ofertas cujo plano de distribuição prevê outro critério não são representáveis. *Razão:* proporcional é o padrão de varejo; os demais estão na tabela de extensões.
- **Vedação aplicada antes da formação.** *Custo:* nenhum; pela exceção do § 1º, III, a exclusão nunca leva a demanda abaixo de `B`, então não altera a formação. *Razão:* segue a ordem lógica da norma e evita excluir reservas de uma oferta que não vai se formar.
- **Colocação limitada como sub-ramo do excesso, não como ramo próprio.** *Custo:* o rateio ganha dois parâmetros (conjunto rateado e quantidade rateada) em vez de um algoritmo fixo. *Razão:* em colocação limitada `D' = D > B`, então é excesso por definição; parametrizar o rateio reutiliza FR-16 a FR-18 e mantém FR-19 como invariante único.

## Métricas de Sucesso

Projeto sem uso em produção; as métricas são de correção e de contrato, verificáveis por teste e por inspeção.

**Leading:**
- Todos os cenários dos Critérios de Aceitação reproduzidos por teste, com igualdade exata dos valores — alvo: 100%.
- Processar o mesmo livro duas vezes em ambiente de teste produz resultados idênticos — alvo: 100% em amostra aleatória de livros gerados.
- Invariantes FR-18, FR-19, FR-22 e FR-23 verificadas em todo livro gerado aleatoriamente — alvo: zero violações.
- Em colocação limitada, toda reserva não vinculada recebe `q` — alvo: zero violações em livros gerados.

**Lagging:**
- Offering e ReservationBook aplicam `BookProcessed` sem precisar de dado que não esteja em FR-25 e FR-26 — verificado contra os PRDs 0001 e 0002 em 2026-09-05.

**Guardrails:**
- Nenhuma reserva recebe mais do que reservou.
- Nenhuma quantidade alocada fracionária.
- Nenhuma alteração no livro fechado ou na definição da oferta por este contexto.

## Critérios de Aceitação

Em todos os cenários, `B = 1000` e `M = 600`, salvo indicação. Letras identificam reservas; a ordem de listagem é a ordem de registro.

- **Dado** reservas A 500 (opção 3) e C 300 (opção 2), nenhuma vinculada, **quando** o livro é processado, **então** `D = D' = 800`, oferta formada em distribuição parcial, `E = 800`, A recebe 400 (parte inteira de 500 × 800 / 1000) e C recebe 300; desfecho formada e alocada, soma 700.
- **Dado** reservas A 100 (opção 1) e C 550 (opção 2), **quando** processado, **então** `D' = 650 ≥ 600`, formada, `E = 650`, A recebe 0 por condicionamento e C recebe 550; desfecho formada e alocada mesmo com soma 550 abaixo de `M`.
- **Dado** reservas A 1 (opção 3) e C 699 (opção 2), **quando** processado, **então** `D' = 700`, `E = 700`, A recebe 0 (parte inteira de 1 × 700 / 1000) com motivo de atendida parcialmente por proporcional, C recebe 699.
- **Dado** reservas somando 500, **quando** processado, **então** oferta não formada, todas com quantidade zero e motivo de oferta não formada; desfecho não formada.
- **Dado** reservas A 700, C 500 e V 300 (V vinculada), **quando** processado, **então** `D = 1500 > 1333,33`, `Dn = 1200 ≥ 1000`, V excluída, `D' = 1200`, rateio: A recebe 583 (583,33), C recebe 416 (416,67), resto 1 vai para C (maior fração) → A 583, C 417, V 0 excluída; soma 1000.
- **Dado** reservas A 800 e V 600 (V vinculada), **quando** processado, **então** `D = 1400 > 1333,33`, `Dn = 800 < 1000`, colocação limitada: A recebe 800 (atendida integralmente), V rateia `1000 − 800 = 200` e recebe 200 (atendida parcialmente por rateio); soma 1000.
- **Dado** reservas A 800, V1 400 e V2 200 (V1 e V2 vinculadas), **quando** processado, **então** `D = 1400`, `Dn = 800 < 1000`, colocação limitada: A 800; vinculadas rateiam 200 sobre `Dr = 600`: V1 133 (133,33), V2 66 (66,67), resto 1 vai para V2 (maior fração) → V1 133, V2 67; soma 1000.
- **Dado** reservas A 600 e C 400, **quando** processado, **então** `D' = 1000 = B`, colocação integral, A 600 e C 400, opções ignoradas.
- **Dado** reservas A 1000 e C 1000 registradas nessa ordem, **quando** processado, **então** rateio 500 e 500, sem resto; se fossem A 1000 e C 999, A 500 (500,25), C 499 (499,75), resto 1 vai para C (maior fração) → 500 e 500.
- **Dado** reservas A 500 e C 500 registradas nessa ordem e `B = 999`, **quando** processado, **então** A 499 (499,5), C 499 (499,5), frações iguais, resto 1 vai para A (registro mais antigo) → A 500, C 499.
- **Dado** um investidor com duas reservas, A1 300 (opção 1) e A2 200 (opção 2), e outro com C 200 (opção 2), **quando** processado, **então** `D' = 700`, distribuição parcial, A1 recebe 0 por condicionamento, A2 recebe 200 e C recebe 200; cada reserva tem resultado próprio.
- **Dado** reservas A 500 e C 500 aceitas no mesmo instante, com A anterior a C na ordem de registro, e `B = 999`, **quando** processado, **então** o resultado é o mesmo do cenário anterior: A 500, C 499.
- **Dado** `M = B = 1000` e reservas somando 900, **quando** processado, **então** oferta não formada.
- **Dado** um livro fechado sem reservas, **quando** processado, **então** `D = D' = 0 < M`, oferta não formada, desfecho não formada sem resultados por reserva.
- **Dado** um processamento interrompido por falha antes de emitir resultado, **quando** é repetido, **então** emite o `BookProcessed` que o original produziria.
- **Dado** um processamento em curso, **quando** a oferta é revogada, **então** nenhum `BookProcessed` é emitido.
- **Dado** uma oferta já processada, **quando** um novo processamento é solicitado, **então** é rejeitado.

## Dependências e Riscos

| Item | Tipo | Impacto |
|---|---|---|
| Offering: definição da oferta, `OfferClosed`, `OfferRevoked`; consome `BookProcessed` | Acoplamento bidirecional | Alto — sem definição não há processamento; o desfecho muda o estado da oferta |
| ReservationBook: leitura do livro fechado com ordem de registro total e imutável; consome `BookProcessed` | Acoplamento bidirecional | Alto — o desempate depende da ordem de registro de FR-14 do PRD 0002 |
| Critério de resto do arredondamento | Risco de desenho | Escolha do modelo, não da norma; pode divergir do plano de distribuição de uma oferta real |
| Processamento sem revisão | Risco operacional | Erro no livro só se corrige por revogação |
| Leitura do livro fechado | Decisão delegada a ADR | Precisa satisfazer NFR-02 do PRD 0002; até o ADR, o contrato é semântico |

## Perguntas em Aberto

Nenhuma em aberto. Decisões tomadas em 2026-09-05 pelo autor, registradas aqui para rastreabilidade:

- **Regra do resto do arredondamento:** maior parte fracionária, desempate pela ordem de registro. FR-17. O termo "sobras" foi substituído por colidir com sobras de subscrição.
- **Alocação abaixo do investimento mínimo por investidor:** permitida, inclusive zero. FR-24.
- **Desempate:** ordem de registro original, total e imutável (PRD 0002, FR-14); instantes iguais não geram indeterminação.
- **Repetição após falha:** permitida enquanto nenhum `BookProcessed` foi emitido. FR-02.
- **Aprovação do resultado pelo operador:** não; processamento automático. Trade-offs.
- **Colocação limitada do art. 56, § 3º:** modelada. FR-07 e FR-21 substituem a regra anterior, em que as vinculadas participavam do rateio normalmente.
- **Leitura do livro fechado:** delegada a ADR; este PRD depende de NFR-02 do PRD 0002.

## Ponto de Maior Fragilidade

A decisão de **processar o livro automaticamente no fechamento e emitir o resultado sem revisão do operador**.

*Vetor de ataque:* um revisor cético aponta que, na vida real, o coordenador revisa o livro antes de divulgar a alocação, e que o modelo não tem nenhum ponto entre Fechada e Formada para corrigir uma reserva indevida, uma declaração de vínculo errada ou um investidor que não deveria estar no livro. Com o processamento automático, a única correção é revogar a oferta inteira, o que pune todos os investidores por um erro de uma reserva. A defesa é que uma aprovação sem ajuste discricionário não compra nada além de "Formada, depois revogar"; ela só vale a pena se o ajuste entrar, e aí a máquina de estados do Offering ganha um passo e a alocação deixa de ser determinística.

*Desafie antes de aprovar:* o determinismo sem intervenção é o que o modelo quer demonstrar, ou é uma simplificação que vai cair no primeiro cenário de erro no livro? Se for o segundo, é mais barato colocar o passo de aprovação agora, com ajuste explícito e auditável, do que reabrir as três máquinas de estado depois.

## Referências

- [Resolução CVM 160 (texto consolidado)](https://conteudo.cvm.gov.br/export/sites/cvm/legislacao/resolucoes/anexos/100/resol160consolid.pdf) — arts. 49, 56, 65, 73, 74 e 75. Texto lido em 2026-09-05.
- [Instrução CVM 400 (revogada)](https://conteudo.cvm.gov.br/export/sites/cvm/legislacao/instrucoes/anexos/400/inst400.pdf) — art. 31, § 1º, origem da distinção totalidade/proporcional.
- [PRD 0001 — Cadastro e Ciclo de Vida da Oferta](0001-offering-offer-lifecycle.md) — definição da oferta, estados e semântica das opções de condicionamento.
- [PRD 0002 — Livro de Reservas](0002-reservation-book-reservation-lifecycle.md) — livro fechado, declarações, ordem do registro e status por reserva.
