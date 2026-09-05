<!-- prd-tier: complexa -->
# Cadastro e Ciclo de Vida da Oferta

| | |
|---|---|
| **Status** | Rascunho |
| **Autor** | Guilherme Salvi |
| **Data** | 2026-09-04 |
| **Contexto Originário** | Offering (primário); consumido por ReservationBook e Allocation; Allocation devolve o desfecho do livro |
| **Confiança** | Média — uma premissa-crítica com plano de validação; leitura do art. 74 da CVM 160 e gatilho de encerramento em aberto |

## Resumo Executivo

A plataforma cobre a janela entre a publicação de uma oferta de cotas de fundo fechado e o resultado da alocação. Tudo nessa janela depende de uma definição de oferta estável e de um estado de oferta inequívoco: preço por cota, quantidade base, montante mínimo, limites por investidor, período de reserva e opções de condicionamento não mudam depois da publicação; o estado avança por transições explícitas, de Draft a Aberta, Fechada, Alocada e Encerrada, ou aos terminais Revogada e Cancelada. O contexto Offering é o dono da definição e do ciclo de vida. Métrica primária: nenhuma oferta publicada com atributo inválido, nenhuma alteração de atributo após a publicação e nenhuma transição de estado fora das permitidas.

## Alinhamento Estratégico

[FATO] O projeto é um modelo executável do comportamento regulado pela Resolução CVM 160 (ofertas públicas) e pela Resolução CVM 175 (fundos), reduzido ao mínimo viável, para o caso de uso de corretora distribuindo cotas a investidor final. Não há liquidação financeira nem integração externa.

[FATO] A plataforma tem três contextos: Offering (definição e ciclo de vida da oferta), ReservationBook (reservas contra uma oferta aberta) e Allocation (processamento do livro fechado: consolidação, vedação a pessoas vinculadas, formação, condicionamento e rateio em cotas inteiras por reserva).

Offering é a raiz de dependência: os outros dois leem a definição da oferta e não a alteram. O estado da oferta, por outro lado, avança com o desfecho que o Allocation produz ao processar o livro. Um erro de definição ou de estado aqui se propaga para todos; por isso o rigor deste PRD está nas regras de validação da publicação, no contrato de imutabilidade dos atributos e na máquina de estados.

[FATO] Séries como nível de processamento, tranches, lote adicional e demais itens da tabela de extensões futuras estão fora do escopo por decisão do autor. A oferta carrega a identificação completa das cotas (fundo, classe, subclasse, número da emissão) desde a v1 para que essas extensões entrem sem renomear o que já existe.

## Contexto e Problema

[FATO] Uma oferta é a emissão de cotas de um fundo fechado, vendida como um único conjunto. Na CVM 175, o fundo se organiza em classes e subclasses (art. 5º, §§ 5º e 7º), e classe fechada é a que não admite resgate de cotas; a entrada do investidor acontece na distribuição, o que torna a oferta o único momento de decisão de investimento coberto pela plataforma.

[FATO] A CVM 160 obriga o ofertante a definir, no ato que delibera a oferta, o tratamento em caso de distribuição parcial, incluindo a quantidade mínima ou o montante mínimo para o qual a oferta é mantida (art. 73). Havendo possibilidade de distribuição parcial, o investidor deve poder condicionar sua adesão à colocação da totalidade ou de quantidade maior ou igual ao mínimo (art. 74). Não atingido o mínimo, tudo é restituído (art. 73, § 3º).

[FATO] A norma distingue revogação da oferta, pedida pelo ofertante e que torna ineficazes a oferta e as aceitações (arts. 67, III, e 68), de cancelamento pela CVM por irregularidade (art. 70). O fim da distribuição é marcado pelo anúncio de encerramento (art. 76).

[FATO] A distinção entre receber a totalidade reservada ou o proporcional em distribuição parcial vinha do § 1º do art. 31 da Instrução CVM 400 (revogada), que presumia totalidade na falta de manifestação. A CVM 160 não repete a cláusula; a prática de mercado a mantém nos documentos da oferta.

Sem definição validada e congelada e sem estado inequívoco, os demais contextos não têm base confiável: uma reserva não pode ser aceita sem saber que a oferta está aberta e com quais limites e opções; o livro não pode ser processado sem quantidade base e montante mínimo fixos e sem saber que as reservas fecharam.

[PREMISSA-CRÍTICA] Na janela coberta pela plataforma, nenhum contexto precisa que um atributo da oferta mude depois de publicada: o que muda é só o estado, e ele muda por transições explícitas cujos gatilhos estão listados neste PRD. Se falsa — por exemplo, se modificação de oferta (CVM 160, art. 67, I e II, e art. 69), encerramento antecipado com redução da quantidade base ou lote adicional exigirem alterar atributos de oferta publicada — o contrato de imutabilidade cai, e todo consumidor que congela a definição no momento da reserva precisa ser revisto.

## Usuário-alvo / JTBD

[PREMISSA] Usuário primário: operador de distribuição da corretora, responsável por cadastrar a oferta a partir dos documentos aprovados, publicá-la, fechar o período de reserva, revogá-la quando necessário e encerrá-la. JTBD: conduzir a oferta por seu ciclo de vida com parâmetros consistentes entre si e com o que os documentos prometem ao investidor, sem risco de alteração depois que reservas começarem a ser recebidas.

Consumidores (tratados como usuários de plataforma): os contextos ReservationBook e Allocation. JTBD: obter a definição publicada e o estado corrente da oferta, confiar que a definição não muda, e, no caso do Allocation, ter o desfecho do livro (formada e alocada, ou não formada) refletido no estado da oferta.

O investidor não interage com este contexto; seu ponto de contato é a reserva, no ReservationBook.

## Solução Proposta

Tornar a oferta um agregado com definição imutável após a publicação e uma máquina de estados explícita:

| Estado | Termo de mercado | Identificador | Entrada | Saídas |
|---|---|---|---|---|
| Draft | minuta, em elaboração | `Draft` | criação | publicar → Aberta; descartar |
| Aberta | oferta a mercado, em período de reserva | `Open` | publicação | fechar → Fechada; revogar → Revogada |
| Fechada | período de reserva encerrado, livro fechado | `Closed` | fechamento explícito | livro processado com oferta formada → Alocada; livro processado com mínimo não atingido → Cancelada; revogar → Revogada |
| Alocada | alocação concluída, em liquidação | `Allocated` | desfecho do livro: formada e alocada | encerrar → Encerrada; revogar → Revogada |
| Cancelada | oferta não formada (art. 73, § 3º) | `Cancelled` | desfecho do livro: montante mínimo não atingido | terminal |
| Revogada | revogação da oferta (arts. 67, III, e 68) | `Revoked` | decisão explícita do operador | terminal |
| Encerrada | anúncio de encerramento (art. 76) | `Completed` | ação explícita do operador após a liquidação, fora do escopo | terminal |

- **Draft** aceita atributos incompletos ou inconsistentes, é editável e descartável, não aceita reservas e não é visível aos demais contextos como oferta.
- **Publicação** valida o conjunto completo de atributos como uma unidade; rejeição relata todas as violações. Aprovada, a oferta passa a Aberta e seus atributos ficam imutáveis até o fim da vida.
- **Estados posteriores** mudam apenas por transições da tabela. Fechar, revogar e encerrar são ações explícitas do operador; Alocada e Cancelada são os dois desfechos possíveis de um único processamento do livro, produzido pelo Allocation.

A oferta publicada carrega a identificação das cotas (fundo, classe, subclasse opcional, número da emissão) e as definições de que os demais contextos dependem: preço por cota, quantidade base, montante mínimo, investimento mínimo e máximo por investidor em cotas, período de reserva e o conjunto de opções de condicionamento aceitas. A semântica das três opções de condicionamento é definida neste contexto e aplicada no Allocation.

Mecanismo de persistência, forma de exposição aos demais contextos e experiência de edição são downstream e fora deste documento.

## Glossário de Domínio

Termos canônicos definidos pelo autor. Os cinco últimos pertencem ao ReservationBook e ao Allocation e entram aqui porque a semântica de condicionamento e o desfecho do livro os referenciam.

| Termo | Definição |
|---|---|
| Oferta | Emissão de cotas de um fundo fechado, com identificação das cotas, preço por cota, quantidade base, montante mínimo, investimento mínimo e máximo por investidor, período de reserva e as opções de condicionamento aceitas. |
| Fundo, classe, subclasse | Identificação das cotas segundo a CVM 175: o fundo, a classe de cotas e, quando houver, a subclasse. |
| Número da emissão | Ordinal da emissão de cotas da classe a que a oferta corresponde. |
| Draft | Oferta em elaboração. Editável livremente; não aceita reservas. |
| Oferta publicada | Oferta que saiu de Draft. Atributos imutáveis; o estado avança pela máquina de estados. |
| Aberta | Oferta publicada que aceita reservas durante o período de reserva. |
| Fechada | Oferta cujo período de reserva foi encerrado pelo operador; não aceita reservas; aguarda o processamento do livro. |
| Alocada | Oferta formada cujo livro foi processado e a alocação concluída. |
| Cancelada | Oferta cujo livro foi processado com demanda abaixo do montante mínimo; não se forma, nada é alocado. |
| Revogada | Oferta encerrada por decisão explícita do operador antes de encerrar; reservas e alocações perdem efeito. |
| Encerrada | Oferta alocada cuja liquidação terminou; estado terminal de sucesso. |
| Preço por cota | Valor unitário fixo da cota na oferta. |
| Quantidade base | Quantidade de cotas inicialmente ofertada. |
| Montante mínimo | Quantidade de cotas abaixo da qual a oferta não se forma. Sempre presente e sempre menor ou igual à quantidade base. |
| Distribuição parcial | Colocação de quantidade entre o montante mínimo e a quantidade base. |
| Investimento mínimo / máximo por investidor | Limites, em cotas, para a quantidade reservada por um investidor em uma oferta. |
| Período de reserva | Intervalo em que a oferta Aberta aceita reservas. |
| Cotas efetivamente distribuídas | Total de cotas objeto de reserva no fechamento, incluindo as reservas condicionadas (CVM 160, art. 74, parágrafo único). |
| Investidor | Pessoa que reserva cotas. No MVP, apenas id e nome, carregados por seed. |
| Reserva | Pedido de compra de uma quantidade de cotas de uma oferta Aberta por um investidor, com declaração de categoria, de vinculação e opção de condicionamento. |
| Condicionamento | Condição declarada pelo investidor para manter a reserva caso a oferta feche em distribuição parcial. |
| Opção de condicionamento | Uma das três formas de condicionamento; a oferta define quais aceita, a reserva escolhe uma delas. |
| Demanda efetiva | Reservas que sobrevivem, no processamento do livro, à vedação a pessoas vinculadas e ao condicionamento; base do rateio. Produzida pelo Allocation. |

## Functional Requirements

Regras de negócio; cada uma é uma condição verificável, não um fluxo de interface.

### Ciclo de vida

- **FR-01 (Must)** Toda oferta nasce como Draft. Não existe criação direta em outro estado.
- **FR-02 (Must)** Um Draft aceita qualquer combinação de atributos, inclusive ausentes ou inconsistentes, e pode ser editado e descartado sem restrição.
- **FR-03 (Must)** A publicação é uma ação explícita, distinta da edição. Ela valida todos os atributos como uma unidade e só leva a oferta a Aberta se nenhuma regra for violada.
- **FR-04 (Must)** Rejeição de publicação informa todas as violações encontradas, identificando o atributo e a regra de cada uma.
- **FR-05 (Must)** Nenhum atributo de oferta publicada pode ser alterado em nenhum estado posterior a Draft. Qualquer tentativa é rejeitada.
- **FR-06 (Must)** As únicas transições de estado são as da tabela da Solução Proposta. Qualquer outra é rejeitada, informando o estado corrente e a transição tentada.
- **FR-07 (Must)** Fechar é ação explícita do operador sobre uma oferta Aberta. [PREMISSA] É permitida a qualquer momento a partir do início do período de reserva, o que admite encerramento antecipado.
- **FR-08 (Must)** Uma oferta Aberta cujo período de reserva terminou não aceita reservas, mesmo antes de o operador fechá-la. A regra de recusa é do ReservationBook; a condição é definida aqui.
- **FR-09 (Must)** Uma oferta Fechada passa a Cancelada quando o desfecho do livro informa que as cotas efetivamente distribuídas ficaram abaixo do montante mínimo.
- **FR-10 (Must)** Uma oferta Fechada passa a Alocada quando o desfecho do livro informa que a oferta se formou e a alocação foi concluída.
- **FR-11 (Must)** O desfecho do livro só é aceito para oferta Fechada. Recebido em qualquer outro estado, inclusive Revogada, é ignorado sem alterar a oferta e fica registrado como descartado.
- **FR-12 (Must)** Revogar é ação explícita do operador, permitida em Aberta, Fechada e Alocada. Draft não é revogado, é descartado. Estados terminais não são revogados.
- **FR-13 (Should)** [PREMISSA] Encerrar é ação explícita do operador sobre uma oferta Alocada, registrando o fim da liquidação, que ocorre fora da plataforma.
- **FR-14 (Must)** Somente ofertas fora de Draft são apresentadas aos demais contextos, sempre com o estado corrente. Drafts não são visíveis como oferta.

### Atributos e validação na publicação

- **FR-15 (Must)** Nome obrigatório e não vazio.
- **FR-16 (Must)** Identificação das cotas obrigatória: fundo, classe e número da emissão; subclasse opcional.
- **FR-17 (Must)** Preço por cota estritamente positivo.
- **FR-18 (Must)** Quantidade base inteira e maior ou igual a 1.
- **FR-19 (Must)** Montante mínimo presente, inteiro, maior ou igual a 1 e menor ou igual à quantidade base.
- **FR-20 (Must)** Quando o montante mínimo é igual à quantidade base, a oferta não admite distribuição parcial e o conjunto de opções de condicionamento não se aplica.
- **FR-21 (Must)** Investimento mínimo por investidor inteiro, maior ou igual a 1 e menor ou igual ao investimento máximo por investidor.
- **FR-22 (Must)** Investimento máximo por investidor inteiro e menor ou igual à quantidade base.
- **FR-23 (Must)** Período de reserva com início e fim definidos e fim posterior ao início.
- **FR-24 (Must)** Publicação rejeitada se o fim do período de reserva já passou no instante da publicação.
- **FR-25 (Should)** [PREMISSA] Publicação rejeitada se o início do período de reserva já passou no instante da publicação. Depende da resposta à pergunta sobre publicação tardia.
- **FR-26 (Must)** Quando a oferta admite distribuição parcial, o conjunto de opções de condicionamento aceitas é não vazio e contém apenas opções entre as três definidas abaixo.

### Semântica das opções de condicionamento

Definidas aqui; aplicadas pelo Allocation. Abaixo do montante mínimo a oferta não se forma, passa a Cancelada e nenhuma opção se aplica.

- **FR-27 (Must)** *Condicionada à colocação total da quantidade base.* Em distribuição parcial, a reserva é cancelada e o investidor não recebe cotas.
- **FR-28 (Must)** *Condicionada ao montante mínimo, recebendo a totalidade.* Em distribuição parcial, o investidor recebe a quantidade integral reservada.
- **FR-29 (Must)** *Condicionada ao montante mínimo, recebendo o proporcional.* Em distribuição parcial, o investidor recebe a quantidade reservada multiplicada pela razão entre cotas efetivamente distribuídas e quantidade base, truncada para cotas inteiras.
- **FR-30 (Must)** Uma reserva escolhe exatamente uma opção, e essa opção precisa estar no conjunto aceito pela oferta. A verificação é do ReservationBook; o conjunto aceito é definido aqui.

## Domain Events

Contratos de domínio entre contextos; o mecanismo de transporte é decisão de arquitetura (ver Perguntas em Aberto). Payload semântico mínimo: identificação da oferta, estado resultante e instante da transição; `OfferPublished` carrega a definição completa.

| Evento | Produtor | Consumidores | Gatilho de negócio |
|---|---|---|---|
| `OfferPublished` | Offering | ReservationBook, Allocation | Publicação aprovada; oferta passa a Aberta |
| `OfferClosed` | Offering | ReservationBook, Allocation | Operador fecha o período de reserva; Allocation inicia o processamento do livro |
| `OfferAllocated` | Offering | ReservationBook | Desfecho do livro com oferta formada |
| `OfferCancelled` | Offering | ReservationBook | Desfecho do livro com mínimo não atingido |
| `OfferRevoked` | Offering | ReservationBook, Allocation | Operador revoga a oferta |
| `OfferCompleted` | Offering | ReservationBook | Operador registra o fim da liquidação |
| `BookProcessed` | Allocation | Offering | Processamento do livro concluído; carrega o desfecho (formada e alocada, ou mínimo não atingido) e as cotas efetivamente distribuídas |

`BookProcessed` é o único evento de entrada deste contexto e o único gatilho de Alocada e Cancelada. Seu contrato pertence ao PRD do Allocation; este PRD fixa que ele é consumido apenas em Fechada (FR-11).

## Non-functional Requirements

- **NFR-01** Validação de publicação e cada transição de estado são atômicas: ou a mudança ocorre por inteiro, ou nada muda.
- **NFR-02** Toda transição de estado registra quem ou qual contexto a disparou e quando, para rastreabilidade. Desfechos descartados por FR-11 também ficam registrados.
- **NFR-03** Definição e estado corrente são os mesmos para todos os consumidores em qualquer instante; não há versão intermediária visível.
- **NFR-04** Preço e cálculo proporcional são exatos: sem arredondamento binário.

## Considerações Regulatórias

[FATO] CVM 160, art. 73: o ato que delibera a oferta define o tratamento da distribuição parcial e o mínimo, em quantidade ou em montante financeiro, para o qual a oferta se mantém; § 3º manda restituir integralmente quando o mínimo não é atingido. O modelo adota quantidade de cotas e mapeia o § 3º no estado Cancelada.

[FATO] CVM 160, art. 74: havendo possibilidade de distribuição parcial, o investidor deve ter a opção de condicionar a adesão à totalidade (inciso I) ou a quantidade maior ou igual ao mínimo (inciso II). O parágrafo único define "efetivamente distribuídos" incluindo as reservas condicionadas — o denominador do cálculo proporcional (FR-29) segue essa definição.

[PREMISSA] Sob o art. 74, as opções 1 e 2 são obrigatórias sempre que a oferta admite distribuição parcial; só a opção 3 (proporcional) é escolha do ofertante, herdada da prática sob a ICVM 400, art. 31, § 1º. Se essa leitura estiver correta, o "conjunto de opções aceitas" tem um único grau de liberdade real (oferecer ou não o proporcional), e uma oferta publicada sem as opções 1 e 2 seria não conforme. Validar antes de fixar FR-26.

[FATO] CVM 160, arts. 67, III, e 68: a revogação é pedida pelo ofertante, deferida pela CVM, e torna ineficazes a oferta e as aceitações, com restituição integral. O estado Revogada modela o efeito; o deferimento pela CVM não é modelado.

[FATO] CVM 160, art. 70: suspensão e cancelamento são atos da CVM por irregularidade. O termo "Cancelada" neste PRD tem outro sentido (mínimo não atingido), alinhado à linguagem dos documentos de oferta e não à do art. 70. Suspensão não é modelada.

[FATO] CVM 160, art. 76: o resultado da oferta é divulgado no anúncio de encerramento, ao fim do prazo ou com a distribuição total. O estado Encerrada corresponde a esse marco; o anúncio em si não é modelado.

[FATO] CVM 160, art. 75: a seção de distribuição parcial não se aplica a ofertas exclusivas para investidores profissionais. A categoria do investidor é declarada na reserva já no MVP, mas seu efeito sobre o condicionamento é extensão futura.

[FATO] CVM 160, art. 65, § 4º: a solicitação de reserva é irrevogável, ressalvadas as hipóteses de modificação da oferta. Coerente com a premissa-crítica: sem modificação de atributos no escopo, não há gatilho para desistência.

[FATO] CVM 160, art. 50: lote adicional de até 25% da quantidade inicialmente requerida. Fora do escopo; quando entrar, a quantidade base deste PRD continua sendo o denominador do cálculo proporcional e a referência do lote.

[LACUNA] Registro da oferta na CVM, prospecto, lâmina e aviso ao mercado (CVM 160, arts. 57 e 65) não são modelados. Se algum atributo da oferta precisar espelhar um documento formal, ele não está listado.

## Não-objetivos

- Série como nível de processamento, tranches por público, lote adicional, outros critérios de rateio, efeito da categoria do investidor, tranche institucional, direito de preferência e sobras — extensões futuras já mapeadas pelo autor.
- Liquidação financeira e integrações externas; Encerrada apenas registra que a liquidação terminou.
- Modificação de atributos e suspensão de oferta publicada.
- Cadastro do fundo, classes e subclasses como entidades próprias; a oferta carrega a identificação, não a define.
- Cadastro de investidores; no MVP são id e nome carregados por seed, fora deste contexto.
- Documentos da oferta, registro na CVM, prospecto, lâmina, anúncio de encerramento.
- Recebimento, alteração e cancelamento de reservas (ReservationBook); consolidação, vedação a pessoas vinculadas, formação, condicionamento e rateio (Allocation). Esses contextos consomem a oferta e, no caso do Allocation, devolvem o desfecho; não definem a oferta.
- Calendário de dias úteis; o período de reserva é um intervalo de instantes.

## Trade-offs Declarados

- **Identificação completa das cotas na v1 sem cadastro de fundo.** *Custo:* fundo, classe, subclasse e emissão são texto ou identificador informado pelo operador, sem validação contra um cadastro; erro de digitação passa. *Razão:* é assim que a oferta se chama na vida real e evita renomear quando classes e séries entrarem; cadastro de fundo é entidade própria, fora do mínimo viável.
- **Série fora, com caminho previsto.** *Custo:* uma emissão com várias séries não é representável hoje. *Razão:* com a identificação das cotas na oferta, séries podem entrar como "uma oferta por série, agrupadas pela emissão", sem novo nível dentro da oferta; a decisão fica adiada sem bloquear o caminho.
- **Revogada e Cancelada como estados distintos, sem campo de motivo.** *Custo:* dois estados terminais com o mesmo efeito downstream (reservas caem, nada é alocado); todo consumidor trata os dois. *Razão:* origem e base regulatória diferem (decisão do ofertante, art. 68, versus mínimo não atingido, art. 73, § 3º); um estado genérico com motivo esconderia a distinção que o domínio faz.
- **Estado final da oferta decidido pelo desfecho do Allocation.** *Custo:* Offering consome um evento de um contexto que lê a oferta; há um ciclo de eventos entre os dois. *Razão:* "a oferta foi cancelada por não atingir o mínimo" e "a oferta foi alocada" são fatos sobre a oferta na linguagem do domínio, e um único ponto de leitura para o estado vale mais que a aciclicidade estrita. O ciclo é contido por FR-11: um único evento de entrada, aceito em um único estado. Ver Ponto de Maior Fragilidade.
- **Fechamento explícito, não derivado do fim do período.** *Custo:* uma oferta cujo período terminou fica Aberta até o operador agir, exigindo a regra FR-08 no ReservationBook. *Razão:* encerramento antecipado por excesso de demanda é prática comum e exige ação explícita; derivar por relógio impediria isso.
- **Encerrada por ação do operador, sem liquidação modelada.** *Custo:* o estado depende de uma informação externa que a plataforma não verifica. *Razão:* liquidação está fora do projeto por definição; o estado existe para o ciclo ter terminal de sucesso alinhado ao vocabulário de mercado.
- **Montante mínimo em cotas, não em moeda.** *Custo:* diverge da linguagem dos documentos de oferta, que costumam expressar o mínimo em reais; a conversão fica a cargo de quem cadastra. *Razão:* com preço fixo por cota as duas formas são equivalentes, e a forma em cotas elimina arredondamento na decisão de distribuição parcial e no cálculo proporcional.
- **Publicação valida tudo de uma vez; Draft não valida nada.** *Custo:* o operador não recebe sinal incremental enquanto preenche. *Razão:* separa "em elaboração" de "compromisso"; validação incremental é refinamento de experiência, downstream.

## Métricas de Sucesso

Projeto sem uso em produção; as métricas são de correção e de contrato, verificáveis por teste e por inspeção.

**Leading:**
- Toda combinação inválida de atributos listada em FR-15 a FR-26 é rejeitada na publicação, com todas as violações reportadas — alvo: 100% dos casos de teste, um por regra e um combinando duas violações.
- Toda transição fora da tabela de estados é rejeitada, e todo desfecho do livro recebido fora de Fechada é descartado — alvo: 100% dos pares (estado, transição) não previstos.
- Nenhuma tentativa de alteração de atributo em oferta publicada é aceita — alvo: 100%.

**Lagging:**
- Nenhum contexto consumidor precisa de atributo ou estado de oferta que não esteja neste PRD — verificado quando os PRDs de ReservationBook e Allocation forem escritos contra este.
- A introdução de séries não exige reinterpretar ofertas publicadas na v1: cada uma vira uma série da sua emissão. Verificável só quando a extensão for desenhada.

**Guardrails:**
- Draft continua aceitando estado incompleto; nenhuma regra de publicação vaza para a edição.
- A semântica das três opções de condicionamento não é reinterpretada pelo Allocation; qualquer divergência entre este PRD e o comportamento de alocação é defeito, não decisão local.
- Nenhum contexto consumidor mantém estado de oferta próprio que possa divergir do estado do Offering.

## Critérios de Aceitação

- **Dado** um Draft com fundo, classe e emissão informados, preço 100, quantidade base 1000, montante mínimo 600, investimento mínimo 10 e máximo 500 por investidor, período de reserva futuro e opções aceitas {1, 2, 3}, **quando** o operador publica, **então** a oferta passa a Aberta e fica disponível aos demais contextos com exatamente esses atributos.
- **Dado** um Draft sem número da emissão, com investimento mínimo 500 e máximo 10 e montante mínimo maior que a quantidade base, **quando** o operador publica, **então** a publicação é rejeitada, o estado permanece Draft e a resposta lista as três violações com o atributo e a regra de cada uma.
- **Dado** uma oferta em qualquer estado fora de Draft, **quando** qualquer atributo é alterado, **então** a alteração é rejeitada e a definição consultada em seguida é idêntica à publicada.
- **Dado** um Draft com todos os atributos válidos, **quando** outro contexto consulta ofertas, **então** o Draft não aparece.
- **Dado** uma oferta Aberta dentro do período de reserva, **quando** o operador fecha, **então** a oferta passa a Fechada.
- **Dado** uma oferta Fechada, **quando** chega o desfecho do livro com 500 cotas efetivamente distribuídas e montante mínimo 600, **então** a oferta passa a Cancelada.
- **Dado** uma oferta Fechada, **quando** chega o desfecho do livro com 700 cotas efetivamente distribuídas, montante mínimo 600 e alocação concluída, **então** a oferta passa a Alocada.
- **Dado** uma oferta Revogada, **quando** chega um desfecho do livro, **então** a oferta permanece Revogada e o desfecho fica registrado como descartado.
- **Dado** uma oferta Alocada, **quando** o operador revoga, **então** a oferta passa a Revogada; **quando** o operador encerra, **então** passa a Encerrada.
- **Dado** uma oferta Cancelada, Revogada ou Encerrada, **quando** qualquer transição é tentada, **então** é rejeitada informando o estado corrente.
- **Dado** um Draft, **quando** o operador tenta revogar ou fechar, **então** a transição é rejeitada.
- **Dado** uma oferta com montante mínimo igual à quantidade base e conjunto de opções vazio, **quando** o operador publica, **então** a publicação é aceita e a oferta é apresentada como não admitindo distribuição parcial.
- **Dado** uma oferta com montante mínimo menor que a quantidade base e conjunto de opções vazio, **quando** o operador publica, **então** a publicação é rejeitada por FR-26.
- **Dado** quantidade base 1000, distribuição efetiva de 700 cotas e reserva de 15 cotas com a opção 3, **quando** o Allocation aplica a semântica definida aqui, **então** o investidor recebe 10 cotas (15 × 700 ÷ 1000 = 10,5, truncado). Com a opção 1, a reserva é cancelada; com a opção 2, o investidor recebe 15 cotas.

## Dependências e Riscos

| Item | Tipo | Impacto |
|---|---|---|
| ReservationBook consome estado, período de reserva, limites por investidor e conjunto de opções aceitas | Acoplamento entre contextos | Alto — só aceita reserva em oferta Aberta dentro do período; sua autonomia depende de a definição não mudar |
| Allocation consome a oferta e o livro fechado e devolve `BookProcessed` | Acoplamento bidirecional | Alto — o desfecho dispara Alocada ou Cancelada; contrato do evento a definir no PRD do Allocation |
| Allocation aplica a semântica de FR-27 a FR-29 | Acoplamento entre contextos | Alto — divergência de interpretação produz alocação errada; a semântica é deste PRD |
| Revogação durante o processamento do livro | Risco de consistência | Contido por FR-11 (desfecho descartado fora de Fechada); resta ao Allocation decidir se interrompe o processamento ao receber `OfferRevoked` |
| Leitura do art. 74 sobre obrigatoriedade das opções 1 e 2 | Risco regulatório | Pode transformar o conjunto configurável em regra fixa e eliminar FR-26 |
| Identificação das cotas sem cadastro de fundo | Risco de dados | Erro de digitação em fundo, classe ou emissão não é detectado |

## Perguntas em Aberto

- [ ] **O conjunto de opções de condicionamento é configurável ou fixo pela norma?** Critério decisivo: confirmar se, sob o art. 74 da CVM 160, as opções 1 e 2 são obrigatórias em toda oferta com distribuição parcial. Se sim, FR-26 vira "opção 3 é a única configurável".
- [ ] **Publicação depois do início do período de reserva é permitida?** Critério decisivo: se "publicar com atraso e abrir reservas imediatamente" é legítimo, FR-25 cai; se a publicação sempre antecede o período, FR-25 vira Must.
- [ ] **Fechamento antecipado é permitido?** Critério decisivo: se o operador pode fechar antes do fim do período de reserva, FR-07 fica como está; se não, fechar só é aceito após o fim do período e a premissa em FR-07 cai.
- [ ] **O que dispara Encerrada?** Critério decisivo: se há alguma informação de liquidação que a plataforma receba, o gatilho é ela; se não, é ação do operador e FR-13 vira Must.
- [ ] **Nome da oferta é único?** Critério decisivo: se o nome é chave de negócio usada pelos demais contextos, a unicidade entra na validação de publicação; se é rótulo, não.
- [ ] **Identificação das cotas é texto livre ou identificador?** Critério decisivo: se algum contexto agrupa ou filtra por fundo ou emissão, precisa de identificador estável; se é só descritivo, texto basta.
- [ ] **Precisão do preço por cota.** Critério decisivo: quantas casas decimais os documentos de oferta usam para o preço de emissão de cotas de fundo fechado no caso de uso da corretora.
- [ ] **Candidato a ADR:** transporte dos eventos de domínio entre contextos, incluindo `BookProcessed`, com garantia de que todos veem a mesma definição e o mesmo estado.

## Ponto de Maior Fragilidade

A decisão de **o Offering ser dono dos desfechos Alocada e Cancelada, consumindo `BookProcessed` do Allocation**, em vez de terminar seu ciclo em Fechada e deixar o desfecho como leitura do Allocation.

*Vetor de ataque:* um revisor cético aponta que o Offering é declarado raiz de dependência e, ainda assim, reage a um evento do contexto que o consome. Mesmo contido por FR-11, o ciclo cria dois lugares onde o desfecho do livro existe (no Allocation, como resultado; no Offering, como estado), e a regra "descartar fora de Fechada" pode esconder um processamento que rodou sobre uma oferta já revogada, com alocações calculadas que ninguém invalidou. A alternativa acíclica é mais simples de raciocinar: Offering termina em Fechada ou Revogada, Allocation expõe "formada e alocada" ou "não formada", e quem precisa do quadro completo compõe as duas leituras.

*Desafie antes de aprovar:* o valor de um único ponto de leitura para "em que pé está a oferta" compensa manter o desfecho em dois contextos? A decisão está bem defendida (fatos sobre a oferta pertencem à oferta; um único evento de entrada em um único estado), mas é a que mais custa se errada, porque muda o contrato do Allocation e a máquina de estados ao mesmo tempo. Se mantiver, o PRD do Allocation precisa dizer o que ele faz ao receber `OfferRevoked` durante o processamento.

## Referências

- [Resolução CVM 160 (texto consolidado)](https://conteudo.cvm.gov.br/export/sites/cvm/legislacao/resolucoes/anexos/100/resol160consolid.pdf) — arts. 50, 57, 65, 67, 68, 70, 73, 74, 75 e 76.
- [Resolução CVM 175 (texto consolidado)](https://conteudo.cvm.gov.br/export/sites/cvm/legislacao/resolucoes/anexos/100/resol175consolid.pdf) — art. 5º, §§ 5º e 7º.
- [Instrução CVM 400 (revogada)](https://conteudo.cvm.gov.br/export/sites/cvm/legislacao/instrucoes/anexos/400/inst400.pdf) — art. 31, § 1º, origem da distinção totalidade/proporcional.
- [PRD 0002 — Livro de Reservas](0002-reservation-book-reservation-lifecycle.md) — regras de reserva e status por reserva após o processamento.
- [PRD 0003 — Processamento do Livro e Alocação](0003-allocation-book-processing.md) — contrato de `BookProcessed` e semântica aplicada no fechamento.
