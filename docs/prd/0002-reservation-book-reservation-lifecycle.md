<!-- prd-tier: complexa -->
# Livro de Reservas

| | |
|---|---|
| **Status** | Rascunho |
| **Autor** | Guilherme Salvi |
| **Data** | 2026-09-04 |
| **Contexto Originário** | ReservationBook (primário); consome Offering; o livro fechado é lido pelo Allocation, que devolve o resultado por reserva |
| **Confiança** | Média — uma premissa-crítica em validação; quem registra a reserva e a regra de uma reserva por investidor em aberto |

## Resumo Executivo

Entre a publicação e o fechamento, a oferta recebe reservas: o investidor pede uma quantidade de cotas e declara categoria, vínculo e opção de condicionamento. O livro de reservas é o registro dessa demanda. Ele precisa aceitar só o que a oferta permite, permitir alteração e cancelamento enquanto a oferta está aberta, congelar no fechamento e, depois do processamento, mostrar em cada reserva o que aconteceu com ela sem alterar o que foi pedido. Métrica primária: nenhuma reserva aceita fora das regras da oferta e nenhuma quantidade reservada alterada após o fechamento.

## Alinhamento Estratégico

[FATO] O projeto é um modelo executável do comportamento regulado pela Resolução CVM 160 e pela Resolução CVM 175, reduzido ao mínimo viável, para o caso de uso de corretora distribuindo cotas a investidor final. A plataforma tem três contextos: Offering, ReservationBook e Allocation.

O livro é o único ponto de contato do investidor com a plataforma e a única fonte de demanda para o fechamento. Junto com o Allocation, forma o núcleo do domínio: o Offering define a oferta, mas é o livro que registra quem quer o quê, e é sobre ele que a alocação decide. Erro aqui vira alocação errada ou reserva indevida.

## Contexto e Problema

[FATO] A CVM 160 admite o recebimento de reservas quando a oferta está a mercado e o fato está divulgado (art. 65). A solicitação de reserva é ato de aceitação da oferta e tem caráter irrevogável, ressalvadas as hipóteses de modificação da oferta (art. 65, § 4º). O pedido de reserva deve conter as condições aplicáveis caso a oferta admita distribuição parcial (art. 65, § 6º, II), o que ancora a opção de condicionamento na reserva.

[FATO] Pessoas vinculadas são controladores, administradores e parentes próximos dos participantes do consórcio, do emissor e do ofertante, entre outros (art. 2º, XVI). A colocação para elas é vedada em caso de excesso de demanda superior a um terço da quantidade ofertada (art. 56). A vedação é aplicada no fechamento, pelo Allocation; a declaração de vínculo é capturada na reserva.

[FATO] Investidor profissional e qualificado são definidos por remissão à regulamentação específica (art. 2º, X e XI; Resolução CVM 30). A verificação de adequação do investimento ao perfil do cliente é dever do intermediário (art. 64) e está fora do escopo.

[FATO] Por decisão do autor, o investidor no MVP tem apenas id e nome, carregados por seed. Categoria e vínculo são declarações feitas na reserva, não atributos do investidor.

Sem um livro que valide contra a oferta e congele no fechamento, o Allocation não tem entrada confiável: quantidades fora dos limites, opções não aceitas pela oferta ou reservas alteradas depois do fechamento produzem alocação inválida. Sem status por reserva após o processamento, o investidor e o operador não conseguem responder "o que aconteceu com a minha reserva" sem consultar outro contexto.

[PREMISSA-CRÍTICA] A declaração do investidor na reserva (categoria e vínculo) é fonte suficiente para as regras da plataforma; não há cadastro verificado nem validação externa. Se falsa — se compliance exigir que categoria e vínculo venham de um cadastro verificado do investidor — o modelo de Investidor mínimo cai, as declarações saem da reserva e passam a ser atributos do investidor, e a vedação do art. 56 passa a depender de dado cadastral, não declarado.

## Usuário-alvo / JTBD

Investidor (comitente): quer garantir participação na oferta com a quantidade e a condição que escolheu, e saber o que aconteceu com a reserva depois do fechamento. [PREMISSA] No MVP, a reserva é registrada pelo operador da corretora em nome do investidor; não há acesso direto do investidor.

Operador da corretora: quer um livro consistente com a oferta, sem reserva fora de limite ou fora do período, e uma visão da demanda acumulada para decidir o fechamento.

Consumidor (tratado como usuário de plataforma): o Allocation lê o livro fechado como entrada única do processamento e devolve o resultado por reserva.

## Solução Proposta

Tornar a reserva um agregado próprio, com o livro de uma oferta sendo o conjunto de suas reservas:

- **Registro** aceito só contra oferta Aberta, dentro do período de reserva, com quantidade dentro dos limites por investidor, declarações obrigatórias e opção de condicionamento pertencente ao conjunto aceito pela oferta.
- **Alteração e cancelamento** pelo investidor enquanto a oferta está Aberta e dentro do período. Depois disso, a reserva é irrevogável.
- **Congelamento** no fechamento da oferta: nenhuma reserva entra, muda ou sai.
- **Status por reserva** após o processamento, derivado do resultado do Allocation, sem alterar a quantidade reservada.

| Status | Identificador | Significado |
|---|---|---|
| Ativa | `Active` | Reserva válida, aguardando o fechamento ou o processamento |
| Cancelada pelo investidor | `Withdrawn` | Cancelada antes do fechamento; não entra no livro fechado |
| Atendida | `Filled` | Recebeu a quantidade integral reservada |
| Atendida parcialmente | `PartiallyFilled` | Recebeu menos que a quantidade reservada, por rateio ou por condicionamento proporcional |
| Não atendida por condicionamento | `CancelledByCondition` | Oferta em distribuição parcial e reserva condicionada à colocação total |
| Excluída por vinculação | `ExcludedRelatedParty` | Excluída pela vedação a pessoas vinculadas |
| Sem efeito | `Void` | Oferta revogada ou não formada; a reserva perde efeito |

Quantidade reservada, declarações e opção de condicionamento são imutáveis a partir do fechamento. O que o investidor recebeu vive no Allocation; o livro mostra o status e a quantidade alocada como leitura derivada.

Mecanismo de persistência, forma de exposição e experiência de registro são downstream e fora deste documento.

## Glossário de Domínio

| Termo | Definição |
|---|---|
| Investidor | Pessoa que reserva cotas. No MVP, apenas id e nome, carregados por seed. |
| Categoria do investidor | Declaração feita na reserva: varejo, qualificado ou profissional. |
| Pessoa vinculada | Investidor que declara, na reserva, vínculo com o fundo, o ofertante ou os intermediários. |
| Reserva | Pedido de compra de uma quantidade de cotas de uma oferta Aberta por um investidor, com declaração de categoria, de vinculação e opção de condicionamento. |
| Livro de reservas | Conjunto das reservas de uma oferta. Livro fechado: as reservas ativas no instante do fechamento da oferta. |
| Condicionamento | Condição declarada pelo investidor para manter a reserva caso a oferta feche em distribuição parcial. |
| Opção de condicionamento | Uma das três formas de condicionamento definidas no PRD do Offering; a reserva escolhe uma entre as aceitas pela oferta. |
| Quantidade reservada | Cotas pedidas na reserva. Imutável a partir do fechamento. |
| Quantidade alocada | Cotas recebidas no processamento do livro. Definida pelo Allocation; lida aqui. |
| Demanda acumulada | Soma das quantidades das reservas ativas de uma oferta em um instante. |

## Functional Requirements

Regras de negócio; cada uma é uma condição verificável, não um fluxo de interface.

### Registro

- **FR-01 (Must)** Reserva só é aceita contra oferta em estado Aberta e com o instante do registro dentro do período de reserva da oferta.
- **FR-02 (Must)** O investidor da reserva deve existir. Não há criação de investidor por este contexto.
- **FR-03 (Must)** Quantidade reservada inteira, maior ou igual ao investimento mínimo e menor ou igual ao investimento máximo por investidor da oferta.
- **FR-04 (Must)** Declaração de categoria obrigatória, com valor entre varejo, qualificado e profissional. No MVP a categoria não altera nenhuma regra; é registrada para as extensões previstas.
- **FR-05 (Must)** Declaração de vínculo obrigatória (vinculado ou não vinculado).
- **FR-06 (Must)** Quando a oferta admite distribuição parcial, a opção de condicionamento é obrigatória e deve pertencer ao conjunto aceito pela oferta. Quando não admite, a reserva não carrega opção.
- **FR-07 (Must)** [PREMISSA] Um investidor tem no máximo uma reserva ativa por oferta. Um segundo pedido do mesmo investidor para a mesma oferta é rejeitado; a via é alterar a reserva existente.
- **FR-08 (Must)** Rejeição de registro informa todas as violações encontradas, identificando o atributo e a regra de cada uma.

### Alteração e cancelamento

- **FR-09 (Must)** O investidor pode alterar quantidade, declarações e opção de condicionamento de uma reserva ativa enquanto a oferta está Aberta e dentro do período de reserva. A alteração é validada pelas mesmas regras do registro.
- **FR-10 (Must)** O investidor pode cancelar uma reserva ativa nas mesmas condições. A reserva passa a Cancelada pelo investidor e não entra no livro fechado.
- **FR-11 (Must)** Fora de oferta Aberta ou fora do período de reserva, alteração e cancelamento são rejeitados. A reserva é irrevogável a partir daí.
- **FR-12 (Must)** Toda alteração e cancelamento preserva o histórico: quem, quando e o que mudou.

### Fechamento e resultado

- **FR-13 (Must)** No fechamento da oferta, o livro congela: as reservas ativas naquele instante formam o livro fechado, e nenhuma reserva entra, muda ou sai depois.
- **FR-14 (Must)** O livro fechado é consultável pelo Allocation com todas as reservas ativas, cada uma com investidor, quantidade, declarações, opção de condicionamento e instante do registro.
- **FR-15 (Must)** O resultado do processamento, recebido do Allocation, atualiza o status e a quantidade alocada de cada reserva do livro fechado. Quantidade reservada, declarações e opção não mudam.
- **FR-16 (Must)** Quando a oferta é revogada ou não se forma, todas as reservas ativas passam a Sem efeito.
- **FR-17 (Must)** O resultado só é aplicado a reservas do livro fechado da oferta correspondente. Resultado para reserva inexistente, cancelada pelo investidor ou já com status terminal é rejeitado e registrado.

### Consulta

- **FR-18 (Should)** O livro de uma oferta é consultável pelo operador a qualquer momento, com demanda acumulada e a lista de reservas com status.
- **FR-19 (Should)** O investidor consulta suas reservas com status e, após o processamento, quantidade alocada.

## Domain Events

Este contexto não produz eventos na v1; o livro é lido pelo Allocation no fechamento. Eventos de reserva (`ReservationPlaced`, `ReservationChanged`, `ReservationWithdrawn`) ficam como candidatos quando houver consumidor.

Eventos consumidos:

| Evento | Produtor | Uso neste contexto |
|---|---|---|
| `OfferPublished` | Offering | Passa a aceitar reservas para a oferta, com seus limites, período e opções aceitas |
| `OfferClosed` | Offering | Congela o livro (FR-13) |
| `OfferRevoked` | Offering | Reservas ativas passam a Sem efeito (FR-16) |
| `OfferCancelled` | Offering | Reservas ativas passam a Sem efeito (FR-16) |
| `BookProcessed` | Allocation | Aplica status e quantidade alocada por reserva (FR-15) |

## Non-functional Requirements

- **NFR-01** Registro, alteração e cancelamento são atômicos e validados contra a definição da oferta vigente no instante da operação.
- **NFR-02** O congelamento do livro é consistente: não existe reserva aceita com instante posterior ao fechamento da oferta.
- **NFR-03** Toda mudança de reserva e todo status aplicado registram origem e instante, para rastreabilidade.
- **NFR-04** Dados do investidor não aparecem em rastros de execução; identificador da reserva e da oferta bastam.

## Considerações Regulatórias

[FATO] CVM 160, art. 65, § 4º: a solicitação de reserva é irrevogável, ressalvadas as hipóteses de modificação da oferta. O modelo admite alteração e cancelamento enquanto a oferta está Aberta e dentro do período, por decisão do autor; a irrevogabilidade passa a valer a partir do fechamento. Ver Trade-offs e Ponto de Maior Fragilidade.

[FATO] CVM 160, art. 65, § 6º, II: o pedido de reserva deve conter as condições aplicáveis caso a oferta admita distribuição parcial. FR-06 modela isso como opção de condicionamento obrigatória na reserva.

[FATO] CVM 160, art. 65, §§ 1º e 2º: o depósito do montante reservado é facultativo e, se houver, fica em conta bloqueada. Não modelado; não há liquidação financeira.

[FATO] CVM 160, art. 2º, XVI, e art. 56: definição de pessoa vinculada e vedação em excesso de demanda. Aqui só a declaração é capturada; a vedação é regra do Allocation.

[FATO] CVM 160, art. 2º, X e XI: investidor profissional e qualificado definidos na Resolução CVM 30. A categoria é declarada e não verificada no MVP.

[FATO] CVM 160, art. 64: verificação de adequação do investimento ao perfil do cliente é dever do intermediário. Fora do escopo.

[FATO] CVM 160, art. 75: a seção de distribuição parcial não se aplica a ofertas exclusivas para investidores profissionais. A categoria já é declarada na reserva; seu efeito sobre o condicionamento é extensão futura.

[LACUNA] Não está definido se o modelo precisa do direito de desistência do investidor em caso de modificação da oferta (art. 69) ou de divergência entre prospectos (art. 65, § 5º). Como modificação de oferta está fora do escopo do Offering, o gatilho não existe; se entrar, este contexto precisa de um cancelamento após o fechamento.

## Não-objetivos

- Cadastro e verificação de investidores; o MVP usa id e nome por seed.
- Verificação da adequação do perfil (suitability) e das declarações de categoria e vínculo.
- Depósito do montante reservado e qualquer movimentação financeira.
- Aplicação da vedação a pessoas vinculadas, condicionamento e rateio; são regras do Allocation.
- Efeito da categoria do investidor sobre regras (tranches, bloqueio de condicionamento para profissional).
- Reservas por mais de um intermediário; a plataforma modela uma corretora.
- Direito de desistência após o fechamento.
- Procedimento de precificação (bookbuilding) e intenções de investimento sem período de reserva.

## Trade-offs Declarados

- **Alteração e cancelamento livres até o fechamento.** *Custo:* a demanda acumulada durante o período não é compromisso; o operador que decide fechar antecipadamente com base nela pode ver o livro encolher antes do fechamento. Diverge da leitura estrita do art. 65, § 4º. *Razão:* é o que a corretora faz na prática com o cliente antes do fechamento; a irrevogabilidade que importa para a alocação é a do livro fechado.
- **Categoria e vínculo como declarações por reserva, não atributos do investidor.** *Custo:* o mesmo investidor pode declarar categorias diferentes em ofertas diferentes; nada impede uma declaração falsa. *Razão:* é assim que a norma trata (declaração no pedido de reserva); evita cadastro de investidor no MVP; coerente com a premissa-crítica.
- **Uma reserva ativa por investidor por oferta.** *Custo:* não representa investidor que reserva em lotes com opções de condicionamento diferentes. *Razão:* simplifica alteração (é edição da reserva única) e o rateio (uma linha por investidor); lotes com opções distintas são exceção no varejo.
- **Status da reserva como projeção do resultado do Allocation.** *Custo:* o desfecho de cada reserva existe em dois contextos. *Razão:* "o que aconteceu com a minha reserva" é pergunta do livro; obrigar o investidor a consultar o Allocation vaza a fronteira. A quantidade reservada nunca muda, então não há dois valores para o mesmo fato.
- **Sem eventos de saída na v1.** *Custo:* quem quiser reagir a reservas em tempo real não tem contrato. *Razão:* o único consumidor do livro é o Allocation, que o lê no fechamento; publicar evento sem consumidor é acoplamento implícito.

## Métricas de Sucesso

Projeto sem uso em produção; as métricas são de correção e de contrato, verificáveis por teste e por inspeção.

**Leading:**
- Toda combinação inválida listada em FR-01 a FR-07 é rejeitada no registro e na alteração, com todas as violações reportadas — alvo: 100% dos casos de teste, um por regra.
- Nenhuma reserva aceita, alterada ou cancelada após o fechamento — alvo: 100%.
- Toda reserva do livro fechado de uma oferta processada tem status terminal e quantidade alocada — alvo: 100%.

**Lagging:**
- O Allocation não precisa de nenhum dado de reserva além do exposto em FR-14 — verificado contra o PRD do Allocation.

**Guardrails:**
- Quantidade reservada, declarações e opção de uma reserva do livro fechado nunca são alteradas pelo resultado do processamento.
- Reserva cancelada pelo investidor antes do fechamento nunca recebe status de resultado.
- Nenhuma regra de categoria é aplicada na v1; a categoria é registrada e nada mais.

## Critérios de Aceitação

- **Dado** uma oferta Aberta dentro do período, com investimento mínimo 10 e máximo 500 e opções aceitas {1, 2, 3}, **quando** um investidor existente reserva 50 cotas declarando varejo, não vinculado e opção 3, **então** a reserva é aceita como Ativa.
- **Dado** a mesma oferta, **quando** o mesmo investidor tenta uma segunda reserva, **então** é rejeitada por FR-07.
- **Dado** a mesma oferta, **quando** um investidor reserva 5 cotas com opção 4 sem declarar vínculo, **então** a reserva é rejeitada e a resposta lista as três violações.
- **Dado** uma oferta que não admite distribuição parcial, **quando** um investidor reserva informando uma opção, **então** a reserva é rejeitada por FR-06.
- **Dado** uma oferta em Draft, Fechada ou Revogada, **quando** alguém tenta reservar, **então** é rejeitado por FR-01.
- **Dado** uma oferta Aberta cujo período de reserva terminou, **quando** alguém tenta reservar, **então** é rejeitado por FR-01.
- **Dado** uma reserva Ativa em oferta Aberta dentro do período, **quando** o investidor altera a quantidade para 80, **então** a alteração é aceita, validada pelos limites, e o histórico registra a mudança.
- **Dado** uma reserva Ativa, **quando** a oferta passa a Fechada e o investidor tenta cancelar, **então** é rejeitado por FR-11.
- **Dado** uma oferta Fechada com reservas Ativas e uma Cancelada pelo investidor, **quando** o Allocation consulta o livro fechado, **então** recebe só as Ativas, com quantidade, declarações, opção e instante do registro.
- **Dado** o livro fechado, **quando** chega o resultado com uma reserva de 50 cotas alocada em 40, **então** a reserva passa a Atendida parcialmente com quantidade alocada 40 e quantidade reservada 50.
- **Dado** o livro fechado, **quando** chega o resultado indicando exclusão por vinculação de uma reserva, **então** ela passa a Excluída por vinculação com quantidade alocada 0.
- **Dado** uma oferta Aberta com reservas Ativas, **quando** a oferta é revogada, **então** todas passam a Sem efeito.
- **Dado** um resultado para reserva Cancelada pelo investidor, **quando** é recebido, **então** é rejeitado e registrado, sem alterar a reserva.

## Dependências e Riscos

| Item | Tipo | Impacto |
|---|---|---|
| Offering: definição da oferta, estado e eventos de ciclo de vida | Acoplamento entre contextos | Alto — toda validação de reserva depende da definição publicada; congelamento depende de `OfferClosed` |
| Allocation lê o livro fechado e devolve `BookProcessed` com resultado por reserva | Acoplamento bidirecional | Alto — contrato de leitura (FR-14) e de resultado (FR-15) a fechar em conjunto com o PRD do Allocation |
| Seed de investidores | Dependência de dados | Sem investidores carregados, nenhuma reserva é possível |
| Declarações não verificadas | Risco de dados | Categoria ou vínculo falsos passam; efeito no MVP limitado à vedação do art. 56 |
| Alteração livre até o fechamento | Risco de comportamento | Demanda acumulada pode encolher antes do fechamento antecipado |

## Perguntas em Aberto

- [ ] **Quem registra a reserva: operador ou investidor?** Critério decisivo: se o investidor acessa a plataforma, entra identidade e autorização do investidor no escopo; se é o operador, basta o investidor existir no seed.
- [ ] **Uma reserva ativa por investidor por oferta é suficiente?** Critério decisivo: se há caso de uso real de um investidor com lotes em opções de condicionamento diferentes, FR-07 cai e o rateio passa a ser por reserva, não por investidor.
- [ ] **Alteração de reserva preserva a ordem cronológica original ou reinicia?** Critério decisivo: se o Allocation usar ordem cronológica como desempate de sobras, precisa saber qual instante vale.
- [ ] **A demanda acumulada é visível ao operador durante o período?** Critério decisivo: se a decisão de fechamento antecipado depende dela, FR-18 vira Must.
- [ ] **Candidato a ADR:** forma de leitura do livro fechado pelo Allocation (consulta no fechamento versus cópia enviada com `OfferClosed`) e garantia de que o Allocation vê exatamente o livro congelado.

## Ponto de Maior Fragilidade

A decisão de **permitir alteração e cancelamento da reserva até o fechamento**, tratando a irrevogabilidade do art. 65, § 4º, como propriedade do livro fechado e não da reserva.

*Vetor de ataque:* um revisor cético lê o § 4º ao pé da letra: a solicitação de reserva é ato de aceitação irrevogável, e as exceções são as de modificação da oferta, não a vontade do investidor. Com alteração livre, a demanda acumulada deixa de ser compromisso, e a decisão de fechamento antecipado do operador (permitida no PRD do Offering) passa a se apoiar em um número que pode cair no minuto seguinte. Se um cenário de teste ou uma revisão regulatória exigir irrevogabilidade desde o registro, entram o direito de desistência como exceção explícita e um estado de reserva "pendente de confirmação", e FR-09 a FR-11 mudam.

*Desafie antes de aprovar:* o caso de uso da corretora com investidor final realmente permite ao cliente mexer na reserva até o fechamento, ou o que existe na prática é uma janela curta de arrependimento seguida de irrevogabilidade? Se for a segunda, o modelo precisa de um instante de confirmação separado do registro.

## Referências

- [Resolução CVM 160 (texto consolidado)](https://conteudo.cvm.gov.br/export/sites/cvm/legislacao/resolucoes/anexos/100/resol160consolid.pdf) — arts. 2º (X, XI, XVI), 56, 64, 65, 69 e 75.
- [Resolução CVM 30](https://conteudo.cvm.gov.br/legislacao/resolucoes/resol030.html) — definição de investidor profissional e qualificado.
- [PRD 0001 — Cadastro e Ciclo de Vida da Oferta](0001-offering-offer-lifecycle.md) — definição da oferta, estados e opções de condicionamento.
- [PRD 0003 — Processamento do Livro e Alocação](0003-allocation-book-processing.md) — vedação, formação, condicionamento, rateio e contrato de `BookProcessed`.
