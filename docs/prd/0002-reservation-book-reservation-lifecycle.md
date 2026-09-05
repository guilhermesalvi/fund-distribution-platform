<!-- prd-tier: complexa -->
# Livro de Reservas

| | |
|---|---|
| **Status** | Rascunho |
| **Autor** | Guilherme Salvi |
| **Data** | 2026-09-04 |
| **Contexto Originário** | ReservationBook (primário); consome Offering; o livro fechado é lido pelo Allocation, que devolve o resultado por reserva |

## Resumo Executivo

Entre a publicação e o fechamento, a oferta recebe reservas: o operador registra, em nome do investidor, uma quantidade de cotas e as declarações de categoria, vínculo e opção de condicionamento. O livro de reservas é o registro dessa demanda. Ele precisa aceitar só o que a oferta permite, permitir alteração e cancelamento enquanto a oferta está aberta, congelar no fechamento e, depois do processamento, mostrar em cada reserva o que aconteceu com ela sem alterar o que foi pedido. Métrica primária: nenhuma reserva aceita fora das regras da oferta e nenhuma quantidade reservada alterada após o fechamento.

## Alinhamento Estratégico

[FATO] O projeto é um modelo executável do comportamento regulado pela Resolução CVM 160 e pela Resolução CVM 175, reduzido ao mínimo viável, para o caso de uso de corretora distribuindo cotas a investidor final. A plataforma tem três contextos: Offering, ReservationBook e Allocation.

O livro é o único ponto de contato do investidor com a plataforma e a única fonte de demanda para o fechamento. Junto com o Allocation, forma o núcleo do domínio: o Offering define a oferta, mas é o livro que registra quem quer o quê, e é sobre ele que a alocação decide. Erro aqui vira alocação errada ou reserva indevida.

## Contexto e Problema

[FATO] A CVM 160 admite o recebimento de reservas quando a oferta está a mercado e o fato está divulgado (art. 65). A solicitação de reserva é ato de aceitação da oferta e tem caráter irrevogável, ressalvados o § 5º e as Seções VI a X do capítulo, que tratam de modificação e revogação (art. 65, § 4º). O pedido de reserva deve conter as condições aplicáveis caso a oferta admita distribuição parcial (art. 65, § 6º, II) e deve possibilitar a identificação da condição de investidor vinculado (art. 65, § 6º, V): a opção de condicionamento e a declaração de vínculo moram no pedido de reserva.

[FATO] Pessoas vinculadas são controladores, administradores e parentes próximos dos participantes do consórcio, do emissor e do ofertante, entre outros (art. 2º, XVI). A colocação para elas é vedada em caso de excesso de demanda superior a um terço da quantidade ofertada (art. 56). A vedação é aplicada no fechamento, pelo Allocation; a declaração de vínculo é capturada na reserva.

[FATO] Investidor profissional e qualificado são definidos por remissão à Resolução CVM 30 (art. 2º, X e XI), cujos arts. 11 e 12 exigem que o investidor ateste por escrito sua condição em termo próprio. A categoria é, na norma, uma autodeclaração. A verificação de adequação do investimento ao perfil do cliente é dever do intermediário (art. 64) e está fora do escopo.

[FATO] Por decisão do autor, o investidor no MVP tem apenas id e nome, carregados por seed. Categoria e vínculo são declarações feitas na reserva, não atributos do investidor, e são únicas por investidor em cada oferta.

Sem um livro que valide contra a oferta e congele no fechamento, o Allocation não tem entrada confiável: quantidades fora dos limites, opções não aceitas pela oferta ou reservas alteradas depois do fechamento produzem alocação inválida. Sem status por reserva após o processamento, o investidor e o operador não conseguem responder "o que aconteceu com a minha reserva" sem consultar outro contexto.

[FATO] A declaração do investidor na reserva (categoria e vínculo) é a fonte que a norma prevê para as regras da plataforma: o vínculo é identificado no pedido de reserva (CVM 160, art. 65, § 6º, V) e a categoria é atestada por escrito pelo próprio investidor (CVM 30, arts. 11 e 12). Não há cadastro verificado nem validação externa. Uma política interna de compliance que exija categoria e vínculo vindos de cadastro verificado é não-objetivo, não incerteza regulatória; se entrar, as declarações passam a atributos do investidor e a vedação do art. 56 passa a depender de dado cadastral.

## Usuário-alvo / JTBD

Investidor (comitente): quer garantir participação na oferta com a quantidade e a condição que escolheu, e saber o que aconteceu com a reserva depois do fechamento. [FATO] Por decisão do autor, no MVP a reserva é registrada pelo operador da corretora em nome do investidor; não há acesso direto do investidor nem identidade de investidor na plataforma.

Operador da corretora: quer um livro consistente com a oferta, sem reserva fora de limite ou fora do período, e a demanda acumulada para decidir o fechamento antecipado.

Consumidor (tratado como usuário de plataforma): o Allocation lê o livro fechado como entrada única do processamento e devolve o resultado por reserva.

## Solução Proposta

Tornar a reserva um agregado próprio, com o livro de uma oferta sendo o conjunto de suas reservas:

- **Registro** aceito só contra oferta Aberta, dentro do período de reserva, com quantidade dentro dos limites, declarações obrigatórias e opção de condicionamento pertencente ao conjunto aceito pela oferta. Um investidor pode ter várias reservas ativas na mesma oferta; o investimento máximo vale para a soma delas, e categoria e vínculo são os mesmos em todas.
- **Alteração e cancelamento** pelo investidor enquanto a oferta está Aberta e dentro do período. Depois disso, a reserva é irrevogável. O instante e a ordem do registro não mudam com a alteração.
- **Congelamento** no fechamento da oferta: nenhuma reserva entra, muda ou sai.
- **Status por reserva** após o processamento, derivado do resultado do Allocation, sem alterar a quantidade reservada.

| Status | Identificador | Significado |
|---|---|---|
| Ativa | `Active` | Reserva válida, aguardando o fechamento ou o processamento |
| Cancelada pelo investidor | `Withdrawn` | Cancelada antes do fechamento; não entra no livro fechado |
| Atendida | `Filled` | Recebeu a quantidade integral reservada |
| Atendida parcialmente | `PartiallyFilled` | Quantidade determinada por rateio ou por condicionamento proporcional: em regra menor que a reservada, inclusive zero; pode igualar a reservada no limite do resto do arredondamento (PRD 0003, FR-18). O status segue a regra aplicada, não a quantidade (PRD 0003, FR-24) |
| Não atendida por condicionamento | `CancelledByCondition` | Oferta em distribuição parcial e reserva condicionada à colocação total |
| Excluída por vinculação | `ExcludedRelatedParty` | Excluída pela vedação a pessoas vinculadas |
| Sem efeito | `Void` | Oferta revogada ou não formada; a reserva perde efeito, inclusive um resultado já aplicado, e a quantidade alocada vigente é zero |

Quantidade reservada, declarações e opção de condicionamento são imutáveis a partir do fechamento. O que o investidor recebeu vive no Allocation; o livro mostra o status e a quantidade alocada como leitura derivada. Revogação da oferta é a única transição que sai de um status de resultado, e leva a Sem efeito.

Mecanismo de persistência, forma de exposição e experiência de registro são downstream e fora deste documento.

## Glossário de Domínio

| Termo | Definição |
|---|---|
| Investidor | Pessoa que reserva cotas. No MVP, apenas id e nome, carregados por seed. |
| Categoria do investidor | Declaração feita na reserva: varejo, qualificado ou profissional. Única por investidor em cada oferta. |
| Pessoa vinculada | Investidor que declara, na reserva, vínculo com o fundo, o ofertante ou os intermediários. Declaração única por investidor em cada oferta. |
| Reserva | Pedido de compra de uma quantidade de cotas de uma oferta Aberta por um investidor, com declaração de categoria, de vinculação e opção de condicionamento. |
| Livro de reservas | Conjunto das reservas de uma oferta. Livro fechado: as reservas ativas no instante do fechamento da oferta. |
| Posição do investidor | Soma das quantidades das reservas ativas de um investidor em uma oferta. Limitada pelo investimento máximo por investidor. |
| Instante do registro | Momento em que a reserva foi aceita. Imutável; alteração não o muda. |
| Ordem de registro | Posição da reserva na sequência de aceitação do livro da oferta. Total e imutável: duas reservas do mesmo livro nunca ocupam a mesma posição, ainda que aceitas no mesmo instante. Usada pelo Allocation como desempate. |
| Condicionamento | Condição declarada pelo investidor para manter a reserva caso a oferta feche em distribuição parcial. |
| Opção de condicionamento | Uma das três formas de condicionamento definidas no PRD do Offering; a reserva escolhe uma entre as aceitas pela oferta. |
| Quantidade reservada | Cotas pedidas na reserva. Imutável a partir do fechamento. |
| Quantidade alocada | Cotas recebidas no processamento do livro. Definida pelo Allocation; lida aqui. Zero quando a reserva está Sem efeito. |
| Demanda acumulada | Soma das quantidades das reservas ativas de uma oferta em um instante. |

## Functional Requirements

Regras de negócio; cada uma é uma condição verificável, não um fluxo de interface.

### Registro

- **FR-01 (Must)** Reserva só é aceita contra oferta em estado Aberta e com o instante do registro dentro do período de reserva da oferta (intervalo fechado; PRD 0001, glossário).
- **FR-02 (Must)** O investidor da reserva deve existir. Não há criação de investidor por este contexto.
- **FR-03 (Must)** Quantidade reservada inteira e maior ou igual ao investimento mínimo por investidor da oferta.
- **FR-04 (Must)** A posição do investidor na oferta, incluindo a reserva sendo registrada ou alterada, é menor ou igual ao investimento máximo por investidor da oferta.
- **FR-05 (Must)** Declaração de categoria obrigatória, com valor entre varejo, qualificado e profissional. No MVP a categoria não altera nenhuma regra; é registrada para as extensões previstas.
- **FR-06 (Must)** Declaração de vínculo obrigatória (vinculado ou não vinculado).
- **FR-07 (Must)** Categoria e vínculo são únicos por investidor em cada oferta. Uma nova reserva de investidor que já tem reserva ativa na oferta deve repetir as declarações vigentes; declaração diferente é rejeitada.
- **FR-08 (Must)** Quando a oferta admite distribuição parcial, a opção de condicionamento é obrigatória e deve pertencer ao conjunto aceito pela oferta. Quando não admite, a reserva não carrega opção. Reservas distintas do mesmo investidor podem ter opções distintas.
- **FR-09 (Must)** Rejeição de registro informa todas as violações encontradas, identificando o atributo e a regra de cada uma.

### Alteração e cancelamento

- **FR-10 (Must)** O investidor, por meio do operador, pode alterar quantidade, declarações e opção de condicionamento de uma reserva ativa enquanto a oferta está Aberta e dentro do período de reserva. A alteração é validada pelas mesmas regras do registro. Alteração de categoria ou vínculo se aplica a todas as reservas ativas do investidor na oferta, e cada uma registra a mudança no histórico.
- **FR-11 (Must)** O investidor, por meio do operador, pode cancelar uma reserva ativa nas mesmas condições. A reserva passa a Cancelada pelo investidor e não entra no livro fechado. As demais reservas ativas do investidor não são afetadas.
- **FR-12 (Must)** Fora de oferta Aberta ou fora do período de reserva, alteração e cancelamento são rejeitados. A reserva é irrevogável a partir daí.
- **FR-13 (Must)** Toda alteração e cancelamento preserva o histórico: quem, quando e o que mudou.
- **FR-14 (Must)** O instante e a ordem do registro são imutáveis; nenhuma alteração os modifica. A ordem de registro é total no livro da oferta: duas reservas nunca compartilham a posição, ainda que aceitas no mesmo instante.

### Fechamento e resultado

- **FR-15 (Must)** No fechamento da oferta, o livro congela: as reservas ativas naquele instante formam o livro fechado, e nenhuma reserva entra, muda ou sai depois.
- **FR-16 (Must)** O livro fechado é consultável pelo Allocation com todas as reservas ativas, cada uma com investidor, quantidade, declarações, opção de condicionamento, instante e ordem do registro.
- **FR-17 (Must)** O resultado do processamento, recebido do Allocation, atualiza o status e a quantidade alocada de cada reserva do livro fechado. O status deriva do motivo do resultado (PRD 0003, FR-25): atendida integralmente → Atendida; atendida parcialmente por proporcional ou por rateio → Atendida parcialmente; não atendida por condicionamento → Não atendida por condicionamento; excluída por vinculação → Excluída por vinculação; oferta não formada → Sem efeito. Quantidade reservada, declarações e opção não mudam.
- **FR-18 (Must)** Quando a oferta é revogada, toda reserva da oferta que não esteja Cancelada pelo investidor passa a Sem efeito, qualquer que seja o status corrente, inclusive um status de resultado já aplicado; reserva já Sem efeito permanece. A quantidade alocada vigente passa a zero, e o resultado aplicado antes fica preservado no histórico (FR-13, NFR-03). Oferta não formada chega pelo resultado por reserva (FR-17), não por evento próprio.
- **FR-19 (Must)** O resultado só é aplicado a reservas do livro fechado da oferta correspondente. Resultado para reserva inexistente, cancelada pelo investidor ou já com status terminal é rejeitado e registrado.

### Consulta

- **FR-20 (Must)** O livro de uma oferta é consultável pelo operador a qualquer momento, com demanda acumulada e a lista de reservas com status. É a informação sobre a qual o operador decide o fechamento antecipado (PRD 0001, FR-07).
- **FR-21 (Should)** As reservas de um investidor são consultáveis pelo operador, por investidor, com status e, após o processamento, quantidade alocada.

## Domain Events

Este contexto não produz eventos na v1; o livro é lido pelo Allocation no fechamento. Eventos de reserva (`ReservationPlaced`, `ReservationChanged`, `ReservationWithdrawn`) ficam como candidatos quando houver consumidor.

Eventos consumidos:

| Evento | Produtor | Uso neste contexto |
|---|---|---|
| `OfferPublished` | Offering | Passa a aceitar reservas para a oferta, com seus limites, período e opções aceitas |
| `OfferClosed` | Offering | Congela o livro (FR-15) |
| `OfferRevoked` | Offering | Reservas passam a Sem efeito, antes ou depois do resultado (FR-18) |
| `BookProcessed` | Allocation | Aplica status e quantidade alocada por reserva, inclusive Sem efeito em oferta não formada (FR-17) |

Formada, Não formada e Encerrada não geram evento na v1 (PRD 0001, Domain Events): o desfecho não formada chega por `BookProcessed`, e o estado da oferta é consultado no Offering quando preciso.

## Non-functional Requirements

- **NFR-01** Registro, alteração e cancelamento são atômicos e validados contra a definição da oferta vigente no instante da operação. A validação de FR-04 e FR-07 lê as demais reservas ativas do investidor na mesma operação atômica.
- **NFR-02** O congelamento do livro é consistente: não existe reserva aceita com instante posterior ao fechamento da oferta, e o livro fechado que o Allocation lê é idêntico ao congelado. Esta é a exigência que o ADR de leitura do livro precisa satisfazer.
- **NFR-03** Toda mudança de reserva e todo status aplicado registram origem e instante, para rastreabilidade.
- **NFR-04** Dados do investidor não aparecem em rastros de execução; identificador da reserva e da oferta bastam.

## Considerações Regulatórias

Texto consolidado das Resoluções CVM 160 e CVM 30 lido em 2026-09-05; artigos citados conferidos contra o texto.

[FATO] CVM 160, art. 65, § 4º: a solicitação de reserva é irrevogável, ressalvados o § 5º e as Seções VI a X (modificação e revogação da oferta). O modelo admite alteração e cancelamento enquanto a oferta está Aberta e dentro do período, por decisão do autor; a irrevogabilidade passa a valer a partir do fechamento. Ver Trade-offs e Ponto de Maior Fragilidade.

[FATO] CVM 160, art. 65, § 6º, II e V: o pedido de reserva deve conter as condições aplicáveis em distribuição parcial e possibilitar a identificação da condição de investidor vinculado. FR-06 e FR-08 modelam as duas exigências como declarações na reserva.

[FATO] CVM 160, art. 65, §§ 1º e 2º: o depósito do montante reservado é facultativo e, se houver, fica em conta bloqueada. Não modelado; não há liquidação financeira.

[FATO] CVM 160, art. 66: a seção de reservas não se aplica a investidores profissionais. Sem efeito na v1, em que a categoria não altera regra; quando o efeito da categoria entrar, este artigo é o gatilho.

[FATO] CVM 160, art. 2º, XVI, e art. 56: definição de pessoa vinculada e vedação em excesso de demanda. Aqui só a declaração é capturada; a vedação, inclusive a colocação limitada do § 3º, é regra do Allocation.

[FATO] CVM 160, art. 2º, X e XI, e CVM 30, arts. 11 e 12: investidor profissional e qualificado atestam por escrito sua condição. A categoria é declarada e não verificada, em linha com a norma.

[FATO] CVM 160, art. 64: verificação de adequação do investimento ao perfil do cliente é dever do intermediário. Fora do escopo.

[FATO] CVM 160, art. 75: a seção de distribuição parcial não se aplica a ofertas exclusivas para investidores profissionais. A categoria já é declarada na reserva; seu efeito sobre o condicionamento é extensão futura.

[FATO] CVM 160, art. 69, § 1º, e art. 65, § 5º: o direito de desistência do investidor nasce da modificação da oferta ou de divergência entre prospectos. Modificação de oferta e prospecto estão fora do escopo (PRD 0001), então o gatilho não existe na v1. Se modificação entrar, este contexto ganha um cancelamento após o fechamento com prazo mínimo de cinco dias úteis e presunção de manutenção no silêncio.

## Não-objetivos

- Cadastro e verificação de investidores; o MVP usa id e nome por seed.
- Identidade e autorização de investidor; o operador registra em nome dele.
- Verificação da adequação do perfil (suitability) e das declarações de categoria e vínculo, inclusive por política interna de compliance.
- Depósito do montante reservado e qualquer movimentação financeira.
- Aplicação da vedação a pessoas vinculadas, condicionamento e rateio; são regras do Allocation.
- Efeito da categoria do investidor sobre regras (tranches, bloqueio de condicionamento para profissional, art. 66).
- Reservas por mais de um intermediário; a plataforma modela uma corretora.
- Direito de desistência após o fechamento (art. 69, § 1º; art. 65, § 5º); entra junto com modificação de oferta.
- Procedimento de precificação (bookbuilding) e intenções de investimento sem período de reserva.

## Trade-offs Declarados

- **Alteração e cancelamento livres até o fechamento.** *Custo:* a demanda acumulada durante o período não é compromisso; o operador que decide fechar antecipadamente com base nela pode ver o livro encolher antes do fechamento. Diverge da letra do art. 65, § 4º. *Razão:* a plataforma modela o livro da corretora, não o do coordenador; a irrevogabilidade que o Allocation exige é a do livro fechado. [PREMISSA] Na corretora, a reserva do cliente é ajustável até o fechamento do livro interno, e o pedido formal ao coordenador é o consolidado. Não verificada em fonte primária; de baixo impacto, porque a decisão se sustenta na fronteira do modelo mesmo sem ela.
- **Categoria e vínculo como declarações na reserva, únicas por investidor em cada oferta.** *Custo:* o mesmo investidor pode declarar categorias diferentes em ofertas diferentes; nada impede uma declaração falsa; alterar a declaração em uma reserva cascateia para as outras. *Razão:* é assim que a norma trata (declaração no pedido de reserva; termo de investidor qualificado); evita cadastro de investidor no MVP; a unicidade por oferta impede um investidor metade vinculado no mesmo livro.
- **Várias reservas ativas por investidor por oferta, com limite máximo sobre a soma.** *Custo:* registro e alteração leem as demais reservas do investidor; o rateio é por reserva, e um investidor que fraciona a posição em várias reservas aumenta suas chances no resto do arredondamento (uma cota por reserva). *Razão:* representa lotes com opções de condicionamento distintas; o limite sobre a posição preserva o teto por investidor que o Offering define.
- **Status da reserva como projeção do resultado do Allocation.** *Custo:* o desfecho de cada reserva existe em dois contextos, e após revogação o resultado emitido pelo Allocation permanece enquanto o livro mostra a reserva sem efeito. *Razão:* "o que aconteceu com a minha reserva" é pergunta do livro; obrigar o investidor a consultar o Allocation vaza a fronteira. A quantidade reservada nunca muda, então não há dois valores para o mesmo fato.
- **Instante e ordem do registro imutáveis, mesmo com alteração.** *Custo:* um investidor pode reservar pouco cedo e aumentar no fim mantendo a prioridade no desempate; o ganho máximo é uma cota, e só em empate exato de fração. *Razão:* campo imutável é simples de explicar e auditar; reiniciar a posição puniria correções e exigiria regra sobre qual alteração reinicia. A ordem, e não só o instante, é o desempate porque duas reservas podem ser aceitas no mesmo instante e o Allocation exige resultado determinístico (PRD 0003, FR-04).
- **Sem eventos de saída na v1.** *Custo:* quem quiser reagir a reservas em tempo real não tem contrato. *Razão:* o único consumidor do livro é o Allocation, que o lê no fechamento; publicar evento sem consumidor é acoplamento implícito.

## Métricas de Sucesso

Projeto sem uso em produção; as métricas são de correção e de contrato, verificáveis por teste e por inspeção.

**Leading:**
- Toda combinação inválida listada em FR-01 a FR-08 é rejeitada no registro e na alteração, com todas as violações reportadas — alvo: 100% dos casos de teste, um por regra.
- Nenhuma reserva aceita, alterada ou cancelada após o fechamento — alvo: 100%.
- Toda reserva do livro fechado de uma oferta processada tem status terminal e quantidade alocada — alvo: 100%.

**Lagging:**
- O Allocation não precisa de nenhum dado de reserva além do exposto em FR-16 — verificado contra o PRD 0003 em 2026-09-05.

**Guardrails:**
- Quantidade reservada, declarações, opção, instante e ordem do registro de uma reserva do livro fechado nunca são alterados pelo resultado do processamento nem pela revogação.
- Reserva cancelada pelo investidor antes do fechamento nunca recebe status de resultado.
- Nenhuma regra de categoria é aplicada na v1; a categoria é registrada e nada mais.
- A posição de um investidor em uma oferta nunca excede o investimento máximo por investidor.

## Critérios de Aceitação

Em todos os cenários, a oferta está Aberta dentro do período, com investimento mínimo 10 e máximo 500 e opções aceitas {1, 2, 3}, salvo indicação.

- **Dado** a oferta, **quando** um investidor existente reserva 50 cotas declarando varejo, não vinculado e opção 3, **então** a reserva é aceita como Ativa.
- **Dado** o investidor com a reserva de 50 acima, **quando** ele registra uma segunda reserva de 400 cotas com opção 1, varejo, não vinculado, **então** é aceita; a posição dele é 450.
- **Dado** o investidor com posição 450, **quando** ele registra uma terceira reserva de 60 cotas, **então** é rejeitada por FR-04, porque a posição chegaria a 510.
- **Dado** o investidor com reserva ativa declarando não vinculado, **quando** ele registra outra reserva declarando vinculado, **então** é rejeitada por FR-07.
- **Dado** um investidor com duas reservas ativas, **quando** ele altera o vínculo de uma para vinculado, **então** as duas passam a vinculado e cada uma registra a mudança no histórico.
- **Dado** a oferta, **quando** um investidor reserva 5 cotas com opção 4 sem declarar vínculo, **então** a reserva é rejeitada e a resposta lista as três violações.
- **Dado** uma oferta que não admite distribuição parcial, **quando** um investidor reserva informando uma opção, **então** a reserva é rejeitada por FR-08.
- **Dado** uma oferta em Draft, Fechada ou Revogada, **quando** alguém tenta reservar, **então** é rejeitado por FR-01.
- **Dado** uma oferta Aberta cujo período de reserva terminou, **quando** alguém tenta reservar, **então** é rejeitado por FR-01.
- **Dado** uma reserva Ativa de 50 cotas registrada às 10h, **quando** o investidor altera a quantidade para 80 às 11h, **então** a alteração é aceita, validada pelos limites, o histórico registra a mudança e o instante do registro continua 10h.
- **Dado** uma reserva Ativa, **quando** a oferta passa a Fechada e o investidor tenta cancelar, **então** é rejeitado por FR-12.
- **Dado** uma oferta Fechada com reservas Ativas e uma Cancelada pelo investidor, **quando** o Allocation consulta o livro fechado, **então** recebe só as Ativas, com quantidade, declarações, opção, instante e ordem do registro.
- **Dado** o livro fechado, **quando** chega o resultado com uma reserva de 50 cotas alocada em 40, **então** a reserva passa a Atendida parcialmente com quantidade alocada 40 e quantidade reservada 50.
- **Dado** o livro fechado, **quando** chega o resultado com uma reserva de 1 cota alocada em 0 por proporcional, **então** a reserva passa a Atendida parcialmente com quantidade alocada 0.
- **Dado** o livro fechado, **quando** chega o resultado indicando exclusão por vinculação de uma reserva, **então** ela passa a Excluída por vinculação com quantidade alocada 0.
- **Dado** uma oferta Aberta com reservas Ativas, **quando** a oferta é revogada, **então** todas passam a Sem efeito.
- **Dado** uma oferta Formada com reservas Atendida (50 alocadas 50), Atendida parcialmente (50 alocadas 40) e uma Cancelada pelo investidor, **quando** a oferta é revogada, **então** as duas primeiras passam a Sem efeito com quantidade alocada 0 e o resultado anterior no histórico; a Cancelada pelo investidor não muda.
- **Dado** o livro fechado, **quando** chega o resultado com oferta não formada, **então** todas as reservas do livro fechado passam a Sem efeito com quantidade alocada 0.
- **Dado** duas reservas aceitas no mesmo instante, **quando** o Allocation consulta o livro fechado, **então** recebe ordens de registro distintas para as duas.
- **Dado** um resultado para reserva Cancelada pelo investidor, **quando** é recebido, **então** é rejeitado e registrado, sem alterar a reserva.
- **Dado** uma oferta Aberta com reservas ativas de 50, 400 e 30 cotas, **quando** o operador consulta o livro, **então** vê demanda acumulada 480 e as três reservas com status Ativa.

## Dependências e Riscos

| Item | Tipo | Impacto |
|---|---|---|
| Offering: definição da oferta, estado e eventos de ciclo de vida | Acoplamento entre contextos | Alto — toda validação de reserva depende da definição publicada; congelamento depende de `OfferClosed` |
| Allocation lê o livro fechado e devolve `BookProcessed` com resultado por reserva | Acoplamento bidirecional | Alto — contrato de leitura (FR-16) e de resultado (FR-17) fechados em conjunto com o PRD 0003; o desempate usa a ordem de registro de FR-14 |
| Seed de investidores | Dependência de dados | Sem investidores carregados, nenhuma reserva é possível |
| Declarações não verificadas | Risco de dados | Categoria ou vínculo falsos passam; efeito no MVP limitado à vedação do art. 56 |
| Alteração livre até o fechamento | Risco de comportamento | Demanda acumulada pode encolher antes do fechamento antecipado |
| Leitura do livro fechado pelo Allocation | Decisão delegada a ADR | Precisa satisfazer NFR-02; até o ADR, o contrato é semântico (FR-16) |

## Perguntas em Aberto

Nenhuma em aberto. Decisões tomadas em 2026-09-05 pelo autor, registradas aqui para rastreabilidade:

- **Quem registra a reserva:** o operador, em nome do investidor. Sem identidade de investidor na v1.
- **Reservas por investidor por oferta:** várias. Investimento máximo vale sobre a posição; categoria e vínculo únicos por oferta. FR-04, FR-07, FR-10.
- **Desempate no Allocation:** ordem de registro original, total e imutável; o instante não basta porque duas reservas podem ser aceitas no mesmo instante. FR-14.
- **Revogação após o processamento:** reservas com resultado aplicado passam a Sem efeito com quantidade alocada zero e histórico preservado. FR-18.
- **Oferta não formada:** aplicada pelo resultado por reserva de `BookProcessed`; sem evento próprio. FR-17.
- **Demanda acumulada visível ao operador:** obrigatória. FR-20 é Must.
- **Leitura do livro fechado pelo Allocation:** delegada a ADR; este PRD exige apenas NFR-02 e FR-16.

## Ponto de Maior Fragilidade

A decisão de **permitir alteração e cancelamento da reserva até o fechamento**, tratando a irrevogabilidade do art. 65, § 4º, como propriedade do livro fechado e não da reserva.

*Vetor de ataque:* um revisor cético lê o § 4º ao pé da letra: a solicitação de reserva é ato de aceitação irrevogável, e as exceções são as de modificação e revogação da oferta, não a vontade do investidor. Com alteração livre, a demanda acumulada deixa de ser compromisso, e a decisão de fechamento antecipado do operador (PRD 0001, FR-07) passa a se apoiar em um número que pode cair no minuto seguinte. A defesa é que a plataforma modela o livro da corretora e o pedido formal é o consolidado no fechamento; essa leitura da prática é a única premissa não verificada deste PRD. Se um cenário de teste ou uma revisão regulatória exigir irrevogabilidade desde o registro, FR-10 a FR-12 caem e entra um estado de reserva confirmada.

*Desafie antes de aprovar:* o caso de uso da corretora com investidor final realmente permite ao cliente mexer na reserva até o fechamento, ou o que existe na prática é uma janela curta de arrependimento seguida de irrevogabilidade? Se for a segunda, o modelo precisa de um instante de confirmação separado do registro.

## Referências

- [Resolução CVM 160 (texto consolidado)](https://conteudo.cvm.gov.br/export/sites/cvm/legislacao/resolucoes/anexos/100/resol160consolid.pdf) — arts. 2º (X, XI, XVI), 56, 64, 65, 66, 69 e 75. Texto lido em 2026-09-05.
- [Resolução CVM 30 (texto consolidado)](https://conteudo.cvm.gov.br/export/sites/cvm/legislacao/resolucoes/anexos/001/resol030consolid.pdf) — arts. 11 e 12, investidor profissional e qualificado atestam por escrito sua condição. Texto lido em 2026-09-05.
- [PRD 0001 — Cadastro e Ciclo de Vida da Oferta](0001-offering-offer-lifecycle.md) — definição da oferta, estados, limites por investidor e opções de condicionamento.
- [PRD 0003 — Processamento do Livro e Alocação](0003-allocation-book-processing.md) — vedação, formação, condicionamento, rateio e contrato de `BookProcessed`.
